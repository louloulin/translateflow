import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useI18n } from '@/contexts/I18nContext';
import { useGlobal } from '@/contexts/GlobalContext';
import { ThemeManager } from '@/components/Themes/ThemeManager';
import { ElysiaGuide } from '@/components/ElysiaGuide';
import { AppSidebar } from './AppSidebar';
import { Sheet, SheetContent, SheetTrigger } from "@/components/ui/sheet";
import { Button } from "@/components/ui/button";
import { Menu, Sparkles, LayoutDashboard, CircleUser, LogOut, Settings as SettingsIcon, User } from "lucide-react";
import { cn } from "@/lib/utils";
import { Toaster } from "@/components/ui/toaster";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";

// Pages
import { Dashboard } from '@/pages/Dashboard';
import { Settings } from '@/pages/Settings';
import { Rules } from '@/pages/Rules';
import { Plugins } from '@/pages/Plugins';
import { TaskQueue } from '@/pages/TaskQueue';
import { TaskRunner } from '@/pages/TaskRunner';
import { Prompts } from '@/pages/Prompts';
import { Monitor } from '@/pages/Monitor';
import { CacheEditor } from '@/pages/CacheEditor';
import { Scheduler } from '@/pages/Scheduler';
import { StevExtraction } from '@/pages/StevExtraction';
import { Server } from '@/pages/Server';
import { DataService } from '@/services/DataService';
import { ProjectDetails } from '@/pages/ProjectDetails';
import { Editor } from '@/pages/Editor';
import { Teams } from '@/pages/Teams';
import { Login } from '@/pages/Login';
import { Profile } from '@/pages/Profile';
import { Subscription } from '@/pages/Subscription';
import { BilingualView } from '@/pages/BilingualView';
import { FileComparisonView } from '@/pages/FileComparisonView';
import { VersionHistoryView } from '@/pages/VersionHistoryView';
import { useAuth } from '@/contexts/AuthContext';

// Custom hook to track hash based location for navigation
const useLocation = () => {
  const [pathname, setPathname] = useState(window.location.hash.substring(1) || '/');

  useEffect(() => {
    const handleHashChange = () => {
      setPathname(window.location.hash.substring(1) || '/');
    };
    window.addEventListener('hashchange', handleHashChange);
    return () => window.removeEventListener('hashchange', handleHashChange);
  }, []);

  return { pathname };
};

export const MainLayout: React.FC = () => {
  const { pathname } = useLocation();
  const { t, language, setLanguage, availableLanguages } = useI18n();
  const { config, activeTheme, rippleData, triggerRipple, uiPrefs, setUiPrefs } = useGlobal();
  const { user, isAuthenticated, logout, isLoading } = useAuth();
  const [systemMode, setSystemMode] = useState<'full' | 'monitor' | 'loading'>('loading');
  const [isMobileOpen, setIsMobileOpen] = useState(false);
  const elysiaActive = activeTheme === 'elysia';

  // Toggle sidebar collapsed state
  const toggleSidebar = () => {
    setUiPrefs((prev: any) => ({
      ...prev,
      sidebarCollapsed: !prev.sidebarCollapsed,
      updatedAt: Date.now(),
    }));
  };

  // --- Theme Logic (Simplified for Layout) ---
  const handleNavigate = (path: string) => {
    window.location.hash = path;
    setIsMobileOpen(false);
  };

  const handleThemeToggle = () => {
      // Logic to toggle theme via ThemeManager is hidden in App.tsx originally
      // Here we might need to expose a method from GlobalContext or just rely on the ThemeDebugger/UI
      // For now, let's trigger the command palette or settings
      window.location.hash = '/settings';
  };

  // --- Initial System Check ---
  useEffect(() => {
    let mounted = true;
    DataService.getSystemMode()
      .then(res => {
        if (mounted) setSystemMode(res.mode || 'full');
      })
      .catch(() => {
        if (mounted) setSystemMode('full');
      });
    return () => { mounted = false; };
  }, []);

  // --- Auth Redirect ---
  // Redirect to login if not authenticated (except on auth pages)
  useEffect(() => {
    // isAuthPage is defined later, use pathname directly here
    const isAuth = pathname === '/login' || pathname === '/register';
    if (!isLoading && !isAuthenticated && !isAuth) {
      window.location.hash = '/login';
    }
  }, [isLoading, isAuthenticated, pathname]);

  // Sync language
  const isInitialLangSync = useRef(true);
  useEffect(() => {
    if (config?.interface_language && isInitialLangSync.current) {
        if (config.interface_language === 'zh_CN' && language !== 'zh_CN') {
            setLanguage('zh_CN');
        } else if (config.interface_language === 'en' && language !== 'en') {
            setLanguage('en');
        }
        isInitialLangSync.current = false;
    }
  }, [config?.interface_language, language, setLanguage]);


  // --- Content Rendering ---
  if (systemMode === 'loading') {
      return (
        <div className="h-screen bg-background flex items-center justify-center">
          <ThemeManager />
          <div className="flex flex-col items-center gap-4">
            <div className={cn("w-12 h-12 border-4 rounded-full animate-spin border-primary/20 border-t-primary", elysiaActive && "border-pink-500/20 border-t-pink-500 shadow-[0_0_15px_#ff8fa3]")}></div>
            <span className={cn("font-mono text-xs uppercase tracking-widest text-muted-foreground", elysiaActive && "text-pink-500 font-bold")}>
              {elysiaActive ? 'Connecting to Elysium...' : 'Initializing System...'}
            </span>
          </div>
        </div>
      );
  }

  const isMonitorMode = systemMode === 'monitor';
  const isMonitorPath = pathname === '/monitor';

  // Check if we should hide the sidebar (for auth pages)
  const isAuthPage = pathname === '/login' || pathname === '/register';

  let content;
  if (isMonitorMode && !isMonitorPath) {
      content = (
        <div className="flex flex-col items-center justify-center h-full p-4 space-y-6 text-center animate-in fade-in duration-500">
          <div className="w-24 h-24 rounded-full bg-red-500/10 flex items-center justify-center text-red-500">
             <LayoutDashboard size={48} />
          </div>
          <h1 className="text-2xl md:text-4xl font-black text-white uppercase tracking-tighter">监控模式下此页面不可用</h1>
          <p className="text-muted-foreground max-w-md">当前系统正处于独立监控模式，所有的交互功能已被禁用。请切换至监控面板查看实时任务进度。</p>
          <Button onClick={() => window.location.hash = '/monitor'} variant="default" size="lg">
            立即跳转至监控面板
          </Button>
        </div>
      );
  } else {
      switch(pathname) {
          case '/': case '': content = <Dashboard />; break;
          case '/task': content = <TaskRunner />; break;
          case '/cache-editor': content = <CacheEditor />; break;
          case '/prompts': content = <Prompts />; break;
          case '/rules': content = <Rules />; break;
          case '/plugins': content = <Plugins />; break;
          case '/queue': content = <TaskQueue />; break;
          case '/scheduler': content = <Scheduler />; break;
          case '/stev': content = <StevExtraction />; break;
          case '/server': content = <Server />; break;
          case '/login': content = <Login />; break;
          case '/register': content = <Login registerMode={true} />; break;
          case '/settings': content = <Settings />; break;
          case '/teams': content = <Teams />; break;
          case '/profile': content = <Profile />; break;
          case '/subscription': content = <Subscription />; break;
          case '/monitor': content = <Monitor />; break;
          case '/export': content = <div className="text-muted-foreground text-center mt-20">{t('menu_export_only')} (Placeholder)</div>; break;
          case '/logs': content = <div className="text-muted-foreground text-center mt-20">System Logs (Placeholder)</div>; break;
          default:
            // Simple router matching for projects
            if (pathname.startsWith('/editor/')) {
              const parts = pathname.split('/');
              const projectId = parts[2];
              const fileId = parts[3];
              content = <Editor projectId={projectId} fileId={fileId} />;
            } else if (pathname.startsWith('/bilingual/')) {
              const parts = pathname.split('/');
              const projectId = parts[2];
              const fileId = parts[3];
              content = <BilingualView projectId={projectId} fileId={fileId} />;
            } else if (pathname.startsWith('/comparison/')) {
              const parts = pathname.split('/');
              const projectId = parts[2];
              content = <FileComparisonView projectId={projectId} />;
            } else if (pathname.startsWith('/history/')) {
              const parts = pathname.split('/');
              const projectId = parts[2];
              const fileId = parts[3];
              content = <VersionHistoryView />;
            } else if (pathname.startsWith('/projects/')) {
              const projectId = pathname.split('/projects/')[1];
              content = <ProjectDetails projectId={projectId} />;
            } else {
              content = <Dashboard />;
            }
      }
  }

  if (isMonitorPath) {
      return (
        <div className="h-screen bg-background overflow-hidden selection:bg-primary/30 selection:text-white">
          <ThemeManager />
          {content}
        </div>
      );
  }

  return (
    <div className="flex h-screen overflow-hidden bg-background" data-density={uiPrefs.density} data-width={uiPrefs.contentWidthMode}>
      <ThemeManager />
      <ElysiaGuide />

      {/* Desktop Sidebar - Hide on auth pages */}
      {!isAuthPage && (
      <div className={cn(
        "hidden md:block h-full shrink-0 transition-all duration-300",
        uiPrefs.sidebarCollapsed ? "w-16" : "w-64"
      )}>
         <AppSidebar
            activePath={pathname}
            activeTheme={activeTheme}
            onNavigate={handleNavigate}
            onThemeToggle={handleThemeToggle}
            isCollapsed={uiPrefs.sidebarCollapsed}
            onToggleCollapse={toggleSidebar}
         />
      </div>
      )}

      {/* Mobile Sidebar - Hide on auth pages */}
      {!isAuthPage && (
      <Sheet open={isMobileOpen} onOpenChange={setIsMobileOpen}>
        <SheetContent side="left" className="p-0 w-72 bg-card border-r-border text-foreground">
             <AppSidebar
                activePath={pathname}
                activeTheme={activeTheme}
                onNavigate={handleNavigate}
                onThemeToggle={handleThemeToggle}
             />
        </SheetContent>
      </Sheet>
      )}

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col h-full overflow-hidden relative">
         {/* Mobile Header - Hide on auth pages */}
         {!isAuthPage && (
         <header className="md:hidden flex items-center h-14 px-4 border-b bg-card border-border">
            <Button variant="ghost" size="icon" onClick={() => setIsMobileOpen(true)} className="mr-2 text-muted-foreground">
                <Menu className="h-5 w-5" />
            </Button>
            <span className="font-semibold text-foreground">TranslateFlow</span>
         </header>
         )}

         {/* Desktop Header - User Info in Top Right */}
         {!isAuthPage && (
         <header className="hidden md:flex items-center justify-end h-14 px-4 border-b bg-card border-border">
            {isAuthenticated && user ? (
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button variant="ghost" className="flex items-center gap-2 px-2 h-auto py-1.5 hover:bg-accent">
                    {user.avatar_url ? (
                      <img
                        src={user.avatar_url}
                        alt={user.username}
                        className="h-8 w-8 rounded-full object-cover"
                      />
                    ) : (
                      <div className="h-8 w-8 rounded-full bg-primary/20 flex items-center justify-center">
                        <CircleUser className="h-4 w-4 text-primary" />
                      </div>
                    )}
                    <div className="flex flex-col items-start">
                      <span className="text-sm font-medium">{user.username}</span>
                      <span className="text-xs text-muted-foreground">{user.email}</span>
                    </div>
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end" className="w-56">
                  <DropdownMenuItem onClick={() => handleNavigate('/profile')}>
                    <User className="h-4 w-4 mr-2" />
                    {t('profile') || '个人资料'}
                  </DropdownMenuItem>
                  <DropdownMenuItem onClick={() => handleNavigate('/settings')}>
                    <SettingsIcon className="h-4 w-4 mr-2" />
                    {t('settings') || '设置'}
                  </DropdownMenuItem>
                  <DropdownMenuSeparator />
                  <DropdownMenuItem
                    onClick={logout}
                    className="text-red-600 focus:text-red-600 focus:bg-red-50"
                  >
                    <LogOut className="h-4 w-4 mr-2" />
                    {t('logout') || '退出登录'}
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            ) : (
              <div className="flex items-center gap-2">
                <Button variant="ghost" onClick={() => handleNavigate('/login')}>
                  {t('login') || '登录'}
                </Button>
                <Button onClick={() => handleNavigate('/register')}>
                  {t('register') || '注册'}
                </Button>
              </div>
            )}
         </header>
         )}

         {/* Main Content Scrollable */}
         <main className={cn(
           'flex-1 overflow-auto relative custom-scrollbar',
           uiPrefs.density === 'compact' ? 'p-3 md:p-6' : 'p-4 md:p-8'
         )}>
            {/* Ripple Effect */}
            {rippleData.active && (
                <div 
                    className={cn("fixed inset-0 z-[10000] pointer-events-none", rippleData.type === 'out' ? 'elysia-ripple-out' : 'elysia-ripple-in')}
                    style={{ '--ripple-x': `${rippleData.x}px`, '--ripple-y': `${rippleData.y}px` } as any}
                />
            )}
            
            {/* Background Decorations */}
            {elysiaActive && (
                <div className="fixed bottom-8 right-8 pointer-events-none opacity-20 z-0">
                    <Sparkles size={200} className="text-pink-300 animate-[spin_20s_linear_infinite]" />
                </div>
            )}

            <div className={cn(
              'mx-auto h-full w-full',
              uiPrefs.contentWidthMode === 'contained' ? 'max-w-7xl' : 'max-w-none'
            )}>
                {content}
            </div>
         </main>
      </div>
      <Toaster />
    </div>
  );
};
