import { Segment } from '@/types';

// Mock data generator
const generateMockSegments = (count: number): Segment[] => {
  return Array.from({ length: count }).map((_, i) => ({
    id: `seg_${i + 1}`,
    index: i + 1,
    source: `This is source sentence number ${i + 1}. It contains some text to translate.`,
    target: i % 3 === 0 ? `这是第 ${i + 1} 句源文。它包含一些需要翻译的文本。` : '',
    status: i % 3 === 0 ? 'translated' : 'draft',
    locked: false,
    comments: []
  }));
};

export class EditorService {
  private static segmentsCache: Map<string, Segment[]> = new Map();

  private static getStorageKey(projectId: string, fileId: string): string {
    return `ainiee_segments_${projectId}_${fileId}`;
  }

  static async loadSegments(projectId: string, fileId: string): Promise<Segment[]> {
    const key = this.getStorageKey(projectId, fileId);
    
    // Check memory cache first
    if (this.segmentsCache.has(key)) {
      return [...(this.segmentsCache.get(key) || [])];
    }

    // Check localStorage
    const stored = localStorage.getItem(key);
    if (stored) {
      const segments = JSON.parse(stored);
      this.segmentsCache.set(key, segments);
      return segments;
    }

    // Generate mock data if nothing exists
    await new Promise(resolve => setTimeout(resolve, 500));
    const segments = generateMockSegments(50);
    this.segmentsCache.set(key, segments);
    this.saveToStorage(projectId, fileId, segments);
    return segments;
  }

  static async updateSegment(projectId: string, fileId: string, segmentId: string, data: Partial<Segment>): Promise<Segment | null> {
    const key = this.getStorageKey(projectId, fileId);
    let segments = this.segmentsCache.get(key);

    if (!segments) {
      // Try to load from storage if not in memory
      const stored = localStorage.getItem(key);
      if (stored) {
        segments = JSON.parse(stored);
        this.segmentsCache.set(key, segments!);
      } else {
        return null;
      }
    }

    const index = segments!.findIndex(s => s.id === segmentId);
    if (index === -1) return null;

    segments![index] = { ...segments![index], ...data };
    this.segmentsCache.set(key, segments!);
    this.saveToStorage(projectId, fileId, segments!);
    return segments![index];
  }

  static async mockTranslateSegment(source: string): Promise<string> {
    await new Promise(resolve => setTimeout(resolve, 600)); // Simulate API call
    // Simple mock translation logic
    if (source.includes('source')) return source.replace('source', '源').replace('sentence', '句子') + ' [AI]';
    return `[AI 翻译] ${source}`;
  }

  static async mockTranslateAll(projectId: string, fileId: string): Promise<Segment[]> {
    const key = this.getStorageKey(projectId, fileId);
    await new Promise(resolve => setTimeout(resolve, 1500)); // Simulate bulk API call
    
    let segments = this.segmentsCache.get(key);
    if (!segments) {
       const stored = localStorage.getItem(key);
       if (stored) segments = JSON.parse(stored);
    }
    
    if (!segments) return [];

    const updatedSegments = segments.map(s => {
      // Only translate empty or draft segments
      if ((!s.target || s.status === 'draft') && !s.locked) {
        return { 
          ...s, 
          target: s.target || `[AI 全文翻译] ${s.source}`, 
          status: 'translated' as const 
        };
      }
      return s;
    });

    this.segmentsCache.set(key, updatedSegments);
    this.saveToStorage(projectId, fileId, updatedSegments);
    return updatedSegments;
  }

  static async saveAll(projectId: string, fileId: string): Promise<boolean> {
    // Already saving to localStorage on every update, but this could trigger a backend sync
    await new Promise(resolve => setTimeout(resolve, 800));
    return true;
  }

  private static saveToStorage(projectId: string, fileId: string, segments: Segment[]) {
    localStorage.setItem(this.getStorageKey(projectId, fileId), JSON.stringify(segments));
  }
}
