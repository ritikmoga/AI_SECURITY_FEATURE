import type { DashboardPage } from '../../types';

const entries: Array<{ id: DashboardPage; label: string; detail: string }> = [
  { id: 'url', label: 'URL scanner', detail: 'Link intelligence' }, { id: 'message', label: 'Message scanner', detail: 'Phishing analysis' },
  { id: 'file', label: 'File scanner', detail: 'Static inspection' }, { id: 'qr', label: 'QR scanner', detail: 'Local decode + scan' },
  { id: 'reports', label: 'Reports', detail: 'Scan history' }, { id: 'lookup', label: 'Report lookup', detail: 'Find by scan ID' }
];

export function Sidebar({ page, onPage, admin }: { page: DashboardPage; onPage: (page: DashboardPage) => void; admin: boolean }) {
  return <aside className="sidebar"><div className="sidebar-brand">SCAMSHIELD <span>AI</span></div><p>Security operations workspace</p><nav>{entries.map((entry) => <button key={entry.id} className={page === entry.id ? 'nav-item active' : 'nav-item'} onClick={() => onPage(entry.id)}><strong>{entry.label}</strong><small>{entry.detail}</small></button>)}{admin ? <button className={page === 'admin' ? 'nav-item active' : 'nav-item'} onClick={() => onPage('admin')}><strong>Administration</strong><small>Platform posture</small></button> : null}</nav></aside>;
}
