import React, { useEffect, useState, useRef } from 'react';
import { useI18n } from '@/contexts/I18nContext';
import { DataService } from '@/services/DataService';
import { ProjectService } from '@/services/ProjectService';
import { Segment, Project, ProjectFile } from '@/types';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { ArrowLeft, Save, Search, Sparkles, Check, Lock, RotateCcw, Copy, ChevronLeft, ChevronRight, Loader2 } from 'lucide-react';
import { cn } from '@/lib/utils';
import { useToast } from '@/hooks/use-toast';

interface EditorProps {
  projectId: string;
  fileId: string;
}

export const Editor: React.FC<EditorProps> = ({ projectId, fileId }) => {
  const { t } = useI18n();
  const { toast } = useToast();
  
  const [segments, setSegments] = useState<Segment[]>([]);
  const [project, setProject] = useState<Project | null>(null);
  const [currentFile, setCurrentFile] = useState<ProjectFile | null>(null);
  
  const [loading, setLoading] = useState(true);
  const [isTranslating, setIsTranslating] = useState(false);
  const [activeSegmentId, setActiveSegmentId] = useState<string | null>(null);
  
  // Search & Filter
  const [searchQuery, setSearchQuery] = useState('');
  const [filterStatus, setFilterStatus] = useState<string>('all');
  
  // Pagination
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [pageSize] = useState(20);
  const [totalItems, setTotalItems] = useState(0);

  const activeRowRef = useRef<HTMLDivElement>(null);

  // Initial Load
  useEffect(() => {
    loadProjectAndCache();
  }, [projectId, fileId]);

  // Reload on page/search change
  useEffect(() => {
    if (project && currentFile) {
        // Debounce search
        const timer = setTimeout(() => {
            loadSegments();
        }, 300);
        return () => clearTimeout(timer);
    }
  }, [page, searchQuery]);

  // Scroll to active
  useEffect(() => {
    if (activeSegmentId && activeRowRef.current) {
      activeRowRef.current.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
  }, [activeSegmentId]);

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
        e.preventDefault();
        if (activeSegmentId) {
          handleStatusToggle(activeSegmentId);
          // Move to next segment
          const currentIndex = segments.findIndex(s => s.id === activeSegmentId);
          if (currentIndex < segments.length - 1) {
            setActiveSegmentId(segments[currentIndex + 1].id);
          }
        }
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [activeSegmentId, segments]);

  const loadProjectAndCache = async () => {
    setLoading(true);
    try {
        const proj = await ProjectService.getProject(projectId);
        if (!proj) throw new Error("Project not found");
        setProject(proj);
        
        const file = proj.files.find(f => f.id === fileId);
        if (file) setCurrentFile(file);

        // Load Cache in Backend
        if (proj.rootPath) {
            await DataService.loadCache(proj.rootPath);
        }
        
        // Load initial segments (using the just loaded project/file info)
        await loadSegments(proj, file);
        
    } catch (error) {
        console.error("Failed to load project", error);
        toast({
            title: "Error",
            description: "Failed to load project data",
            variant: "destructive",
        });
    } finally {
        setLoading(false);
    }
  };

  const loadSegments = async (proj = project, file = currentFile) => {
      if (!proj) return;

      try {
          const res = await DataService.getCacheItems(page, pageSize, searchQuery, file?.path);
          
          const mappedSegments: Segment[] = res.items.map((item: any) => {
              let status: Segment['status'] = 'draft';
              if (item.translation_status === 1) status = 'translated';
              if (item.translation_status >= 2) status = 'approved'; // Simplified mapping

              return {
                  id: item.id.toString(),
                  index: item.text_index,
                  source: item.source,
                  target: item.translation || '',
                  status: status,
                  locked: false
              };
          });
          
          setSegments(mappedSegments);
          setTotalPages(res.pagination.total_pages);
          setTotalItems(res.pagination.total_items);
      } catch (e) {
          console.error("Failed to fetch segments", e);
          toast({
            title: "Error",
            description: "Failed to fetch segments",
            variant: "destructive",
          });
      }
  };

  const handleBack = () => {
    window.location.hash = `/projects/${projectId}`;
  };

  const handleSegmentUpdate = async (id: string, newTarget: string) => {
    // Optimistic update
    setSegments(prev => prev.map(s => 
      s.id === id ? { ...s, target: newTarget } : s
    ));
    
    // Backend update
    if (project?.rootPath) {
        try {
            await DataService.updateCacheItem(parseInt(id), newTarget, project.rootPath);
        } catch (error) {
            console.error("Failed to save segment", error);
            toast({
                title: "Save Failed",
                description: "Could not save changes to backend",
                variant: "destructive",
            });
        }
    }
  };

  const handleStatusToggle = (id: string) => {
    // Currently backend doesn't support direct status toggle via API, 
    // but we can update UI state.
    setSegments(prev => prev.map(s => {
      if (s.id !== id) return s;
      const nextStatus = s.status === 'approved' ? 'draft' : 'approved';
      return { ...s, status: nextStatus };
    }));
  };

  const handleTranslateSegment = async (id: string, source: string) => {
    const segment = segments.find(s => s.id === id);
    if (!segment || segment.locked) return;

    if (!project?.rootPath || !currentFile) {
        toast({ title: "Error", description: "Project path missing", variant: "destructive" });
        return;
    }

    setIsTranslating(true);
    try {
      // Use checkSingleLine for AI translation/proofread
      const result = await DataService.checkSingleLine(
          project.rootPath, 
          currentFile.path, 
          segment.index, 
          segment.target // Pass current target as context if any
      );
      
      if (result.corrected_translation) {
          handleSegmentUpdate(id, result.corrected_translation);
          toast({
            title: "Translated",
            description: "AI translation applied",
          });
      } else {
          toast({
            title: "Info",
            description: result.message || "No changes suggested",
          });
      }

    } catch (error) {
      console.error(error);
      toast({
        title: "Error",
        description: "Translation failed",
        variant: "destructive",
      });
    } finally {
      setIsTranslating(false);
    }
  };

  const handleTranslateAll = async () => {
    // This should trigger a backend task
    toast({
        title: "Coming Soon",
        description: "Batch translation task trigger will be implemented soon.",
    });
  };

  const handleCopySource = (id: string, source: string) => {
    handleSegmentUpdate(id, source);
  };

  // Filter is done client side for current page, 
  // ideally backend should support status filter.
  const filteredSegments = segments.filter(s => {
      // Search is already handled by backend, but we might want to double check or highlight
      // Status filter:
      if (filterStatus === 'all') return true;
      return s.status === filterStatus;
  });

  const progress = totalItems > 0 ? (segments.filter(s => s.status === 'approved' || s.status === 'translated').length / segments.length) * 100 : 0; // Approximate for current page

  if (loading) return <div className="flex items-center justify-center h-full gap-2 text-muted-foreground"><Loader2 className="h-4 w-4 animate-spin" /> Loading Project Data...</div>;

  return (
    <div className="flex flex-col h-full bg-background">
      {/* Header Toolbar */}
      <header className="flex flex-col border-b bg-card shadow-sm z-10 shrink-0">
        <div className="flex items-center justify-between px-4 py-2">
          <div className="flex items-center gap-4">
            <Button variant="ghost" size="icon" onClick={handleBack}>
              <ArrowLeft className="h-5 w-5" />
            </Button>
            <div className="flex flex-col">
              <h1 className="text-sm font-semibold flex items-center gap-2">
                {currentFile?.name || 'Unknown File'}
                {/* @ts-ignore */}
                <Badge variant="outline" className="font-normal text-[10px] h-5">
                  {project?.sourceLang} → {project?.targetLang}
                </Badge>
              </h1>
              <span className="text-xs text-muted-foreground">
                {totalItems} segments total
              </span>
            </div>
          </div>

          <div className="flex items-center gap-2 flex-1 max-w-xl mx-4">
            <div className="relative flex-1">
              <Search className="absolute left-2 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input 
                placeholder="Search segments..." 
                className="pl-8 h-9"
                value={searchQuery}
                onChange={(e) => {
                    setSearchQuery(e.target.value);
                    setPage(1); // Reset to page 1 on search
                }}
              />
            </div>
            <Select value={filterStatus} onValueChange={setFilterStatus}>
              <SelectTrigger className="w-[140px] h-9">
                <SelectValue placeholder="Filter" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Segments</SelectItem>
                <SelectItem value="draft">Draft</SelectItem>
                <SelectItem value="translated">Translated</SelectItem>
                <SelectItem value="approved">Approved</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div className="flex items-center gap-2">
            <Button 
              size="sm" 
              variant="secondary" 
              onClick={handleTranslateAll}
              disabled={isTranslating}
            >
              <Sparkles className={cn("h-4 w-4 mr-2 text-pink-500", isTranslating && "animate-pulse")} />
              {isTranslating ? 'Translating...' : 'AI Translate Page'}
            </Button>
            <Button size="sm">
              <Save className="h-4 w-4 mr-2" />
              Save
            </Button>
          </div>
        </div>
        <Progress value={progress} className="h-1 w-full rounded-none" />
      </header>

      {/* Editor Grid */}
      <div className="flex-1 overflow-y-auto">
        <div className="min-w-full divide-y divide-border pb-20">
          {filteredSegments.map((segment) => (
            <div 
              key={segment.id}
              ref={activeSegmentId === segment.id ? activeRowRef : null}
              className={cn(
                "grid grid-cols-[50px_1fr_1fr_50px] group transition-colors",
                activeSegmentId === segment.id ? "bg-accent/50" : "hover:bg-accent/20"
              )}
              onClick={() => setActiveSegmentId(segment.id)}
            >
              {/* Index Column */}
              <div className="p-3 text-xs text-muted-foreground border-r flex flex-col items-center justify-center select-none bg-muted/10 gap-1">
                <span>{segment.index}</span>
                {segment.status === 'approved' && (
                  <div className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
                )}
                {segment.status === 'translated' && (
                  <div className="w-1.5 h-1.5 rounded-full bg-blue-500" />
                )}
              </div>

              {/* Source Column */}
              <div className="p-4 text-sm border-r leading-relaxed whitespace-pre-wrap relative group/source">
                {segment.source}
                <Button
                  variant="ghost"
                  size="icon"
                  className="absolute top-2 right-2 h-6 w-6 opacity-0 group-hover/source:opacity-100 transition-opacity"
                  onClick={(e) => {
                    e.stopPropagation();
                    handleCopySource(segment.id, segment.source);
                  }}
                  title="Copy Source to Target"
                >
                  <Copy className="h-3 w-3" />
                </Button>
              </div>

              {/* Target Column */}
              <div className="relative p-0 border-r group/target">
                <textarea
                  className={cn(
                    "w-full h-full min-h-[80px] p-4 text-sm bg-transparent resize-none focus:outline-none focus:bg-background/80 transition-colors leading-relaxed",
                    segment.status === 'approved' && "text-emerald-600 dark:text-emerald-400 font-medium"
                  )}
                  value={segment.target}
                  onChange={(e) => handleSegmentUpdate(segment.id, e.target.value)}
                  placeholder="Type translation here..."
                  disabled={segment.locked}
                />
                <div className="absolute bottom-2 right-2 flex gap-1 opacity-0 group-hover/target:opacity-100 transition-opacity">
                  <Button 
                    size="icon" 
                    variant="ghost" 
                    className="h-7 w-7 rounded-full bg-background border shadow-sm hover:bg-pink-50 dark:hover:bg-pink-900/20"
                    title="AI Suggestion"
                    onClick={(e) => {
                      e.stopPropagation();
                      handleTranslateSegment(segment.id, segment.source);
                    }}
                    disabled={isTranslating || segment.locked}
                  >
                    <Loader2 className={cn("h-3.5 w-3.5 text-pink-500", isTranslating ? "animate-spin" : "hidden")} />
                    <Sparkles className={cn("h-3.5 w-3.5 text-pink-500", isTranslating ? "hidden" : "block")} />
                  </Button>
                  <Button 
                    size="icon" 
                    variant="ghost" 
                    className="h-7 w-7 rounded-full bg-background border shadow-sm"
                    title="Clear Translation"
                    onClick={(e) => {
                      e.stopPropagation();
                      handleSegmentUpdate(segment.id, '');
                    }}
                    disabled={segment.locked}
                  >
                    <RotateCcw className="h-3.5 w-3.5 text-muted-foreground" />
                  </Button>
                </div>
              </div>

              {/* Status Column */}
              <div className="p-2 flex flex-col items-center gap-2 justify-center bg-muted/5 border-l">
                <Button
                  variant="ghost"
                  size="icon"
                  className={cn(
                    "h-8 w-8 rounded-full transition-all",
                    segment.status === 'approved' 
                      ? "bg-emerald-100 text-emerald-600 dark:bg-emerald-900/30 dark:text-emerald-400 shadow-sm" 
                      : "text-muted-foreground hover:bg-emerald-100/50 hover:text-emerald-600 dark:hover:bg-emerald-900/20 dark:hover:text-emerald-400"
                  )}
                  onClick={(e) => {
                    e.stopPropagation();
                    handleStatusToggle(segment.id);
                  }}
                  title={segment.status === 'approved' ? "Mark as Draft" : "Approve Translation (Ctrl+Enter)"}
                  disabled={segment.locked}
                >
                  <Check className="h-4 w-4" />
                </Button>
                {segment.locked && (
                  <Lock className="h-3 w-3 text-muted-foreground/50" />
                )}
              </div>
            </div>
          ))}
          
          {filteredSegments.length === 0 && (
            <div className="flex flex-col items-center justify-center p-12 text-muted-foreground gap-2">
              <Search className="h-8 w-8 opacity-20" />
              <p>No segments found.</p>
            </div>
          )}
        </div>
      </div>

      {/* Footer / Pagination */}
      <div className="border-t p-2 bg-card flex items-center justify-between shrink-0 text-sm text-muted-foreground">
          <div className="flex items-center gap-2">
              <span>Page {page} of {totalPages}</span>
              <span className="mx-2">|</span>
              <span>Total: {totalItems}</span>
          </div>
          <div className="flex items-center gap-2">
              <Button 
                  variant="outline" 
                  size="sm" 
                  onClick={() => setPage(p => Math.max(1, p - 1))}
                  disabled={page <= 1}
              >
                  <ChevronLeft className="h-4 w-4" />
                  Previous
              </Button>
              <Button 
                  variant="outline" 
                  size="sm" 
                  onClick={() => setPage(p => Math.min(totalPages, p + 1))}
                  disabled={page >= totalPages}
              >
                  Next
                  <ChevronRight className="h-4 w-4" />
              </Button>
          </div>
      </div>
    </div>
  );
};
