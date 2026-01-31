/**
 * Web版本缓存管理服务
 * 基于TUI编辑器的缓存机制设计，提供与CLI相同的缓存功能
 */

export interface CacheItem {
  text_index: number;
  source_text: string;
  translated_text?: string;
  polished_text?: string;
  translation_status: number; // 0: 未翻译, 1: 已翻译, 2: 已润色
  modified?: boolean; // Web专用，标记是否已修改
}

export interface CacheFile {
  file_path: string;
  items: CacheItem[];
}

export interface CacheProject {
  files: { [filePath: string]: CacheFile };
  metadata: {
    version: string;
    created_at: string;
    last_modified: string;
    total_items: number;
  };
}

export interface CacheMetrics {
  total_files: number;
  total_items: number;
  translated_items: number;
  polished_items: number;
  modified_items: number; // Web端修改的项目数量
}

export interface CacheServiceEvents {
  onCacheLoaded: (project: CacheProject) => void;
  onCacheUpdated: (filePath: string, item: CacheItem) => void;
  onCacheSaved: (success: boolean) => void;
  onError: (error: string) => void;
}

/**
 * Web缓存管理器
 * 提供与CLI TUI编辑器相同的缓存读取、修改和保存功能
 */
export class CacheService {
  private project: CacheProject | null = null;
  private eventListeners: Partial<CacheServiceEvents> = {};
  private autoSaveTimer: NodeJS.Timeout | null = null;
  private modifiedItems: Set<string> = new Set(); // 跟踪修改项目的唯一标识

  // 缓存配置
  private config = {
    autoSaveInterval: 30000, // 30秒自动保存
    batchSize: 50, // 批量操作大小
    maxRetries: 3, // 最大重试次数
    cacheExpiration: 5 * 60 * 1000, // 5分钟缓存过期
  };

  // 内存缓存，用于提高性能
  private memoryCache: Map<string, CacheItem[]> = new Map();
  private cacheTimestamps: Map<string, number> = new Map();

  constructor() {
    // 启动自动保存
    this.startAutoSave();
  }

  /**
   * 加载缓存项目
   * 对应TUI中的load_cache_data方法
   */
  async loadProject(projectPath: string): Promise<CacheProject> {
    try {
      // 构建缓存文件路径
      const cacheFilePath = `${projectPath}/cache/AinieeCacheData.json`;

      // 通过DataService加载缓存数据（需要后端API支持）
      const response = await fetch(`/api/cache/load?path=${encodeURIComponent(cacheFilePath)}`);

      if (!response.ok) {
        throw new Error(`Failed to load cache: ${response.statusText}`);
      }

      const cacheData = await response.json();

      // 转换为Web格式
      this.project = this.convertToWebFormat(cacheData);

      // 通知监听器
      this.eventListeners.onCacheLoaded?.(this.project);

      // 更新内存缓存
      this.updateMemoryCache();

      return this.project;
    } catch (error) {
      const errorMessage = `Cache loading failed: ${error instanceof Error ? error.message : 'Unknown error'}`;
      this.eventListeners.onError?.(errorMessage);
      throw error;
    }
  }

  /**
   * 获取文件的缓存项目（分页支持）
   * 对应TUI中的_get_current_page_data方法
   */
  async getFileItems(
    filePath: string,
    page: number = 0,
    pageSize: number = 15,
    useCache: boolean = true
  ): Promise<{
    items: CacheItem[];
    total_items: number;
    current_page: number;
    page_size: number;
    total_pages: number;
    file_path: string;
  }> {
    // 检查内存缓存
    const cacheKey = filePath;
    const cached = this.memoryCache.get(cacheKey);
    const cacheTime = this.cacheTimestamps.get(cacheKey) || 0;
    const isExpired = Date.now() - cacheTime > this.config.cacheExpiration;

    let items: CacheItem[] = [];

    if (useCache && cached && !isExpired) {
      items = cached;
    } else {
      // 从项目数据或API获取
      if (this.project && this.project.files[filePath]) {
        items = this.project.files[filePath].items;
      } else {
        // 如果项目未加载或文件不存在，通过API获取
        const response = await fetch(`/api/cache/file?path=${encodeURIComponent(filePath)}`);
        if (response.ok) {
          const fileData = await response.json();
          items = fileData.items || [];
        }
      }

      // 更新缓存
      this.memoryCache.set(cacheKey, items);
      this.cacheTimestamps.set(cacheKey, Date.now());
    }

    // 过滤掉没有翻译内容的项目（与TUI保持一致）
    const filteredItems = items.filter(item =>
      item.translated_text?.trim() || item.polished_text?.trim()
    );

    // 计算分页
    const totalItems = filteredItems.length;
    const totalPages = Math.ceil(totalItems / pageSize);
    const start = page * pageSize;
    const end = Math.min(start + pageSize, totalItems);
    const pageItems = filteredItems.slice(start, end);

    return {
      items: pageItems,
      total_items: totalItems,
      current_page: page,
      page_size: pageSize,
      total_pages: totalPages,
      file_path: filePath
    };
  }

  /**
   * 更新缓存项目
   * 对应TUI中的_save_to_cache方法
   */
  async updateItem(filePath: string, textIndex: number, newTranslation: string): Promise<boolean> {
    try {
      if (!this.project || !this.project.files[filePath]) {
        throw new Error(`File not found in cache: ${filePath}`);
      }

      const fileItems = this.project.files[filePath].items;
      const itemIndex = fileItems.findIndex(item => item.text_index === textIndex);

      if (itemIndex === -1) {
        throw new Error(`Item not found: ${textIndex} in ${filePath}`);
      }

      const item = fileItems[itemIndex];
      const itemId = `${filePath}:${textIndex}`;

      // 更新项目
      if (item.translation_status === 2) {
        // 已润色状态，更新polished_text
        item.polished_text = newTranslation;
      } else {
        // 更新translated_text
        item.translated_text = newTranslation;
        // 如果之前未翻译，更新状态
        if (item.translation_status === 0) {
          item.translation_status = 1;
        }
      }

      item.modified = true;

      // 标记为已修改
      this.modifiedItems.add(itemId);

      // 更新内存缓存
      this.invalidateMemoryCache(filePath);

      // 通知监听器
      this.eventListeners.onCacheUpdated?.(filePath, item);

      // 立即保存（可选，根据配置决定）
      if (this.modifiedItems.size >= 5) {
        await this.saveProject();
      }

      return true;
    } catch (error) {
      const errorMessage = `Failed to update item: ${error instanceof Error ? error.message : 'Unknown error'}`;
      this.eventListeners.onError?.(errorMessage);
      return false;
    }
  }

  /**
   * 批量更新项目
   */
  async batchUpdateItems(updates: Array<{
    filePath: string;
    textIndex: number;
    newTranslation: string;
  }>): Promise<boolean> {
    try {
      const results = await Promise.all(
        updates.map(update =>
          this.updateItem(update.filePath, update.textIndex, update.newTranslation)
        )
      );

      return results.every(result => result);
    } catch (error) {
      this.eventListeners.onError?.(`Batch update failed: ${error}`);
      return false;
    }
  }

  /**
   * 保存项目到文件系统
   * 对应TUI中的require_save_to_file方法
   */
  async saveProject(): Promise<boolean> {
    try {
      if (!this.project || this.modifiedItems.size === 0) {
        return true; // 没有修改，无需保存
      }

      // 准备保存数据
      const saveData = this.convertToApiFormat(this.project);

      // 发送到后端API
      const response = await fetch('/api/cache/save', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(saveData),
      });

      if (!response.ok) {
        throw new Error(`Save failed: ${response.statusText}`);
      }

      // 清除修改标记
      this.modifiedItems.clear();

      // 更新项目元数据
      this.project.metadata.last_modified = new Date().toISOString();

      // 通知监听器
      this.eventListeners.onCacheSaved?.(true);

      return true;
    } catch (error) {
      this.eventListeners.onError?.(`Save failed: ${error}`);
      this.eventListeners.onCacheSaved?.(false);
      return false;
    }
  }

  /**
   * 搜索缓存项目
   * 支持TUI编辑器的搜索功能
   */
  async searchItems(
    query: string,
    options: {
      searchSource?: boolean;
      searchTranslation?: boolean;
      caseSensitive?: boolean;
      filePath?: string;
    } = {}
  ): Promise<Array<{
    filePath: string;
    textIndex: number;
    lineNumber: number;
    source: string;
    translation: string;
    matchType: 'source' | 'translation';
    context?: string;
  }>> {
    const {
      searchSource = true,
      searchTranslation = true,
      caseSensitive = false,
      filePath
    } = options;

    if (!this.project) {
      return [];
    }

    const results: Array<any> = [];
    const searchQuery = caseSensitive ? query : query.toLowerCase();

    const filesToSearch = filePath
      ? [filePath]
      : Object.keys(this.project.files);

    for (const file of filesToSearch) {
      const fileData = this.project.files[file];
      if (!fileData) continue;

      fileData.items.forEach((item, index) => {
        const sourceText = caseSensitive ? item.source_text : item.source_text.toLowerCase();
        const translation = item.translated_text || item.polished_text || '';
        const translationText = caseSensitive ? translation : translation.toLowerCase();

        let matchFound = false;
        let matchType: 'source' | 'translation' = 'source';

        if (searchSource && sourceText.includes(searchQuery)) {
          matchFound = true;
          matchType = 'source';
        } else if (searchTranslation && translationText.includes(searchQuery)) {
          matchFound = true;
          matchType = 'translation';
        }

        if (matchFound) {
          results.push({
            filePath: file,
            textIndex: item.text_index,
            lineNumber: index + 1,
            source: item.source_text,
            translation,
            matchType,
            context: this.getSearchContext(fileData.items, index)
          });
        }
      });
    }

    return results;
  }

  /**
   * 获取缓存统计信息
   */
  getMetrics(): CacheMetrics {
    if (!this.project) {
      return {
        total_files: 0,
        total_items: 0,
        translated_items: 0,
        polished_items: 0,
        modified_items: 0
      };
    }

    let totalItems = 0;
    let translatedItems = 0;
    let polishedItems = 0;
    let modifiedItems = 0;

    Object.values(this.project.files).forEach(file => {
      file.items.forEach(item => {
        totalItems++;
        if (item.translation_status >= 1) translatedItems++;
        if (item.translation_status === 2) polishedItems++;
        if (item.modified) modifiedItems++;
      });
    });

    return {
      total_files: Object.keys(this.project.files).length,
      total_items: totalItems,
      translated_items: translatedItems,
      polished_items: polishedItems,
      modified_items: modifiedItems
    };
  }

  /**
   * 事件监听器管理
   */
  addEventListener<K extends keyof CacheServiceEvents>(
    event: K,
    listener: CacheServiceEvents[K]
  ): void {
    this.eventListeners[event] = listener;
  }

  removeEventListener<K extends keyof CacheServiceEvents>(event: K): void {
    delete this.eventListeners[event];
  }

  /**
   * 清理资源
   */
  destroy(): void {
    this.stopAutoSave();
    this.memoryCache.clear();
    this.cacheTimestamps.clear();
    this.modifiedItems.clear();
    this.eventListeners = {};
  }

  // 私有方法

  private convertToWebFormat(apiData: any): CacheProject {
    // 将API数据转换为Web格式
    // 这里需要根据实际API格式进行调整
    return {
      files: apiData.files || {},
      metadata: {
        version: apiData.version || '1.0.0',
        created_at: apiData.created_at || new Date().toISOString(),
        last_modified: apiData.last_modified || new Date().toISOString(),
        total_items: apiData.total_items || 0
      }
    };
  }

  private convertToApiFormat(project: CacheProject): any {
    // 将Web格式转换为API格式
    return {
      ...project,
      save_timestamp: Date.now()
    };
  }

  private updateMemoryCache(): void {
    if (!this.project) return;

    Object.entries(this.project.files).forEach(([filePath, fileData]) => {
      this.memoryCache.set(filePath, fileData.items);
      this.cacheTimestamps.set(filePath, Date.now());
    });
  }

  private invalidateMemoryCache(filePath: string): void {
    this.memoryCache.delete(filePath);
    this.cacheTimestamps.delete(filePath);
  }

  private getSearchContext(items: CacheItem[], index: number): string {
    const contextSize = 1;
    const start = Math.max(0, index - contextSize);
    const end = Math.min(items.length, index + contextSize + 1);

    return items.slice(start, end)
      .map(item => item.source_text.substring(0, 50))
      .join(' ... ');
  }

  private startAutoSave(): void {
    this.autoSaveTimer = setInterval(() => {
      if (this.modifiedItems.size > 0) {
        this.saveProject().catch(error => {
          console.error('Auto-save failed:', error);
        });
      }
    }, this.config.autoSaveInterval);
  }

  private stopAutoSave(): void {
    if (this.autoSaveTimer) {
      clearInterval(this.autoSaveTimer);
      this.autoSaveTimer = null;
    }
  }
}

// 单例实例
export const cacheService = new CacheService();