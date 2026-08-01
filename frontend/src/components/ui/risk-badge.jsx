import { cn } from '@/lib/utils';
import { Badge } from '@/components/ui/badge';

/* Phase 01C — canonical risk-score badge. Thresholds:
     0–29  Low      success (emerald)
     30–59 Mid      warning (amber)
     60–84 High     danger  (red-400)
     85–100 Critical danger  (red-500)
   These four are EXPORTED and reused verbatim by the transaction feed
   (Phase 03), audit log, agent detail, and policy dry-run (Phase 04).
   Never invent a per-screen threshold. */

export const RISK_THRESHOLDS = {
  LOW: { min: 0, max: 29 },
  MID: { min: 30, max: 59 },
  HIGH: { min: 60, max: 84 },
  CRITICAL: { min: 85, max: 100 },
};

export function riskLevelForScore(score) {
  if (score <= RISK_THRESHOLDS.LOW.max) return 'LOW';
  if (score <= RISK_THRESHOLDS.MID.max) return 'MID';
  if (score <= RISK_THRESHOLDS.HIGH.max) return 'HIGH';
  return 'CRITICAL';
}

const LEVEL_TO_VARIANT = { LOW: 'success', MID: 'warning', HIGH: 'danger', CRITICAL: 'danger' };
const LEVEL_TO_TOKEN = {
  LOW: 'var(--color-success-500)',
  MID: 'var(--color-warning-500)',
  HIGH: 'var(--color-danger-400)',
  CRITICAL: 'var(--color-danger-500)',
};
const LEVEL_LABEL = { LOW: 'Low', MID: 'Mid', HIGH: 'High', CRITICAL: 'Critical' };

export function riskColorForScore(score) {
  return LEVEL_TO_TOKEN[riskLevelForScore(score)];
}

export function RiskBadge({ score, showScore = true, showLabel = false, className }) {
  const level = riskLevelForScore(score);
  return (
    <Badge
      variant={LEVEL_TO_VARIANT[level]}
      className={cn('gap-1 text-[11px] font-mono', className)}
      title={`Risk score ${score}/100 — ${LEVEL_LABEL[level]}`}
    >
      {showLabel && LEVEL_LABEL[level]}
      {showScore && score}
    </Badge>
  );
}
