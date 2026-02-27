"""
Quota enforcement middleware for usage limits.
"""

from typing import Dict, Any


"""
Quota enforcement middleware for usage limits.

Features:
- Pre-operation quota checking
- Automatic usage recording
- FastAPI middleware integration
- Caching for performance
- Detailed error messages with upgrade guidance
"""

from typing import Dict, Any, Optional
from functools import wraps
from datetime import datetime, timedelta
import hashlib


class QuotaEnforcer:
    """Enforce usage quotas for users."""

    def __init__(self, cache_ttl: int = 60):
        """
        初始化配额执行器

        Args:
            cache_ttl: 配额缓存时间（秒），默认60秒
        """
        from ModuleFolders.Service.Billing.SubscriptionManager import SubscriptionManager
        from ModuleFolders.Service.Billing.UsageTracker import UsageTracker

        self.subscription_manager = SubscriptionManager()
        self.usage_tracker = UsageTracker()
        self.cache_ttl = cache_ttl
        self._quota_cache: Dict[str, Dict[str, Any]] = {}

    def _get_cache_key(self, user_id: str, metric_type: str) -> str:
        """生成缓存键"""
        today = datetime.now().date().isoformat()
        key_data = f"{user_id}:{metric_type}:{today}"
        return hashlib.md5(key_data.encode()).hexdigest()

    def _get_cached_quota(self, user_id: str, metric_type: str) -> Optional[Dict[str, Any]]:
        """获取缓存的配额信息"""
        cache_key = self._get_cache_key(user_id, metric_type)
        cached = self._quota_cache.get(cache_key)

        if cached:
            # 检查缓存是否过期
            if datetime.now() < cached["expires_at"]:
                return cached["data"]

        return None

    def _set_cached_quota(self, user_id: str, metric_type: str, data: Dict[str, Any]):
        """设置配额缓存"""
        cache_key = self._get_cache_key(user_id, metric_type)
        self._quota_cache[cache_key] = {
            "data": data,
            "expires_at": datetime.now() + timedelta(seconds=self.cache_ttl),
        }

    def _invalidate_cache(self, user_id: str, metric_type: str):
        """使缓存失效"""
        cache_key = self._get_cache_key(user_id, metric_type)
        self._quota_cache.pop(cache_key, None)

    def check_before_operation(
        self,
        user_id: str,
        estimated_quantity: int,
        metric_type: str = "characters",
        raise_on_exceeded: bool = True,
    ) -> Dict[str, Any]:
        """
        在操作前检查配额

        Args:
            user_id: 用户ID
            estimated_quantity: 预计使用量
            metric_type: 指标类型
            raise_on_exceeded: 超额时是否抛出异常

        Returns:
            配额检查结果字典
        """
        # 尝试从缓存获取
        cached_quota = self._get_cached_quota(user_id, metric_type)
        if cached_quota:
            quota = cached_quota
        else:
            quota = self.subscription_manager.check_quota(user_id, metric_type)
            self._set_cached_quota(user_id, metric_type, quota)

        result = {
            "allowed": quota.get("allowed", False),
            "remaining": quota.get("remaining", 0),
            "limit": quota.get("limit", 0),
            "used": quota.get("used", 0),
            "requested": estimated_quantity,
            "exceeded": False,
            "message": None,
            "upgrade_url": None,
        }

        # 配额已用完
        if not result["allowed"]:
            result["exceeded"] = True
            result["message"] = self._generate_exceeded_message(metric_type, result)
            result["upgrade_url"] = "/pricing"
            if raise_on_exceeded:
                raise QuotaExceededError(
                    message=result["message"],
                    limit=result["limit"],
                    used=result["used"],
                    remaining=result["remaining"],
                    upgrade_url=result["upgrade_url"],
                )

        # 请求量超过剩余配额
        elif result["remaining"] != -1 and estimated_quantity > result["remaining"]:
            result["exceeded"] = True
            result["message"] = self._generate_insufficient_message(
                metric_type, estimated_quantity, result["remaining"]
            )
            result["upgrade_url"] = "/pricing"
            if raise_on_exceeded:
                raise QuotaExceededError(
                    message=result["message"],
                    limit=result["limit"],
                    used=result["used"],
                    remaining=result["remaining"],
                    requested=estimated_quantity,
                    upgrade_url=result["upgrade_url"],
                )

        return result

    def record_and_check(
        self,
        user_id: str,
        quantity: int,
        metric_type: str = "characters",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        记录使用量并返回更新后的配额状态

        Args:
            user_id: 用户ID
            quantity: 使用量
            metric_type: 指标类型
            metadata: 额外元数据

        Returns:
            更新后的配额状态
        """
        # 记录使用量
        self.usage_tracker.record_usage(
            user_id=user_id,
            metric_type=metric_type,
            quantity=quantity,
            metadata=metadata,
        )

        # 使缓存失效
        self._invalidate_cache(user_id, metric_type)

        # 返回更新后的配额
        return self.subscription_manager.check_quota(user_id, metric_type)

    def check_and_record(
        self,
        user_id: str,
        quantity: int,
        metric_type: str = "characters",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        先检查配额，如果通过则记录使用量

        Args:
            user_id: 用户ID
            quantity: 使用量
            metric_type: 指标类型
            metadata: 额外元数据

        Returns:
            包含配额检查结果和记录信息的字典

        Raises:
            QuotaExceededError: 配额不足时抛出
        """
        # 先检查配额
        check_result = self.check_before_operation(
            user_id=user_id,
            estimated_quantity=quantity,
            metric_type=metric_type,
            raise_on_exceeded=True,
        )

        # 记录使用量
        record_result = self.usage_tracker.record_usage(
            user_id=user_id,
            metric_type=metric_type,
            quantity=quantity,
            metadata=metadata,
        )

        # 使缓存失效
        self._invalidate_cache(user_id, metric_type)

        # 获取更新后的配额状态
        updated_quota = self.subscription_manager.check_quota(user_id, metric_type)

        return {
            "record": record_result,
            "quota_before": check_result,
            "quota_after": updated_quota,
        }

    def is_quota_available(self, user_id: str, metric_type: str = "characters") -> bool:
        """
        简单检查配额是否可用

        Args:
            user_id: 用户ID
            metric_type: 指标类型

        Returns:
            配额是否可用
        """
        try:
            quota = self.check_before_operation(
                user_id=user_id,
                estimated_quantity=1,
                metric_type=metric_type,
                raise_on_exceeded=False,
            )
            return not quota["exceeded"]
        except Exception:
            return False

    def get_usage_percentage(self, user_id: str, metric_type: str = "characters") -> float:
        """
        获取配额使用百分比

        Args:
            user_id: 用户ID
            metric_type: 指标类型

        Returns:
            使用百分比 (0-100), 无限配额返回 0.0
        """
        quota = self.subscription_manager.check_quota(user_id, metric_type)
        limit = quota.get("limit", 0)
        used = quota.get("used", 0)

        if limit == -1:  # Unlimited
            return 0.0

        if limit == 0:
            return 100.0 if used > 0 else 0.0

        return min(100.0, (used / limit) * 100)

    def _generate_exceeded_message(
        self,
        metric_type: str,
        quota_info: Dict[str, Any],
    ) -> str:
        """生成配额超限的错误消息"""
        metric_names = {
            "characters": "翻译字符",
            "api_calls": "API调用",
            "storage_mb": "存储空间",
            "concurrent_tasks": "并发任务",
            "team_members": "团队成员",
        }
        metric_name = metric_names.get(metric_type, metric_type)

        if quota_info["limit"] == 0:
            return f"您的{metric_name}配额已用完。请升级您的订阅计划以继续使用。"

        return (
            f"您的{metric_name}配额已用完。"
            f"今日已使用: {quota_info['used']:,} / {quota_info['limit']:,}。"
            f"请升级您的订阅计划以获取更多配额。"
        )

    def _generate_insufficient_message(
        self,
        metric_type: str,
        requested: int,
        remaining: int,
    ) -> str:
        """生成配额不足的错误消息"""
        metric_names = {
            "characters": "翻译字符",
            "api_calls": "API调用",
            "storage_mb": "存储空间(MB)",
            "concurrent_tasks": "并发任务",
            "team_members": "团队成员",
        }
        metric_name = metric_names.get(metric_type, metric_type)

        return (
            f"剩余{metric_name}配额不足。"
            f"请求量: {requested:,}, 剩余量: {remaining:,}。"
            f"请升级您的订阅计划以获取更多配额。"
        )


class QuotaExceededError(Exception):
    """配额超限异常"""

    def __init__(
        self,
        message: str = "Quota exceeded",
        limit: int = 0,
        used: int = 0,
        remaining: int = 0,
        requested: Optional[int] = None,
        upgrade_url: Optional[str] = None,
    ):
        self.message = message
        self.limit = limit
        self.used = used
        self.remaining = remaining
        self.requested = requested
        self.upgrade_url = upgrade_url
        super().__init__(self.message)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式（用于API响应）"""
        result = {
            "error": "quota_exceeded",
            "message": self.message,
            "limit": self.limit,
            "used": self.used,
            "remaining": self.remaining,
        }
        if self.requested is not None:
            result["requested"] = self.requested
        if self.upgrade_url:
            result["upgrade_url"] = self.upgrade_url
        return result


def require_quota(metric_type: str = "characters", quantity_param: str = "quantity"):
    """
    装饰器：在执行操作前自动检查配额

    用法:
        @require_quota(metric_type="characters", quantity_param="char_count")
        async def translate_text(user_id: str, char_count: int, text: str):
            # 执行翻译操作
            pass

    Args:
        metric_type: 指标类型
        quantity_param: 函数参数中代表使用量的参数名
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 获取 user_id 和 quantity
            user_id = kwargs.get("user_id")
            quantity = kwargs.get(quantity_param, 1)

            if not user_id:
                raise ValueError("user_id parameter is required for quota checking")

            # 创建配额执行器并检查
            enforcer = QuotaEnforcer()
            enforcer.check_before_operation(
                user_id=user_id,
                estimated_quantity=quantity,
                metric_type=metric_type,
                raise_on_exceeded=True,
            )

            # 执行原函数
            result = await func(*args, **kwargs)

            # 记录使用量
            enforcer.usage_tracker.record_usage(
                user_id=user_id,
                metric_type=metric_type,
                quantity=quantity,
                metadata={"function": func.__name__},
            )

            return result
        return wrapper
    return decorator


class QuotaExceededError(Exception):
    """Exception raised when quota is exceeded."""
    
    def __init__(self, message: str = "Quota exceeded"):
        self.message = message
        super().__init__(self.message)
