import React from 'react';
import { Card, CardContent, CardFooter, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { ProgressBar } from '@/components/ProgressBar';
import { Project } from '@/types';
import { ArrowRight, Calendar, Globe, FileText, Trash2 } from 'lucide-react';
import { cn } from '@/lib/utils';
import { useI18n } from '@/contexts/I18nContext';

interface ProjectCardProps {
  project: Project;
  onOpen: (id: string) => void;
  onDelete?: (id: string) => void;
  variant?: 'default' | 'compact';
}

export const ProjectCard: React.FC<ProjectCardProps> = ({ 
  project, 
  onOpen, 
  onDelete,
  variant = 'default' 
}) => {
  const { t } = useI18n();
  const fileCount = project.files.length;
  
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active': return 'default';
      case 'completed': return 'secondary';
      case 'archived': return 'outline';
      default: return 'default';
    }
  };

  const getProgressVariant = (progress: number) => {
    if (progress === 100) return 'success';
    if (progress > 0) return 'default';
    return 'default';
  };

  if (variant === 'compact') {
    return (
      <div 
        className="group flex items-center gap-4 p-3 rounded-lg border bg-card hover:bg-accent/50 transition-colors cursor-pointer"
        onClick={() => onOpen(project.id)}
      >
        <div className="h-10 w-10 rounded-md bg-primary/10 flex items-center justify-center shrink-0">
          <FileText className="text-primary h-5 w-5" />
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center justify-between mb-1">
            <h4 className="text-sm font-medium truncate">{project.name}</h4>
            <span className="text-xs text-muted-foreground">{new Date(project.updatedAt).toLocaleDateString()}</span>
          </div>
          <div className="flex items-center gap-2">
            <ProgressBar 
              progress={project.progress} 
              size="sm" 
              className="flex-1"
              variant={getProgressVariant(project.progress)}
            />
            <span className="text-xs text-muted-foreground tabular-nums">{project.progress}%</span>
          </div>
        </div>
      </div>
    );
  }

  return (
    <Card className="group relative overflow-hidden hover:shadow-lg transition-all border-l-4 border-l-primary/50">
      <CardHeader className="pb-3">
        <div className="flex justify-between items-start">
          <div className="space-y-1">
            <CardTitle className="text-lg flex items-center gap-2">
              <span className="truncate" title={project.name}>{project.name}</span>
            </CardTitle>
            <CardDescription className="line-clamp-1">
              {project.description || t('ui_no_description') || 'No description'}
            </CardDescription>
          </div>
          {/* @ts-ignore */}
          <Badge variant={getStatusColor(project.status)}>
            {project.status.toUpperCase()}
          </Badge>
        </div>
      </CardHeader>
      
      <CardContent className="pb-3 space-y-4">
        <div className="flex items-center gap-4 text-xs text-muted-foreground">
          <div className="flex items-center gap-1">
            <Globe className="h-3.5 w-3.5" />
            <span>{project.sourceLang} → {project.targetLang}</span>
          </div>
          <div className="flex items-center gap-1">
            <FileText className="h-3.5 w-3.5" />
            <span>{fileCount} files</span>
          </div>
        </div>

        <div className="space-y-1.5">
          <div className="flex justify-between text-xs">
            <span className="text-muted-foreground">Progress</span>
            <span className="font-medium">{project.progress}%</span>
          </div>
          <ProgressBar 
            progress={project.progress} 
            variant={getProgressVariant(project.progress)}
            size="md"
          />
        </div>
      </CardContent>

      <CardFooter className="pt-3 border-t bg-muted/20 flex justify-between">
        <div className="flex items-center gap-1 text-xs text-muted-foreground">
          <Calendar className="h-3.5 w-3.5" />
          <span>Updated {new Date(project.updatedAt).toLocaleDateString()}</span>
        </div>
        
        <div className="flex gap-2">
            {onDelete && (
                <Button 
                    variant="ghost" 
                    size="sm" 
                    className="h-8 w-8 p-0 text-muted-foreground hover:text-destructive"
                    onClick={(e) => {
                        e.stopPropagation();
                        onDelete(project.id);
                    }}
                >
                    <Trash2 className="h-4 w-4" />
                </Button>
            )}
            <Button 
            variant="ghost" 
            size="sm" 
            className="h-8 text-xs hover:bg-primary hover:text-primary-foreground group-hover:translate-x-1 transition-all"
            onClick={() => onOpen(project.id)}
            >
            Open <ArrowRight className="ml-1 h-3.5 w-3.5" />
            </Button>
        </div>
      </CardFooter>
    </Card>
  );
};
