import React, { useState, useEffect, useMemo } from 'react';
import { useI18n } from '@/contexts/I18nContext';
import { Project } from '@/types';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  TrendingUp,
  Clock,
  FileText,
  CheckCircle2,
  AlertCircle,
  Activity,
  Zap,
  Calendar,
  BarChart3,
  PieChart,
  Timer,
  Target,
  ArrowUp,
  ArrowDown,
  Minus
} from 'lucide-react';
import { cn } from '@/lib/utils';

interface ProgressDashboardProps {
  projects: Project[];
}

interface ProjectStats {
  totalProjects: number;
  activeProjects: number;
  completedProjects: number;
  totalFiles: number;
  completedFiles: number;
  inProgressFiles: number;
  averageProgress: number;
  totalSegments: number;
  completedSegments: number;
}

interface TimeEstimate {
  estimatedMinutes: number;
  basedOnSpeed: number;
}

export function ProgressDashboard({ projects }: ProgressDashboardProps) {
  const { t } = useI18n();
  const [timeRange, setTimeRange] = useState<'week' | 'month' | 'all'>('week');

  // Calculate project statistics
  const stats: ProjectStats = useMemo(() => {
    let totalFiles = 0;
    let completedFiles = 0;
    let inProgressFiles = 0;
    let totalSegments = 0;
    let completedSegments = 0;
    let totalProgress = 0;
    let activeCount = 0;
    let completedCount = 0;

    projects.forEach(project => {
      if (project.status === 'active') activeCount++;
      if (project.status === 'completed') completedCount++;

      if (project.files) {
        project.files.forEach(file => {
          totalFiles++;
          if (file.status === 'completed') {
            completedFiles++;
          } else if (file.status === 'translating') {
            inProgressFiles++;
          }

          // Estimate segments based on file size (rough approximation)
          const estimatedSegments = Math.max(1, Math.floor(file.size / 100));
          totalSegments += estimatedSegments;
          completedSegments += Math.floor(estimatedSegments * (file.progress / 100));
        });
      }

      totalProgress += project.progress || 0;
    });

    const avgProgress = projects.length > 0 ? totalProgress / projects.length : 0;

    return {
      totalProjects: projects.length,
      activeProjects: activeCount,
      completedProjects: completedCount,
      totalFiles,
      completedFiles,
      inProgressFiles,
      averageProgress: Math.round(avgProgress),
      totalSegments,
      completedSegments
    };
  }, [projects]);

  // Calculate time estimates
  const timeEstimate: TimeEstimate = useMemo(() => {
    // Assume average translation speed of 500 words/min
    const wordsPerMinute = 500;
    const remainingSegments = stats.totalSegments - stats.completedSegments;
    const estimatedMinutes = Math.ceil(remainingSegments / 50); // ~50 segments per minute
    return {
      estimatedMinutes,
      basedOnSpeed: wordsPerMinute
    };
  }, [stats]);

  // Get completion rate
  const completionRate = stats.totalFiles > 0
    ? Math.round((stats.completedFiles / stats.totalFiles) * 100)
    : 0;

  // Get recent activity (mock data for now)
  const recentActivity = useMemo(() => {
    return projects
      .filter(p => p.status === 'active' || p.status === 'completed')
      .sort((a, b) => (b.updatedAt || 0) - (a.updatedAt || 0))
      .slice(0, 5)
      .map(p => ({
        id: p.id,
        name: p.name,
        status: p.status,
        progress: p.progress,
        updatedAt: p.updatedAt
      }));
  }, [projects]);

  // Format time remaining
  const formatTimeRemaining = (minutes: number) => {
    if (minutes < 60) {
      return `${minutes} ${t('minutes', '分钟')}`;
    }
    const hours = Math.floor(minutes / 60);
    const mins = minutes % 60;
    if (hours < 24) {
      return `${hours}${t('hours', '小时')}${mins}${t('minutes_short', '分')}`;
    }
    const days = Math.floor(hours / 24);
    const hrs = hours % 24;
    return `${days}${t('days', '天')}${hrs}${t('hours_short', '时')}`;
  };

  const formatDate = (timestamp: number) => {
    if (!timestamp) return '-';
    const date = new Date(timestamp);
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    const hours = Math.floor(diff / (1000 * 60 * 60));
    const days = Math.floor(hours / 24);

    if (days > 0) return `${days}${t('days_ago', '天前')}`;
    if (hours > 0) return `${hours}${t('hours_ago', '小时前')}`;
    return t('just_now', '刚刚');
  };

  return (
    <div className="space-y-6">
      {/* Stats Overview */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Total Projects */}
        <Card>
          <CardHeader className="pb-2">
            <CardDescription className="flex items-center gap-2">
              <FileText className="h-4 w-4" />
              {t('totalProjects', '总项目数')}
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">{stats.totalProjects}</div>
            <div className="flex items-center gap-2 mt-1 text-xs text-muted-foreground">
              <span className="text-green-500 flex items-center gap-1">
                <CheckCircle2 className="h-3 w-3" />
                {stats.completedProjects} {t('completed', '已完成')}
              </span>
              <span className="text-blue-500 flex items-center gap-1">
                <Activity className="h-3 w-3" />
                {stats.activeProjects} {t('active', '进行中')}
              </span>
            </div>
          </CardContent>
        </Card>

        {/* Overall Progress */}
        <Card>
          <CardHeader className="pb-2">
            <CardDescription className="flex items-center gap-2">
              <TrendingUp className="h-4 w-4" />
              {t('overallProgress', '总体进度')}
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">{stats.averageProgress}%</div>
            <Progress value={stats.averageProgress} className="h-2 mt-2" />
            <div className="text-xs text-muted-foreground mt-1">
              {stats.completedSegments} / {stats.totalSegments} {t('segments', '段落')}
            </div>
          </CardContent>
        </Card>

        {/* Completion Rate */}
        <Card>
          <CardHeader className="pb-2">
            <CardDescription className="flex items-center gap-2">
              <Target className="h-4 w-4" />
              {t('completionRate', '完成率')}
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">{completionRate}%</div>
            <div className="flex items-center gap-2 mt-1 text-xs text-muted-foreground">
              <span className="text-green-500 flex items-center gap-1">
                <CheckCircle2 className="h-3 w-3" />
                {stats.completedFiles} {t('files', '文件')}
              </span>
              <span className="text-amber-500 flex items-center gap-1">
                <Clock className="h-3 w-3" />
                {stats.inProgressFiles} {t('inProgress', '进行中')}
              </span>
            </div>
          </CardContent>
        </Card>

        {/* Estimated Time */}
        <Card>
          <CardHeader className="pb-2">
            <CardDescription className="flex items-center gap-2">
              <Timer className="h-4 w-4" />
              {t('estimatedTime', '预计剩余时间')}
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">
              {timeEstimate.estimatedMinutes > 0
                ? formatTimeRemaining(timeEstimate.estimatedMinutes)
                : t('completed', '已完成')}
            </div>
            <div className="text-xs text-muted-foreground mt-1 flex items-center gap-1">
              <Zap className="h-3 w-3" />
              {t('basedOnSpeed', '基于速度')}: ~{timeEstimate.basedOnSpeed} {t('wpm', '词/分钟')}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Detailed Stats */}
      <Tabs defaultValue="overview" className="w-full">
        <TabsList>
          <TabsTrigger value="overview">
            <BarChart3 className="h-4 w-4 mr-2" />
            {t('overview', '概览')}
          </TabsTrigger>
          <TabsTrigger value="activity">
            <Activity className="h-4 w-4 mr-2" />
            {t('recentActivity', '最近活动')}
          </TabsTrigger>
          <TabsTrigger value="detailed">
            <PieChart className="h-4 w-4 mr-2" />
            {t('detailedStats', '详细统计')}
          </TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="mt-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Progress by Project */}
            <Card>
              <CardHeader>
                <CardTitle className="text-base">{t('progressByProject', '项目进度')}</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                {projects.length === 0 ? (
                  <p className="text-muted-foreground text-sm">{t('noProjects', '暂无项目')}</p>
                ) : (
                  projects.slice(0, 5).map(project => (
                    <div key={project.id} className="space-y-1">
                      <div className="flex items-center justify-between text-sm">
                        <span className="truncate max-w-[200px]">{project.name}</span>
                        <span className="text-muted-foreground">{project.progress}%</span>
                      </div>
                      <Progress value={project.progress} className="h-2" />
                    </div>
                  ))
                )}
              </CardContent>
            </Card>

            {/* Status Distribution */}
            <Card>
              <CardHeader>
                <CardTitle className="text-base">{t('fileStatus', '文件状态分布')}</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="space-y-2">
                    <div className="flex items-center justify-between text-sm">
                      <span className="flex items-center gap-2">
                        <div className="w-3 h-3 rounded-full bg-green-500" />
                        {t('completed', '已完成')}
                      </span>
                      <span className="font-medium">{stats.completedFiles}</span>
                    </div>
                    <Progress value={completionRate} className="h-2" />
                  </div>
                  <div className="space-y-2">
                    <div className="flex items-center justify-between text-sm">
                      <span className="flex items-center gap-2">
                        <div className="w-3 h-3 rounded-full bg-blue-500" />
                        {t('inProgress', '进行中')}
                      </span>
                      <span className="font-medium">{stats.inProgressFiles}</span>
                    </div>
                    <Progress value={stats.totalFiles > 0 ? (stats.inProgressFiles / stats.totalFiles) * 100 : 0} className="h-2" />
                  </div>
                  <div className="space-y-2">
                    <div className="flex items-center justify-between text-sm">
                      <span className="flex items-center gap-2">
                        <div className="w-3 h-3 rounded-full bg-gray-300" />
                        {t('pending', '待处理')}
                      </span>
                      <span className="font-medium">{stats.totalFiles - stats.completedFiles - stats.inProgressFiles}</span>
                    </div>
                    <Progress value={stats.totalFiles > 0 ? ((stats.totalFiles - stats.completedFiles - stats.inProgressFiles) / stats.totalFiles) * 100 : 0} className="h-2" />
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="activity" className="mt-4">
          <Card>
            <CardHeader>
              <CardTitle className="text-base">{t('recentActivity', '最近活动')}</CardTitle>
            </CardHeader>
            <CardContent>
              {recentActivity.length === 0 ? (
                <p className="text-muted-foreground text-sm">{t('noRecentActivity', '暂无最近活动')}</p>
              ) : (
                <div className="space-y-4">
                  {recentActivity.map(activity => (
                    <div key={activity.id} className="flex items-center gap-4">
                      {activity.status === 'completed' ? (
                        <CheckCircle2 className="h-5 w-5 text-green-500" />
                      ) : activity.status === 'active' ? (
                        <Activity className="h-5 w-5 text-blue-500" />
                      ) : (
                        <AlertCircle className="h-5 w-5 text-amber-500" />
                      )}
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium truncate">{activity.name}</p>
                        <p className="text-xs text-muted-foreground">
                          {activity.status === 'completed' ? t('completed', '已完成') : t('inProgress', '进行中')} - {activity.progress}%
                        </p>
                      </div>
                      <span className="text-xs text-muted-foreground">
                        {formatDate(activity.updatedAt || 0)}
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="detailed" className="mt-4">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <Card>
              <CardContent className="pt-6">
                <div className="text-center">
                  <div className="text-3xl font-bold">{stats.totalFiles}</div>
                  <div className="text-sm text-muted-foreground mt-1">{t('totalFiles', '总文件数')}</div>
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="pt-6">
                <div className="text-center">
                  <div className="text-3xl font-bold">{stats.totalSegments}</div>
                  <div className="text-sm text-muted-foreground mt-1">{t('totalSegments', '总段落数')}</div>
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="pt-6">
                <div className="text-center">
                  <div className="text-3xl font-bold">{stats.completedSegments}</div>
                  <div className="text-sm text-muted-foreground mt-1">{t('completedSegments', '已完成段落')}</div>
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="pt-6">
                <div className="text-center">
                  <div className="text-3xl font-bold">
                    {stats.totalSegments > 0
                      ? Math.round((stats.completedSegments / stats.totalSegments) * 100)
                      : 0}%
                  </div>
                  <div className="text-sm text-muted-foreground mt-1">{t('overallCompletion', '整体完成度')}</div>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}
