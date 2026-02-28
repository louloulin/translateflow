import { Project, ProjectFile } from '@/types';

const STORAGE_KEY = 'ainiee_projects_v1';

export class ProjectService {
  private static projects: Project[] = [];

  static async init() {
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      if (stored) {
        this.projects = JSON.parse(stored);
      } else {
        // Add some mock data for demonstration
        this.projects = [
          {
            id: 'proj_001',
            name: 'Demo Game Translation',
            rootPath: '/Users/louloulin/Documents/linchong/ai/AiNiee-Next/output/demo_project',
            description: 'RPG Maker MZ game translation project',
            sourceLang: 'Japanese',
            targetLang: 'Chinese (Simplified)',
            createdAt: Date.now() - 86400000 * 2,
            updatedAt: Date.now() - 3600000,
            status: 'active',
            progress: 45,
            files: [
              {
                id: 'file_001',
                name: 'Map001.json',
                path: '/games/demo/data/Map001.json',
                size: 1024 * 50,
                sourceLang: 'Japanese',
                targetLang: 'Chinese (Simplified)',
                progress: 100,
                status: 'completed',
                lastModified: Date.now()
              },
              {
                id: 'file_002',
                name: 'CommonEvents.json',
                path: '/games/demo/data/CommonEvents.json',
                size: 1024 * 120,
                sourceLang: 'Japanese',
                targetLang: 'Chinese (Simplified)',
                progress: 30,
                status: 'translating',
                lastModified: Date.now()
              }
            ]
          }
        ];
        this.save();
      }
    } catch (e) {
      console.error('Failed to init ProjectService', e);
    }
  }

  static async listProjects(): Promise<Project[]> {
    if (this.projects.length === 0) {
      await this.init();
    }
    return [...this.projects];
  }

  static async getProject(id: string): Promise<Project | null> {
    const project = this.projects.find(p => p.id === id);
    return project || null;
  }

  static async createProject(data: Partial<Project>): Promise<Project> {
    const newProject: Project = {
      id: `proj_${Date.now()}`,
      name: data.name || 'New Project',
      rootPath: data.rootPath || '/tmp/ainiee_project',
      description: data.description || '',
      sourceLang: data.sourceLang || 'Japanese',
      targetLang: data.targetLang || 'Chinese (Simplified)',
      createdAt: Date.now(),
      updatedAt: Date.now(),
      status: 'active',
      progress: 0,
      files: [],
      ...data
    } as Project;

    this.projects.unshift(newProject);
    this.save();
    return newProject;
  }

  static async updateProject(id: string, data: Partial<Project>): Promise<Project | null> {
    const index = this.projects.findIndex(p => p.id === id);
    if (index === -1) return null;

    this.projects[index] = {
      ...this.projects[index],
      ...data,
      updatedAt: Date.now()
    };
    this.save();
    return this.projects[index];
  }

  static async deleteProject(id: string): Promise<boolean> {
    const index = this.projects.findIndex(p => p.id === id);
    if (index === -1) return false;

    this.projects.splice(index, 1);
    this.save();
    return true;
  }

  private static save() {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(this.projects));
    } catch (e) {
      console.error('Failed to save projects', e);
    }
  }
}
