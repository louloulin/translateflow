import React, { useState, useEffect, useMemo } from 'react';
import { useI18n } from '@/contexts/I18nContext';
import { FileVersion, VersionDiff, DiffLine } from '@/types';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  ArrowLeft,
  GitCompare,
  Clock,
  FileText,
  ChevronLeft,
  ChevronRight,
  Plus,
  Minus,
  RefreshCw,
  Download,
  Eye,
  Trash2,
  Save,
  ArrowRightLeft,
  ScrollText
} from 'lucide-react';
import { cn } from '@/lib/utils';

interface VersionHistoryViewerProps {
  projectId: string;
  fileId: string;
  fileName: string;
  onBack?: () => void;
}

// Simple diff algorithm
function computeDiff(oldText: string, newText: string): DiffLine[] {
  const oldLines = oldText.split('\n');
  const newLines = newText.split('\n');
  const diff: DiffLine[] = [];

  // Simple line-by-line diff using LCS approach
  const lcs = longestCommonSubsequence(oldLines, newLines);

  let oldIdx = 0;
  let newIdx = 0;
  let lcsIdx = 0;

  while (oldIdx < oldLines.length || newIdx < newLines.length) {
    if (lcsIdx < lcs.length && oldIdx < oldLines.length && oldLines[oldIdx] === lcs[lcsIdx] && newIdx < newLines.length && newLines[newIdx] === lcs[lcsIdx]) {
      diff.push({
        type: 'unchanged',
        lineNumber: newIdx + 1,
        oldLineNumber: oldIdx + 1,
        newLineNumber: newIdx + 1,
        content: oldLines[oldIdx]
      });
      oldIdx++;
      newIdx++;
      lcsIdx++;
    } else if (oldIdx < oldLines.length && (lcsIdx >= lcs.length || oldLines[oldIdx] !== lcs[lcsIdx])) {
      diff.push({
        type: 'removed',
        lineNumber: oldIdx + 1,
        oldLineNumber: oldIdx + 1,
        content: oldLines[oldIdx]
      });
      oldIdx++;
    } else if (newIdx < newLines.length && (lcsIdx >= lcs.length || newLines[newIdx] !== lcs[lcsIdx])) {
      diff.push({
        type: 'added',
        lineNumber: newIdx + 1,
        newLineNumber: newIdx + 1,
        content: newLines[newIdx]
      });
      newIdx++;
    }
  }

  return diff;
}

function longestCommonSubsequence(arr1: string[], arr2: string[]): string[] {
  const m = arr1.length;
  const n = arr2.length;
  const dp: number[][] = Array(m + 1).fill(null).map(() => Array(n + 1).fill(0));

  for (let i = 1; i <= m; i++) {
    for (let j = 1; j <= n; j++) {
      if (arr1[i - 1] === arr2[j - 1]) {
        dp[i][j] = dp[i - 1][j - 1] + 1;
      } else {
        dp[i][j] = Math.max(dp[i - 1][j], dp[i][j - 1]);
      }
    }
  }

  const lcs: string[] = [];
  let i = m, j = n;
  while (i > 0 && j > 0) {
    if (arr1[i - 1] === arr2[j - 1]) {
      lcs.unshift(arr1[i - 1]);
      i--;
      j--;
    } else if (dp[i - 1][j] > dp[i][j - 1]) {
      i--;
    } else {
      j--;
    }
  }

  return lcs;
}

export function VersionHistoryViewer({ projectId, fileId, fileName, onBack }: VersionHistoryViewerProps) {
  const { t } = useI18n();
  const [versions, setVersions] = useState<FileVersion[]>([]);
  const [selectedOldVersion, setSelectedOldVersion] = useState<FileVersion | null>(null);
  const [selectedNewVersion, setSelectedNewVersion] = useState<FileVersion | null>(null);
  const [oldContent, setOldContent] = useState<string>('');
  const [newContent, setNewContent] = useState<string>('');
  const [diff, setDiff] = useState<DiffLine[]>([]);
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState<'list' | 'compare'>('list');
  const [viewMode, setViewMode] = useState<'split' | 'unified'>('unified');

  // Stats
  const stats = useMemo(() => {
    return {
      added: diff.filter(d => d.type === 'added').length,
      removed: diff.filter(d => d.type === 'removed').length,
      unchanged: diff.filter(d => d.type === 'unchanged').length
    };
  }, [diff]);

  // Load versions
  useEffect(() => {
    loadVersions();
  }, [projectId, fileId]);

  // Compute diff when both versions selected
  useEffect(() => {
    if (oldContent && newContent) {
      const computedDiff = computeDiff(oldContent, newContent);
      setDiff(computedDiff);
    }
  }, [oldContent, newContent]);

  const loadVersions = async () => {
    setLoading(true);
    try {
      const response = await fetch(`/api/v1/files/${fileId}/versions`);
      if (response.ok) {
        const data = await response.json();
        setVersions(data.versions || []);
        // Auto-select last two versions if available
        if (data.versions && data.versions.length >= 2) {
          const latest = data.versions[data.versions.length - 1];
          const previous = data.versions[data.versions.length - 2];
          setSelectedNewVersion(latest);
          setSelectedOldVersion(previous);
          // Load content for both
          loadVersionContent(latest, previous);
        }
      }
    } catch (error) {
      console.error('Failed to load versions:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadVersionContent = async (newVer: FileVersion, oldVer: FileVersion) => {
    try {
      const [oldRes, newRes] = await Promise.all([
        fetch(`/api/v1/files/${fileId}/versions/${oldVer.id}/content`),
        fetch(`/api/v1/files/${fileId}/versions/${newVer.id}/content`)
      ]);

      if (oldRes.ok) {
        const oldData = await oldRes.json();
        setOldContent(oldData.content || '');
      }
      if (newRes.ok) {
        const newData = await newRes.json();
        setNewContent(newData.content || '');
      }
    } catch (error) {
      console.error('Failed to load version content:', error);
    }
  };

  const handleVersionSelect = async (version: FileVersion, type: 'old' | 'new') => {
    try {
      const response = await fetch(`/api/v1/files/${fileId}/versions/${version.id}/content`);
      if (response.ok) {
        const data = await response.json();
        if (type === 'old') {
          setOldContent(data.content || '');
          setSelectedOldVersion(version);
        } else {
          setNewContent(data.content || '');
          setSelectedNewVersion(version);
        }
      }
    } catch (error) {
      console.error('Failed to load version content:', error);
    }
  };

  const saveCurrentVersion = async () => {
    try {
      const response = await fetch(`/api/v1/files/${fileId}/versions`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          description: 'Manual snapshot'
        })
      });
      if (response.ok) {
        loadVersions();
      }
    } catch (error) {
      console.error('Failed to save version:', error);
    }
  };

  const formatDate = (timestamp: number) => {
    return new Date(timestamp).toLocaleString();
  };

  const formatSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  const getStatusBadge = (status: string) => {
    const colors: Record<string, string> = {
      draft: 'bg-yellow-500',
      translated: 'bg-blue-500',
      completed: 'bg-green-500'
    };
    return <Badge className={colors[status] || 'bg-gray-500'}>{status}</Badge>;
  };

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b bg-card">
        <div className="flex items-center gap-4">
          {onBack && (
            <Button variant="ghost" size="icon" onClick={onBack}>
              <ArrowLeft className="h-5 w-5" />
            </Button>
          )}
          <div>
            <h2 className="text-xl font-semibold">{t('versionHistory', 'Version History')}</h2>
            <p className="text-sm text-muted-foreground">{fileName}</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" onClick={saveCurrentVersion}>
            <Save className="h-4 w-4 mr-2" />
            {t('saveSnapshot', 'Save Snapshot')}
          </Button>
          <Button variant="outline" size="sm" onClick={loadVersions}>
            <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
            {t('refresh', 'Refresh')}
          </Button>
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b">
        <Tabs value={activeTab} onValueChange={(v) => setActiveTab(v as 'list' | 'compare')}>
          <TabsList>
            <TabsTrigger value="list">
              <ScrollText className="h-4 w-4 mr-2" />
              {t('versionList', 'Version List')}
            </TabsTrigger>
            <TabsTrigger value="compare">
              <GitCompare className="h-4 w-4 mr-2" />
              {t('compare', 'Compare')}
            </TabsTrigger>
          </TabsList>
        </Tabs>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-auto p-4">
        {activeTab === 'list' ? (
          // Version List
          <div className="space-y-4">
            {versions.length === 0 ? (
              <Card>
                <CardContent className="flex flex-col items-center justify-center py-12">
                  <Clock className="h-12 w-12 text-muted-foreground mb-4" />
                  <p className="text-muted-foreground">{t('noVersions', 'No versions saved yet')}</p>
                  <Button className="mt-4" onClick={saveCurrentVersion}>
                    <Save className="h-4 w-4 mr-2" />
                    {t('createFirstVersion', 'Create First Version')}
                  </Button>
                </CardContent>
              </Card>
            ) : (
              <div className="grid gap-4">
                {versions.slice().reverse().map((version, index) => (
                  <Card
                    key={version.id}
                    className={cn(
                      'cursor-pointer transition-colors',
                      (selectedOldVersion?.id === version.id || selectedNewVersion?.id === version.id) &&
                        'ring-2 ring-primary'
                    )}
                    onClick={() => {
                      if (!selectedOldVersion || selectedOldVersion.id === version.id) {
                        handleVersionSelect(version, 'old');
                      } else if (!selectedNewVersion || selectedNewVersion.id === version.id) {
                        handleVersionSelect(version, 'new');
                      } else {
                        handleVersionSelect(version, 'old');
                      }
                    }}
                  >
                    <CardHeader className="pb-2">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <FileText className="h-5 w-5" />
                          <CardTitle className="text-base">
                            {t('version', 'Version')} {version.version}
                          </CardTitle>
                          {index === 0 && (
                            <Badge variant="default">{t('latest', 'Latest')}</Badge>
                          )}
                        </div>
                        {getStatusBadge(version.status)}
                      </div>
                    </CardHeader>
                    <CardContent>
                      <div className="flex items-center gap-4 text-sm text-muted-foreground">
                        <span className="flex items-center gap-1">
                          <Clock className="h-4 w-4" />
                          {formatDate(version.timestamp)}
                        </span>
                        <span>{formatSize(version.size)}</span>
                        <span>{version.segmentCount} {t('segments', 'segments')}</span>
                      </div>
                      {version.description && (
                        <p className="mt-2 text-sm">{version.description}</p>
                      )}
                    </CardContent>
                  </Card>
                ))}
              </div>
            )}
          </div>
        ) : (
          // Compare View
          <div className="h-full flex flex-col">
            {/* Version Selectors */}
            <div className="flex items-center gap-4 mb-4">
              <div className="flex-1">
                <label className="text-sm font-medium mb-2 block">{t('oldVersion', 'Old Version')}</label>
                <select
                  className="w-full p-2 border rounded-md bg-background"
                  value={selectedOldVersion?.id || ''}
                  onChange={(e) => {
                    const version = versions.find(v => v.id === e.target.value);
                    if (version) handleVersionSelect(version, 'old');
                  }}
                >
                  <option value="">{t('selectVersion', 'Select version...')}</option>
                  {versions.map(v => (
                    <option key={v.id} value={v.id}>
                      {t('version', 'Version')} {v.version} - {formatDate(v.timestamp)}
                    </option>
                  ))}
                </select>
              </div>
              <ArrowRightLeft className="h-5 w-5 mt-6" />
              <div className="flex-1">
                <label className="text-sm font-medium mb-2 block">{t('newVersion', 'New Version')}</label>
                <select
                  className="w-full p-2 border rounded-md bg-background"
                  value={selectedNewVersion?.id || ''}
                  onChange={(e) => {
                    const version = versions.find(v => v.id === e.target.value);
                    if (version) handleVersionSelect(version, 'new');
                  }}
                >
                  <option value="">{t('selectVersion', 'Select version...')}</option>
                  {versions.map(v => (
                    <option key={v.id} value={v.id}>
                      {t('version', 'Version')} {v.version} - {formatDate(v.timestamp)}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            {/* Stats */}
            {diff.length > 0 && (
              <div className="flex items-center gap-4 mb-4">
                <div className="flex items-center gap-2">
                  <Plus className="h-4 w-4 text-green-500" />
                  <span className="text-sm">{stats.added} {t('added', 'added')}</span>
                </div>
                <div className="flex items-center gap-2">
                  <Minus className="h-4 w-4 text-red-500" />
                  <span className="text-sm">{stats.removed} {t('removed', 'removed')}</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-sm text-muted-foreground">{stats.unchanged} {t('unchanged', 'unchanged')}</span>
                </div>
                <div className="ml-auto">
                  <Tabs value={viewMode} onValueChange={(v) => setViewMode(v as 'split' | 'unified')}>
                    <TabsList>
                      <TabsTrigger value="unified">{t('unified', 'Unified')}</TabsTrigger>
                      <TabsTrigger value="split">{t('split', 'Split')}</TabsTrigger>
                    </TabsList>
                  </Tabs>
                </div>
              </div>
            )}

            {/* Diff View */}
            {diff.length > 0 ? (
              viewMode === 'unified' ? (
                <Card className="flex-1 overflow-auto">
                  <CardContent className="p-0">
                    <div className="font-mono text-sm">
                      {diff.map((line, index) => (
                        <div
                          key={index}
                          className={cn(
                            'flex px-4 py-0.5',
                            line.type === 'added' && 'bg-green-500/10',
                            line.type === 'removed' && 'bg-red-500/10'
                          )}
                        >
                          <span className="w-12 text-muted-foreground select-none">
                            {line.type === 'added' ? '+' : line.type === 'removed' ? '-' : ' '}
                          </span>
                          <span className="w-16 text-muted-foreground text-xs">
                            {line.lineNumber}
                          </span>
                          <span className={cn(
                            'flex-1',
                            line.type === 'added' && 'text-green-600',
                            line.type === 'removed' && 'text-red-600'
                          )}>
                            {line.content}
                          </span>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              ) : (
                <div className="flex-1 flex gap-4 overflow-hidden">
                  <Card className="flex-1 overflow-auto">
                    <CardHeader className="py-2">
                      <CardTitle className="text-sm">{t('oldVersion', 'Old Version')}: {selectedOldVersion ? t('version', 'Version') + ' ' + selectedOldVersion.version : '-'}</CardTitle>
                    </CardHeader>
                    <CardContent className="p-0">
                      <div className="font-mono text-sm">
                        {diff.filter(d => d.type !== 'added').map((line, index) => (
                          <div
                            key={index}
                            className={cn(
                              'flex px-4 py-0.5',
                              line.type === 'removed' && 'bg-red-500/10'
                            )}
                          >
                            <span className="w-16 text-muted-foreground text-xs">
                              {line.oldLineNumber}
                            </span>
                            <span className={cn(
                              'flex-1',
                              line.type === 'removed' && 'text-red-600'
                            )}>
                              {line.content}
                            </span>
                          </div>
                        ))}
                      </div>
                    </CardContent>
                  </Card>
                  <Card className="flex-1 overflow-auto">
                    <CardHeader className="py-2">
                      <CardTitle className="text-sm">{t('newVersion', 'New Version')}: {selectedNewVersion ? t('version', 'Version') + ' ' + selectedNewVersion.version : '-'}</CardTitle>
                    </CardHeader>
                    <CardContent className="p-0">
                      <div className="font-mono text-sm">
                        {diff.filter(d => d.type !== 'removed').map((line, index) => (
                          <div
                            key={index}
                            className={cn(
                              'flex px-4 py-0.5',
                              line.type === 'added' && 'bg-green-500/10'
                            )}
                          >
                            <span className="w-16 text-muted-foreground text-xs">
                              {line.newLineNumber}
                            </span>
                            <span className={cn(
                              'flex-1',
                              line.type === 'added' && 'text-green-600'
                            )}>
                              {line.content}
                            </span>
                          </div>
                        ))}
                      </div>
                    </CardContent>
                  </Card>
                </div>
              )
            ) : (
              <Card>
                <CardContent className="flex flex-col items-center justify-center py-12">
                  <GitCompare className="h-12 w-12 text-muted-foreground mb-4" />
                  <p className="text-muted-foreground">{t('selectVersionsToCompare', 'Select two versions to compare')}</p>
                </CardContent>
              </Card>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
