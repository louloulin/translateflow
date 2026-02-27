"""
Team manager for team business logic.

Provides high-level team management operations with validation,
authorization, and business rules.
"""

import secrets
import string
from typing import List, Optional, Dict, Any
from datetime import datetime

from ModuleFolders.Service.Auth.models import (
    Team,
    TeamMember,
    TeamRole,
    User,
    SubscriptionPlan,
    Tenant,
)
from ModuleFolders.Service.Team.team_repository import TeamRepository
from ModuleFolders.Service.Billing.SubscriptionManager import SubscriptionManager
from ModuleFolders.Service.Email.email_service import get_email_service


class TeamError(Exception):
    """团队管理错误"""

    def __init__(self, message: str, code: str = "team_error"):
        self.message = message
        self.code = code
        super().__init__(self.message)


class TeamManager:
    """
    团队管理器

    提供团队创建、成员管理、角色分配等功能。
    """

    def __init__(self):
        self.repository = TeamRepository()
        self.subscription_manager = SubscriptionManager()

    # ==================== 团队管理 ====================

    def create_team(
        self,
        owner_id: str,
        name: str,
        slug: str,
        tenant_id: Optional[str] = None,
        description: Optional[str] = None,
    ) -> Team:
        """
        创建团队

        Args:
            owner_id: 所有者用户ID
            name: 团队名称
            slug: 团队slug (用于URL)
            tenant_id: 租户ID (可选)
            description: 团队描述

        Returns:
            创建的Team对象

        Raises:
            TeamError: 创建失败时
        """
        # 验证用户存在
        try:
            owner = User.get(User.id == owner_id)
        except Exception:
            raise TeamError("用户不存在", "user_not_found")

        # 验证slug格式
        self._validate_slug(slug)

        # 检查slug是否已被使用
        existing = self.repository.find_by_slug(tenant_id, slug)
        if existing:
            raise TeamError("团队slug已被使用", "slug_already_exists")

        # 获取订阅计划的最大成员数
        max_members = self._get_max_members_for_user(owner_id)

        # 创建团队
        team = self.repository.create_team(
            name=name,
            slug=slug,
            owner_id=owner_id,
            tenant_id=tenant_id,
            description=description,
            max_members=max_members,
        )

        # 自动将所有者添加为团队成员(Owner角色)
        self.repository.add_member(
            team_id=team.id,
            user_id=owner_id,
            role=TeamRole.OWNER.value,
            invitation_status="accepted",
        )

        return team

    def update_team(
        self,
        team_id: str,
        user_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        settings: Optional[Dict[str, Any]] = None,
    ) -> Team:
        """
        更新团队信息

        Args:
            team_id: 团队ID
            user_id: 操作用户ID
            name: 新名称
            description: 新描述
            settings: 新设置

        Returns:
            更新后的Team对象

        Raises:
            TeamError: 更新失败时
        """
        # 验证团队存在
        team = self.repository.find_by_id(team_id)
        if not team:
            raise TeamError("团队不存在", "team_not_found")

        # 验证权限 (只有所有者可以更新)
        if team.owner_id != user_id:
            member = self.repository.find_member(team_id, user_id)
            if not member or member.role != TeamRole.OWNER.value:
                raise TeamError("无权限更新团队", "permission_denied")

        # 更新字段
        update_data = {}
        if name is not None:
            update_data["name"] = name
        if description is not None:
            update_data["description"] = description
        if settings is not None:
            update_data["settings"] = settings

        return self.repository.update_team(team, **update_data)

    def delete_team(self, team_id: str, user_id: str) -> bool:
        """
        删除团队

        Args:
            team_id: 团队ID
            user_id: 操作用户ID

        Returns:
            是否删除成功

        Raises:
            TeamError: 删除失败时
        """
        # 验证团队存在
        team = self.repository.find_by_id(team_id)
        if not team:
            raise TeamError("团队不存在", "team_not_found")

        # 验证权限 (只有所有者可以删除)
        if team.owner_id != user_id:
            raise TeamError("无权限删除团队", "permission_denied")

        return self.repository.delete_team(team)

    def get_team(self, team_id: str, user_id: str) -> Team:
        """
        获取团队详情

        Args:
            team_id: 团队ID
            user_id: 操作用户ID

        Returns:
            Team对象

        Raises:
            TeamError: 获取失败时
        """
        team = self.repository.find_by_id(team_id)
        if not team:
            raise TeamError("团队不存在", "team_not_found")

        # 验证用户是团队成员
        member = self.repository.find_member(team_id, user_id)
        if not member and team.owner_id != user_id:
            raise TeamError("无权限访问团队", "permission_denied")

        return team

    def list_user_teams(self, user_id: str) -> List[Team]:
        """
        列出用户参与的所有团队

        Args:
            user_id: 用户ID

        Returns:
            Team列表
        """
        # 用户拥有的团队
        owned_teams = self.repository.find_by_owner(user_id)

        # 用户参与的团队
        member_teams = self.repository.find_by_member(user_id)

        # 合并并去重
        all_teams = list(set(owned_teams + member_teams))
        return all_teams

    # ==================== 成员管理 ====================

    def invite_member(
        self,
        team_id: str,
        inviter_id: str,
        email: str,
        role: str = TeamRole.MEMBER.value,
    ) -> TeamMember:
        """
        邀请成员加入团队

        Args:
            team_id: 团队ID
            inviter_id: 邀请人ID
            email: 被邀请人邮箱
            role: 成员角色

        Returns:
            创建的TeamMember对象(待接受状态)

        Raises:
            TeamError: 邀请失败时
        """
        # 验证团队存在
        team = self.repository.find_by_id(team_id)
        if not team:
            raise TeamError("团队不存在", "team_not_found")

        # 验证邀请人权限 (只有Owner和Admin可以邀请)
        inviter_member = self.repository.find_member(team_id, inviter_id)
        if not inviter_member or inviter_member.role not in [
            TeamRole.OWNER.value,
            TeamRole.ADMIN.value,
        ]:
            raise TeamError("无权限邀请成员", "permission_denied")

        # 检查团队是否已满
        member_count = self.repository.count_members(team_id, include_pending=True)
        if member_count >= team.max_members:
            raise TeamError(
                f"团队成员已满 (最大{team.max_members}人)",
                "team_full"
            )

        # 查找被邀请用户
        try:
            invitee = User.get(User.email == email)
        except Exception:
            raise TeamError("用户不存在", "user_not_found")

        # 检查用户是否已是团队成员
        existing = self.repository.find_member(team_id, invitee.id)
        if existing:
            raise TeamError("用户已在团队中", "already_member")

        # 生成邀请令牌
        invitation_token = self._generate_invitation_token()

        # 创建团队成员记录(待接受状态)
        member = self.repository.add_member(
            team_id=team_id,
            user_id=invitee.id,
            role=role,
            invitation_status="pending",
        )
        member.invitation_token = invitation_token
        member.save()

        # 发送邀请邮件
        try:
            email_service = get_email_service()
            if email_service.is_available():
                # 构建接受邀请的URL
                # TODO: 从环境变量或配置中获取基础URL
                base_url = "https://translateflow.example.com"
                invitation_url = f"{base_url}/teams/accept?token={invitation_token}"
                
                # 获取邀请人信息
                inviter = User.get_by_id(inviter_id)
                inviter_name = inviter.full_name or inviter.username or inviter.email.split("@")[0]
                
                # 获取被邀请人信息
                invitee_name = invitee.full_name or invitee.username or invitee.email.split("@")[0]
                
                # 发送邀请邮件
                email_service.send_team_invitation(
                    email=invitee.email,
                    invitee_name=invitee_name,
                    inviter_name=inviter_name,
                    team_name=team.name,
                    invitation_url=invitation_url,
                    role=role,
                )
        except Exception as e:
            # 邮件发送失败不影响邀请创建
            print(f"Failed to send invitation email: {e}")

        return member

    def accept_invitation(self, token: str, user_id: str) -> TeamMember:
        """
        接受团队邀请

        Args:
            token: 邀请令牌
            user_id: 用户ID

        Returns:
            更新后的TeamMember对象

        Raises:
            TeamError: 接受失败时
        """
        # 查找邀请记录
        member = self.repository.find_by_invitation_token(token)
        if not member:
            raise TeamError("邀请不存在或已过期", "invitation_not_found")

        # 验证用户
        if member.user_id != user_id:
            raise TeamError("无权限接受此邀请", "permission_denied")

        # 检查邀请状态
        if member.invitation_status == "accepted":
            raise TeamError("邀请已被接受", "already_accepted")
        if member.invitation_status == "declined":
            raise TeamError("邀请已被拒绝", "already_declined")

        # 更新状态
        return self.repository.update_invitation_status(member, "accepted")

    def decline_invitation(self, token: str, user_id: str) -> TeamMember:
        """
        拒绝团队邀请

        Args:
            token: 邀请令牌
            user_id: 用户ID

        Returns:
            更新后的TeamMember对象

        Raises:
            TeamError: 拒绝失败时
        """
        # 查找邀请记录
        member = self.repository.find_by_invitation_token(token)
        if not member:
            raise TeamError("邀请不存在或已过期", "invitation_not_found")

        # 验证用户
        if member.user_id != user_id:
            raise TeamError("无权限拒绝此邀请", "permission_denied")

        # 更新状态
        return self.repository.update_invitation_status(member, "declined")

    def update_member_role(
        self,
        team_id: str,
        operator_id: str,
        member_user_id: str,
        new_role: str,
    ) -> TeamMember:
        """
        更新成员角色

        Args:
            team_id: 团队ID
            operator_id: 操作用户ID
            member_user_id: 目标成员用户ID
            new_role: 新角色

        Returns:
            更新后的TeamMember对象

        Raises:
            TeamError: 更新失败时
        """
        # 验证团队存在
        team = self.repository.find_by_id(team_id)
        if not team:
            raise TeamError("团队不存在", "team_not_found")

        # 验证操作人权限 (只有Owner可以更新角色)
        if team.owner_id != operator_id:
            raise TeamError("无权限更新成员角色", "permission_denied")

        # 查找成员
        member = self.repository.find_member(team_id, member_user_id)
        if not member:
            raise TeamError("成员不存在", "member_not_found")

        # 不能修改所有者的角色
        if member.role == TeamRole.OWNER.value:
            raise TeamError("不能修改团队所有者的角色", "cannot_change_owner")

        # 更新角色
        return self.repository.update_member_role(member, new_role)

    def remove_member(
        self,
        team_id: str,
        operator_id: str,
        member_user_id: str,
    ) -> bool:
        """
        移除团队成员

        Args:
            team_id: 团队ID
            operator_id: 操作用户ID
            member_user_id: 目标成员用户ID

        Returns:
            是否移除成功

        Raises:
            TeamError: 移除失败时
        """
        # 验证团队存在
        team = self.repository.find_by_id(team_id)
        if not team:
            raise TeamError("团队不存在", "team_not_found")

        # 查找成员
        member = self.repository.find_member(team_id, member_user_id)
        if not member:
            raise TeamError("成员不存在", "member_not_found")

        # 验证权限 (Owner可以移除任何人, Admin可以移除Member)
        if team.owner_id != operator_id:
            operator_member = self.repository.find_member(team_id, operator_id)
            if not operator_member or operator_member.role != TeamRole.ADMIN.value:
                raise TeamError("无权限移除成员", "permission_denied")

            # Admin不能移除Owner或其他Admin
            if member.role in [TeamRole.OWNER.value, TeamRole.ADMIN.value]:
                raise TeamError("无权限移除该成员", "permission_denied")

        # 不能移除团队所有者
        if member.role == TeamRole.OWNER.value:
            raise TeamError("不能移除团队所有者", "cannot_remove_owner")

        return self.repository.remove_member(member)

    def list_members(self, team_id: str, user_id: str) -> List[TeamMember]:
        """
        列出团队成员

        Args:
            team_id: 团队ID
            user_id: 操作用户ID

        Returns:
            TeamMember列表

        Raises:
            TeamError: 查询失败时
        """
        # 验证团队存在
        team = self.repository.find_by_id(team_id)
        if not team:
            raise TeamError("团队不存在", "team_not_found")

        # 验证用户是团队成员
        member = self.repository.find_member(team_id, user_id)
        if not member and team.owner_id != user_id:
            raise TeamError("无权限访问团队成员列表", "permission_denied")

        return self.repository.find_members(team_id)

    # ==================== 辅助方法 ====================

    def _validate_slug(self, slug: str) -> None:
        """
        验证slug格式

        Args:
            slug: 团队slug

        Raises:
            TeamError: 格式无效时
        """
        if not slug:
            raise TeamError("团队slug不能为空", "invalid_slug")

        if len(slug) < 3 or len(slug) > 50:
            raise TeamError("团队slug长度必须在3-50字符之间", "invalid_slug")

        # 只允许字母、数字、连字符
        allowed_chars = set(string.ascii_lowercase + string.digits + "-")
        if not all(c in allowed_chars for c in slug):
            raise TeamError(
                "团队slug只能包含小写字母、数字和连字符",
                "invalid_slug"
            )

        # 不能以连字符开头或结尾
        if slug.startswith("-") or slug.endswith("-"):
            raise TeamError("团队slug不能以连字符开头或结尾", "invalid_slug")

    def _generate_invitation_token(self) -> str:
        """
        生成邀请令牌

        Returns:
            随机令牌字符串
        """
        alphabet = string.ascii_letters + string.digits
        token = "".join(secrets.choice(alphabet) for _ in range(32))
        return f"inv_{token}"

    def _get_max_members_for_user(self, user_id: str) -> int:
        """
        根据用户订阅计划获取最大团队成员数

        Args:
            user_id: 用户ID

        Returns:
            最大成员数
        """
        try:
            # 获取用户租户的订阅计划
            tenant = User.get(User.id == user_id).tenant_id
            if tenant:
                tenant_obj = Tenant.get(Tenant.id == tenant)
                plan = tenant_obj.plan

                # 根据计划返回配额
                quotas = {
                    SubscriptionPlan.FREE.value: 5,
                    SubscriptionPlan.STARTER.value: 10,
                    SubscriptionPlan.PRO.value: 50,
                    SubscriptionPlan.ENTERPRISE.value: -1,  # 无限制
                }
                return quotas.get(plan, 5)
        except Exception:
            pass

        return 5  # 默认配额
