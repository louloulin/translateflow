import React, { useEffect, useRef, useState } from 'react';
import { Terminal } from '../components/Terminal';
import { StatsPanel } from '../components/StatsPanel';
import { ResizableVerticalSplit } from '../components/ResizableVerticalSplit';
import { Play, Square, Upload, FileText, ChevronRight, ChevronDown, Terminal as TerminalIcon, Loader2, History, AlertCircle, Sparkles, ListPlus, X } from 'lucide-react';
import { DataService } from '../services/DataService';
import { TaskStats, LogEntry, TaskType, TaskPayload } from '../types';
import { useGlobal } from '../contexts/GlobalContext';
import { useI18n } from '../contexts/I18nContext';

export const TaskRunner: React.FC = () => {
  const { t } = useI18n();
  const { config, taskState, setTaskState, uiPrefs, setUiPrefs } = useGlobal(); // Use persistent global state
  
  const intervalRef = useRef<any>(null);

  const [splitRatio, setSplitRatio] = useState(uiPrefs.taskConsole.splitRatio);

  useEffect(() => {
    setSplitRatio(uiPrefs.taskConsole.splitRatio);
  }, [uiPrefs.taskConsole.splitRatio]);

  /**
   * Persists the task console split ratio to localStorage-backed UI preferences.
   */
  const commitSplitRatio = (nextRatio: number) => {
    setSplitRatio(nextRatio);
    setUiPrefs(prev => ({
      ...prev,
      taskConsole: {
        ...prev.taskConsole,
        splitRatio: nextRatio,
      },
      updatedAt: Date.now(),
    }));
  };
  
  // Upload State
  const [tempFiles, setTempFiles] = useState<{name: string, path: string, size: number}[]>([]);
  const [showTempFileList, setShowTempFileList] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [showUploadArea, setShowUploadArea] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // --- Helper Functions (Hoisted) ---

  const addLog = (msg: string, type: LogEntry['type'] = 'info') => {
    setTaskState(prev => ({
        ...prev,
        logs: [...prev.logs, {
            id: Date.now().toString(),
            timestamp: new Date().toLocaleTimeString(),
            message: msg,
            type
        }]
    }));
  };

  const setTaskType = (type: TaskType) => {
      setTaskState(prev => ({ ...prev, taskType: type }));
  };

  const setCustomInputPath = (path: string) => {
      setTaskState(prev => ({ ...prev, customInputPath: path }));
  };

  const loadTempFiles = async () => {
      try {
          const files = await DataService.listTempFiles();
          setTempFiles(files);
      } catch (e) {
          console.error("Failed to load temp files", e);
      }
  };

  // --- Event Handlers ---

  const processUpload = async (file: File) => {
      setIsUploading(true);
      try {
          // Attempt 1: Default Policy
          let result = await DataService.uploadFile(file, 'default');
          
          // Case 1: Limit Reached (10 files) -> Ask user
          if (result.status === 'limit_reached') {
              const confirmMsg = t('msg_upload_limit_reached')
                  .replace('{}', result.limit)
                  .replace('{}', result.oldest); // Reuse token
              
              if (confirm(confirmMsg)) {
                  // User chose to Delete (Overwrite)
                  result = await DataService.uploadFile(file, 'overwrite');
              } else {
                  // User chose Cancel (Keep old, use buffer)
                  result = await DataService.uploadFile(file, 'buffer');
              }
          }
          
          // Case 2: Forced Delete (12th file attempt)
          if (result.status === 'forced_delete') {
              const warnMsg = t('msg_upload_forced_delete')
                  .replace('{}', result.limit + 1)
                  .replace('{}', result.deleted);
              
              alert(warnMsg);
              // Backend already deleted oldest and saved new file in this request? 
              // Wait, my backend logic for 'forced_delete' returned early without saving!
              // I need to fix backend to save after deleting.
              // Assuming backend fixed:
              // actually backend logic: if count >= limit+1: delete, return status. 
              // It didn't save. Frontend needs to retry upload?
              // Let's re-read my backend code.
              
              // Backend Code: 
              // elif count >= limit + 1:
              //    try: os.remove(files[0][0]) ...
              //    return { "status": "forced_delete", ... }
              // It RETURNS before saving!
              
              // So Frontend must re-upload now that space is made.
              // Policy 'buffer' or 'default' should work now as count dropped.
              result = await DataService.uploadFile(file, 'default');
          }

          if (result.path) {
              addLog(`[SYSTEM] File uploaded: ${result.path}`, "system");
              await loadTempFiles();
              setCustomInputPath(result.path);
              setShowUploadArea(false);
          }
      } catch (error: any) {
          addLog(`[ERROR] Upload failed: ${error.message}`, "error");
      } finally {
          setIsUploading(false);
          if (fileInputRef.current) fileInputRef.current.value = '';
      }
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
      if (e.target.files && e.target.files[0]) {
          await processUpload(e.target.files[0]);
      }
  };

  const handleDragOver = (e: React.DragEvent) => {
      e.preventDefault();
      e.stopPropagation();
  };

  const handleDrop = async (e: React.DragEvent) => {
      e.preventDefault();
      e.stopPropagation();
      
      if (e.dataTransfer.files && e.dataTransfer.files[0]) {
          await processUpload(e.dataTransfer.files[0]);
      }
  };

  const startPolling = () => {
      stopPolling();
      intervalRef.current = setInterval(async () => {
          try {
              const data = await DataService.getTaskStatus();
              
              setTaskState(prev => {
                  try {
                      // Use backend-provided chart data
                      const stats = data.stats || prev.stats;
                      const newChartData = data.chart_data || prev.chartData;

                      // Map backend logs to LogEntry interface
                      const mappedLogs = (data.logs || []).map((l: any, idx: number) => {
                          if (!l) return null;
                          return {
                              id: l.id || `be-${idx}-${l.timestamp || Date.now()}`,
                              timestamp: typeof l.timestamp === 'number' 
                                  ? new Date(l.timestamp * 1000).toLocaleTimeString() 
                                  : (l.timestamp || new Date().toLocaleTimeString()),
                              message: String(l.message || ''),
                              type: l.type || 'info'
                          };
                      }).filter(Boolean) as LogEntry[];

                      // Update State
                      const newState = {
                          ...prev,
                          stats: stats,
                          logs: mappedLogs.length > 0 ? mappedLogs : prev.logs,
                          chartData: newChartData,
                          comparison: data.comparison ? { ...data.comparison } : prev.comparison
                      };
                      
                      // Check stop condition
                      if (stats.status === 'completed' || stats.status === 'error' || stats.status === 'idle') {
                          if (prev.isRunning) {
                              // Stop running locally if backend is done
                              stopPolling();
                              return { ...newState, isRunning: false };
                          }
                      }

                      return newState;
                  } catch (innerError) {
                      console.error("State update error", innerError);
                      return prev;
                  }
              });

          } catch (e) {
              console.error("Polling error", e);
          }
      }, 1000);
  };

  const stopPolling = () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
  };

  const handleStart = async (isAllInOne = false) => {
      if (!config || !config.target_platform) {
          addLog("[ERROR] Configuration not fully loaded or platform not selected.", "error");
          return;
      }
      if (!taskState.customInputPath) {
          addLog("[ERROR] Input path is required.", "error");
          return;
      }

      // Defensive access
      const targetPlatform = config.target_platform;
      const platformConfig = config.platforms ? config.platforms[targetPlatform] : undefined;
      const apiKey = platformConfig?.api_key || (config as any).api_key || undefined;

      // Prepare payload with explicit values (transmitting parameters correctly)
      const payload: TaskPayload = {
          task: taskState.taskType || TaskType.TRANSLATE,
          input_path: taskState.customInputPath,
          output_path: config.label_output_path || undefined, 
          source_lang: config.source_language || undefined,
          target_lang: config.target_language || undefined,
          project_type: config.translation_project || undefined,
          resume: !!taskState.isResuming,
          profile: config.active_profile || undefined,
          rules_profile: config.active_rules_profile || undefined,
          
          threads: Number(config.user_thread_counts || 0),
          retry: Number(config.retry_count || 0),
          timeout: Number(config.request_timeout || 60),
          rounds: Number(config.round_limit || 3),
          pre_lines: Number(config.pre_line_counts || 3),
          
          platform: targetPlatform,
          model: config.model || platformConfig?.model || '',
          api_key: apiKey,
          api_url: config.base_url || platformConfig?.api_url || undefined,
          
          failover: !!config.enable_api_failover,
          
          lines: !config.tokens_limit_switch ? Number(config.lines_limit || 20) : undefined,
          tokens: config.tokens_limit_switch ? Number(config.tokens_limit || 1500) : undefined,
          
          run_all_in_one: isAllInOne
      };

      // Reset Chart but keep input path
      setTaskState(prev => ({ 
          ...prev, 
          isRunning: true, 
          chartData: [],
          logs: [],
          stats: { 
              ...(prev.stats || {}), 
              status: 'running',
              completedProgress: 0 // Reset local progress display
          }
      }));
      
      addLog(`[SYSTEM] Starting ${isAllInOne ? 'ALL-IN-ONE' : payload.task.toUpperCase()} task...`, "system");

      try {
          await DataService.startTask(payload);
          startPolling();
      } catch (e: any) {
          setTaskState(prev => ({ ...prev, isRunning: false, stats: { ...prev.stats, status: 'error' } }));
          addLog(`[ERROR] Failed to start: ${e.message}`, "error");
      }
  };

  const handleStop = async () => {
      addLog("[SYSTEM] Sending STOP signal...", "warning");
      try {
          await DataService.stopTask();
          // We wait for polling to pick up the status change
      } catch (e: any) {
          addLog(`[ERROR] Failed to stop: ${e.message}`, "error");
      }
  };

  const generateCLIPreview = () => {
      if (!config) return "Loading config...";
      const parts = ['uv run ainiee_cli.py', taskState.taskType || 'translate', `"${taskState.customInputPath || ''}"`];
      
      // Flags
      if (taskState.isResuming) parts.push('-y --resume');
      else parts.push('-y');

      // Add Profile (Critical)
      if (config.active_profile) parts.push(`--profile "${config.active_profile}"`);
      if (config.active_rules_profile) parts.push(`--rules-profile "${config.active_rules_profile}"`);

      if (config.source_language) parts.push(`-s "${config.source_language}"`);
      if (config.target_language) parts.push(`-t "${config.target_language}"`);
      if (config.user_thread_counts) parts.push(`--threads ${config.user_thread_counts}`);
      if (config.target_platform) parts.push(`--platform "${config.target_platform}"`);
      return parts.join(' ');
  }

  // --- Effects ---

  // Initial Sync with logs if empty and config loaded
  useEffect(() => {
    if (config && taskState.logs.length === 0) {
        addLog(`[SYSTEM] Ready. Loaded profile: ${config.active_profile || 'default'}`, 'system');
    }
    loadTempFiles();

    // Check for breakpoint/resume status when config loads
    const checkBreakpoint = async () => {
        try {
            const breakpoint = await DataService.getBreakpointStatus();
            if (breakpoint.can_resume && breakpoint.has_incomplete && !taskState.isResuming) {
                // Found incomplete work - auto-enable resume option
                setTaskState(prev => ({ ...prev, isResuming: true }));
                addLog(`[SYSTEM] Detected incomplete translation: ${breakpoint.project_name} (${breakpoint.completed_line}/${breakpoint.total_line} lines, ${breakpoint.progress}%)`, 'info');
            }
        } catch (e) {
            console.error("Failed to check breakpoint status", e);
        }
    };
    if (config) {
        checkBreakpoint();
    }
  }, [config]);

  // Initial sync on mount to recover state after refresh
  useEffect(() => {
    const recoverState = async () => {
        try {
            const data = await DataService.getTaskStatus();
            setTaskState(prev => ({
                ...prev,
                isRunning: data.stats.status === 'running',
                stats: data.stats,
                chartData: data.chart_data || [],
                comparison: data.comparison || prev.comparison,
                logs: (data.logs || []).map((l: any, idx: number) => ({
                    id: l.id || `sync-${idx}`,
                    timestamp: typeof l.timestamp === 'number' ? new Date(l.timestamp * 1000).toLocaleTimeString() : l.timestamp,
                    message: l.message,
                    type: l.type || 'info'
                }))
            }));
            
            if (data.stats.status === 'running') {
                startPolling();
            }
        } catch (e) {
            console.error("Failed to recover state", e);
        }
    };
    recoverState();
  }, []);

  // Handle polling when task is running
  useEffect(() => {
    if (taskState.isRunning) {
        startPolling();
    }
    return () => stopPolling();
  }, [taskState.isRunning]);

  // --- Render ---

  const [activeTab, setActiveTab] = useState<'console' | 'comparison'>('console');

  return (
    <div className="space-y-3 h-[calc(100vh-140px)] flex flex-col">
      {/* Header Controls */}
      <div className="bg-card border border-border p-4 rounded-xl space-y-4 shadow-sm">
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
            <div className="flex items-center gap-4 w-full md:w-auto flex-1">
                <div className="w-12 h-12 bg-secondary rounded-lg flex items-center justify-center border border-border shrink-0">
                    <FileText size={24} className="text-muted-foreground" />
                </div>
                <div className="flex-1 min-w-[300px] space-y-2">
                    <div className="flex gap-2">
                        <button 
                            disabled={taskState.isRunning}
                            onClick={() => setTaskType(TaskType.TRANSLATE)} 
                            className={`text-xs px-3 py-1 rounded transition-colors ${taskState.taskType === TaskType.TRANSLATE ? 'bg-primary text-primary-foreground font-bold' : 'bg-secondary text-muted-foreground hover:text-foreground'}`}
                        >
                            {t('ui_task_translate')}
                        </button>
                        <button 
                            disabled={taskState.isRunning}
                            onClick={() => setTaskType(TaskType.POLISH)} 
                            className={`text-xs px-3 py-1 rounded transition-colors ${taskState.taskType === TaskType.POLISH ? 'bg-accent text-accent-foreground font-bold' : 'bg-secondary text-muted-foreground hover:text-foreground'}`}
                        >
                            {t('ui_task_polish')}
                        </button>
                        <button 
                            disabled={taskState.isRunning}
                            onClick={() => setTaskType(TaskType.EXPORT)} 
                            className={`text-xs px-3 py-1 rounded transition-colors ${taskState.taskType === TaskType.EXPORT ? 'bg-emerald-500 text-white font-bold' : 'bg-secondary text-muted-foreground hover:text-foreground'}`}
                        >
                            {t('ui_task_export')}
                        </button>
                    </div>
                    <div className="relative">
                         <input 
                            type="text" 
                            placeholder={t('prompt_input_path')} 
                            value={taskState.customInputPath}
                            onChange={(e) => setCustomInputPath(e.target.value)}
                            className="bg-transparent border-b border-border p-1 text-foreground font-semibold focus:ring-0 focus:border-primary placeholder:text-muted-foreground w-full outline-none transition-colors pr-8"
                        />
                         <div className="absolute right-0 top-0">
                            <button 
                                onClick={() => setShowTempFileList(!showTempFileList)}
                                className={`text-muted-foreground hover:text-foreground p-1 transition-transform ${showTempFileList ? 'rotate-180 text-primary' : ''}`}
                            >
                                <ChevronDown size={14} />
                            </button>
                             {showTempFileList && (
                                 <div className="absolute right-0 top-full mt-1 w-80 bg-popover border border-border rounded shadow-xl z-20 max-h-60 overflow-y-auto animate-in fade-in slide-in-from-top-2 duration-200">
                                     <div className="px-3 py-2 text-xs font-bold text-muted-foreground border-b border-border bg-muted flex justify-between items-center">
                                         <span>{t('ui_task_temp_uploaded')}</span>
                                         <button onClick={() => setShowTempFileList(false)} className="hover:text-foreground transition-colors"><X size={12} /></button>
                                     </div>
                                     {tempFiles.length === 0 ? (
                                         <div className="p-3 text-xs text-muted-foreground text-center italic">{t('msg_no_files_found')}</div>
                                     ) : (
                                         tempFiles.map((f, i) => (
                                             <div 
                                                key={i} 
                                                className="px-3 py-2 hover:bg-accent cursor-pointer text-xs text-foreground truncate border-b border-border/50 last:border-0"
                                                onClick={() => {
                                                    setCustomInputPath(f.path);
                                                    setShowTempFileList(false);
                                                }}
                                                title={f.path}
                                             >
                                                 {f.name} <span className="text-muted-foreground ml-1">({(f.size/1024).toFixed(1)} KB)</span>
                                             </div>
                                         ))
                                     )}
                                 </div>
                             )}
                         </div>
                    </div>
                    {/* Resume Switch */}
                    <div className="flex items-center gap-2">
                        <label className="flex items-center gap-2 cursor-pointer group">
                            <input 
                                type="checkbox" 
                                checked={taskState.isResuming}
                                onChange={(e) => setTaskState(prev => ({ ...prev, isResuming: e.target.checked }))}
                                className="w-4 h-4 rounded border-input text-primary focus:ring-primary bg-background"
                            />
                            <span className="text-xs text-muted-foreground group-hover:text-foreground transition-colors">{t('ui_resume')} / {t('option_resume')}</span>
                        </label>
                    </div>
                </div>
            </div>
            
            <div className="flex gap-3 w-full md:w-auto justify-end">
                 <button 
                    disabled={taskState.isRunning}
                    onClick={() => setShowUploadArea(!showUploadArea)} 
                    className={`flex items-center gap-2 px-6 py-2 rounded-lg font-bold transition-all border ${showUploadArea ? 'bg-blue-500 text-slate-900 border-blue-400' : 'bg-blue-500/10 text-blue-400 border-blue-500/50 hover:bg-blue-500/20'}`}
                >
                    <Upload size={18} /> {t('ui_task_upload')}
                </button>

                 {!taskState.isRunning ? (
                    <div className="flex gap-2">
                        <button 
                            onClick={() => handleStart(false)}
                            className="flex items-center gap-2 px-6 py-2 rounded-lg font-bold transition-all bg-accent/10 text-accent-foreground border border-accent/50 hover:bg-accent/20 hover:shadow-lg hover:shadow-accent/10"
                        >
                            <Play size={18} /> {t('ui_task_start')} {taskState.taskType.toUpperCase()}
                        </button>
                        
                        <button 
                            onClick={() => handleStart(true)}
                            className="flex items-center gap-2 px-4 py-2 rounded-lg font-bold transition-all bg-green-500/10 text-green-600 dark:text-green-400 border border-green-500/50 hover:bg-green-500/20 hover:shadow-lg"
                            title={t('menu_start_all_in_one')}
                        >
                            <Sparkles size={18} /> {t('menu_start_all_in_one')?.split('【')[0]}
                        </button>

                        <button 
                            onClick={() => window.location.hash = '/queue'}
                            className="flex items-center gap-2 px-4 py-2 rounded-lg font-bold transition-all bg-blue-500/10 text-blue-600 dark:text-blue-400 border border-blue-500/50 hover:bg-blue-500/20"
                            title={t('menu_task_queue')}
                        >
                            <ListPlus size={18} /> {t('ui_process_queue') || 'Queue'}
                        </button>
                    </div>
                ) : (
                    <button 
                        onClick={handleStop}
                        className="flex items-center gap-2 px-6 py-2 rounded-lg font-bold transition-all bg-red-500/10 text-red-600 dark:text-red-500 border border-red-500/50 hover:bg-red-500/20 hover:shadow-lg hover:shadow-red-500/10"
                    >
                        <Square size={18} fill="currentColor" /> {t('ui_task_stop')}
                    </button>
                )}
            </div>
        </div>

        {/* Upload Drag & Drop Area */}
        {showUploadArea && (
            <div 
                className={`border-2 border-dashed rounded-xl p-8 transition-all text-center cursor-pointer ${isUploading ? 'border-primary bg-primary/5' : 'border-border hover:border-foreground/50 hover:bg-accent/30'}`}
                onDragOver={handleDragOver}
                onDrop={handleDrop}
                onClick={() => fileInputRef.current?.click()}
            >
                <input 
                    type="file" 
                    ref={fileInputRef} 
                    className="hidden" 
                    onChange={handleFileUpload} 
                />
                <div className="flex flex-col items-center gap-3">
                    {isUploading ? (
                        <>
                             <Loader2 size={32} className="text-primary animate-spin" />
                             <p className="text-primary font-bold">{t('msg_uploading') || 'Uploading...'}</p>
                        </>
                    ) : (
                        <>
                            <div className="p-3 bg-secondary rounded-full text-muted-foreground">
                                <Upload size={24} />
                            </div>
                            <div>
                                <p className="text-foreground font-medium">{t('msg_drag_drop_title') || 'Drag & Drop files here, or click to browse'}</p>
                                <p className="text-muted-foreground text-sm mt-1">{t('msg_drag_drop_subtitle') || 'Files will be uploaded to project temp folder'}</p>
                            </div>
                        </>
                    )}
                </div>
            </div>
        )}
      </div>

      <div className="bg-muted border border-border rounded-lg p-3 font-mono text-xs text-muted-foreground flex items-start gap-3 overflow-x-auto whitespace-nowrap">
        <TerminalIcon size={14} className="mt-0.5 text-primary shrink-0" />
        <span className="text-muted-foreground select-none">$</span>
        <span className="text-primary">{generateCLIPreview()}</span>
      </div>

      {/* Tabs */}
      {config?.show_detailed_logs && (
        <div className="flex gap-2 border-b border-border px-2 mt-2">
          <button 
            onClick={() => setActiveTab('console')}
            className={`px-4 py-2 text-xs font-bold transition-all border-b-2 flex items-center gap-2 ${activeTab === 'console' ? 'border-primary text-primary' : 'border-transparent text-muted-foreground hover:text-foreground'}`}
          >
            <TerminalIcon size={14} />
            {t('ui_tab_console') || 'CONSOLE'}
          </button>
          <button 
            onClick={() => setActiveTab('comparison')}
            className={`px-4 py-2 text-xs font-bold transition-all border-b-2 flex items-center gap-2 ${activeTab === 'comparison' ? 'border-primary text-primary' : 'border-transparent text-muted-foreground hover:text-foreground'}`}
          >
            <FileText size={14} />
            {t('ui_tab_comparison') || 'COMPARISON'}
          </button>
        </div>
      )}

      {/* Content */}
      <div className="flex-1 min-h-0 flex flex-col relative space-y-4 pt-2">
        {(!config?.show_detailed_logs || activeTab === 'console') ? (
            <ResizableVerticalSplit
              ratio={splitRatio}
              onRatioCommit={commitSplitRatio}
              minTopPx={220}
              minBottomPx={uiPrefs.taskConsole.minTerminalPx}
              top={<StatsPanel data={taskState.chartData} stats={taskState.stats} />}
              bottom={<Terminal logs={taskState.logs} height="h-full" />}
            />
        ) : (
            <ResizableVerticalSplit
              ratio={splitRatio}
              onRatioCommit={commitSplitRatio}
              minTopPx={220}
              minBottomPx={uiPrefs.taskConsole.minTerminalPx}
              top={<StatsPanel data={taskState.chartData} stats={taskState.stats} variant="compact" />}
              bottom={(
                <div className="h-full min-h-0 overflow-y-auto">
                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 min-h-0">
                      {/* Source Pane */}
                      <div className="flex flex-col bg-card/40 border border-accent/20 rounded-xl overflow-hidden backdrop-blur-sm shadow-inner shadow-accent/5 min-h-[300px]">
                          <div className="px-4 py-2 bg-accent/10 border-b border-accent/20 flex justify-between items-center">
                              <span className="text-[10px] font-bold text-accent uppercase tracking-widest">{t('label_original_source')}</span>
                              <span className="text-[10px] text-muted-foreground font-mono">{(taskState.comparison?.source?.split('\n').length || 0)} {t('label_lines')}</span>
                          </div>
                          <div className="flex-1 p-4 overflow-y-auto font-mono text-sm text-foreground leading-relaxed scrollbar-thin scrollbar-thumb-accent/20 whitespace-pre-wrap">
                              {taskState.comparison?.source || <span className="text-muted-foreground italic">{t('msg_waiting_text')}</span>}
                          </div>
                      </div>

                      {/* Translation Pane */}
                      <div className="flex flex-col bg-card/40 border border-primary/20 rounded-xl overflow-hidden backdrop-blur-sm shadow-inner shadow-primary/5 min-h-[300px]">
                          <div className="px-4 py-2 bg-primary/10 border-b border-primary/20 flex justify-between items-center">
                              <span className="text-[10px] font-bold text-primary uppercase tracking-widest">{t('label_translation_output')}</span>
                              <span className="text-[10px] text-muted-foreground font-mono">{(taskState.comparison?.translation?.split('\n').length || 0)} {t('label_lines')}</span>
                          </div>
                          <div className="flex-1 p-4 overflow-y-auto font-mono text-sm text-primary-light leading-relaxed scrollbar-thin scrollbar-thumb-primary/20 whitespace-pre-wrap">
                              {taskState.comparison?.translation || <span className="text-muted-foreground italic animate-pulse">{t('msg_processing_batch')}</span>}
                          </div>
                      </div>
                  </div>
                </div>
              )}
            />
        )}

        {taskState.isRunning && (
            <div className="absolute top-4 right-4 flex items-center gap-2 bg-card/80 backdrop-blur px-3 py-1 rounded-full border border-primary/20 text-primary text-xs font-mono animate-pulse">
                <Loader2 size={12} className="animate-spin" />
                {t('msg_processing')}
            </div>
        )}
      </div>
    </div>
  );
};
