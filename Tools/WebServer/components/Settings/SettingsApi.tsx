import React, { useState } from 'react';
import { useI18n } from '@/contexts/I18nContext';
import { useGlobal } from '@/contexts/GlobalContext';
import { DataService } from '@/services/DataService';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Button } from '@/components/ui/button';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Plus, Trash2, Server, Sparkles, AlertTriangle, RefreshCw, Check, X } from 'lucide-react';
import { PlatformConfig } from '@/types';

export const SettingsApi: React.FC = () => {
  const { t } = useI18n();
  const { config, setConfig } = useGlobal();
  
  const [isCreatingPlatform, setIsCreatingPlatform] = useState(false);
  const [tempName, setTempName] = useState('');
  const [newPoolItem, setNewPoolItem] = useState('');
  const [actionError, setActionError] = useState<string | null>(null);

  if (!config) return null;

  const handlePlatformChange = (tag: string) => {
    if (!config.platforms[tag]) return;
    const p = config.platforms[tag];
    setConfig({
        ...config,
        target_platform: tag,
        base_url: p.api_url || config.base_url,
        model: p.model || config.model,
        api_settings: { translate: tag, polish: tag }
    });
  };

  const handleChange = (field: string, value: any) => {
    setConfig({ ...config, [field]: value });
  };

  const handleCreatePlatform = async () => {
      if (!tempName.trim()) { setActionError("Name cannot be empty"); return; }
      try {
          await DataService.createPlatform(tempName);
          const newConfig = await DataService.getConfig();
          setConfig(newConfig);
          setIsCreatingPlatform(false);
          setTempName('');
      } catch (e: any) { setActionError(e.message); }
  };

  const handlePoolAdd = () => {
    if (newPoolItem && !config.backup_apis.includes(newPoolItem)) {
      handleChange('backup_apis', [...config.backup_apis, newPoolItem]);
      setNewPoolItem('');
    }
  };

  const handlePoolRemove = (item: string) => {
    handleChange('backup_apis', config.backup_apis.filter(i => i !== item));
  };

  return (
    <div className="space-y-6">
      {/* Platform Configuration */}
      <Card>
        <CardHeader>
            <CardTitle className="flex items-center gap-2">
                <Server className="h-5 w-5 text-primary" />
                Platform Configuration
            </CardTitle>
            <CardDescription>Configure your AI provider settings</CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="space-y-2">
                    <div className="flex justify-between items-center">
                        <Label>{t('label_platform')}</Label>
                        <Dialog open={isCreatingPlatform} onOpenChange={setIsCreatingPlatform}>
                            <DialogTrigger asChild>
                                <Button variant="link" size="sm" className="h-auto p-0 text-xs">
                                    <Plus className="h-3 w-3 mr-1" /> {t('menu_api_add_custom') || 'Add New'}
                                </Button>
                            </DialogTrigger>
                            <DialogContent>
                                <DialogHeader>
                                    <DialogTitle>Add Custom Platform</DialogTitle>
                                    <DialogDescription>Create a new API configuration based on OpenAI format.</DialogDescription>
                                </DialogHeader>
                                <div className="space-y-4 py-4">
                                    <div className="space-y-2">
                                        <Label>Platform Name</Label>
                                        <Input 
                                            value={tempName}
                                            onChange={(e) => setTempName(e.target.value)}
                                            placeholder="e.g. MyLocalLLM"
                                        />
                                        {actionError && <p className="text-destructive text-xs">{actionError}</p>}
                                    </div>
                                </div>
                                <DialogFooter>
                                    <Button variant="outline" onClick={() => setIsCreatingPlatform(false)}>Cancel</Button>
                                    <Button onClick={handleCreatePlatform}>Create</Button>
                                </DialogFooter>
                            </DialogContent>
                        </Dialog>
                    </div>
                    
                    <Select value={config.target_platform} onValueChange={handlePlatformChange}>
                        <SelectTrigger>
                            <SelectValue placeholder="Select platform" />
                        </SelectTrigger>
                        <SelectContent>
                            {Object.values(config.platforms).map((p: PlatformConfig) => (
                                <SelectItem key={p.tag} value={p.tag}>
                                    {p.name}
                                </SelectItem>
                            ))}
                        </SelectContent>
                    </Select>
                </div>

                <div className="space-y-2">
                    <Label>{t('label_model')}</Label>
                    <Input 
                        value={config.model} 
                        onChange={(e) => handleChange('model', e.target.value)} 
                    />
                </div>

                <div className="col-span-1 md:col-span-2 space-y-2">
                    <Label>{t('label_key')}</Label>
                    <Input 
                        type="password"
                        value={config.platforms[config.target_platform]?.api_key || ''}
                        onChange={(e) => {
                            const newKey = e.target.value;
                            setConfig({
                                ...config,
                                platforms: {
                                    ...config.platforms,
                                    [config.target_platform]: { ...(config.platforms[config.target_platform] || {}), api_key: newKey }
                                }
                            });
                        }}
                    />
                </div>

                <div className="col-span-1 md:col-span-2 space-y-2">
                    <Label>{t('label_url')}</Label>
                    <Input 
                        value={config.base_url} 
                        onChange={(e) => handleChange('base_url', e.target.value)} 
                    />
                </div>
            </div>

            <div className="flex items-center justify-between p-4 border rounded-lg bg-muted/50">
                <div className="space-y-0.5">
                    <Label className="text-base">{t('自动补全 OpenAI 规范的 Chat 终点')}</Label>
                    <p className="text-sm text-muted-foreground">
                        {t('如果开启，当 URL 不以 /chat/completions 结尾时，程序将自动尝试补全它')}
                    </p>
                </div>
                <Switch 
                    checked={config.platforms[config.target_platform]?.auto_complete}
                    onCheckedChange={(checked) => {
                        setConfig({
                            ...config,
                            platforms: {
                                ...config.platforms,
                                [config.target_platform]: { ...(config.platforms[config.target_platform] || {}), auto_complete: checked }
                            }
                        });
                    }}
                />
            </div>
        </CardContent>
      </Card>

      {/* Thinking Features */}
      <Card>
        <CardHeader>
            <CardTitle className="flex items-center gap-2">
                <Sparkles className="h-5 w-5 text-purple-500" />
                {t('menu_api_think_switch')}
            </CardTitle>
        </CardHeader>
        <CardContent className="space-y-6">
            <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                    <Label className="text-base">Enable Thinking Mode</Label>
                    <p className="text-sm text-muted-foreground">Enable advanced reasoning capabilities for supported models</p>
                </div>
                <Switch 
                    checked={config.think_switch}
                    onCheckedChange={(checked) => {
                        setConfig({
                            ...config,
                            think_switch: checked,
                            platforms: {
                                ...config.platforms,
                                [config.target_platform]: {
                                    ...(config.platforms[config.target_platform] || {}),
                                    think_switch: checked
                                }
                            }
                        });
                    }}
                />
            </div>

            {config.think_switch && (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6 pt-4 border-t">
                    <div className="space-y-2">
                        <Label>{t('menu_api_think_depth')}</Label>
                        {config.platforms[config.target_platform]?.api_format === 'Anthropic' ? (
                            <Select 
                                value={config.think_depth?.toString() || 'low'}
                                onValueChange={(val) => {
                                    setConfig({
                                        ...config,
                                        think_depth: val,
                                        platforms: {
                                            ...config.platforms,
                                            [config.target_platform]: {
                                                ...(config.platforms[config.target_platform] || {}),
                                                think_depth: val
                                            }
                                        }
                                    });
                                }}
                            >
                                <SelectTrigger>
                                    <SelectValue />
                                </SelectTrigger>
                                <SelectContent>
                                    <SelectItem value="low">Low</SelectItem>
                                    <SelectItem value="medium">Medium</SelectItem>
                                    <SelectItem value="high">High</SelectItem>
                                </SelectContent>
                            </Select>
                        ) : (
                            <Input 
                                type="number"
                                value={config.think_depth || 0}
                                onChange={(e) => {
                                    const val = parseInt(e.target.value);
                                    setConfig({
                                        ...config,
                                        think_depth: val,
                                        platforms: {
                                            ...config.platforms,
                                            [config.target_platform]: {
                                                ...(config.platforms[config.target_platform] || {}),
                                                think_depth: val
                                            }
                                        }
                                    });
                                }}
                            />
                        )}
                    </div>

                    <div className="space-y-2">
                        <Label>{t('menu_api_think_budget')}</Label>
                        <Input 
                            type="number"
                            value={config.thinking_budget ?? ''}
                            onChange={(e) => {
                                const val = e.target.value;
                                const newBudget = val === '' ? undefined : parseInt(val);
                                setConfig({
                                    ...config,
                                    thinking_budget: newBudget,
                                    platforms: {
                                        ...config.platforms,
                                        [config.target_platform]: {
                                            ...(config.platforms[config.target_platform] || {}),
                                            thinking_budget: newBudget
                                        }
                                    }
                                });
                            }}
                            placeholder="4096"
                        />
                        <p className="text-xs text-muted-foreground">{t('hint_think_budget')}</p>
                    </div>

                    <div className="col-span-1 md:col-span-2">
                        <Alert variant="destructive">
                            <AlertTriangle className="h-4 w-4" />
                            <AlertTitle>Compatibility Warning</AlertTitle>
                            <AlertDescription>
                                {['sakura', 'localllm', 'murasaki'].includes(config.target_platform?.toLowerCase() || '')
                                    ? t('warning_thinking_online_only')
                                    : t('warning_thinking_compatibility')
                                }
                            </AlertDescription>
                        </Alert>
                    </div>
                </div>
            )}
        </CardContent>
      </Card>

      {/* API Failover */}
      <Card>
        <CardHeader>
            <div className="flex items-center justify-between">
                <div className="space-y-1">
                    <CardTitle className="flex items-center gap-2">
                        <RefreshCw className="h-5 w-5 text-accent" />
                        {t('menu_api_pool_settings')}
                    </CardTitle>
                    <CardDescription>Configure backup APIs for reliability</CardDescription>
                </div>
                <Switch 
                    checked={config.enable_api_failover} 
                    onCheckedChange={(checked) => handleChange('enable_api_failover', checked)} 
                />
            </div>
        </CardHeader>
        {config.enable_api_failover && (
            <CardContent className="space-y-6">
                <div className="space-y-2">
                    <Label>{t('setting_api_failover_threshold')}</Label>
                    <Input 
                        type="number"
                        value={config.api_failover_threshold}
                        onChange={(e) => handleChange('api_failover_threshold', parseInt(e.target.value))}
                    />
                </div>

                <div className="space-y-4">
                    <div className="flex gap-2">
                        <Select value={newPoolItem} onValueChange={setNewPoolItem}>
                            <SelectTrigger className="flex-1">
                                <SelectValue placeholder={t('prompt_add_to_pool')} />
                            </SelectTrigger>
                            <SelectContent>
                                {Object.keys(config.platforms)
                                    .filter(p => !config.backup_apis.includes(p) && p !== config.target_platform)
                                    .map(p => (
                                        <SelectItem key={p} value={p}>{p}</SelectItem>
                                    ))
                                }
                            </SelectContent>
                        </Select>
                        <Button onClick={handlePoolAdd} size="icon">
                            <Plus className="h-4 w-4" />
                        </Button>
                    </div>

                    <div className="space-y-2">
                        {config.backup_apis.map((api, idx) => (
                            <div key={idx} className="flex justify-between items-center p-3 bg-muted rounded-md border">
                                <span className="text-sm font-medium">{api}</span>
                                <Button 
                                    variant="ghost" 
                                    size="sm" 
                                    onClick={() => handlePoolRemove(api)}
                                    className="text-destructive hover:text-destructive hover:bg-destructive/10"
                                >
                                    <Trash2 className="h-4 w-4" />
                                </Button>
                            </div>
                        ))}
                        {config.backup_apis.length === 0 && (
                            <p className="text-sm text-muted-foreground italic text-center py-4">{t('msg_api_pool_empty')}</p>
                        )}
                    </div>
                </div>
            </CardContent>
        )}
      </Card>
    </div>
  );
};
