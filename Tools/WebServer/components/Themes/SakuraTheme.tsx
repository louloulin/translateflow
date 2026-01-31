import React, { useEffect } from 'react';

export const SakuraTheme: React.FC<{ active: boolean }> = ({ active }) => {
  useEffect(() => {
    if (active) {
      document.documentElement.classList.add('sakura-mode');
      return () => document.documentElement.classList.remove('sakura-mode');
    }
  }, [active]);

  return (
    <>
      {active && (
        <div className="sakura-overlay">
          <div className="sakura-vignette"></div>
          <div className="sakura-glow-orb sakura-glow-1"></div>
          <div className="sakura-glow-orb sakura-glow-2"></div>
        </div>
      )}
      <style>{`
        :root.sakura-mode {
          --sakura-pink: #f4b0c7;
          --sakura-red: #e63946;
          --sakura-bg: #10080a;
        }
        .sakura-mode body { background-color: var(--sakura-bg) !important; color: #f8f0f2 !important; }
        .sakura-overlay { position: fixed; inset: 0; pointer-events: none; z-index: 9998; overflow: hidden; }
        .sakura-vignette { position: absolute; inset: 0; background: radial-gradient(circle, transparent 40%, rgba(244, 176, 199, 0.2) 100%); }
        .sakura-glow-orb { position: fixed; width: 55vw; height: 55vw; border-radius: 50%; filter: blur(120px); opacity: 0.18; z-index: -1; animation: sakura-float 20s ease-in-out infinite alternate; }
        .sakura-glow-1 { background: var(--sakura-pink); left: -5%; top: -10%; }
        .sakura-glow-2 { background: var(--sakura-red); right: -15%; bottom: -15%; }
        @keyframes sakura-float { from { transform: translate(0,0); } to { transform: translate(5%, 5%); } }
      `}</style>
    </>
  );
};
