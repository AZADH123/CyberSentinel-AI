import React from 'react';

interface RiskMeterProps {
  score: number;
  band?: string;
  showBar?: boolean;
}

export const RiskMeter: React.FC<RiskMeterProps> = ({ score, band, showBar = true }) => {
  const clamped = Math.max(0, Math.min(100, score));

  let color = 'bg-slate-500';
  let textColor = 'text-slate-400';

  if (clamped >= 75) {
    color = 'bg-red-500';
    textColor = 'text-red-400 font-bold';
  } else if (clamped >= 50) {
    color = 'bg-amber-500';
    textColor = 'text-amber-400 font-semibold';
  } else if (clamped >= 25) {
    color = 'bg-yellow-500';
    textColor = 'text-yellow-400 font-medium';
  } else {
    color = 'bg-emerald-500';
    textColor = 'text-emerald-400 font-medium';
  }

  return (
    <div className="flex flex-col gap-1 w-full max-w-[120px]">
      <div className="flex items-center justify-between text-xs">
        <span className={`font-mono text-sm ${textColor}`}>{clamped}</span>
        {band && <span className="text-[10px] uppercase tracking-wider text-slate-400">{band}</span>}
      </div>
      {showBar && (
        <div className="w-full bg-slate-800 rounded-full h-1.5 overflow-hidden">
          <div
            className={`h-full ${color} transition-all duration-500 ease-out`}
            style={{ width: `${clamped}%` }}
          />
        </div>
      )}
    </div>
  );
};
