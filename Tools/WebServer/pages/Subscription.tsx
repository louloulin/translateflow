import React, { useState, useEffect } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { useI18n } from '@/contexts/I18nContext';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { AuthService } from '@/services/AuthService';
import { CreditCard, Receipt, BarChart3, Zap, Check, X, Download, Loader2 } from 'lucide-react';

interface SubscriptionPlan {
  plan: string;
  daily_characters: number;
  monthly_price: number;
  yearly_price?: number;
  features: string[];
}

export const Subscription: React.FC = () => {
  const { t } = useI18n();
  const { user, token } = useAuth();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  // Data state
  const [plans, setPlans] = useState<SubscriptionPlan[]>([]);
  const [currentSubscription, setCurrentSubscription] = useState<any>(null);
  const [usage, setUsage] = useState<any>(null);
  const [invoices, setInvoices] = useState<any[]>([]);

  // Tab state
  const [activeTab, setActiveTab] = useState('plans');

  // Plan features mapping
  const planFeatures: Record<string, string[]> = {
    free: ['1000 chars/day', 'Basic formats', 'No API access'],
    starter: ['50000 chars/day', 'All formats', '1 user', 'Email support'],
    pro: ['500000 chars/day', 'All formats', '5 users', 'API access', 'Priority support'],
    enterprise: ['Unlimited', 'All formats', 'Unlimited users', 'API access', 'Priority support', 'Custom quotas'],
  };

  useEffect(() => {
    loadData();
  }, [token]);

  const loadData = async () => {
    setLoading(true);
    setError('');

    try {
      // Load plans (no auth required)
      const plansData = await AuthService.getSubscriptionPlans();
      setPlans(plansData);

      // Load subscription, usage, and invoices (auth required)
      if (token) {
        try {
          const subData = await AuthService.getCurrentSubscription(token);
          setCurrentSubscription(subData);
        } catch (e) {
          // User might not have a subscription yet
          setCurrentSubscription(null);
        }

        try {
          const usageData = await AuthService.getUsageCurrent(token);
          setUsage(usageData);
        } catch (e) {
          setUsage(null);
        }

        try {
          const invoiceData = await AuthService.getInvoices(token);
          setInvoices(invoiceData);
        } catch (e) {
          setInvoices([]);
        }
      }
    } catch (err: any) {
      setError(err.message || 'Failed to load data');
    } finally {
      setLoading(false);
    }
  };

  const handleUpgrade = async (plan: string) => {
    if (!token) {
      window.location.hash = '/login';
      return;
    }

    if (!confirm(t('subscription_confirm_upgrade') || 'Are you sure you want to upgrade to this plan?')) {
      return;
    }

    setLoading(true);
    setError('');
    setSuccess('');

    try {
      await AuthService.createSubscription(token, plan);
      setSuccess(t('subscription_update_success') || 'Subscription updated successfully');
      await loadData();
    } catch (err: any) {
      setError(err.message || 'Failed to update subscription');
    } finally {
      setLoading(false);
    }
  };

  const handleCancelSubscription = async () => {
    if (!token) return;

    if (!confirm(t('subscription_confirm_cancel') || 'Are you sure you want to cancel your subscription?')) {
      return;
    }

    setLoading(true);
    setError('');
    setSuccess('');

    try {
      await AuthService.cancelSubscription(token);
      setSuccess(t('subscription_update_success') || 'Subscription cancelled successfully');
      await loadData();
    } catch (err: any) {
      setError(err.message || 'Failed to cancel subscription');
    } finally {
      setLoading(false);
    }
  };

  const handleDownloadInvoice = async (invoiceId: string) => {
    if (!token) return;

    try {
      const blob = await AuthService.getInvoicePdf(token, invoiceId);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `invoice-${invoiceId}.pdf`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (err: any) {
      setError(err.message || 'Failed to download invoice');
    }
  };

  const getPlanDisplayName = (plan: string) => {
    const names: Record<string, string> = {
      free: t('subscription_plan_free') || 'Free',
      starter: t('subscription_plan_starter') || 'Starter',
      pro: t('subscription_plan_pro') || 'Pro',
      enterprise: t('subscription_plan_enterprise') || 'Enterprise',
    };
    return names[plan] || plan;
  };

  const formatChars = (chars: number) => {
    if (chars === -1) return t('subscription_unlimited') || 'Unlimited';
    if (chars >= 1000) return `${(chars / 1000).toFixed(0)}K`;
    return chars.toString();
  };

  if (!user) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-900 to-slate-800 p-4">
        <Card className="w-full max-w-md">
          <CardHeader className="text-center">
            <CardTitle>{t('auth_login_required') || 'Login Required'}</CardTitle>
            <CardDescription>
              {t('auth_login_required_desc') || 'Please login to view your subscription'}
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
      <div className="max-w-6xl mx-auto">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-white">{t('subscription_title') || 'Subscription Management'}</h1>
          <p className="text-slate-400 mt-2">
            {t('subscription_description') || 'Manage your subscription plan and payment methods'}
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

        {loading && (
          <div className="flex items-center justify-center py-8">
            <Loader2 className="w-8 h-8 animate-spin text-slate-400" />
          </div>
        )}

        <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
          <TabsList className="w-full justify-start bg-slate-800 border-slate-700 mb-6">
            <TabsTrigger value="plans" className="text-slate-300 data-[state=active]:bg-slate-700 data-[state=active]:text-white">
              <Zap className="w-4 h-4 mr-2" />
              {t('subscription_plan') || 'Plans'}
            </TabsTrigger>
            <TabsTrigger value="usage" className="text-slate-300 data-[state=active]:bg-slate-700 data-[state=active]:text-white">
              <BarChart3 className="w-4 h-4 mr-2" />
              {t('subscription_usage') || 'Usage'}
            </TabsTrigger>
            <TabsTrigger value="invoices" className="text-slate-300 data-[state=active]:bg-slate-700 data-[state=active]:text-white">
              <Receipt className="w-4 h-4 mr-2" />
              {t('subscription_invoices') || 'Invoices'}
            </TabsTrigger>
          </TabsList>

          <TabsContent value="plans">
            {/* Current Plan */}
            {currentSubscription && (
              <Card className="bg-slate-800 border-slate-700 mb-6">
                <CardHeader>
                  <CardTitle className="text-white">{t('subscription_current_plan') || 'Current Plan'}</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-2xl font-bold text-white">
                        {getPlanDisplayName(currentSubscription.plan)}
                      </p>
                      <p className="text-slate-400">
                        {t('subscription_next_billing') || 'Next billing'}: {currentSubscription.next_billing_date || 'N/A'}
                      </p>
                    </div>
                    <div className="flex gap-2">
                      <Button variant="outline" onClick={() => setActiveTab('plans')}>
                        {t('subscription_change_plan') || 'Change Plan'}
                      </Button>
                      <Button variant="destructive" onClick={handleCancelSubscription} disabled={loading}>
                        {t('subscription_cancel') || 'Cancel'}
                      </Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Plan Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              {plans.map((plan) => {
                const isCurrentPlan = currentSubscription?.plan === plan.plan;
                const features = planFeatures[plan.plan] || [];

                return (
                  <Card
                    key={plan.plan}
                    className={`bg-slate-800 border-slate-700 ${isCurrentPlan ? 'ring-2 ring-blue-500' : ''}`}
                  >
                    <CardHeader>
                      <CardTitle className="text-white flex items-center justify-between">
                        {getPlanDisplayName(plan.plan)}
                        {isCurrentPlan && (
                          <span className="text-xs bg-blue-500 text-white px-2 py-1 rounded">
                            {t('subscription_current') || 'Current'}
                          </span>
                        )}
                      </CardTitle>
                      <CardDescription className="text-slate-400">
                        {plan.monthly_price === 0 ? (
                          <span className="text-3xl font-bold text-white">¥0</span>
                        ) : plan.monthly_price ? (
                          <span className="text-3xl font-bold text-white">¥{plan.monthly_price}</span>
                        ) : (
                          <span className="text-3xl font-bold text-white">{t('subscription_per_month')}</span>
                        )}
                        {plan.monthly_price !== null && plan.monthly_price !== 0 && (
                          <span className="text-slate-400">/{t('subscription_per_month') || 'month'}</span>
                        )}
                      </CardDescription>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-3 mb-6">
                        <div className="flex items-center text-slate-300">
                          <BarChart3 className="w-4 h-4 mr-2 text-slate-400" />
                          <span>
                            {formatChars(plan.daily_characters)} {t('subscription_characters') || 'chars'}/day
                          </span>
                        </div>
                        {features.map((feature, idx) => (
                          <div key={idx} className="flex items-center text-slate-300">
                            <Check className="w-4 h-4 mr-2 text-green-400" />
                            <span>{feature}</span>
                          </div>
                        ))}
                      </div>
                      <Button
                        className="w-full"
                        variant={isCurrentPlan ? 'outline' : 'default'}
                        disabled={isCurrentPlan || loading}
                        onClick={() => handleUpgrade(plan.plan)}
                      >
                        {isCurrentPlan
                          ? (t('subscription_current') || 'Current Plan')
                          : (t('subscription_upgrade') || 'Upgrade')}
                      </Button>
                    </CardContent>
                  </Card>
                );
              })}
            </div>
          </TabsContent>

          <TabsContent value="usage">
            <Card className="bg-slate-800 border-slate-700">
              <CardHeader>
                <CardTitle className="text-white">{t('usage_title') || 'Usage Statistics'}</CardTitle>
                <CardDescription className="text-slate-400">
                  {t('usage_description') || 'View your usage data'}
                </CardDescription>
              </CardHeader>
              <CardContent>
                {usage ? (
                  <div className="space-y-6">
                    {/* Daily Usage */}
                    <div>
                      <h3 className="text-lg font-semibold text-white mb-4">
                        {t('usage_daily') || 'Daily Usage'}
                      </h3>
                      <div className="bg-slate-700 rounded-lg p-4">
                        <div className="flex justify-between items-center mb-2">
                          <span className="text-slate-300">
                            {usage.daily_characters_used || 0} / {formatChars(usage.daily_limit || 0)} {t('subscription_characters') || 'chars'}
                          </span>
                          <span className="text-slate-300">
                            {usage.daily_percent || 0}%
                          </span>
                        </div>
                        <div className="w-full bg-slate-600 rounded-full h-2">
                          <div
                            className="bg-blue-500 h-2 rounded-full"
                            style={{ width: `${Math.min(usage.daily_percent || 0, 100)}%` }}
                          />
                        </div>
                      </div>
                    </div>

                    {/* Monthly Usage */}
                    <div>
                      <h3 className="text-lg font-semibold text-white mb-4">
                        {t('usage_monthly') || 'Monthly Usage'}
                      </h3>
                      <div className="bg-slate-700 rounded-lg p-4">
                        <div className="flex justify-between items-center mb-2">
                          <span className="text-slate-300">
                            {usage.monthly_characters_used || 0} / {formatChars(usage.monthly_limit || 0)} {t('subscription_characters') || 'chars'}
                          </span>
                          <span className="text-slate-300">
                            {usage.monthly_percent || 0}%
                          </span>
                        </div>
                        <div className="w-full bg-slate-600 rounded-full h-2">
                          <div
                            className="bg-green-500 h-2 rounded-full"
                            style={{ width: `${Math.min(usage.monthly_percent || 0, 100)}%` }}
                          />
                        </div>
                      </div>
                    </div>

                    {/* Reset Time */}
                    {usage.reset_time && (
                      <div className="text-sm text-slate-400">
                        {t('usage_reset_time') || 'Resets at'}: {new Date(usage.reset_time).toLocaleString()}
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="text-center py-8 text-slate-400">
                    {t('usage_no_data') || 'No usage data available'}
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="invoices">
            <Card className="bg-slate-800 border-slate-700">
              <CardHeader>
                <CardTitle className="text-white">{t('subscription_invoices') || 'Invoice History'}</CardTitle>
              </CardHeader>
              <CardContent>
                {invoices.length > 0 ? (
                  <div className="space-y-3">
                    {invoices.map((invoice) => (
                      <div
                        key={invoice.id}
                        className="flex items-center justify-between p-4 bg-slate-700 rounded-lg"
                      >
                        <div>
                          <p className="text-white font-medium">
                            {t('subscription_invoice_date') || 'Date'}: {invoice.created_at ? new Date(invoice.created_at).toLocaleDateString() : 'N/A'}
                          </p>
                          <p className="text-slate-400">
                            {t('subscription_invoice_amount') || 'Amount'}: ¥{invoice.amount || 0}
                          </p>
                        </div>
                        <div className="flex items-center gap-2">
                          <span className={`px-2 py-1 rounded text-xs ${
                            invoice.status === 'paid'
                              ? 'bg-green-500/20 text-green-400'
                              : 'bg-yellow-500/20 text-yellow-400'
                          }`}>
                            {invoice.status || 'pending'}
                          </span>
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => handleDownloadInvoice(invoice.id)}
                          >
                            <Download className="w-4 h-4 mr-2" />
                            {t('subscription_download_pdf') || 'PDF'}
                          </Button>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-center py-8 text-slate-400">
                    {t('usage_no_data') || 'No invoices available'}
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

export default Subscription;
