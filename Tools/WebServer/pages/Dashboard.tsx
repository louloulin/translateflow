import React, { useEffect, useState } from 'react';
import { Play, Settings, FileOutput, ArrowRight, FileText, Folder, AlertCircle, PlayCircle } from 'lucide-react';
import { useI18n } from '@/contexts/I18nContext';
import { useGlobal } from '@/contexts/GlobalContext';
import { DataService } from '@/services/DataService';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Progress } from '@/components/ui/progress';
import { cn } from '@/lib/utils';

export const Dashboard: React.FC = () => {
  const { t } = useI18n();
  const { version, config, setTaskState, activeTheme } = useGlobal();
  const [recentProjects, setRecentProjects] = useState<any[]>([]);
  const [breakpointStatus, setBreakpointStatus] = useState<{
    can_resume: boolean;
    has_incomplete: boolean;
    project_name?: string;
    progress?: number;
    total_line?: number;
    completed_line?: number;
    message: string;
  } | null>(null);

  const elysiaActive = activeTheme === 'elysia';

  const getCharacterBlessing = () => {
    switch(activeTheme) {
      case 'elysia': return "嗨~ 想我了吗？无论结果如何，努力的你才是最美的哦，快让我看看你的成果吧~";
      case 'eden': return "欢迎来到这片黄金的港湾。在这里，文字不只是符号，它们是流淌的乐章，是永不褪色的艺术。愿这些杰作因你而生.";
      case 'mobius': return "哦？这就是你选择的‘进化’之路吗？很有趣。来吧，让我看看你会如何重塑这些平庸的文字……哪怕是失败，也是通往无限的基石.";
      case 'pardofelis': return "哎呀，大老板你来啦！罐头，快打个招呼~ 既然来了就别急着走嘛，咱家这儿多得是好宝贝，一定能帮你把活儿干得漂漂亮亮的！";
      case 'griseo': return "你在看这幅画吗？我正在为它填色。这些文字……它们有着很温柔的颜色。请坐下，和我一起慢慢描绘它们吧.";
      case 'kevin': return "无论前方的道路多么严寒，拯救的使命永远不会熄灭。既然背负了这份沉重，就请拼尽全力，将这些文字转化为对抗‘终焉’的力量.";
      case 'kalpas': return "哈！你还在磨蹭什么？破坏！或者创造！只要能点燃我的怒火，怎样都好！滚去工作，用这些文字撕碎所有的无趣！";
      case 'aponia': return "我已预见到了终局……但在那之前，请允许我为你祈祷。愿这些文字不再沉重，愿你的心不再迷茫。";
      case 'villv': return "这是天才的杰作，还是疯子的妄想？没关系，在我的舞台上，所有文字都将服从逻辑的戏法。让我们开始这场华丽的变革吧！";
      case 'su': return "在这一叶一世界中，文字的流动亦是因果的循环。请静下心来，感受那些隐藏在字里行间的真实。";
      case 'sakura': return "瞬身之意，止于须臾。这些文字如落樱般轻盈，却也承载着斩断过去的觉悟。请珍惜它们。";
      case 'kosma': return "黑夜终会吞噬一切……但在光亮消失前，我守在这里。请继续你的工作，我会挡住那些阴影。";
      case 'hua': return "武道与文道，皆在于精诚。每一份对文字的雕琢，都是对自我的磨砺。请务必保持这份专注。";
      case 'herrscher_of_human': return "欢迎来到这永恒的奇迹。在这里，每一个字都是爱的证明，每一段旅程都是光的回响。作为‘人之律者’，我将守护你笔下所有的美好。";
      default: return null;
    }
  };

  const getCharacterGreeting = () => {
    switch(activeTheme) {
      case 'elysia': return "嗨~ 想我了吗？";
      case 'eden': return "欢迎回来，我的挚友。";
      case 'mobius': return "实验又要开始了。";
      case 'pardofelis': return "欢迎光临，大老板！";
      case 'griseo': return "你来了……";
      case 'kevin': return "欢迎回来。";
      case 'kalpas': return "哼，你终于滚回来了！";
      case 'aponia': return "愿你能得到救赎。";
      case 'villv': return "欢迎来到魔术表演现场！";
      case 'su': return "心如止水，方见真意。";
      case 'sakura': return "樱花散落之时，亦是归家之日。";
      case 'kosma': return "……你，不该靠近这里。";
      case 'hua': return "寸心拳致，不负此生。";
      case 'herrscher_of_human': return "我是一切，也是始终。";
      default: return null;
    }
  };

  const characterGreeting = getCharacterGreeting();
  const characterQuote = getCharacterBlessing();
  
  useEffect(() => {
    if (config) {
        setRecentProjects([...(config.recent_projects || [])]);
    }
  }, [config]);

  useEffect(() => {
    const checkBreakpoint = async () => {
      try {
        const status = await DataService.getBreakpointStatus();
        setBreakpointStatus(status);
      } catch (error) {
        console.error("Failed to check breakpoint status:", error);
      }
    };
    checkBreakpoint();
  }, []);

  const handleResumeBreakpoint = () => {
    setTaskState(prev => ({
      ...prev,
      isResuming: true,
    }));
    navigate('/task');
  };

  const navigate = (path: string) => {
    window.location.hash = path;
  };

  const handleResume = async (project: any) => {
      const path = typeof project === 'string' ? project : project.path;
      const profile = typeof project === 'object' ? project.profile : null;
      const rulesProfile = typeof project === 'object' ? project.rules_profile : null;

      try {
          if (profile && profile !== config?.active_profile) {
              await DataService.switchProfile(profile);
          }
          if (rulesProfile && rulesProfile !== config?.active_rules_profile) {
              await DataService.switchRulesProfile(rulesProfile);
          }

          setTaskState(prev => ({
              ...prev, 
              customInputPath: path,
              isResuming: true,
          }));

          navigate('/task');
      } catch (error) {
          console.error("Failed to resume project with specific profiles", error);
          setTaskState(prev => ({ ...prev, customInputPath: path, isResuming: true }));
          navigate('/task');
      }
  };

  const getProjectInfo = (path: string) => {
      const normalized = path.replace(/\\/g, '/');
      const parts = normalized.split('/');
      const name = parts.pop() || path;
      
      let type = "FOLDER";
      let icon = <Folder size={16} className="text-blue-400" />;
      
      if (name.includes('.')) {
          const ext = name.split('.').pop()?.toUpperCase();
          type = ext || "FILE";
          icon = <FileText size={16} className="text-slate-400" />;
      }

      return { name, type, icon, fullPath: path };
  };

  return (
    <div className="space-y-6 md:space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
      {/* Breakpoint Alert */}
      {breakpointStatus && breakpointStatus.has_incomplete && (
        <Alert className={cn(
          "border-l-4", 
          elysiaActive ? "border-l-pink-500 bg-pink-500/5" : "border-l-amber-500 bg-amber-500/5"
        )}>
          <AlertCircle className={cn("h-4 w-4", elysiaActive ? "text-pink-500" : "text-amber-500")} />
          <AlertTitle className={cn(elysiaActive ? "text-pink-500" : "text-amber-500")}>
            检测到未完成的翻译任务
          </AlertTitle>
          <AlertDescription className="mt-2">
            <div className="flex flex-col gap-2">
              <span className="text-muted-foreground text-xs">
                {breakpointStatus.project_name} - {breakpointStatus.completed_line}/{breakpointStatus.total_line} 行 ({breakpointStatus.progress?.toFixed(1)}%)
              </span>
              <div className="flex items-center gap-4 w-full">
                <Progress value={breakpointStatus.progress || 0} className="h-2 flex-1" />
                <Button size="sm" onClick={handleResumeBreakpoint} className={cn(elysiaActive && "bg-pink-500 hover:bg-pink-600")}>
                  继续翻译
                </Button>
              </div>
            </div>
          </AlertDescription>
        </Alert>
      )}

      {/* Header */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-end gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">
            {characterGreeting || t('ui_dashboard_welcome')}
          </h1>
          <p className="text-muted-foreground mt-2 max-w-xl">
            {characterQuote || t('ui_dashboard_subtitle')}
          </p>
        </div>
        <div className="flex gap-2">
           <Badge variant="outline" className={cn(
             "transition-all duration-500",
             activeTheme === 'herrscher_of_human' 
               ? 'bg-pink-400/20 text-pink-500 border-pink-400/40' 
               : (elysiaActive ? 'bg-pink-500/10 text-pink-400 border-pink-500/30' : '')
           )}>
             {activeTheme === 'herrscher_of_human' ? '人之律者 · 爱与希望' : (elysiaActive ? '完美无瑕' : t('ui_system_online'))}
           </Badge>
           <Badge variant="secondary" className="font-mono">
             {activeTheme === 'herrscher_of_human' ? `∞ ${version}` : version}
           </Badge>
        </div>
      </div>

      {/* Action Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-6">
        <Card 
            className="cursor-pointer hover:shadow-lg transition-all hover:border-primary/50 group relative overflow-hidden"
            onClick={() => navigate('/task')}
        >
          <div className="absolute top-0 right-0 p-4 opacity-5 group-hover:opacity-10 transition-opacity">
            <Play size={100} />
          </div>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
                <PlayCircle className="text-primary" />
                {t('menu_start_translation')}
            </CardTitle>
            <CardDescription>{t('ui_new_task_desc')}</CardDescription>
          </CardHeader>
          <CardContent>
            {elysiaActive && (
              <Badge className="absolute top-4 right-4 bg-pink-500 animate-pulse">MAGIC</Badge>
            )}
          </CardContent>
          <CardFooter>
            <Button variant="ghost" className="p-0 text-primary hover:text-primary hover:bg-transparent group-hover:translate-x-1 transition-transform">
                {t('ui_btn_start')} <ArrowRight className="ml-2 h-4 w-4" />
            </Button>
          </CardFooter>
        </Card>

        <Card 
            className="cursor-pointer hover:shadow-lg transition-all hover:border-primary/50 group relative overflow-hidden"
            onClick={() => navigate('/settings')}
        >
          <div className="absolute top-0 right-0 p-4 opacity-5 group-hover:opacity-10 transition-opacity">
            <Settings size={100} />
          </div>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
                <Settings className="text-primary" />
                {t('menu_settings')}
            </CardTitle>
            <CardDescription>{t('ui_config_desc')}</CardDescription>
          </CardHeader>
          <CardFooter>
            <Button variant="ghost" className="p-0 text-primary hover:text-primary hover:bg-transparent group-hover:translate-x-1 transition-transform">
                {t('ui_btn_edit')} <ArrowRight className="ml-2 h-4 w-4" />
            </Button>
          </CardFooter>
        </Card>

        <Card 
            className="cursor-pointer hover:shadow-lg transition-all hover:border-primary/50 group relative overflow-hidden"
            onClick={() => navigate('/export')}
        >
          <div className="absolute top-0 right-0 p-4 opacity-5 group-hover:opacity-10 transition-opacity">
            <FileOutput size={100} />
          </div>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
                <FileOutput className="text-primary" />
                {t('menu_export_only')}
            </CardTitle>
            <CardDescription>{t('ui_history_desc')}</CardDescription>
          </CardHeader>
          <CardFooter>
            <Button variant="ghost" className="p-0 text-primary hover:text-primary hover:bg-transparent group-hover:translate-x-1 transition-transform">
                {t('ui_btn_history')} <ArrowRight className="ml-2 h-4 w-4" />
            </Button>
          </CardFooter>
        </Card>
      </div>

      {/* Recent Projects */}
      <Card>
        <CardHeader>
          <CardTitle>{t('menu_recent_projects')}</CardTitle>
        </CardHeader>
        <CardContent>
            {!config ? (
                <div className="text-muted-foreground text-sm animate-pulse py-4">Loading configuration...</div>
            ) : recentProjects.length === 0 ? (
                <div className="text-muted-foreground text-sm italic py-4">No recent projects found.</div>
            ) : (
                <Table>
                    <TableHeader>
                        <TableRow>
                            <TableHead>{t('ui_recent_proj_header')}</TableHead>
                            <TableHead>{t('ui_recent_type')}</TableHead>
                            <TableHead className="hidden md:table-cell">{t('label_input')}</TableHead>
                            <TableHead className="text-right">{t('ui_recent_action')}</TableHead>
                        </TableRow>
                    </TableHeader>
                    <TableBody>
                        {recentProjects.map((project, i) => {
                            const path = typeof project === 'string' ? project : project.path;
                            const info = getProjectInfo(path);
                            const profileStr = typeof project === 'object' ? `${project.profile} / ${project.rules_profile}` : 'legacy';
        
                            return (
                                <TableRow key={i} className="group">
                                    <TableCell className="font-medium flex items-center gap-3">
                                        {info.icon}
                                        <div className="flex flex-col">
                                            <span>{info.name}</span>
                                            <span className="text-[10px] text-muted-foreground md:hidden">{profileStr}</span>
                                        </div>
                                    </TableCell>
                                    <TableCell>
                                        <div className="flex flex-col gap-1">
                                            <Badge variant="secondary" className="w-fit text-[10px]">{info.type}</Badge>
                                            <span className="text-[10px] text-muted-foreground hidden md:block">{profileStr}</span>
                                        </div>
                                    </TableCell>
                                    <TableCell className="text-muted-foreground text-xs font-mono hidden md:table-cell truncate max-w-[200px]" title={info.fullPath}>
                                        {info.fullPath}
                                    </TableCell>
                                    <TableCell className="text-right">
                                        <Button 
                                            variant="outline" 
                                            size="sm" 
                                            onClick={() => handleResume(project)}
                                            className="h-7 text-xs"
                                        >
                                            {t('ui_resume')}
                                        </Button>
                                    </TableCell>
                                </TableRow>
                            );
                        })}
                    </TableBody>
                </Table>
            )}
        </CardContent>
      </Card>
    </div>
  );
};
