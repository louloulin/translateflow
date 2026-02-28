import React, { useState, useEffect } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { useI18n } from '@/contexts/I18nContext';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { AuthService, User } from '@/services/AuthService';
import { Save, Lock, History, User as UserIcon, Mail, Calendar } from 'lucide-react';

export const Profile: React.FC = () => {
  const { t } = useI18n();
  const { user, token, refreshUser } = useAuth();
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [success, setSuccess] = useState('');
  const [error, setError] = useState('');

  // Profile form state
  const [profileData, setProfileData] = useState({
    username: '',
    email: '',
    avatar_url: '',
  });

  // Password change state
  const [passwordData, setPasswordData] = useState({
    old_password: '',
    new_password: '',
    confirm_password: '',
  });

  // Login history state
  const [loginHistory, setLoginHistory] = useState<any[]>([]);
  const [historyLoading, setHistoryLoading] = useState(false);

  useEffect(() => {
    if (user) {
      setProfileData({
        username: user.username || '',
        email: user.email || '',
        avatar_url: user.avatar_url || '',
      });
    }
  }, [user]);

  const handleProfileSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!token) return;

    setSaving(true);
    setError('');
    setSuccess('');

    try {
      const updatedUser = await AuthService.updateUserProfile(token, {
        username: profileData.username,
        avatar_url: profileData.avatar_url,
      });
      await refreshUser();
      setSuccess(t('profile_update_success') || 'Profile updated successfully');
    } catch (err: any) {
      setError(err.message || 'Failed to update profile');
    } finally {
      setSaving(false);
    }
  };

  const handlePasswordSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!token) return;

    if (passwordData.new_password !== passwordData.confirm_password) {
      setError(t('auth_password_mismatch') || 'Passwords do not match');
      return;
    }

    if (passwordData.new_password.length < 6) {
      setError(t('auth_password_too_short') || 'Password must be at least 6 characters');
      return;
    }

    setSaving(true);
    setError('');
    setSuccess('');

    try {
      await AuthService.updateUserPassword(
        token,
        passwordData.old_password,
        passwordData.new_password
      );
      setSuccess(t('profile_password_success') || 'Password updated successfully');
      setPasswordData({ old_password: '', new_password: '', confirm_password: '' });
    } catch (err: any) {
      setError(err.message || 'Failed to update password');
    } finally {
      setSaving(false);
    }
  };

  const loadLoginHistory = async () => {
    if (!token) return;

    setHistoryLoading(true);
    try {
      const history = await AuthService.getLoginHistory(token);
      setLoginHistory(history);
    } catch (err) {
      console.error('Failed to load login history:', err);
    } finally {
      setHistoryLoading(false);
    }
  };

  if (!user) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-900 to-slate-800 p-4">
        <Card className="w-full max-w-md">
          <CardHeader className="text-center">
            <CardTitle>{t('auth_login_required') || 'Login Required'}</CardTitle>
            <CardDescription>
              {t('auth_login_required_desc') || 'Please login to view your profile'}
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Button className="w-full" onClick={() => window.location.hash = '/login'}>
              {t('auth_login') || 'Login'}
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 to-slate-800 p-6">
      <div className="max-w-4xl mx-auto">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-white">{t('profile_title') || 'My Profile'}</h1>
          <p className="text-slate-400 mt-2">
            {t('profile_description') || 'Manage your account settings and preferences'}
          </p>
        </div>

        {error && (
          <div className="bg-destructive/10 text-destructive p-3 rounded-md mb-4">
            {error}
          </div>
        )}

        {success && (
          <div className="bg-green-500/10 text-green-500 p-3 rounded-md mb-4">
            {success}
          </div>
        )}

        <Tabs defaultValue="profile" className="w-full">
          <TabsList className="w-full justify-start bg-slate-800 border-slate-700">
            <TabsTrigger value="profile" className="text-slate-300 data-[state=active]:bg-slate-700 data-[state=active]:text-white">
              <UserIcon className="w-4 h-4 mr-2" />
              {t('profile_tab_profile') || 'Profile'}
            </TabsTrigger>
            <TabsTrigger value="security" className="text-slate-300 data-[state=active]:bg-slate-700 data-[state=active]:text-white">
              <Lock className="w-4 h-4 mr-2" />
              {t('profile_tab_security') || 'Security'}
            </TabsTrigger>
            <TabsTrigger value="history" className="text-slate-300 data-[state=active]:bg-slate-700 data-[state=active]:text-white">
              <History className="w-4 h-4 mr-2" />
              {t('profile_tab_history') || 'Login History'}
            </TabsTrigger>
          </TabsList>

          <TabsContent value="profile">
            <Card className="bg-slate-800 border-slate-700">
              <CardHeader>
                <CardTitle className="text-white">{t('profile_info') || 'Profile Information'}</CardTitle>
                <CardDescription className="text-slate-400">
                  {t('profile_info_desc') || 'Update your personal information'}
                </CardDescription>
              </CardHeader>
              <CardContent>
                <form onSubmit={handleProfileSubmit} className="space-y-4">
                  <div className="space-y-2">
                    <label className="text-sm font-medium text-slate-300">
                      {t('auth_username') || 'Username'}
                    </label>
                    <Input
                      value={profileData.username}
                      onChange={(e) => setProfileData({ ...profileData, username: e.target.value })}
                      placeholder={t('auth_username') || 'Username'}
                      className="bg-slate-700 border-slate-600 text-white"
                    />
                  </div>

                  <div className="space-y-2">
                    <label className="text-sm font-medium text-slate-300">
                      {t('auth_email') || 'Email'}
                    </label>
                    <Input
                      value={profileData.email}
                      disabled
                      className="bg-slate-700 border-slate-600 text-slate-400"
                    />
                    <p className="text-xs text-slate-500">
                      {t('profile_email_note') || 'Contact support to change your email'}
                    </p>
                  </div>

                  <div className="space-y-2">
                    <label className="text-sm font-medium text-slate-300">
                      {t('profile_avatar_url') || 'Avatar URL'}
                    </label>
                    <Input
                      value={profileData.avatar_url}
                      onChange={(e) => setProfileData({ ...profileData, avatar_url: e.target.value })}
                      placeholder="https://example.com/avatar.jpg"
                      className="bg-slate-700 border-slate-600 text-white"
                    />
                  </div>

                  <div className="pt-4 border-t border-slate-700">
                    <div className="flex items-center gap-4 text-sm text-slate-400">
                      <div className="flex items-center gap-2">
                        <Calendar className="w-4 h-4" />
                        <span>{t('profile_created_at') || 'Created'}: {user.created_at ? new Date(user.created_at).toLocaleDateString() : 'N/A'}</span>
                      </div>
                      {user.last_login_at && (
                        <div className="flex items-center gap-2">
                          <History className="w-4 h-4" />
                          <span>{t('profile_last_login') || 'Last login'}: {new Date(user.last_login_at).toLocaleDateString()}</span>
                        </div>
                      )}
                    </div>
                  </div>

                  <Button type="submit" disabled={saving} className="w-full">
                    <Save className="w-4 h-4 mr-2" />
                    {saving ? (t('common_saving') || 'Saving...') : (t('common_save') || 'Save Changes')}
                  </Button>
                </form>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="security">
            <Card className="bg-slate-800 border-slate-700">
              <CardHeader>
                <CardTitle className="text-white">{t('profile_security') || 'Security'}</CardTitle>
                <CardDescription className="text-slate-400">
                  {t('profile_security_desc') || 'Change your password'}
                </CardDescription>
              </CardHeader>
              <CardContent>
                <form onSubmit={handlePasswordSubmit} className="space-y-4">
                  <div className="space-y-2">
                    <label className="text-sm font-medium text-slate-300">
                      {t('profile_current_password') || 'Current Password'}
                    </label>
                    <Input
                      type="password"
                      value={passwordData.old_password}
                      onChange={(e) => setPasswordData({ ...passwordData, old_password: e.target.value })}
                      placeholder={t('profile_current_password') || 'Current Password'}
                      className="bg-slate-700 border-slate-600 text-white"
                    />
                  </div>

                  <div className="space-y-2">
                    <label className="text-sm font-medium text-slate-300">
                      {t('profile_new_password') || 'New Password'}
                    </label>
                    <Input
                      type="password"
                      value={passwordData.new_password}
                      onChange={(e) => setPasswordData({ ...passwordData, new_password: e.target.value })}
                      placeholder={t('profile_new_password') || 'New Password'}
                      className="bg-slate-700 border-slate-600 text-white"
                    />
                  </div>

                  <div className="space-y-2">
                    <label className="text-sm font-medium text-slate-300">
                      {t('profile_confirm_password') || 'Confirm New Password'}
                    </label>
                    <Input
                      type="password"
                      value={passwordData.confirm_password}
                      onChange={(e) => setPasswordData({ ...passwordData, confirm_password: e.target.value })}
                      placeholder={t('profile_confirm_password') || 'Confirm New Password'}
                      className="bg-slate-700 border-slate-600 text-white"
                    />
                  </div>

                  <Button type="submit" disabled={saving} className="w-full">
                    <Lock className="w-4 h-4 mr-2" />
                    {saving ? (t('common_saving') || 'Saving...') : (t('profile_change_password') || 'Change Password')}
                  </Button>
                </form>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="history">
            <Card className="bg-slate-800 border-slate-700">
              <CardHeader>
                <CardTitle className="text-white">{t('profile_login_history') || 'Login History'}</CardTitle>
                <CardDescription className="text-slate-400">
                  {t('profile_login_history_desc') || 'View your recent login activity'}
                </CardDescription>
              </CardHeader>
              <CardContent>
                {!loginHistory.length ? (
                  <div className="text-center py-8">
                    <Button variant="outline" onClick={loadLoginHistory} disabled={historyLoading}>
                      {historyLoading ? (t('common_loading') || 'Loading...') : (t('profile_load_history') || 'Load History')}
                    </Button>
                  </div>
                ) : (
                  <div className="space-y-3">
                    {loginHistory.map((item, index) => (
                      <div key={index} className="flex items-center justify-between p-3 bg-slate-700 rounded-lg">
                        <div className="flex items-center gap-3">
                          <History className="w-5 h-5 text-slate-400" />
                          <div>
                            <p className="text-white font-medium">{item.ip_address || 'Unknown IP'}</p>
                            <p className="text-sm text-slate-400">{item.user_agent || 'Unknown Browser'}</p>
                          </div>
                        </div>
                        <div className="text-right">
                          <p className="text-sm text-slate-300">
                            {item.created_at ? new Date(item.created_at).toLocaleString() : 'N/A'}
                          </p>
                          <p className={`text-xs ${item.success ? 'text-green-400' : 'text-red-400'}`}>
                            {item.success ? (t('profile_success') || 'Success') : (t('profile_failed') || 'Failed')}
                          </p>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
};

export default Profile;
