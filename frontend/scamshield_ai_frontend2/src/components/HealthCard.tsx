import { useEffect, useState } from 'react';
import { API_BASE_URL, getHealth } from '../lib/api';
import type { HealthStatus } from '../types';

export function HealthCard() {
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [error, setError] = useState<string>('');

  useEffect(() => {
    let active = true;
    getHealth()
      .then((data) => {
        if (active) {
          setHealth(data);
          setError('');
        }
      })
      .catch((err: Error) => {
        if (active) setError(err.message);
      });
    return () => {
      active = false;
    };
  }, []);

  return (
    <section className="health-card">
      <div>
        <p className="eyebrow">API connection</p>
        <h3>{health ? 'Backend online' : error ? 'Backend offline' : 'Checking backend...'}</h3>
        <p className="muted mono">{API_BASE_URL}</p>
      </div>
      <div className={health ? 'status-dot online' : 'status-dot'} />
      {health ? (
        <div className="health-stats">
          <span>v{health.version}</span>
          <span>{health.max_file_size_mb} MB max file</span>
          <span>{health.external_checks_enabled ? 'External checks on' : 'Local checks only'}</span>
        </div>
      ) : error ? (
        <p className="error-text">{error}</p>
      ) : null}
    </section>
  );
}
