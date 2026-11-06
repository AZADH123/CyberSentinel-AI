import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { ArrowLeft, CheckCircle, AlertTriangle, ShieldCheck } from 'lucide-react';
import { api } from '../api/client';
import { Badge } from '../components/Badge';
import { RiskMeter } from '../components/RiskMeter';

interface ReviewPageProps {
  incidentId: string;
  onBack: () => void;
  onSuccess: () => void;
}

export const ReviewPage: React.FC<ReviewPageProps> = ({
  incidentId,
  onBack,
  onSuccess,
}) => {
  const queryClient = useQueryClient();
  const [reviewer, setReviewer] = useState('local-reviewer');
  const [disposition, setDisposition] = useState<'accept' | 'reject' | 'escalate'>('escalate');
  const [notes, setNotes] = useState('');
  const [formError, setFormError] = useState<string | null>(null);

  const { data: incident, isLoading } = useQuery({
    queryKey: ['incident', incidentId],
    queryFn: () => api.getIncident(incidentId),
  });

  const reviewMutation = useMutation({
    mutationFn: () =>
      api.submitReview(incidentId, {
        reviewer,
        disposition,
        notes: notes.trim() || undefined,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['incident', incidentId] });
      queryClient.invalidateQueries({ queryKey: ['incidents'] });
      queryClient.invalidateQueries({ queryKey: ['alerts'] });
      onSuccess();
    },
    onError: (err: unknown) => {
      if (err instanceof Error) {
        setFormError(err.message);
      } else {
        setFormError('Failed to record review decision');
      }
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setFormError(null);

    if (disposition === 'reject' || disposition === 'escalate') {
      if (!notes.trim()) {
        setFormError(`Notes are required when rejecting or escalating an incident.`);
        return;
      }
    }

    reviewMutation.mutate();
  };

  const isAlreadyReviewed =
    incident?.status === 'accepted' ||
    incident?.status === 'rejected' ||
    incident?.status === 'escalated';

  return (
    <div className="flex flex-col gap-6 max-w-3xl mx-auto w-full">
      <button
        onClick={onBack}
        className="text-slate-400 hover:text-slate-200 flex items-center gap-1.5 text-xs font-medium self-start"
      >
        <ArrowLeft className="w-4 h-4" />
        Back
      </button>

      <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 flex flex-col gap-5 shadow-2xl">
        <div className="border-b border-slate-800 pb-4 flex items-center justify-between">
          <div>
            <h2 className="text-lg font-bold text-slate-100 flex items-center gap-2">
              <ShieldCheck className="w-5 h-5 text-indigo-400" />
              Human Disposition Review
            </h2>
            <p className="text-xs text-slate-400 mt-0.5">
              Target Incident: <span className="font-mono text-sky-400 font-semibold">{incidentId}</span>
            </p>
          </div>

          {incident && (
            <div className="flex items-center gap-2">
              <Badge label={incident.status} variant="status" />
              <Badge label={incident.severity} variant="severity" />
            </div>
          )}
        </div>

        {/* Incident Summary Card */}
        {incident && (
          <div className="bg-slate-950/70 p-4 rounded-lg border border-slate-800/80 flex items-center justify-between text-xs">
            <div>
              <span className="text-slate-500 block">User & Host</span>
              <span className="font-semibold text-slate-200">
                {incident.alert_summary?.username || 'Unknown'} @ {incident.alert_summary?.host || 'Unknown'}
              </span>
            </div>
            <div>
              <span className="text-slate-500 block">Failures</span>
              <span className="font-mono text-amber-400 font-bold">
                {incident.alert_summary?.failure_count || 0}
              </span>
            </div>
            <div>
              <span className="text-slate-500 block mb-1">Risk Score</span>
              <RiskMeter score={incident.risk_score} band={incident.risk_band} />
            </div>
          </div>
        )}

        {isAlreadyReviewed ? (
          <div className="p-4 bg-emerald-950/30 border border-emerald-800/50 rounded-lg text-emerald-300 text-xs flex items-center gap-3">
            <CheckCircle className="w-5 h-5 text-emerald-400 shrink-0" />
            <div>
              <p className="font-semibold">Incident is already resolved</p>
              <p className="text-[11px] text-emerald-400/80 mt-0.5">
                Current status is <strong>{incident?.status}</strong>. Decisions are immutable and recorded in the audit log.
              </p>
            </div>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="flex flex-col gap-4 text-xs">
            {formError && (
              <div className="p-3 bg-red-950/50 border border-red-800/70 rounded-lg text-red-300 flex items-start gap-2">
                <AlertTriangle className="w-4 h-4 text-red-400 shrink-0 mt-0.5" />
                <span>{formError}</span>
              </div>
            )}

            <div>
              <label className="block text-slate-300 font-medium mb-1.5">Reviewer Identity</label>
              <input
                type="text"
                className="w-full bg-slate-800/80 border border-slate-700 rounded-lg px-3 py-2 text-slate-200 focus:outline-none focus:border-sky-500"
                value={reviewer}
                onChange={(e) => setReviewer(e.target.value)}
                required
              />
            </div>

            <div>
              <label className="block text-slate-300 font-medium mb-1.5">Review Disposition</label>
              <div className="grid grid-cols-3 gap-3">
                <button
                  type="button"
                  onClick={() => setDisposition('accept')}
                  className={`p-3 rounded-lg border text-left flex flex-col gap-1 transition ${
                    disposition === 'accept'
                      ? 'bg-emerald-950/50 border-emerald-600 text-emerald-300'
                      : 'bg-slate-800/50 border-slate-700 text-slate-400 hover:border-slate-600'
                  }`}
                >
                  <span className="font-bold text-sm">Accept</span>
                  <span className="text-[11px] text-slate-400">Confirm alert & close incident</span>
                </button>

                <button
                  type="button"
                  onClick={() => setDisposition('reject')}
                  className={`p-3 rounded-lg border text-left flex flex-col gap-1 transition ${
                    disposition === 'reject'
                      ? 'bg-slate-800 border-slate-500 text-slate-200'
                      : 'bg-slate-800/50 border-slate-700 text-slate-400 hover:border-slate-600'
                  }`}
                >
                  <span className="font-bold text-sm">Reject</span>
                  <span className="text-[11px] text-slate-400">False positive (notes required)</span>
                </button>

                <button
                  type="button"
                  onClick={() => setDisposition('escalate')}
                  className={`p-3 rounded-lg border text-left flex flex-col gap-1 transition ${
                    disposition === 'escalate'
                      ? 'bg-rose-950/50 border-rose-600 text-rose-300'
                      : 'bg-slate-800/50 border-slate-700 text-slate-400 hover:border-slate-600'
                  }`}
                >
                  <span className="font-bold text-sm">Escalate</span>
                  <span className="text-[11px] text-slate-400">Tier-2 escalation (notes required)</span>
                </button>
              </div>
            </div>

            <div>
              <label className="block text-slate-300 font-medium mb-1.5">
                Review Notes{' '}
                {(disposition === 'reject' || disposition === 'escalate') && (
                  <span className="text-amber-400 font-normal">(Required)</span>
                )}
              </label>
              <textarea
                rows={4}
                className="w-full bg-slate-800/80 border border-slate-700 rounded-lg p-3 text-slate-200 focus:outline-none focus:border-sky-500 font-sans"
                placeholder={
                  disposition === 'escalate'
                    ? 'Explain reasons for escalation, unusual context, or accounts to investigate...'
                    : disposition === 'reject'
                    ? 'Explain justification for false positive dismissal...'
                    : 'Optional observations or verification steps...'
                }
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
              />
            </div>

            <div className="flex items-center justify-end gap-3 pt-4 border-t border-slate-800">
              <button
                type="button"
                onClick={onBack}
                className="px-4 py-2 rounded-lg text-slate-400 hover:text-slate-200"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={reviewMutation.isPending || isLoading}
                className="px-5 py-2 rounded-lg bg-sky-500 hover:bg-sky-400 text-slate-950 font-bold transition disabled:opacity-50"
              >
                {reviewMutation.isPending ? 'Submitting...' : 'Commit Decision'}
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
};
