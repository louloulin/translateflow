import React, { useState, useEffect } from 'react';
import { useI18n } from '@/contexts/I18nContext';
import TeamService, { Team, TeamMember, TeamQuota, CreateTeamRequest, InviteMemberRequest } from '@/services/TeamService';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import {
  Users,
  Plus,
  MoreVertical,
  UserPlus,
  Settings,
  Trash2,
  Crown,
  Shield,
  User,
  Mail,
  Clock,
  CheckCircle,
  XCircle,
} from 'lucide-react';
import { useToast } from '@/components/ui/use-toast';
import { cn } from '@/lib/utils';

export const Teams: React.FC = () => {
  const { t } = useI18n();
  const { toast } = useToast();
  const [teams, setTeams] = useState<Team[]>([]);
  const [selectedTeam, setSelectedTeam] = useState<Team | null>(null);
  const [members, setMembers] = useState<TeamMember[]>([]);
  const [quota, setQuota] = useState<TeamQuota | null>(null);
  const [loading, setLoading] = useState(true);
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [inviteDialogOpen, setInviteDialogOpen] = useState(false);
  const [detailsDialogOpen, setDetailsDialogOpen] = useState(false);

  // Form states
  const [newTeamName, setNewTeamName] = useState('');
  const [newTeamSlug, setNewTeamSlug] = useState('');
  const [newTeamDescription, setNewTeamDescription] = useState('');
  const [inviteEmail, setInviteEmail] = useState('');
  const [inviteRole, setInviteRole] = useState<'admin' | 'member'>('member');

  // Load teams
  useEffect(() => {
    loadTeams();
  }, []);

  const loadTeams = async () => {
    try {
      setLoading(true);
      const data = await TeamService.getMyTeams();
      setTeams(data);
    } catch (error: any) {
      toast({
        title: t('teams_load_error') || '加载团队失败',
        description: error.message || 'Failed to load teams',
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  };

  const loadTeamDetails = async (teamId: string) => {
    try {
      const [teamData, membersData, quotaData] = await Promise.all([
        TeamService.getTeam(teamId),
        TeamService.getTeamMembers(teamId),
        TeamService.getTeamQuota(teamId),
      ]);
      setSelectedTeam(teamData);
      setMembers(membersData);
      setQuota(quotaData);
      setDetailsDialogOpen(true);
    } catch (error: any) {
      toast({
        title: t('team_details_error') || '加载团队详情失败',
        description: error.message || 'Failed to load team details',
        variant: 'destructive',
      });
    }
  };

  const handleCreateTeam = async () => {
    if (!newTeamName || !newTeamSlug) {
      toast({
        title: t('validation_error') || '验证错误',
        description: t('team_name_slug_required') || '团队名称和标识不能为空',
        variant: 'destructive',
      });
      return;
    }

    try {
      const data: CreateTeamRequest = {
        name: newTeamName,
        slug: newTeamSlug,
        description: newTeamDescription || undefined,
      };
      await TeamService.createTeam(data);
      toast({
        title: t('team_created') || '团队创建成功',
        description: t('team_created_success') || '新团队已成功创建',
      });
      setCreateDialogOpen(false);
      resetCreateForm();
      loadTeams();
    } catch (error: any) {
      toast({
        title: t('team_create_error') || '创建团队失败',
        description: error.message || 'Failed to create team',
        variant: 'destructive',
      });
    }
  };

  const handleInviteMember = async () => {
    if (!selectedTeam || !inviteEmail) {
      toast({
        title: t('validation_error') || '验证错误',
        description: t('email_required') || '邮箱地址不能为空',
        variant: 'destructive',
      });
      return;
    }

    try {
      const data: InviteMemberRequest = {
        email: inviteEmail,
        role: inviteRole,
      };
      await TeamService.inviteMember(selectedTeam.id, data);
      toast({
        title: t('invitation_sent') || '邀请已发送',
        description: t('invitation_sent_success') || '团队邀请已发送到邮箱',
      });
      setInviteDialogOpen(false);
      resetInviteForm();
      loadTeamDetails(selectedTeam.id);
    } catch (error: any) {
      toast({
        title: t('invitation_error') || '发送邀请失败',
        description: error.message || 'Failed to send invitation',
        variant: 'destructive',
      });
    }
  };

  const handleRemoveMember = async (memberUserId: string) => {
    if (!selectedTeam) return;

    try {
      await TeamService.removeMember(selectedTeam.id, memberUserId);
      toast({
        title: t('member_removed') || '成员已移除',
        description: t('member_removed_success') || '团队成员已成功移除',
      });
      loadTeamDetails(selectedTeam.id);
    } catch (error: any) {
      toast({
        title: t('remove_member_error') || '移除成员失败',
        description: error.message || 'Failed to remove member',
        variant: 'destructive',
      });
    }
  };

  const handleDeleteTeam = async (teamId: string) => {
    if (!confirm(t('confirm_delete_team') || '确定要删除这个团队吗？此操作不可撤销。')) {
      return;
    }

    try {
      await TeamService.deleteTeam(teamId);
      toast({
        title: t('team_deleted') || '团队已删除',
        description: t('team_deleted_success') || '团队已成功删除',
      });
      loadTeams();
    } catch (error: any) {
      toast({
        title: t('delete_team_error') || '删除团队失败',
        description: error.message || 'Failed to delete team',
        variant: 'destructive',
      });
    }
  };

  const resetCreateForm = () => {
    setNewTeamName('');
    setNewTeamSlug('');
    setNewTeamDescription('');
  };

  const resetInviteForm = () => {
    setInviteEmail('');
    setInviteRole('member');
  };

  const getRoleIcon = (role: string) => {
    switch (role) {
      case 'owner':
        return <Crown className="h-4 w-4 text-yellow-500" />;
      case 'admin':
        return <Shield className="h-4 w-4 text-blue-500" />;
      default:
        return <User className="h-4 w-4 text-gray-500" />;
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'accepted':
        return (
          <Badge variant="default" className="bg-green-500/10 text-green-500 border-green-500/20">
            <CheckCircle className="h-3 w-3 mr-1" />
            {t('status_accepted') || '已接受'}
          </Badge>
        );
      case 'pending':
        return (
          <Badge variant="secondary" className="bg-yellow-500/10 text-yellow-500 border-yellow-500/20">
            <Clock className="h-3 w-3 mr-1" />
            {t('status_pending') || '待接受'}
          </Badge>
        );
      case 'declined':
        return (
          <Badge variant="destructive" className="bg-red-500/10 text-red-500 border-red-500/20">
            <XCircle className="h-3 w-3 mr-1" />
            {t('status_declined') || '已拒绝'}
          </Badge>
        );
      default:
        return null;
    }
  };

  return (
    <div className="container mx-auto p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">{t('teams_title') || '团队管理'}</h1>
          <p className="text-muted-foreground mt-1">
            {t('teams_description') || '管理您的团队和成员'}
          </p>
        </div>
        <Button onClick={() => setCreateDialogOpen(true)}>
          <Plus className="h-4 w-4 mr-2" />
          {t('create_team') || '创建团队'}
        </Button>
      </div>

      {loading ? (
        <div className="text-center py-12">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto" />
          <p className="mt-4 text-muted-foreground">{t('loading') || '加载中...'}</p>
        </div>
      ) : teams.length === 0 ? (
        <Card>
          <CardContent className="py-12">
            <div className="text-center">
              <Users className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
              <h3 className="text-lg font-semibold mb-2">
                {t('no_teams') || '还没有团队'}
              </h3>
              <p className="text-muted-foreground mb-4">
                {t('create_first_team') || '创建您的第一个团队开始协作'}
              </p>
              <Button onClick={() => setCreateDialogOpen(true)}>
                <Plus className="h-4 w-4 mr-2" />
                {t('create_team') || '创建团队'}
              </Button>
            </div>
          </CardContent>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {teams.map((team) => (
            <Card key={team.id} className="hover:shadow-lg transition-shadow cursor-pointer">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="h-10 w-10 rounded-lg bg-primary/10 flex items-center justify-center">
                      <Users className="h-5 w-5 text-primary" />
                    </div>
                    <div>
                      <CardTitle className="text-lg">{team.name}</CardTitle>
                      <CardDescription className="text-xs">{team.slug}</CardDescription>
                    </div>
                  </div>
                  <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                      <Button variant="ghost" size="icon">
                        <MoreVertical className="h-4 w-4" />
                      </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="end">
                      <DropdownMenuItem onClick={() => loadTeamDetails(team.id)}>
                        <Settings className="h-4 w-4 mr-2" />
                        {t('manage_team') || '管理团队'}
                      </DropdownMenuItem>
                      {team.user_role === 'owner' && (
                        <>
                          <DropdownMenuSeparator />
                          <DropdownMenuItem
                            className="text-red-600"
                            onClick={() => handleDeleteTeam(team.id)}
                          >
                            <Trash2 className="h-4 w-4 mr-2" />
                            {t('delete_team') || '删除团队'}
                          </DropdownMenuItem>
                        </>
                      )}
                    </DropdownMenuContent>
                  </DropdownMenu>
                </div>
              </CardHeader>
              <CardContent>
                {team.description && (
                  <p className="text-sm text-muted-foreground mb-4 line-clamp-2">
                    {team.description}
                  </p>
                )}
                <div className="flex items-center justify-between text-sm">
                  <div className="flex items-center gap-2">
                    <Users className="h-4 w-4 text-muted-foreground" />
                    <span>{team.member_count || 0} {t('members') || '成员'}</span>
                  </div>
                  <Badge variant="outline">
                    {team.user_role === 'owner' && (t('role_owner') || '所有者')}
                    {team.user_role === 'admin' && (t('role_admin') || '管理员')}
                    {team.user_role === 'member' && (t('role_member') || '成员')}
                  </Badge>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* Create Team Dialog */}
      <Dialog open={createDialogOpen} onOpenChange={setCreateDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{t('create_new_team') || '创建新团队'}</DialogTitle>
            <DialogDescription>
              {t('create_team_description') || '创建一个新团队开始协作'}
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="team-name">{t('team_name') || '团队名称'}</Label>
              <Input
                id="team-name"
                placeholder={t('team_name_placeholder') || '我的翻译团队'}
                value={newTeamName}
                onChange={(e) => setNewTeamName(e.target.value)}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="team-slug">{t('team_slug') || '团队标识'}</Label>
              <Input
                id="team-slug"
                placeholder={t('team_slug_placeholder') || 'my-translation-team'}
                value={newTeamSlug}
                onChange={(e) => setNewTeamSlug(e.target.value.toLowerCase().replace(/\s+/g, '-'))}
              />
              <p className="text-xs text-muted-foreground">
                {t('team_slug_help') || '仅限小写字母、数字和连字符'}
              </p>
            </div>
            <div className="space-y-2">
              <Label htmlFor="team-description">{t('team_description_optional') || '团队描述 (可选)'}</Label>
              <Textarea
                id="team-description"
                placeholder={t('team_description_placeholder') || '描述团队的目标和用途'}
                value={newTeamDescription}
                onChange={(e) => setNewTeamDescription(e.target.value)}
                rows={3}
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setCreateDialogOpen(false)}>
              {t('cancel') || '取消'}
            </Button>
            <Button onClick={handleCreateTeam}>
              {t('create') || '创建'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Team Details Dialog */}
      <Dialog open={detailsDialogOpen} onOpenChange={setDetailsDialogOpen}>
        <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>{selectedTeam?.name || t('team_details') || '团队详情'}</DialogTitle>
            <DialogDescription>
              {t('manage_team_members') || '管理团队成员和设置'}
            </DialogDescription>
          </DialogHeader>

          {quota && (
            <div className="space-y-2 py-4">
              <div className="flex items-center justify-between">
                <Label>{t('team_quota') || '团队配额'}</Label>
                <span className="text-sm text-muted-foreground">
                  {quota.current_members} / {quota.is_unlimited ? '∞' : quota.max_members}
                </span>
              </div>
              <Progress
                value={quota.is_unlimited ? 0 : quota.usage_percentage}
                className="h-2"
              />
              <p className="text-xs text-muted-foreground">
                {t('team_plan') || '订阅计划'}: {quota.plan} • {quota.remaining_slots} {t('slots_remaining') || '个名额剩余'}
              </p>
            </div>
          )}

          <div className="space-y-4 py-4">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-semibold">{t('team_members') || '团队成员'}</h3>
              {selectedTeam && (selectedTeam.user_role === 'owner' || selectedTeam.user_role === 'admin') && (
                <Button
                  size="sm"
                  onClick={() => setInviteDialogOpen(true)}
                  disabled={quota && !quota.is_unlimited && quota.remaining_slots <= 0}
                >
                  <UserPlus className="h-4 w-4 mr-2" />
                  {t('invite_member') || '邀请成员'}
                </Button>
              )}
            </div>

            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>{t('member') || '成员'}</TableHead>
                  <TableHead>{t('role') || '角色'}</TableHead>
                  <TableHead>{t('status') || '状态'}</TableHead>
                  <TableHead>{t('joined_date') || '加入时间'}</TableHead>
                  <TableHead className="text-right">{t('actions') || '操作'}</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {members.map((member) => (
                  <TableRow key={member.id}>
                    <TableCell>
                      <div className="flex items-center gap-3">
                        <div className="h-8 w-8 rounded-full bg-primary/10 flex items-center justify-center">
                          <User className="h-4 w-4" />
                        </div>
                        <div>
                          <div className="font-medium">
                            {member.user?.full_name || member.user?.username || member.user?.email}
                          </div>
                          <div className="text-xs text-muted-foreground">
                            {member.user?.email}
                          </div>
                        </div>
                      </div>
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-2">
                        {getRoleIcon(member.role)}
                        <span className="capitalize">{member.role}</span>
                      </div>
                    </TableCell>
                    <TableCell>{getStatusBadge(member.invitation_status)}</TableCell>
                    <TableCell className="text-sm text-muted-foreground">
                      {member.joined_at
                        ? new Date(member.joined_at).toLocaleDateString()
                        : '-'}
                    </TableCell>
                    <TableCell className="text-right">
                      {selectedTeam && selectedTeam.user_role === 'owner' && member.role !== 'owner' && (
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleRemoveMember(member.user_id)}
                        >
                          <Trash2 className="h-4 w-4 text-red-500" />
                        </Button>
                      )}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>

          <DialogFooter>
            <Button onClick={() => setDetailsDialogOpen(false)}>
              {t('close') || '关闭'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Invite Member Dialog */}
      <Dialog open={inviteDialogOpen} onOpenChange={setInviteDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{t('invite_team_member') || '邀请团队成员'}</DialogTitle>
            <DialogDescription>
              {t('invite_member_description') || '通过邮箱邀请新成员加入团队'}
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="invite-email">{t('email_address') || '邮箱地址'}</Label>
              <Input
                id="invite-email"
                type="email"
                placeholder={t('email_placeholder') || 'member@example.com'}
                value={inviteEmail}
                onChange={(e) => setInviteEmail(e.target.value)}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="invite-role">{t('member_role') || '成员角色'}</Label>
              <select
                id="invite-role"
                className="w-full px-3 py-2 border rounded-md"
                value={inviteRole}
                onChange={(e) => setInviteRole(e.target.value as 'admin' | 'member')}
              >
                <option value="member">{t('role_member') || '普通成员'}</option>
                <option value="admin">{t('role_admin') || '管理员'}</option>
              </select>
              <p className="text-xs text-muted-foreground">
                {t('role_help') || '管理员可以邀请和管理成员'}
              </p>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setInviteDialogOpen(false)}>
              {t('cancel') || '取消'}
            </Button>
            <Button onClick={handleInviteMember}>
              <Mail className="h-4 w-4 mr-2" />
              {t('send_invitation') || '发送邀请'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};
