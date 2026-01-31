import React, { createContext, useContext, useState, useEffect } from 'react';
import { ZH_CN_LOCALE, EN_LOCALE } from '../constants';

interface I18nContextType {
  language: string;
  setLanguage: (lang: string) => void;
  t: (key: string, ...args: any[]) => string;
  availableLanguages: { code: string; label: string }[];
}

const I18nContext = createContext<I18nContextType | undefined>(undefined);

export const I18nProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  // Default to zh_CN as per request
  const [language, setLanguage] = useState('zh_CN');
  const [translations, setTranslations] = useState<Record<string, string>>(ZH_CN_LOCALE);

  useEffect(() => {
    // In a real app, we might fetch the JSON file here.
    // For now, switch between the embedded constants.
    if (language === 'zh_CN') {
      setTranslations(ZH_CN_LOCALE);
    } else if (language === 'en') {
      setTranslations(EN_LOCALE);
    } else {
      setTranslations(ZH_CN_LOCALE);
    }
  }, [language]);

  const t = (key: string, ...args: any[]): string => {
    let text = translations[key] || key;
    
    // Simple placeholder replacement {}
    if (args.length > 0) {
      args.forEach((arg, index) => {
        // Replace {} or {0}, {1} etc if implemented, but simple {} for now
        text = text.replace('{}', String(arg)); 
      });
    }
    return text;
  };

  const availableLanguages = [
    { code: 'zh_CN', label: '简体中文' },
    { code: 'en', label: 'English' }
  ];

  return (
    <I18nContext.Provider value={{ language, setLanguage, t, availableLanguages }}>
      {children}
    </I18nContext.Provider>
  );
};

export const useI18n = () => {
  const context = useContext(I18nContext);
  if (!context) {
    throw new Error('useI18n must be used within an I18nProvider');
  }
  return context;
};