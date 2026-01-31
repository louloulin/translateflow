import React, { useState, useEffect } from 'react';
import { Puzzle, ToggleLeft, ToggleRight, RefreshCw, AlertCircle, CheckCircle2, Info, Boxes } from 'lucide-react';
import { useI18n } from '../contexts/I18nContext';
import { useGlobal } from '../contexts/GlobalContext';
import { DataService } from '../services/DataService';

interface PluginInfo {
  name: string;
  description: string;
  enabled: boolean;
  default_enable: boolean;
}

export const Plugins: React.FC = () => {
  const { t } = useI18n();
  const { config, setConfig, unlockThemeWithNotification, triggerRipple } = useGlobal();
  const [plugins, setPlugins] = useState<PluginInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [toggling, setToggling] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const loadPlugins = async () => {
    setLoading(true);
    // Pardo Trigger: Refreshing plugin list
    unlockThemeWithNotification('pardofelis');
    try {
      const data = await DataService.getPlugins();
      setPlugins(data);
    } catch (e: any) {
      setError(e.message || 'Failed to load plugins');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadPlugins();

    // Pardofelis Trigger: Count entries
    const entries = parseInt(sessionStorage.getItem('pardo_entries') || '0');
    const newEntries = entries + 1;
    sessionStorage.setItem('pardo_entries', newEntries.toString());
    if (newEntries >= 5) {
        unlockThemeWithNotification('pardofelis');
        sessionStorage.setItem('pardo_entries', '0');
    }

    // Pardofelis Trigger: Scroll to bottom
    const handleScroll = () => {
        if ((window.innerHeight + window.scrollY) >= document.body.offsetHeight - 2) {
            const scrollCount = parseInt(sessionStorage.getItem('pardo_scroll') || '0');
            const newCount = scrollCount + 1;
            sessionStorage.setItem('pardo_scroll', newCount.toString());
            if (newCount >= 3) {
                unlockThemeWithNotification('pardofelis');
                sessionStorage.setItem('pardo_scroll', '0');
            }
        }
    };

    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  const handleToggle = async (name: string, currentStatus: boolean) => {
    setToggling(name);
    try {
      await DataService.togglePlugin(name, !currentStatus);
      // Update local state
      setPlugins(prev => prev.map(p => 
        p.name === name ? { ...p, enabled: !currentStatus } : p
      ));
    } catch (e: any) {
      alert(e.message || 'Failed to toggle plugin');
    } finally {
      setToggling(null);
    }
  };

  return (
    <div className="max-w-5xl mx-auto space-y-8 pb-12">
      {/* Header section with distinct style */}
      <div className="flex justify-between items-end pb-6 border-b border-slate-800">
        <div className="space-y-1">
          <div className="flex items-center gap-3">
            <div className="p-2.5 bg-primary/20 rounded-xl text-primary shadow-[0_0_15px_rgba(6,182,212,0.2)]">
              <Boxes size={28} />
            </div>
            <h1 className="text-3xl font-extrabold text-white tracking-tight">{t('menu_plugin_settings')}</h1>
          </div>
          <p className="text-slate-500 text-sm pl-1">{t('ui_plugins_subtitle')}</p>
        </div>
        <button 
          onClick={loadPlugins}
          disabled={loading}
          className="flex items-center gap-2 px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg transition-all active:scale-95 disabled:opacity-50 border border-slate-700"
        >
          <RefreshCw size={18} className={loading ? "animate-spin" : ""} />
          <span className="text-sm font-bold">{t('ui_btn_refresh')}</span>
        </button>
      </div>

      {error && (
        <div className="p-4 bg-red-500/10 border border-red-500/20 rounded-xl flex items-center gap-3 text-red-400 animate-in fade-in slide-in-from-top-4 duration-300">
          <AlertCircle size={20} />
          <p className="text-sm font-semibold">{error}</p>
        </div>
      )}

      {/* Plugin Grid for clear separation */}
      <div className="grid grid-cols-1 gap-6">
        {loading && plugins.length === 0 ? (
          <div className="py-32 flex flex-col items-center justify-center space-y-4 bg-slate-900/20 border border-slate-800 border-dashed rounded-3xl">
            <RefreshCw size={48} className="text-primary animate-spin opacity-40" />
            <div className="text-center">
              <p className="text-slate-400 font-bold uppercase tracking-widest text-xs">{t('ui_plugins_scan_title')}</p>
              <p className="text-slate-600 text-sm mt-1">{t('ui_plugins_scan_desc')}</p>
            </div>
          </div>
        ) : plugins.length === 0 ? (
          <div className="py-32 flex flex-col items-center justify-center space-y-4 bg-slate-900/20 border border-slate-800 border-dashed rounded-3xl">
            <Puzzle size={48} className="text-slate-700 opacity-40" />
            <p className="text-slate-500 font-medium">{t('msg_no_plugins_found')}</p>
          </div>
        ) : (
          plugins.map((plugin) => (
            <div 
              key={plugin.name} 
              className={`relative overflow-hidden group rounded-2xl border-2 transition-all duration-500 ${
                plugin.enabled 
                  ? 'bg-slate-900/40 border-primary/30 shadow-[0_8px_30px_rgb(0,0,0,0.12)] shadow-primary/5' 
                  : 'bg-slate-950/20 border-slate-800 hover:border-slate-700 shadow-none'
              }`}
            >
              {/* Highlight bar for enabled plugins */}
              {plugin.enabled && (
                <div className="absolute top-0 left-0 w-1.5 h-full bg-primary shadow-[0_0_15px_rgba(6,182,212,0.5)]" />
              )}
              
              <div className="p-6 md:p-8 flex flex-col md:flex-row md:items-center justify-between gap-6">
                <div className="flex-1 space-y-4 min-w-0">
                  <div className="flex items-center flex-wrap gap-3">
                    <h3 className={`text-xl font-black transition-colors ${plugin.enabled ? 'text-white' : 'text-slate-400 group-hover:text-slate-300'}`}>
                      {plugin.name}
                    </h3>
                    {plugin.enabled && (
                      <div className="flex items-center gap-1.5 px-2.5 py-1 bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 rounded-full text-[10px] font-black uppercase tracking-tighter animate-in zoom-in-90">
                        <CheckCircle2 size={12} />
                        {t('ui_plugins_active')}
                      </div>
                    )}
                  </div>
                  
                  <div className="relative">
                    <p className={`text-sm leading-relaxed max-w-3xl transition-colors duration-300 ${plugin.enabled ? 'text-slate-300' : 'text-slate-500 italic'}`}>
                      {plugin.description || t('ui_plugins_no_desc')}
                    </p>
                  </div>
                  
                  <div className="flex items-center gap-4 text-[10px] font-mono tracking-tight">
                    <span className={`px-2 py-0.5 rounded ${plugin.enabled ? 'bg-slate-800 text-slate-400' : 'bg-slate-900 text-slate-600'}`}>
                      {t('ui_plugins_source')}: {plugin.name}.py
                    </span>
                    <span className="text-slate-600">
                      {t('ui_plugins_default')}: {plugin.default_enable ? t('ui_plugins_on') : t('ui_plugins_off')}
                    </span>
                  </div>
                </div>

                <div className="flex flex-col items-center gap-3 shrink-0 bg-black/20 p-4 rounded-2xl border border-white/5">
                  <button 
                    onClick={() => handleToggle(plugin.name, plugin.enabled)}
                    disabled={toggling === plugin.name}
                    className={`group/btn relative inline-flex h-10 w-20 shrink-0 cursor-pointer items-center rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none ${
                      plugin.enabled ? 'bg-primary' : 'bg-slate-800'
                    } ${toggling === plugin.name ? 'opacity-50 cursor-not-allowed' : ''}`}
                  >
                    <span
                      aria-hidden="true"
                      className={`pointer-events-none inline-block h-8 w-8 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out ${
                        plugin.enabled ? 'translate-x-10' : 'translate-x-0'
                      }`}
                    />
                  </button>
                  <div className="flex flex-col items-center">
                    <span className={`text-[11px] font-black uppercase tracking-widest ${plugin.enabled ? 'text-primary' : 'text-slate-600'}`}>
                      {plugin.enabled ? t('ui_plugins_running') : t('ui_plugins_disabled')}
                    </span>
                    {toggling === plugin.name && <span className="text-[9px] text-slate-400 animate-pulse mt-0.5 font-bold">{t('ui_plugins_applying')}</span>}
                  </div>
                </div>
              </div>
            </div>
          ))
        )}
      </div>

      {/* Info footer */}
      <div className="p-6 bg-slate-900/50 border border-slate-800 rounded-3xl flex gap-4 items-start">
        <div className="p-2 bg-blue-500/10 rounded-lg text-blue-400">
          <Info size={20} />
        </div>
        <div className="space-y-2">
          <h4 className="text-sm font-black text-slate-200 uppercase tracking-wider">{t('ui_plugins_arch_title')}</h4>
          <p className="text-xs text-slate-400 leading-relaxed max-w-3xl">
            {t('ui_plugins_about_desc_part1')}
            <strong className="text-slate-200 font-bold">{t('ui_plugins_about_desc_part2')}</strong>
            {t('ui_plugins_about_desc_part3')}
          </p>
        </div>
      </div>
    </div>
  );
};
