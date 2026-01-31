import React, { useEffect, useState } from 'react';
import { Sparkles, X, Unlock, Info } from 'lucide-react';
import { ThemeType } from '../types';

interface UnlockModalProps {
  theme: ThemeType;
  onClose: () => void;
}

export const UnlockModal: React.FC<UnlockModalProps> = ({ theme, onClose }) => {
  const [isVisible, setIsVisible] = useState(false);

  useEffect(() => {
    setIsVisible(true);
  }, []);

  const getThemeData = (type: ThemeType) => {
    switch (type) {
      case 'elysia': return { name: '爱莉希雅', color: '#ff6699', quote: '嗨~ 想我了吗？这就是我给你的小惊喜哦♪' };
      case 'eden': return { name: '伊甸', color: '#d4af37', quote: '愿这片黄金的港湾，能成为你创作的灵感源泉。' };
      case 'mobius': return { name: '梅比乌斯', color: '#00ff41', quote: '呵呵……发现了吗？这是通往无限进化的另一条路径。' };
      case 'pardofelis': return { name: '帕朵菲莉丝', color: '#e6b8a2', quote: '哎呀，大老板！咱家这儿又多了一件压箱底的好宝贝，快来看看！' };
      case 'griseo': return { name: '格蕾修', color: '#a2c2e1', quote: '我在画板上为你留了一个位置……想看看这些新的颜色吗？' };
      case 'kevin': return { name: '凯文', color: '#00f2ff', quote: '无论前路多么寒冷，这份力量都会与你同在。' };
      case 'kalpas': return { name: '千劫', color: '#ff4d4d', quote: '哈！既然你有胆量触碰这里，那就让这怒火烧得更旺些吧！' };
      case 'aponia': return { name: '阿波尼亚', color: '#9d81ba', quote: '迷途的灵魂……戒律已为你敞开大门，去寻找你的救赎吧。' };
      case 'villv': return { name: '维尔薇', color: '#c5a059', quote: '大幕拉开！天才的新舞台已准备就绪，尽情享受这场奇迹吧！' };
      case 'su': return { name: '苏', color: '#88a070', quote: '须臾之间，万物皆空。请在这一叶的世界里，静待真实的浮现。' };
      case 'sakura': return { name: '樱', color: '#f4b0c7', quote: '落樱已至，这份静谧的守护，从此属于你了。' };
      case 'kosma': return { name: '科斯魔', color: '#1a2a4a', quote: '……黑夜虽沉，但你不再是孤身一人。' };
      case 'hua': return { name: '华', color: '#d4a017', quote: '精诚所至，金石为开。这份内敛的力量，赠予同样专注的你。' };
      case 'herrscher_of_human': return { name: '真我·人之律者', color: '#ff8fa3', quote: '这是为你，也为所有人创造的奇迹。让我们一起，把故事写完吧。' };
      default: return { name: '未知', color: '#06b6d4', quote: '一个神秘的新配置已解锁。' };
    }
  };

  const data = getThemeData(theme);

  return (
    <div className={`fixed inset-0 z-[10002] flex items-center justify-center p-4 transition-all duration-700 ${isVisible ? 'opacity-100' : 'opacity-0'}`}>
      <div className="absolute inset-0 bg-black/60 backdrop-blur-md" onClick={onClose}></div>
      
      <div className={`relative w-full max-w-md bg-slate-900 border border-white/10 rounded-3xl overflow-hidden shadow-2xl transition-all duration-700 transform ${isVisible ? 'scale-100 translate-y-0' : 'scale-90 translate-y-10'}`}>
        {/* Animated Background Orbs */}
        <div className="absolute -top-24 -left-24 w-48 h-48 rounded-full blur-[80px] opacity-20 animate-pulse" style={{ backgroundColor: data.color }}></div>
        <div className="absolute -bottom-24 -right-24 w-48 h-48 rounded-full blur-[80px] opacity-20 animate-pulse" style={{ backgroundColor: data.color, animationDelay: '1s' }}></div>

        <div className="p-8 flex flex-col items-center text-center">
          <div className="w-16 h-16 rounded-2xl bg-white/5 flex items-center justify-center mb-6 relative group">
             <div className="absolute inset-0 rounded-2xl animate-ping opacity-20" style={{ backgroundColor: data.color }}></div>
             <Unlock size={32} style={{ color: data.color }} />
          </div>
          
          <h2 className="text-2xl font-black text-white mb-2 tracking-tight">发现新的主题！</h2>
          <div className="px-3 py-1 rounded-full text-[10px] font-bold uppercase tracking-widest mb-6 border" style={{ borderColor: `${data.color}40`, color: data.color, backgroundColor: `${data.color}10` }}>
            {data.name} 系列
          </div>
          
          <p className="text-slate-300 italic font-serif leading-relaxed mb-8 relative">
            <span className="text-3xl absolute -top-4 -left-2 opacity-20 font-serif">"</span>
            {data.quote}
            <span className="text-3xl absolute -bottom-8 -right-2 opacity-20 font-serif">"</span>
          </p>

          <div className="w-full space-y-3">
            <div className="flex items-start gap-3 p-3 bg-white/5 rounded-xl border border-white/5 text-left">
              <Info size={14} className="shrink-0 mt-0.5 text-slate-400" />
              <p className="text-[10px] text-slate-400">设置页面内貌似新增了一些什么，你可以在「项目配置 - 配置文件」区域查看并切换已解锁的主题。</p>
            </div>
            
            <button 
              onClick={onClose}
              className="w-full py-3 bg-white text-slate-900 font-bold rounded-xl hover:bg-slate-200 transition-all transform active:scale-95"
            >
              太棒了！
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
