import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Plus, RefreshCw, Filter, ArrowRight, ShieldAlert } from 'lucide-react';
import { api } from '../api/client';
import { Badge } from '../components/Badge';
import { RiskMeter } from '../components/RiskMeter';
import { NewAlertModal } from '../components/NewAlertModal';

interface AlertQueuePageProps {
  onSelectAlert: (alertId: string) => void;
}

export const AlertQueuePage: React.FC<AlertQueuePageProps> = ({ onSelectAlert }) => {
  const [modalOpen, setModalOpen] = useState(false);
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [severityFilter, setSeverityFilter] = useState<string>('');

  const { data, isLoading, isError, error, refetch, isFetching } = useQuery({
    queryKey: ['alerts', statusFilter, severityFilter],
    queryFn: () =>
      api.getAlerts({
        limit: 50,
        status: statusFilter || undefined,
        severity: severityFilter || undefined,
      }),
    refetchInterval: 5000,
  });

  return (
    <div className="flex flex-col gap-5">
      {/* Page Title & Actions */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-slate-100">SOC Alert Queue</h1>
          <p className="text-xs text-slate-400 mt-0.5">
            Real-time ingested authentication and access anomalies
          </p>
        </div>

        <div className="flex items-center gap-2.5">
          <button
            onClick={() => refetch()}
            disabled={isFetching}
            className="px-3 py-1.5 text-xs font-medium rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 flex items-center gap-1.5 border border-slate-700"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isFetching ? 'animate-spin' : ''}`} />
            Refresh
          </button>
          <button
            onClick={() => setModalOpen(true)}
            className="px-3.5 py-1.5 text-xs font-semibold rounded-lg bg-sky-500 hover:bg-sky-400 text-slate-950 flex items-center gap-1.5 shadow-lg shadow-sky-500/10"
          >
            <Plus className="w-4 h-4" />
            Ingest Test Alert
          </button>
        </div>
      </div>

      {/* Filter Bar */}
      <div className="flex items-center gap-3 bg-slate-900/80 border border-slate-800/80 p-3 rounded-xl text-xs">
        <Filter className="w-4 h-4 text-slate-500" />
        <div className="flex items-center gap-2">
          <label className="text-slate-400">Status:</label>
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="bg-slate-800 border border-slate-700 rounded px-2 py-1 text-slate-200"
          >
            <option value="">All Statuses</option>
            <option value="open">Open</option>
            <option value="investigating">Investigating</option>
            <option value="awaiting_review">Awaiting Review</option>
            <option value="accepted">Accepted</option>
            <option value="rejected">Rejected</option>
            <option value="escalated">Escalated</option>
          </select>
        </div>

        <div className="flex items-center gap-2 ml-2">
          <label className="text-slate-400">Severity:</label>
          <select
            value={severityFilter}
            onChange={(e) => setSeverityFilter(e.target.value)}
            className="bg-slate-800 border border-slate-700 rounded px-2 py-1 text-slate-200"
          >
            <option value="">All Severities</option>
            <option value="informational">Informational</option>
            <option value="low">Low</option>
            <option value="medium">Medium</option>
            <option value="high">High</option>
          </select>
        </div>

        {(statusFilter || severityFilter) && (
          <button
            onClick={() => {
              setStatusFilter('');
              setSeverityFilter('');
            }}
            className="text-xs text-sky-400 hover:underline ml-auto"
          >
            Clear filters
          </button>
        )}
      </div>

      {/* Alerts Table */}
      <div className="bg-slate-900/90 border border-slate-800 rounded-xl overflow-hidden shadow-xl">
        {isLoading ? (
          <div className="p-12 text-center flex flex-col items-center justify-center gap-3 text-slate-500">
            <RefreshCw className="w-6 h-6 animate-spin text-sky-500" />
            <p className="text-sm">Loading alerts...</p>
          </div>
        ) : isError ? (
          <div className="p-8 text-center flex flex-col items-center justify-center gap-2 text-slate-400">
            <ShieldAlert className="w-8 h-8 text-amber-500" />
            <p className="font-semibold text-slate-300">Database Offline / Degraded</p>
            <p className="text-xs max-w-md text-slate-500">
              {(error as Error)?.message || 'Could not connect to PostgreSQL. Once PostgreSQL is running, ingested alerts will appear here.'}
            </p>
          </div>
        ) : !data?.items || data.items.length === 0 ? (
          <div className="p-12 text-center flex flex-col items-center justify-center gap-3 text-slate-400">
            <div className="p-3 rounded-full bg-slate-800/80 border border-slate-700 text-slate-500">
              <ShieldAlert className="w-6 h-6" />
            </div>
            <p className="font-semibold text-slate-300">No alerts found</p>
            <p className="text-xs text-slate-500 max-w-sm">
              Use the "Ingest Test Alert" button above to submit an alert payload or wait for incoming events.
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="border-b border-slate-800 bg-slate-950/60 text-slate-400 font-semibold uppercase tracking-wider">
                  <th className="py-3 px-4">Event Time</th>
                  <th className="py-3 px-4">User</th>
                  <th className="py-3 px-4">Host / IP</th>
                  <th className="py-3 px-4">Outcome</th>
                  <th className="py-3 px-4">Failures</th>
                  <th className="py-3 px-4">Severity</th>
                  <th className="py-3 px-4">Risk Score</th>
                  <th className="py-3 px-4">Status</th>
                  <th className="py-3 px-4 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 font-mono text-slate-300">
                {data.items.map((alert) => (
                  <tr
                    key={alert.alert_id}
                    onClick={() => onSelectAlert(alert.alert_id)}
                    className="hover:bg-slate-800/50 cursor-pointer transition-colors group"
                  >
                    <td className="py-3 px-4 text-slate-400 whitespace-nowrap">
                      {new Date(alert.event_time).toLocaleString()}
                    </td>
                    <td className="py-3 px-4 font-semibold text-slate-200">
                      {alert.username}
                    </td>
                    <td className="py-3 px-4">
                      <div>{alert.host}</div>
                      <div className="text-[11px] text-slate-500">{alert.source_ip}</div>
                    </td>
                    <td className="py-3 px-4">
                      <span
                        className={`inline-block px-1.5 py-0.5 rounded text-[11px] ${
                          alert.outcome === 'success'
                            ? 'bg-emerald-950 text-emerald-400'
                            : 'bg-red-950 text-red-400'
                        }`}
                      >
                        {alert.outcome}
                      </span>
                    </td>
                    <td className="py-3 px-4">
                      {alert.failure_count > 0 ? (
                        <span className="font-bold text-amber-400">{alert.failure_count}</span>
                      ) : (
                        <span className="text-slate-600">0</span>
                      )}
                    </td>
                    <td className="py-3 px-4">
                      <Badge label={alert.severity} variant="severity" />
                    </td>
                    <td className="py-3 px-4">
                      <RiskMeter score={alert.risk_score} />
                    </td>
                    <td className="py-3 px-4">
                      <Badge label={alert.status} variant="status" />
                    </td>
                    <td className="py-3 px-4 text-right">
                      <button className="p-1 rounded text-slate-400 group-hover:text-sky-400 transition">
                        <ArrowRight className="w-4 h-4" />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      <NewAlertModal
        isOpen={modalOpen}
        onClose={() => setModalOpen(false)}
        onCreated={() => refetch()}
      />
    </div>
  );
};
