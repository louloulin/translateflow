import React from 'react';
import { cn } from '@/lib/utils';

interface ProgressBarProps {
  progress: number;
  className?: string;
  showText?: boolean;
  size?: 'sm' | 'md' | 'lg';
  variant?: 'default' | 'success' | 'warning' | 'danger';
}

export const ProgressBar: React.FC<ProgressBarProps> = ({
  progress,
  className,
  showText = false,
  size = 'md',
  variant = 'default'
}) => {
  const clampedProgress = Math.min(100, Math.max(0, progress));

  const heightClass = {
    sm: 'h-1.5',
    md: 'h-2.5',
    lg: 'h-4'
  }[size];

  const colorClass = {
    default: 'bg-primary',
    success: 'bg-emerald-500',
    warning: 'bg-amber-500',
    danger: 'bg-destructive'
  }[variant];

  return (
    <div className={cn("w-full flex items-center gap-2", className)}>
      <div className={cn("flex-1 bg-secondary rounded-full overflow-hidden", heightClass)}>
        <div 
          className={cn("h-full transition-all duration-500 ease-in-out rounded-full", colorClass)}
          style={{ width: `${clampedProgress}%` }}
        />
      </div>
      {showText && (
        <span className="text-xs font-mono text-muted-foreground w-10 text-right">
          {Math.round(clampedProgress)}%
        </span>
      )}
    </div>
  );
};
