import type { ScanReport } from '../types';
import { RiskBadge } from './RiskBadge';

type Props = {
  reports: ScanReport[];
  onSelect: (report: ScanReport) => void;
  onClear: () => void;
};

export function HistoryPanel({ reports, onSelect, onClear }: Props) {
  return (
    <section className="panel history-panel">
      <div className="section-title-row">
        <div>
          <p className="eyebrow">Local history</p>
          <h2>Recent scans</h2>
        </div>
        {reports.length > 0 ? (
          <button className="ghost-btn" onClick={onClear} type="button">
            Clear
          </button>
        ) : null}
      </div>

      {reports.length === 0 ? (
        <p className="muted">Recent reports are saved in your browser only.</p>
      ) : (
        <div className="history-list">
          {reports.map((report) => (
            <button key={report.scan_id} className="history-item" type="button" onClick={() => onSelect(report)}>
              <span>{report.scan_type.toUpperCase()}</span>
              <strong>{report.target}</strong>
              <RiskBadge level={report.risk_level} />
            </button>
          ))}
        </div>
      )}
    </section>
  );
}
