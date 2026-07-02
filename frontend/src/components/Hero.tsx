import { HealthCard } from './HealthCard';

export function Hero() {
  return (
    <header className="hero">
      <nav className="top-nav">
        <div className="brand">
          <img src="/scamshield.svg" alt="ScamShield AI logo" />
          <div>
            <strong>ScamShield AI</strong>
            <span>Defensive Scanner Console</span>
          </div>
        </div>
        <a className="docs-link" href="http://127.0.0.1:5001/api/health" target="_blank" rel="noreferrer">
          API Health
        </a>
      </nav>

      <div className="hero-grid">
        <div>
          <p className="eyebrow">AI security feature frontend</p>
          <h1>Scan links, messages, files, and QR content in one futuristic dashboard.</h1>
          <p className="hero-copy">
            Built for your Flask backend with fast Vite + React + TypeScript. The UI keeps suspicious inputs on a safe defensive path and displays clean risk reports.
          </p>
          <div className="hero-actions">
            <a href="#scanner" className="primary-link">Start scanning</a>
            <span>Backend: http://127.0.0.1:5001</span>
          </div>
        </div>
        <HealthCard />
      </div>
    </header>
  );
}
