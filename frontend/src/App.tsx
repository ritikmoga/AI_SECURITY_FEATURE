import { useCallback, useEffect, useMemo, useState } from 'react';
import { AuthButton } from './components/AuthButton';
import { AdminPanel } from './components/AdminPanel';
import { Sidebar } from './components/layout/Sidebar';
import { Hero } from './components/Hero';
import { HistoryPanel } from './components/HistoryPanel';
import { ResultCard } from './components/ResultCard';
import { ScannerPanel } from './components/ScannerPanel';
import { clearHistory, readHistory, saveReportToHistory } from './lib/history';
import { fetchUserReports, readSession } from './lib/api';
import type { AppUser, DashboardPage, ScanReport } from './types';

export default function App() {
  const [page, setPage] = useState<DashboardPage>('url');
  const [selectedReport, setSelectedReport] = useState<ScanReport | null>(null);
  const [history, setHistory] = useState<ScanReport[]>(() => readHistory());
  const [user, setUser] = useState<AppUser | null>(() => readSession()?.user || null);

  const handleUser = useCallback((next: AppUser | null) => setUser(next), []);
  useEffect(() => { if (user) fetchUserReports().then((reports) => setHistory(reports)).catch(() => undefined); }, [user]);

  const stats = useMemo(() => {
    const total = history.length;
    const risky = history.filter((item) => item.risk_level === 'High Risk' || item.risk_level === 'Dangerous').length;
    const average = total ? Math.round(history.reduce((sum, item) => sum + item.risk_score, 0) / total) : 0;
    return { total, risky, average };
  }, [history]);

  function handleReport(report: ScanReport) {
    setSelectedReport(report);
    setHistory(saveReportToHistory(report));
    setPage('reports');
  }

  function handleClearHistory() {
    clearHistory();
    setHistory([]);
  }

  return (
    <main className="app-shell dashboard-shell">
      <Sidebar page={page} onPage={setPage} admin={user?.role === 'admin'} />
      <div className="dashboard-content"><Hero />
      <div className="account-bar"><span>{user ? 'Your scans are stored in your account history.' : 'Sign in to keep your scan history across devices.'}</span><AuthButton user={user} onUser={handleUser} /></div>
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

      {page === 'admin' && user?.role === 'admin' ? <AdminPanel /> : null}
      {page === 'reports' ? <HistoryPanel reports={history} onSelect={setSelectedReport} onClear={handleClearHistory} /> : null}
      {page !== 'reports' && page !== 'admin' ? <section id="scanner" className="workspace-grid">
        <div className="left-stack">
          <ScannerPanel page={page} onReport={handleReport} />
        </div>
        <ResultCard report={selectedReport} />
      </section> : null}

      <footer className="footer-note">
        Defensive scanning only. Do not upload private documents unless you control the backend and understand where reports are stored.
      </footer>
      </div>
    </main>
  );
}
