import { FormEvent, useState } from 'react';
import { scanUrl } from '../../lib/api';
import type { ScannerFormProps } from './types';

export function UrlScanForm({ disabled, run }: ScannerFormProps) {
  const [url, setUrl] = useState('');
  function submit(event: FormEvent) { event.preventDefault(); run(() => scanUrl(url.trim())); }
  return <form className="scan-form" onSubmit={submit}><label>URL to scan<input value={url} onChange={(event) => setUrl(event.target.value)} placeholder="https://example.com" inputMode="url" required /></label><button className="primary-btn" disabled={disabled || !url.trim()}>Scan URL</button></form>;
}
