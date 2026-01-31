import React, { Suspense, lazy } from 'react';
import { useGlobal } from '../../contexts/GlobalContext';

// Lazy load all themes to reduce initial bundle size and memory usage
const ElysiaTheme = lazy(() => import('../ElysiaTheme').then(m => ({ default: m.ElysiaTheme })));
const EdenTheme = lazy(() => import('./EdenTheme').then(m => ({ default: m.EdenTheme })));
const MobiusTheme = lazy(() => import('./MobiusTheme').then(m => ({ default: m.MobiusTheme })));
const PardofelisTheme = lazy(() => import('./PardofelisTheme').then(m => ({ default: m.PardofelisTheme })));
const GriseoTheme = lazy(() => import('./GriseoTheme').then(m => ({ default: m.GriseoTheme })));
const KevinTheme = lazy(() => import('./KevinTheme').then(m => ({ default: m.KevinTheme })));
const KalpasTheme = lazy(() => import('./KalpasTheme').then(m => ({ default: m.KalpasTheme })));
const AponiaTheme = lazy(() => import('./AponiaTheme').then(m => ({ default: m.AponiaTheme })));
const VillVTheme = lazy(() => import('./VillVTheme').then(m => ({ default: m.VillVTheme })));
const SuTheme = lazy(() => import('./SuTheme').then(m => ({ default: m.SuTheme })));
const SakuraTheme = lazy(() => import('./SakuraTheme').then(m => ({ default: m.SakuraTheme })));
const KosmaTheme = lazy(() => import('./KosmaTheme').then(m => ({ default: m.KosmaTheme })));
const HuaTheme = lazy(() => import('./HuaTheme').then(m => ({ default: m.HuaTheme })));
const HerrscherOfHumanTheme = lazy(() => import('./HerrscherOfHumanTheme').then(m => ({ default: m.HerrscherOfHumanTheme })));

export const ThemeManager: React.FC = () => {
  const { activeTheme } = useGlobal();

  // Optimized Switch: Only mount the ACTIVE theme component.
  // This prevents background processing/animations of inactive themes.
  const renderActiveTheme = () => {
    switch (activeTheme) {
      case 'elysia': return <ElysiaTheme active={true} />;
      case 'eden': return <EdenTheme active={true} />;
      case 'mobius': return <MobiusTheme active={true} />;
      case 'pardofelis': return <PardofelisTheme active={true} />;
      case 'griseo': return <GriseoTheme active={true} />;
      case 'kevin': return <KevinTheme active={true} />;
      case 'kalpas': return <KalpasTheme active={true} />;
      case 'aponia': return <AponiaTheme active={true} />;
      case 'villv': return <VillVTheme active={true} />;
      case 'su': return <SuTheme active={true} />;
      case 'sakura': return <SakuraTheme active={true} />;
      case 'kosma': return <KosmaTheme active={true} />;
      case 'hua': return <HuaTheme active={true} />;
      case 'herrscher_of_human': return <HerrscherOfHumanTheme active={true} />;
      default: return null;
    }
  };

  return (
    <Suspense fallback={null}>
      {renderActiveTheme()}
    </Suspense>
  );
};