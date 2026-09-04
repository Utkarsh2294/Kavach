import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { Activity, Bot, CircleAlert, FlaskConical, Play, RefreshCcw, ShieldCheck, TriangleAlert } from 'lucide-react';
import { useAuth } from '@/hooks/useAuth';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';

const API = import.meta.env.VITE_API_BASE_URL || '';

function readableError(body) {
  return body?.detail?.message || body?.detail || body?.error?.message || 'Sandbox action failed';
}

function formatCurrency(value) {
  return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 }).format(value || 0);
}

export function SandboxPage() {
  const { accessToken } = useAuth();
  const [agents, setAgents] = useState([]);
  const [transactions, setTransactions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [action, setAction] = useState('');
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');

  const request = useCallback(async (path, options = {}) => {
    const response = await fetch(`${API}${path}`, {
      ...options,
      headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${accessToken}`, ...(options.headers || {}) },
    });
    const body = response.status === 204 ? null : await response.json().catch(() => null);
    if (!response.ok) throw new Error(readableError(body));
    return body;
  }, [accessToken]);

  const refresh = useCallback(async () => {
    if (!accessToken) return;
    setLoading(true);
    try {
      const [fleet, feed] = await Promise.all([
        request('/api/v1/agents?sandbox=true&page_size=100'),
        request('/api/v1/transactions?sandbox=true&page_size=30'),
      ]);
      setAgents(fleet);
      setTransactions(feed);
      setError('');
    } catch (err) {
      setError(err.message || 'Unable to load sandbox data');
    } finally {
      setLoading(false);
    }
  }, [accessToken, request]);

  useEffect(() => { refresh(); }, [refresh]);

  const run = async (kind) => {
    setAction(kind);
    setError('');
    setNotice('');
    try {
      const result = await request(`/api/v1/sandbox/${kind}`, { method: 'POST' });
      await refresh();
      const messages = {
        start: result.created ? `Sandbox started with ${result.agent_count} isolated agents.` : `Sandbox is already running with ${result.agent_count} isolated agents.`,
        reset: `Sandbox reset with ${result.agent_count} fresh isolated agents.`,
        'trigger-rogue': 'Rogue activity triggered: two unauthorized sub-agents and a spend spike were evaluated through the normal governance pipeline.',
      };
      setNotice(messages[kind]);
    } catch (err) {
      setError(err.message || 'Sandbox action failed');
    } finally {
      setAction('');
    }
  };

  const activeAgents = agents.filter((agent) => agent.status !== 'revoked').length;
  const rogueAgents = agents.filter((agent) => agent.name.startsWith('Unauthorized Sandbox')).length;
  const decisions = useMemo(() => ({
    approve: transactions.filter((transaction) => transaction.decision === 'approve').length,
    escalate: transactions.filter((transaction) => transaction.decision === 'escalate').length,
    deny: transactions.filter((transaction) => transaction.decision === 'deny').length,
  }), [transactions]);

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
        <div><div className="flex items-center gap-2"><h1 className="text-2xl font-bold tracking-tight text-foreground">Sandbox</h1><Badge variant="warning"><FlaskConical className="mr-1 h-3 w-3" />Isolated environment</Badge></div><p className="mt-1 text-sm text-muted-foreground">Practice governance responses with synthetic agents and transactions. Sandbox data never appears in the real fleet.</p></div>
        <Button variant="outline" onClick={refresh} disabled={loading || Boolean(action)}><RefreshCcw className="mr-2 h-4 w-4" />Refresh</Button>
      </div>

      <Card className="border-warning-500/35 bg-warning-500/5"><div className="flex gap-3 p-5"><TriangleAlert className="mt-0.5 h-5 w-5 shrink-0 text-warning-400" /><div><h2 className="text-sm font-semibold text-foreground">Safe by design</h2><p className="mt-1 text-sm leading-6 text-muted-foreground">The sandbox uses the same rules, risk models, audit chain, and transaction pipeline as production. Its agents, transactions, escalations, and audit records are marked and queried separately.</p></div></div></Card>

      <div className="grid grid-cols-1 gap-3 md:grid-cols-3"><Metric icon={Bot} label="Sandbox agents" value={agents.length} sub={`${activeAgents} active`} /><Metric icon={Activity} label="Evaluated transactions" value={transactions.length} sub={`${decisions.approve} approved · ${decisions.escalate} escalated · ${decisions.deny} denied`} /><Metric icon={CircleAlert} label="Rogue sub-agents" value={rogueAgents} sub="created only by the scenario" /></div>

      {error && <Banner tone="danger" text={error} />}
      {notice && <Banner tone="success" text={notice} />}

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
        <Card className="p-5 lg:col-span-2"><div className="flex items-center gap-2"><ShieldCheck className="h-4 w-4 text-primary-400" /><h2 className="text-sm font-semibold text-foreground">Scenario controls</h2></div><p className="mt-1 text-sm text-muted-foreground">Start a repeatable fleet, then introduce suspicious behavior to observe the full governance response.</p><div className="mt-5 grid grid-cols-1 gap-3 sm:grid-cols-3"><Scenario icon={Play} title="Start sandbox" detail="Create a 10-agent synthetic fleet." label="Start" busy={action === 'start'} onClick={() => run('start')} /><Scenario icon={CircleAlert} title="Trigger rogue activity" detail="Create rogue sub-agents and a spend spike." label="Trigger" tone="danger" disabled={!agents.length} busy={action === 'trigger-rogue'} onClick={() => run('trigger-rogue')} /><Scenario icon={RefreshCcw} title="Reset sandbox" detail="Delete only sandbox records and recreate the fleet." label="Reset" tone="outline" busy={action === 'reset'} onClick={() => run('reset')} /></div></Card>
        <Card className="p-5"><p className="text-xs font-medium text-muted-foreground">What is exercised</p><ul className="mt-3 space-y-3 text-sm text-muted-foreground"><li className="flex gap-2"><span className="text-primary-400">01</span>Deterministic policy enforcement</li><li className="flex gap-2"><span className="text-primary-400">02</span>Isolation Forest novelty detection</li><li className="flex gap-2"><span className="text-primary-400">03</span>XGBoost transaction risk scoring</li><li className="flex gap-2"><span className="text-primary-400">04</span>Audit, escalation, and feed updates</li></ul></Card>
      </div>

      <Card className="overflow-hidden"><div className="flex items-center justify-between border-b border-border px-5 py-4"><div><h2 className="text-sm font-semibold text-foreground">Synthetic fleet</h2><p className="mt-0.5 text-xs text-muted-foreground">Separate from the real agent fleet.</p></div><Badge variant="outline">{agents.length} agents</Badge></div>{loading ? <div className="p-10 text-center text-sm text-muted-foreground">Loading sandbox…</div> : agents.length === 0 ? <div className="p-10 text-center text-sm text-muted-foreground">Start the sandbox to create the isolated fleet.</div> : <div className="divide-y divide-border">{agents.map((agent) => <div key={agent.id} className="flex flex-col gap-2 px-5 py-3 sm:flex-row sm:items-center"><div className="min-w-0 flex-1"><p className="truncate text-sm font-medium text-foreground">{agent.name}</p><p className="mt-0.5 text-xs capitalize text-muted-foreground">{agent.type} · {formatCurrency(agent.spendCapCurrent)} cap</p></div><Badge variant={agent.name.startsWith('Unauthorized Sandbox') ? 'danger' : agent.status === 'revoked' ? 'outline' : 'success'}>{agent.name.startsWith('Unauthorized Sandbox') ? 'Rogue' : agent.status}</Badge></div>)}</div>}</Card>
    </div>
  );
}

function Metric({ icon: Icon, label, value, sub }) {
  return <Card className="p-4"><div className="flex items-start justify-between"><div><p className="text-xs font-medium text-muted-foreground">{label}</p><p className="mt-2 text-2xl font-bold text-foreground">{value}</p><p className="mt-1 text-xs text-muted-foreground">{sub}</p></div><Icon className="h-4 w-4 text-warning-400" /></div></Card>;
}

function Scenario({ icon: Icon, title, detail, label, tone = 'default', disabled, busy, onClick }) {
  return <div className="rounded-lg border border-border bg-muted/20 p-3"><Icon className="h-4 w-4 text-primary-400" /><p className="mt-2 text-sm font-semibold text-foreground">{title}</p><p className="mt-1 min-h-10 text-xs leading-5 text-muted-foreground">{detail}</p><Button variant={tone === 'danger' ? 'destructive' : tone === 'outline' ? 'outline' : 'default'} size="sm" className="mt-3 w-full" disabled={disabled || busy} onClick={onClick}>{busy ? 'Working…' : label}</Button></div>;
}

function Banner({ tone, text }) {
  const success = tone === 'success';
  return <div role="status" className={`rounded-lg border px-4 py-3 text-sm ${success ? 'border-success-500/30 bg-success-500/10 text-success-300' : 'border-danger-500/35 bg-danger-500/10 text-danger-300'}`}>{text}</div>;
}
