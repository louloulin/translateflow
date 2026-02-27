import React, { useEffect, useRef } from 'react';
import { LogEntry } from '../types';
import { useI18n } from '../contexts/I18nContext';
import { useGlobal } from '../contexts/GlobalContext';

interface TerminalProps {
  logs: LogEntry[];
  height?: string;
}

export const Terminal: React.FC<TerminalProps> = ({ logs, height = "h-64" }) => {
  const { t } = useI18n();
  const { triggerRipple, unlockThemeWithNotification } = useGlobal();
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [logs]);

  const getColor = (type: LogEntry['type']) => {
    switch (type) {
      case 'error': return 'text-red-400';
      case 'warning': return 'text-yellow-400';
      case 'success': return 'text-green-400';
      case 'system': return 'text-primary';
      default: return 'text-slate-300';
    }
  };

  const handleLogClick = (e: React.MouseEvent, type: LogEntry['type']) => {
    if (type === 'error') {
      unlockThemeWithNotification('kalpas');
    }
  };
  return (
    <div className={`w-full ${height} bg-slate-950 border border-slate-800 rounded-lg overflow-hidden flex flex-col font-mono text-sm shadow-inner`}>
      <div className="bg-slate-900 px-4 py-2 border-b border-slate-800 flex items-center justify-between">
        <span className="text-slate-400 text-xs">{t('ui_task_console')}</span>
        <div className="flex gap-1.5">
          <div className="w-2.5 h-2.5 rounded-full bg-red-500/20 border border-red-500/50 cursor-pointer hover:bg-red-500/40" onClick={(e) => triggerRipple(e.clientX, e.clientY, 'kalpas')}></div>
          <div className="w-2.5 h-2.5 rounded-full bg-yellow-500/20 border border-yellow-500/50"></div>
          <div className="w-2.5 h-2.5 rounded-full bg-green-500/20 border border-green-500/50"></div>
        </div>
      </div>
      <div className="flex-1 overflow-y-auto p-4 space-y-1">
        {logs.map((log) => (
          <div 
            key={log.id} 
            className={`flex gap-3 min-w-0 hover:bg-white/5 p-0.5 rounded px-2 transition-colors ${log.type === 'error' ? 'cursor-pointer' : ''}`}
            onClick={(e) => handleLogClick(e, log.type)}
          >
            <span className="text-slate-500 min-w-[80px] select-none">[{log.timestamp}]</span>
            <span className={`${getColor(log.type)} min-w-0 whitespace-pre-wrap break-words`}>{log.message}</span>
          </div>
        ))}
        <div ref={bottomRef} />
      </div>
    </div>
  );
};
