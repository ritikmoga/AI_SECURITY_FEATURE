import type { ApiEnvelope, HealthStatus, ScanReport } from '../types';

const DEFAULT_API_BASE = 'http://127.0.0.1:5001';
export const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || DEFAULT_API_BASE).replace(/\/$/, '');

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
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ url })
  });
  return parseResponse<ScanReport>(response);
}

export async function scanMessage(payload: { subject: string; body: string; attachments: Array<{ filename: string }> }): Promise<ScanReport> {
  const response = await fetch(`${API_BASE_URL}/api/scan/message`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  });
  return parseResponse<ScanReport>(response);
}

export async function scanQrText(text: string): Promise<ScanReport> {
  const response = await fetch(`${API_BASE_URL}/api/scan/qr`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text })
  });
  return parseResponse<ScanReport>(response);
}

export async function scanFile(file: File): Promise<ScanReport> {
  const form = new FormData();
  form.append('file', file);
  const response = await fetch(`${API_BASE_URL}/api/scan/file`, {
    method: 'POST',
    body: form
  });
  return parseResponse<ScanReport>(response);
}

export async function fetchReport(scanId: string): Promise<ScanReport> {
  const response = await fetch(`${API_BASE_URL}/api/scan/report/${encodeURIComponent(scanId.trim())}`);
  return parseResponse<ScanReport>(response);
}
