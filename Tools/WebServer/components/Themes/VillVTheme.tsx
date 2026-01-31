import React, { useEffect } from 'react';

export const VillVTheme: React.FC<{ active: boolean }> = ({ active }) => {
  useEffect(() => {
    if (active) {
      document.documentElement.classList.add('villv-mode');
      return () => document.documentElement.classList.remove('villv-mode');
    }
  }, [active]);

  return (
    <>
      {active && (
        <div className="villv-overlay">
          <div className="villv-vignette"></div>
          <div className="villv-glow-orb villv-glow-1"></div>
          <div className="villv-glow-orb villv-glow-2"></div>
        </div>
      )}
      <style>{`
        :root.villv-mode {
          --villv-gold: #c5a059;
          --villv-brass: #845a33;
          --villv-bg: #12100e;
        }
        .villv-mode body { background-color: var(--villv-bg) !important; color: #e2d1b1 !important; }
        .villv-overlay { position: fixed; inset: 0; pointer-events: none; z-index: 9998; overflow: hidden; }
        .villv-vignette { position: absolute; inset: 0; background: radial-gradient(circle, transparent 30%, rgba(132, 90, 51, 0.3) 100%); }
        .villv-glow-orb { position: fixed; width: 50vw; height: 50vw; border-radius: 50%; filter: blur(110px); opacity: 0.2; z-index: -1; animation: villv-float 15s ease-in-out infinite alternate; }
        .villv-glow-1 { background: var(--villv-gold); left: -5%; top: -5%; }
        .villv-glow-2 { background: var(--villv-brass); right: -10%; bottom: -10%; }
        @keyframes villv-float { from { transform: rotate(0deg) translate(0, 0); } to { transform: rotate(5deg) translate(5%, 5%); } }
      `}</style>
    </>
  );
};
