import type { Finding, ScanReport } from '../types';
import { RiskGauge } from './RiskGauge';

function formatDate(value: string): string {
  try {
    return new Intl.DateTimeFormat(undefined, {
      dateStyle: 'medium',
      timeStyle: 'short'
    }).format(new Date(value));
  } catch {
    return value;
  }
}

function FindingRow({ finding }: { finding: Finding }) {
  const severity = String(finding.severity || 'info').toLowerCase();
  return (
    <article className={`finding severity-${severity}`}>
      <div>
        <span className="finding-severity">{finding.severity || 'info'}</span>
        <h4>{finding.title || finding.type || 'Finding'}</h4>
      </div>
      {finding.description ? <p>{finding.description}</p> : null}
      {finding.evidence ? <code>{finding.evidence}</code> : null}
      {typeof finding.score === 'number' ? <span className="finding-score">+{finding.score}</span> : null}
    </article>
  );
}

export function ResultCard({ report }: { report: ScanReport | null }) {
  if (!report) {
    return (
      <section className="panel empty-state">
        <div className="empty-orb">AI</div>
        <h3>No scan selected</h3>
        <p>Run a URL, message, file, or QR scan. The full security report will appear here.</p>
      </section>
    );
  }

  return (
    <section className="panel result-panel">
      <div className="result-head">
        <div>
          <p className="eyebrow">Scan report</p>
          <h2>{report.scan_type.toUpperCase()} analysis</h2>
          <p className="muted">{formatDate(report.created_at)} · ID: {report.scan_id}</p>
        </div>
      </div>

      <RiskGauge score={report.risk_score} level={report.risk_level} />

      <div className="report-grid">
        <div className="report-block">
          <span>Target</span>
          <strong>{report.target}</strong>
        </div>
        <div className="report-block">
          <span>Summary</span>
          <p>{report.summary}</p>
        </div>
        <div className="report-block wide">
          <span>Recommended action</span>
          <p>{report.recommended_action}</p>
        </div>
      </div>

      <div className="findings-list">
        <div className="section-title-row">
          <h3>Findings</h3>
          <span>{report.findings.length} item(s)</span>
        </div>
        {report.findings.length === 0 ? (
          <p className="muted">No local risk indicators were detected.</p>
        ) : (
          report.findings.map((finding, index) => <FindingRow key={`${finding.type || 'finding'}-${index}`} finding={finding} />)
        )}
      </div>

      {report.metadata && Object.keys(report.metadata).length > 0 ? (
        <details className="metadata-box">
          <summary>Metadata</summary>
          <pre>{JSON.stringify(report.metadata, null, 2)}</pre>
        </details>
      ) : null}

      {report.disclaimer ? <p className="disclaimer">{report.disclaimer}</p> : null}
    </section>
  );
}
