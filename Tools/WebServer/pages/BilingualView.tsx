import React, { useEffect, useState } from 'react';
import { useI18n } from '@/contexts/I18nContext';
import { DataService } from '@/services/DataService';
import { ProjectService } from '@/services/ProjectService';
import { Project, ProjectFile } from '@/types';
import { BilingualViewer } from '@/components/BilingualViewer';
import { Button } from '@/components/ui/button';
import { ArrowLeft, Loader2, AlertCircle } from 'lucide-react';
import { useToast } from '@/hooks/use-toast';

interface BilingualViewProps {
  projectId: string;
  fileId: string;
}

interface BilingualSegment {
  id: string;
  index: number;
  source: string;
  translation: string;
  status?: 'draft' | 'translated' | 'approved';
}

export const BilingualView: React.FC<BilingualViewProps> = ({ projectId, fileId }) => {
  const { t } = useI18n();
  const { toast } = useToast();

  const [project, setProject] = useState<Project | null>(null);
  const [currentFile, setCurrentFile] = useState<ProjectFile | null>(null);
  const [segments, setSegments] = useState<BilingualSegment[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadBilingualData();
  }, [projectId, fileId]);

  const loadBilingualData = async () => {
    setLoading(true);
    setError(null);

    try {
      // Load project
      const proj = await ProjectService.getProject(projectId);
      if (!proj) {
        throw new Error('Project not found');
      }
      setProject(proj);

      // Find file
      const file = proj.files.find(f => f.id === fileId);
      if (!file) {
        throw new Error('File not found');
      }
      setCurrentFile(file);

      // Load cache data
      if (proj.rootPath) {
        await DataService.loadCache(proj.rootPath);
      }

      // Load all segments (no pagination for bilingual view)
      const pageSize = 10000; // Large number to get all segments
      const res = await DataService.getCacheItems(1, pageSize, '', file?.path);

      const mappedSegments: BilingualSegment[] = res.items.map((item: any, index: number) => {
        let status: BilingualSegment['status'] = 'draft';
        if (item.translation_status === 1) status = 'translated';
        if (item.translation_status >= 2) status = 'approved';

        return {
          id: item.id.toString(),
          index: item.text_index || index,
          source: item.source || '',
          translation: item.translation || '',
          status: status
        };
      });

      setSegments(mappedSegments);
    } catch (err: any) {
      console.error('Failed to load bilingual data:', err);
      setError(err.message || 'Failed to load bilingual file');

      toast({
        title: 'Error',
        description: err.message || 'Failed to load bilingual file',
        variant: 'destructive'
      });
    } finally {
      setLoading(false);
    }
  };

  const handleBack = () => {
    window.location.hash = `/projects/${projectId}`;
  };

  if (loading) {
    return (
      <div className="h-screen flex flex-col items-center justify-center">
        <Loader2 className="w-12 h-12 animate-spin text-primary mb-4" />
        <p className="text-muted-foreground">{t('loading_bilingual') || 'Loading bilingual file...'}</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="h-screen flex flex-col items-center justify-center p-4">
        <AlertCircle className="w-12 h-12 text-destructive mb-4" />
        <h2 className="text-xl font-semibold mb-2">{t('error_loading') || 'Error Loading File'}</h2>
        <p className="text-muted-foreground mb-4 text-center">{error}</p>
        <Button onClick={handleBack}>
          <ArrowLeft className="w-4 h-4 mr-2" />
          {t('back_to_project') || 'Back to Project'}
        </Button>
      </div>
    );
  }

  return (
    <div className="h-screen flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b bg-card">
        <div className="flex items-center gap-4">
          <Button variant="ghost" size="sm" onClick={handleBack}>
            <ArrowLeft className="w-4 h-4 mr-1" />
            {t('back') || 'Back'}
          </Button>
          <div>
            <h2 className="text-lg font-semibold">
              {currentFile?.name || 'Bilingual View'}
            </h2>
            <p className="text-sm text-muted-foreground">
              {project?.name} → {t('bilingual_output') || 'Bilingual Output'}
            </p>
          </div>
        </div>
      </div>

      {/* Bilingual Viewer */}
      <div className="flex-1 overflow-hidden">
        <BilingualViewer
          segments={segments}
          fileName={currentFile?.name?.replace(/\.[^/.]+$/, '_bilingual.txt') || 'bilingual.txt'}
        />
      </div>
    </div>
  );
};
