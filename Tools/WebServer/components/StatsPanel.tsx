import React from 'react';
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts';
import { ChartDataPoint, TaskStats } from '../types';
import { Activity, Zap, FileText, Clock } from 'lucide-react';
import { useI18n } from '../contexts/I18nContext';

interface StatsPanelProps {
  data: ChartDataPoint[];
  stats: TaskStats;
  variant?: 'default' | 'compact';
}

const StatCard = ({ icon: Icon, label, value, subtext, color, compact }: any) => (
  <div className={`${compact ? 'p-2' : 'p-4'} bg-surface/50 border border-slate-700/50 rounded-xl flex items-center gap-4 backdrop-blur-sm`}>
    <div className={`${compact ? 'p-2' : 'p-3'} rounded-lg bg-${color}-500/10 text-${color}-400`}>
      <Icon size={compact ? 16 : 24} />
    </div>
    <div>
      <p className="text-slate-400 text-[10px] uppercase tracking-wider font-semibold">{label}</p>
      <p className={`${compact ? 'text-lg' : 'text-2xl'} font-bold text-slate-100`}>{value}</p>
      {subtext && !compact && <p className="text-slate-500 text-xs">{subtext}</p>}
    </div>
  </div>
);

export const StatsPanel: React.FC<StatsPanelProps> = ({ data, stats, variant = 'default' }) => {
  const { t } = useI18n();
  const isCompact = variant === 'compact';
  // Defensive values
  const rpm = stats?.rpm || 0;
  const tpm = stats?.tpm || 0;
  const completed = stats?.completedProgress || 0;
  const total = Math.max(stats?.totalProgress || 0, 1);
  const elapsed = stats?.elapsedTime || 0;

  return (
    <div className={isCompact ? 'space-y-3' : 'space-y-6'}>
      <div className={`grid grid-cols-2 ${isCompact ? 'lg:grid-cols-4' : 'md:grid-cols-2 lg:grid-cols-4'} gap-3`}>
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

      <div className={`bg-surface/50 border border-slate-700/50 rounded-xl p-4 ${isCompact ? 'h-32' : 'h-64'} backdrop-blur-sm relative`}>
        <h3 className="text-slate-400 text-[10px] font-semibold uppercase absolute top-2 left-4 z-10">{t('ui_task_perf_chart')}</h3>
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={data}>
            <defs>
              <linearGradient id="colorRpm" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#06b6d4" stopOpacity={0.3}/>
                <stop offset="95%" stopColor="#06b6d4" stopOpacity={0}/>
              </linearGradient>
              <linearGradient id="colorTpm" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#8b5cf6" stopOpacity={0.3}/>
                <stop offset="95%" stopColor="#8b5cf6" stopOpacity={0}/>
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#334155" opacity={0.5} vertical={false} />
            <XAxis dataKey="time" hide />
            <YAxis hide />
            <Tooltip 
              contentStyle={{ backgroundColor: '#1e293b', borderColor: '#334155', borderRadius: '8px', fontSize: '10px' }}
              itemStyle={{ color: '#e2e8f0' }}
            />
            <Area type="monotone" dataKey="rpm" stroke="#06b6d4" strokeWidth={isCompact ? 1 : 2} fillOpacity={1} fill="url(#colorRpm)" />
            <Area type="monotone" dataKey="tpm" stroke="#8b5cf6" strokeWidth={isCompact ? 1 : 2} fillOpacity={1} fill="url(#colorTpm)" />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};