import { useMemo, useState } from 'react';
import { Hero } from './components/Hero';
import { HistoryPanel } from './components/HistoryPanel';
import { ResultCard } from './components/ResultCard';
import { ScannerPanel } from './components/ScannerPanel';
import { clearHistory, readHistory, saveReportToHistory } from './lib/history';
import type { ScanReport, ScannerTab } from './types';

export default function App() {
  const [activeTab, setActiveTab] = useState<ScannerTab>('url');
  const [selectedReport, setSelectedReport] = useState<ScanReport | null>(null);
  const [history, setHistory] = useState<ScanReport[]>(() => readHistory());

  const stats = useMemo(() => {
    const total = history.length;
    const risky = history.filter((item) => item.risk_level === 'High Risk' || item.risk_level === 'Dangerous').length;
    const average = total ? Math.round(history.reduce((sum, item) => sum + item.risk_score, 0) / total) : 0;
    return { total, risky, average };
  }, [history]);

  function handleReport(report: ScanReport) {
    setSelectedReport(report);
    setHistory(saveReportToHistory(report));
  }

  function handleClearHistory() {
    clearHistory();
    setHistory([]);
  }

  return (
    <main className="app-shell">
      <Hero />

      <section className="metrics-row" aria-label="Scanner metrics">
        <article className="metric-card">
          <span>Recent scans</span>
          <strong>{stats.total}</strong>
        </article>
        <article className="metric-card">
          <span>High-risk reports</span>
          <strong>{stats.risky}</strong>
        </article>
        <article className="metric-card">
          <span>Average score</span>
          <strong>{stats.average}</strong>
        </article>
      </section>

      <section id="scanner" className="workspace-grid">
        <div className="left-stack">
          <ScannerPanel activeTab={activeTab} setActiveTab={setActiveTab} onReport={handleReport} />
          <HistoryPanel reports={history} onSelect={setSelectedReport} onClear={handleClearHistory} />
        </div>
        <ResultCard report={selectedReport} />
      </section>

      <footer className="footer-note">
        Defensive scanning only. Do not upload private documents unless you control the backend and understand where reports are stored.
      </footer>
    </main>
  );
}
