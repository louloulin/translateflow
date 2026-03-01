import React from 'react';
import { useI18n } from '@/contexts/I18nContext';
import { useGlobal } from '@/contexts/GlobalContext';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Switch } from '@/components/ui/switch';
import { Label } from '@/components/ui/label';
import { Puzzle } from 'lucide-react';
import { AppConfig } from '@/types';

export const SettingsFeatures: React.FC = () => {
  const { t } = useI18n();
  const { config, setConfig } = useGlobal();

  if (!config) return null;

  const handleChange = (field: keyof AppConfig, value: boolean) => {
    setConfig({ ...config, [field]: value });
  };

  const FeatureToggle = ({ field, label, desc }: { field: keyof AppConfig, label: string, desc?: string }) => (
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
      <Card>
        <CardHeader>
            <CardTitle className="flex items-center gap-2">
                <Puzzle className="h-5 w-5 text-primary" />
                {t('ui_tab_features')}
            </CardTitle>
            <CardDescription>Enable or disable advanced translation pipeline features</CardDescription>
        </CardHeader>
        <CardContent className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <FeatureToggle field="pre_translation_switch" label={t('feature_pre_translation_switch')} />
            <FeatureToggle field="post_translation_switch" label={t('feature_post_translation_switch')} />
            <FeatureToggle field="prompt_dictionary_switch" label={t('feature_prompt_dictionary_switch')} />
            <FeatureToggle field="exclusion_list_switch" label={t('feature_exclusion_list_switch')} />
            <FeatureToggle field="characterization_switch" label={t('feature_characterization_switch')} />
            <FeatureToggle field="world_building_switch" label={t('feature_world_building_switch')} />
            <FeatureToggle field="writing_style_switch" label={t('feature_writing_style_switch')} />
            <FeatureToggle field="translation_example_switch" label={t('feature_translation_example_switch')} />
            <FeatureToggle field="few_shot_and_example_switch" label={t('feature_few_shot_and_example_switch')} />
            <FeatureToggle field="auto_process_text_code_segment" label={t('feature_auto_process_text_code_segment')} />
            <FeatureToggle field="enable_bilingual_output" label={t('feature_enable_bilingual_output')} />
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
            <CardTitle>{t('feature_proofread_section')}</CardTitle>
        </CardHeader>
        <CardContent className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <FeatureToggle field="enable_auto_proofread" label={t('feature_enable_auto_proofread')} />
        </CardContent>
      </Card>
    </div>
  );
};
