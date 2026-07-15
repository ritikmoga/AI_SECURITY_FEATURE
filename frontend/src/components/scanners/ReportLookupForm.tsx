import { FormEvent, useState } from 'react';
import { fetchReport } from '../../lib/api';
import type { ScannerFormProps } from './types';

export function ReportLookupForm({ disabled, run }: ScannerFormProps) {
  const [scanId, setScanId] = useState('');
  function submit(event: FormEvent) { event.preventDefault(); run(() => fetchReport(scanId)); }
  return <form className="scan-form" onSubmit={submit}><label>Scan report ID<input value={scanId} onChange={(event) => setScanId(event.target.value)} placeholder="Paste a scan ID" required /></label><button className="primary-btn" disabled={disabled || !scanId.trim()}>Fetch Report</button></form>;
}
