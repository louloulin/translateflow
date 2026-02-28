"""
Stripe webhook handler for processing payment events.

Handles the following events:
- payment_succeeded: 订单支付成功
- payment_failed: 订单支付失败
- subscription_updated: 订阅更新
- subscription_deleted: 订阅取消
- invoice_payment_failed: 发票支付失败
- invoice_paid: 发票已支付
"""

import json
import os
import hmac
import hashlib
from datetime import datetime
from typing import Dict, Any, Optional

try:
    import stripe
except ImportError:
    stripe = None

from ModuleFolders.Infrastructure.Database.pgsql import get_database
from ModuleFolders.Service.Auth.models import User, Tenant, SubscriptionPlan
from ModuleFolders.Service.Billing.SubscriptionManager import SubscriptionManager
from ModuleFolders.Service.Billing.InvoiceGenerator import InvoiceGenerator
from ModuleFolders.Service.Email.email_service import EmailService


class StripeWebhookHandler:
    """处理 Stripe Webhook 事件"""

    def __init__(self):
        self.db = get_database()
        self.webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET")
        self.subscription_manager = SubscriptionManager()
        self.invoice_generator = InvoiceGenerator()
        self.email_service = EmailService()

        if stripe:
            stripe.api_key = os.getenv("STRIPE_API_KEY")

    def verify_signature(self, payload: bytes, signature: str) -> bool:
        """验证 Webhook 签名"""
        if not self.webhook_secret:
            raise ValueError("STRIPE_WEBHOOK_SECRET 未配置")

        try:
            stripe.Webhook.construct_event(
                payload, signature, self.webhook_secret
            )
            return True
        except ValueError:
            # 无效的 payload
            return False
        except stripe.error.SignatureVerificationError:
            # 无效的签名
            return False

    def handle_event(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """处理 Stripe 事件"""
        event_type = event_data.get("type")
        data = event_data.get("data", {}).get("object", {})

        handlers = {
            "payment_intent.succeeded": self._handle_payment_succeeded,
            "payment_intent.payment_failed": self._handle_payment_failed,
            "customer.subscription.updated": self._handle_subscription_updated,
            "customer.subscription.deleted": self._handle_subscription_deleted,
            "invoice.payment_failed": self._handle_invoice_payment_failed,
            "invoice.paid": self._handle_invoice_paid,
            "checkout.session.completed": self._handle_checkout_completed,
        }

        handler = handlers.get(event_type)
        if handler:
            return handler(data)
        else:
            return {"status": "ignored", "event_type": event_type}

    def _handle_payment_succeeded(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """处理支付成功事件"""
        payment_intent_id = data.get("id")
        customer_id = data.get("customer")
        amount = data.get("amount")  # 单位：分
        currency = data.get("currency")

        # 查找用户
        user = self._find_user_by_customer_id(customer_id)
        if not user:
            return {
                "status": "error",
                "message": f"未找到客户 {customer_id} 对应的用户"
            }

        # 记录支付
        cursor = self.db.cursor()
        cursor.execute(
            """INSERT INTO payments
               (id, user_id, stripe_payment_id, amount, currency, status, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                payment_intent_id,
                user.id,
                payment_intent_id,
                amount / 100,  # 转换为元
                currency.upper(),
                "succeeded",
                datetime.now().isoformat()
            )
        )
        self.db.commit()

        # 发送支付成功邮件
        self.email_service.send_payment_notification(
            email=user.email,
            payment_id=payment_intent_id,
            amount=amount / 100,
            currency=currency.upper(),
            status="成功"
        )

        return {
            "status": "success",
            "payment_id": payment_intent_id,
            "user_id": user.id
        }

    def _handle_payment_failed(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """处理支付失败事件"""
        payment_intent_id = data.get("id")
        customer_id = data.get("customer")
        error_message = data.get("last_payment_error", {}).get("message", "未知错误")

        user = self._find_user_by_customer_id(customer_id)
        if not user:
            return {
                "status": "error",
                "message": f"未找到客户 {customer_id} 对应的用户"
            }

        # 记录失败支付
        cursor = self.db.cursor()
        cursor.execute(
            """INSERT INTO payments
               (id, user_id, stripe_payment_id, status, error_message, created_at)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (
                payment_intent_id,
                user.id,
                payment_intent_id,
                "failed",
                error_message,
                datetime.now().isoformat()
            )
        )
        self.db.commit()

        # 发送支付失败邮件
        self.email_service.send_payment_notification(
            email=user.email,
            payment_id=payment_intent_id,
            status="失败",
            error_message=error_message
        )

        return {
            "status": "failed",
            "payment_id": payment_intent_id,
            "user_id": user.id
        }

    def _handle_subscription_updated(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """处理订阅更新事件"""
        subscription_id = data.get("id")
        customer_id = data.get("customer")
        status = data.get("status")
        plan_id = data.get("items", {}).get("data", [{}])[0].get("price", {}).get("id")

        user = self._find_user_by_customer_id(customer_id)
        if not user:
            return {
                "status": "error",
                "message": f"未找到客户 {customer_id} 对应的用户"
            }

        # 根据 Stripe Price ID 映射到计划
        plan = self._map_price_to_plan(plan_id)

        # 更新租户计划
        if user.tenant_id:
            cursor = self.db.cursor()
            cursor.execute(
                """UPDATE tenants SET plan = ?, updated_at = ?
                   WHERE id = ?""",
                (plan.value, datetime.now().isoformat(), user.tenant_id)
            )
            self.db.commit()

        # 记录订阅更新
        cursor = self.db.cursor()
        cursor.execute(
            """INSERT INTO subscription_events
               (id, user_id, subscription_id, event_type, plan, status, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                subscription_id,
                user.id,
                subscription_id,
                "updated",
                plan.value,
                status,
                datetime.now().isoformat()
            )
        )
        self.db.commit()

        # 发送订阅更新通知
        self.email_service.send_subscription_notification(
            email=user.email,
            event="updated",
            plan=plan.value,
            status=status
        )

        return {
            "status": "success",
            "subscription_id": subscription_id,
            "plan": plan.value,
            "user_id": user.id
        }

    def _handle_subscription_deleted(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """处理订阅取消事件"""
        subscription_id = data.get("id")
        customer_id = data.get("customer")

        user = self._find_user_by_customer_id(customer_id)
        if not user:
            return {
                "status": "error",
                "message": f"未找到客户 {customer_id} 对应的用户"
            }

        # 将租户降级为免费计划
        if user.tenant_id:
            cursor = self.db.cursor()
            cursor.execute(
                """UPDATE tenants SET plan = ?, updated_at = ?
                   WHERE id = ?""",
                (SubscriptionPlan.FREE.value, datetime.now().isoformat(), user.tenant_id)
            )
            self.db.commit()

        # 记录订阅取消
        cursor = self.db.cursor()
        cursor.execute(
            """INSERT INTO subscription_events
               (id, user_id, subscription_id, event_type, status, created_at)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (
                subscription_id,
                user.id,
                subscription_id,
                "cancelled",
                "cancelled",
                datetime.now().isoformat()
            )
        )
        self.db.commit()

        # 发送订阅取消通知
        self.email_service.send_subscription_notification(
            email=user.email,
            event="cancelled",
            plan="free"
        )

        return {
            "status": "success",
            "subscription_id": subscription_id,
            "user_id": user.id
        }

    def _handle_invoice_payment_failed(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """处理发票支付失败事件"""
        invoice_id = data.get("id")
        customer_id = data.get("customer")
        attempt_count = data.get("attempt_count", 0)

        user = self._find_user_by_customer_id(customer_id)
        if not user:
            return {
                "status": "error",
                "message": f"未找到客户 {customer_id} 对应的用户"
            }

        # 更新发票状态
        cursor = self.db.cursor()
        cursor.execute(
            """UPDATE invoices SET status = ?, updated_at = ?
               WHERE stripe_invoice_id = ?""",
            ("payment_failed", datetime.now().isoformat(), invoice_id)
        )
        self.db.commit()

        # 发送支付失败通知
        self.email_service.send_invoice_notification(
            email=user.email,
            invoice_id=invoice_id,
            status="支付失败",
            attempt_count=attempt_count
        )

        return {
            "status": "failed",
            "invoice_id": invoice_id,
            "user_id": user.id,
            "attempt_count": attempt_count
        }

    def _handle_invoice_paid(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """处理发票已支付事件"""
        invoice_id = data.get("id")
        customer_id = data.get("customer")
        amount_paid = data.get("amount_paid")  # 单位：分
        currency = data.get("currency")

        user = self._find_user_by_customer_id(customer_id)
        if not user:
            return {
                "status": "error",
                "message": f"未找到客户 {customer_id} 对应的用户"
            }

        # 更新发票状态
        cursor = self.db.cursor()
        cursor.execute(
            """UPDATE invoices
               SET status = ?, amount_paid = ?, paid_at = ?, updated_at = ?
               WHERE stripe_invoice_id = ?""",
            (
                "paid",
                amount_paid / 100,
                datetime.now().isoformat(),
                datetime.now().isoformat(),
                invoice_id
            )
        )
        self.db.commit()

        # 发送发票支付成功通知
        self.email_service.send_invoice_notification(
            email=user.email,
            invoice_id=invoice_id,
            status="已支付",
            amount=amount_paid / 100,
            currency=currency.upper()
        )

        return {
            "status": "success",
            "invoice_id": invoice_id,
            "user_id": user.id
        }

    def _handle_checkout_completed(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """处理结账会话完成事件"""
        session_id = data.get("id")
        customer_id = data.get("customer")
        subscription_id = data.get("subscription")
        user_id = data.get("metadata", {}).get("user_id")

        if not user_id:
            return {
                "status": "error",
                "message": "结账会话缺少 user_id 元数据"
            }

        # 查找用户
        try:
            user = User.get_by_id(user_id)
        except User.DoesNotExist:
            return {
                "status": "error",
                "message": f"用户 {user_id} 不存在"
            }

        # 更新用户的 Stripe 客户 ID
        cursor = self.db.cursor()
        cursor.execute(
            """UPDATE users SET stripe_customer_id = ?, updated_at = ?
               WHERE id = ?""",
            (customer_id, datetime.now().isoformat(), user_id)
        )
        self.db.commit()

        # 记录结账完成事件
        cursor = self.db.cursor()
        cursor.execute(
            """INSERT INTO checkout_sessions
               (id, user_id, stripe_session_id, stripe_customer_id,
                stripe_subscription_id, status, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                session_id,
                user_id,
                session_id,
                customer_id,
                subscription_id,
                "completed",
                datetime.now().isoformat()
            )
        )
        self.db.commit()

        return {
            "status": "success",
            "session_id": session_id,
            "user_id": user_id,
            "customer_id": customer_id,
            "subscription_id": subscription_id
        }

    def _find_user_by_customer_id(self, customer_id: str) -> Optional[User]:
        """根据 Stripe 客户 ID 查找用户"""
        cursor = self.db.cursor()
        cursor.execute(
            "SELECT id FROM users WHERE stripe_customer_id = ?",
            (customer_id,)
        )
        row = cursor.fetchone()

        if row:
            try:
                return User.get_by_id(row[0])
            except User.DoesNotExist:
                return None
        return None

    def _map_price_to_plan(self, price_id: str) -> SubscriptionPlan:
        """将 Stripe Price ID 映射到订阅计划"""
        price_mapping = {
            os.getenv("STRIPE_PRICE_STARTER"): SubscriptionPlan.STARTER,
            os.getenv("STRIPE_PRICE_PRO"): SubscriptionPlan.PRO,
            os.getenv("STRIPE_PRICE_ENTERPRISE"): SubscriptionPlan.ENTERPRISE,
        }
        return price_mapping.get(price_id, SubscriptionPlan.FREE)
