import React, { useState, useEffect, useRef } from 'react';
import { useI18n } from '../contexts/I18nContext';

interface CacheItem {
  id: number;
  file_path: string;
  text_index: number;
  source: string;
  translation: string;
  original_translation: string;
  translation_status: number;
  modified: boolean;
}

interface CacheStatus {
  loaded: boolean;
  file_count: number;
  total_items: number;
  project_name: string | null;
}

interface Pagination {
  current_page: number;
  page_size: number;
  total_items: number;
  total_pages: number;
  has_next: boolean;
  has_prev: boolean;
}

// State persistence key
const CACHE_EDITOR_STATE_KEY = 'cache_editor_state';

// Helper functions for state persistence
const saveStateToStorage = (state: any) => {
  try {
    localStorage.setItem(CACHE_EDITOR_STATE_KEY, JSON.stringify(state));
  } catch (err) {
    console.warn('Failed to save cache editor state:', err);
  }
};

const loadStateFromStorage = () => {
  try {
    const saved = localStorage.getItem(CACHE_EDITOR_STATE_KEY);
    return saved ? JSON.parse(saved) : null;
  } catch (err) {
    console.warn('Failed to load cache editor state:', err);
    return null;
  }
};

export const CacheEditor: React.FC = () => {
  const { t } = useI18n();

  // Load saved state - will be refreshed when needed
  const [savedState, setSavedState] = useState(() => loadStateFromStorage());

  const [cacheStatus, setCacheStatus] = useState<CacheStatus>({
    loaded: false,
    file_count: 0,
    total_items: 0,
    project_name: null
  });
  const [cacheItems, setCacheItems] = useState<CacheItem[]>([]);
  const [pagination, setPagination] = useState<Pagination | null>(null);
  const [currentPage, setCurrentPage] = useState(() => savedState?.currentPage || 1);
  const [pageSize, setPageSize] = useState(() => savedState?.pageSize || 15);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [projectPath, setProjectPath] = useState(() => savedState?.projectPath || '');
  const [searchQuery, setSearchQuery] = useState(() => savedState?.searchQuery || '');
  const [editingItem, setEditingItem] = useState<number | null>(null);
  const [editingText, setEditingText] = useState('');
  const [currentLine, setCurrentLine] = useState(() => savedState?.currentLine || 0);

  // Refs for scroll sync
  const sourceScrollRef = useRef<HTMLDivElement>(null);
  const translationScrollRef = useRef<HTMLDivElement>(null);
  const scrollSyncActive = useRef<boolean>(false);

  // Save state to localStorage whenever key values change
  useEffect(() => {
    const stateToSave = {
      currentPage,
      pageSize,
      projectPath,
      searchQuery,
      currentLine
    };
    saveStateToStorage(stateToSave);
  }, [currentPage, pageSize, projectPath, searchQuery, currentLine]);

  // Auto-restore cache if we have a saved project path
  useEffect(() => {
    const initializeState = async () => {
      try {
        await checkCacheStatus();
        // Load page size, but don't fail if it's not available
        try {
          await loadPageSize();
        } catch (err) {
          console.warn('Could not load page size config:', err);
        }

        // Only try to restore if we have saved state and backend is accessible
        const currentSavedState = loadStateFromStorage(); // Re-check in case it was cleared
        if (currentSavedState?.projectPath && !cacheStatus.loaded) {
          setProjectPath(currentSavedState.projectPath);
          // Small delay to ensure state is set, then try to load
          setTimeout(async () => {
            try {
              await loadCacheFromSavedPath(currentSavedState.projectPath);
              // Update component state with the restored saved state
              setSavedState(currentSavedState);
              if (currentSavedState.currentPage) setCurrentPage(currentSavedState.currentPage);
              if (currentSavedState.pageSize) setPageSize(currentSavedState.pageSize);
              if (currentSavedState.searchQuery) setSearchQuery(currentSavedState.searchQuery);
              if (currentSavedState.currentLine !== undefined) setCurrentLine(currentSavedState.currentLine);
            } catch (err) {
              console.warn('Failed to restore cached project, backend may be unavailable:', err);
              // Clear the invalid saved state
              localStorage.removeItem(CACHE_EDITOR_STATE_KEY);
              setSavedState(null);
              setProjectPath('');
            }
          }, 100);
        }
      } catch (err) {
        console.warn('Backend not available, skipping auto-restore:', err);
        // Clear saved state if backend is not available
        localStorage.removeItem(CACHE_EDITOR_STATE_KEY);
        setSavedState(null);
      }
    };

    initializeState();
  }, []); // Only run on mount

  useEffect(() => {
    if (cacheStatus.loaded) {
      loadCacheItems();
    }
  }, [cacheStatus.loaded, currentPage, searchQuery, pageSize]);

  // Restore row alignment after data loads
  useEffect(() => {
    if (cacheItems.length > 0 && currentLine >= 0 && currentLine < cacheItems.length) {
      // Small delay to ensure DOM is updated
      setTimeout(() => {
        scrollToRow(sourceScrollRef, currentLine);
        scrollToRow(translationScrollRef, currentLine);
      }, 100);
    }
  }, [cacheItems, currentLine]);

  const loadPageSize = async () => {
    try {
      const response = await fetch('/api/config');
      if (response.ok) {
        const config = await response.json();
        if (config.cache_editor_page_size) {
          setPageSize(config.cache_editor_page_size);
        }
      }
    } catch (err) {
      // Use default value if config loading fails
      console.warn('Failed to load page size from config:', err);
    }
  };

  const checkCacheStatus = async () => {
    const response = await fetch('/api/cache/status');
    if (!response.ok) {
      throw new Error('Backend not available');
    }
    const status = await response.json();
    setCacheStatus(status);
  };

  const loadCacheFromPath = async () => {
    if (!projectPath.trim()) {
      setError(t('cache_editor_enter_project_path'));
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await fetch('/api/cache/load', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ project_path: projectPath })
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || t('cache_editor_failed_load_cache'));
      }

      const result = await response.json();
      await checkCacheStatus(); // Refresh status
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : t('cache_editor_failed_load_cache'));
    } finally {
      setLoading(false);
    }
  };

  const loadCacheFromSavedPath = async (path: string) => {
    const response = await fetch('/api/cache/load', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ project_path: path })
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }));
      throw new Error(errorData.detail || 'Failed to load cache from saved path');
    }

    await checkCacheStatus(); // Refresh status
    console.log('Cache restored from saved path:', path);
  };

  const loadCacheItems = async () => {
    setLoading(true);
    setCurrentLine(0);
    try {
      const params = new URLSearchParams({
        page: currentPage.toString(),
        page_size: pageSize.toString()
      });

      if (searchQuery) {
        params.append('search', searchQuery);
      }

      const response = await fetch(`/api/cache/items?${params}`);

      if (!response.ok) {
        throw new Error(t('cache_editor_failed_load_cache'));
      }

      const data = await response.json();
      setCacheItems(data.items);
      setPagination(data.pagination);
    } catch (err) {
      setError(err instanceof Error ? err.message : t('cache_editor_failed_load_cache'));
    } finally {
      setLoading(false);
    }
  };

  const updateCacheItem = async (itemId: number, newTranslation: string) => {
    try {
      const response = await fetch(`/api/cache/items/${itemId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          item_id: itemId,
          translation: newTranslation,
          project_path: projectPath
        })
      });

      if (!response.ok) {
        throw new Error(t('cache_editor_failed_update_item'));
      }

      // Update local state
      setCacheItems(items =>
        items.map(item =>
          item.id === itemId
            ? { ...item, translation: newTranslation, modified: true }
            : item
        )
      );

      setEditingItem(null);
      setEditingText('');
    } catch (err) {
      setError(err instanceof Error ? err.message : t('cache_editor_failed_update_item'));
    }
  };

  const handleEditStart = (item: CacheItem) => {
    setEditingItem(item.id);
    setEditingText(item.translation);
  };

  const handleEditSave = async () => {
    if (editingItem !== null) {
      await updateCacheItem(editingItem, editingText);
    }
  };

  const handleEditCancel = async () => {
    if (editingItem !== null) {
      const originalItem = cacheItems.find(item => item.id === editingItem);
      const hasChanges = originalItem && editingText !== originalItem.translation;

      if (hasChanges && editingText.trim() !== '') {
        // Auto-save on cancel if there are changes
        await updateCacheItem(editingItem, editingText);
      }
    }

    setEditingItem(null);
    setEditingText('');
  };

  // Shared function to scroll a container to align a specific row
  const scrollToRow = (containerRef: React.RefObject<HTMLDivElement>, rowIndex: number) => {
    if (containerRef.current) {
      const rowElements = containerRef.current.querySelectorAll('[data-row-index]');
      const targetRow = rowElements[rowIndex] as HTMLElement;

      if (targetRow) {
        const containerHeight = containerRef.current.clientHeight;
        const rowTop = targetRow.offsetTop;
        const rowHeight = targetRow.offsetHeight;

        // Center the target row in the viewport
        const scrollTop = rowTop - (containerHeight / 2) + (rowHeight / 2);
        containerRef.current.scrollTop = Math.max(0, scrollTop);
      }
    }
  };

  // Align both panes to show the same row at the same visual position
  const alignRowsInBothPanes = (index: number) => {
    setTimeout(() => {
      scrollToRow(sourceScrollRef, index);
      scrollToRow(translationScrollRef, index);
    }, 0);
  };

  const handleRowClick = (index: number) => {
    setCurrentLine(index);
    alignRowsInBothPanes(index);
  };

  const handleRowDoubleClick = (item: CacheItem, index: number) => {
    setCurrentLine(index);
    handleEditStart(item);
    alignRowsInBothPanes(index);
  };

  // Keyboard navigation (only Enter and Esc)
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (editingItem !== null && e.key === 'Escape') {
        e.preventDefault();
        handleEditCancel();
      } else if (editingItem === null && e.key === 'Enter' && cacheItems[currentLine]) {
        e.preventDefault();
        handleEditStart(cacheItems[currentLine]);
        setTimeout(() => {
          scrollToRow(sourceScrollRef, currentLine);
          scrollToRow(translationScrollRef, currentLine);
        }, 0);
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [currentLine, editingItem, cacheItems]);

  // Scroll synchronization with debounce to prevent recursion
  const handleScrollSync = (source: 'left' | 'right') => (e: React.UIEvent<HTMLDivElement>) => {
    // Prevent recursive sync calls
    if (scrollSyncActive.current) return;

    const scrollTop = e.currentTarget.scrollTop;

    scrollSyncActive.current = true;

    if (source === 'left' && translationScrollRef.current) {
      translationScrollRef.current.scrollTop = scrollTop;
    } else if (source === 'right' && sourceScrollRef.current) {
      sourceScrollRef.current.scrollTop = scrollTop;
    }

    // Reset sync flag after a brief delay
    setTimeout(() => {
      scrollSyncActive.current = false;
    }, 10);
  };

  return (
    <div className="h-screen flex flex-col cache-editor-container">
      {/* Header - Only show when not loaded */}
      {!cacheStatus.loaded && (
        <div className="p-6">
          <div className="bg-surface/50 rounded-lg p-4 mb-6">
            <h1 className="text-2xl font-bold mb-4">{t('cache_editor_title')}</h1>
            <div className="space-y-4">
              <div className="flex gap-4 items-end">
                <div className="flex-1">
                  <label className="block text-sm font-medium mb-2">{t('cache_editor_project_path')}</label>
                  <input
                    type="text"
                    value={projectPath}
                    onChange={(e) => setProjectPath(e.target.value)}
                    placeholder={t('cache_editor_project_path_placeholder')}
                    className="w-full px-3 py-2 bg-slate-900 border border-gray-600 rounded-md focus:border-primary"
                  />
                </div>
                <button
                  onClick={loadCacheFromPath}
                  disabled={loading || !projectPath.trim()}
                  className="px-4 py-2 bg-primary text-white rounded-md hover:bg-primary/80 disabled:opacity-50 transition-all duration-200"
                >
                  {loading ? t('cache_editor_loading') : t('cache_editor_load_cache')}
                </button>
              </div>
            </div>
          </div>

          {error && (
            <div className="bg-red-500/20 border border-red-500 text-red-100 px-4 py-2 rounded-md mb-4">
              {error}
            </div>
          )}
        </div>
      )}

      {cacheStatus.loaded && (
        <div className="flex-1 flex flex-col overflow-hidden">
          {/* Error display */}
          {error && (
            <div className="mx-4 mt-4 bg-red-500/20 border border-red-500 text-red-100 px-4 py-2 rounded-md">
              {error}
            </div>
          )}

          {/* Top navigation bar */}
          <div className="flex items-center justify-between p-4 bg-surface/30 border-b border-gray-700">
            <div className="flex items-center gap-4">
              <span className="text-sm text-gray-300">
                {t('cache_editor_line_info',
                  currentLine + 1 + (currentPage - 1) * pageSize,
                  pagination?.total_items || 0,
                  currentPage,
                  pagination?.total_pages || 0
                )}
              </span>
            </div>
            <div className="flex items-center gap-4">
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder={t('cache_editor_search_placeholder')}
                className="px-3 py-1 bg-slate-800 border border-gray-600 rounded text-sm focus:border-primary"
              />
              <button
                onClick={() => {
                  setCacheStatus({ loaded: false, file_count: 0, total_items: 0, project_name: null });
                  setCacheItems([]);
                  setPagination(null);
                  setCurrentPage(1);
                  setSearchQuery('');
                  setProjectPath('');
                  setCurrentLine(0);
                  // Clear saved state from localStorage and component state
                  localStorage.removeItem(CACHE_EDITOR_STATE_KEY);
                  setSavedState(null);
                }}
                className="px-3 py-1 bg-gray-600 text-white rounded text-sm hover:bg-gray-700"
              >
                {t('cache_editor_switch_project')}
              </button>
            </div>
          </div>

          {/* Main dual-pane editor area */}
          <div className="flex-1 flex overflow-hidden">
            {/* Left pane - Source text (read-only) */}
            <div className="flex-1 bg-surface/50 flex flex-col border-r border-gray-600">
              <div className="bg-purple-600/20 px-4 py-3 border-b border-purple-600/30">
                <h3 className="font-semibold text-purple-300">{t('cache_editor_source_text')}</h3>
              </div>
              <div
                ref={sourceScrollRef}
                className="flex-1 overflow-y-auto p-4 space-y-2"
                onScroll={handleScrollSync('left')}
              >
                {cacheItems.length === 0 ? (
                  <div className="text-center text-gray-500 py-8">
                    {loading ? t('cache_editor_loading') : t('cache_editor_no_source_loaded')}
                  </div>
                ) : (
                  cacheItems.map((item, index) => (
                    <div
                      key={item.id}
                      data-row-index={index}
                      className={`p-3 rounded border-l-4 cursor-pointer ${
                        index === currentLine
                          ? 'bg-blue-500/20 border-l-blue-500'
                          : 'bg-slate-800/50 border-l-gray-600 hover:bg-slate-700/50'
                      } transition-all duration-200`}
                      onClick={() => handleRowClick(index)}
                    >
                      <div className="text-xs text-gray-400 mb-1">
                        {index + 1 + (currentPage - 1) * pageSize}. {item.file_path}:{item.text_index}
                      </div>
                      <div className={`${index === currentLine ? 'text-white' : 'text-gray-300'}`}>
                        {item.source || <em className="text-gray-500">{t('cache_editor_no_source_text')}</em>}
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>

            {/* Right pane - Translation (editable) */}
            <div className="flex-1 bg-surface/50 flex flex-col">
              <div className={`px-4 py-3 border-b ${
                editingItem !== null
                  ? 'bg-red-600/20 border-red-600/30'
                  : 'bg-green-600/20 border-green-600/30'
              }`}>
                <h3 className={`font-semibold ${
                  editingItem !== null ? 'text-red-300' : 'text-green-300'
                }`}>
                  {t('cache_editor_translation')} {editingItem !== null ? t('cache_editor_editing') : ''}
                </h3>
              </div>
              <div
                ref={translationScrollRef}
                className="flex-1 overflow-y-auto p-4 space-y-2"
                onScroll={handleScrollSync('right')}
              >
                {cacheItems.length === 0 ? (
                  <div className="text-center text-gray-500 py-8">
                    {loading ? t('cache_editor_loading_translations') : t('cache_editor_no_translations_loaded')}
                  </div>
                ) : (
                  cacheItems.map((item, index) => (
                  <div
                    key={item.id}
                    data-row-index={index}
                    className={`p-3 rounded border-l-4 ${
                      index === currentLine && editingItem === item.id
                        ? 'bg-red-500/20 border-l-red-500'
                        : index === currentLine
                        ? 'bg-blue-500/20 border-l-blue-500'
                        : 'bg-slate-800/50 border-l-gray-600'
                    } transition-all duration-200`}
                    onClick={() => handleRowClick(index)}
                    onDoubleClick={() => handleRowDoubleClick(item, index)}
                  >
                    <div className="flex items-center justify-between text-xs text-gray-400 mb-1">
                      <span>{index + 1 + (currentPage - 1) * pageSize}.</span>
                      {item.modified && (
                        <span className="text-yellow-400">{t('cache_editor_modified')}</span>
                      )}
                    </div>

                    {editingItem === item.id ? (
                      <div className="space-y-2">
                        <textarea
                          value={editingText}
                          onChange={(e) => setEditingText(e.target.value)}
                          className="w-full h-24 p-2 bg-slate-900 border border-red-500 rounded resize-none focus:outline-none focus:ring-2 focus:ring-red-500"
                          autoFocus
                        />
                        <div className="flex gap-2">
                          <button
                            onClick={handleEditSave}
                            className="px-3 py-1 bg-green-600 text-white rounded text-sm hover:bg-green-700 transition-colors"
                          >
                            {t('cache_editor_save')}
                          </button>
                          <button
                            onClick={handleEditCancel}
                            className="px-3 py-1 bg-gray-600 text-white rounded text-sm hover:bg-gray-700 transition-colors"
                          >
                            {t('cache_editor_cancel')}
                          </button>
                        </div>
                      </div>
                    ) : (
                      <div
                        className={`cursor-pointer ${
                          index === currentLine ? 'text-white' : 'text-gray-300'
                        } hover:text-white transition-colors min-h-[2rem] flex items-center`}
                      >
                        {item.translation || <em className="text-gray-500">{t('cache_editor_no_translation')}</em>}
                      </div>
                    )}
                  </div>
                  ))
                )}
              </div>
            </div>
          </div>

          {/* Pagination */}
          {pagination && pagination.total_pages > 1 && (
            <div className="flex items-center justify-center gap-4 p-4 bg-surface/30 border-t border-gray-700">
              <button
                onClick={() => setCurrentPage(currentPage - 1)}
                disabled={!pagination.has_prev}
                className="px-3 py-1 bg-gray-600 text-white rounded disabled:opacity-50 hover:bg-gray-700 transition-colors"
              >
                {t('cache_editor_previous')}
              </button>

              <span className="text-sm text-gray-300">
                {t('cache_editor_page_info', currentPage, pagination.total_pages)}
              </span>

              <button
                onClick={() => setCurrentPage(currentPage + 1)}
                disabled={!pagination.has_next}
                className="px-3 py-1 bg-gray-600 text-white rounded disabled:opacity-50 hover:bg-gray-700 transition-colors"
              >
                {t('cache_editor_next')}
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
};