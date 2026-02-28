"""
Payment processing service for Stripe integration.
"""

import os
from typing import Optional, Dict, Any, List

try:
    import stripe
except ImportError:
    stripe = None

from ModuleFolders.Service.Auth.models import SubscriptionPlan


class PaymentProcessor:
    """Handle payment processing with Stripe."""
    
    def __init__(self):
        self.stripe_api_key = os.getenv("STRIPE_API_KEY")
        self.webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET")
        
        if stripe and self.stripe_api_key:
            stripe.api_key = self.stripe_api_key
    
    def create_customer(self, user_id: str, email: str, metadata: Optional[Dict] = None) -> str:
        """Create a Stripe customer for a user."""
        if not stripe:
            raise ValueError("Stripe is not configured")
        
        customer = stripe.Customer.create(
            email=email,
            metadata={
                "user_id": user_id,
                **(metadata or {})
            }
        )
        
        return customer.id
    
    def create_checkout_session(
        self,
        user_id: str,
        plan: SubscriptionPlan,
        success_url: str,
        cancel_url: str,
    ) -> Dict[str, Any]:
        """Create a Stripe checkout session for subscription."""
        if not stripe:
            raise ValueError("Stripe is not configured")
        
        price_ids = {
            SubscriptionPlan.STARTER: os.getenv("STRIPE_PRICE_STARTER"),
            SubscriptionPlan.PRO: os.getenv("STRIPE_PRICE_PRO"),
            SubscriptionPlan.ENTERPRISE: os.getenv("STRIPE_PRICE_ENTERPRISE"),
        }
        
        price_id = price_ids.get(plan)
        if not price_id:
            raise ValueError(f"No price ID configured for plan: {plan}")
        
        session = stripe.checkout.Session.create(
            mode="subscription",
            payment_method_types=["card"],
            line_items=[{
                "price": price_id,
                "quantity": 1,
            }],
            success_url=success_url,
            cancel_url=cancel_url,
            metadata={"user_id": user_id},
        )
        
        return {
            "session_id": session.id,
            "url": session.url,
        }
    
    def create_portal_session(self, customer_id: str, return_url: str) -> str:
        """Create a Stripe customer portal session."""
        if not stripe:
            raise ValueError("Stripe is not configured")

        session = stripe.billing_portal.Session.create(
            customer=customer_id,
            return_url=return_url,
        )

        return session.url

    def get_payment_methods(self, customer_id: str) -> List[Dict[str, Any]]:
        """获取客户的所有支付方式"""
        if not stripe:
            raise ValueError("Stripe is not configured")

        payment_methods = stripe.PaymentMethod.list(
            customer=customer_id,
            type="card"
        )

        return [
            {
                "id": pm.id,
                "type": pm.type,
                "card": {
                    "brand": pm.card.brand,
                    "last4": pm.card.last4,
                    "exp_month": pm.card.exp_month,
                    "exp_year": pm.card.exp_year,
                }
            }
            for pm in payment_methods.data
        ]

    def attach_payment_method(
        self,
        customer_id: str,
        payment_method_id: str
    ) -> Dict[str, Any]:
        """将支付方式附加到客户"""
        if not stripe:
            raise ValueError("Stripe is not configured")

        payment_method = stripe.PaymentMethod.attach(
            payment_method_id,
            customer=customer_id
        )

        return {
            "id": payment_method.id,
            "type": payment_method.type,
            "card": {
                "brand": payment_method.card.brand,
                "last4": payment_method.card.last4,
            }
        }

    def detach_payment_method(self, payment_method_id: str) -> bool:
        """分离支付方式"""
        if not stripe:
            raise ValueError("Stripe is not configured")

        try:
            stripe.PaymentMethod.detach(payment_method_id)
            return True
        except Exception:
            return False

    def set_default_payment_method(
        self,
        customer_id: str,
        payment_method_id: str
    ) -> bool:
        """设置默认支付方式"""
        if not stripe:
            raise ValueError("Stripe is not configured")

        try:
            stripe.Customer.modify(
                customer_id,
                invoice_settings={
                    "default_payment_method": payment_method_id
                }
            )
            return True
        except Exception:
            return False

    def create_subscription(
        self,
        customer_id: str,
        price_id: str,
        trial_days: Optional[int] = None,
        metadata: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """创建订阅"""
        if not stripe:
            raise ValueError("Stripe is not configured")

        subscription_params = {
            "customer": customer_id,
            "items": [{"price": price_id}],
            "metadata": metadata or {}
        }

        if trial_days:
            subscription_params["trial_period_days"] = trial_days

        subscription = stripe.Subscription.create(**subscription_params)

        return {
            "id": subscription.id,
            "status": subscription.status,
            "current_period_start": subscription.current_period_start,
            "current_period_end": subscription.current_period_end,
            "cancel_at_period_end": subscription.cancel_at_period_end,
        }

    def cancel_subscription(
        self,
        subscription_id: str,
        at_period_end: bool = True
    ) -> Dict[str, Any]:
        """取消订阅"""
        if not stripe:
            raise ValueError("Stripe is not configured")

        if at_period_end:
            # 在当前计费周期结束时取消
            subscription = stripe.Subscription.modify(
                subscription_id,
                cancel_at_period_end=True
            )
        else:
            # 立即取消
            subscription = stripe.Subscription.delete(subscription_id)

        return {
            "id": subscription.id,
            "status": subscription.status,
            "cancel_at_period_end": subscription.cancel_at_period_end,
        }

    def update_subscription(
        self,
        subscription_id: str,
        new_price_id: str
    ) -> Dict[str, Any]:
        """更新订阅计划（升降级）"""
        if not stripe:
            raise ValueError("Stripe is not configured")

        subscription = stripe.Subscription.retrieve(subscription_id)

        # 更新订阅项目
        updated_subscription = stripe.Subscription.modify(
            subscription_id,
            items=[{
                "id": subscription["items"]["data"][0].id,
                "price": new_price_id
            }]
        )

        return {
            "id": updated_subscription.id,
            "status": updated_subscription.status,
            "current_period_start": updated_subscription.current_period_start,
            "current_period_end": updated_subscription.current_period_end,
        }

    def get_subscription(self, subscription_id: str) -> Dict[str, Any]:
        """获取订阅详情"""
        if not stripe:
            raise ValueError("Stripe is not configured")

        subscription = stripe.Subscription.retrieve(subscription_id)

        return {
            "id": subscription.id,
            "status": subscription.status,
            "current_period_start": subscription.current_period_start,
            "current_period_end": subscription.current_period_end,
            "cancel_at_period_end": subscription.cancel_at_period_end,
            "customer": subscription.customer,
            "plan": {
                "id": subscription.plan.id,
                "amount": subscription.plan.amount,
                "currency": subscription.plan.currency,
                "interval": subscription.plan.interval,
            }
        }

    def get_invoice(self, invoice_id: str) -> Dict[str, Any]:
        """获取发票详情"""
        if not stripe:
            raise ValueError("Stripe is not configured")

        invoice = stripe.Invoice.retrieve(invoice_id)

        return {
            "id": invoice.id,
            "number": invoice.number,
            "status": invoice.status,
            "amount_due": invoice.amount_due,
            "amount_paid": invoice.amount_paid,
            "currency": invoice.currency,
            "invoice_pdf": invoice.invoice_pdf,
            "hosted_invoice_url": invoice.hosted_invoice_url,
            "created": invoice.created,
            "due_date": invoice.due_date,
        }

    def list_invoices(
        self,
        customer_id: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """获取客户的发票列表"""
        if not stripe:
            raise ValueError("Stripe is not configured")

        invoices = stripe.Invoice.list(
            customer=customer_id,
            limit=limit
        )

        return [
            {
                "id": inv.id,
                "number": inv.number,
                "status": inv.status,
                "amount_due": inv.amount_due,
                "currency": inv.currency,
                "created": inv.created,
                "due_date": inv.due_date,
            }
            for inv in invoices.data
        ]
