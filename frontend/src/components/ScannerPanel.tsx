import { useState } from 'react';
import { FileScanForm } from './scanners/FileScanForm';
import { DeviceScanForm } from './scanners/DeviceScanForm';
import { MessageScanForm } from './scanners/MessageScanForm';
import { QrScanForm } from './scanners/QrScanForm';
import { ReportLookupForm } from './scanners/ReportLookupForm';
import type { RunScan } from './scanners/types';
import { UrlScanForm } from './scanners/UrlScanForm';
import type { DashboardPage, ScanReport } from '../types';

const copy: Record<Exclude<DashboardPage, 'reports' | 'admin'>, { eyebrow: string; title: string; description: string }> = {
  url: { eyebrow: 'URL intelligence', title: 'Inspect a destination before opening it', description: 'Analyze link structure, redirect patterns, risky domains, and known social-engineering signals.' },
  message: { eyebrow: 'Message intelligence', title: 'Analyze suspicious messages', description: 'Review phishing language, embedded links, and attachment names without contacting the sender.' },
  file: { eyebrow: 'Static file analysis', title: 'Inspect a file safely', description: 'The scanner reads metadata and indicators only. Uploaded content is never executed.' },
  device: { eyebrow: 'Consent-based device scan', title: 'Inspect a folder you explicitly select', description: 'Browsers cannot read your full device or messages. Select a folder you own; files are statically analyzed and never executed.' },
  qr: { eyebrow: 'QR intelligence', title: 'Decode and inspect QR content', description: 'QR images are decoded in your browser; only their decoded text is sent for analysis.' },
  lookup: { eyebrow: 'Report retrieval', title: 'Open a previous scan report', description: 'Use the scan ID from any completed analysis to retrieve its full report.' }
};

export function ScannerPanel({ page, onReport }: { page: Exclude<DashboardPage, 'reports' | 'admin'>; onReport: (report: ScanReport) => void }) {
  const [loading, setLoading] = useState(false); const [error, setError] = useState(''); const details = copy[page];
  const run: RunScan = async (task) => { setLoading(true); setError(''); try { onReport(await task()); } catch (err) { setError(err instanceof Error ? err.message : 'Scan failed safely.'); } finally { setLoading(false); } };
  const props = { disabled: loading, run };
  return <section className="panel scanner-panel"><div className="section-title-row"><div><p className="eyebrow">{details.eyebrow}</p><h2>{details.title}</h2><p className="muted">{details.description}</p></div>{loading ? <span className="loading-pill">Analyzing…</span> : null}</div>{page === 'url' ? <UrlScanForm {...props} /> : null}{page === 'message' ? <MessageScanForm {...props} /> : null}{page === 'file' ? <FileScanForm {...props} /> : null}{page === 'device' ? <DeviceScanForm {...props} /> : null}{page === 'qr' ? <QrScanForm {...props} /> : null}{page === 'lookup' ? <ReportLookupForm {...props} /> : null}{error ? <div className="alert error">{error}</div> : null}</section>;
}
