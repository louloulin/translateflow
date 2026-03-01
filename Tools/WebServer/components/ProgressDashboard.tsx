import React, { useState, useEffect, useMemo } from 'react';
import { useI18n } from '@/contexts/I18nContext';
import { Project } from '@/types';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Button } from '@/components/ui/button';
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
  Minus,
  Download,
  FileJson,
  FileSpreadsheet,
  Type,
  Star,
  ThumbsUp,
  ThumbsDown,
  Gauge
} from 'lucide-react';
import { cn } from '@/lib/utils';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  PieChart as RechartsPieChart,
  Pie,
  Cell,
  Legend
} from 'recharts';

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
  totalWords: number;
  completedWords: number;
  pendingFiles: number;
  qualityScore: number;
  translationQuality: {
    excellent: number;
    good: number;
    needsReview: number;
  };
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
    let totalWords = 0;
    let completedWords = 0;
    let totalProgress = 0;
    let activeCount = 0;
    let completedCount = 0;
    let excellentCount = 0;
    let goodCount = 0;
    let needsReviewCount = 0;

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
          const completedSegs = Math.floor(estimatedSegments * (file.progress / 100));
          totalSegments += estimatedSegments;
          completedSegments += completedSegs;

          // Estimate words: ~5 chars per word, segments typically 50-200 chars
          const estimatedWords = Math.floor(estimatedSegments * 100 / 5); // ~100 chars per segment / 5
          const completedWordCount = Math.floor(estimatedWords * (file.progress / 100));
          totalWords += estimatedWords;
          completedWords += completedWordCount;

          // Quality estimation based on completion (mock quality metrics)
          if (file.progress >= 90) {
            excellentCount++;
          } else if (file.progress >= 50) {
            goodCount++;
          } else if (file.progress > 0) {
            needsReviewCount++;
          }
        });
      }

      totalProgress += project.progress || 0;
    });

    const avgProgress = projects.length > 0 ? totalProgress / projects.length : 0;
    // Quality score: weighted average based on completion levels
    const totalWithProgress = excellentCount + goodCount + needsReviewCount;
    const qualityScore = totalWithProgress > 0
      ? Math.round((excellentCount * 100 + goodCount * 70 + needsReviewCount * 40) / totalWithProgress)
      : 100;

    return {
      totalProjects: projects.length,
      activeProjects: activeCount,
      completedProjects: completedCount,
      totalFiles,
      completedFiles,
      inProgressFiles,
      averageProgress: Math.round(avgProgress),
      totalSegments,
      completedSegments,
      totalWords,
      completedWords,
      pendingFiles: totalFiles - completedFiles - inProgressFiles,
      qualityScore,
      translationQuality: {
        excellent: excellentCount,
        good: goodCount,
        needsReview: needsReviewCount
      }
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

  // Chart data for project progress
  const projectProgressData = useMemo(() => {
    return projects.slice(0, 6).map(p => ({
      name: p.name.length > 10 ? p.name.substring(0, 10) + '...' : p.name,
      progress: p.progress || 0,
      files: p.files?.length || 0
    }));
  }, [projects]);

  // Pie chart data for status distribution
  const statusPieData = useMemo(() => {
    return [
      { name: t('completed', '已完成'), value: stats.completedFiles, color: '#22c55e' },
      { name: t('inProgress', '进行中'), value: stats.inProgressFiles, color: '#3b82f6' },
      { name: t('pending', '待处理'), value: stats.pendingFiles, color: '#9ca3af' }
    ].filter(d => d.value > 0);
  }, [stats, t]);

  // Pie chart data for quality distribution
  const qualityPieData = useMemo(() => {
    return [
      { name: t('excellent', '优秀'), value: stats.translationQuality.excellent, color: '#22c55e' },
      { name: t('good', '良好'), value: stats.translationQuality.good, color: '#3b82f6' },
      { name: t('needsReview', '需审核'), value: stats.translationQuality.needsReview, color: '#f59e0b' }
    ].filter(d => d.value > 0);
  }, [stats, t]);

  // Export to JSON
  const exportToJSON = () => {
    const reportData = {
      generatedAt: new Date().toISOString(),
      summary: {
        totalProjects: stats.totalProjects,
        activeProjects: stats.activeProjects,
        completedProjects: stats.completedProjects,
        totalFiles: stats.totalFiles,
        completedFiles: stats.completedFiles,
        inProgressFiles: stats.inProgressFiles,
        totalWords: stats.totalWords,
        completedWords: stats.completedWords,
        totalSegments: stats.totalSegments,
        completedSegments: stats.completedSegments,
        averageProgress: stats.averageProgress,
        qualityScore: stats.qualityScore
      },
      projects: projects.map(p => ({
        id: p.id,
        name: p.name,
        status: p.status,
        progress: p.progress,
        sourceLang: p.sourceLang,
        targetLang: p.targetLang,
        files: p.files?.map(f => ({
          name: f.name,
          status: f.status,
          progress: f.progress,
          size: f.size
        })) || []
      }))
    };

    const blob = new Blob([JSON.stringify(reportData, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `translation-report-${new Date().toISOString().split('T')[0]}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  // Export to CSV
  const exportToCSV = () => {
    const headers = ['Project', 'Status', 'Progress', 'Files', 'Source', 'Target'];
    const rows = projects.map(p => [
      p.name,
      p.status,
      `${p.progress}%`,
      p.files?.length || 0,
      p.sourceLang,
      p.targetLang
    ]);

    const csvContent = [
      headers.join(','),
      ...rows.map(row => row.map(cell => `"${cell}"`).join(','))
    ].join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `translation-report-${new Date().toISOString().split('T')[0]}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  // Format number with K/M suffix
  const formatNumber = (num: number) => {
    if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M';
    if (num >= 1000) return (num / 1000).toFixed(1) + 'K';
    return num.toString();
  };

  return (
    <div className="space-y-6">
      {/* Export Buttons */}
      <div className="flex justify-end gap-2">
        <Button variant="outline" size="sm" onClick={exportToCSV}>
          <FileSpreadsheet className="h-4 w-4 mr-2" />
          {t('exportCSV', '导出CSV')}
        </Button>
        <Button variant="outline" size="sm" onClick={exportToJSON}>
          <FileJson className="h-4 w-4 mr-2" />
          {t('exportJSON', '导出JSON')}
        </Button>
      </div>

      {/* Stats Overview */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
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

        {/* Word Count */}
        <Card>
          <CardHeader className="pb-2">
            <CardDescription className="flex items-center gap-2">
              <Type className="h-4 w-4" />
              {t('totalWords', '总词数')}
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">{formatNumber(stats.totalWords)}</div>
            <div className="text-xs text-muted-foreground mt-1">
              {t('completed', '已完成')}: {formatNumber(stats.completedWords)} {t('words', '词')}
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

        {/* Quality Score */}
        <Card>
          <CardHeader className="pb-2">
            <CardDescription className="flex items-center gap-2">
              <Gauge className="h-4 w-4" />
              {t('qualityScore', '质量评分')}
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold flex items-center gap-2">
              {stats.qualityScore}%
              {stats.qualityScore >= 80 ? (
                <ThumbsUp className="h-5 w-5 text-green-500" />
              ) : stats.qualityScore >= 50 ? (
                <ThumbsUp className="h-5 w-5 text-blue-500" />
              ) : (
                <ThumbsDown className="h-5 w-5 text-amber-500" />
              )}
            </div>
            <div className="flex items-center gap-2 mt-1 text-xs text-muted-foreground">
              <span className="text-green-500 flex items-center gap-1">
                <Star className="h-3 w-3" />
                {stats.translationQuality.excellent} {t('excellent', '优秀')}
              </span>
              <span className="text-blue-500 flex items-center gap-1">
                <Activity className="h-3 w-3" />
                {stats.translationQuality.good} {t('good', '良好')}
              </span>
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
            {/* Progress by Project - Bar Chart */}
            <Card>
              <CardHeader>
                <CardTitle className="text-base">{t('progressByProject', '项目进度')}</CardTitle>
              </CardHeader>
              <CardContent>
                {projects.length === 0 ? (
                  <p className="text-muted-foreground text-sm">{t('noProjects', '暂无项目')}</p>
                ) : (
                  <div className="h-48">
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart data={projectProgressData} layout="vertical">
                        <XAxis type="number" domain={[0, 100]} tickFormatter={(v) => `${v}%`} />
                        <YAxis type="category" dataKey="name" width={80} tick={{ fontSize: 12 }} />
                        <Tooltip
                          formatter={(value: number) => [`${value}%`, t('progress', '进度')]}
                          contentStyle={{
                            backgroundColor: 'var(--card)',
                            border: '1px solid var(--border)',
                            borderRadius: '8px'
                          }}
                        />
                        <Bar dataKey="progress" fill="#3b82f6" radius={[0, 4, 4, 0]} />
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Status Distribution - Pie Chart */}
            <Card>
              <CardHeader>
                <CardTitle className="text-base">{t('fileStatus', '文件状态分布')}</CardTitle>
              </CardHeader>
              <CardContent>
                {statusPieData.length === 0 ? (
                  <p className="text-muted-foreground text-sm">{t('noFiles', '暂无文件')}</p>
                ) : (
                  <div className="h-48">
                    <ResponsiveContainer width="100%" height="100%">
                      <RechartsPieChart>
                        <Pie
                          data={statusPieData}
                          cx="50%"
                          cy="50%"
                          innerRadius={40}
                          outerRadius={70}
                          paddingAngle={2}
                          dataKey="value"
                          label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                          labelLine={false}
                        >
                          {statusPieData.map((entry, index) => (
                            <Cell key={`cell-${index}`} fill={entry.color} />
                          ))}
                        </Pie>
                        <Tooltip
                          contentStyle={{
                            backgroundColor: 'var(--card)',
                            border: '1px solid var(--border)',
                            borderRadius: '8px'
                          }}
                        />
                      </RechartsPieChart>
                    </ResponsiveContainer>
                  </div>
                )}
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
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Stats Grid */}
            <div className="grid grid-cols-2 gap-4">
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
                    <div className="text-3xl font-bold">{stats.totalWords.toLocaleString()}</div>
                    <div className="text-sm text-muted-foreground mt-1">{t('totalWords', '总词数')}</div>
                  </div>
                </CardContent>
              </Card>
              <Card>
                <CardContent className="pt-6">
                  <div className="text-center">
                    <div className="text-3xl font-bold">{stats.totalSegments.toLocaleString()}</div>
                    <div className="text-sm text-muted-foreground mt-1">{t('totalSegments', '总段落数')}</div>
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

            {/* Quality Distribution - Pie Chart */}
            <Card>
              <CardHeader>
                <CardTitle className="text-base">{t('qualityDistribution', '质量分布')}</CardTitle>
              </CardHeader>
              <CardContent>
                {qualityPieData.length === 0 ? (
                  <p className="text-muted-foreground text-sm">{t('noData', '暂无数据')}</p>
                ) : (
                  <div className="h-48">
                    <ResponsiveContainer width="100%" height="100%">
                      <RechartsPieChart>
                        <Pie
                          data={qualityPieData}
                          cx="50%"
                          cy="50%"
                          innerRadius={40}
                          outerRadius={70}
                          paddingAngle={2}
                          dataKey="value"
                          label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                          labelLine={false}
                        >
                          {qualityPieData.map((entry, index) => (
                            <Cell key={`cell-${index}`} fill={entry.color} />
                          ))}
                        </Pie>
                        <Tooltip
                          contentStyle={{
                            backgroundColor: 'var(--card)',
                            border: '1px solid var(--border)',
                            borderRadius: '8px'
                          }}
                        />
                      </RechartsPieChart>
                    </ResponsiveContainer>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}
