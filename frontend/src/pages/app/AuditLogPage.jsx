import React, { useEffect, useMemo, useState } from 'react';
import { CheckCircle, Search, ShieldCheck, XCircle } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { DataTable } from '@/components/ui/data-table';
import { Input } from '@/components/ui/input';
import { Separator } from '@/components/ui/separator';
import { useAuth } from '@/hooks/useAuth';

const eventVariant = (type) => type === 'grant' ? 'success'
  : ['deny', 'revoke', 'kill_switch'].includes(type) ? 'danger'
    : type === 'override' ? 'warning' : 'default';

export function AuditLogPage() {
  const { accessToken } = useAuth();
  const [entries, setEntries] = useState([]);
  const [chain, setChain] = useState(null);
  const [search, setSearch] = useState('');
  const [error, setError] = useState('');

  const api = async (path) => {
    const response = await fetch(path, { headers: { Authorization: `Bearer ${accessToken}` } });
    const data = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(data.detail?.message || data.detail || 'Request failed');
    return data;
  };
  const load = async () => {
    try { setEntries(await api('/api/v1/audit')); setError(''); } catch (err) { setError(err.message); }
  };
  useEffect(() => { load(); }, [accessToken]);
  const verify = async () => {
    try { setChain(await api('/api/v1/audit/verify')); setError(''); } catch (err) { setError(err.message); }
  };
  const rows = useMemo(() => entries.filter((entry) => JSON.stringify(entry).toLowerCase().includes(search.toLowerCase())).map((entry) => ({
    ...entry, timestamp: new Date(entry.timestamp).getTime(), payloadText: JSON.stringify(entry.payload),
  })), [entries, search]);

  return <div className="space-y-4">
    <div><h1 className="text-2xl font-bold tracking-tight text-foreground">Audit Log Explorer</h1><p className="text-sm text-muted-foreground mt-1">Tamper-evident cryptographic audit chain</p></div>
    <div className="flex items-center gap-3 flex-wrap">
      <Button variant="outline" onClick={verify} className="gap-2"><ShieldCheck className="h-4 w-4" />Verify Chain Integrity</Button>
      {chain && (chain.valid ? <div className="flex items-center gap-2 text-success-500 text-sm rounded-lg border border-success-500/30 bg-success-500/10 px-4 py-2"><CheckCircle className="h-4 w-4" />Chain valid — {chain.recordsVerified} records, 0 breaks</div> : <div className="flex items-center gap-2 text-danger-500 text-sm rounded-lg border border-danger-500/30 bg-danger-500/10 px-4 py-2"><XCircle className="h-4 w-4" />Integrity breach — {chain.breaks.length} break(s) found</div>)}
    </div>
    {error && <div className="rounded-lg border border-danger-500/30 bg-danger-500/10 px-4 py-3 text-sm text-danger-500">{error}</div>}
    <Separator />
    <div className="relative max-w-sm"><Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" /><Input placeholder="Search audit records..." value={search} onChange={(event) => setSearch(event.target.value)} className="pl-9" /></div>
    <DataTable columns={[
      { key: 'timestamp', header: 'Timestamp', sortable: true, render: (row) => <span className="text-xs font-mono text-muted-foreground">{new Date(row.timestamp).toLocaleString()}</span> },
      { key: 'eventType', header: 'Event Type', sortable: true, render: (row) => <Badge variant={eventVariant(row.eventType)} className="capitalize text-[11px]">{row.eventType.replace('_', ' ')}</Badge> },
      { key: 'agentId', header: 'Agent ID', render: (row) => <span className="font-mono text-xs">{row.agentId || '—'}</span> },
      { key: 'payloadText', header: 'Payload', render: (row) => <span className="text-xs text-muted-foreground font-mono">{row.payloadText.slice(0, 70)}</span> },
      { key: 'chain', header: 'Hash Chain', render: (row) => <Badge variant="outline" className="text-[10px] font-mono">{row.prevHash?.slice(0, 8)} → {row.thisHash?.slice(0, 8)}</Badge> },
    ]} rows={rows} initialSortKey="timestamp" initialSortDir="desc" emptyMessage="No audit log entries found" />
  </div>;
}
