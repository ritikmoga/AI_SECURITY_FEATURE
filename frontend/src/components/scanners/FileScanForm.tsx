import { FormEvent, useState } from 'react';
import { scanFile } from '../../lib/api';
import type { ScannerFormProps } from './types';

export function FileScanForm({ disabled, run }: ScannerFormProps) {
  const [file, setFile] = useState<File | null>(null);
  function submit(event: FormEvent) { event.preventDefault(); if (file) run(() => scanFile(file)); }
  return <form className="scan-form" onSubmit={submit}><label className="drop-zone"><span>Upload a safe test file</span><small>The backend performs static checks only and never executes uploads.</small><input type="file" onChange={(event) => setFile(event.currentTarget.files?.[0] || null)} /></label>{file ? <div className="file-preview"><strong>{file.name}</strong><span>{(file.size / 1024).toFixed(1)} KB</span></div> : null}<button className="primary-btn" disabled={disabled || !file}>Scan File</button></form>;
}
