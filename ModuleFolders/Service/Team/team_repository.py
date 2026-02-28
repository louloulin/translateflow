"""
Team repository for data access operations.

Provides database access methods for Team and TeamMember models.
"""

import uuid
from typing import List, Optional
from peewee import DoesNotExist

from ModuleFolders.Service.Auth.models import Team, TeamMember, TeamRole, User


class TeamRepository:
    """Repository for team data access operations."""

    @staticmethod
    def find_by_id(team_id: str) -> Optional[Team]:
        """
        根据ID查找团队

        Args:
            team_id: 团队ID

        Returns:
            Team对象或None
        """
        try:
            return Team.get(Team.id == team_id)
        except DoesNotExist:
            return None

    @staticmethod
    def find_by_slug(tenant_id: Optional[str], slug: str) -> Optional[Team]:
        """
        根据slug查找团队

        Args:
            tenant_id: 租户ID (可选)
            slug: 团队slug

        Returns:
            Team对象或None
        """
        try:
            if tenant_id:
                return Team.get((Team.tenant_id == tenant_id) & (Team.slug == slug))
            return Team.get(Team.slug == slug)
        except DoesNotExist:
            return None

    @staticmethod
    def find_by_owner(owner_id: str) -> List[Team]:
        """
        查找用户拥有的所有团队

        Args:
            owner_id: 所有者用户ID

        Returns:
            Team列表
        """
        return list(Team.select().where(Team.owner_id == owner_id))

    @staticmethod
    def find_by_member(user_id: str) -> List[Team]:
        """
        查找用户参与的所有团队

        Args:
            user_id: 用户ID

        Returns:
            Team列表
        """
        return list(
            Team.select()
            .join(TeamMember)
            .where(TeamMember.user_id == user_id)
            .distinct()
        )

    @staticmethod
    def find_members(team_id: str) -> List[TeamMember]:
        """
        查找团队所有成员

        Args:
            team_id: 团队ID

        Returns:
            TeamMember列表
        """
        return list(TeamMember.select().where(TeamMember.team_id == team_id))

    @staticmethod
    def find_member(team_id: str, user_id: str) -> Optional[TeamMember]:
        """
        查找团队成员

        Args:
            team_id: 团队ID
            user_id: 用户ID

        Returns:
            TeamMember对象或None
        """
        try:
            return TeamMember.get(
                (TeamMember.team_id == team_id) & (TeamMember.user_id == user_id)
            )
        except DoesNotExist:
            return None

    @staticmethod
    def find_by_invitation_token(token: str) -> Optional[TeamMember]:
        """
        根据邀请令牌查找团队成员记录

        Args:
            token: 邀请令牌

        Returns:
            TeamMember对象或None
        """
        try:
            return TeamMember.get(TeamMember.invitation_token == token)
        except DoesNotExist:
            return None

    @staticmethod
    def count_members(team_id: str, include_pending: bool = False) -> int:
        """
        统计团队成员数量

        Args:
            team_id: 团队ID
            include_pending: 是否包含待接受邀请的成员

        Returns:
            成员数量
        """
        query = TeamMember.select().where(TeamMember.team_id == team_id)
        if not include_pending:
            query = query.where(TeamMember.invitation_status == "accepted")
        return query.count()

    @staticmethod
    def create_team(
        name: str,
        slug: str,
        owner_id: str,
        tenant_id: Optional[str] = None,
        description: Optional[str] = None,
        max_members: int = 5,
        settings: dict = None,
    ) -> Team:
        """
        创建团队

        Args:
            name: 团队名称
            slug: 团队slug
            owner_id: 所有者用户ID
            tenant_id: 租户ID (可选)
            description: 团队描述
            max_members: 最大成员数
            settings: 团队设置

        Returns:
            创建的Team对象
        """
        team = Team(
            name=name,
            slug=slug,
            owner_id=owner_id,
            tenant_id=tenant_id,
            description=description,
            max_members=max_members,
            settings=settings or {},
            is_active=True,
        )
        team.save()
        return team

    @staticmethod
    def update_team(team: Team, **kwargs) -> Team:
        """
        更新团队信息

        Args:
            team: Team对象
            **kwargs: 要更新的字段

        Returns:
            更新后的Team对象
        """
        for key, value in kwargs.items():
            if hasattr(team, key):
                setattr(team, key, value)
        team.save()
        return team

    @staticmethod
    def delete_team(team: Team) -> bool:
        """
        删除团队

        Args:
            team: Team对象

        Returns:
            是否删除成功
        """
        try:
            team.delete_instance(recursive=True)
            return True
        except Exception:
            return False

    @staticmethod
    def add_member(
        team_id: str,
        user_id: str,
        role: str = TeamRole.MEMBER.value,
        invitation_status: str = "accepted",
    ) -> TeamMember:
        """
        添加团队成员

        Args:
            team_id: 团队ID
            user_id: 用户ID
            role: 成员角色
            invitation_status: 邀请状态

        Returns:
            创建的TeamMember对象
        """
        member = TeamMember(
            team_id=team_id,
            user_id=user_id,
            role=role,
            invitation_status=invitation_status,
        )
        if invitation_status == "accepted":
            from datetime import datetime
            member.joined_at = datetime.utcnow()
        member.save()
        return member

    @staticmethod
    def update_member_role(member: TeamMember, new_role: str) -> TeamMember:
        """
        更新成员角色

        Args:
            member: TeamMember对象
            new_role: 新角色

        Returns:
            更新后的TeamMember对象
        """
        member.role = new_role
        member.save()
        return member

    @staticmethod
    def update_invitation_status(
        member: TeamMember, status: str
    ) -> TeamMember:
        """
        更新邀请状态

        Args:
            member: TeamMember对象
            status: 新状态 (accepted, declined)

        Returns:
            更新后的TeamMember对象
        """
        member.invitation_status = status
        if status == "accepted":
            from datetime import datetime
            member.joined_at = datetime.utcnow()
        member.save()
        return member

    @staticmethod
    def remove_member(member: TeamMember) -> bool:
        """
        移除团队成员

        Args:
            member: TeamMember对象

        Returns:
            是否移除成功
        """
        try:
            member.delete_instance()
            return True
        except Exception:
            return False

    @staticmethod
    def list_teams(
        tenant_id: Optional[str] = None,
        page: int = 1,
        per_page: int = 20,
    ) -> tuple[List[Team], int]:
        """
        列出团队(分页)

        Args:
            tenant_id: 租户ID (可选,用于过滤)
            page: 页码
            per_page: 每页数量

        Returns:
            (Team列表, 总数)
        """
        query = Team.select()
        if tenant_id:
            query = query.where(Team.tenant_id == tenant_id)

        total = query.count()
        teams = list(
            query.order_by(Team.created_at.desc())
            .paginate(page, per_page)
        )

        return teams, total
