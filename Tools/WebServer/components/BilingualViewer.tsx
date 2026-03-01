import React, { useState, useEffect, useRef } from 'react';
import { useI18n } from '@/contexts/I18nContext';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import {
  BookOpen,
  Download,
  Search,
  ChevronLeft,
  ChevronRight,
  Maximize2,
  Minimize2,
  AlignLeft,
  AlignCenter,
  AlignRight
} from 'lucide-react';
import { cn } from '@/lib/utils';

interface BilingualSegment {
  id: string;
  index: number;
  source: string;
  translation: string;
  status?: 'draft' | 'translated' | 'approved';
}

interface BilingualViewerProps {
  segments: BilingualSegment[];
  fileName?: string;
  className?: string;
}

type ViewMode = 'side-by-side' | 'top-bottom' | 'source-only' | 'translation-only';
type Alignment = 'left' | 'center' | 'right';

export const BilingualViewer: React.FC<BilingualViewerProps> = ({
  segments,
  fileName = 'bilingual.txt',
  className
}) => {
  const { t } = useI18n();

  // View settings
  const [viewMode, setViewMode] = useState<ViewMode>('side-by-side');
  const [alignment, setAlignment] = useState<Alignment>('left');
  const [fontSize, setFontSize] = useState(14);

  // Search
  const [searchQuery, setSearchQuery] = useState('');
  const [currentMatch, setCurrentMatch] = useState(0);
  const [totalMatches, setTotalMatches] = useState(0);

  // Pagination
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage] = useState(50);
  const [isFullscreen, setIsFullscreen] = useState(false);

  // Refs
  const containerRef = useRef<HTMLDivElement>(null);
  const sourcePanelRef = useRef<HTMLDivElement>(null);
  const translationPanelRef = useRef<HTMLDivElement>(null);

  // Calculate matches
  useEffect(() => {
    if (!searchQuery) {
      setTotalMatches(0);
      setCurrentMatch(0);
      return;
    }

    let matchCount = 0;
    segments.forEach(seg => {
      if (seg.source.toLowerCase().includes(searchQuery.toLowerCase()) ||
          seg.translation.toLowerCase().includes(searchQuery.toLowerCase())) {
        matchCount++;
      }
    });
    setTotalMatches(matchCount);
    setCurrentMatch(0);
  }, [searchQuery, segments]);

  // Sync scroll
  const handleSourceScroll = (e: React.UIEvent<HTMLDivElement>) => {
    if (translationPanelRef.current && viewMode === 'side-by-side') {
      const target = e.target as HTMLDivElement;
      translationPanelRef.current.scrollTop = target.scrollTop;
    }
  };

  const handleTranslationScroll = (e: React.UIEvent<HTMLDivElement>) => {
    if (sourcePanelRef.current && viewMode === 'side-by-side') {
      const target = e.target as HTMLDivElement;
      sourcePanelRef.current.scrollTop = target.scrollTop;
    }
  };

  // Highlight search matches
  const highlightText = (text: string) => {
    if (!searchQuery) return text;

    const regex = new RegExp(`(${searchQuery})`, 'gi');
    const parts = text.split(regex);

    return parts.map((part, index) =>
      regex.test(part) ? (
        <mark key={index} className="bg-yellow-200 dark:bg-yellow-800 rounded px-0.5">
          {part}
        </mark>
      ) : (
        part
      )
    );
  };

  // Export functionality
  const handleExport = (format: 'txt' | 'json') => {
    if (format === 'txt') {
      const content = segments
        .map(seg => `${seg.source}\n${seg.translation}\n`)
        .join('\n');
      const blob = new Blob([content], { type: 'text/plain;charset=utf-8' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = fileName;
      a.click();
      URL.revokeObjectURL(url);
    } else if (format === 'json') {
      const content = JSON.stringify(segments, null, 2);
      const blob = new Blob([content], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = fileName.replace('.txt', '.json');
      a.click();
      URL.revokeObjectURL(url);
    }
  };

  // Pagination
  const totalPages = Math.ceil(segments.length / itemsPerPage);
  const paginatedSegments = segments.slice(
    (currentPage - 1) * itemsPerPage,
    currentPage * itemsPerPage
  );

  // Navigation
  const nextPage = () => {
    if (currentPage < totalPages) setCurrentPage(currentPage + 1);
  };

  const prevPage = () => {
    if (currentPage > 1) setCurrentPage(currentPage - 1);
  };

  const toggleFullscreen = () => {
    if (!isFullscreen && containerRef.current) {
      containerRef.current.requestFullscreen();
      setIsFullscreen(true);
    } else {
      document.exitFullscreen();
      setIsFullscreen(false);
    }
  };

  return (
    <div
      ref={containerRef}
      className={cn(
        'flex flex-col h-full bg-background',
        isFullscreen && 'fixed inset-0 z-50',
        className
      )}
    >
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b bg-card">
        <div className="flex items-center gap-2">
          <BookOpen className="w-5 h-5" />
          <h3 className="font-semibold">{fileName}</h3>
          <Badge variant="secondary">{segments.length} segments</Badge>
        </div>

        <div className="flex items-center gap-2">
          {/* View Mode */}
          <Select value={viewMode} onValueChange={(v: ViewMode) => setViewMode(v)}>
            <SelectTrigger className="w-[180px]">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="side-by-side">Side by Side</SelectItem>
              <SelectItem value="top-bottom">Top / Bottom</SelectItem>
              <SelectItem value="source-only">Source Only</SelectItem>
              <SelectItem value="translation-only">Translation Only</SelectItem>
            </SelectContent>
          </Select>

          {/* Text Alignment */}
          <div className="flex items-center border rounded-md">
            <Button
              variant={alignment === 'left' ? 'secondary' : 'ghost'}
              size="sm"
              onClick={() => setAlignment('left')}
            >
              <AlignLeft className="w-4 h-4" />
            </Button>
            <Button
              variant={alignment === 'center' ? 'secondary' : 'ghost'}
              size="sm"
              onClick={() => setAlignment('center')}
            >
              <AlignCenter className="w-4 h-4" />
            </Button>
            <Button
              variant={alignment === 'right' ? 'secondary' : 'ghost'}
              size="sm"
              onClick={() => setAlignment('right')}
            >
              <AlignRight className="w-4 h-4" />
            </Button>
          </div>

          {/* Font Size */}
          <Select
            value={fontSize.toString()}
            onValueChange={(v) => setFontSize(parseInt(v))}
          >
            <SelectTrigger className="w-[100px]">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="12">12px</SelectItem>
              <SelectItem value="14">14px</SelectItem>
              <SelectItem value="16">16px</SelectItem>
              <SelectItem value="18">18px</SelectItem>
              <SelectItem value="20">20px</SelectItem>
            </SelectContent>
          </Select>

          {/* Export */}
          <Button variant="outline" size="sm" onClick={() => handleExport('txt')}>
            <Download className="w-4 h-4 mr-1" />
            Export
          </Button>

          {/* Fullscreen */}
          <Button variant="outline" size="sm" onClick={toggleFullscreen}>
            {isFullscreen ? (
              <Minimize2 className="w-4 h-4" />
            ) : (
              <Maximize2 className="w-4 h-4" />
            )}
          </Button>
        </div>
      </div>

      {/* Search Bar */}
      <div className="flex items-center gap-2 p-3 border-b bg-card">
        <Search className="w-4 h-4 text-muted-foreground" />
        <input
          type="text"
          placeholder={t('search_placeholder') || 'Search in source or translation...'}
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="flex-1 bg-transparent border-0 outline-none"
        />
        {totalMatches > 0 && (
          <Badge variant="secondary">
            {currentMatch + 1} / {totalMatches}
          </Badge>
        )}
      </div>

      {/* Content */}
      <div className="flex-1 overflow-hidden">
        {viewMode === 'side-by-side' ? (
          <div className="flex h-full">
            {/* Source Panel */}
            <div className="flex-1 border-r">
              <div className="p-2 bg-muted/50 border-b font-semibold text-sm">
                {t('source_text') || 'Source'}
              </div>
              <div
                ref={sourcePanelRef}
                onScroll={handleSourceScroll}
                className="h-full overflow-auto p-4"
                style={{ fontSize: `${fontSize}px`, textAlign: alignment }}
              >
                {paginatedSegments.map((seg) => (
                  <div
                    key={seg.id}
                    className="mb-4 p-3 rounded hover:bg-muted/50 transition-colors"
                  >
                    <div className="flex items-start gap-2 mb-1">
                      <Badge variant="outline" className="text-xs">
                        {seg.index}
                      </Badge>
                    </div>
                    <div className="leading-relaxed">{highlightText(seg.source)}</div>
                  </div>
                ))}
              </div>
            </div>

            {/* Translation Panel */}
            <div className="flex-1">
              <div className="p-2 bg-muted/50 border-b font-semibold text-sm">
                {t('translation_text') || 'Translation'}
              </div>
              <div
                ref={translationPanelRef}
                onScroll={handleTranslationScroll}
                className="h-full overflow-auto p-4"
                style={{ fontSize: `${fontSize}px`, textAlign: alignment }}
              >
                {paginatedSegments.map((seg) => (
                  <div
                    key={seg.id}
                    className="mb-4 p-3 rounded hover:bg-muted/50 transition-colors"
                  >
                    <div className="flex items-start gap-2 mb-1">
                      <Badge variant="outline" className="text-xs">
                        {seg.index}
                      </Badge>
                      {seg.status && (
                        <Badge
                          variant={
                            seg.status === 'approved'
                              ? 'default'
                              : seg.status === 'translated'
                              ? 'secondary'
                              : 'outline'
                          }
                          className="text-xs"
                        >
                          {seg.status}
                        </Badge>
                      )}
                    </div>
                    <div className="leading-relaxed">{highlightText(seg.translation)}</div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        ) : viewMode === 'top-bottom' ? (
          <div className="h-full overflow-auto p-4">
            {paginatedSegments.map((seg) => (
              <div
                key={seg.id}
                className="mb-6 p-4 border rounded-lg hover:bg-muted/50 transition-colors"
              >
                <div className="flex items-center gap-2 mb-2">
                  <Badge variant="outline">{seg.index}</Badge>
                  {seg.status && (
                    <Badge
                      variant={
                        seg.status === 'approved'
                          ? 'default'
                          : seg.status === 'translated'
                          ? 'secondary'
                          : 'outline'
                      }
                    >
                      {seg.status}
                    </Badge>
                  )}
                </div>
                <div className="space-y-2" style={{ fontSize: `${fontSize}px`, textAlign: alignment }}>
                  <div className="p-2 bg-muted/30 rounded">
                    <span className="text-xs text-muted-foreground mr-2">Source:</span>
                    {highlightText(seg.source)}
                  </div>
                  <div className="p-2 bg-primary/10 rounded">
                    <span className="text-xs text-muted-foreground mr-2">Translation:</span>
                    {highlightText(seg.translation)}
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : viewMode === 'source-only' ? (
          <div className="h-full overflow-auto p-4" style={{ fontSize: `${fontSize}px`, textAlign: alignment }}>
            {paginatedSegments.map((seg) => (
              <div key={seg.id} className="mb-4 p-3 rounded hover:bg-muted/50">
                <Badge variant="outline" className="text-xs mb-2">{seg.index}</Badge>
                <div className="leading-relaxed">{highlightText(seg.source)}</div>
              </div>
            ))}
          </div>
        ) : (
          <div className="h-full overflow-auto p-4" style={{ fontSize: `${fontSize}px`, textAlign: alignment }}>
            {paginatedSegments.map((seg) => (
              <div key={seg.id} className="mb-4 p-3 rounded hover:bg-muted/50">
                <Badge variant="outline" className="text-xs mb-2">{seg.index}</Badge>
                <div className="leading-relaxed">{highlightText(seg.translation)}</div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Footer / Pagination */}
      <div className="flex items-center justify-between p-3 border-t bg-card">
        <div className="text-sm text-muted-foreground">
          {t('showing') || 'Showing'} {(currentPage - 1) * itemsPerPage + 1} - {Math.min(currentPage * itemsPerPage, segments.length)} {t('of') || 'of'} {segments.length}
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" onClick={prevPage} disabled={currentPage === 1}>
            <ChevronLeft className="w-4 h-4" />
          </Button>
          <span className="text-sm">
            {t('page') || 'Page'} {currentPage} / {totalPages}
          </span>
          <Button variant="outline" size="sm" onClick={nextPage} disabled={currentPage === totalPages}>
            <ChevronRight className="w-4 h-4" />
          </Button>
        </div>
      </div>
    </div>
  );
};
