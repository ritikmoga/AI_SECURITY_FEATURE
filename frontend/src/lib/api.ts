import type { AdminOverview, ApiEnvelope, AuthSession, HealthStatus, ScanReport } from '../types';

const DEFAULT_API_BASE = '';
export const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || DEFAULT_API_BASE).replace(/\/$/, '');
const SESSION_KEY = 'scamshield.auth.session.v1';

export function readSession(): AuthSession | null {
  try { return JSON.parse(localStorage.getItem(SESSION_KEY) || 'null'); } catch { return null; }
}

export function saveSession(session: AuthSession): void { localStorage.setItem(SESSION_KEY, JSON.stringify(session)); }
export function clearSession(): void { localStorage.removeItem(SESSION_KEY); }
function authHeaders(): HeadersInit {
  const token = readSession()?.token;
  return token ? { Authorization: `Bearer ${token}` } : {};
}

async function parseResponse<T>(response: Response): Promise<T> {
  let payload: ApiEnvelope<T> | T;
  try {
    payload = await response.json();
  } catch {
    throw new Error(`Server returned ${response.status}, but the body was not valid JSON.`);
  }

  if (!response.ok) {
    const envelope = payload as ApiEnvelope<T>;
    throw new Error(envelope.message || envelope.error || `Request failed with status ${response.status}.`);
  }

  const envelope = payload as ApiEnvelope<T>;
  if (envelope && typeof envelope === 'object' && 'status' in envelope && envelope.status === 'success' && 'data' in envelope) {
    return envelope.data as T;
  }

  return payload as T;
}

export async function getHealth(): Promise<HealthStatus> {
  const response = await fetch(`${API_BASE_URL}/api/health`);
  return parseResponse<HealthStatus>(response);
}

export async function scanUrl(url: string): Promise<ScanReport> {
  const response = await fetch(`${API_BASE_URL}/api/scan/url`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...authHeaders() },
    body: JSON.stringify({ url })
  });
  return parseResponse<ScanReport>(response);
}

export async function scanMessage(payload: { subject: string; body: string; attachments: Array<{ filename: string }> }): Promise<ScanReport> {
  const response = await fetch(`${API_BASE_URL}/api/scan/message`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...authHeaders() },
    body: JSON.stringify(payload)
  });
  return parseResponse<ScanReport>(response);
}

export async function scanQrText(text: string): Promise<ScanReport> {
  const response = await fetch(`${API_BASE_URL}/api/scan/qr`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...authHeaders() },
    body: JSON.stringify({ text })
  });
  return parseResponse<ScanReport>(response);
}

export async function scanFile(file: File): Promise<ScanReport> {
  const form = new FormData();
  form.append('file', file);
  const response = await fetch(`${API_BASE_URL}/api/scan/file`, {
    method: 'POST', headers: authHeaders(),
    body: form
  });
  return parseResponse<ScanReport>(response);
}

export async function scanDeviceFiles(files: File[]): Promise<ScanReport> {
  const form = new FormData(); files.forEach((file) => form.append('files', file, file.webkitRelativePath || file.name));
  const response = await fetch(`${API_BASE_URL}/api/scan/device-files`, { method: 'POST', headers: authHeaders(), body: form });
  return parseResponse<ScanReport>(response);
}

export async function fetchReport(scanId: string): Promise<ScanReport> {
  const response = await fetch(`${API_BASE_URL}/api/scan/report/${encodeURIComponent(scanId.trim())}`, { headers: authHeaders() });
  return parseResponse<ScanReport>(response);
}

export async function googleSignIn(credential: string): Promise<AuthSession> {
  const response = await fetch(`${API_BASE_URL}/api/auth/google`, {
    method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ credential })
  });
  return parseResponse<AuthSession>(response);
}

export async function fetchUserReports(): Promise<ScanReport[]> {
  const response = await fetch(`${API_BASE_URL}/api/user/reports`, { headers: authHeaders() });
  return parseResponse<ScanReport[]>(response);
}

export async function fetchAdminOverview(): Promise<AdminOverview> {
  const response = await fetch(`${API_BASE_URL}/api/admin/overview`, { headers: authHeaders() });
  return parseResponse<AdminOverview>(response);
}

export async function exportUserReports(): Promise<Blob> {
  const response = await fetch(`${API_BASE_URL}/api/user/reports/export.csv`, { headers: authHeaders() });
  if (!response.ok) throw new Error('Could not export scan reports.');
  return response.blob();
}
