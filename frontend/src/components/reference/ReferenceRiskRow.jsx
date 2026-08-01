import { RiskBadge, riskLevelForScore } from '@/components/ui/risk-badge';
import { Badge } from '@/components/ui/badge';
import { cn } from '@/lib/utils';

/* Phase 01C — table row with risk-score badge. Reused verbatim by the
   transaction feed (Phase 03), audit log, and agent detail (Phase 04). */

const DECISION_VARIANT = { approve: 'success', deny: 'danger', escalate: 'warning' };

export function ReferenceRiskRow({ tx }) {
  return (
    <div className="flex items-center gap-3 px-3.5 py-2.5 border-b border-border/60 last:border-0 hover:bg-muted/40 transition-colors">
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <span className="text-sm font-medium text-foreground truncate">{tx.agentName}</span>
          <Badge
            variant={DECISION_VARIANT[tx.decision] ?? 'secondary'}
            className="text-[10px] py-0.5 px-1.5 capitalize"
          >
            {tx.decision}
          </Badge>
        </div>
        <div className="flex items-center gap-2 text-[11px] text-muted-foreground mt-0.5">
          <span className="font-mono">${tx.amount.toFixed(2)}</span>
          <span className="truncate">{tx.merchantCategory}</span>
        </div>
      </div>
      <RiskBadge score={tx.riskScore} />
    </div>
  );
}

const fakeTx = { id: 'txn_demo_1', agentName: 'Payment Gateway', amount: 342.5, merchantCategory: 'SaaS License', decision: 'approve', riskScore: 18 };
const fakeTxMid = { id: 'txn_demo_2', agentName: 'Refund Handler', amount: 89.0, merchantCategory: 'Data Transfer', decision: 'escalate', riskScore: 47 };
const fakeTxHigh = { id: 'txn_demo_3', agentName: 'Export Service', amount: 4100.0, merchantCategory: 'Storage', decision: 'deny', riskScore: 92 };

export function ReferenceRiskRowGallery() {
  return (
    <div className="rounded-xl border border-border bg-card overflow-hidden">
      <div className="px-3.5 py-2 border-b border-border text-xs font-semibold uppercase tracking-wider text-muted-foreground">
        Risk row — three variants of the same row component
      </div>
      <ReferenceRiskRow tx={fakeTx} />
      <ReferenceRiskRow tx={fakeTxMid} />
      <ReferenceRiskRow tx={fakeTxHigh} />
    </div>
  );
}
