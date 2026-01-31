import React, { useEffect } from 'react';

export const AponiaTheme: React.FC<{ active: boolean }> = ({ active }) => {
  useEffect(() => {
    if (active) {
      document.documentElement.classList.add('aponia-mode');
      return () => document.documentElement.classList.remove('aponia-mode');
    }
  }, [active]);

  return (
    <>
      {active && (
        <div className="aponia-overlay">
          <div className="aponia-vignette"></div>
          <div className="aponia-glow-orb aponia-glow-1"></div>
          <div className="aponia-glow-orb aponia-glow-2"></div>
        </div>
      )}
      <style>{`
        :root.aponia-mode {
          --aponia-purple: #9d81ba;
          --aponia-blue: #5b7da1;
          --aponia-bg: #0b0c10;
        }
        .aponia-mode body { background-color: var(--aponia-bg) !important; color: #d1d1d1 !important; }
        .aponia-overlay { position: fixed; inset: 0; pointer-events: none; z-index: 9998; overflow: hidden; }
        .aponia-vignette { position: absolute; inset: 0; background: radial-gradient(circle, transparent 40%, rgba(157, 129, 186, 0.2) 100%); }
        .aponia-glow-orb { position: fixed; width: 60vw; height: 60vw; border-radius: 50%; filter: blur(120px); opacity: 0.15; z-index: -1; pointer-events: none; animation: aponia-float 25s ease-in-out infinite alternate; }
        .aponia-glow-1 { background: var(--aponia-purple); left: -10%; top: -10%; }
        .aponia-glow-2 { background: var(--aponia-blue); right: -10%; bottom: -10%; animation-delay: -5s; }
        @keyframes aponia-float { from { transform: translate(0, 0) scale(1); } to { transform: translate(5%, 10%) scale(1.2); } }
      `}</style>
    </>
  );
};
