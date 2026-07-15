import { useEffect, useState } from 'react';
import { fetchAdminOverview } from '../lib/api';
import type { AdminOverview } from '../types';

export function AdminPanel() {
  const [overview, setOverview] = useState<AdminOverview | null>(null);

  useEffect(() => { fetchAdminOverview().then(setOverview).catch(() => setOverview(null)); }, []);
  if (!overview) return null;

  return <section className="admin-panel" aria-label="Administrator console">
    <div><p className="eyebrow">Administrator console</p><h2>Security service posture</h2></div>
    <div className="admin-grid">
      <span><small>Storage</small><strong>{overview.storage}</strong></span>
      <span><small>Rate limiter</small><strong>{overview.rate_limiter}</strong></span>
      <span><small>Reputation checks</small><strong>{overview.external_checks_enabled ? 'Enabled' : 'Disabled'}</strong></span>
    </div>
  </section>;
}
