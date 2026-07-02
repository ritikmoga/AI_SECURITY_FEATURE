import type { RiskLevel } from '../types';

function riskClass(level: RiskLevel): string {
  const normalized = level.toLowerCase();
  if (normalized.includes('danger')) return 'risk danger';
  if (normalized.includes('high')) return 'risk high';
  if (normalized.includes('suspicious')) return 'risk suspicious';
  return 'risk safe';
}

export function RiskBadge({ level }: { level: RiskLevel }) {
  return <span className={riskClass(level)}>{level}</span>;
}
