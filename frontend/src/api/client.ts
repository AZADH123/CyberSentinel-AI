import type {
  AlertCreatePayload,
  AlertCreateResponse,
  AlertDetail,
  AlertListResponse,
  EvidenceItem,
  HealthStatus,
  IncidentDetail,
  IncidentListResponse,
  InvestigationDetail,
  InvestigationStartResponse,
  ReviewPayload,
  ReviewResponse,
} from '../types';

export class ApiError extends Error {
  status: number;
  code: string;
  details?: Array<{ field?: string; issue?: string }>;

  constructor(
    status: number,
    code: string,
    message: string,
    details?: Array<{ field?: string; issue?: string }>
  ) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.code = code;
    this.details = details;
  }
}

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const headers = new Headers(options?.headers);
  if (!headers.has('Content-Type') && options?.body) {
    headers.set('Content-Type', 'application/json');
  }

  const response = await fetch(path, {
    ...options,
    headers,
  });

  if (!response.ok) {
    let errorData: { error?: { code?: string; message?: string; details?: Array<{ field?: string; issue?: string }> } } = {};
    try {
      errorData = await response.json();
    } catch {
      // not json
    }
    const code = errorData.error?.code || `HTTP_${response.status}`;
    const message = errorData.error?.message || response.statusText || 'Request failed';
    throw new ApiError(response.status, code, message, errorData.error?.details);
  }

  return response.json();
}

export const api = {
  getHealth: () => request<HealthStatus>('/health'),

  getAlerts: (params?: {
    limit?: number;
    cursor?: string;
    status?: string;
    severity?: string;
    source?: string;
  }) => {
    const q = new URLSearchParams();
    if (params?.limit) q.set('limit', String(params.limit));
    if (params?.cursor) q.set('cursor', params.cursor);
    if (params?.status) q.set('status', params.status);
    if (params?.severity) q.set('severity', params.severity);
    if (params?.source) q.set('source', params.source);
    const qs = q.toString();
    return request<AlertListResponse>(`/api/v1/alerts${qs ? `?${qs}` : ''}`);
  },

  getAlert: (alertId: string) => request<AlertDetail>(`/api/v1/alerts/${alertId}`),

  createAlert: (payload: AlertCreatePayload, idempotencyKey?: string) => {
    const headers: Record<string, string> = {};
    if (idempotencyKey) {
      headers['Idempotency-Key'] = idempotencyKey;
    }
    return request<AlertCreateResponse>('/api/v1/alerts', {
      method: 'POST',
      headers,
      body: JSON.stringify(payload),
    });
  },

  getIncidents: (params?: {
    limit?: number;
    cursor?: string;
    status?: string;
    severity?: string;
  }) => {
    const q = new URLSearchParams();
    if (params?.limit) q.set('limit', String(params.limit));
    if (params?.cursor) q.set('cursor', params.cursor);
    if (params?.status) q.set('status', params.status);
    if (params?.severity) q.set('severity', params.severity);
    const qs = q.toString();
    return request<IncidentListResponse>(`/api/v1/incidents${qs ? `?${qs}` : ''}`);
  },

  getIncident: (incidentId: string) => request<IncidentDetail>(`/api/v1/incidents/${incidentId}`),

  getIncidentEvidence: (incidentId: string, kind?: string) => {
    const q = kind ? `?kind=${encodeURIComponent(kind)}` : '';
    return request<EvidenceItem[]>(`/api/v1/incidents/${incidentId}/evidence${q}`);
  },

  startInvestigation: (alertId: string) =>
    request<InvestigationStartResponse>(`/api/v1/alerts/${alertId}/investigate`, {
      method: 'POST',
    }),

  getInvestigation: (investigationId: string) =>
    request<InvestigationDetail>(`/api/v1/investigations/${investigationId}`),

  submitReview: (incidentId: string, payload: ReviewPayload) =>
    request<ReviewResponse>(`/api/v1/incidents/${incidentId}/review`, {
      method: 'POST',
      body: JSON.stringify(payload),
    }),
};
