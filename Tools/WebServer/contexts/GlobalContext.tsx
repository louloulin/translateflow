import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { AppConfig, LogEntry, TaskStats, ChartDataPoint, TaskType, ThemeType, UiPreferences } from '../types';
import { DEFAULT_CONFIG } from '../constants';
import { DataService } from '../services/DataService';
import { clearUiPreferences, getDefaultUiPreferences, loadUiPreferences, normalizeUiPreferences, saveUiPreferences } from '@/lib/uiPreferences';

// Define the shape of the Task Runner's persistent state
interface TaskRunnerState {
  logs: LogEntry[];
  stats: TaskStats;
  chartData: ChartDataPoint[];
  isRunning: boolean;
  taskType: TaskType;
  customInputPath: string;
  isResuming: boolean;
  comparison?: {
    source: string;
    translation: string;
  };
}

const DEFAULT_TASK_STATE: TaskRunnerState = {
  logs: [],
  stats: {
    rpm: 0,
    tpm: 0,
    totalProgress: 0,
    completedProgress: 0,
    totalTokens: 0,
    elapsedTime: 0,
    status: 'idle',
    currentFile: 'Waiting for task...'
  },
  chartData: [],
  isRunning: false,
  taskType: TaskType.TRANSLATE,
  customInputPath: '',
  isResuming: false,
  comparison: undefined // Set to undefined to match optional interface
};

interface GlobalContextType {
  // System Info
  version: string;
  setVersion: (v: string) => void;

  // Theme State
  activeTheme: ThemeType;
  setActiveTheme: (theme: ThemeType) => void;
  unlockedThemes: ThemeType[];
  unlockTheme: (theme: ThemeType) => void;
  unlockThemeWithNotification: (theme: ThemeType) => void; // New persistent unlock with modal
  notification: ThemeType | null;
  setNotification: (theme: ThemeType | null) => void;
  elysiaActive: boolean; 
  rippleData: { active: boolean, x: number, y: number, type: 'in' | 'out', targetTheme?: ThemeType };
  triggerRipple: (x: number, y: number, targetTheme?: ThemeType) => void;

  // Config
  config: AppConfig | null;
  setConfig: (c: AppConfig | null) => void;
  refreshConfig: () => Promise<void>;
  profiles: string[];
  rulesProfiles: string[];

  // Task Runner State
  taskState: TaskRunnerState;
  setTaskState: (state: TaskRunnerState | ((prev: TaskRunnerState) => TaskRunnerState)) => void;

  // Helper to clear task state (optional, if needed manually)
  resetTaskState: () => void;

  // UI Preferences
  uiPrefs: UiPreferences;
  setUiPrefs: (next: UiPreferences | ((prev: UiPreferences) => UiPreferences)) => void;
  resetUiPrefs: () => void;
}

const GlobalContext = createContext<GlobalContextType | undefined>(undefined);

export const GlobalProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [version, setVersion] = useState<string>("Loading...");
  const [config, setConfigState] = useState<AppConfig | null>(null);
  const [profiles, setProfiles] = useState<string[]>([]);
  const [rulesProfiles, setRulesProfiles] = useState<string[]>([]);

  // Theme & Transition
  const [activeTheme, setActiveThemeState] = useState<ThemeType>('default');
  const [notification, setNotification] = useState<ThemeType | null>(null);

  const [unlockedThemes, setUnlockedThemes] = useState<ThemeType[]>(['default']);

  const [uiPrefs, setUiPrefsState] = useState<UiPreferences>(() => {
    if (typeof window === 'undefined') return getDefaultUiPreferences();
    return loadUiPreferences();
  });

  // Update unlockedThemes and activeTheme when config is loaded
  useEffect(() => {
    if (config?.unlocked_themes) {
        setUnlockedThemes(config.unlocked_themes as ThemeType[]);

        // Auto-unlock Herrscher of Human if all 13 Flame-Chasers are unlocked
        const flameChasers: ThemeType[] = ['elysia', 'eden', 'mobius', 'pardofelis', 'griseo', 'kevin', 'kalpas', 'aponia', 'villv', 'su', 'sakura', 'kosma', 'hua'];
        const allUnlocked = flameChasers.every(t => config.unlocked_themes?.includes(t));

        if (allUnlocked && !config.unlocked_themes.includes('herrscher_of_human')) {
            unlockThemeWithNotification('herrscher_of_human');
        }
    }
    // Load active theme from config (server-side), fallback to localStorage for backwards compatibility
    if (config?.active_theme) {
        setActiveThemeState(config.active_theme as ThemeType);
    } else {
        const localTheme = localStorage.getItem('active_theme') as ThemeType;
        if (localTheme) {
            setActiveThemeState(localTheme);
        }
    }
  }, [config?.unlocked_themes, config?.active_theme]);

  const elysiaActive = activeTheme === 'elysia';

  const [rippleData, setRippleData] = useState<{ active: boolean, x: number, y: number, type: 'in' | 'out', targetTheme?: ThemeType }>({ active: false, x: 0, y: 0, type: 'out' });

  const setActiveTheme = async (theme: ThemeType) => {
    setActiveThemeState(theme);
    localStorage.setItem('active_theme', theme);
    // Also save to server-side config for persistence across port changes
    if (config) {
      const updatedConfig = { ...config, active_theme: theme };
      setConfigState(updatedConfig);
      try {
        await DataService.saveConfig(updatedConfig);
      } catch (e) {
        console.error("Failed to persist active theme to config", e);
      }
    }
  };

  const unlockTheme = (theme: ThemeType) => {
    setUnlockedThemes(prev => {
      if (prev.includes(theme)) return prev;
      return [...prev, theme];
    });
  };

  const unlockThemeWithNotification = async (theme: ThemeType) => {
    // 1. Check if already unlocked
    const alreadyUnlocked = config?.unlocked_themes?.includes(theme);
    if (alreadyUnlocked) return;

    // 2. Add to config and save to server
    if (config) {
        const newUnlocked = [...(config.unlocked_themes || ['default']), theme];
        const updatedConfig = { ...config, unlocked_themes: newUnlocked };
        setConfigState(updatedConfig);
        
        try {
            await DataService.saveConfig(updatedConfig);
            // 3. Show notification
            setNotification(theme);
            // 4. Update local state
            setUnlockedThemes(newUnlocked as ThemeType[]);
        } catch (e) {
            console.error("Failed to persist unlock to config", e);
        }
    }
  };

  const triggerRipple = (x: number, y: number, targetTheme?: ThemeType) => {
    const currentIsDefault = activeTheme === 'default';
    const isClosing = targetTheme === 'default' || (targetTheme === undefined && !currentIsDefault);
    const newType = isClosing ? 'in' : 'out';

    setRippleData({ active: true, x, y, type: newType, targetTheme });

    setTimeout(() => {
        const next = targetTheme !== undefined ? targetTheme : (activeTheme === 'default' ? 'elysia' : 'default');
        setActiveTheme(next);
        if (next !== 'default') unlockTheme(next);
    }, 1500); // Increased from 1000ms for more buffer

    setTimeout(() => {
        setRippleData(prev => ({ ...prev, active: false }));
    }, 2500); // Increased from 2000ms to allow smooth fade out
  };

  // Initialize Task State
  const [taskState, setTaskState] = useState<TaskRunnerState>(DEFAULT_TASK_STATE);

  /**
   * Updates UI preferences and persists the result to localStorage.
   */
  const setUiPrefs = (next: UiPreferences | ((prev: UiPreferences) => UiPreferences)) => {
    setUiPrefsState(prev => {
      const computed = typeof next === 'function' ? (next as any)(prev) : next;
      const normalized = normalizeUiPreferences({
        ...computed,
        updatedAt: Date.now(),
      });
      saveUiPreferences(normalized);
      return normalized;
    });
  };

  /**
   * Resets UI preferences to defaults and clears persisted storage.
   */
  const resetUiPrefs = () => {
    clearUiPreferences();
    setUiPrefsState(getDefaultUiPreferences());
  };

  // Initial Data Fetch
  useEffect(() => {
    // Fetch Version
    DataService.getVersion()
      .then(data => setVersion(data.version))
      .catch(() => setVersion("Offline"));

    // Fetch Config
    refreshConfig();
  }, []);

  const refreshConfig = async () => {
    try {
      const data = await DataService.getConfig();
      setConfigState(data);

      // Fetch profiles
      const pList = await DataService.getProfiles();
      setProfiles(pList);
      const rList = await DataService.getRulesProfiles();
      setRulesProfiles(rList);

      // Also sync input path if not set yet
      setTaskState(prev => {
         if (!prev.customInputPath && data.label_input_path) {
             return { ...prev, customInputPath: data.label_input_path };
         }
         return prev;
      });
    } catch (e) {
      console.error("Global Context: Failed to load config", e);
    }
  };

  // Wrap setConfig to allow simpler updates from components
  const setConfig = (newConfig: AppConfig | null) => {
      setConfigState(newConfig);
      // In a real app, you might want to auto-save here or debounce save
  };

  useEffect(() => {
    setUiPrefsState(prev => normalizeUiPreferences(prev));
  }, []);

  // Apply Theme Mode (Light/Dark)
  useEffect(() => {
    const root = window.document.documentElement;
    root.classList.remove('light', 'dark');

    const mode = uiPrefs.themeMode;
    const systemTheme = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
    const effectiveTheme = mode === 'system' ? systemTheme : mode;

    root.classList.add(effectiveTheme);
  }, [uiPrefs.themeMode]);

  const resetTaskState = () => {
      setTaskState(DEFAULT_TASK_STATE);
  };

  return (
    <GlobalContext.Provider value={{
      version,
      setVersion,
      activeTheme,
      setActiveTheme,
      unlockedThemes,
      unlockTheme,
      unlockThemeWithNotification,
      notification,
      setNotification,
      elysiaActive,
      rippleData,
      triggerRipple,
      config,
      setConfig,
      refreshConfig,
      profiles,
      rulesProfiles,
      taskState,
      setTaskState,
      resetTaskState,
      uiPrefs,
      setUiPrefs,
      resetUiPrefs
    }}>
      {children}
    </GlobalContext.Provider>
  );
};
export const useGlobal = () => {
  const context = useContext(GlobalContext);
  if (!context) {
    throw new Error('useGlobal must be used within a GlobalProvider');
  }
  return context;
};
