import { useState } from 'react';
import { exportUserReports } from '../lib/api';

export function ExportReportsButton() {
  const [loading, setLoading] = useState(false);
  async function download() {
    setLoading(true);
    try {
      const blob = await exportUserReports();
      const url = URL.createObjectURL(blob); const link = document.createElement('a');
      link.href = url; link.download = 'scamshield-reports.csv'; link.click(); URL.revokeObjectURL(url);
    } finally { setLoading(false); }
  }
  return <button className="ghost-btn" type="button" disabled={loading} onClick={download}>{loading ? 'Preparing…' : 'Export CSV'}</button>;
}
