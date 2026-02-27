import React, { useState, useEffect, useRef } from 'react';
import { Play, FolderOpen, Save, FileText, Upload, RefreshCw, Terminal, AlertTriangle, Info, CheckCircle2 } from 'lucide-react';
import { DataService } from '../services/DataService';
import { useI18n } from '../contexts/I18nContext';
import { useGlobal } from '../contexts/GlobalContext';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { Label } from '../components/ui/label';
import { Separator } from '../components/ui/separator';
import { ScrollArea } from '../components/ui/scroll-area';
import { Badge } from '../components/ui/badge';

export const StevExtraction: React.FC = () => {
    const { t } = useI18n();
    const { config } = useGlobal();
    
    const [activeTab, setActiveTab] = useState('extract');
    const [logs, setLogs] = useState<string[]>([]);
    const [status, setStatus] = useState<'idle' | 'running' | 'completed' | 'error'>('idle');
    const logsEndRef = useRef<HTMLDivElement>(null);

    // Extract State
    const [extractGameDir, setExtractGameDir] = useState('');
    const [extractSavePath, setExtractSavePath] = useState('');
    const [extractDataPath, setExtractDataPath] = useState('');

    // Inject State
    const [injectGameDir, setInjectGameDir] = useState('');
    const [injectTransPath, setInjectTransPath] = useState('');
    const [injectOutputPath, setInjectOutputPath] = useState('');

    // Update State
    const [updateGameDir, setUpdateGameDir] = useState('');
    const [updateTransPath, setUpdateTransPath] = useState('');
    const [updateSavePath, setUpdateSavePath] = useState('');
    const [updateDataPath, setUpdateDataPath] = useState('');

    useEffect(() => {
        if (logsEndRef.current) {
            logsEndRef.current.scrollIntoView({ behavior: 'smooth' });
        }
    }, [logs]);

    useEffect(() => {
        // Poll for status if running
        let interval: any;
        if (status === 'running') {
            interval = setInterval(async () => {
                try {
                    const res = await DataService.getStevStatus();
                    if (res.logs && res.logs.length > logs.length) {
                        setLogs(res.logs);
                    }
                    if (res.status !== 'running') {
                        setStatus(res.status);
                    }
                } catch (e) {
                    console.error("Polling failed", e);
                }
            }, 1000);
        }
        return () => clearInterval(interval);
    }, [status, logs.length]);

    const handleExtract = async () => {
        if (!extractGameDir || !extractSavePath || !extractDataPath) {
            alert(t('msg_fill_all_fields') || 'Please fill all fields');
            return;
        }
        setLogs([`[${new Date().toLocaleTimeString()}] Starting Extraction...`]);
        setStatus('running');
        try {
            await DataService.startStevTask('extract', {
                game_dir: extractGameDir,
                save_path: extractSavePath,
                data_path: extractDataPath
            });
        } catch (e: any) {
            setLogs(prev => [...prev, `Error: ${e.message}`]);
            setStatus('error');
        }
    };

    const handleInject = async () => {
        if (!injectGameDir || !injectTransPath || !injectOutputPath) {
            alert(t('msg_fill_all_fields') || 'Please fill all fields');
            return;
        }
        setLogs([`[${new Date().toLocaleTimeString()}] Starting Injection...`]);
        setStatus('running');
        try {
            await DataService.startStevTask('inject', {
                game_dir: injectGameDir,
                path: injectTransPath,
                output_path: injectOutputPath
            });
        } catch (e: any) {
            setLogs(prev => [...prev, `Error: ${e.message}`]);
            setStatus('error');
        }
    };

    const handleUpdate = async () => {
        if (!updateGameDir || !updateTransPath || !updateSavePath || !updateDataPath) {
            alert(t('msg_fill_all_fields') || 'Please fill all fields');
            return;
        }
        setLogs([`[${new Date().toLocaleTimeString()}] Starting Update...`]);
        setStatus('running');
        try {
            await DataService.startStevTask('update', {
                game_dir: updateGameDir,
                path: updateTransPath,
                save_path: updateSavePath,
                data_path: updateDataPath
            });
        } catch (e: any) {
            setLogs(prev => [...prev, `Error: ${e.message}`]);
            setStatus('error');
        }
    };

    return (
        <div className="flex flex-col h-[calc(100vh-100px)] gap-4 p-4 max-w-[1600px] mx-auto w-full">
            <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                    <FileText className="h-6 w-6 text-primary" />
                    <h1 className="text-2xl font-bold tracking-tight">{t('menu_text_extraction') || 'Text Extraction Tool'}</h1>
                </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 flex-1 overflow-hidden">
                <div className="lg:col-span-2 flex flex-col overflow-hidden">
                    <Tabs value={activeTab} onValueChange={setActiveTab} className="flex-1 flex flex-col">
                        <TabsList className="grid w-full grid-cols-3">
                            <TabsTrigger value="extract">{t('tab_extract') || 'Export Source'}</TabsTrigger>
                            <TabsTrigger value="inject">{t('tab_inject') || 'Import Translation'}</TabsTrigger>
                            <TabsTrigger value="update">{t('tab_update') || 'Update Project'}</TabsTrigger>
                        </TabsList>
                        
                        <div className="flex-1 mt-2">
                            <TabsContent value="extract" className="mt-0 h-full">
                                <Card className="h-full border-border/50 shadow-sm bg-card/50 backdrop-blur-sm">
                                    <CardHeader>
                                        <CardTitle>{t('title_extract') || 'Extract Text from Game'}</CardTitle>
                                        <CardDescription>{t('desc_extract') || 'Extract text from RPG Maker JSON files to create a translation project.'}</CardDescription>
                                    </CardHeader>
                                    <CardContent className="space-y-6">
                                        <div className="space-y-2">
                                            <Label>{t('label_game_dir') || 'Game Directory (www folder or root)'}</Label>
                                            <div className="flex gap-2">
                                                <Input value={extractGameDir} onChange={e => setExtractGameDir(e.target.value)} placeholder="/path/to/game/www" />
                                            </div>
                                        </div>
                                        <div className="space-y-2">
                                            <Label>{t('label_save_path') || 'Project Save Path (for CSVs)'}</Label>
                                            <div className="flex gap-2">
                                                <Input value={extractSavePath} onChange={e => setExtractSavePath(e.target.value)} placeholder="/path/to/project/save" />
                                            </div>
                                        </div>
                                        <div className="space-y-2">
                                            <Label>{t('label_data_path') || 'Data Output Path (for XLSX)'}</Label>
                                            <div className="flex gap-2">
                                                <Input value={extractDataPath} onChange={e => setExtractDataPath(e.target.value)} placeholder="/path/to/project/data" />
                                            </div>
                                        </div>
                                        <div className="pt-4">
                                            <Button onClick={handleExtract} disabled={status === 'running'} className="w-full gap-2">
                                                <Upload className="h-4 w-4" />
                                                {status === 'running' ? 'Extracting...' : (t('btn_start_extract') || 'Start Extraction')}
                                            </Button>
                                        </div>
                                    </CardContent>
                                </Card>
                            </TabsContent>

                            <TabsContent value="inject" className="mt-0 h-full">
                                <Card className="h-full border-border/50 shadow-sm bg-card/50 backdrop-blur-sm">
                                    <CardHeader>
                                        <CardTitle>{t('title_inject') || 'Inject Translation into Game'}</CardTitle>
                                        <CardDescription>{t('desc_inject') || 'Inject translated text back into game files.'}</CardDescription>
                                    </CardHeader>
                                    <CardContent className="space-y-6">
                                        <div className="space-y-2">
                                            <Label>{t('label_game_dir') || 'Game Directory'}</Label>
                                            <Input value={injectGameDir} onChange={e => setInjectGameDir(e.target.value)} placeholder="/path/to/game/www" />
                                        </div>
                                        <div className="space-y-2">
                                            <Label>{t('label_trans_path') || 'Translation Project Path'}</Label>
                                            <Input value={injectTransPath} onChange={e => setInjectTransPath(e.target.value)} placeholder="/path/to/project" />
                                        </div>
                                        <div className="space-y-2">
                                            <Label>{t('label_output_path') || 'Output Directory (for patched files)'}</Label>
                                            <Input value={injectOutputPath} onChange={e => setInjectOutputPath(e.target.value)} placeholder="/path/to/output" />
                                        </div>
                                        <div className="pt-4">
                                            <Button onClick={handleInject} disabled={status === 'running'} className="w-full gap-2">
                                                <CheckCircle2 className="h-4 w-4" />
                                                {status === 'running' ? 'Injecting...' : (t('btn_start_inject') || 'Start Injection')}
                                            </Button>
                                        </div>
                                    </CardContent>
                                </Card>
                            </TabsContent>

                            <TabsContent value="update" className="mt-0 h-full">
                                <Card className="h-full border-border/50 shadow-sm bg-card/50 backdrop-blur-sm">
                                    <CardHeader>
                                        <CardTitle>{t('title_update') || 'Update Project'}</CardTitle>
                                        <CardDescription>{t('desc_update') || 'Update existing project with new game files (incremental update).'}</CardDescription>
                                    </CardHeader>
                                    <CardContent className="space-y-6">
                                        <div className="space-y-2">
                                            <Label>{t('label_game_dir') || 'New Game Directory'}</Label>
                                            <Input value={updateGameDir} onChange={e => setUpdateGameDir(e.target.value)} placeholder="/path/to/new_version/www" />
                                        </div>
                                        <div className="space-y-2">
                                            <Label>{t('label_trans_path') || 'Existing Project Path'}</Label>
                                            <Input value={updateTransPath} onChange={e => setUpdateTransPath(e.target.value)} placeholder="/path/to/old_project" />
                                        </div>
                                        <div className="space-y-2">
                                            <Label>{t('label_save_path') || 'New Save Path'}</Label>
                                            <Input value={updateSavePath} onChange={e => setUpdateSavePath(e.target.value)} placeholder="/path/to/new_project_save" />
                                        </div>
                                        <div className="space-y-2">
                                            <Label>{t('label_data_path') || 'New Data Path'}</Label>
                                            <Input value={updateDataPath} onChange={e => setUpdateDataPath(e.target.value)} placeholder="/path/to/new_project_data" />
                                        </div>
                                        <div className="pt-4">
                                            <Button onClick={handleUpdate} disabled={status === 'running'} className="w-full gap-2">
                                                <RefreshCw className="h-4 w-4" />
                                                {status === 'running' ? 'Updating...' : (t('btn_start_update') || 'Start Update')}
                                            </Button>
                                        </div>
                                    </CardContent>
                                </Card>
                            </TabsContent>
                        </div>
                    </Tabs>
                </div>

                <div className="lg:col-span-1 flex flex-col overflow-hidden h-full">
                    <Card className="h-full flex flex-col border-border/50 shadow-sm bg-card/50 backdrop-blur-sm">
                        <CardHeader className="pb-2">
                            <CardTitle className="text-sm font-medium flex items-center gap-2">
                                <Terminal className="h-4 w-4" />
                                {t('ui_console_output') || 'Console Output'}
                            </CardTitle>
                        </CardHeader>
                        <CardContent className="flex-1 p-0 overflow-hidden relative">
                            <ScrollArea className="h-full p-4 font-mono text-xs">
                                {logs.length === 0 ? (
                                    <div className="text-muted-foreground italic opacity-50 text-center mt-10">
                                        Waiting for tasks...
                                    </div>
                                ) : (
                                    logs.map((log, i) => (
                                        <div key={i} className="mb-1 whitespace-pre-wrap break-all">
                                            {log}
                                        </div>
                                    ))
                                )}
                                <div ref={logsEndRef} />
                            </ScrollArea>
                            {status === 'running' && (
                                <div className="absolute bottom-4 right-4 animate-pulse">
                                    <Badge variant="outline" className="bg-background text-primary border-primary">Running</Badge>
                                </div>
                            )}
                        </CardContent>
                    </Card>
                </div>
            </div>
        </div>
    );
};
