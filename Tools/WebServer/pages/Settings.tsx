import React, { useState } from 'react';
import { Save, RefreshCw, Sparkles } from 'lucide-react';
import { useI18n } from '@/contexts/I18nContext';
import { useGlobal } from '@/contexts/GlobalContext';
import { DataService } from '@/services/DataService';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { SettingsGeneral } from '@/components/Settings/SettingsGeneral';
import { SettingsApi } from '@/components/Settings/SettingsApi';
import { SettingsProject } from '@/components/Settings/SettingsProject';
import { SettingsFeatures } from '@/components/Settings/SettingsFeatures';
import { SettingsSystem } from '@/components/Settings/SettingsSystem';
import { SettingsProfiles } from '@/components/Settings/SettingsProfiles';
import { cn } from '@/lib/utils';

export const Settings: React.FC = () => {
  const { t } = useI18n();
  const { config, activeTheme, unlockThemeWithNotification } = useGlobal();
  const [saving, setSaving] = useState(false);
  const [saveCount, setSaveCount] = useState(0);

  // Easter Egg: Hua Save Trigger
  const handleHuaSaveCount = () => {
    const next = saveCount + 1;
    setSaveCount(next);
    if (next >= 5) {
      unlockThemeWithNotification('hua');
      setSaveCount(0);
    }
  };

  const handleSaveConfig = async () => {
    if (!config) return;
    setSaving(true);
    try {
        await DataService.saveConfig(config);
        // Using native alert for now, could be replaced with Toast later
        alert(t('msg_saved'));
    } catch (e) {
        console.error("Failed to save", e);
        alert("Save failed.");
    } finally {
        setSaving(false);
    }
  };

  if (!config) {
      return <div className="p-12 text-center text-muted-foreground animate-pulse">Loading Configuration...</div>;
  }

  const elysiaActive = activeTheme === 'elysia';

  return (
    <div className="max-w-5xl mx-auto space-y-6 pb-12 animate-in fade-in slide-in-from-bottom-4 duration-500">
      <div className="flex justify-between items-center sticky top-0 bg-background/95 backdrop-blur z-20 py-4 border-b">
        <h1 className="text-3xl font-bold tracking-tight">{t('ui_settings_title')}</h1>
        <Button 
            onClick={() => { handleSaveConfig(); handleHuaSaveCount(); }}
            disabled={saving}
            className={cn("gap-2 shadow-lg", elysiaActive && "bg-pink-500 hover:bg-pink-600")}
        >
          {saving ? <RefreshCw className="h-4 w-4 animate-spin" /> : <Save className="h-4 w-4" />}
          {t('ui_settings_save')}
        </Button>
      </div>

      <Tabs defaultValue="general" className="w-full">
        <TabsList className="w-full justify-start overflow-x-auto h-auto p-1 bg-muted/50 backdrop-blur supports-[backdrop-filter]:bg-muted/50">
            {[
                { id: 'general', label: t('ui_tab_general') },
                { id: 'api', label: t('ui_tab_api') },
                { id: 'project', label: t('ui_tab_project') },
                { id: 'features', label: t('ui_tab_features') },
                { id: 'system', label: t('ui_tab_system') },
                { id: 'profiles', label: t('menu_profiles') }
            ].map(tab => (
                <TabsTrigger 
                    key={tab.id} 
                    value={tab.id}
                    className={cn(
                        "px-4 py-2 data-[state=active]:bg-background data-[state=active]:shadow-sm",
                        elysiaActive && "data-[state=active]:text-pink-500"
                    )}
                >
                    {tab.label}
                    {elysiaActive && <Sparkles className="ml-1 h-3 w-3 inline-block opacity-0 data-[state=active]:opacity-100 animate-pulse text-pink-400" />}
                </TabsTrigger>
            ))}
        </TabsList>

        <div className="mt-6">
            <TabsContent value="general">
                <SettingsGeneral />
            </TabsContent>
            <TabsContent value="api">
                <SettingsApi />
            </TabsContent>
            <TabsContent value="project">
                <SettingsProject />
            </TabsContent>
            <TabsContent value="features">
                <SettingsFeatures />
            </TabsContent>
            <TabsContent value="system">
                <SettingsSystem />
            </TabsContent>
            <TabsContent value="profiles">
                <SettingsProfiles />
            </TabsContent>
        </div>
      </Tabs>
    </div>
  );
};
