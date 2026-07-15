import type { ScanReport } from '../../types';

export type RunScan = (task: () => Promise<ScanReport>) => void;

export type ScannerFormProps = { disabled: boolean; run: RunScan };
