import React, { useState, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { Play, ArrowRight } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { DataTable } from '@/components/ui/data-table';
import { RiskBadge } from '@/components/ui/risk-badge';
import { Separator } from '@/components/ui/separator';
import { useLiveDataContext } from '@/context/useLiveDataContext';
import { decisionBadgeVariant } from '@/mocks/livedata';

const FAKE_POLICIES = [
  { id: 'pol_fake_1', name: 'Amount Cap', conditions: [{ field: 'amount', op: '<=', value: 250 }] },
  { id: 'pol_fake_2', name: 'Category Block', conditions: [{ field: 'merchantCategory', op: 'in', value: ['Storage', 'CDN Cache'] }] },
  { id: 'pol_fake_3', name: 'Agent Type Restrict', conditions: [{ field: 'agentType', op: '==', value: 'payment' }] },
];

export function DryRunPage() {
  const navigate = useNavigate();
  const { dryRunPolicy } = useLiveDataContext();

  const hash = typeof window !== 'undefined' ? window.location.hash.slice(1) : '';
  const initialJSON = (() => {
    try { return hash ? JSON.parse(decodeURIComponent(hash)) : null; } catch { return null; }
  })();

  const [selectedPolicy, setSelectedPolicy] = useState('');
  const [results, setResults] = useState(null);

  const policy = initialJSON
    ? { id: 'from_hash', name: 'Imported from Policy Builder', conditions: initialJSON.conditions || [] }
    : FAKE_POLICIES.find(p => p.id === selectedPolicy);

  const handleRun = () => {
    if (!policy) return;
    const r = dryRunPolicy(policy.conditions);
    setResults(r);
  };

  const beforeAfterRows = useMemo(() => {
    if (!results) return [];
    return results.map(tx => ({
      id: tx.id,
      agentName: tx.agentName,
      amount: tx.amount,
      category: tx.merchantCategory,
      riskScore: tx.riskScore,
      before: tx.before,
      after: tx.after,
      changed: tx.before !== tx.after,
    }));
  }, [results]);

  const summary = beforeAfterRows.reduce(
    (acc, r) => {
      if (r.changed) {
        if (r.after === 'deny') acc.blocked++;
        else if (r.after === 'approve') acc.allowed++;
      }
      return acc;
    },
    { blocked: 0, allowed: 0 },
  );

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-foreground">Dry Run Sandbox</h1>
        <p className="text-sm text-muted-foreground mt-1">Simulate policy effects against recent transactions</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Select Policy</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <select
            value={selectedPolicy}
            onChange={(e) => {
              setSelectedPolicy(e.target.value);
              setResults(null);
            }}
            className="w-full h-10 rounded-lg border border-border bg-card text-foreground text-sm px-3 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
          >
            <option value="">-- Choose a policy --</option>
            {FAKE_POLICIES.map(p => (
              <option key={p.id} value={p.id}>{p.name}</option>
            ))}
          </select>

          {initialJSON && (
            <div className="text-sm text-muted-foreground">
              Loaded policy from URL hash
            </div>
          )}

          <Button onClick={handleRun} disabled={!policy} className="w-full">
            <Play className="mr-2 h-4 w-4" />
            Run Dry-Run
          </Button>
        </CardContent>
      </Card>

      {results && (
        <>
          <div className="grid grid-cols-2 gap-3">
            <Card>
              <CardContent className="p-4 text-center">
                <div className="text-xs text-muted-foreground">Newly Blocked</div>
                <div className="text-2xl font-bold text-danger-500 mt-1">{summary.blocked}</div>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="p-4 text-center">
                <div className="text-xs text-muted-foreground">Newly Allowed</div>
                <div className="text-2xl font-bold text-success-500 mt-1">{summary.allowed}</div>
              </CardContent>
            </Card>
          </div>

          <Separator />

          <DataTable
            columns={[
              { key: 'agentName', header: 'Agent Name' },
              {
                key: 'amount',
                header: 'Amount',
                sortable: true,
                render: (r) => <span className="font-mono">${r.amount.toFixed(2)}</span>,
              },
              { key: 'category', header: 'Category', sortable: true },
              {
                key: 'riskScore',
                header: 'Risk Score',
                sortable: true,
                render: (r) => <RiskBadge score={r.riskScore} />,
              },
              {
                key: 'before',
                header: 'Before',
                render: (r) => (
                  <Badge variant={decisionBadgeVariant(r.before)} className="capitalize text-[11px]">
                    {r.before}
                  </Badge>
                ),
              },
              {
                key: 'after',
                header: 'After',
                render: (r) => (
                  <Badge variant={decisionBadgeVariant(r.after)} className="capitalize text-[11px]">
                    {r.after}
                  </Badge>
                ),
              },
              {
                key: 'change',
                header: 'Change',
                render: (r) =>
                  r.changed ? (
                    <Badge variant={r.after === 'deny' ? 'danger' : 'success'} className="text-[11px]">
                      {r.after === 'deny' ? 'Blocked' : 'Allowed'}
                    </Badge>
                  ) : (
                    <span className="text-muted-foreground text-xs">—</span>
                  ),
              },
            ]}
            rows={beforeAfterRows}
            initialSortKey="amount"
            initialSortDir="desc"
            emptyMessage="No results — run a dry-run first"
          />
        </>
      )}
    </div>
  );
}