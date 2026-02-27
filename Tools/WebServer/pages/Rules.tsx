import React, { useState, useEffect, useRef } from 'react';
import { Save, Plus, Trash2, BookOpen, Ban, AlertTriangle, RefreshCw, Search, ToggleLeft, ToggleRight, Download, Upload, History, Users, Map as MapIcon, PenTool, Languages, FileJson, ChevronDown, Sparkles, Play, Square, Settings } from 'lucide-react';
import { GlossaryItem, ExclusionItem, CharacterizationItem, TranslationExampleItem, TermItem, TermOption } from '../types';
import { DataService } from '../services/DataService';
import { useI18n } from '../contexts/I18nContext';
import { useGlobal } from '../contexts/GlobalContext';
import { TermSelector } from '../components/TermSelector';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Textarea } from '../components/ui/textarea';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../components/ui/table';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Switch } from '../components/ui/switch';
import { Label } from '../components/ui/label';
import { Separator } from '../components/ui/separator';
import { Badge } from '../components/ui/badge';
import { ScrollArea } from '../components/ui/scroll-area';
import { cn } from '../lib/utils';

type TabType = 'glossary' | 'exclusion' | 'characterization' | 'world' | 'style' | 'example' | 'ai_glossary';

export const Rules: React.FC = () => {
    const { t } = useI18n();
    const { config, setConfig, activeTheme } = useGlobal();
    const [activeTab, setActiveTab] = useState<TabType>('glossary');

    // Data State
    const [glossary, setGlossary] = useState<GlossaryItem[]>([]);
    const [exclusion, setExclusion] = useState<ExclusionItem[]>([]);
    const [characterization, setCharacterization] = useState<CharacterizationItem[]>([]);
    const [worldBuilding, setWorldBuilding] = useState<string>("");
    const [writingStyle, setWritingStyle] = useState<string>("");
    const [translationExample, setTranslationExample] = useState<TranslationExampleItem[]>([]);
    
    const [loading, setLoading] = useState(false);
    const [saving, setSaving] = useState(false);
    const [hasDraft, setHasDraft] = useState(false);
    
    // Profile State
    const [profiles, setProfiles] = useState<string[]>([]);
    
    // Filter State
    const [filter, setFilter] = useState('');

    // AI Glossary Analysis State
    const [aiInputPath, setAiInputPath] = useState('');
    const [aiPercent, setAiPercent] = useState(30);
    const [aiLines, setAiLines] = useState<number | undefined>(undefined);
    const [aiStatus, setAiStatus] = useState<any>({ status: 'idle', progress: 0, total: 0, message: '', results: [] });
    const [aiMinFreq, setAiMinFreq] = useState(2);
    const [aiFilename, setAiFilename] = useState('auto_glossary');
    const [aiLogs, setAiLogs] = useState<string[]>([]);
    const [aiUseTempConfig, setAiUseTempConfig] = useState(false);
    const [aiTempPlatform, setAiTempPlatform] = useState('');
    const [aiTempApiKey, setAiTempApiKey] = useState('');
    const [aiTempApiUrl, setAiTempApiUrl] = useState('');
    const [aiTempModel, setAiTempModel] = useState('');
    const [aiTempThreads, setAiTempThreads] = useState<number>(5);

    // Term Selector State
    const [showTermSelector, setShowTermSelector] = useState(false);
    const [selectorTerms, setSelectorTerms] = useState<TermItem[]>([]);

    // Refs
    const draftTimerRef = useRef<any>(null);
    const fileInputRef = useRef<HTMLInputElement>(null);

    useEffect(() => {
        loadData();
        loadProfiles();
        checkDrafts();
    }, []);

    // 切换到AI术语分析标签页时加载当前状态
    useEffect(() => {
        if (activeTab === 'ai_glossary') {
            const loadAnalysisStatus = async () => {
                try {
                    const status = await DataService.getAnalysisStatus();
                    setAiStatus(status);
                    if (status.logs && Array.isArray(status.logs)) {
                        setAiLogs(status.logs);
                    }
                    // 如果正在运行，继续轮询
                    if (status.status === 'running') {
                        pollAnalysisStatus();
                    }
                } catch (e) {
                    console.error("Failed to load analysis status", e);
                }
            };
            loadAnalysisStatus();
        }
    }, [activeTab]);

    const loadProfiles = async () => {
        try {
            const list = await DataService.getRulesProfiles();
            setProfiles(list);
        } catch (e) {
            console.error("Failed to load rules profiles", e);
        }
    };

    const handleProfileSwitch = async (profileName: string) => {
        if (config?.active_rules_profile === profileName) return;
        setLoading(true);
        try {
            const newConfig = await DataService.switchRulesProfile(profileName);
            setConfig(newConfig);
            // Reload data for the new profile
            await loadData(); 
        } catch (e) {
            alert("Failed to switch rules profile");
        } finally {
            setLoading(false);
        }
    };

    const loadData = async () => {
        setLoading(true);
        try {
            const [g, e, c, w, s, ex] = await Promise.all([
                DataService.getGlossary(),
                DataService.getExclusion(),
                DataService.getCharacterization(),
                DataService.getWorldBuilding(),
                DataService.getWritingStyle(),
                DataService.getTranslationExample()
            ]);
            setGlossary(g || []);
            setExclusion(e || []);
            setCharacterization(c || []);
            setWorldBuilding(w || "");
            setWritingStyle(s || "");
            setTranslationExample(ex || []);
        } catch (error) {
            console.error("Failed to load rules", error);
        } finally {
            setLoading(false);
        }
    };

    const checkDrafts = async () => {
        try {
            const drafts = await Promise.all([
                DataService.getGlossaryDraft(),
                DataService.getExclusionDraft(),
                DataService.getCharacterizationDraft(),
                DataService.getWorldBuildingDraft(),
                DataService.getWritingStyleDraft(),
                DataService.getTranslationExampleDraft()
            ]);
            if (drafts.some(d => d && (Array.isArray(d) ? d.length > 0 : d.length > 0))) {
                setHasDraft(true);
            }
        } catch {}
    };

    const recoverDraft = async () => {
        if (!confirm(t('msg_recover_draft_confirm'))) return;
        try {
            const [gd, ed, cd, wd, sd, exd] = await Promise.all([
                DataService.getGlossaryDraft(),
                DataService.getExclusionDraft(),
                DataService.getCharacterizationDraft(),
                DataService.getWorldBuildingDraft(),
                DataService.getWritingStyleDraft(),
                DataService.getTranslationExampleDraft()
            ]);
            
            if (gd && gd.length > 0) setGlossary(gd);
            if (ed && ed.length > 0) setExclusion(ed);
            if (cd && cd.length > 0) setCharacterization(cd);
            if (wd) setWorldBuilding(wd);
            if (sd) setWritingStyle(sd);
            if (exd && exd.length > 0) setTranslationExample(exd);
            
            alert(t('msg_draft_recovered'));
        } catch (error) {
            alert("Failed to recover draft.");
        }
    };

    const handleSave = async () => {
        setSaving(true);
        try {
            switch (activeTab) {
                case 'glossary': await DataService.saveGlossary(glossary); break;
                case 'exclusion': await DataService.saveExclusion(exclusion); break;
                case 'characterization': await DataService.saveCharacterization(characterization); break;
                case 'world': await DataService.saveWorldBuilding(worldBuilding); break;
                case 'style': await DataService.saveWritingStyle(writingStyle); break;
                case 'example': await DataService.saveTranslationExample(translationExample); break;
            }
            if (config) {
                await DataService.saveConfig(config);
            }
            alert(t('msg_saved'));
        } catch (error) {
            console.error("Failed to save", error);
            alert("Save failed.");
        } finally {
            setSaving(false);
        }
    };

    const triggerDraftSave = () => {
        if (draftTimerRef.current) clearTimeout(draftTimerRef.current);
        draftTimerRef.current = setTimeout(async () => {
            switch (activeTab) {
                case 'glossary': await DataService.saveGlossaryDraft(glossary); break;
                case 'exclusion': await DataService.saveExclusionDraft(exclusion); break;
                case 'characterization': await DataService.saveCharacterizationDraft(characterization); break;
                case 'world': await DataService.saveWorldBuildingDraft(worldBuilding); break;
                case 'style': await DataService.saveWritingStyleDraft(writingStyle); break;
                case 'example': await DataService.saveTranslationExampleDraft(translationExample); break;
            }
            setHasDraft(true);
        }, 2000); // 2s debounce
    };

    const exportData = () => {
        let data: any;
        let filename = `${activeTab}.json`;
        let isText = false;

        switch (activeTab) {
            case 'glossary': data = glossary; break;
            case 'exclusion': data = exclusion; break;
            case 'characterization': data = characterization; break;
            case 'world': data = worldBuilding; filename = 'world_building.txt'; isText = true; break;
            case 'style': data = writingStyle; filename = 'writing_style.txt'; isText = true; break;
            case 'example': data = translationExample; filename = 'examples.json'; break;
        }

        const blob = new Blob([isText ? data : JSON.stringify(data, null, 4)], { type: isText ? 'text/plain' : 'application/json' });
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = filename;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        URL.revokeObjectURL(url);
    };

    const importData = (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (!file) return;

        const reader = new FileReader();
        reader.onload = (event) => {
            const content = event.target?.result as string;
            
            try {
                if (activeTab === 'world' || activeTab === 'style') {
                    if (activeTab === 'world') setWorldBuilding(content);
                    else setWritingStyle(content);
                } else {
                    const json = JSON.parse(content);
                    if (Array.isArray(json)) {
                        switch (activeTab) {
                            case 'glossary': setGlossary(json); break;
                            case 'exclusion': setExclusion(json); break;
                            case 'characterization': setCharacterization(json); break;
                            case 'example': setTranslationExample(json); break;
                        }
                    } else {
                        alert(t('msg_import_error_list'));
                        return;
                    }
                }
                triggerDraftSave();
                alert(t('msg_import_success'));
            } catch (err) {
                alert(t('msg_import_error_parse'));
            }
        };
        reader.readAsText(file);
        if (fileInputRef.current) fileInputRef.current.value = '';
    };

    // --- Toggle Handlers ---
    const toggleSwitch = (field: keyof typeof config) => {
        if (!config) return;
        // @ts-ignore
        setConfig({ ...config, [field]: !config[field] });
    };

    const isLocal = config?.target_platform && ["sakura", "localllm", "murasaki"].includes(config.target_platform.toLowerCase());
    const isOnlineOnlyTab = ['characterization', 'world', 'style', 'example'].includes(activeTab);

    // --- CRUD Helpers ---
    const addCharacterItem = () => {
        setCharacterization([{ 
            original_name: '', translated_name: '', gender: '', age: '', 
            personality: '', speech_style: '', additional_info: '' 
        }, ...characterization]);
        triggerDraftSave();
    };

    const updateCharacterItem = (originalIdx: number, field: keyof CharacterizationItem, val: string) => {
        const newItems = [...characterization];
        newItems[originalIdx] = { ...newItems[originalIdx], [field]: val };
        setCharacterization(newItems);
        triggerDraftSave();
    };

    const addExampleItem = () => {
        setTranslationExample([{ src: '', dst: '' }, ...translationExample]);
        triggerDraftSave();
    };

    const updateExampleItem = (originalIdx: number, field: keyof TranslationExampleItem, val: string) => {
        const newItems = [...translationExample];
        newItems[originalIdx] = { ...newItems[originalIdx], [field]: val };
        setTranslationExample(newItems);
        triggerDraftSave();
    };

    // --- AI Glossary Analysis Functions ---
    const startAiAnalysis = async () => {
        if (!aiInputPath) { alert('请输入文件路径'); return; }
        try {
            await DataService.startGlossaryAnalysis(
                aiInputPath, aiPercent, aiLines,
                aiUseTempConfig, aiTempPlatform, aiTempApiKey, aiTempApiUrl, aiTempModel, aiTempThreads
            );
            pollAnalysisStatus();
        } catch (e: any) {
            setAiLogs(prev => [...prev, `[${new Date().toLocaleTimeString()}] 错误: ${e.message}`]);
        }
    };

    const pollAnalysisStatus = () => {
        const poll = async () => {
            try {
                const status = await DataService.getAnalysisStatus();
                setAiStatus(status);
                // 从后端获取日志
                if (status.logs && Array.isArray(status.logs)) {
                    setAiLogs(status.logs);
                }
                if (status.status === 'running') {
                    setTimeout(poll, 1000);
                }
            } catch (e) {
                console.error(e);
            }
        };
        poll();
    };

    const stopAiAnalysis = async () => {
        try {
            await DataService.stopGlossaryAnalysis();
            setAiLogs(prev => [...prev, `[${new Date().toLocaleTimeString()}] 已停止分析`]);
        } catch (e: any) {
            setAiLogs(prev => [...prev, `[${new Date().toLocaleTimeString()}] 停止失败: ${e.message}`]);
        }
    };

    const saveAiResults = async () => {
        try {
            const result = await DataService.saveAnalysisResults(aiMinFreq, aiFilename);
            setAiLogs(prev => [...prev, `[${new Date().toLocaleTimeString()}] ${result.message}`]);
            alert(result.message);
            // Reload glossary data
            const g = await DataService.getGlossary();
            setGlossary(g || []);
        } catch (e: any) {
            setAiLogs(prev => [...prev, `[${new Date().toLocaleTimeString()}] 保存失败: ${e.message}`]);
            alert('保存失败: ' + e.message);
        }
    };

    // --- Term Selection Handlers ---
    const enterTermSelection = () => {
        try {
            if (!aiStatus || !Array.isArray(aiStatus.results)) {
                alert('尚未进行分析或分析结果无效');
                return;
            }

            const filtered = aiStatus.results.filter((r: any) => r && r.src && r.count >= aiMinFreq);
            if (filtered.length === 0) {
                alert('没有符合条件的术语');
                return;
            }

            // Create a map of existing glossary terms for quick lookup
            const glossaryMap = new Map();
            if (Array.isArray(glossary)) {
                glossary.forEach(item => {
                    if (item && item.src) glossaryMap.set(item.src, item);
                });
            }

            const initialTerms: TermItem[] = filtered.map((r: any) => {
                const existing = glossaryMap.get(r.src);
                return {
                    src: r.src,
                    type: r.type || (existing ? (existing.info || '专有名词') : '专有名词'),
                    options: existing ? [{ dst: existing.dst, info: existing.info || '术语表' }] : [],
                    selected_index: 0,
                    saved: !!existing
                };
            });
            
            setSelectorTerms(initialTerms);
            setShowTermSelector(true);
        } catch (err: any) {
            console.error("Error entering term selection:", err);
            alert("进入选择界面失败: " + err.message);
        }
    };

    const handleTermRetry = async (item: TermItem) => {
        const avoid = item.options.map(o => o.dst);
        try {
            const res = await DataService.retryTermTranslation(
                item.src, 
                item.type, 
                avoid,
                aiUseTempConfig ? {
                    platform: aiTempPlatform,
                    api_key: aiTempApiKey,
                    api_url: aiTempApiUrl,
                    model: aiTempModel
                } : undefined
            );
            return res;
        } catch (e: any) {
            console.error(e);
            alert("重试失败: " + e.message);
            return null;
        }
    };

    const handleTermSaveSingle = async (item: TermItem) => {
        const selected = item.options[item.selected_index];
        if (!selected) return;
        try {
            await DataService.addGlossaryItem({
                src: item.src,
                dst: selected.dst,
                info: selected.info
            });
            // Update glossary list in state if needed
            const g = await DataService.getGlossary();
            setGlossary(g || []);
        } catch (e) {
            alert('保存失败');
        }
    };

    const handleTermSaveAll = async (termsToSave: TermItem[]) => {
        const items = termsToSave.map(t => {
            const sel = t.options[t.selected_index];
            return { src: t.src, dst: sel?.dst || '', info: sel?.info || '' };
        }).filter(i => i.dst);
        
        if (items.length === 0) {
            alert('没有待保存的已翻译术语');
            return;
        }

        try {
            await DataService.batchAddGlossaryItems(items);
            alert(`成功保存 ${items.length} 条术语`);
            setShowTermSelector(false);
            // Refresh glossary
            const g = await DataService.getGlossary();
            setGlossary(g || []);
        } catch (e) {
            alert('批量保存失败');
        }
    };

    return (
        <div className="flex flex-col h-[calc(100vh-100px)] gap-4 p-4 max-w-[1600px] mx-auto w-full">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div className="flex items-center gap-4">
                    <h1 className="text-2xl font-bold tracking-tight">{t('menu_glossary_rules')}</h1>
                    
                    {/* Profile Selector */}
                    <Select value={config?.active_rules_profile} onValueChange={handleProfileSwitch}>
                        <SelectTrigger className="w-[180px]">
                            <SelectValue placeholder="Select Profile" />
                        </SelectTrigger>
                        <SelectContent>
                            {profiles.map(p => (
                                <SelectItem key={p} value={p}>{p}</SelectItem>
                            ))}
                        </SelectContent>
                    </Select>
                </div>
                
                <div className="flex items-center gap-2">
                    <div className="relative w-48">
                        <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
                        <Input 
                            placeholder={t('ui_rules_filter')}
                            value={filter}
                            onChange={(e) => setFilter(e.target.value)}
                            className="pl-8 h-9"
                        />
                    </div>
                    
                    <Button variant="outline" size="icon" onClick={exportData} title="Export to File">
                        <Download className="h-4 w-4" />
                    </Button>

                    <Button variant="outline" size="icon" onClick={() => fileInputRef.current?.click()} title="Import from File">
                        <Upload className="h-4 w-4" />
                        <input type="file" ref={fileInputRef} className="hidden" accept={activeTab === 'world' || activeTab === 'style' ? ".txt" : ".json"} onChange={importData} />
                    </Button>

                    {hasDraft && (
                        <Button variant="outline" size="icon" onClick={recoverDraft} title="Recover Unsaved Draft" className="text-orange-400 border-orange-400/50 hover:text-orange-500 hover:bg-orange-500/10">
                            <History className="h-4 w-4" />
                        </Button>
                    )}

                    <Button onClick={handleSave} disabled={saving} className="gap-2">
                        {saving ? <RefreshCw className="h-4 w-4 animate-spin" /> : <Save className="h-4 w-4" />}
                        <span className="hidden sm:inline">{t('ui_rules_save')}</span>
                    </Button>
                </div>
            </div>

            <Tabs value={activeTab} onValueChange={(v) => setActiveTab(v as TabType)} className="flex-1 flex flex-col overflow-hidden">
                <TabsList className="w-full justify-start overflow-x-auto no-scrollbar">
                    <TabsTrigger value="glossary" className="gap-2"><BookOpen className="h-4 w-4" /> {t('ui_rules_glossary')}</TabsTrigger>
                    <TabsTrigger value="exclusion" className="gap-2"><Ban className="h-4 w-4" /> {t('ui_rules_exclusion')}</TabsTrigger>
                    <TabsTrigger value="characterization" className="gap-2"><Users className="h-4 w-4" /> {t('feature_characterization_switch')}</TabsTrigger>
                    <TabsTrigger value="world" className="gap-2"><MapIcon className="h-4 w-4" /> {t('feature_world_building_switch')}</TabsTrigger>
                    <TabsTrigger value="style" className="gap-2"><PenTool className="h-4 w-4" /> {t('feature_writing_style_switch')}</TabsTrigger>
                    <TabsTrigger value="example" className="gap-2"><Languages className="h-4 w-4" /> {t('feature_translation_example_switch')}</TabsTrigger>
                    <TabsTrigger value="ai_glossary" className="gap-2"><Sparkles className="h-4 w-4" /> {t('ui_ai_glossary')}</TabsTrigger>
                </TabsList>

                <div className="flex-1 overflow-hidden mt-2 bg-card/50 backdrop-blur-sm border rounded-lg shadow-sm">
                    {loading || !config ? (
                        <div className="flex flex-col items-center justify-center h-full text-muted-foreground gap-3">
                            <RefreshCw className="h-8 w-8 animate-spin text-primary" />
                            <p>Loading...</p>
                        </div>
                    ) : (
                        <ScrollArea className="h-full">
                            <div className="p-4">
                                {isLocal && isOnlineOnlyTab && (
                                    <div className="p-4 bg-destructive/10 border border-destructive/20 rounded-lg flex items-center gap-3 mb-6 shadow-sm">
                                        <AlertTriangle className="h-6 w-6 text-destructive shrink-0" />
                                        <div>
                                            <h4 className="text-sm font-bold text-destructive uppercase tracking-wider">Online Only / 仅限在线接口</h4>
                                            <p className="text-xs text-muted-foreground mt-1 font-medium">{t('msg_online_features_warning')}</p>
                                        </div>
                                    </div>
                                )}
                                
                                {/* Glossary */}
                                <TabsContent value="glossary" className="m-0 space-y-4">
                                    <div className="flex justify-between items-center bg-muted/30 p-3 rounded-lg border">
                                        <div className="flex items-center gap-4">
                                            <div className="flex items-center gap-2">
                                                <Switch 
                                                    checked={config.prompt_dictionary_switch} 
                                                    onCheckedChange={() => toggleSwitch('prompt_dictionary_switch')}
                                                />
                                                <Label>{t('ui_rules_enable_glossary')}</Label>
                                            </div>
                                        </div>
                                        <Button size="sm" onClick={() => { setGlossary([{ src: '', dst: '', info: '' }, ...glossary]); triggerDraftSave(); }} className="gap-1">
                                            <Plus className="h-4 w-4" /> {t('ui_rules_add')}
                                        </Button>
                                    </div>
                                    <div className="space-y-2">
                                        {glossary.map((item, originalIdx) => {
                                            if (filter && !item.src?.toLowerCase().includes(filter.toLowerCase())) return null;
                                            return (
                                                <Card key={originalIdx} className="overflow-hidden">
                                                    <CardContent className="p-3 grid grid-cols-1 md:grid-cols-12 gap-3 items-center">
                                                        <div className="md:col-span-4">
                                                            <Input placeholder={t('ui_rules_source')} value={item.src} onChange={(e) => { const n = [...glossary]; n[originalIdx].src = e.target.value; setGlossary(n); triggerDraftSave(); }} className="border-primary/20 focus-visible:ring-primary/30" />
                                                        </div>
                                                        <div className="md:col-span-4">
                                                            <Input placeholder={t('ui_rules_target')} value={item.dst} onChange={(e) => { const n = [...glossary]; n[originalIdx].dst = e.target.value; setGlossary(n); triggerDraftSave(); }} className="border-primary/20 focus-visible:ring-primary/30" />
                                                        </div>
                                                        <div className="md:col-span-3">
                                                            <Input placeholder={t('ui_rules_note')} value={item.info || ''} onChange={(e) => { const n = [...glossary]; n[originalIdx].info = e.target.value; setGlossary(n); triggerDraftSave(); }} className="text-muted-foreground" />
                                                        </div>
                                                        <div className="md:col-span-1 flex justify-end">
                                                            <Button variant="ghost" size="icon" onClick={() => setGlossary(glossary.filter((_, i) => i !== originalIdx))} className="text-muted-foreground hover:text-destructive">
                                                                <Trash2 className="h-4 w-4" />
                                                            </Button>
                                                        </div>
                                                    </CardContent>
                                                </Card>
                                            );
                                        })}
                                    </div>
                                </TabsContent>

                                {/* Exclusion */}
                                <TabsContent value="exclusion" className="m-0 space-y-4">
                                    <div className="flex justify-between items-center bg-muted/30 p-3 rounded-lg border">
                                        <div className="flex items-center gap-4">
                                            <div className="flex items-center gap-2">
                                                <Switch 
                                                    checked={config.exclusion_list_switch} 
                                                    onCheckedChange={() => toggleSwitch('exclusion_list_switch')}
                                                />
                                                <Label>{t('ui_rules_enable_exclusion')}</Label>
                                            </div>
                                        </div>
                                        <Button size="sm" onClick={() => { setExclusion([{ markers: '', regex: '', info: '' }, ...exclusion]); triggerDraftSave(); }} className="gap-1">
                                            <Plus className="h-4 w-4" /> {t('ui_rules_add')}
                                        </Button>
                                    </div>
                                    <div className="space-y-2">
                                        {exclusion.map((item, originalIdx) => {
                                            if (filter && !item.markers?.toLowerCase().includes(filter.toLowerCase())) return null;
                                            return (
                                                <Card key={originalIdx} className="overflow-hidden">
                                                    <CardContent className="p-3 grid grid-cols-1 md:grid-cols-12 gap-3 items-center">
                                                        <div className="md:col-span-4">
                                                            <Input placeholder={t('ui_rules_marker')} value={item.markers} onChange={(e) => { const n = [...exclusion]; n[originalIdx].markers = e.target.value; setExclusion(n); triggerDraftSave(); }} className="font-mono text-xs border-primary/20" />
                                                        </div>
                                                        <div className="md:col-span-4">
                                                            <Input placeholder={t('ui_rules_regex')} value={item.regex || ''} onChange={(e) => { const n = [...exclusion]; n[originalIdx].regex = e.target.value; setExclusion(n); triggerDraftSave(); }} className="font-mono text-xs border-primary/20" />
                                                        </div>
                                                        <div className="md:col-span-3">
                                                            <Input placeholder={t('ui_rules_note')} value={item.info || ''} onChange={(e) => { const n = [...exclusion]; n[originalIdx].info = e.target.value; setExclusion(n); triggerDraftSave(); }} className="text-muted-foreground" />
                                                        </div>
                                                        <div className="md:col-span-1 flex justify-end">
                                                            <Button variant="ghost" size="icon" onClick={() => setExclusion(exclusion.filter((_, i) => i !== originalIdx))} className="text-muted-foreground hover:text-destructive">
                                                                <Trash2 className="h-4 w-4" />
                                                            </Button>
                                                        </div>
                                                    </CardContent>
                                                </Card>
                                            );
                                        })}
                                    </div>
                                </TabsContent>

                                {/* Characterization */}
                                <TabsContent value="characterization" className="m-0 space-y-4">
                                    <div className="flex justify-between items-center bg-muted/30 p-3 rounded-lg border">
                                        <div className="flex items-center gap-2">
                                            <Switch 
                                                checked={config.characterization_switch} 
                                                onCheckedChange={() => toggleSwitch('characterization_switch')}
                                            />
                                            <Label>{t('feature_characterization_switch')}</Label>
                                        </div>
                                        <Button size="sm" onClick={addCharacterItem} className="gap-1">
                                            <Plus className="h-4 w-4" /> {t('ui_rules_add')}
                                        </Button>
                                    </div>
                                    <div className="grid grid-cols-1 gap-4">
                                        {characterization.map((item, originalIdx) => {
                                            if (filter && !item.original_name?.includes(filter) && !item.translated_name?.includes(filter)) return null;
                                            return (
                                                <Card key={originalIdx}>
                                                    <CardContent className="p-4 space-y-3">
                                                        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                                                            <Input placeholder={t('ui_rules_character_orig')} value={item.original_name} onChange={(e) => updateCharacterItem(originalIdx, 'original_name', e.target.value)} />
                                                            <Input placeholder={t('ui_rules_character_trans')} value={item.translated_name} onChange={(e) => updateCharacterItem(originalIdx, 'translated_name', e.target.value)} />
                                                            <Input placeholder={t('ui_rules_character_gender')} value={item.gender} onChange={(e) => updateCharacterItem(originalIdx, 'gender', e.target.value)} />
                                                            <Input placeholder={t('ui_rules_character_age')} value={item.age} onChange={(e) => updateCharacterItem(originalIdx, 'age', e.target.value)} />
                                                        </div>
                                                        <div className="grid grid-cols-2 gap-3">
                                                            <Input placeholder={t('ui_rules_character_personality')} value={item.personality} onChange={(e) => updateCharacterItem(originalIdx, 'personality', e.target.value)} />
                                                            <Input placeholder={t('ui_rules_character_speech')} value={item.speech_style} onChange={(e) => updateCharacterItem(originalIdx, 'speech_style', e.target.value)} />
                                                        </div>
                                                        <div className="flex gap-3">
                                                            <Input placeholder={t('ui_rules_character_info')} value={item.additional_info} onChange={(e) => updateCharacterItem(originalIdx, 'additional_info', e.target.value)} className="flex-1" />
                                                            <Button variant="ghost" size="icon" onClick={() => setCharacterization(characterization.filter((_, i) => i !== originalIdx))} className="text-muted-foreground hover:text-destructive">
                                                                <Trash2 className="h-4 w-4" />
                                                            </Button>
                                                        </div>
                                                    </CardContent>
                                                </Card>
                                            );
                                        })}
                                    </div>
                                </TabsContent>

                                {/* World Building */}
                                <TabsContent value="world" className="m-0 space-y-4">
                                    <div className="flex justify-between items-center bg-muted/30 p-3 rounded-lg border">
                                        <div className="flex items-center gap-2">
                                            <Switch 
                                                checked={config.world_building_switch} 
                                                onCheckedChange={() => toggleSwitch('world_building_switch')}
                                            />
                                            <Label>{t('feature_world_building_switch')}</Label>
                                        </div>
                                    </div>
                                    <Textarea
                                        value={worldBuilding}
                                        onChange={(e) => { setWorldBuilding(e.target.value); triggerDraftSave(); }}
                                        placeholder={t('ui_rules_world_placeholder')}
                                        className="min-h-[400px] font-mono leading-relaxed"
                                    />
                                </TabsContent>

                                {/* Writing Style */}
                                <TabsContent value="style" className="m-0 space-y-4">
                                    <div className="flex justify-between items-center bg-muted/30 p-3 rounded-lg border">
                                        <div className="flex items-center gap-2">
                                            <Switch 
                                                checked={config.writing_style_switch} 
                                                onCheckedChange={() => toggleSwitch('writing_style_switch')}
                                            />
                                            <Label>{t('feature_writing_style_switch')}</Label>
                                        </div>
                                    </div>
                                    <Textarea
                                        value={writingStyle}
                                        onChange={(e) => { setWritingStyle(e.target.value); triggerDraftSave(); }}
                                        placeholder={t('ui_rules_style_placeholder')}
                                        className="min-h-[400px] font-mono leading-relaxed"
                                    />
                                </TabsContent>

                                {/* Examples */}
                                <TabsContent value="example" className="m-0 space-y-4">
                                    <div className="flex justify-between items-center bg-muted/30 p-3 rounded-lg border">
                                        <div className="flex items-center gap-2">
                                            <Switch 
                                                checked={config.translation_example_switch} 
                                                onCheckedChange={() => toggleSwitch('translation_example_switch')}
                                            />
                                            <Label>{t('feature_translation_example_switch')}</Label>
                                        </div>
                                        <Button size="sm" onClick={addExampleItem} className="gap-1">
                                            <Plus className="h-4 w-4" /> {t('ui_rules_add')}
                                        </Button>
                                    </div>
                                    <div className="space-y-4">
                                        {translationExample.map((item, originalIdx) => {
                                            if (filter && !item.src?.includes(filter) && !item.dst?.includes(filter)) return null;
                                            return (
                                                <Card key={originalIdx}>
                                                    <CardContent className="p-3 grid grid-cols-12 gap-3 items-center">
                                                        <div className="col-span-5">
                                                            <Textarea placeholder={t('ui_rules_example_src')} value={item.src} onChange={(e) => updateExampleItem(originalIdx, 'src', e.target.value)} className="min-h-[80px]" />
                                                        </div>
                                                        <div className="col-span-1 flex items-center justify-center text-muted-foreground">→</div>
                                                        <div className="col-span-5">
                                                            <Textarea placeholder={t('ui_rules_example_dst')} value={item.dst} onChange={(e) => updateExampleItem(originalIdx, 'dst', e.target.value)} className="min-h-[80px]" />
                                                        </div>
                                                        <div className="col-span-1 flex items-center justify-end">
                                                            <Button variant="ghost" size="icon" onClick={() => setTranslationExample(translationExample.filter((_, i) => i !== originalIdx))} className="text-muted-foreground hover:text-destructive">
                                                                <Trash2 className="h-4 w-4" />
                                                            </Button>
                                                        </div>
                                                    </CardContent>
                                                </Card>
                                            );
                                        })}
                                    </div>
                                </TabsContent>

                                {/* AI Glossary */}
                                <TabsContent value="ai_glossary" className="m-0 space-y-4">
                                    {showTermSelector ? (
                                        <TermSelector 
                                            terms={selectorTerms}
                                            onSaveAll={handleTermSaveAll}
                                            onSaveSingle={handleTermSaveSingle}
                                            onRetry={handleTermRetry}
                                            onCancel={() => setShowTermSelector(false)}
                                            themeColor={activeTheme === 'elysia' ? '#ff6699' : '#06b6d4'} // Simplified for now
                                            isLightCityTheme={['herrscher_of_human', 'elysia'].includes(activeTheme)}
                                        />
                                    ) : (
                                        <>
                                            <div className="bg-yellow-500/10 border border-yellow-500/20 text-yellow-500 p-4 rounded-lg flex items-center gap-3">
                                                <AlertTriangle className="h-5 w-5" />
                                                <span className="text-sm font-medium">{t('ai_glossary_warning')}</span>
                                            </div>

                                            <Card>
                                                <CardContent className="p-6 space-y-6">
                                                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                                        <div className="space-y-2">
                                                            <Label>{t('ai_glossary_input_path')}</Label>
                                                            <Input 
                                                                value={aiInputPath} 
                                                                onChange={(e) => setAiInputPath(e.target.value)}
                                                                placeholder="C:/path/to/file.epub" 
                                                            />
                                                        </div>
                                                        <div className="grid grid-cols-2 gap-4">
                                                            <div className="space-y-2">
                                                                <Label>{t('ai_glossary_percent')}</Label>
                                                                <Input 
                                                                    type="number" 
                                                                    value={aiPercent} 
                                                                    onChange={(e) => setAiPercent(Number(e.target.value))}
                                                                    min={1} max={100} 
                                                                />
                                                            </div>
                                                            <div className="space-y-2">
                                                                <Label>{t('ai_glossary_lines')}</Label>
                                                                <Input 
                                                                    type="number" 
                                                                    value={aiLines || ''} 
                                                                    onChange={(e) => setAiLines(e.target.value ? Number(e.target.value) : undefined)}
                                                                    placeholder="Optional" 
                                                                />
                                                            </div>
                                                        </div>
                                                    </div>

                                                    <Separator />

                                                    <div className="space-y-4">
                                                        <div className="flex items-center gap-4">
                                                            <Label>{t('ai_glossary_api_config')}:</Label>
                                                            <div className="flex gap-2">
                                                                <Button 
                                                                    variant={!aiUseTempConfig ? "default" : "outline"} 
                                                                    size="sm"
                                                                    onClick={() => setAiUseTempConfig(false)}
                                                                >
                                                                    {t('ai_glossary_use_current')}
                                                                </Button>
                                                                <Button 
                                                                    variant={aiUseTempConfig ? "default" : "outline"} 
                                                                    size="sm"
                                                                    onClick={() => setAiUseTempConfig(true)}
                                                                >
                                                                    {t('ai_glossary_use_temp')}
                                                                </Button>
                                                            </div>
                                                        </div>

                                                        {aiUseTempConfig && (
                                                            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 p-4 bg-muted/50 rounded-lg border">
                                                                <div className="space-y-2">
                                                                    <Label className="text-xs">{t('ai_glossary_temp_platform')}</Label>
                                                                    <Input 
                                                                        value={aiTempPlatform} 
                                                                        onChange={(e) => setAiTempPlatform(e.target.value)}
                                                                        placeholder="openai / anthropic / google" 
                                                                    />
                                                                </div>
                                                                <div className="space-y-2">
                                                                    <Label className="text-xs">{t('ai_glossary_temp_model')}</Label>
                                                                    <Input 
                                                                        value={aiTempModel} 
                                                                        onChange={(e) => setAiTempModel(e.target.value)}
                                                                        placeholder="gpt-4o / claude-3-5-sonnet" 
                                                                    />
                                                                </div>
                                                                <div className="space-y-2">
                                                                    <Label className="text-xs">{t('ai_glossary_temp_threads')}</Label>
                                                                    <Input 
                                                                        type="number" 
                                                                        value={aiTempThreads} 
                                                                        onChange={(e) => setAiTempThreads(Number(e.target.value))}
                                                                        min={1} max={100} 
                                                                    />
                                                                </div>
                                                                <div className="space-y-2">
                                                                    <Label className="text-xs">{t('ai_glossary_temp_url')}</Label>
                                                                    <Input 
                                                                        value={aiTempApiUrl} 
                                                                        onChange={(e) => setAiTempApiUrl(e.target.value)}
                                                                        placeholder="https://api.openai.com" 
                                                                    />
                                                                </div>
                                                                <div className="space-y-2 md:col-span-2">
                                                                    <Label className="text-xs">{t('ai_glossary_temp_key')}</Label>
                                                                    <Input 
                                                                        type="password" 
                                                                        value={aiTempApiKey} 
                                                                        onChange={(e) => setAiTempApiKey(e.target.value)}
                                                                        placeholder="sk-..." 
                                                                    />
                                                                </div>
                                                            </div>
                                                        )}
                                                    </div>

                                                    <div className="flex gap-2">
                                                        <Button 
                                                            onClick={startAiAnalysis} 
                                                            disabled={aiStatus.status === 'running'}
                                                            className="gap-2"
                                                        >
                                                            <Play className="h-4 w-4" /> {t('ai_glossary_start')}
                                                        </Button>
                                                        <Button 
                                                            onClick={stopAiAnalysis} 
                                                            disabled={aiStatus.status !== 'running'}
                                                            variant="destructive"
                                                            className="gap-2"
                                                        >
                                                            <Square className="h-4 w-4" /> {t('ai_glossary_stop')}
                                                        </Button>
                                                    </div>
                                                </CardContent>
                                            </Card>

                                            <Card>
                                                <CardHeader className="pb-3">
                                                    <CardTitle className="text-sm font-medium flex items-center justify-between">
                                                        <span>{t('ai_glossary_status')}: {aiStatus.message || t(`ai_glossary_${aiStatus.status}`)}</span>
                                                        {aiStatus.total > 0 && <span className="text-muted-foreground">{aiStatus.progress}/{aiStatus.total}</span>}
                                                    </CardTitle>
                                                </CardHeader>
                                                <CardContent>
                                                    {aiStatus.total > 0 && (
                                                        <div className="w-full h-2 bg-secondary rounded-full overflow-hidden mb-4">
                                                            <div 
                                                                className="h-full bg-primary transition-all duration-300" 
                                                                style={{ width: `${(aiStatus.progress / aiStatus.total) * 100}%` }} 
                                                            />
                                                        </div>
                                                    )}
                                                    <ScrollArea className="h-32 rounded border bg-muted/50 p-2 font-mono text-xs text-muted-foreground">
                                                        {aiLogs.map((log, i) => <div key={i}>{log}</div>)}
                                                    </ScrollArea>
                                                </CardContent>
                                            </Card>

                                            {aiStatus.status === 'completed' && aiStatus.results.length > 0 && (
                                                <Card>
                                                    <CardHeader className="pb-3">
                                                        <div className="flex items-center justify-between">
                                                            <CardTitle className="text-sm font-medium">
                                                                {t('ai_glossary_results')} ({aiStatus.results.length})
                                                            </CardTitle>
                                                            <div className="flex items-center gap-2">
                                                                <Label className="text-xs whitespace-nowrap">{t('ai_glossary_min_freq')}:</Label>
                                                                <Input 
                                                                    type="number" 
                                                                    value={aiMinFreq} 
                                                                    onChange={(e) => setAiMinFreq(Number(e.target.value))}
                                                                    className="w-16 h-8 text-xs" 
                                                                    min={1} 
                                                                />
                                                                <Input 
                                                                    value={aiFilename} 
                                                                    onChange={(e) => setAiFilename(e.target.value)}
                                                                    className="w-32 h-8 text-xs" 
                                                                    placeholder="filename" 
                                                                />
                                                                <Button size="sm" onClick={saveAiResults} className="gap-1 h-8">
                                                                    <Save className="h-3 w-3" /> {t('ai_glossary_save')}
                                                                </Button>
                                                                <Button size="sm" variant="outline" onClick={enterTermSelection} className="gap-1 h-8">
                                                                    <Sparkles className="h-3 w-3" /> 选择翻译
                                                                </Button>
                                                            </div>
                                                        </div>
                                                    </CardHeader>
                                                    <CardContent>
                                                        <ScrollArea className="h-64">
                                                            <Table>
                                                                <TableHeader>
                                                                    <TableRow>
                                                                        <TableHead>{t('ai_glossary_term')}</TableHead>
                                                                        <TableHead>{t('ai_glossary_type')}</TableHead>
                                                                        <TableHead className="text-right">{t('ai_glossary_count')}</TableHead>
                                                                    </TableRow>
                                                                </TableHeader>
                                                                <TableBody>
                                                                    {aiStatus.results.filter((r: any) => r.count >= aiMinFreq).map((r: any, i: number) => (
                                                                        <TableRow key={i}>
                                                                            <TableCell className="font-medium">{r.src}</TableCell>
                                                                            <TableCell className="text-muted-foreground">{r.type}</TableCell>
                                                                            <TableCell className="text-right">{r.count}</TableCell>
                                                                        </TableRow>
                                                                    ))}
                                                                </TableBody>
                                                            </Table>
                                                        </ScrollArea>
                                                    </CardContent>
                                                </Card>
                                            )}
                                        </>
                                    )}
                                </TabsContent>
                            </div>
                        </ScrollArea>
                    )}
                </div>
            </Tabs>
        </div>
    );
};
