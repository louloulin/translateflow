import React from 'react';
import { I18nProvider } from '@/contexts/I18nContext';
import { GlobalProvider } from '@/contexts/GlobalContext';
import { MainLayout } from '@/components/Layout/MainLayout';
import './index.css';

const App: React.FC = () => {
  return (
    <I18nProvider>
      <GlobalProvider>
        <MainLayout />
      </GlobalProvider>
    </I18nProvider>
  );
}

export default App;
