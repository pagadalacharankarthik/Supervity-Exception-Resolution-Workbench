import type {
  User, Exception, ExceptionDetail, DashboardStats,
  DashboardTrend, DashboardAnalytics, PaginatedExceptions,
  Policy, PolicyDecision, AuditEvent, Investigation, Document
} from '../types';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000/api';

function getHeaders(isMultipart = false): HeadersInit {
  const headers: Record<string, string> = {};
  if (!isMultipart) {
    headers['Content-Type'] = 'application/json';
  }
  const token = localStorage.getItem('supervity_token');
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  return headers;
}

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    let errorMessage = 'An error occurred';
    try {
      const data = await response.json();
      errorMessage = data.detail || errorMessage;
    } catch {
      errorMessage = response.statusText || errorMessage;
    }
    throw new Error(errorMessage);
  }
  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}

export const api = {
  // ── Auth ──────────────────────────────────────────────────────────────────
  async login(email: string, password: string): Promise<{ access_token: string; token_type: string }> {
    const res = await fetch(`${API_BASE_URL}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
    });
    return handleResponse(res);
  },

  async getMe(): Promise<User> {
    const res = await fetch(`${API_BASE_URL}/auth/me`, { headers: getHeaders() });
    return handleResponse(res);
  },

  async logout(): Promise<void> {
    await fetch(`${API_BASE_URL}/auth/logout`, { method: 'POST', headers: getHeaders() });
  },

  // ── Dashboard ─────────────────────────────────────────────────────────────
  async getStats(): Promise<DashboardStats> {
    const res = await fetch(`${API_BASE_URL}/dashboard/stats`, { headers: getHeaders() });
    return handleResponse(res);
  },

  async getTrend(): Promise<DashboardTrend> {
    const res = await fetch(`${API_BASE_URL}/dashboard/trend`, { headers: getHeaders() });
    return handleResponse(res);
  },

  async getAnalytics(): Promise<DashboardAnalytics> {
    const res = await fetch(`${API_BASE_URL}/dashboard/analytics`, { headers: getHeaders() });
    return handleResponse(res);
  },

  // ── Exceptions ────────────────────────────────────────────────────────────
  async listExceptions(filters?: {
    page?: number;
    page_size?: number;
    search?: string;
    status?: string;
    risk?: string;
    type?: string;
    severity?: string;
    sort_by?: string;
    sort_order?: string;
  }): Promise<PaginatedExceptions> {
    const params = new URLSearchParams();
    if (filters?.page) params.append('page', filters.page.toString());
    if (filters?.page_size) params.append('page_size', filters.page_size.toString());
    if (filters?.search) params.append('search', filters.search);
    if (filters?.status) params.append('status_filter', filters.status);
    if (filters?.risk) params.append('risk_filter', filters.risk);
    if (filters?.type) params.append('type_filter', filters.type);
    if (filters?.severity) params.append('severity_filter', filters.severity);
    if (filters?.sort_by) params.append('sort_by', filters.sort_by);
    if (filters?.sort_order) params.append('sort_order', filters.sort_order);
    const qs = params.toString() ? `?${params.toString()}` : '';
    const res = await fetch(`${API_BASE_URL}/exceptions${qs}`, { headers: getHeaders() });
    return handleResponse(res);
  },

  async triggerDetection(): Promise<{ detected: number; new_exceptions: number; existing_exceptions: number }> {
    const res = await fetch(`${API_BASE_URL}/exceptions/detect`, { method: 'POST', headers: getHeaders() });
    return handleResponse(res);
  },

  async getException(id: string): Promise<ExceptionDetail> {
    const res = await fetch(`${API_BASE_URL}/exceptions/${id}`, { headers: getHeaders() });
    return handleResponse(res);
  },

  // ── AI Investigation ──────────────────────────────────────────────────────
  async runInvestigation(id: string): Promise<Investigation> {
    const res = await fetch(`${API_BASE_URL}/exceptions/${id}/investigate`, {
      method: 'POST',
      headers: getHeaders(),
    });
    return handleResponse(res);
  },

  async sendChat(id: string, messages: Array<{ sender: string; text: string }>, userMessage: string): Promise<{ reply: string }> {
    const res = await fetch(`${API_BASE_URL}/exceptions/${id}/chat`, {
      method: 'POST',
      headers: getHeaders(),
      body: JSON.stringify({ messages, user_message: userMessage }),
    });
    return handleResponse(res);
  },

  // ── Policy Engine ─────────────────────────────────────────────────────────
  async evaluatePolicy(id: string): Promise<PolicyDecision> {
    const res = await fetch(`${API_BASE_URL}/exceptions/${id}/evaluate-policy`, {
      method: 'POST',
      headers: getHeaders(),
    });
    return handleResponse(res);
  },

  async getPolicyDecision(id: string): Promise<PolicyDecision | null> {
    const res = await fetch(`${API_BASE_URL}/exceptions/${id}/decision`, { headers: getHeaders() });
    if (res.status === 404) return null;
    return handleResponse(res);
  },

  async listPolicies(): Promise<Policy[]> {
    const res = await fetch(`${API_BASE_URL}/policies`, { headers: getHeaders() });
    return handleResponse(res);
  },

  async updatePolicy(id: string, rules: Record<string, any>, isActive?: boolean): Promise<Policy> {
    const res = await fetch(`${API_BASE_URL}/policies/${id}`, {
      method: 'PUT',
      headers: getHeaders(),
      body: JSON.stringify({ rules, is_active: isActive }),
    });
    return handleResponse(res);
  },

  // ── Resolution ────────────────────────────────────────────────────────────
  async resolveException(id: string, comments: string): Promise<Resolution> {
    const res = await fetch(`${API_BASE_URL}/exceptions/${id}/resolve`, {
      method: 'POST',
      headers: getHeaders(),
      body: JSON.stringify({ action: 'RESOLVE', comments }),
    });
    return handleResponse(res);
  },

  async rejectException(id: string, reason: string): Promise<Resolution> {
    const res = await fetch(`${API_BASE_URL}/exceptions/${id}/reject`, {
      method: 'POST',
      headers: getHeaders(),
      body: JSON.stringify({ reason }),
    });
    return handleResponse(res);
  },

  async escalateException(id: string, reason: string): Promise<Resolution> {
    const res = await fetch(`${API_BASE_URL}/exceptions/${id}/escalate`, {
      method: 'POST',
      headers: getHeaders(),
      body: JSON.stringify({ reason }),
    });
    return handleResponse(res);
  },

  async markFalsePositive(id: string, reason: string): Promise<Resolution> {
    const res = await fetch(`${API_BASE_URL}/exceptions/${id}/false-positive`, {
      method: 'POST',
      headers: getHeaders(),
      body: JSON.stringify({ reason }),
    });
    return handleResponse(res);
  },

  async autoResolveException(id: string): Promise<Resolution> {
    const res = await fetch(`${API_BASE_URL}/exceptions/${id}/auto-resolve`, {
      method: 'POST',
      headers: getHeaders(),
    });
    return handleResponse(res);
  },

  // ── Audit ─────────────────────────────────────────────────────────────────
  async getGlobalAuditLogs(): Promise<AuditEvent[]> {
    const res = await fetch(`${API_BASE_URL}/audit/logs`, { headers: getHeaders() });
    return handleResponse(res);
  },

  // ── Documents ─────────────────────────────────────────────────────────────
  async listDocuments(): Promise<Document[]> {
    const res = await fetch(`${API_BASE_URL}/documents`, { headers: getHeaders() });
    return handleResponse(res);
  },

  async getDocument(id: string): Promise<Document> {
    const res = await fetch(`${API_BASE_URL}/documents/${id}`, { headers: getHeaders() });
    return handleResponse(res);
  },

  async uploadDocument(file: File, documentType = 'INVOICE'): Promise<Document> {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('document_type', documentType);
    const res = await fetch(`${API_BASE_URL}/documents/upload`, {
      method: 'POST',
      headers: getHeaders(true),
      body: formData,
    });
    return handleResponse(res);
  },

  async verifyDocumentField(docId: string, fieldId: string): Promise<any> {
    const res = await fetch(`${API_BASE_URL}/documents/${docId}/fields/${fieldId}/verify`, {
      method: 'POST',
      headers: getHeaders(),
    });
    return handleResponse(res);
  },

  async editDocumentField(docId: string, fieldId: string, newValue: string, reason?: string): Promise<any> {
    const res = await fetch(`${API_BASE_URL}/documents/${docId}/fields/${fieldId}/edit`, {
      method: 'POST',
      headers: getHeaders(),
      body: JSON.stringify({ new_value: newValue, reason }),
    });
    return handleResponse(res);
  },

  async flagDocumentField(docId: string, fieldId: string): Promise<any> {
    const res = await fetch(`${API_BASE_URL}/documents/${docId}/fields/${fieldId}/flag`, {
      method: 'POST',
      headers: getHeaders(),
    });
    return handleResponse(res);
  },

  async verifyDocument(id: string): Promise<Document> {
    const res = await fetch(`${API_BASE_URL}/documents/${id}/verify`, {
      method: 'POST',
      headers: getHeaders(),
    });
    return handleResponse(res);
  },

  getDocumentPreviewUrl(id: string): string {
    const token = localStorage.getItem('supervity_token');
    return `${API_BASE_URL}/documents/${id}/preview?token=${token}`;
  },
};
