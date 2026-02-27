import React, { useState, useEffect } from 'react';
import { useI18n } from '@/contexts/I18nContext';
import { useGlobal } from '@/contexts/GlobalContext';
import { DataService } from '@/services/DataService';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Plus, RefreshCw, FileJson, Edit2, Trash2, Check, X, Loader2, Sparkles, AlertTriangle } from 'lucide-react';
import { cn } from '@/lib/utils';

export const SettingsProfiles: React.FC = () => {
  const { t } = useI18n();
  const { config, setConfig, activeTheme, triggerRipple, unlockThemeWithNotification, unlockedThemes } = useGlobal();
  
  const [profiles, setProfiles] = useState<string[]>([]);
  const [loadingProfiles, setLoadingProfiles] = useState(false);
  const [switchingProfile, setSwitchingProfile] = useState<string | null>(null);
  
  const [isCreating, setIsCreating] = useState(false);
  const [renamingId, setRenamingId] = useState<string | null>(null);
  const [tempName, setTempName] = useState('');
  const [actionError, setActionError] = useState<string | null>(null);

  const elysiaActive = activeTheme === 'elysia';

  useEffect(() => {
    loadProfiles();
  }, []);

  const loadProfiles = async () => {
      setLoadingProfiles(true);
      try {
          const list = await DataService.getProfiles();
          setProfiles(list);
      } catch (e) {
          console.error("Failed to load profiles", e);
      } finally {
          setLoadingProfiles(false);
      }
  };

  const handleSwitchProfile = async (profileName: string) => {
      if (switchingProfile || renamingId || isCreating) return;
      if (config?.active_profile === profileName) return;
      setSwitchingProfile(profileName);
      try {
          const newConfig = await DataService.switchProfile(profileName);
          setConfig(newConfig);
      } catch (e) {
          console.error("Failed to switch profile", e);
      } finally {
          setSwitchingProfile(null);
      }
  };

  const handleCreateProfile = async () => {
      if (!tempName.trim()) { setActionError("Name cannot be empty"); return; }
      try {
          await DataService.createProfile(tempName, config?.active_profile);
          await loadProfiles();
          setIsCreating(false);
          setTempName('');
      } catch (e: any) { setActionError(e.message); }
  };

  const handleRenameProfile = async (oldName: string) => {
      if (!tempName.trim() || tempName === oldName) { setRenamingId(null); return; }
      try {
          await DataService.renameProfile(oldName, tempName);
          if (config?.active_profile === oldName) { setConfig({ ...config, active_profile: tempName }); }
          await loadProfiles();
          setRenamingId(null);
      } catch (e: any) { setActionError(e.message); }
  };

  const handleDeleteProfile = async (name: string, e: React.MouseEvent) => {
      e.stopPropagation();
      if (!window.confirm(t('msg_profile_delete_confirm').replace('{}', name))) return;
      try { await DataService.deleteProfile(name); await loadProfiles(); } catch (e: any) { alert(e.message); }
  };

  const getCharacterName = (id: string) => {
    // ... (Reuse or import mapping if possible, for now simplify or inline)
    const map: Record<string, string> = {
        'elysia': '无瑕·爱莉希雅',
        'eden': '黄金·伊甸',
        'mobius': '无限·梅比乌斯',
        // ... add others if needed
    };
    return map[id] || id;
  };

  return (
    <div className="space-y-6">
        <div className="flex justify-between items-center">
            <h2 className="text-xl font-bold tracking-tight">{t('menu_profiles')}</h2>
            <div className="flex gap-2">
                <Dialog open={isCreating} onOpenChange={setIsCreating}>
                    <DialogTrigger asChild>
                        <Button variant="outline" size="sm">
                            <Plus className="h-4 w-4 mr-2" /> {t('menu_profile_create')}
                        </Button>
                    </DialogTrigger>
                    <DialogContent>
                        <DialogHeader>
                            <DialogTitle>Create New Profile</DialogTitle>
                            <DialogDescription>Create a new configuration profile based on current settings.</DialogDescription>
                        </DialogHeader>
                        <div className="space-y-4 py-4">
                            <div className="space-y-2">
                                <Label>Profile Name</Label>
                                <Input 
                                    value={tempName}
                                    onChange={(e) => setTempName(e.target.value)}
                                    placeholder="e.g. MyNovelProject"
                                />
                                {actionError && <p className="text-destructive text-xs">{actionError}</p>}
                            </div>
                        </div>
                        <DialogFooter>
                            <Button variant="outline" onClick={() => setIsCreating(false)}>Cancel</Button>
                            <Button onClick={handleCreateProfile}>Create</Button>
                        </DialogFooter>
                    </DialogContent>
                </Dialog>
                <Button variant="ghost" size="icon" onClick={loadProfiles} disabled={loadingProfiles}>
                    <RefreshCw className={cn("h-4 w-4", loadingProfiles && "animate-spin")} />
                </Button>
            </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {profiles.map((profileName) => {
                const isSelected = config?.active_profile === profileName;
                const isRenaming = renamingId === profileName;

                return (
                    <Card 
                        key={profileName}
                        className={cn(
                            "cursor-pointer transition-all hover:border-primary/50",
                            isSelected && "border-primary bg-primary/5 shadow-md"
                        )}
                        onClick={() => !isRenaming && handleSwitchProfile(profileName)}
                    >
                        <CardContent className="p-4">
                            <div className="flex justify-between items-start">
                                <div className="flex items-center gap-3">
                                    <div className={cn("p-2 rounded-md", isSelected ? "bg-primary/20 text-primary" : "bg-muted text-muted-foreground")}>
                                        <FileJson className="h-5 w-5" />
                                    </div>
                                    <div>
                                        {isRenaming ? (
                                            <div className="flex items-center gap-2" onClick={e => e.stopPropagation()}>
                                                <Input 
                                                    className="h-7 text-xs w-[120px]"
                                                    value={tempName}
                                                    onChange={(e) => setTempName(e.target.value)}
                                                    autoFocus
                                                />
                                                <Button size="icon" variant="ghost" className="h-6 w-6" onClick={() => handleRenameProfile(profileName)}>
                                                    <Check className="h-3 w-3 text-green-500" />
                                                </Button>
                                                <Button size="icon" variant="ghost" className="h-6 w-6" onClick={() => setRenamingId(null)}>
                                                    <X className="h-3 w-3 text-red-500" />
                                                </Button>
                                            </div>
                                        ) : (
                                            <>
                                                <h4 className="font-semibold text-sm">{profileName}</h4>
                                                <span className="text-xs text-muted-foreground uppercase">JSON Config</span>
                                            </>
                                        )}
                                    </div>
                                </div>
                                
                                {switchingProfile === profileName ? (
                                    <Loader2 className="h-4 w-4 animate-spin text-primary" />
                                ) : isSelected && (
                                    <div className="flex flex-col items-end gap-2">
                                        <Badge variant="default" className="text-[10px]">Active</Badge>
                                        {unlockedThemes.length > 1 && (
                                            <Select 
                                                value={activeTheme} 
                                                onValueChange={(val) => triggerRipple(window.innerWidth/2, window.innerHeight/2, val as any)}
                                            >
                                                <SelectTrigger className="h-6 w-[100px] text-[10px]" onClick={e => e.stopPropagation()}>
                                                    <SelectValue />
                                                </SelectTrigger>
                                                <SelectContent>
                                                    {unlockedThemes.map(tId => (
                                                        <SelectItem key={tId} value={tId}>{getCharacterName(tId)}</SelectItem>
                                                    ))}
                                                </SelectContent>
                                            </Select>
                                        )}
                                    </div>
                                )}
                            </div>

                            {!isRenaming && (
                                <div className="flex justify-end gap-1 mt-4 opacity-0 group-hover:opacity-100 transition-opacity">
                                    <Button 
                                        size="icon" 
                                        variant="ghost" 
                                        className="h-7 w-7" 
                                        onClick={(e) => { e.stopPropagation(); setRenamingId(profileName); setTempName(profileName); }}
                                    >
                                        <Edit2 className="h-3 w-3" />
                                    </Button>
                                    <Button 
                                        size="icon" 
                                        variant="ghost" 
                                        className="h-7 w-7 text-destructive hover:text-destructive" 
                                        disabled={isSelected}
                                        onClick={(e) => handleDeleteProfile(profileName, e)}
                                    >
                                        <Trash2 className="h-3 w-3" />
                                    </Button>
                                </div>
                            )}
                        </CardContent>
                    </Card>
                );
            })}
        </div>

        <Alert variant="warning" className="bg-amber-500/10 border-amber-500/20 text-amber-500">
            <AlertTriangle className="h-4 w-4" />
            <AlertTitle>Warning</AlertTitle>
            <AlertDescription>
                Switching profiles will overwrite your current unsaved settings. Please save any critical changes first.
            </AlertDescription>
        </Alert>
    </div>
  );
};
