"""
Quota enforcement middleware for usage limits.
"""

from typing import Dict, Any


class QuotaEnforcer:
    """Enforce usage quotas for users."""
    
    def __init__(self):
        from ModuleFolders.Service.Billing.SubscriptionManager import SubscriptionManager
        from ModuleFolders.Service.Billing.UsageTracker import UsageTracker
        
        self.subscription_manager = SubscriptionManager()
        self.usage_tracker = UsageTracker()
    
    def check_before_operation(
        self,
        user_id: str,
        estimated_quantity: int,
        metric_type: str = "characters",
        raise_on_exceeded: bool = True,
    ) -> Dict[str, Any]:
        """Check if user has quota before an operation."""
        quota = self.subscription_manager.check_quota(user_id, metric_type)
        
        result = {
            "allowed": quota.get("allowed", False),
            "remaining": quota.get("remaining", 0),
            "limit": quota.get("limit", 0),
            "used": quota.get("used", 0),
            "requested": estimated_quantity,
            "exceeded": False,
            "message": None,
        }
        
        if not result["allowed"]:
            result["exceeded"] = True
            result["message"] = "Daily quota exceeded. Please upgrade your plan."
            if raise_on_exceeded:
                raise QuotaExceededError(
                    f"Quota exceeded: {result['used']}/{result['limit']} used"
                )
        elif result["remaining"] != -1 and estimated_quantity > result["remaining"]:
            result["exceeded"] = True
            result["message"] = f"Insufficient quota. Requested: {estimated_quantity}, Remaining: {result['remaining']}"
            if raise_on_exceeded:
                raise QuotaExceededError(result["message"])
        
        return result
    
    def record_and_check(
        self,
        user_id: str,
        quantity: int,
        metric_type: str = "characters",
    ) -> Dict[str, Any]:
        """Record usage and return updated quota status."""
        self.usage_tracker.record_usage(
            user_id=user_id,
            metric_type=metric_type,
            quantity=quantity,
        )
        
        return self.subscription_manager.check_quota(user_id, metric_type)
    
    def is_quota_available(self, user_id: str) -> bool:
        """Simple check if quota is available."""
        quota = self.subscription_manager.check_quota(user_id)
        return quota.get("allowed", False)


class QuotaExceededError(Exception):
    """Exception raised when quota is exceeded."""
    
    def __init__(self, message: str = "Quota exceeded"):
        self.message = message
        super().__init__(self.message)
