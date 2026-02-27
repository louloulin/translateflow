import React, { useState, useEffect } from 'react';
import { Save, Plus, Trash2, FileText, Search, RefreshCw, ChevronRight, AlertTriangle, Check, X, Edit3, Sparkles } from 'lucide-react';
import { DataService } from '../services/DataService';
import { useI18n } from '../contexts/I18nContext';
import { useGlobal } from '../contexts/GlobalContext';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Textarea } from '../components/ui/textarea';
import { ScrollArea } from '../components/ui/scroll-area';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger, DialogFooter } from '../components/ui/dialog';
import { Separator } from '../components/ui/separator';
import { Badge } from '../components/ui/badge';
import { cn } from '../lib/utils';

export const Prompts: React.FC = () => {
    const { t } = useI18n();
    const { config, setConfig, activeTheme } = useGlobal();
    
    const [categories, setCategories] = useState<string[]>([]);
    const [activeCategory, setActiveCategory] = useState<string>('');
    const [prompts, setPrompts] = useState<string[]>([]);
    const [selectedPrompt, setSelectedPrompt] = useState<string | null>(null);
    const [content, setContent] = useState<string>('');
    const [loading, setLoading] = useState(false);
    const [saving, setSaving] = useState(false);
    const [filter, setFilter] = useState('');
    
    const [isCreating, setIsCreating] = useState(false);
    const [newName, setNewName] = useState('');

    const elysiaActive = activeTheme === 'elysia';

    useEffect(() => {
        loadCategories();
    }, []);

    useEffect(() => {
        if (activeCategory) {
            loadPrompts(activeCategory);
            setSelectedPrompt(null);
            setContent('');
        }
    }, [activeCategory]);

    const loadCategories = async () => {
        try {
            const cats = await DataService.listPromptCategories();
            setCategories(cats);
            if (cats.length > 0 && !activeCategory) {
                setActiveCategory(cats.includes('Translate') ? 'Translate' : cats[0]);
            }
        } catch (e) {
            console.error("Failed to load categories", e);
        }
    };

    const loadPrompts = async (cat: string) => {
        setLoading(true);
        try {
            const list = await DataService.listPrompts(cat);
            setPrompts(list);
        } catch (e) {
            console.error("Failed to load prompts", e);
        } finally {
            setLoading(false);
        }
    };

    const loadPromptContent = async (filename: string) => {
        setLoading(true);
        try {
            const data = await DataService.getPromptContent(activeCategory, filename);
            setContent(data);
            setSelectedPrompt(filename);
            setIsCreating(false);
        } catch (e) {
            console.error("Failed to load prompt content", e);
        } finally {
            setLoading(false);
        }
    };

    const handleSave = async () => {
        if (!selectedPrompt) return;
        setSaving(true);
        try {
            await DataService.savePromptContent(activeCategory, selectedPrompt, content);
            // using toast would be better here, but for now alert is fine or we can add a simple notification system later
            // For now, let's just use alert as in the original code, or console log
            console.log('Saved successfully');
        } catch (e) {
            console.error('Save failed', e);
        } finally {
            setSaving(false);
        }
    };

    const handleApply = async () => {
        if (!selectedPrompt || !config) return;
        const key = activeCategory === 'Polishing' ? 'polishing_prompt_selection' : 'translation_prompt_selection';
        const newConfig = {
            ...config,
            [key]: {
                last_selected_id: selectedPrompt.replace('.txt', ''),
                prompt_content: content
            }
        };
        try {
            await DataService.saveConfig(newConfig);
            setConfig(newConfig);
        } catch (e) {
            console.error('Apply failed', e);
        }
    };

    const handleCreate = async () => {
        if (!newName.trim()) return;
        const filename = newName.endsWith('.txt') ? newName : newName + '.txt';
        try {
            await DataService.savePromptContent(activeCategory, filename, '');
            await loadPrompts(activeCategory);
            setIsCreating(false);
            setNewName('');
            loadPromptContent(filename);
        } catch (e) {
            console.error('Create failed', e);
        }
    };

    const isSystem = activeCategory === 'System';
    const isSelectionTarget = ['Translate', 'Polishing'].includes(activeCategory);

    const filteredPrompts = prompts.filter(p => p.toLowerCase().includes(filter.toLowerCase()));

    return (
        <div className="flex flex-col h-[calc(100vh-100px)] gap-4 p-4 max-w-[1600px] mx-auto w-full">
            <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                    <Edit3 className="h-6 w-6 text-primary" />
                    <h1 className="text-2xl font-bold tracking-tight">{t('menu_prompt_features') || 'Prompt Management'}</h1>
                </div>
                {selectedPrompt && !isSystem && (
                    <div className="flex gap-2">
                        {isSelectionTarget && (
                            <Button variant="outline" onClick={handleApply} className="gap-2">
                                <Check className="h-4 w-4" /> {t('opt_apply') || 'Apply'}
                            </Button>
                        )}
                        <Button onClick={handleSave} disabled={saving} className="gap-2">
                            {saving ? <RefreshCw className="h-4 w-4 animate-spin" /> : <Save className="h-4 w-4" />}
                            {t('ui_settings_save') || 'Save'}
                        </Button>
                    </div>
                )}
            </div>

            <div className="flex flex-1 gap-4 overflow-hidden">
                {/* Sidebar */}
                <Card className="w-80 flex flex-col border-border/50 shadow-sm bg-card/50 backdrop-blur-sm">
                    <CardHeader className="pb-2">
                        <CardTitle className="text-sm font-medium text-muted-foreground uppercase tracking-wider">
                            Categories
                        </CardTitle>
                    </CardHeader>
                    <div className="px-4 pb-4">
                        <div className="flex flex-wrap gap-2">
                            {categories.map(cat => (
                                <Button
                                    key={cat}
                                    variant={activeCategory === cat ? "default" : "secondary"}
                                    size="sm"
                                    onClick={() => setActiveCategory(cat)}
                                    className={cn("text-xs", activeCategory === cat ? "" : "text-muted-foreground")}
                                >
                                    {cat}
                                </Button>
                            ))}
                        </div>
                    </div>
                    
                    <Separator />
                    
                    <div className="p-4 flex flex-col gap-2 flex-1 overflow-hidden">
                        <div className="relative">
                            <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
                            <Input
                                placeholder="Filter prompts..."
                                value={filter}
                                onChange={e => setFilter(e.target.value)}
                                className="pl-8 h-9"
                            />
                        </div>
                        
                        {!isSystem && (
                            <Dialog open={isCreating} onOpenChange={setIsCreating}>
                                <DialogTrigger asChild>
                                    <Button variant="outline" className="w-full justify-start gap-2 h-9 border-dashed text-muted-foreground hover:text-primary">
                                        <Plus className="h-4 w-4" /> {t('menu_prompt_create') || 'New Prompt'}
                                    </Button>
                                </DialogTrigger>
                                <DialogContent>
                                    <DialogHeader>
                                        <DialogTitle>Create New Prompt</DialogTitle>
                                    </DialogHeader>
                                    <div className="py-4">
                                        <Input
                                            placeholder="Enter prompt name..."
                                            value={newName}
                                            onChange={e => setNewName(e.target.value)}
                                            onKeyDown={e => e.key === 'Enter' && handleCreate()}
                                            autoFocus
                                        />
                                    </div>
                                    <DialogFooter>
                                        <Button variant="outline" onClick={() => setIsCreating(false)}>Cancel</Button>
                                        <Button onClick={handleCreate}>Create</Button>
                                    </DialogFooter>
                                </DialogContent>
                            </Dialog>
                        )}

                        <ScrollArea className="flex-1 pr-2">
                            <div className="flex flex-col gap-1 py-1">
                                {filteredPrompts.map(p => (
                                    <Button
                                        key={p}
                                        variant={selectedPrompt === p ? "secondary" : "ghost"}
                                        className={cn(
                                            "justify-between h-auto py-2 px-3 font-normal",
                                            selectedPrompt === p && "bg-primary/10 text-primary font-medium"
                                        )}
                                        onClick={() => loadPromptContent(p)}
                                    >
                                        <div className="flex items-center gap-2 truncate">
                                            <FileText className={cn("h-4 w-4 shrink-0", selectedPrompt === p ? "text-primary" : "text-muted-foreground")} />
                                            <span className="truncate">{p.replace(/\.(txt|json)$/, '')}</span>
                                        </div>
                                        {selectedPrompt === p && <ChevronRight className="h-3 w-3 opacity-50" />}
                                    </Button>
                                ))}
                                {filteredPrompts.length === 0 && (
                                    <div className="text-center py-8 text-muted-foreground text-sm">
                                        No prompts found
                                    </div>
                                )}
                            </div>
                        </ScrollArea>
                    </div>
                </Card>

                {/* Editor */}
                <Card className="flex-1 flex flex-col overflow-hidden border-border/50 shadow-sm bg-card/50 backdrop-blur-sm">
                    {selectedPrompt ? (
                        <>
                            <div className="flex items-center justify-between p-4 border-b">
                                <div>
                                    <div className="flex items-center gap-2">
                                        <Badge variant="outline" className="text-[10px] uppercase">{activeCategory}</Badge>
                                        <h2 className="font-semibold text-lg">{selectedPrompt}</h2>
                                    </div>
                                </div>
                                {isSystem && (
                                    <Badge variant="destructive" className="gap-1">
                                        <AlertTriangle className="h-3 w-3" />
                                        {t('label_readonly') || 'Read Only'}
                                    </Badge>
                                )}
                            </div>
                            <div className="flex-1 p-0 relative">
                                {loading && (
                                    <div className="absolute inset-0 bg-background/50 backdrop-blur-sm z-10 flex items-center justify-center">
                                        <RefreshCw className="h-8 w-8 animate-spin text-primary" />
                                    </div>
                                )}
                                <Textarea
                                    value={content}
                                    onChange={e => setContent(e.target.value)}
                                    readOnly={isSystem}
                                    className="w-full h-full resize-none border-0 focus-visible:ring-0 rounded-none p-6 font-mono text-sm leading-relaxed"
                                    placeholder="Enter prompt content here..."
                                />
                            </div>
                        </>
                    ) : (
                        <div className="flex-1 flex flex-col items-center justify-center text-muted-foreground gap-4">
                            <div className="h-16 w-16 rounded-full bg-secondary/50 flex items-center justify-center">
                                <FileText className="h-8 w-8" />
                            </div>
                            <p className="text-sm font-medium">Select a prompt to view or edit</p>
                            {elysiaActive && <Sparkles className="text-pink-400 animate-pulse h-6 w-6" />}
                        </div>
                    )}
                </Card>
            </div>
        </div>
    );
};
