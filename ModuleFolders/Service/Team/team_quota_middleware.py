"""
Team member quota enforcement middleware.

Provides middleware to enforce team member limits based on subscription plans.
"""

from typing import Dict, Any, Optional
from functools import wraps

from ModuleFolders.Service.Auth.models import User, SubscriptionPlan
from ModuleFolders.Service.Team.team_manager import TeamManager, TeamError
from ModuleFolders.Service.Billing.SubscriptionManager import SubscriptionManager


class TeamQuotaError(Exception):
    """团队配额错误"""

    def __init__(
        self,
        message: str,
        current_members: int = 0,
        max_members: int = 0,
        plan: str = "free"
    ):
        self.message = message
        self.current_members = current_members
        self.max_members = max_members
        self.plan = plan
        super().__init__(self.message)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "error": "team_quota_exceeded",
            "message": self.message,
            "current_members": self.current_members,
            "max_members": self.max_members,
            "plan": self.plan,
            "upgrade_url": "/pricing"  # 升级链接
        }


class TeamQuotaMiddleware:
    """
    团队成员配额中间件

    根据用户的订阅计划检查和执行团队成员配额限制。
    """

    def __init__(self):
        self.team_manager = TeamManager()
        self.subscription_manager = SubscriptionManager()

        # 配额配置
        self.QUOTA_LIMITS = {
            SubscriptionPlan.FREE: 5,
            SubscriptionPlan.STARTER: 10,
            SubscriptionPlan.PRO: 50,
            SubscriptionPlan.ENTERPRISE: float('inf'),  # 无限制
        }

    def get_max_members(self, user_id: str) -> int:
        """
        获取用户的最大团队成员配额

        Args:
            user_id: 用户ID

        Returns:
            最大成员数
        """
        # 获取用户的订阅计划
        try:
            subscription = self.subscription_manager.get_user_subscription(user_id)
            if not subscription:
                # 默认为免费计划
                plan = SubscriptionPlan.FREE
            else:
                plan = subscription.plan
        except Exception:
            # 如果获取订阅失败，默认为免费计划
            plan = SubscriptionPlan.FREE

        return self.QUOTA_LIMITS.get(plan, 5)

    def get_plan_name(self, user_id: str) -> str:
        """
        获取用户的订阅计划名称

        Args:
            user_id: 用户ID

        Returns:
            计划名称 (free/starter/pro/enterprise)
        """
        try:
            subscription = self.subscription_manager.get_user_subscription(user_id)
            if not subscription:
                return "free"
            return subscription.plan.value
        except Exception:
            return "free"

    def check_team_quota(
        self,
        team_id: str,
        user_id: str,
        include_pending: bool = True
    ) -> Dict[str, Any]:
        """
        检查团队成员配额

        Args:
            team_id: 团队ID
            user_id: 操作用户ID（用于获取配额限制）
            include_pending: 是否包含待接受的邀请

        Returns:
            配额检查结果字典

        Raises:
            TeamQuotaError: 团队成员已满
        """
        # 获取配额限制
        max_members = self.get_max_members(user_id)
        plan = self.get_plan_name(user_id)

        # 获取当前成员数
        from ModuleFolders.Service.Team.team_repository import TeamRepository
        repo = TeamRepository()
        current_members = repo.count_members(team_id, include_pending=include_pending)

        # 检查是否超过配额
        if current_members >= max_members:
            raise TeamQuotaError(
                message=f"团队成员数已达上限 ({current_members}/{max_members})。当前计划: {plan}。请升级订阅以邀请更多成员。",
                current_members=current_members,
                max_members=max_members,
                plan=plan
            )

        return {
            "allowed": True,
            "current_members": current_members,
            "max_members": max_members,
            "remaining_slots": max_members - current_members,
            "plan": plan,
        }

    def check_before_add_member(
        self,
        team_id: str,
        operator_id: str,
        email: str
    ) -> Dict[str, Any]:
        """
        添加成员前检查配额

        Args:
            team_id: 团队ID
            operator_id: 操作人ID
            email: 被邀请人邮箱

        Returns:
            检查结果

        Raises:
            TeamQuotaError: 团队成员已满
        """
        return self.check_team_quota(team_id, operator_id, include_pending=True)

    def get_quota_status(
        self,
        team_id: str,
        user_id: str
    ) -> Dict[str, Any]:
        """
        获取团队配额状态

        Args:
            team_id: 团队ID
            user_id: 用户ID

        Returns:
            配额状态字典
        """
        max_members = self.get_max_members(user_id)
        plan = self.get_plan_name(user_id)

        from ModuleFolders.Service.Team.team_repository import TeamRepository
        repo = TeamRepository()
        current_members = repo.count_members(team_id, include_pending=False)
        pending_invites = repo.count_members(team_id, include_pending=True) - current_members

        return {
            "current_members": current_members,
            "pending_invites": pending_invites,
            "total_reserved": current_members + pending_invites,
            "max_members": max_members,
            "remaining_slots": max_members - current_members - pending_invites,
            "usage_percentage": (current_members / max_members * 100) if max_members != float('inf') else 0,
            "plan": plan,
            "is_unlimited": max_members == float('inf'),
        }


# FastAPI 依赖函数
async def require_team_quota(
    team_id: str,
    current_user: User,
) -> Dict[str, Any]:
    """
    FastAPI 依赖：检查团队配额

    Usage:
        @app.post("/api/v1/teams/{team_id}/members")
        async def invite_member(
            team_id: str,
            request: InviteMemberRequest,
            current_user: User = Depends(get_current_user),
            quota: Dict[str, Any] = Depends(require_team_quota)
        ):
            # quota 包含配额检查结果
            pass
    """
    middleware = TeamQuotaMiddleware()
    return middleware.check_team_quota(team_id, current_user.id)


# 装饰器
def check_team_quota(team_id_param: str = "team_id"):
    """
    团队配额检查装饰器

    Usage:
        @check_team_quota()
        async def invite_member(team_id: str, ...):
            # 配额检查通过后执行
            pass
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 从参数中获取 team_id
            team_id = kwargs.get(team_id_param)
            if not team_id:
                raise ValueError(f"Missing parameter: {team_id_param}")

            # 从参数中获取 current_user
            current_user = kwargs.get("current_user")
            if not current_user:
                raise ValueError("Missing parameter: current_user")

            # 检查配额
            middleware = TeamQuotaMiddleware()
            try:
                quota_result = middleware.check_team_quota(team_id, current_user.id)
                # 将结果添加到 kwargs
                kwargs["quota_result"] = quota_result
            except TeamQuotaError as e:
                # 抛出配额异常
                raise e

            return await func(*args, **kwargs)
        return wrapper
    return decorator


# 便捷函数
def get_team_quota_middleware() -> TeamQuotaMiddleware:
    """获取团队配额中间件实例"""
    return TeamQuotaMiddleware()
