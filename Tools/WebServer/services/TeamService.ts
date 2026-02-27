/**
 * Team Management Service
 * 团队管理API服务
 */

const API_BASE = '/api/v1';

// Helper function for API calls
async function get<T>(url: string): Promise<T> {
  const token = localStorage.getItem('access_token');
  const res = await fetch(url, {
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
  });

  if (!res.ok) {
    const error = await res.json();
    throw new Error(error.detail || error.message || 'Request failed');
  }

  return res.json();
}

async function post<T>(url: string, data?: any): Promise<T> {
  const token = localStorage.getItem('access_token');
  const res = await fetch(url, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
    body: data ? JSON.stringify(data) : undefined,
  });

  if (!res.ok) {
    const error = await res.json();
    throw new Error(error.detail || error.message || 'Request failed');
  }

  return res.json();
}

async function put<T>(url: string, data?: any): Promise<T> {
  const token = localStorage.getItem('access_token');
  const res = await fetch(url, {
    method: 'PUT',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
    body: data ? JSON.stringify(data) : undefined,
  });

  if (!res.ok) {
    const error = await res.json();
    throw new Error(error.detail || error.message || 'Request failed');
  }

  return res.json();
}

async function del(url: string): Promise<void> {
  const token = localStorage.getItem('access_token');
  const res = await fetch(url, {
    method: 'DELETE',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
  });

  if (!res.ok) {
    const error = await res.json();
    throw new Error(error.detail || error.message || 'Request failed');
  }
}

export interface Team {
  id: string;
  name: string;
  slug: string;
  description?: string;
  owner_id: string;
  tenant_id: string;
  max_members: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  member_count?: number;
  user_role?: 'owner' | 'admin' | 'member';
}

export interface TeamMember {
  id: string;
  team_id: string;
  user_id: string;
  role: 'owner' | 'admin' | 'member';
  invitation_status: 'pending' | 'accepted' | 'declined';
  invitation_token?: string;
  invited_at: string;
  joined_at?: string;
  user?: {
    id: string;
    email: string;
    username: string;
    full_name?: string;
    avatar_url?: string;
  };
}

export interface TeamQuota {
  current_members: number;
  pending_invites: number;
  total_reserved: number;
  max_members: number;
  remaining_slots: number;
  usage_percentage: number;
  plan: string;
  is_unlimited: boolean;
}

export interface CreateTeamRequest {
  name: string;
  slug: string;
  description?: string;
}

export interface UpdateTeamRequest {
  name?: string;
  description?: string;
  settings?: Record<string, any>;
}

export interface InviteMemberRequest {
  email: string;
  role: 'admin' | 'member';
}

export interface UpdateMemberRoleRequest {
  new_role: 'admin' | 'member';
}

export interface AcceptInvitationRequest {
  token: string;
}

export interface DeclineInvitationRequest {
  token: string;
}

class TeamService {
  /**
   * 创建团队
   */
  async createTeam(data: CreateTeamRequest): Promise<Team> {
    return post<Team>(`${API_BASE}/teams`, data);
  }

  /**
   * 获取我的团队列表
   */
  async getMyTeams(): Promise<Team[]> {
    return get<Team[]>(`${API_BASE}/teams`);
  }

  /**
   * 获取团队详情
   */
  async getTeam(teamId: string): Promise<Team> {
    return get<Team>(`${API_BASE}/teams/${teamId}`);
  }

  /**
   * 更新团队信息
   */
  async updateTeam(teamId: string, data: UpdateTeamRequest): Promise<Team> {
    return put<Team>(`${API_BASE}/teams/${teamId}`, data);
  }

  /**
   * 删除团队
   */
  async deleteTeam(teamId: string): Promise<void> {
    return del(`${API_BASE}/teams/${teamId}`);
  }

  /**
   * 获取团队成员列表
   */
  async getTeamMembers(teamId: string): Promise<TeamMember[]> {
    return get<TeamMember[]>(`${API_BASE}/teams/${teamId}/members`);
  }

  /**
   * 邀请成员
   */
  async inviteMember(teamId: string, data: InviteMemberRequest): Promise<TeamMember> {
    return post<TeamMember>(`${API_BASE}/teams/${teamId}/members`, data);
  }

  /**
   * 更新成员角色
   */
  async updateMemberRole(
    teamId: string,
    memberUserId: string,
    data: UpdateMemberRoleRequest
  ): Promise<TeamMember> {
    return put<TeamMember>(`${API_BASE}/teams/${teamId}/members/${memberUserId}`, data);
  }

  /**
   * 移除成员
   */
  async removeMember(teamId: string, memberUserId: string): Promise<void> {
    return del(`${API_BASE}/teams/${teamId}/members/${memberUserId}`);
  }

  /**
   * 接受邀请
   */
  async acceptInvitation(data: AcceptInvitationRequest): Promise<TeamMember> {
    return post<TeamMember>(`${API_BASE}/teams/accept`, data);
  }

  /**
   * 拒绝邀请
   */
  async declineInvitation(data: DeclineInvitationRequest): Promise<void> {
    return post<void>(`${API_BASE}/teams/decline`, data);
  }

  /**
   * 获取团队配额状态
   */
  async getTeamQuota(teamId: string): Promise<TeamQuota> {
    return get<TeamQuota>(`${API_BASE}/teams/${teamId}/quota`);
  }
}

export default new TeamService();
