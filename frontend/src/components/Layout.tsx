import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { Shield, AlertTriangle, CheckCircle2, RefreshCw } from 'lucide-react';
import { api } from '../api/client';

interface LayoutProps {
  children: React.ReactNode;
  activeTab: 'alerts' | 'incidents' | 'detail' | 'review';
  onNavigate: (tab: 'alerts' | 'incidents', id?: string) => void;
}

export const Layout: React.FC<LayoutProps> = ({ children, activeTab, onNavigate }) => {
  const { data: health, isLoading: healthLoading, refetch: refetchHealth } = useQuery({
    queryKey: ['health'],
    queryFn: api.getHealth,
    refetchInterval: 10000,
  });

  const isDegraded = health?.status === 'degraded' || health?.checks.database.status === 'error';

  return (
    <div className="min-h-screen bg-[#090d16] text-slate-100 flex flex-col font-sans">
      {/* Top Header */}
      <header className="border-b border-slate-800 bg-[#0f172a]/90 backdrop-blur sticky top-0 z-50 px-6 py-3.5 flex items-center justify-between">
        <div className="flex items-center gap-6">
          <div
            className="flex items-center gap-2.5 cursor-pointer"
            onClick={() => onNavigate('alerts')}
          >
            <div className="p-1.5 rounded-lg bg-sky-500/10 border border-sky-500/30 text-sky-400">
              <Shield className="w-5 h-5" />
            </div>
            <div>
              <span className="font-bold text-base tracking-tight bg-gradient-to-r from-sky-400 to-indigo-300 bg-clip-text text-transparent">
                CyberSentinel AI
              </span>
              <span className="ml-2 px-1.5 py-0.5 text-[10px] uppercase font-mono rounded bg-slate-800 text-slate-400 border border-slate-700">
                SOC v0.1.0
              </span>
            </div>
          </div>

          <nav className="flex items-center gap-1 border-l border-slate-800 pl-6">
            <button
              onClick={() => onNavigate('alerts')}
              className={`px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
                activeTab === 'alerts'
                  ? 'bg-sky-500/15 text-sky-300 border border-sky-500/30'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
              }`}
            >
              Alerts Queue
            </button>
            <button
              onClick={() => onNavigate('incidents')}
              className={`px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
                activeTab === 'incidents'
                  ? 'bg-sky-500/15 text-sky-300 border border-sky-500/30'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
              }`}
            >
              Incidents
            </button>
          </nav>
        </div>

        {/* Health status badge */}
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 px-3 py-1 rounded-full bg-slate-900 border border-slate-800 text-xs">
            {healthLoading ? (
              <RefreshCw className="w-3.5 h-3.5 animate-spin text-slate-500" />
            ) : isDegraded ? (
              <span className="flex items-center gap-1.5 text-amber-400 font-medium">
                <AlertTriangle className="w-3.5 h-3.5 text-amber-400" />
                Degraded (Offline DB)
              </span>
            ) : (
              <span className="flex items-center gap-1.5 text-emerald-400 font-medium">
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                System Ready
              </span>
            )}

            {health && (
              <span className="text-slate-500 border-l border-slate-800 pl-2">
                Enrich: <strong className="text-slate-300">{health.checks.enrichment.mode}</strong>
              </span>
            )}
          </div>

          <button
            onClick={() => refetchHealth()}
            title="Refresh status"
            className="p-1.5 text-slate-400 hover:text-slate-200 rounded hover:bg-slate-800 transition"
          >
            <RefreshCw className="w-3.5 h-3.5" />
          </button>
        </div>
      </header>

      {/* Main Content Area */}
      <main className="flex-1 max-w-7xl w-full mx-auto p-6 flex flex-col gap-6">
        {children}
      </main>

      <footer className="border-t border-slate-800/80 px-6 py-4 text-center text-xs text-slate-500 flex items-center justify-between">
        <span>CyberSentinel AI &bull; Evidence-grounded SOC alert triage & investigation prototype</span>
        <span className="font-mono text-[11px]">Recommend-only &bull; No automated containment tools</span>
      </footer>
    </div>
  );
};
