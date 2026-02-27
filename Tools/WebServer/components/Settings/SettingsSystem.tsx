import React, { useState, useEffect } from 'react';
import { useI18n } from '@/contexts/I18nContext';
import { useGlobal } from '@/contexts/GlobalContext';
import { DataService } from '@/services/DataService';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Switch } from '@/components/ui/switch';
import { Label } from '@/components/ui/label';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Checkbox } from '@/components/ui/checkbox';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Settings, FileJson, Trash2, ChevronDown, Wifi, WifiOff, AlertTriangle } from 'lucide-react';
import { AppConfig } from '@/types';
import { cn } from '@/lib/utils';

export const SettingsSystem: React.FC = () => {
  const { t } = useI18n();
  const { config, setConfig, unlockThemeWithNotification } = useGlobal();
  const [tempFiles, setTempFiles] = useState<{name: string, path: string, size: number}[]>([]);
  const [selectedTempFiles, setSelectedTempFiles] = useState<string[]>([]);
  const [isDeletingFiles, setIsDeletingFiles] = useState(false);
  const [isTempFilesExpanded, setIsTempFilesExpanded] = useState(false);
  const [isOnline, setIsOnline] = useState(true);
  const [warningClicks, setWarningClicks] = useState(0);

  useEffect(() => {
    handleLoadTempFiles();
  }, []);

  if (!config) return null;

  const handleChange = (field: keyof AppConfig, value: any) => {
    setConfig({ ...config, [field]: value });
  };

  const handleCheckChange = (key: string, val: boolean) => {
      const currentSwitch = typeof config.response_check_switch === 'object' && config.response_check_switch !== null
          ? config.response_check_switch
          : { newline_character_count_check: false, return_to_original_text_check: false, residual_original_text_check: false, reply_format_check: false };
      setConfig({
          ...config,
          response_check_switch: {
              ...currentSwitch,
              [key]: val
          }
      });
  };

  const handleLoadTempFiles = async () => {
      const list = await DataService.listTempFiles();
      setTempFiles(list);
  };

  const handleDeleteTempFiles = async () => {
      if (selectedTempFiles.length === 0) return;
      if (!confirm(`Delete ${selectedTempFiles.length} files?`)) return;
      setIsDeletingFiles(true);
      try {
          await DataService.deleteTempFiles(selectedTempFiles);
          await handleLoadTempFiles();
          setSelectedTempFiles([]);
      } catch (e) {
          alert("Failed to delete files");
      } finally {
          setIsDeletingFiles(false);
      }
  };

  const handleWarningClick = () => {
    const newCount = warningClicks + 1;
    setWarningClicks(newCount);
    if (newCount >= 3) {
      unlockThemeWithNotification('aponia');
      setWarningClicks(0);
    }
  };

  const ToggleItem = ({ field, label, desc }: { field: keyof AppConfig, label: string, desc?: string }) => (
    <div className="flex items-center justify-between p-4 border rounded-lg bg-card hover:bg-accent/5 transition-colors">
        <div className="space-y-0.5">
            <Label className="text-base font-medium">{label}</Label>
            {desc && <p className="text-sm text-muted-foreground">{desc}</p>}
        </div>
        <Switch 
            checked={!!config[field]} 
            onCheckedChange={(checked) => handleChange(field, checked)} 
        />
    </div>
  );

  return (
    <div className="space-y-6">
      {/* General System Toggles */}
      <Card>
        <CardHeader>
            <CardTitle className="flex items-center gap-2">
                <Settings className="h-5 w-5 text-primary" />
                {t('ui_tab_system')}
            </CardTitle>
            <CardDescription>System-level configurations and maintenance</CardDescription>
        </CardHeader>
        <CardContent className="grid grid-cols-1 md:grid-cols-2 gap-4">
             <ToggleItem field="show_detailed_logs" label={t('setting_detailed_logs')} />
             <ToggleItem field="enable_cache_backup" label={t('setting_cache_backup')} />
             <ToggleItem field="enable_auto_restore_ebook" label={t('setting_auto_restore_ebook')} />
             <ToggleItem field="enable_xlsx_conversion" label={t('setting_enable_xlsx_conversion')} />
             <ToggleItem field="enable_dry_run" label={t('setting_dry_run')} />
             <ToggleItem field="enable_smart_round_limit" label={t('setting_enable_smart_round_limit')} />
             <ToggleItem field="response_conversion_toggle" label={t('setting_response_conversion_toggle')} />
             <ToggleItem field="enable_context_enhancement" label={t('setting_enable_context_enhancement')} desc={t('setting_enable_context_enhancement_desc')} />
        </CardContent>
      </Card>

      {/* Rate Limiting */}
      <Card>
        <CardHeader>
            <div className="flex items-center justify-between">
                <CardTitle>Rate Limiting</CardTitle>
                <Switch 
                    checked={config.enable_rate_limit} 
                    onCheckedChange={(checked) => handleChange('enable_rate_limit', checked)} 
                />
            </div>
            <CardDescription>{t('setting_enable_rate_limit_desc')}</CardDescription>
        </CardHeader>
        {config.enable_rate_limit && (
            <CardContent className="grid grid-cols-1 md:grid-cols-2 gap-6">
                 <div className="space-y-2">
                    <Label>{t('setting_custom_rpm_limit')}</Label>
                    <Input 
                        type="number" 
                        value={config.custom_rpm_limit ?? 0} 
                        onChange={(e) => handleChange('custom_rpm_limit', parseInt(e.target.value) || 0)}
                        placeholder="0 = use platform default"
                    />
                    <p className="text-xs text-muted-foreground">{t('setting_custom_rpm_limit_desc')}</p>
                 </div>
                 <div className="space-y-2">
                    <Label>{t('setting_custom_tpm_limit')}</Label>
                    <Input 
                        type="number" 
                        value={config.custom_tpm_limit ?? 0} 
                        onChange={(e) => handleChange('custom_tpm_limit', parseInt(e.target.value) || 0)}
                        placeholder="0 = use platform default"
                    />
                    <p className="text-xs text-muted-foreground">{t('setting_custom_tpm_limit_desc')}</p>
                 </div>
            </CardContent>
        )}
      </Card>

      {/* Temp Files */}
      <Card>
        <CardHeader>
            <div className="flex items-center justify-between">
                <CardTitle className="flex items-center gap-2">
                    <FileJson className="h-5 w-5 text-primary" />
                    Temp Files ({tempFiles.length})
                </CardTitle>
                <div className="flex items-center gap-2">
                    {selectedTempFiles.length > 0 && (
                        <Button 
                            variant="destructive" 
                            size="sm" 
                            onClick={handleDeleteTempFiles}
                            disabled={isDeletingFiles}
                        >
                            <Trash2 className="h-4 w-4 mr-2" /> Delete ({selectedTempFiles.length})
                        </Button>
                    )}
                    <Button variant="ghost" size="icon" onClick={() => setIsTempFilesExpanded(!isTempFilesExpanded)}>
                        <ChevronDown className={cn("h-4 w-4 transition-transform", isTempFilesExpanded && "rotate-180")} />
                    </Button>
                </div>
            </div>
        </CardHeader>
        {isTempFilesExpanded && (
            <CardContent>
                <div className="space-y-4">
                    <div className="flex gap-4">
                        <div className="space-y-2 flex-1">
                            <Label>{t('setting_temp_file_limit')}</Label>
                            <Input 
                                type="number" 
                                value={config.temp_file_limit ?? 10} 
                                onChange={(e) => handleChange('temp_file_limit', parseInt(e.target.value))} 
                            />
                        </div>
                        <div className="space-y-2 flex-1">
                            <Label>Cache Editor Page Size</Label>
                            <Input 
                                type="number" 
                                value={config.cache_editor_page_size ?? 15} 
                                onChange={(e) => handleChange('cache_editor_page_size', parseInt(e.target.value))} 
                            />
                        </div>
                    </div>
                    
                    <ScrollArea className="h-[200px] rounded-md border p-4">
                        {tempFiles.length === 0 ? (
                            <p className="text-center text-sm text-muted-foreground italic">No temp files found</p>
                        ) : (
                            <div className="space-y-2">
                                {tempFiles.map(f => (
                                    <div key={f.name} className="flex items-center space-x-2 p-2 hover:bg-accent rounded-md">
                                        <Checkbox 
                                            id={f.name} 
                                            checked={selectedTempFiles.includes(f.name)}
                                            onCheckedChange={(checked) => {
                                                setSelectedTempFiles(prev => 
                                                    checked ? [...prev, f.name] : prev.filter(n => n !== f.name)
                                                )
                                            }}
                                        />
                                        <label htmlFor={f.name} className="flex-1 text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70 cursor-pointer">
                                            {f.name} <span className="text-xs text-muted-foreground ml-2">({(f.size/1024).toFixed(1)} KB)</span>
                                        </label>
                                    </div>
                                ))}
                            </div>
                        )}
                    </ScrollArea>
                </div>
            </CardContent>
        )}
      </Card>

      {/* Response Checks */}
      <Card>
        <CardHeader>
            <div className="flex items-center justify-between">
                <CardTitle>{t('menu_response_checks')}</CardTitle>
                <div className={cn(
                    "flex items-center gap-2 px-3 py-1 rounded-full text-xs font-bold border",
                    isOnline 
                        ? "bg-emerald-500/10 text-emerald-500 border-emerald-500/20" 
                        : "bg-destructive/10 text-destructive border-destructive/20 animate-pulse"
                )}>
                    {isOnline ? <Wifi size={14} /> : <WifiOff size={14} />}
                    {isOnline ? t('ui_system_online') : "SYSTEM OFFLINE"}
                </div>
            </div>
        </CardHeader>
        <CardContent className="grid grid-cols-1 md:grid-cols-2 gap-4">
             {typeof config.response_check_switch === 'object' && config.response_check_switch !== null && Object.entries(config.response_check_switch).map(([key, val]) => (
                 <div key={key} className="flex items-center justify-between p-4 border rounded-lg bg-card">
                     <div className="flex items-center gap-2">
                        <AlertTriangle size={16} className="text-yellow-500 cursor-help" onClick={handleWarningClick} />
                        <Label className="text-sm cursor-pointer" onClick={() => handleCheckChange(key, !(val as boolean))}>
                            {t(`check_${key}`) || key}
                        </Label>
                     </div>
                     <Switch 
                        checked={val as boolean} 
                        onCheckedChange={(checked) => handleCheckChange(key, checked)} 
                     />
                 </div>
             ))}
        </CardContent>
      </Card>
    </div>
  );
};
