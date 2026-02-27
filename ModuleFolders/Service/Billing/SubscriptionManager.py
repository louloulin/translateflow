"""
Subscription management service.

Handles subscription lifecycle including:
- Creating/updating/canceling subscriptions
- Plan upgrades/downgrades
- Subscription status tracking
- Stripe integration
"""

import os
import uuid
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any

try:
    import stripe
except ImportError:
    stripe = None

from ModuleFolders.Service.Auth.models import SubscriptionPlan, User
from ModuleFolders.Infrastructure.Database.pgsql import get_database


class SubscriptionManager:
    """Manage user subscriptions and billing."""
    
    # Plan limits (characters per day)
    PLAN_LIMITS = {
        SubscriptionPlan.FREE: 1000,
        SubscriptionPlan.STARTER: 50000,
        SubscriptionPlan.PRO: 500000,
        SubscriptionPlan.ENTERPRISE: -1,  # Unlimited
    }
    
    # Plan pricing (CNY per month)
    PLAN_PRICING = {
        SubscriptionPlan.FREE: 0,
        SubscriptionPlan.STARTER: 29,
        SubscriptionPlan.PRO: 99,
        SubscriptionPlan.ENTERPRISE: None,  # Custom pricing
    }
    
    def __init__(self):
        self.db = get_database()
        self.stripe_api_key = os.getenv("STRIPE_API_KEY")
        
        if stripe and self.stripe_api_key:
            stripe.api_key = self.stripe_api_key
    
    def get_plan_limits(self, plan: SubscriptionPlan) -> Dict[str, Any]:
        """Get plan limits and features."""
        return {
            "plan": plan.value,
            "daily_characters": self.PLAN_LIMITS.get(plan, 0),
            "monthly_price": self.PLAN_PRICING.get(plan),
            "features": self._get_plan_features(plan),
        }
    
    def get_all_plans(self) -> List[Dict[str, Any]]:
        """Get all available subscription plans."""
        return [
            self.get_plan_limits(plan)
            for plan in SubscriptionPlan
        ]
    
    def check_quota(self, user_id: str, metric_type: str = "characters") -> Dict[str, Any]:
        """Check if user has remaining quota."""
        from ModuleFolders.Service.Auth.models import Tenant
        
        try:
            user = User.get_by_id(user_id)
        except User.DoesNotExist:
            return {"allowed": False, "reason": "User not found"}
        
        # Get tenant plan
        plan = SubscriptionPlan.FREE
        if user.tenant_id:
            try:
                tenant = Tenant.get_by_id(user.tenant_id)
                plan = SubscriptionPlan(tenant.plan)
            except Tenant.DoesNotExist:
                pass
        
        limits = self.get_plan_limits(plan)
        daily_limit = limits["daily_characters"]
        
        if daily_limit == -1:  # Unlimited
            return {"allowed": True, "remaining": -1, "limit": -1}
        
        # Get today's usage from usage_records table
        today = datetime.now().date().isoformat()
        cursor = self.db.cursor()
        cursor.execute(
            """SELECT COALESCE(SUM(quantity), 0) as total
               FROM usage_records
               WHERE user_id = ? AND metric_type = ?
               AND date(recorded_at) = ?""",
            (user_id, metric_type, today)
        )
        result = cursor.fetchone()

        used = result[0] if result else 0
        remaining = max(0, daily_limit - used)
        
        return {
            "allowed": remaining > 0,
            "remaining": remaining,
            "limit": daily_limit,
            "used": used,
        }
    
    def _get_plan_features(self, plan: SubscriptionPlan) -> List[str]:
        """Get feature list for a plan."""
        features = {
            SubscriptionPlan.FREE: [
                "1,000 characters per day",
                "Basic file formats",
                "No API access",
            ],
            SubscriptionPlan.STARTER: [
                "50,000 characters per day",
                "All file formats",
                "1 user",
                "Email support",
            ],
            SubscriptionPlan.PRO: [
                "500,000 characters per day",
                "Advanced features",
                "5 team members",
                "Priority support",
                "API access",
            ],
            SubscriptionPlan.ENTERPRISE: [
                "Unlimited characters",
                "Dedicated support",
                "Unlimited team members",
                "SSO",
                "Custom integrations",
            ],
        }
        return features.get(plan, [])
