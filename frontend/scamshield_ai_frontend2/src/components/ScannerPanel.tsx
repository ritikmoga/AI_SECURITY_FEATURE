import { FormEvent, useState } from 'react';
import { decodeQrImage } from '../lib/qr';
import { fetchReport, scanFile, scanMessage, scanQrText, scanUrl } from '../lib/api';
import type { ScanReport, ScannerTab } from '../types';

type ScannerPanelProps = {
  activeTab: ScannerTab;
  setActiveTab: (tab: ScannerTab) => void;
  onReport: (report: ScanReport) => void;
};

const tabs: Array<{ id: ScannerTab; label: string; helper: string }> = [
  { id: 'url', label: 'URL', helper: 'Link reputation and pattern scan' },
  { id: 'message', label: 'Message', helper: 'Phishing-style text analysis' },
  { id: 'file', label: 'File', helper: 'Safe static file inspection' },
  { id: 'qr', label: 'QR', helper: 'Decoded QR text analysis' },
  { id: 'report', label: 'Report', helper: 'Fetch previous scan ID' }
];

export function ScannerPanel({ activeTab, setActiveTab, onReport }: ScannerPanelProps) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  async function run(task: () => Promise<ScanReport>) {
    setLoading(true);
    setError('');
    try {
      const report = await task();
      onReport(report);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Scan failed.');
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="panel scanner-panel">
      <div className="section-title-row">
        <div>
          <p className="eyebrow">Scanner console</p>
          <h2>Choose an input type</h2>
        </div>
        {loading ? <span className="loading-pill">Scanning...</span> : null}
      </div>

      <div className="tabs" role="tablist" aria-label="Scanner types">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            className={activeTab === tab.id ? 'tab active' : 'tab'}
            type="button"
            onClick={() => {
              setActiveTab(tab.id);
              setError('');
            }}
          >
            <strong>{tab.label}</strong>
            <span>{tab.helper}</span>
          </button>
        ))}
      </div>

      {activeTab === 'url' ? <UrlScanner disabled={loading} run={run} /> : null}
      {activeTab === 'message' ? <MessageScanner disabled={loading} run={run} /> : null}
      {activeTab === 'file' ? <FileScanner disabled={loading} run={run} /> : null}
      {activeTab === 'qr' ? <QrScanner disabled={loading} run={run} setError={setError} /> : null}
      {activeTab === 'report' ? <ReportScanner disabled={loading} run={run} /> : null}

      {error ? <div className="alert error">{error}</div> : null}
    </section>
  );
}

function UrlScanner({ disabled, run }: { disabled: boolean; run: (task: () => Promise<ScanReport>) => void }) {
  const [url, setUrl] = useState('');

  function submit(event: FormEvent) {
    event.preventDefault();
    run(() => scanUrl(url.trim()));
  }

  return (
    <form className="scan-form" onSubmit={submit}>
      <label>
        URL to scan
        <input
          value={url}
          onChange={(event) => setUrl(event.target.value)}
          placeholder="https://example.com"
          inputMode="url"
          required
        />
      </label>
      <button className="primary-btn" disabled={disabled || !url.trim()} type="submit">
        Scan URL
      </button>
    </form>
  );
}

function MessageScanner({ disabled, run }: { disabled: boolean; run: (task: () => Promise<ScanReport>) => void }) {
  const [subject, setSubject] = useState('');
  const [body, setBody] = useState('');
  const [attachments, setAttachments] = useState('');

  function submit(event: FormEvent) {
    event.preventDefault();
    const attachmentList = attachments
      .split(',')
      .map((filename) => filename.trim())
      .filter(Boolean)
      .map((filename) => ({ filename }));

    run(() => scanMessage({ subject, body, attachments: attachmentList }));
  }

  return (
    <form className="scan-form" onSubmit={submit}>
      <label>
        Subject
        <input value={subject} onChange={(event) => setSubject(event.target.value)} placeholder="Payment alert / account notice" />
      </label>
      <label>
        Message body
        <textarea
          value={body}
          onChange={(event) => setBody(event.target.value)}
          placeholder="Paste a message or email text here."
          rows={7}
          required
        />
      </label>
      <label>
        Attachment filenames, optional
        <input
          value={attachments}
          onChange={(event) => setAttachments(event.target.value)}
          placeholder="invoice.pdf, document.docm"
        />
      </label>
      <button className="primary-btn" disabled={disabled || !body.trim()} type="submit">
        Scan Message
      </button>
    </form>
  );
}

function FileScanner({ disabled, run }: { disabled: boolean; run: (task: () => Promise<ScanReport>) => void }) {
  const [file, setFile] = useState<File | null>(null);

  function submit(event: FormEvent) {
    event.preventDefault();
    if (!file) return;
    run(() => scanFile(file));
  }

  return (
    <form className="scan-form" onSubmit={submit}>
      <label className="drop-zone">
        <span>Upload a safe test file</span>
        <small>Backend performs static checks only. It does not execute files.</small>
        <input
          type="file"
          onChange={(event) => setFile(event.currentTarget.files?.[0] || null)}
        />
      </label>
      {file ? (
        <div className="file-preview">
          <strong>{file.name}</strong>
          <span>{(file.size / 1024).toFixed(1)} KB</span>
        </div>
      ) : null}
      <button className="primary-btn" disabled={disabled || !file} type="submit">
        Scan File
      </button>
    </form>
  );
}

function QrScanner({
  disabled,
  run,
  setError
}: {
  disabled: boolean;
  run: (task: () => Promise<ScanReport>) => void;
  setError: (message: string) => void;
}) {
  const [text, setText] = useState('');
  const [decoding, setDecoding] = useState(false);

  function submit(event: FormEvent) {
    event.preventDefault();
    run(() => scanQrText(text.trim()));
  }

  async function handleQrImage(file: File | undefined) {
    if (!file) return;
    setDecoding(true);
    setError('');
    try {
      const decoded = await decodeQrImage(file);
      setText(decoded);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'QR decoding failed.');
    } finally {
      setDecoding(false);
    }
  }

  return (
    <form className="scan-form" onSubmit={submit}>
      <label>
        QR decoded text or URL
        <textarea
          value={text}
          onChange={(event) => setText(event.target.value)}
          placeholder="Paste QR text here, or upload a QR image below to decode it in your browser."
          rows={5}
          required
        />
      </label>
      <label className="mini-upload">
        Decode QR image locally
        <input type="file" accept="image/*" onChange={(event) => handleQrImage(event.currentTarget.files?.[0])} />
      </label>
      <button className="primary-btn" disabled={disabled || decoding || !text.trim()} type="submit">
        {decoding ? 'Decoding...' : 'Scan QR Text'}
      </button>
    </form>
  );
}

function ReportScanner({ disabled, run }: { disabled: boolean; run: (task: () => Promise<ScanReport>) => void }) {
  const [scanId, setScanId] = useState('');

  function submit(event: FormEvent) {
    event.preventDefault();
    run(() => fetchReport(scanId));
  }

  return (
    <form className="scan-form" onSubmit={submit}>
      <label>
        Scan report ID
        <input value={scanId} onChange={(event) => setScanId(event.target.value)} placeholder="paste scan_id here" required />
      </label>
      <button className="primary-btn" disabled={disabled || !scanId.trim()} type="submit">
        Fetch Report
      </button>
    </form>
  );
}
