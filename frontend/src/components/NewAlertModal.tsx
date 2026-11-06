import React, { useState } from 'react';
import { X, Send, AlertCircle } from 'lucide-react';
import { api } from '../api/client';
import type { AlertCreatePayload } from '../types';

interface NewAlertModalProps {
  isOpen: boolean;
  onClose: () => void;
  onCreated: () => void;
}

export const NewAlertModal: React.FC<NewAlertModalProps> = ({ isOpen, onClose, onCreated }) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [form, setForm] = useState<AlertCreatePayload>({
    source: 'lab-auth-simulator',
    event_type: 'authentication',
    event_time: new Date().toISOString(),
    username: 'admin',
    source_ip: '198.51.100.24',
    host: 'vpn-01',
    outcome: 'failure',
    failure_count: 18,
    asset_criticality: 'high',
    raw_event: { message: 'Repeated authentication failures observed on remote access portal' },
  });

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      await api.createAlert({
        ...form,
        event_time: new Date().toISOString(),
      });
      onCreated();
      onClose();
    } catch (err: unknown) {
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError('Failed to create alert');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="bg-slate-900 border border-slate-800 rounded-xl max-w-lg w-full p-6 shadow-2xl flex flex-col gap-4 text-slate-200">
        <div className="flex items-center justify-between border-b border-slate-800 pb-3">
          <h3 className="font-semibold text-lg text-slate-100 flex items-center gap-2">
            Ingest Synthetic Alert
          </h3>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-slate-200 p-1 rounded hover:bg-slate-800"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {error && (
          <div className="p-3 bg-red-950/60 border border-red-800/80 rounded-lg text-sm text-red-300 flex items-start gap-2">
            <AlertCircle className="w-4 h-4 mt-0.5 text-red-400 shrink-0" />
            <div>
              <p className="font-medium">Failed to submit alert</p>
              <p className="text-xs text-red-400 mt-0.5">{error}</p>
            </div>
          </div>
        )}

        <form onSubmit={handleSubmit} className="flex flex-col gap-4 text-sm">
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-medium text-slate-400 mb-1">Source</label>
              <input
                type="text"
                className="w-full bg-slate-800/80 border border-slate-700 rounded px-2.5 py-1.5 text-slate-200"
                value={form.source}
                onChange={(e) => setForm({ ...form, source: e.target.value })}
                required
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-400 mb-1">Event Type</label>
              <select
                className="w-full bg-slate-800/80 border border-slate-700 rounded px-2.5 py-1.5 text-slate-200"
                value={form.event_type}
                onChange={(e) => setForm({ ...form, event_type: e.target.value })}
              >
                <option value="authentication">authentication</option>
                <option value="authorization">authorization</option>
                <option value="account_change">account_change</option>
              </select>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-medium text-slate-400 mb-1">Username</label>
              <input
                type="text"
                className="w-full bg-slate-800/80 border border-slate-700 rounded px-2.5 py-1.5 text-slate-200"
                value={form.username}
                onChange={(e) => setForm({ ...form, username: e.target.value })}
                required
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-400 mb-1">Source IP</label>
              <input
                type="text"
                className="w-full bg-slate-800/80 border border-slate-700 rounded px-2.5 py-1.5 text-slate-200"
                value={form.source_ip}
                onChange={(e) => setForm({ ...form, source_ip: e.target.value })}
                required
              />
            </div>
          </div>

          <div className="grid grid-cols-3 gap-3">
            <div>
              <label className="block text-xs font-medium text-slate-400 mb-1">Host</label>
              <input
                type="text"
                className="w-full bg-slate-800/80 border border-slate-700 rounded px-2.5 py-1.5 text-slate-200"
                value={form.host}
                onChange={(e) => setForm({ ...form, host: e.target.value })}
                required
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-400 mb-1">Outcome</label>
              <select
                className="w-full bg-slate-800/80 border border-slate-700 rounded px-2.5 py-1.5 text-slate-200"
                value={form.outcome}
                onChange={(e) => setForm({ ...form, outcome: e.target.value })}
              >
                <option value="failure">failure</option>
                <option value="success">success</option>
                <option value="unknown">unknown</option>
              </select>
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-400 mb-1">Failures</label>
              <input
                type="number"
                min={0}
                max={10000}
                className="w-full bg-slate-800/80 border border-slate-700 rounded px-2.5 py-1.5 text-slate-200"
                value={form.failure_count}
                onChange={(e) => setForm({ ...form, failure_count: parseInt(e.target.value) || 0 })}
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-400 mb-1">Asset Criticality</label>
            <select
              className="w-full bg-slate-800/80 border border-slate-700 rounded px-2.5 py-1.5 text-slate-200"
              value={form.asset_criticality}
              onChange={(e) => setForm({ ...form, asset_criticality: e.target.value })}
            >
              <option value="critical">critical</option>
              <option value="high">high</option>
              <option value="medium">medium</option>
              <option value="low">low</option>
            </select>
          </div>

          <div className="flex items-center justify-end gap-2.5 pt-3 border-t border-slate-800">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 rounded text-slate-400 hover:text-slate-200 hover:bg-slate-800"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              className="px-4 py-2 rounded bg-sky-500 hover:bg-sky-400 text-slate-950 font-semibold flex items-center gap-1.5 disabled:opacity-50"
            >
              <Send className="w-4 h-4" />
              {loading ? 'Submitting...' : 'Ingest Alert'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
