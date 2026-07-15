import { FormEvent, useState } from 'react';
import { scanQrText } from '../../lib/api';
import { decodeQrImage } from '../../lib/qr';
import type { ScannerFormProps } from './types';

export function QrScanForm({ disabled, run }: ScannerFormProps) {
  const [text, setText] = useState(''); const [decoding, setDecoding] = useState(false); const [error, setError] = useState('');
  function submit(event: FormEvent) { event.preventDefault(); run(() => scanQrText(text.trim())); }
  async function decode(file?: File) { if (!file) return; setDecoding(true); setError(''); try { setText(await decodeQrImage(file)); } catch (err) { setError(err instanceof Error ? err.message : 'QR decoding failed.'); } finally { setDecoding(false); } }
  return <form className="scan-form" onSubmit={submit}><label>QR decoded text or URL<textarea value={text} onChange={(event) => setText(event.target.value)} placeholder="Paste QR text, or decode an image below." rows={6} required /></label><label className="mini-upload">Decode QR image locally<input type="file" accept="image/*" onChange={(event) => decode(event.currentTarget.files?.[0])} /></label>{error ? <div className="alert error">{error}</div> : null}<button className="primary-btn" disabled={disabled || decoding || !text.trim()}>{decoding ? 'Decoding...' : 'Scan QR Text'}</button></form>;
}
