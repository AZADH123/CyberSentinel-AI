export interface HealthStatus {
  status: 'ok' | 'degraded' | 'error';
  version: string;
  checks: {
    database: {
      status: 'ok' | 'error';
      latency_ms: number | null;
      detail?: string;
    };
    enrichment: {
      mode: 'live' | 'mock' | 'off';
      configured: boolean;
    };
    llm: {
      enabled: boolean;
      configured: boolean;
    };
  };
}

export interface AlertListItem {
  alert_id: string;
  source: string;
  event_type: string;
  event_time: string;
  username: string;
  source_ip: string;
  host: string;
  outcome: string;
  failure_count: number;
  severity: 'informational' | 'low' | 'medium' | 'high';
  risk_score: number;
  status: string;
  confidence: 'low' | 'medium' | 'high';
  created_at: string;
}

export interface AlertListResponse {
  items: AlertListItem[];
  next_cursor: string | null;
}

export interface AlertDetail {
  alert_id: string;
  source: string;
  event_type: string;
  event_time: string;
  raw_event: Record<string, unknown>;
  normalized_event: {
    event_time: string;
    username: string;
    source_ip: string;
    host: string;
    action: string;
    outcome: string;
    asset_criticality: string;
    failure_count: number;
  };
  incident: {
    incident_id: string;
    status: string;
    severity: string;
    risk_score: number;
    risk_band: string;
    confidence: string;
    created_at: string;
  };
  duplicate_of: string | null;
  created_at: string;
}

export interface AlertCreatePayload {
  source: string;
  event_type: string;
  event_time: string;
  username: string;
  source_ip: string;
  host: string;
  outcome: string;
  failure_count: number;
  asset_criticality: string;
  raw_event: Record<string, unknown>;
  idempotency_key?: string;
}

export interface AlertCreateResponse {
  alert_id: string;
  incident_id: string;
  status: string;
  event_time: string;
  created_at: string;
  duplicate_of: string | null;
}

export interface IncidentSummary {
  incident_id: string;
  status: string;
  severity: 'informational' | 'low' | 'medium' | 'high';
  risk_score: number;
  risk_band: 'informational' | 'low' | 'medium' | 'high';
  confidence: 'low' | 'medium' | 'high';
  created_at: string;
}

export interface IncidentListResponse {
  items: IncidentSummary[];
  next_cursor: string | null;
}

export interface EvidenceItem {
  id: string;
  investigation_id: string;
  evidence_key: string;
  kind: string;
  source: string;
  reference: string;
  captured_at: string;
  value: Record<string, unknown>;
  checksum: string;
  supersedes: string | null;
}

export interface IncidentDetail {
  incident_id: string;
  alert_id: string;
  status: string;
  severity: 'informational' | 'low' | 'medium' | 'high';
  risk_score: number;
  risk_band: 'informational' | 'low' | 'medium' | 'high';
  confidence: 'low' | 'medium' | 'high';
  created_at: string;
  updated_at: string;
  alert_summary?: {
    alert_id: string;
    source: string;
    event_type: string;
    event_time: string;
    username: string;
    host: string;
    source_ip: string;
    outcome: string;
    failure_count: number;
  };
  latest_investigation_id?: string | null;
  investigation_status?: string | null;
  report?: {
    incident_id: string;
    investigation_id: string;
    summary: string;
    risk_assessment: {
      score: number;
      band: string;
      confidence: string;
      factors: Array<{
        rule_id: string;
        label: string;
        points: number;
        evidence_refs: string[];
      }>;
    };
    attack_candidates: Array<{
      technique_id: string;
      technique_name: string;
      tactic: string;
      confidence: string;
      rationale: string;
      url: string;
      evidence_refs: string[];
    }>;
    gaps: string[];
    generated_at: string;
  } | null;
  reviews: Array<{
    id: string;
    reviewer: string;
    disposition: 'accept' | 'reject' | 'escalate';
    notes: string | null;
    reviewed_at: string;
  }>;
}

export interface InvestigationStartResponse {
  investigation_id: string;
  status: string;
  started_at: string;
  poll: string;
}

export interface InvestigationDetail {
  investigation_id: string;
  status: 'queued' | 'running' | 'completed' | 'completed_degraded' | 'failed' | 'cancelled' | 'interrupted';
  progress: {
    completed_nodes: string[];
    current_node: string | null;
    elapsed_ms: number;
  };
  trace: Array<{
    node: string;
    outcome: string;
    duration_ms: number;
    detail?: string | null;
  }>;
  report?: Record<string, unknown> | null;
  created_at: string;
  started_at?: string | null;
  completed_at?: string | null;
  error_summary?: string | null;
}

export interface ReviewPayload {
  reviewer: string;
  disposition: 'accept' | 'reject' | 'escalate';
  notes?: string;
}

export interface ReviewResponse {
  incident_id: string;
  disposition: string;
  reviewer: string;
  reviewed_at: string;
  incident_status: string;
  executed_actions: string[];
}
