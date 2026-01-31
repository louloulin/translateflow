import React, { useState, useEffect, useRef } from 'react';
import { useGlobal } from '../contexts/GlobalContext';
import { Sparkles, MessageCircle } from 'lucide-react';

interface Tip {
  id: string;
  text: string;
  trigger?: 'idle' | 'hover';
  condition?: (pathname: string) => boolean;
}

const TIPS: Tip[] = [
  { id: 'eden', text: "我也很喜欢听她唱歌呢……如果不谈谈‘价值’的话，她是不会出现的哦♪" },
  { id: 'mobius', text: "那是连我也觉得有些危险的颜色……不过，想要追求‘进化’的话，就必须哪怕失败也要不断尝试吧？" },
  { id: 'pardo', text: "哎呀，东西是不是又找不到了？那只小猫咪可能藏在货物堆里哦。" },
  { id: 'griseo', text: "嘘……她在画画呢。你要为这片夜空染上什么颜色？" },
  { id: 'kevin', text: "那个男人……总是背负着最沉重的东西。如果是为了对抗崩坏（Bug），你会用尽全力吗？" },
  { id: 'kalpas', text: "小心！不要惹他生气……虽然他已经在生气了！如果你执意要破坏这一切的话……" },
  { id: 'general1', text: "今天也是充满奇迹的一天呢，对吧？" },
  { id: 'general2', text: "在这片记忆的海洋里，你发现什么有趣的宝藏了吗？" }
];

export const ElysiaGuide: React.FC = () => {
  const { activeTheme } = useGlobal();
  const [showTip, setShowTip] = useState(false);
  const [currentTip, setCurrentTip] = useState<Tip | null>(null);
  const idleTimer = useRef<any>(null);

  const resetIdleTimer = () => {
    if (idleTimer.current) clearTimeout(idleTimer.current);
    if (activeTheme === 'elysia') {
      idleTimer.current = setTimeout(() => {
        triggerRandomTip();
      }, 30000); // 30 seconds idle
    }
  };

  const triggerRandomTip = () => {
    const randomTip = TIPS[Math.floor(Math.random() * TIPS.length)];
    setCurrentTip(randomTip);
    setShowTip(true);
    setTimeout(() => setShowTip(false), 8000);
  };

  useEffect(() => {
    if (activeTheme === 'elysia') {
      window.addEventListener('mousemove', resetIdleTimer);
      window.addEventListener('keydown', resetIdleTimer);
      resetIdleTimer();
    } else {
      setShowTip(false);
    }
    return () => {
      window.removeEventListener('mousemove', resetIdleTimer);
      window.removeEventListener('keydown', resetIdleTimer);
      if (idleTimer.current) clearTimeout(idleTimer.current);
    };
  }, [activeTheme]);

  if (activeTheme !== 'elysia') return null;

  return (
    <div className={`fixed bottom-24 right-8 z-[10000] transition-all duration-500 transform ${showTip ? 'translate-y-0 opacity-100' : 'translate-y-10 opacity-0 pointer-events-none'}`}>
      <div className="relative flex items-center gap-4 bg-white/90 backdrop-blur-md p-4 rounded-2xl shadow-[0_10px_30px_rgba(255,102,153,0.3)] border border-pink-200 max-w-xs">
        <div className="flex-shrink-0 w-12 h-12 rounded-full bg-pink-100 flex items-center justify-center text-pink-500 shadow-inner">
          <Sparkles size={24} className="animate-pulse" />
        </div>
        <div className="flex-1">
          <p className="text-sm text-pink-600 font-medium leading-relaxed">
            {currentTip?.text}
          </p>
        </div>
        <div className="absolute -bottom-2 right-6 w-4 h-4 bg-white/90 border-r border-b border-pink-200 transform rotate-45"></div>
      </div>
    </div>
  );
};
