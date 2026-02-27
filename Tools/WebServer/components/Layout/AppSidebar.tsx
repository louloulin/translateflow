import * as React from "react"
import { 
  LayoutDashboard, PlayCircle, Settings, Archive, Terminal, 
  BookOpen, Puzzle, ListPlus, Database, Clock, Sparkles, 
  Menu, X, Paintbrush, Wand2, FileText, Server
} from "lucide-react"
import { cn } from "@/lib/utils"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Separator } from "@/components/ui/separator"
import { Button } from "@/components/ui/button"
import { useI18n } from "@/contexts/I18nContext"
import { useGlobal } from "@/contexts/GlobalContext"

interface SidebarProps extends React.HTMLAttributes<HTMLDivElement> {
  className?: string
  activePath: string
  activeTheme: string
  onNavigate: (path: string) => void
  onThemeToggle: () => void
  isCollapsed?: boolean
}

interface NavItem {
  title: string
  icon: React.ElementType
  path: string
  labelKey: string
}

const navGroups: { title: string, items: NavItem[] }[] = [
  {
    title: "menu_group_quick_start",
    items: [
      { title: "Dashboard", icon: LayoutDashboard, path: "/", labelKey: "menu_title" },
      { title: "Start Translation", icon: PlayCircle, path: "/task", labelKey: "menu_start_translation" },
    ]
  },
  {
    title: "menu_group_task_config",
    items: [
      { title: "Settings", icon: Settings, path: "/settings", labelKey: "menu_settings" },
    ]
  },
  {
    title: "menu_group_advanced",
    items: [
      { title: "Plugins", icon: Puzzle, path: "/plugins", labelKey: "menu_plugin_settings" },
      { title: "Rules", icon: BookOpen, path: "/rules", labelKey: "menu_glossary_rules" },
      { title: "Prompts", icon: Sparkles, path: "/prompts", labelKey: "menu_prompt_features" },
    ]
  },
  {
    title: "menu_group_tools",
    items: [
      { title: "Text Extraction", icon: FileText, path: "/stev", labelKey: "menu_text_extraction" },
      { title: "Cache Editor", icon: Database, path: "/cache-editor", labelKey: "menu_cache_editor" },
      { title: "Task Queue", icon: ListPlus, path: "/queue", labelKey: "menu_task_queue" },
      { title: "Scheduler", icon: Clock, path: "/scheduler", labelKey: "menu_scheduler" },
      { title: "Server Control", icon: Server, path: "/server", labelKey: "menu_server_control" },
      { title: "Export", icon: Archive, path: "/export", labelKey: "menu_export_only" },
      { title: "Logs", icon: Terminal, path: "/logs", labelKey: "setting_session_logging" },
    ]
  }
]

export function AppSidebar({ className, activePath, activeTheme, onNavigate, onThemeToggle, isCollapsed }: SidebarProps) {
  const { t } = useI18n()
  const { uiPrefs } = useGlobal()
  const isElysia = activeTheme === 'elysia'
  const isCompact = uiPrefs.density === 'compact'

  return (
    <div className={cn("pb-12 h-full flex flex-col border-r bg-slate-900/95 backdrop-blur supports-[backdrop-filter]:bg-slate-900/60", className)}>
      <div className={cn("flex-1", isCompact ? "space-y-3 py-3" : "space-y-4 py-4")}>
        <div className="px-3 py-2">
          <div className="mb-2 px-4 flex items-center gap-2">
            <div className={cn(
              "h-8 w-8 rounded-lg bg-gradient-to-br from-primary to-primary/50 flex items-center justify-center shadow-lg shadow-primary/20",
              activeTheme === 'elysia' && "from-pink-500 to-pink-300 shadow-pink-500/20"
            )}>
              <span className="text-white font-bold font-mono">Ai</span>
            </div>
            {!isCollapsed && (
              <h2 className="text-lg font-semibold tracking-tight text-slate-100">
                AiNiee <span className={cn("text-primary text-xs ml-1", isElysia && "text-pink-400")}>{isElysia ? 'Elysia' : 'UI'}</span>
              </h2>
            )}
          </div>
          
          <ScrollArea className="h-[calc(100vh-10rem)] px-1">
            <div className={cn(isCompact ? "space-y-4 py-3" : "space-y-6 py-4")}>
              {navGroups.map((group, i) => (
                <div key={i} className={cn("px-3", isCompact ? "py-1.5" : "py-2")}>
                  {!isCollapsed && (
                    <h3 className="mb-2 px-2 text-xs font-semibold uppercase text-slate-500 tracking-wider">
                      {t(group.title) || group.title.replace('menu_group_', '').replace('_', ' ')}
                    </h3>
                  )}
                  <div className={cn(isCompact ? "space-y-0.5" : "space-y-1")}>
                    {group.items.map((item) => {
                      const isActive = activePath === item.path || (item.path === '/' && activePath === '')
                      return (
                        <Button
                          key={item.path}
                          variant={isActive ? "secondary" : "ghost"}
                          size={isCollapsed ? "icon" : "default"}
                          className={cn(
                            "w-full justify-start font-normal text-slate-400 hover:text-slate-100 hover:bg-slate-800",
                            isActive && "bg-slate-800 text-slate-100 font-medium",
                            isActive && isElysia && "bg-pink-500/10 text-pink-400 border border-pink-500/20 hover:bg-pink-500/20 hover:text-pink-300",
                            isCollapsed && "justify-center px-2",
                            isCompact && !isCollapsed && "h-8 px-3"
                          )}
                          onClick={() => onNavigate(item.path)}
                        >
                          <item.icon className={cn("h-4 w-4", !isCollapsed && "mr-2", isActive && "text-current")} />
                          {!isCollapsed && (t(item.labelKey) || item.title)}
                          {isActive && !isCollapsed && isElysia && (
                            <Sparkles className="ml-auto h-3 w-3 text-pink-400 animate-pulse" />
                          )}
                        </Button>
                      )
                    })}
                  </div>
                </div>
              ))}
            </div>
          </ScrollArea>
        </div>
      </div>
      
      <div className="px-3 py-2 border-t border-slate-800/50">
        <Button 
          variant="ghost" 
          className="w-full justify-start text-slate-400 hover:text-slate-100 hover:bg-slate-800"
          onClick={onThemeToggle}
        >
          <Paintbrush className={cn("h-4 w-4", !isCollapsed && "mr-2")} />
          {!isCollapsed && t("ui_theme_switch") || "Theme"}
        </Button>
      </div>
    </div>
  )
}
