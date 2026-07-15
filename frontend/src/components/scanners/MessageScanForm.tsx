import { FormEvent, useState } from 'react';
import { scanMessage } from '../../lib/api';
import type { ScannerFormProps } from './types';

export function MessageScanForm({ disabled, run }: ScannerFormProps) {
  const [subject, setSubject] = useState(''); const [body, setBody] = useState(''); const [attachments, setAttachments] = useState('');
  function submit(event: FormEvent) { event.preventDefault(); const list = attachments.split(',').map((filename) => filename.trim()).filter(Boolean).map((filename) => ({ filename })); run(() => scanMessage({ subject, body, attachments: list })); }
  return <form className="scan-form" onSubmit={submit}><label>Subject<input value={subject} onChange={(event) => setSubject(event.target.value)} placeholder="Payment alert / account notice" /></label><label>Message body<textarea value={body} onChange={(event) => setBody(event.target.value)} placeholder="Paste a message or email text here." rows={8} required /></label><label>Attachment filenames, optional<input value={attachments} onChange={(event) => setAttachments(event.target.value)} placeholder="invoice.pdf, document.docm" /></label><button className="primary-btn" disabled={disabled || !body.trim()}>Scan Message</button></form>;
}
