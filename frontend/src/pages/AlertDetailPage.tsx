import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  ArrowLeft,
  Play,
  ExternalLink,
  ShieldAlert,
  ClipboardList,
  Cpu,
  Layers,
  UserCheck,
} from 'lucide-react';
import { api } from '../api/client';
import { Badge } from '../components/Badge';

interface AlertDetailPageProps {
  alertId: string;
  onBack: () => void;
  onGoToReview: (incidentId: string) => void;
}

export const AlertDetailPage: React.FC<AlertDetailPageProps> = ({
  alertId,
  onBack,
  onGoToReview,
}) => {
  const queryClient = useQueryClient();
  const [activeTab, setActiveTab] = useState<'analysis' | 'evidence' | 'raw'>('analysis');

  // Fetch alert details
  const { data: alert, isLoading, isError, error } = useQuery({
    queryKey: ['alert', alertId],
    queryFn: () => api.getAlert(alertId),
  });

  const incidentId = alert?.incident.incident_id;

  // Fetch incident details (includes latest investigation & report)
  const { data: incident, refetch: refetchIncident } = useQuery({
    queryKey: ['incident', incidentId],
    queryFn: () => api.getIncident(incidentId!),
    enabled: !!incidentId,
    refetchInterval: (query) => {
      const status = query.state.data?.investigation_status;
      return status === 'running' || status === 'queued' ? 1000 : false;
    },
  });

  // Fetch evidence if available
  const { data: evidence } = useQuery({
    queryKey: ['evidence', incidentId],
    queryFn: () => api.getIncidentEvidence(incidentId!),
    enabled: !!incidentId && activeTab === 'evidence',
  });

  // Mutation to start investigation
  const startMutation = useMutation({
    mutationFn: () => api.startInvestigation(alertId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['alert', alertId] });
      queryClient.invalidateQueries({ queryKey: ['incident', incidentId] });
      refetchIncident();
    },
  });

  if (isLoading) {
    return (
      <div className="p-16 text-center text-slate-500">
        Loading alert details...
      </div>
    );
  }

  if (isError || !alert) {
    return (
      <div className="p-8 bg-slate-900 border border-slate-800 rounded-xl text-center">
        <p className="text-red-400 font-medium">Failed to load alert</p>
        <p className="text-xs text-slate-500 mt-1">{(error as Error)?.message || 'Alert not found'}</p>
        <button
          onClick={onBack}
          className="mt-4 px-4 py-2 text-xs bg-slate-800 text-slate-300 rounded hover:bg-slate-700"
        >
          Return to Queue
        </button>
      </div>
    );
  }

  const isInvestigating = incident?.investigation_status === 'running' || incident?.investigation_status === 'queued';
  const hasReport = !!incident?.report;

  return (
    <div className="flex flex-col gap-6">
      {/* Top Header */}
      <div className="flex items-center justify-between">
        <button
          onClick={onBack}
          className="text-slate-400 hover:text-slate-200 flex items-center gap-1.5 text-xs font-medium"
        >
          <ArrowLeft className="w-4 h-4" />
          Back to Queue
        </button>

        <div className="flex items-center gap-3">
          {incident && (
            <button
              onClick={() => onGoToReview(incident.incident_id)}
              className="px-3.5 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold flex items-center gap-1.5 transition"
            >
              <UserCheck className="w-4 h-4" />
              Review Incident
            </button>
          )}

          <button
            onClick={() => startMutation.mutate()}
            disabled={startMutation.isPending || isInvestigating}
            className="px-4 py-1.5 rounded-lg bg-sky-500 hover:bg-sky-400 disabled:opacity-50 text-slate-950 text-xs font-bold flex items-center gap-1.5 transition shadow-lg shadow-sky-500/10"
          >
            <Play className={`w-3.5 h-3.5 ${isInvestigating ? 'animate-spin' : ''}`} />
            {isInvestigating
              ? 'Investigating...'
              : hasReport
              ? 'Re-Investigate'
              : 'Launch Investigation'}
          </button>
        </div>
      </div>

      {/* Main Alert & Incident Cards */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
        {/* Alert Overview */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 flex flex-col gap-4">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <span className="text-xs uppercase font-mono text-slate-400">Alert Context</span>
            <Badge label={alert.source} variant="default" />
          </div>

          <div className="grid grid-cols-2 gap-3 text-xs">
            <div>
              <span className="text-slate-500 block">User</span>
              <span className="font-semibold text-slate-200">{alert.normalized_event.username}</span>
            </div>
            <div>
              <span className="text-slate-500 block">Source IP</span>
              <span className="font-mono text-slate-200">{alert.normalized_event.source_ip}</span>
            </div>
            <div>
              <span className="text-slate-500 block">Target Host</span>
              <span className="text-slate-200">{alert.normalized_event.host}</span>
            </div>
            <div>
              <span className="text-slate-500 block">Outcome</span>
              <span
                className={`font-semibold ${
                  alert.normalized_event.outcome === 'success' ? 'text-emerald-400' : 'text-red-400'
                }`}
              >
                {alert.normalized_event.outcome}
              </span>
            </div>
            <div>
              <span className="text-slate-500 block">Failures</span>
              <span className="font-mono text-amber-400 font-bold">
                {alert.normalized_event.failure_count}
              </span>
            </div>
            <div>
              <span className="text-slate-500 block">Criticality</span>
              <span className="text-slate-200 capitalize">
                {alert.normalized_event.asset_criticality}
              </span>
            </div>
          </div>

          <div className="pt-2 border-t border-slate-800 text-[11px] text-slate-500 font-mono">
            ID: {alert.alert_id}
          </div>
        </div>

        {/* Incident Summary */}
        <div className="lg:col-span-2 bg-slate-900 border border-slate-800 rounded-xl p-5 flex flex-col gap-4">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <div className="flex items-center gap-2">
              <span className="text-sm font-bold text-slate-200">Incident {alert.incident.incident_id}</span>
              <Badge label={alert.incident.status} variant="status" />
            </div>
            <div className="flex items-center gap-2">
              <span className="text-xs text-slate-500">Confidence:</span>
              <Badge label={alert.incident.confidence} variant="confidence" />
            </div>
          </div>

          <div className="grid grid-cols-3 gap-4 items-center">
            <div className="bg-slate-950/60 p-4 rounded-lg border border-slate-800 flex flex-col items-center">
              <span className="text-xs text-slate-400 mb-1">Risk Score</span>
              <span className="text-3xl font-extrabold text-sky-400 font-mono">
                {incident?.risk_score ?? alert.incident.risk_score}
              </span>
              <span className="text-[10px] uppercase tracking-wider text-slate-500 mt-0.5">
                Band: {incident?.risk_band ?? alert.incident.risk_band}
              </span>
            </div>

            <div className="bg-slate-950/60 p-4 rounded-lg border border-slate-800 flex flex-col justify-center gap-2">
              <span className="text-xs text-slate-400">Severity Level</span>
              <div>
                <Badge label={incident?.severity ?? alert.incident.severity} variant="severity" size="md" />
              </div>
            </div>

            <div className="bg-slate-950/60 p-4 rounded-lg border border-slate-800 flex flex-col justify-center gap-2">
              <span className="text-xs text-slate-400">Investigation State</span>
              <div>
                <Badge
                  label={incident?.investigation_status ?? 'Not Run'}
                  variant="status"
                  size="md"
                />
              </div>
            </div>
          </div>

          {incident?.reviews && incident.reviews.length > 0 && (
            <div className="mt-2 p-3 bg-indigo-950/30 border border-indigo-900/50 rounded-lg text-xs flex items-center justify-between">
              <span className="text-indigo-300">
                Reviewed by <strong>{incident.reviews[0].reviewer}</strong>: {incident.reviews[0].disposition}
              </span>
              <span className="text-indigo-400 text-[11px]">
                {new Date(incident.reviews[0].reviewed_at).toLocaleString()}
              </span>
            </div>
          )}
        </div>
      </div>

      {/* Tabs */}
      <div className="flex items-center gap-2 border-b border-slate-800">
        <button
          onClick={() => setActiveTab('analysis')}
          className={`px-4 py-2 text-xs font-semibold border-b-2 flex items-center gap-2 transition ${
            activeTab === 'analysis'
              ? 'border-sky-500 text-sky-400'
              : 'border-transparent text-slate-400 hover:text-slate-200'
          }`}
        >
          <Cpu className="w-4 h-4" />
          Investigation & Findings
        </button>
        <button
          onClick={() => setActiveTab('evidence')}
          className={`px-4 py-2 text-xs font-semibold border-b-2 flex items-center gap-2 transition ${
            activeTab === 'evidence'
              ? 'border-sky-500 text-sky-400'
              : 'border-transparent text-slate-400 hover:text-slate-200'
          }`}
        >
          <Layers className="w-4 h-4" />
          Evidence Substrate
        </button>
        <button
          onClick={() => setActiveTab('raw')}
          className={`px-4 py-2 text-xs font-semibold border-b-2 flex items-center gap-2 transition ${
            activeTab === 'raw'
              ? 'border-sky-500 text-sky-400'
              : 'border-transparent text-slate-400 hover:text-slate-200'
          }`}
        >
          <ClipboardList className="w-4 h-4" />
          Raw Payload
        </button>
      </div>

      {/* Tab Contents */}
      {activeTab === 'analysis' && (
        <div className="flex flex-col gap-5">
          {!hasReport ? (
            <div className="p-12 text-center bg-slate-900/60 border border-slate-800 rounded-xl flex flex-col items-center justify-center gap-3">
              <ShieldAlert className="w-8 h-8 text-slate-600" />
              <p className="text-sm text-slate-300 font-medium">No investigation executed yet</p>
              <p className="text-xs text-slate-500 max-w-sm">
                Click "Launch Investigation" above to execute deterministic triage, correlation, and ATT&CK candidate mapping.
              </p>
            </div>
          ) : (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
              {/* Triage Findings & Score Breakdown */}
              <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 flex flex-col gap-4">
                <h3 className="font-semibold text-sm text-slate-200 flex items-center gap-2">
                  <Cpu className="w-4 h-4 text-sky-400" />
                  Deterministic Score Breakdown
                </h3>

                <div className="flex flex-col gap-2.5">
                  {incident.report?.risk_assessment.factors.map((factor, idx) => (
                    <div
                      key={idx}
                      className="p-3 bg-slate-950/60 border border-slate-800/80 rounded-lg flex items-center justify-between text-xs"
                    >
                      <div className="flex items-center gap-2">
                        <span className="font-mono text-[10px] px-1.5 py-0.5 rounded bg-sky-950 text-sky-400 border border-sky-800/60">
                          {factor.rule_id}
                        </span>
                        <span className="text-slate-200">{factor.label}</span>
                      </div>
                      <span className="font-mono font-bold text-amber-400">+{factor.points} pts</span>
                    </div>
                  ))}
                </div>

                {incident.report?.gaps && incident.report.gaps.length > 0 && (
                  <div className="mt-2 pt-3 border-t border-slate-800">
                    <span className="text-xs text-slate-400 font-medium block mb-2">Identified Gaps:</span>
                    <div className="flex flex-wrap gap-1.5">
                      {incident.report.gaps.map((gap, idx) => (
                        <span
                          key={idx}
                          className="px-2 py-0.5 rounded text-[11px] bg-slate-800 text-slate-400 font-mono"
                        >
                          {gap}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>

              {/* MITRE ATT&CK Mapping */}
              <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 flex flex-col gap-4">
                <h3 className="font-semibold text-sm text-slate-200 flex items-center gap-2">
                  <Layers className="w-4 h-4 text-indigo-400" />
                  MITRE ATT&CK Candidates
                </h3>

                <div className="flex flex-col gap-2.5">
                  {incident.report?.attack_candidates.map((cand, idx) => (
                    <div
                      key={idx}
                      className="p-3 bg-slate-950/60 border border-slate-800/80 rounded-lg flex flex-col gap-1.5 text-xs"
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <span className="font-mono text-indigo-400 font-semibold">{cand.technique_id}</span>
                          <span className="text-slate-200 font-medium">{cand.technique_name}</span>
                        </div>
                        <Badge label={cand.tactic} variant="default" />
                      </div>
                      <p className="text-slate-400 text-[11px]">{cand.rationale}</p>
                      <div className="flex items-center justify-between pt-1 text-[11px]">
                        <span className="text-slate-500 font-mono">
                          Evidence: {cand.evidence_refs.join(', ')}
                        </span>
                        <a
                          href={cand.url}
                          target="_blank"
                          rel="noreferrer"
                          className="text-sky-400 hover:underline flex items-center gap-1"
                        >
                          MITRE Reference <ExternalLink className="w-3 h-3" />
                        </a>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {activeTab === 'evidence' && (
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 flex flex-col gap-4">
          <h3 className="font-semibold text-sm text-slate-200">Append-Only Evidence Records</h3>
          {!evidence || evidence.length === 0 ? (
            <p className="text-xs text-slate-500">No evidence items recorded yet.</p>
          ) : (
            <div className="flex flex-col gap-2.5">
              {evidence.map((ev) => (
                <div
                  key={ev.id}
                  className="p-3.5 bg-slate-950/60 border border-slate-800 rounded-lg text-xs flex flex-col gap-2"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-emerald-400 font-bold">{ev.evidence_key}</span>
                      <span className="text-slate-300 font-medium">{ev.source}</span>
                    </div>
                    <Badge label={ev.kind} variant="default" />
                  </div>
                  <pre className="p-2 rounded bg-slate-900 text-[11px] font-mono text-slate-400 overflow-x-auto">
                    {JSON.stringify(ev.value, null, 2)}
                  </pre>
                  <div className="text-[10px] font-mono text-slate-500 flex items-center justify-between">
                    <span>SHA-256: {ev.checksum.slice(0, 16)}...</span>
                    <span>Captured: {new Date(ev.captured_at).toLocaleTimeString()}</span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {activeTab === 'raw' && (
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 flex flex-col gap-4">
          <h3 className="font-semibold text-sm text-slate-200">Original Alert Payload</h3>
          <pre className="p-4 rounded-lg bg-slate-950 font-mono text-xs text-sky-300/90 overflow-x-auto border border-slate-800 leading-relaxed">
            {JSON.stringify(alert.raw_event, null, 2)}
          </pre>
        </div>
      )}
    </div>
  );
};
