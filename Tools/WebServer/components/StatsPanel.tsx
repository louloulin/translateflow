import React from 'react';
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts';
import { ChartDataPoint, TaskStats } from '../types';
import { Activity, Zap, FileText, Clock, CheckCircle, AlertCircle } from 'lucide-react';
import { useI18n } from '../contexts/I18nContext';
import { useGlobal } from '../contexts/GlobalContext';

interface StatsPanelProps {
  data: ChartDataPoint[];
  stats: TaskStats;
  variant?: 'default' | 'compact';
}

const colorMap: Record<string, { bg: string, text: string }> = {
  yellow: { bg: 'bg-yellow-500/10', text: 'text-yellow-600 dark:text-yellow-400' },
  primary: { bg: 'bg-primary/10', text: 'text-primary' },
  green: { bg: 'bg-green-500/10', text: 'text-green-600 dark:text-green-400' },
  red: { bg: 'bg-red-500/10', text: 'text-red-600 dark:text-red-400' },
  accent: { bg: 'bg-accent/10', text: 'text-accent' },
  secondary: { bg: 'bg-secondary', text: 'text-secondary-foreground' }
};

const StatCard = ({ icon: Icon, label, value, subtext, color, compact }: any) => {
  const styles = colorMap[color] || colorMap.primary;
  return (
    <div className={`${compact ? 'p-2' : 'p-3'} bg-card/50 border border-border rounded-xl flex items-center gap-3 backdrop-blur-sm shadow-sm`}>
      <div className={`${compact ? 'p-1.5' : 'p-2.5'} rounded-lg ${styles.bg} ${styles.text}`}>
        <Icon size={compact ? 14 : 20} />
      </div>
      <div className="overflow-hidden">
        <p className="text-muted-foreground text-[9px] uppercase tracking-wider font-semibold truncate">{label}</p>
        <p className={`${compact ? 'text-base' : 'text-xl'} font-bold text-foreground`}>{value}</p>
        {subtext && !compact && <p className="text-muted-foreground text-[10px] truncate">{subtext}</p>}
      </div>
    </div>
  );
};

export const StatsPanel: React.FC<StatsPanelProps> = ({ data, stats, variant = 'default' }) => {
  const { t } = useI18n();
  const { uiPrefs } = useGlobal();
  const isCompact = variant === 'compact';

  // Detect current theme
  const isDark = typeof window !== 'undefined' && document.documentElement.classList.contains('dark');

  // Theme-aware chart colors
  const chartColors = {
    rpm: isDark ? '#06b6d4' : '#0891b2', // cyan shades
    tpm: isDark ? '#8b5cf6' : '#7c3aed', // purple shades
    grid: isDark ? '#334155' : '#cbd5e1',
    tooltipBg: isDark ? '#1e293b' : '#ffffff',
    tooltipBorder: isDark ? '#334155' : '#e2e8f0',
    tooltipText: isDark ? '#e2e8f0' : '#1e293b'
  };

  // Defensive values
  const rpm = stats?.rpm || 0;
  const tpm = stats?.tpm || 0;
  const completed = stats?.completedProgress || 0;
  const total = Math.max(stats?.totalProgress || 0, 1);
  const elapsed = stats?.elapsedTime || 0;
  const sRate = stats?.successRate || 0;
  const eRate = stats?.errorRate || 0;

  return (
    <div className={isCompact ? 'space-y-2' : 'space-y-4'}>
      <div className={`grid grid-cols-2 ${isCompact ? 'lg:grid-cols-4' : 'md:grid-cols-2 lg:grid-cols-4'} gap-2`}>
        <StatCard 
          icon={Zap} 
          label="RPM" 
          value={rpm.toFixed(1)} 
          subtext="Requests per min"
          color="yellow" 
          compact={isCompact}
        />
        <StatCard 
          icon={Activity} 
          label="TPM" 
          value={`${tpm.toFixed(1)}k`} 
          subtext="Tokens per min"
          color="primary" 
          compact={isCompact}
        />
        <StatCard 
          icon={CheckCircle} 
          label="S-Rate" 
          value={`${sRate.toFixed(1)}%`} 
          subtext="Success Rate"
          color="green" 
          compact={isCompact}
        />
        <StatCard 
          icon={AlertCircle} 
          label="E-Rate" 
          value={`${eRate.toFixed(1)}%`} 
          subtext="Error Rate"
          color="red" 
          compact={isCompact}
        />
        <StatCard 
          icon={FileText} 
          label="Progress" 
          value={`${completed}/${stats?.totalProgress || 0}`} 
          subtext={`${((completed / total) * 100).toFixed(1)}% Completed`}
          color="accent" 
          compact={isCompact}
        />
        <StatCard 
          icon={Clock} 
          label="Elapsed" 
          value={`${Math.floor(elapsed / 60)}m ${Math.floor(elapsed % 60)}s`} 
          subtext="Session duration"
          color="secondary" 
          compact={isCompact}
        />
      </div>

      <div className={`bg-card/50 border border-border rounded-xl p-4 ${isCompact ? 'h-32' : 'h-64'} backdrop-blur-sm relative shadow-sm`}>
        <h3 className="text-muted-foreground text-[10px] font-semibold uppercase absolute top-2 left-4 z-10">{t('ui_task_perf_chart')}</h3>
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={data}>
            <defs>
              <linearGradient id="colorRpm" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor={chartColors.rpm} stopOpacity={0.3}/>
                <stop offset="95%" stopColor={chartColors.rpm} stopOpacity={0}/>
              </linearGradient>
              <linearGradient id="colorTpm" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor={chartColors.tpm} stopOpacity={0.3}/>
                <stop offset="95%" stopColor={chartColors.tpm} stopOpacity={0}/>
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke={chartColors.grid} opacity={0.5} vertical={false} />
            <XAxis dataKey="time" hide />
            <YAxis hide />
            <Tooltip
              contentStyle={{ backgroundColor: chartColors.tooltipBg, borderColor: chartColors.tooltipBorder, borderRadius: '8px', fontSize: '10px' }}
              itemStyle={{ color: chartColors.tooltipText }}
            />
            <Area type="monotone" dataKey="rpm" stroke={chartColors.rpm} strokeWidth={isCompact ? 1 : 2} fillOpacity={1} fill="url(#colorRpm)" />
            <Area type="monotone" dataKey="tpm" stroke={chartColors.tpm} strokeWidth={isCompact ? 1 : 2} fillOpacity={1} fill="url(#colorTpm)" />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};