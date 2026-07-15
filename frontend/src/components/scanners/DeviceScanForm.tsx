import { FormEvent, useEffect, useRef, useState } from 'react';
import { scanDeviceFiles } from '../../lib/api';
import type { ScannerFormProps } from './types';

export function DeviceScanForm({ disabled, run }: ScannerFormProps) {
  const input = useRef<HTMLInputElement>(null); const [files, setFiles] = useState<File[]>([]);
  useEffect(() => { input.current?.setAttribute('webkitdirectory', ''); input.current?.setAttribute('directory', ''); }, []);
  function submit(event: FormEvent) { event.preventDefault(); if (files.length) run(() => scanDeviceFiles(files)); }
  return <form className="scan-form" onSubmit={submit}>
    <div className="alert device-notice"><strong>Consent-based device scan</strong><br />Select a folder you own. The browser can only scan files you explicitly select; files are analyzed statically and are never executed. Messages require an export you choose to upload or paste.</div>
    <label className="drop-zone"><span>Select a folder to scan</span><small>Up to 100 files per run. Oversized files are skipped.</small><input ref={input} type="file" multiple onChange={(event) => setFiles(Array.from(event.currentTarget.files || []).slice(0, 100))} /></label>
    {files.length ? <div className="file-preview"><strong>{files.length} selected file(s)</strong><span>{files.slice(0, 2).map((file) => file.name).join(', ')}{files.length > 2 ? ' …' : ''}</span></div> : null}
    <button className="primary-btn" disabled={disabled || !files.length}>Run Local Device Scan</button>
  </form>;
}
