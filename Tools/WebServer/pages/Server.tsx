import React, { useState, useEffect } from 'react';
import { Server as ServerIcon, Cpu, HardDrive, RefreshCw, Power, GitMerge, CheckCircle2, XCircle, Terminal } from 'lucide-react';
import { DataService } from '../services/DataService';
import { useI18n } from '../contexts/I18nContext';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card';
import { Progress } from '../components/ui/progress';
import { Badge } from '../components/ui/badge';
import { ScrollArea } from '../components/ui/scroll-area';

export const Server: React.FC = () => {
    const { t } = useI18n();
    const [status, setStatus] = useState<any>(null);
    const [loading, setLoading] = useState(false);
    const [updateOutput, setUpdateOutput] = useState('');
    const [restarting, setRestarting] = useState(false);

    useEffect(() => {
        loadStatus();
        const interval = setInterval(loadStatus, 5000);
        return () => clearInterval(interval);
    }, []);

    const loadStatus = async () => {
        try {
            const res = await fetch('/api/system/status');
            const data = await res.json();
            setStatus(data);
        } catch (e) {
            console.error("Failed to load system status", e);
        }
    };

    const handleUpdate = async () => {
        setLoading(true);
        setUpdateOutput('Checking for updates...');
        try {
            const res = await fetch('/api/system/update', { method: 'POST' });
            const data = await res.json();
            setUpdateOutput(data.output || (data.success ? 'Update successful' : 'Update failed'));
        } catch (e: any) {
            setUpdateOutput(`Update failed: ${e.message}`);
        } finally {
            setLoading(false);
        }
    };

    const handleRestart = async () => {
        if (!confirm('Are you sure you want to restart the server?')) return;
        setRestarting(true);
        try {
            await fetch('/api/system/restart', { method: 'POST' });
            // Wait for server to restart
            setTimeout(() => {
                window.location.reload();
            }, 3000);
        } catch (e) {
            console.error("Restart failed", e);
            setRestarting(false);
        }
    };

    const formatUptime = (seconds: number) => {
        const d = Math.floor(seconds / (3600*24));
        const h = Math.floor(seconds % (3600*24) / 3600);
        const m = Math.floor(seconds % 3600 / 60);
        return `${d}d ${h}h ${m}m`;
    };

    return (
        <div className="flex flex-col h-[calc(100vh-100px)] gap-6 p-6 max-w-[1200px] mx-auto w-full">
            <div className="flex items-center gap-3">
                <div className="p-2 bg-primary/10 rounded-lg">
                    <ServerIcon className="h-6 w-6 text-primary" />
                </div>
                <div>
                    <h1 className="text-2xl font-bold tracking-tight">Server Control</h1>
                    <p className="text-muted-foreground text-sm">Manage backend server status and updates</p>
                </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                {/* System Status Cards */}
                <Card>
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium">CPU Usage</CardTitle>
                        <Cpu className="h-4 w-4 text-muted-foreground" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold">{status?.cpu_percent?.toFixed(1) || 0}%</div>
                        <Progress value={status?.cpu_percent || 0} className="h-2 mt-2" />
                    </CardContent>
                </Card>
                <Card>
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium">Memory Usage</CardTitle>
                        <Cpu className="h-4 w-4 text-muted-foreground" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold">{status?.memory_percent?.toFixed(1) || 0}%</div>
                        <Progress value={status?.memory_percent || 0} className="h-2 mt-2" />
                    </CardContent>
                </Card>
                <Card>
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium">Disk Usage</CardTitle>
                        <HardDrive className="h-4 w-4 text-muted-foreground" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold">{status?.disk_percent?.toFixed(1) || 0}%</div>
                        <Progress value={status?.disk_percent || 0} className="h-2 mt-2" />
                    </CardContent>
                </Card>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 flex-1">
                {/* Server Actions */}
                <Card className="flex flex-col">
                    <CardHeader>
                        <CardTitle>Actions</CardTitle>
                        <CardDescription>Control the backend server process</CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-4 flex-1">
                        <div className="flex items-center justify-between p-4 border rounded-lg bg-card/50">
                            <div className="space-y-1">
                                <div className="font-medium flex items-center gap-2">
                                    <GitMerge className="h-4 w-4" /> Update Server
                                </div>
                                <div className="text-xs text-muted-foreground">Pull latest changes from git repository</div>
                            </div>
                            <Button onClick={handleUpdate} disabled={loading} variant="outline">
                                {loading ? <RefreshCw className="h-4 w-4 animate-spin mr-2" /> : null}
                                {loading ? 'Updating...' : 'Check for Updates'}
                            </Button>
                        </div>

                        <div className="flex items-center justify-between p-4 border rounded-lg bg-destructive/5 border-destructive/20">
                            <div className="space-y-1">
                                <div className="font-medium flex items-center gap-2 text-destructive">
                                    <Power className="h-4 w-4" /> Restart Server
                                </div>
                                <div className="text-xs text-muted-foreground">Restart the backend process immediately</div>
                            </div>
                            <Button onClick={handleRestart} disabled={restarting} variant="destructive">
                                {restarting ? <RefreshCw className="h-4 w-4 animate-spin mr-2" /> : null}
                                {restarting ? 'Restarting...' : 'Restart'}
                            </Button>
                        </div>

                        {status?.boot_time && (
                            <div className="text-xs text-center text-muted-foreground mt-4">
                                Server Uptime: {formatUptime(Date.now()/1000 - status.boot_time)}
                            </div>
                        )}
                    </CardContent>
                </Card>

                {/* Console Output */}
                <Card className="flex flex-col overflow-hidden">
                    <CardHeader className="pb-2">
                        <CardTitle className="flex items-center gap-2">
                            <Terminal className="h-4 w-4" /> Console Output
                        </CardTitle>
                    </CardHeader>
                    <CardContent className="flex-1 p-0 relative min-h-[300px]">
                        <ScrollArea className="h-full w-full absolute inset-0">
                            <div className="p-4 font-mono text-xs whitespace-pre-wrap">
                                {updateOutput || <span className="text-muted-foreground italic">No output to display. Run an action to see logs.</span>}
                            </div>
                        </ScrollArea>
                    </CardContent>
                </Card>
            </div>
        </div>
    );
};
