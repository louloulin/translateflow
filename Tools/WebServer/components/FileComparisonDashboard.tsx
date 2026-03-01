import React, { useState, useEffect } from 'react';
import { useI18n } from '@/contexts/I18nContext';
import { ProjectService } from '@/services/ProjectService';
import { Project, ProjectFile } from '@/types';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Checkbox } from '@/components/ui/checkbox';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { ProgressBar } from '@/components/ProgressBar';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  ArrowLeft,
  FileText,
  GitCompare,
  Download,
  Eye,
  CheckCircle2,
  AlertCircle,
  Clock,
  Filter,
  ChevronLeft,
  ChevronRight,
  FileJson,
  FileCode,
  Settings,
  Loader2
} from 'lucide-react';
import { cn } from '@/lib/utils';

interface FileComparisonDashboardProps {
  projectId: string;
}

type ViewMode = 'grid' | 'list' | 'compare';
type FilterType = 'all' | 'completed' | 'in-progress' | 'error';

interface FileComparison {
  fileId: string;
  fileName: string;
  originalSize: number;
  translatedSize: number;
  bilingualSize: number;
  originalExists: boolean;
  translatedExists: boolean;
  bilingualExists: boolean;
  progress: number;
  status: 'pending' | 'translating' | 'completed' | 'error';
  diffCount?: number;
  lastModified: number;
}

export const FileComparisonDashboard: React.FC<FileComparisonDashboardProps> = ({ projectId }) => {
  const { t } = useI18n();

  // Data
  const [project, setProject] = useState<Project | null>(null);
  const [comparisons, setComparisons] = useState<FileComparison[]>([]);
  const [loading, setLoading] = useState(true);

  // UI State
  const [viewMode, setViewMode] = useState<ViewMode>('grid');
  const [filter, setFilter] = useState<FilterType>('all');
  const [selectedFiles, setSelectedFiles] = useState<Set<string>>(new Set());
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage] = useState(12);

  // Comparison view
  const [selectedComparison, setSelectedComparison] = useState<FileComparison | null>(null);

  useEffect(() => {
    loadProject();
  }, [projectId]);

  const loadProject = async () => {
    setLoading(true);
    const p = await ProjectService.getProject(projectId);
    setProject(p);

    // Generate comparison data
    const comparisonData: FileComparison[] = p.files.map(file => ({
      fileId: file.id,
      fileName: file.name,
      originalSize: file.size,
      translatedSize: file.size, // Simulated - would be calculated from actual files
      bilingualSize: file.size * 2, // Simulated - bilingual contains both
      originalExists: true,
      translatedExists: file.status === 'completed',
      bilingualExists: file.status === 'completed',
      progress: file.progress,
      status: file.status,
      lastModified: file.lastModified,
      diffCount: Math.floor(Math.random() * 50) // Simulated - would be calculated from actual diff
    }));

    setComparisons(comparisonData);
    setLoading(false);
  };

  const handleBack = () => {
    window.location.hash = '/';
  };

  const handleSelectAll = () => {
    if (selectedFiles.size === filteredComparisons.length) {
      setSelectedFiles(new Set());
    } else {
      setSelectedFiles(new Set(filteredComparisons.map(c => c.fileId)));
    }
  };

  const handleSelectFile = (fileId: string) => {
    const newSelected = new Set(selectedFiles);
    if (newSelected.has(fileId)) {
      newSelected.delete(fileId);
    } else {
      newSelected.add(fileId);
    }
    setSelectedFiles(newSelected);
  };

  const handleExportComparison = () => {
    // Export selected files comparison
    const selected = comparisons.filter(c => selectedFiles.has(c.fileId));
    const report = {
      project: project?.name,
      exportedAt: new Date().toISOString(),
      files: selected.map(c => ({
        file: c.fileName,
        original: c.originalExists,
        translated: c.translatedExists,
        bilingual: c.bilingualExists,
        progress: c.progress,
        diffCount: c.diffCount
      }))
    };

    const blob = new Blob([JSON.stringify(report, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${project?.name}-comparison-report.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const handleViewFile = (comparison: FileComparison) => {
    // Navigate to file viewer
    setSelectedComparison(comparison);
    setViewMode('compare');
  };

  // Filter comparisons
  const filteredComparisons = comparisons.filter(c => {
    switch (filter) {
      case 'completed':
        return c.status === 'completed';
      case 'in-progress':
        return c.status === 'translating';
      case 'error':
        return c.status === 'error';
      default:
        return true;
    }
  });

  // Pagination
  const totalPages = Math.ceil(filteredComparisons.length / itemsPerPage);
  const paginatedComparisons = filteredComparisons.slice(
    (currentPage - 1) * itemsPerPage,
    currentPage * itemsPerPage
  );

  // Stats
  const stats = {
    total: comparisons.length,
    completed: comparisons.filter(c => c.status === 'completed').length,
    inProgress: comparisons.filter(c => c.status === 'translating').length,
    error: comparisons.filter(c => c.status === 'error').length,
    avgProgress: Math.round(
      comparisons.reduce((sum, c) => sum + c.progress, 0) / comparisons.length || 0
    ),
    totalDiffs: comparisons.reduce((sum, c) => sum + (c.diffCount || 0), 0)
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed': return <CheckCircle2 className="h-4 w-4 text-emerald-500" />;
      case 'translating': return <Clock className="h-4 w-4 text-amber-500 animate-pulse" />;
      case 'error': return <AlertCircle className="h-4 w-4 text-destructive" />;
      default: return <Clock className="h-4 w-4 text-muted-foreground" />;
    }
  };

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  const formatDate = (timestamp: number) => {
    return new Date(timestamp).toLocaleDateString();
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="flex items-center gap-3">
          <Loader2 className="h-5 w-5 animate-spin" />
          <span>Loading comparison data...</span>
        </div>
      </div>
    );
  }

  if (!project) {
    return (
      <div className="flex flex-col items-center justify-center h-full gap-4">
        <h2 className="text-xl font-semibold">Project not found</h2>
        <Button onClick={handleBack}>Return to Dashboard</Button>
      </div>
    );
  }

  return (
    <div className="space-y-6 p-6">
      {/* Header */}
      <div className="flex flex-col gap-4">
        <div className="flex items-center gap-2 text-sm text-muted-foreground">
          <Button variant="ghost" size="sm" className="h-6 px-2 -ml-2" onClick={handleBack}>
            <ArrowLeft className="h-4 w-4 mr-1" /> Back
          </Button>
          <span>/</span>
          <span>Projects</span>
          <span>/</span>
          <span>{project.name}</span>
          <span>/</span>
          <span className="text-foreground font-medium">File Comparison</span>
        </div>

        <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
          <div className="space-y-1">
            <h1 className="text-3xl font-bold tracking-tight flex items-center gap-3">
              <GitCompare className="h-8 w-8" />
              File Comparison Dashboard
            </h1>
            <p className="text-muted-foreground">
              Compare original, translated, and bilingual files side-by-side
            </p>
          </div>

          <div className="flex gap-2">
            {selectedFiles.size > 0 && (
              <Button variant="outline" size="sm" onClick={handleExportComparison}>
                <Download className="h-4 w-4 mr-2" />
                Export Report ({selectedFiles})
              </Button>
            )}
            <Button variant="outline" size="sm">
              <Settings className="h-4 w-4 mr-2" />
              Settings
            </Button>
          </div>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
        <Card>
          <CardHeader className="pb-2">
            <CardDescription>Total Files</CardDescription>
            <CardTitle className="text-2xl">{stats.total}</CardTitle>
          </CardHeader>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardDescription>Completed</CardDescription>
            <CardTitle className="text-2xl text-emerald-600">{stats.completed}</CardTitle>
          </CardHeader>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardDescription>In Progress</CardDescription>
            <CardTitle className="text-2xl text-amber-600">{stats.inProgress}</CardTitle>
          </CardHeader>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardDescription>Average Progress</CardDescription>
            <CardTitle className="text-2xl">{stats.avgProgress}%</CardTitle>
          </CardHeader>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardDescription>Total Diffs</CardDescription>
            <CardTitle className="text-2xl">{stats.totalDiffs}</CardTitle>
          </CardHeader>
        </Card>
      </div>

      {/* Controls */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div className="flex items-center gap-2">
          {/* Filter */}
          <Select value={filter} onValueChange={(v: FilterType) => setFilter(v)}>
            <SelectTrigger className="w-[150px]">
              <Filter className="h-4 w-4 mr-2" />
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Files</SelectItem>
              <SelectItem value="completed">Completed</SelectItem>
              <SelectItem value="in-progress">In Progress</SelectItem>
              <SelectItem value="error">Errors</SelectItem>
            </SelectContent>
          </Select>

          {/* View Mode */}
          <Tabs value={viewMode} onValueChange={(v: ViewMode) => setViewMode(v)}>
            <TabsList>
              <TabsTrigger value="grid">Grid</TabsTrigger>
              <TabsTrigger value="list">List</TabsTrigger>
              <TabsTrigger value="compare">Compare</TabsTrigger>
            </TabsList>
          </Tabs>
        </div>

        <div className="text-sm text-muted-foreground">
          Showing {paginatedComparisons.length} of {filteredComparisons.length} files
        </div>
      </div>

      {/* Content */}
      {viewMode === 'grid' && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {paginatedComparisons.map((comparison) => (
            <Card
              key={comparison.fileId}
              className="hover:shadow-md transition-shadow cursor-pointer"
              onClick={() => handleViewFile(comparison)}
            >
              <CardHeader>
                <div className="flex items-start justify-between">
                  <div className="flex items-start gap-2 flex-1 min-w-0">
                    <Checkbox
                      checked={selectedFiles.has(comparison.fileId)}
                      onCheckedChange={() => handleSelectFile(comparison.fileId)}
                      onClick={(e) => e.stopPropagation()}
                    />
                    <div className="flex-1 min-w-0">
                      <CardTitle className="text-base truncate">{comparison.fileName}</CardTitle>
                      <CardDescription className="flex items-center gap-1 mt-1">
                        {getStatusIcon(comparison.status)}
                        {comparison.status}
                      </CardDescription>
                    </div>
                  </div>
                  {comparison.diffCount !== undefined && comparison.diffCount > 0 && (
                    <Badge variant="secondary">{comparison.diffCount} diffs</Badge>
                  )}
                </div>
              </CardHeader>

              <CardContent>
                <div className="space-y-3">
                  {/* Progress */}
                  <div>
                    <div className="flex justify-between text-sm mb-1">
                      <span>Progress</span>
                      <span>{comparison.progress}%</span>
                    </div>
                    <ProgressBar progress={comparison.progress} />
                  </div>

                  {/* File Status */}
                  <div className="grid grid-cols-3 gap-2 text-xs">
                    <div className={cn(
                      "flex items-center gap-1 p-2 rounded",
                      comparison.originalExists ? "bg-emerald-50 text-emerald-700" : "bg-muted text-muted-foreground"
                    )}>
                      <FileText className="h-3 w-3" />
                      Original
                    </div>
                    <div className={cn(
                      "flex items-center gap-1 p-2 rounded",
                      comparison.translatedExists ? "bg-blue-50 text-blue-700" : "bg-muted text-muted-foreground"
                    )}>
                      <FileCode className="h-3 w-3" />
                      Translated
                    </div>
                    <div className={cn(
                      "flex items-center gap-1 p-2 rounded",
                      comparison.bilingualExists ? "bg-purple-50 text-purple-700" : "bg-muted text-muted-foreground"
                    )}>
                      <FileJson className="h-3 w-3" />
                      Bilingual
                    </div>
                  </div>

                  {/* File Sizes */}
                  <div className="flex justify-between text-xs text-muted-foreground">
                    <span>{formatFileSize(comparison.originalSize)}</span>
                    <span>Modified: {formatDate(comparison.lastModified)}</span>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {viewMode === 'list' && (
        <Card>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead className="w-[50px]">
                  <Checkbox
                    checked={selectedFiles.size === filteredComparisons.length}
                    onCheckedChange={handleSelectAll}
                  />
                </TableHead>
                <TableHead>File Name</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Progress</TableHead>
                <TableHead>Original</TableHead>
                <TableHead>Translated</TableHead>
                <TableHead>Bilingual</TableHead>
                <TableHead>Diffs</TableHead>
                <TableHead>Last Modified</TableHead>
                <TableHead>Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {paginatedComparisons.map((comparison) => (
                <TableRow key={comparison.fileId}>
                  <TableCell>
                    <Checkbox
                      checked={selectedFiles.has(comparison.fileId)}
                      onCheckedChange={() => handleSelectFile(comparison.fileId)}
                    />
                  </TableCell>
                  <TableCell className="font-medium">{comparison.fileName}</TableCell>
                  <TableCell>
                    <div className="flex items-center gap-1">
                      {getStatusIcon(comparison.status)}
                      <span className="capitalize">{comparison.status}</span>
                    </div>
                  </TableCell>
                  <TableCell>
                    <div className="flex items-center gap-2">
                      <ProgressBar progress={comparison.progress} className="flex-1" />
                      <span className="text-xs">{comparison.progress}%</span>
                    </div>
                  </TableCell>
                  <TableCell>{comparison.originalExists ? formatFileSize(comparison.originalSize) : '-'}</TableCell>
                  <TableCell>{comparison.translatedExists ? formatFileSize(comparison.translatedSize) : '-'}</TableCell>
                  <TableCell>{comparison.bilingualExists ? formatFileSize(comparison.bilingualSize) : '-'}</TableCell>
                  <TableCell>
                    {comparison.diffCount !== undefined && comparison.diffCount > 0 ? (
                      <Badge variant="secondary">{comparison.diffCount}</Badge>
                    ) : (
                      <span className="text-muted-foreground">-</span>
                    )}
                  </TableCell>
                  <TableCell>{formatDate(comparison.lastModified)}</TableCell>
                  <TableCell>
                    <Button variant="ghost" size="sm" onClick={() => handleViewFile(comparison)}>
                      <Eye className="h-4 w-4" />
                    </Button>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </Card>
      )}

      {viewMode === 'compare' && selectedComparison && (
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle>{selectedComparison.fileName}</CardTitle>
                <CardDescription>
                  Side-by-side comparison of original, translated, and bilingual versions
                </CardDescription>
              </div>
              <Button variant="outline" size="sm" onClick={() => setViewMode('grid')}>
                <ArrowLeft className="h-4 w-4 mr-2" />
                Back to Grid
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {/* Original */}
              <div className="border rounded-lg p-4">
                <div className="flex items-center justify-between mb-2">
                  <h3 className="font-semibold flex items-center gap-2">
                    <FileText className="h-4 w-4" />
                    Original
                  </h3>
                  <Badge variant={selectedComparison.originalExists ? "default" : "secondary"}>
                    {selectedComparison.originalExists ? 'Exists' : 'Missing'}
                  </Badge>
                </div>
                <div className="text-sm text-muted-foreground space-y-1">
                  <p>Size: {formatFileSize(selectedComparison.originalSize)}</p>
                  <p>Modified: {formatDate(selectedComparison.lastModified)}</p>
                </div>
              </div>

              {/* Translated */}
              <div className="border rounded-lg p-4">
                <div className="flex items-center justify-between mb-2">
                  <h3 className="font-semibold flex items-center gap-2">
                    <FileCode className="h-4 w-4" />
                    Translated
                  </h3>
                  <Badge variant={selectedComparison.translatedExists ? "default" : "secondary"}>
                    {selectedComparison.translatedExists ? 'Exists' : 'Missing'}
                  </Badge>
                </div>
                <div className="text-sm text-muted-foreground space-y-1">
                  <p>Size: {formatFileSize(selectedComparison.translatedSize)}</p>
                  <p>Progress: {selectedComparison.progress}%</p>
                </div>
              </div>

              {/* Bilingual */}
              <div className="border rounded-lg p-4">
                <div className="flex items-center justify-between mb-2">
                  <h3 className="font-semibold flex items-center gap-2">
                    <FileJson className="h-4 w-4" />
                    Bilingual
                  </h3>
                  <Badge variant={selectedComparison.bilingualExists ? "default" : "secondary"}>
                    {selectedComparison.bilingualExists ? 'Exists' : 'Missing'}
                  </Badge>
                </div>
                <div className="text-sm text-muted-foreground space-y-1">
                  <p>Size: {formatFileSize(selectedComparison.bilingualSize)}</p>
                  <p>{selectedComparison.diffCount || 0} differences</p>
                </div>
              </div>
            </div>

            {/* Action Buttons */}
            <div className="flex gap-2 mt-4">
              <Button variant="outline" size="sm">
                <Download className="h-4 w-4 mr-2" />
                Download Original
              </Button>
              <Button variant="outline" size="sm">
                <Download className="h-4 w-4 mr-2" />
                Download Translated
              </Button>
              <Button variant="outline" size="sm">
                <Download className="h-4 w-4 mr-2" />
                Download Bilingual
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between">
          <div className="text-sm text-muted-foreground">
            Page {currentPage} of {totalPages}
          </div>
          <div className="flex gap-2">
            <Button variant="outline" size="sm" onClick={() => setCurrentPage(p => Math.max(1, p - 1))} disabled={currentPage === 1}>
              <ChevronLeft className="h-4 w-4" />
            </Button>
            <Button variant="outline" size="sm" onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))} disabled={currentPage === totalPages}>
              <ChevronRight className="h-4 w-4" />
            </Button>
          </div>
        </div>
      )}
    </div>
  );
};
