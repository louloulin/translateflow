import React from 'react';
import { useI18n } from '@/contexts/I18nContext';
import { useGlobal } from '@/contexts/GlobalContext';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Sparkles, Globe, ToggleLeft, ToggleRight } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';

export const SettingsGeneral: React.FC = () => {
  const { t, language, setLanguage, availableLanguages } = useI18n();
  const { config, setConfig, activeTheme, triggerRipple } = useGlobal();
  const elysiaActive = activeTheme === 'elysia';
  const isElysiaProfile = config?.active_profile?.toLowerCase() === 'elysia';

  const handleChange = (field: string, value: any) => {
    if (!config) return;
    setConfig({ ...config, [field]: value });
  };

  const handleToggleElysia = (e: React.MouseEvent) => {
    triggerRipple(e.clientX, e.clientY);
  };

  if (!config) return null;

  return (
    <div className="space-y-6">
      {/* Elysia Theme Banner */}
      {(localStorage.getItem('elysia_unlocked') === 'true' && !isElysiaProfile) && (
        <Card className={cn(
            "transition-all duration-500",
            elysiaActive ? 'bg-pink-500/10 border-pink-500/20' : 'bg-slate-900/50 border-slate-700'
        )}>
          <CardContent className="flex items-center justify-between p-6">
             <div className="flex items-center gap-4">
                <div className={cn("p-2 rounded-full", elysiaActive ? 'bg-pink-500/20 text-pink-500' : 'bg-slate-800 text-slate-500')}>
                    <Sparkles size={24} />
                </div>
                <div>
                    <h4 className={cn("font-bold text-sm", elysiaActive ? 'text-pink-600' : 'text-slate-300')}>真我·主题 (Elysia Theme)</h4>
                    <p className={cn("text-xs", elysiaActive ? 'text-pink-400' : 'text-slate-500')}>在这里，与奇迹相遇。这就是我给你的小惊喜哦♪</p>
                </div>
             </div>
             <Button
                variant="ghost"
                size="icon"
                onClick={handleToggleElysia}
                className={cn("transition-all duration-300 hover:bg-transparent", elysiaActive ? 'text-pink-500 scale-110' : 'text-slate-600')}
             >
                {elysiaActive ? <ToggleRight size={40} /> : <ToggleLeft size={40} />}
             </Button>
          </CardContent>
        </Card>
      )}

      {/* Language Settings */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Globe className="h-5 w-5 text-primary" />
            {t('ui_language')}
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap gap-2">
            {availableLanguages.map(lang => (
                <Button
                    key={lang.code}
                    variant={language === lang.code ? "default" : "outline"}
                    size="sm"
                    onClick={() => {
                        setLanguage(lang.code);
                        handleChange('interface_language', lang.code);
                    }}
                    className={cn(language === lang.code && "bg-primary text-primary-foreground shadow-md")}
                >
                    {lang.label}
                </Button>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Path Settings */}
      <Card>
        <CardHeader>
            <CardTitle>{t('menu_group_task_config')}</CardTitle>
            <CardDescription>Input and Output directory configuration</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="space-y-2">
                    <Label htmlFor="input_path">{t('setting_input_path')}</Label>
                    <Input 
                        id="input_path" 
                        value={config.label_input_path} 
                        onChange={(e) => handleChange('label_input_path', e.target.value)} 
                    />
                </div>
                <div className="space-y-2">
                    <Label htmlFor="output_path">{t('setting_output_path')}</Label>
                    <Input 
                        id="output_path"
                        value={config.label_output_path}
                        onChange={(e) => handleChange('label_output_path', e.target.value)}
                        disabled={config.auto_set_output_path}
                        placeholder="Auto (beside input folder)"
                    />
                </div>
            </div>
            
            <div className="flex items-center justify-between p-4 border rounded-lg bg-muted/50">
                <div className="space-y-0.5">
                    <Label className="text-base">{t('setting_auto_set_output_path')}</Label>
                    <p className="text-sm text-muted-foreground">
                        Ignore fixed output path and create output folder beside input file/folder
                    </p>
                </div>
                <Switch 
                    checked={config.auto_set_output_path} 
                    onCheckedChange={(checked) => handleChange('auto_set_output_path', checked)} 
                />
            </div>
        </CardContent>
      </Card>

      {/* Language & Thread Settings */}
      <Card>
        <CardHeader>
            <CardTitle>Translation Parameters</CardTitle>
        </CardHeader>
        <CardContent className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="space-y-2">
                <Label>{t('prompt_source_lang')}</Label>
                <Input 
                    value={config.source_language} 
                    onChange={(e) => handleChange('source_language', e.target.value)} 
                />
            </div>
            <div className="space-y-2">
                <Label>{t('prompt_target_lang')}</Label>
                <Input 
                    value={config.target_language} 
                    onChange={(e) => handleChange('target_language', e.target.value)} 
                />
            </div>
            <div className="space-y-2">
                <Label>{t('setting_thread_count')}</Label>
                <Input 
                    type="number"
                    value={config.user_thread_counts} 
                    onChange={(e) => handleChange('user_thread_counts', parseInt(e.target.value))} 
                />
            </div>
            <div className="space-y-2">
                <Label>{t('setting_request_timeout')}</Label>
                <Input 
                    type="number"
                    value={config.request_timeout} 
                    onChange={(e) => handleChange('request_timeout', parseInt(e.target.value))} 
                />
            </div>
        </CardContent>
      </Card>
    </div>
  );
};
