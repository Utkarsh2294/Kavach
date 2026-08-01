import React, { useState, useMemo } from 'react';
import { ChevronDown, ChevronUp, ShieldCheck, ShieldX, SlidersHorizontal } from 'lucide-react';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { RiskBadge } from '@/components/ui/risk-badge';
import { useLiveDataContext } from '@/context/useLiveDataContext';
import { toast } from '@/components/ui/toast';

export function EscalationsPage() {
  const { transactions } = useLiveDataContext();
  const [expandedId, setExpandedId] = useState(null);
  const [resolvedIds, setResolvedIds] = useState(new Set());

  const escalationItems = useMemo(() => {
    return transactions
      .filter(tx => tx.riskScore >= 40 && tx.riskScore <= 80 && !resolvedIds.has(tx.id))
      .slice(0, 8);
  }, [transactions, resolvedIds]);

  const handleApprove = (tx) => {
    setResolvedIds(prev => new Set([...prev, tx.id]));
    toast.success(`Escalation approved — adjusted cap for ${tx.agentName}`);
  };

  const handleDeny = (tx) => {
    setResolvedIds(prev => new Set([...prev, tx.id]));
    toast.error(`Escalation denied for ${tx.agentName}`);
  };

  const handleAdjustCap = (tx) => {
    setResolvedIds(prev => new Set([...prev, tx.id]));
    toast.success(`Cap adjusted for ${tx.agentName}`);
  };

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-foreground">Escalation Queue</h1>
        <p className="text-sm text-muted-foreground mt-1">Awaiting Human Review</p>
      </div>

      {escalationItems.length === 0 ? (
        <Card>
          <CardContent className="py-12 text-center">
            <div className="text-success-500 text-lg font-semibold mb-1">All clear</div>
            <div className="text-sm text-muted-foreground">All medium-risk transactions reviewed</div>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-3">
          {escalationItems.map(tx => {
            const expanded = expandedId === tx.id;
            return (
              <Card key={tx.id}>
                <div
                  className="p-4 cursor-pointer hover:bg-muted/20 transition-colors"
                  onClick={() => setExpandedId(expanded ? null : tx.id)}
                >
                  <div className="flex items-center justify-between gap-3">
                    <div className="flex items-center gap-3 min-w-0">
                      <RiskBadge score={tx.riskScore} />
                      <div className="min-w-0">
                        <div className="text-sm font-medium text-foreground truncate">{tx.agentName}</div>
                        <div className="text-xs text-muted-foreground font-mono">{tx.id}</div>
                      </div>
                    </div>
                    <div className="flex items-center gap-4 shrink-0">
                      <div className="text-right">
                        <div className="text-sm font-semibold text-foreground font-mono">${tx.amount.toFixed(2)}</div>
                        <div className="text-xs text-muted-foreground">{tx.merchantCategory}</div>
                      </div>
                      {expanded ? <ChevronUp className="h-4 w-4 text-muted-foreground" /> : <ChevronDown className="h-4 w-4 text-muted-foreground" />}
                    </div>
                  </div>
                </div>

                {expanded && (
                  <>
                    <Separator />
                    <div className="p-4 space-y-3">
                      <div className="grid grid-cols-3 gap-3 text-xs">
                        <div>
                          <div className="text-muted-foreground mb-0.5">Transaction ID</div>
                          <div className="font-mono text-foreground">{tx.id}</div>
                        </div>
                        <div>
                          <div className="text-muted-foreground mb-0.5">Agent</div>
                          <div className="text-foreground">{tx.agentName}</div>
                        </div>
                        <div>
                          <div className="text-muted-foreground mb-0.5">Risk Score</div>
                          <RiskBadge score={tx.riskScore} showLabel />
                        </div>
                        <div>
                          <div className="text-muted-foreground mb-0.5">Amount</div>
                          <div className="font-mono text-foreground">${tx.amount.toFixed(2)}</div>
                        </div>
                        <div>
                          <div className="text-muted-foreground mb-0.5">Category</div>
                          <div className="text-foreground">{tx.merchantCategory}</div>
                        </div>
                        <div>
                          <div className="text-muted-foreground mb-0.5">Decision</div>
                          <Badge variant="warning" className="capitalize text-[11px]">{tx.decision}</Badge>
                        </div>
                      </div>

                      <div className="bg-muted/50 rounded-lg p-3">
                        <div className="text-xs font-medium text-muted-foreground mb-1">Review History (mock)</div>
                        <div className="space-y-1 text-xs text-muted-foreground">
                          <div className="flex items-center gap-2">
                            <div className="w-1.5 h-1.5 rounded-full bg-muted-foreground/40" />
                            Automated system flagged for mid-risk score ({tx.riskScore}/100)
                          </div>
                          <div className="flex items-center gap-2">
                            <div className="w-1.5 h-1.5 rounded-full bg-muted-foreground/40" />
                            Requires human review — amount ${tx.amount.toFixed(2)} in {tx.merchantCategory}
                          </div>
                        </div>
                      </div>

                      <div className="flex items-center gap-2 pt-1">
                        <Button
                          size="sm"
                          variant="default"
                          onClick={(e) => { e.stopPropagation(); handleApprove(tx); }}
                          className="gap-1.5"
                        >
                          <ShieldCheck className="h-3.5 w-3.5" />
                          Approve
                        </Button>
                        <Button
                          size="sm"
                          variant="destructive"
                          onClick={(e) => { e.stopPropagation(); handleDeny(tx); }}
                          className="gap-1.5"
                        >
                          <ShieldX className="h-3.5 w-3.5" />
                          Deny
                        </Button>
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={(e) => { e.stopPropagation(); handleAdjustCap(tx); }}
                          className="gap-1.5"
                        >
                          <SlidersHorizontal className="h-3.5 w-3.5" />
                          Adjust Cap
                        </Button>
                      </div>
                    </div>
                  </>
                )}
              </Card>
            );
          })}
        </div>
      )}
    </div>
  );
}