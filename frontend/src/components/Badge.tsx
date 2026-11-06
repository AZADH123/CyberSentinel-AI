import React from 'react';

interface BadgeProps {
  label: string;
  variant?: 'severity' | 'status' | 'enrichment' | 'confidence' | 'default';
  size?: 'sm' | 'md';
}

export const Badge: React.FC<BadgeProps> = ({ label, variant = 'default', size = 'sm' }) => {
  const normalized = label.toLowerCase();

  let colorClasses = 'bg-slate-800 text-slate-300 border-slate-700';

  if (variant === 'severity') {
    switch (normalized) {
      case 'high':
      case 'critical':
        colorClasses = 'bg-red-950/80 text-red-300 border-red-700/60';
        break;
      case 'medium':
        colorClasses = 'bg-amber-950/80 text-amber-300 border-amber-700/60';
        break;
      case 'low':
        colorClasses = 'bg-emerald-950/80 text-emerald-300 border-emerald-700/60';
        break;
      case 'informational':
      default:
        colorClasses = 'bg-slate-800 text-slate-300 border-slate-700';
        break;
    }
  } else if (variant === 'status') {
    switch (normalized) {
      case 'open':
        colorClasses = 'bg-sky-950/80 text-sky-300 border-sky-700/60';
        break;
      case 'investigating':
      case 'running':
        colorClasses = 'bg-purple-950/80 text-purple-300 border-purple-700/60 animate-pulse';
        break;
      case 'awaiting_review':
        colorClasses = 'bg-amber-950/80 text-amber-300 border-amber-700/60';
        break;
      case 'accepted':
      case 'completed':
        colorClasses = 'bg-emerald-950/80 text-emerald-300 border-emerald-700/60';
        break;
      case 'completed_degraded':
      case 'degraded':
        colorClasses = 'bg-yellow-950/80 text-yellow-300 border-yellow-700/60';
        break;
      case 'rejected':
      case 'failed':
        colorClasses = 'bg-red-950/80 text-red-300 border-red-700/60';
        break;
      case 'escalated':
        colorClasses = 'bg-rose-950/80 text-rose-300 border-rose-700/60 font-semibold';
        break;
    }
  } else if (variant === 'enrichment') {
    switch (normalized) {
      case 'live':
        colorClasses = 'bg-emerald-950/80 text-emerald-300 border-emerald-700/60';
        break;
      case 'mock':
        colorClasses = 'bg-indigo-950/80 text-indigo-300 border-indigo-700/60';
        break;
      case 'skipped':
        colorClasses = 'bg-slate-800 text-slate-400 border-slate-700';
        break;
      case 'timeout':
      case 'rate_limited':
        colorClasses = 'bg-amber-950/80 text-amber-300 border-amber-700/60';
        break;
    }
  }

  const sizeClass = size === 'sm' ? 'px-2 py-0.5 text-xs' : 'px-2.5 py-1 text-sm';

  return (
    <span
      className={`inline-flex items-center font-medium rounded-full border ${sizeClass} ${colorClasses}`}
    >
      {label}
    </span>
  );
};
