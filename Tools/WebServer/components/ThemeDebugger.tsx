import React, { useState, useEffect } from 'react';
import { useGlobal } from '../contexts/GlobalContext';
import { ThemeType } from '../types';
import { Bug, Sparkles } from 'lucide-react';

export const ThemeDebugger: React.FC = () => {
  const { activeTheme, setActiveTheme, unlockTheme } = useGlobal();
  const [visible, setVisible] = useState(false);

  const themes: ThemeType[] = [
    'default', 'elysia', 'eden', 'mobius', 'pardofelis', 'griseo', 'kevin', 'kalpas',
    'aponia', 'villv', 'su', 'sakura', 'kosma', 'hua', 'herrscher_of_human'
  ];

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Ctrl + Shift + D 切换显示
      if (e.ctrlKey && e.shiftKey && e.key === 'D') {
        setVisible(v => !v);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  if (!visible) return (
    <div 
        className="fixed bottom-4 left-4 z-[99999] opacity-20 hover:opacity-100 cursor-help"
        title="Debug Mode: Ctrl+Shift+D"
    >
        <Bug size={16} className="text-slate-500" />
    </div>
  );

  return (
    <div className="fixed top-20 left-4 z-[99999] bg-slate-900/95 backdrop-blur-md border-2 border-red-500/50 p-4 rounded-2xl shadow-[0_20px_50px_rgba(0,0,0,0.5)] w-48 animate-in fade-in zoom-in duration-200">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2 text-red-500">
          <Bug size={18} />
          <span className="font-black text-xs uppercase tracking-tighter">Theme Debug</span>
        </div>
        <button onClick={() => setVisible(false)} className="text-slate-500 hover:text-white">×</button>
      </div>
      
      <div className="space-y-1.5">
        {themes.map(t => (
          <button
            key={t}
            onClick={() => {
              setActiveTheme(t);
              unlockTheme(t);
            }}
            className={`w-full text-left px-3 py-2 rounded-lg text-[10px] font-black uppercase tracking-widest transition-all ${
              activeTheme === t 
                ? 'bg-red-500 text-white shadow-lg shadow-red-500/20 translate-x-1' 
                : 'bg-slate-800/50 text-slate-400 hover:bg-slate-700 hover:text-slate-200'
            }`}
          >
            {activeTheme === t && <Sparkles size={10} className="inline-block mr-2 animate-pulse" />}
            {t}
          </button>
        ))}
      </div>
      
      <div className="mt-4 pt-3 border-t border-slate-800">
        <p className="text-[9px] text-slate-500 italic leading-tight">
          Shortcut: <span className="text-slate-300">Ctrl+Shift+D</span><br/>
          Click theme to apply & unlock.
        </p>
      </div>
    </div>
  );
};
