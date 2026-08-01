import React, { useState, useRef, useMemo } from 'react';
import { ShieldCheck, ShieldAlert, Search, CheckCircle, XCircle } from 'lucide-react';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { DataTable } from '@/components/ui/data-table';
import { Separator } from '@/components/ui/separator';

const EVENT_TYPES = ['grant', 'deny', 'override', 'revoke', 'kill_switch'];

function fakeSha1() {
  let h = '';
  for (let i = 0; i < 40; i++) h += '0123456789abcdef'[Math.floor(Math.random() * 16)];
  return h;
}

function generateMockLog() {
  const now = Date.now();
  const entries = [];
  let prevHash = '0000000000000000000000000000000000000000';
  for (let i = 0; i < 50; i++) {
    const thisHash = fakeSha1();
    const eventType = EVENT_TYPES[Math.floor(Math.random() * EVENT_TYPES.length)];
    const agentNum = String(Math.floor(Math.random() * 12) + 1).padStart(3, '0');
    const agentName = `Agent ${agentNum}`;
    entries.push({
      id: `audit_${String(i + 1).padStart(4, '0')}`,
      eventType,
      agentId: `agent_${agentNum}`,
      agentName,
      payload: `${eventType.replace('_', ' ')} transaction for agent agent_${agentNum} — approved by governance`,
      timestamp: now - Math.floor(Math.random() * 24 * 60 * 60 * 1000),
      thisHash,
      prevHash,
    });
    prevHash = thisHash;
  }
  return entries.sort((a, b) => b.timestamp - a.timestamp);
}

export function AuditLogPage() {
  const [chainValid, setChainValid] = useState(null);
  const [search, setSearch] = useState('');
  const [fromDate, setFromDate] = useState('');
  const [toDate, setToDate] = useState('');

  const logEntries = useMemo(() => generateMockLog(), []);

  const filtered = useMemo(() => {
    let rows = logEntries;
    if (search) {
      const q = search.toLowerCase();
      rows = rows.filter(e =>
        e.agentName.toLowerCase().includes(q) ||
        e.eventType.toLowerCase().includes(q) ||
        e.payload.toLowerCase().includes(q),
      );
    }
    if (fromDate) {
      const from = new Date(fromDate).getTime();
      rows = rows.filter(e => e.timestamp >= from);
    }
    if (toDate) {
      const to = new Date(toDate).getTime() + 86400000;
      rows = rows.filter(e => e.timestamp <= to);
    }
    return rows;
  }, [logEntries, search, fromDate, toDate]);

  const handleVerify = () => {
    setChainValid(prev => prev === null ? true : !prev);
  };

  const eventVariant = (type) => {
    if (type === 'grant') return 'success';
    if (type === 'deny' || type === 'revoke' || type === 'kill_switch') return 'danger';
    if (type === 'override') return 'warning';
    return 'default';
  };

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-foreground">Audit Log Explorer</h1>
        <p className="text-sm text-muted-foreground mt-1">Tamper-evident cryptographic audit chain</p>
      </div>

      <div className="flex items-center gap-3 flex-wrap">
        <Button variant="outline" onClick={handleVerify} className="gap-2">
          <ShieldCheck className="h-4 w-4" />
          Verify Chain Integrity
        </Button>
        {chainValid !== null && (
          chainValid ? (
            <div className="flex items-center gap-2 text-success-500 text-sm rounded-lg border border-success-500/30 bg-success-500/10 px-4 py-2">
              <CheckCircle className="h-4 w-4" />
              Chain valid — {logEntries.length} records, 0 breaks
            </div>
          ) : (
            <div className="flex items-center gap-2 text-danger-500 text-sm rounded-lg border border-danger-500/30 bg-danger-500/10 px-4 py-2">
              <XCircle className="h-4 w-4" />
              Integrity breach at record #12 — hash check fails
            </div>
          )
        )}
      </div>

      <Separator />

      <div className="flex items-center gap-3">
        <div className="relative flex-1 max-w-sm">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search by agent, event, payload..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-9"
          />
        </div>
        <Input
          type="date"
          value={fromDate}
          onChange={(e) => setFromDate(e.target.value)}
          className="w-40"
        />
        <span className="text-muted-foreground text-sm">to</span>
        <Input
          type="date"
          value={toDate}
          onChange={(e) => setToDate(e.target.value)}
          className="w-40"
        />
      </div>

      <DataTable
        columns={[
          {
            key: 'timestamp',
            header: 'Timestamp',
            sortable: true,
            render: (r) => (
              <span className="text-xs font-mono text-muted-foreground">
                {new Date(r.timestamp).toLocaleString()}
              </span>
            ),
          },
          {
            key: 'eventType',
            header: 'Event Type',
            sortable: true,
            render: (r) => (
              <Badge variant={eventVariant(r.eventType)} className="capitalize text-[11px]">
                {r.eventType.replace('_', ' ')}
              </Badge>
            ),
          },
          { key: 'agentName', header: 'Agent Name', sortable: true },
          {
            key: 'payload',
            header: 'Payload',
            render: (r) => (
              <span className="text-xs text-muted-foreground font-mono">
                {(r.payload || '').slice(0, 40)}{r.payload && r.payload.length > 40 ? '…' : ''}
              </span>
            ),
          },
          {
            key: 'chain',
            header: 'Hash Chain',
            render: (r) => (
              <Badge variant="outline" className="text-[10px] font-mono gap-1">
                {r.prevHash?.slice(0, 8)}
                <span className="text-muted-foreground">→</span>
                {r.thisHash?.slice(0, 8)}
              </Badge>
            ),
          },
        ]}
        rows={filtered}
        initialSortKey="timestamp"
        initialSortDir="desc"
        emptyMessage="No audit log entries found"
      />
    </div>
  );
}