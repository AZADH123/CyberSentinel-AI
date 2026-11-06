import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { RefreshCw, Filter, ShieldCheck, UserCheck, ArrowRight } from 'lucide-react';
import { api } from '../api/client';
import { Badge } from '../components/Badge';
import { RiskMeter } from '../components/RiskMeter';

interface IncidentsPageProps {
  onSelectIncident: (incidentId: string) => void;
  onReviewIncident: (incidentId: string) => void;
}

export const IncidentsPage: React.FC<IncidentsPageProps> = ({
  onSelectIncident,
  onReviewIncident,
}) => {
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [severityFilter, setSeverityFilter] = useState<string>('');

  const { data, isLoading, isError, error, refetch, isFetching } = useQuery({
    queryKey: ['incidents', statusFilter, severityFilter],
    queryFn: () =>
      api.getIncidents({
        limit: 50,
        status: statusFilter || undefined,
        severity: severityFilter || undefined,
      }),
    refetchInterval: 5000,
  });

  return (
    <div className="flex flex-col gap-5">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-slate-100">Security Incidents</h1>
          <p className="text-xs text-slate-400 mt-0.5">
            Prioritized by deterministic risk score and triage severity
          </p>
        </div>

        <button
          onClick={() => refetch()}
          disabled={isFetching}
          className="px-3 py-1.5 text-xs font-medium rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 flex items-center gap-1.5 border border-slate-700"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${isFetching ? 'animate-spin' : ''}`} />
          Refresh
        </button>
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
      </div>

      {/* Incidents Table */}
      <div className="bg-slate-900/90 border border-slate-800 rounded-xl overflow-hidden shadow-xl">
        {isLoading ? (
          <div className="p-12 text-center flex flex-col items-center justify-center gap-3 text-slate-500">
            <RefreshCw className="w-6 h-6 animate-spin text-sky-500" />
            <p className="text-sm">Loading incidents...</p>
          </div>
        ) : isError ? (
          <div className="p-8 text-center flex flex-col items-center justify-center gap-2 text-slate-400">
            <ShieldCheck className="w-8 h-8 text-amber-500" />
            <p className="font-semibold text-slate-300">Database Offline / Degraded</p>
            <p className="text-xs max-w-md text-slate-500">
              {(error as Error)?.message || 'Database connection unavailable.'}
            </p>
          </div>
        ) : !data?.items || data.items.length === 0 ? (
          <div className="p-12 text-center text-slate-500">No incidents in the queue.</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="border-b border-slate-800 bg-slate-950/60 text-slate-400 font-semibold uppercase tracking-wider">
                  <th className="py-3 px-4">Incident ID</th>
                  <th className="py-3 px-4">Created At</th>
                  <th className="py-3 px-4">Risk Score</th>
                  <th className="py-3 px-4">Severity Band</th>
                  <th className="py-3 px-4">Confidence</th>
                  <th className="py-3 px-4">Status</th>
                  <th className="py-3 px-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 font-mono text-slate-300">
                {data.items.map((inc) => (
                  <tr
                    key={inc.incident_id}
                    className="hover:bg-slate-800/50 transition-colors"
                  >
                    <td
                      onClick={() => onSelectIncident(inc.incident_id)}
                      className="py-3 px-4 font-bold text-sky-400 cursor-pointer hover:underline"
                    >
                      {inc.incident_id}
                    </td>
                    <td className="py-3 px-4 text-slate-400">
                      {new Date(inc.created_at).toLocaleString()}
                    </td>
                    <td className="py-3 px-4">
                      <RiskMeter score={inc.risk_score} band={inc.risk_band} />
                    </td>
                    <td className="py-3 px-4">
                      <Badge label={inc.severity} variant="severity" />
                    </td>
                    <td className="py-3 px-4">
                      <Badge label={inc.confidence} variant="confidence" />
                    </td>
                    <td className="py-3 px-4">
                      <Badge label={inc.status} variant="status" />
                    </td>
                    <td className="py-3 px-4 text-right">
                      <div className="flex items-center justify-end gap-2">
                        <button
                          onClick={() => onReviewIncident(inc.incident_id)}
                          className="px-2.5 py-1 rounded bg-indigo-600/80 hover:bg-indigo-600 text-white text-[11px] font-medium flex items-center gap-1"
                        >
                          <UserCheck className="w-3.5 h-3.5" />
                          Review
                        </button>
                        <button
                          onClick={() => onSelectIncident(inc.incident_id)}
                          className="p-1 rounded text-slate-400 hover:text-slate-200"
                        >
                          <ArrowRight className="w-4 h-4" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};
