"""
Team management service module.

This module provides team management functionality including:
- Team creation and management
- Member invitation and role assignment
- Team settings and permissions
"""

from .team_manager import TeamManager
from .team_repository import TeamRepository

__all__ = ["TeamManager", "TeamRepository"]
