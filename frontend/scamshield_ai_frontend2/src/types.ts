export type RiskLevel = 'Safe' | 'Suspicious' | 'High Risk' | 'Dangerous' | string;

export interface Finding {
  type?: string;
  title?: string;
  severity?: 'info' | 'low' | 'medium' | 'high' | 'critical' | string;
  description?: string;
  evidence?: string;
  score?: number;
  [key: string]: unknown;
}

export interface ScanReport {
  scan_id: string;
  created_at: string;
  scan_type: 'url' | 'message' | 'file' | 'qr' | string;
  target: string;
  risk_score: number;
  risk_level: RiskLevel;
  summary: string;
  recommended_action: string;
  findings: Finding[];
  metadata?: Record<string, unknown>;
  disclaimer?: string;
}

export interface ApiEnvelope<T> {
  status: 'success' | 'error';
  data?: T;
  message?: string;
  error?: string;
}

export interface HealthStatus {
  status: string;
  service: string;
  version: string;
  external_checks_enabled: boolean;
  max_file_size_mb: number;
}

export type ScannerTab = 'url' | 'message' | 'file' | 'qr' | 'report';
