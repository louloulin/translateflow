import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { DataService } from '../services/DataService';
import { AppConfig } from '../types';
import { useI18n } from './I18nContext';

interface AppContextType {
  version: string;
  recentProjects: string[];
  isLoadingProjects: boolean;
  config: AppConfig | null; // Full app config, potentially shared for other components
  loadConfig: () => Promise<void>; // Function to explicitly reload config
}

const AppContext = createContext<AppContextType | undefined>(undefined);

export const AppProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { setLanguage } = useI18n();

  const [version, setVersion] = useState<string>("Loading...");
  const [recentProjects, setRecentProjects] = useState<string[]>([]);
  const [isLoadingProjects, setIsLoadingProjects] = useState(true);
  const [config, setConfig] = useState<AppConfig | null>(null);

  const loadConfig = useCallback(async () => {
    setIsLoadingProjects(true);
    try {
      const fetchedConfig = await DataService.getConfig();
      setConfig(fetchedConfig);
      setRecentProjects([...(fetchedConfig.recent_projects || [])].reverse());
      if (fetchedConfig.interface_language) {
        setLanguage(fetchedConfig.interface_language);
      }
    } catch (e) {
      console.error("Failed to load config in AppContext", e);
      setConfig(null);
    } finally {
      setIsLoadingProjects(false);
    }
  }, [setLanguage]);

  useEffect(() => {
    // Fetch Version only once when the provider mounts
    DataService.getVersion()
      .then(data => setVersion(data.version))
      .catch(() => setVersion("Offline"));

    // Fetch config and recent projects when the provider mounts
    loadConfig();
  }, [loadConfig]); // Dependency on loadConfig to ensure it's stable

  return (
    <AppContext.Provider value={{
      version,
      recentProjects,
      isLoadingProjects,
      config,
      loadConfig
    }}>
      {children}
    </AppContext.Provider>
  );
};

export const useAppContext = () => {
  const context = useContext(AppContext);
  if (context === undefined) {
    throw new Error('useAppContext must be used within an AppProvider');
  }
  return context;
};
