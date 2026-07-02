import type { ScanReport } from '../types';

const KEY = 'scamshield.scan.history.v1';
const LIMIT = 12;

export function readHistory(): ScanReport[] {
  try {
    const raw = window.localStorage.getItem(KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

export function saveReportToHistory(report: ScanReport): ScanReport[] {
  const current = readHistory();
  const deduped = current.filter((item) => item.scan_id !== report.scan_id);
  const next = [report, ...deduped].slice(0, LIMIT);
  window.localStorage.setItem(KEY, JSON.stringify(next));
  return next;
}

export function clearHistory(): void {
  window.localStorage.removeItem(KEY);
}
