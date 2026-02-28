import React from 'react';
import { useI18n } from '@/contexts/I18nContext';
import { useGlobal } from '@/contexts/GlobalContext';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { AlertTriangle, FolderOpen } from 'lucide-react';
import { PROJECT_TYPES } from '@/constants';

export const SettingsProject: React.FC = () => {
  const { t } = useI18n();
  const { config, setConfig } = useGlobal();

  if (!config) return null;

  const handleChange = (field: string, value: any) => {
    setConfig({ ...config, [field]: value });
  };

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
            <CardTitle className="flex items-center gap-2">
                <FolderOpen className="h-5 w-5 text-primary" />
                {t('ui_tab_project')}
            </CardTitle>
            <CardDescription>Configure project handling and constraints</CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
            <div className="space-y-2">
                <Label>{t('setting_project_type')}</Label>
                <Select 
                    value={config.translation_project} 
                    onValueChange={(val) => handleChange('translation_project', val)}
                >
                    <SelectTrigger>
                        <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                        {PROJECT_TYPES.map(p => (
                            <SelectItem key={p} value={p}>{p}</SelectItem>
                        ))}
                    </SelectContent>
                </Select>
            </div>

            <div className="p-4 border rounded-lg bg-muted/30 space-y-4">
                <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
                    <div className="space-y-0.5">
                        <Label className="text-base">{t('setting_limit_mode')}</Label>
                        <p className="text-sm text-muted-foreground">{t('menu_trans_mode_select')}</p>
                    </div>
                    <Tabs 
                        value={config.tokens_limit_switch ? "token" : "line"} 
                        onValueChange={(val) => handleChange('tokens_limit_switch', val === "token")}
                        className="w-[200px]"
                    >
                        <TabsList className="grid w-full grid-cols-2">
                            <TabsTrigger value="line">Line</TabsTrigger>
                            <TabsTrigger value="token">Token</TabsTrigger>
                        </TabsList>
                    </Tabs>
                </div>

                {!config.tokens_limit_switch ? (
                    <div className="space-y-2">
                        <Label>{t('prompt_limit_val')} (Lines)</Label>
                        <Input 
                            type="number"
                            value={config.lines_limit} 
                            onChange={(e) => handleChange('lines_limit', parseInt(e.target.value))}
                        />
                    </div>
                ) : (
                    <div className="space-y-2">
                        <div className="flex items-center gap-2 text-yellow-500 mb-1">
                            <AlertTriangle size={14} />
                            <span className="text-[10px] font-bold uppercase">{t('warn_token_mode_severe')}</span>
                        </div>
                        <Input 
                            type="number"
                            value={config.lines_limit * 100} 
                            onChange={(e) => handleChange('lines_limit', Math.floor(parseInt(e.target.value)/100))}
                        />
                    </div>
                )}
            </div>

            <div className="space-y-2 pt-4 border-t">
                <Label>{t('setting_pre_lines') || 'Context Lines (Pre-lines)'}</Label>
                <p className="text-sm text-muted-foreground mb-2">
                    {t('desc_pre_lines') || 'Number of previous translated lines to include as context for AI.'}
                </p>
                <Input 
                    type="number"
                    value={config.pre_line_counts ?? 3} 
                    onChange={(e) => handleChange('pre_line_counts', parseInt(e.target.value) || 0)}
                />
            </div>
        </CardContent>
      </Card>
    </div>
  );
};
