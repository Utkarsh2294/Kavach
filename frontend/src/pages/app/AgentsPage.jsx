import React, { useMemo } from 'react';
import { Link, useParams } from 'react-router-dom';
import { Activity, ArrowUpRight, Bot, CircleAlert, CircleCheck, Clock3, ShieldCheck, Workflow } from 'lucide-react';
import { useLiveDataContext } from '@/context/useLiveDataContext';
import { Badge } from '@/components/ui/badge';
import { Card } from '@/components/ui/card';

function modelSignal(agentId, transactions) {
  const evaluated = transactions
    .filter((transaction) => transaction.agentId === agentId)
    .sort((left, right) => right.timestamp - left.timestamp);
  const latest = evaluated[0];
  if (!latest) return { label: 'Awaiting activity', variant: 'outline', score: null, decision: null };
  const score = Number(latest.riskScore ?? 0);
  if (score >= 70) return { label: 'High risk', variant: 'danger', score, decision: latest.decision };
  if (score >= 30) return { label: 'Review band', variant: 'warning', score, decision: latest.decision };
  return { label: 'Low risk', variant: 'success', score, decision: latest.decision };
}

function formatCurrency(value) {
  return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 }).format(value || 0);
}

function statusVariant(agent) {
  return agent.active ? 'success' : 'danger';
}

export function AgentsPage() {
  const { agents, transactions, modelReady, connected } = useLiveDataContext();
  const rows = useMemo(
    () => Object.values(agents)
      .map((agent) => ({ agent, signal: modelSignal(agent.id, transactions) }))
      .sort((left, right) => (right.signal.score ?? -1) - (left.signal.score ?? -1) || right.agent.cap - left.agent.cap),
    [agents, transactions],
  );
  const evaluatedCount = rows.filter(({ signal }) => signal.score !== null).length;

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-foreground">Agent fleet</h1>
          <p className="mt-1 text-sm text-muted-foreground">Governance and risk signals for every autonomous agent.</p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Badge variant={modelReady === true ? 'success' : modelReady === false ? 'danger' : 'outline'}>
            <Activity className="mr-1 h-3 w-3" />
            {modelReady === true ? 'Models online' : modelReady === false ? 'Models unavailable' : 'Checking models'}
          </Badge>
          <Badge variant={connected ? 'success' : 'outline'}>{connected ? 'Live feed connected' : 'Live feed reconnecting'}</Badge>
        </div>
      </div>

      <Card className="overflow-hidden border-primary-500/25 bg-card">
        <div className="flex flex-col gap-4 p-5 lg:flex-row lg:items-center lg:justify-between">
          <div className="flex items-start gap-3">
            <div className="rounded-lg bg-primary-500/15 p-2 text-primary-400"><Workflow className="h-5 w-5" /></div>
            <div>
              <h2 className="text-sm font-semibold text-foreground">Every eligible transaction is evaluated in one governed pipeline</h2>
              <p className="mt-1 text-sm text-muted-foreground">Rules enforce hard limits first. Isolation Forest detects novelty, XGBoost estimates risk, then Kavach approves, escalates, or denies.</p>
            </div>
          </div>
          <div className="flex shrink-0 items-center gap-2 text-xs font-medium text-muted-foreground">
            <span>Rules</span><span className="text-primary-400">→</span><span>Isolation Forest</span><span className="text-primary-400">→</span><span>XGBoost</span><span className="text-primary-400">→</span><span>Decision</span>
          </div>
        </div>
      </Card>

      <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
        <Metric icon={Bot} label="Fleet size" value={rows.length} sub="registered agents" />
        <Metric icon={ShieldCheck} label="Active agents" value={rows.filter(({ agent }) => agent.active).length} sub="not revoked" />
        <Metric icon={Activity} label="Model-evaluated" value={evaluatedCount} sub="within the loaded feed" />
      </div>

      <Card className="overflow-hidden">
        <div className="flex items-center justify-between border-b border-border px-5 py-4">
          <div><h2 className="text-sm font-semibold text-foreground">Agent risk posture</h2><p className="mt-0.5 text-xs text-muted-foreground">Risk reflects the latest completed transaction evaluation.</p></div>
          <Badge variant="outline">{rows.length} agents</Badge>
        </div>
        {rows.length === 0 ? (
          <div className="p-10 text-center text-sm text-muted-foreground">Loading the agent fleet…</div>
        ) : (
          <div className="divide-y divide-border">
            {rows.map(({ agent, signal }) => <AgentRow key={agent.id} agent={agent} signal={signal} />)}
          </div>
        )}
      </Card>
    </div>
  );
}

function Metric({ icon: Icon, label, value, sub }) {
  return <Card className="p-4"><div className="flex items-start justify-between"><div><p className="text-xs font-medium text-muted-foreground">{label}</p><p className="mt-2 text-2xl font-bold text-foreground">{value}</p><p className="mt-1 text-xs text-muted-foreground">{sub}</p></div><Icon className="h-4 w-4 text-primary-400" /></div></Card>;
}

function AgentRow({ agent, signal }) {
  const Icon = signal.score === null ? Clock3 : signal.score >= 70 ? CircleAlert : CircleCheck;
  return (
    <Link to={`/app/agents/${agent.id}`} className="group flex flex-col gap-4 px-5 py-4 transition-colors hover:bg-muted/35 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring sm:flex-row sm:items-center">
      <div className="flex min-w-0 flex-1 items-center gap-3">
        <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-muted text-primary-400"><Bot className="h-4 w-4" /></div>
        <div className="min-w-0"><p className="truncate text-sm font-semibold text-foreground">{agent.name}</p><p className="mt-0.5 truncate text-xs capitalize text-muted-foreground">{agent.agentType} agent</p></div>
      </div>
      <div className="flex flex-wrap items-center gap-2 sm:justify-end">
        <Badge variant={statusVariant(agent)}>{agent.active ? 'Active' : 'Revoked'}</Badge>
        <Badge variant={signal.variant}><Icon className="mr-1 h-3 w-3" />{signal.label}{signal.score !== null ? ` · ${signal.score}` : ''}</Badge>
        <span className="min-w-24 text-right font-mono text-xs text-muted-foreground">{formatCurrency(agent.cap)} cap</span>
        <ArrowUpRight className="h-4 w-4 text-muted-foreground transition-transform group-hover:-translate-y-0.5 group-hover:translate-x-0.5" />
      </div>
    </Link>
  );
}

export function AgentDetailPage() {
  const { id } = useParams();
  const { agents, transactions, modelReady } = useLiveDataContext();
  const agent = agents[id];
  const signal = agent ? modelSignal(agent.id, transactions) : null;
  const recent = transactions.filter((transaction) => transaction.agentId === id).sort((left, right) => right.timestamp - left.timestamp).slice(0, 5);

  if (!agent) return <div className="py-14 text-center text-sm text-muted-foreground">Loading agent details…</div>;

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center gap-3"><Link to="/app/agents" className="text-sm text-muted-foreground hover:text-foreground">Agents</Link><span className="text-muted-foreground">/</span><span className="text-sm text-foreground">{agent.name}</span></div>
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between"><div><h1 className="text-2xl font-bold text-foreground">{agent.name}</h1><p className="mt-1 capitalize text-sm text-muted-foreground">{agent.agentType} agent · {formatCurrency(agent.cap)} spending cap</p></div><Badge variant={signal.variant}>{signal.label}{signal.score !== null ? ` · ${signal.score}/100` : ''}</Badge></div>
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
        <Card className="p-5 lg:col-span-2"><div className="flex items-center gap-2"><Workflow className="h-4 w-4 text-primary-400" /><h2 className="text-sm font-semibold text-foreground">Connected risk controls</h2></div><div className="mt-5 grid grid-cols-1 gap-3 sm:grid-cols-3"><Control label="Deterministic rules" detail="Hard policy limits are evaluated first." state="Enforced" /><Control label="Isolation Forest" detail="Flags behavior outside normal patterns." state={modelReady ? 'Online' : 'Checking'} /><Control label="XGBoost" detail="Calculates the learned transaction-risk score." state={modelReady ? 'Online' : 'Checking'} /></div></Card>
        <Card className="p-5"><p className="text-xs font-medium text-muted-foreground">Latest model signal</p><p className="mt-3 text-3xl font-bold text-foreground">{signal.score === null ? '—' : `${signal.score}/100`}</p><p className="mt-1 text-xs text-muted-foreground">{signal.score === null ? 'No eligible transaction has been evaluated yet.' : `Latest decision: ${signal.decision}`}</p></Card>
      </div>
      <Card className="overflow-hidden"><div className="border-b border-border px-5 py-4"><h2 className="text-sm font-semibold text-foreground">Recent evaluated transactions</h2></div>{recent.length === 0 ? <div className="p-8 text-center text-sm text-muted-foreground">This agent has no evaluated transactions yet. Submit a transaction to activate the model signal.</div> : <div className="divide-y divide-border">{recent.map((transaction) => <div key={transaction.id} className="flex items-center justify-between px-5 py-3 text-sm"><div><p className="font-medium text-foreground">{transaction.merchantCategory}</p><p className="mt-0.5 text-xs text-muted-foreground">{new Date(transaction.timestamp * 1000).toLocaleString()}</p></div><div className="text-right"><p className="font-mono text-foreground">{formatCurrency(transaction.amount)}</p><p className="mt-0.5 text-xs capitalize text-muted-foreground">{transaction.decision} · {transaction.riskScore}/100 risk</p></div></div>)}</div>}</Card>
    </div>
  );
}

function Control({ label, detail, state }) {
  return <div className="rounded-lg border border-border bg-muted/25 p-3"><div className="flex items-start justify-between gap-2"><p className="text-xs font-semibold text-foreground">{label}</p><Badge variant={state === 'Online' || state === 'Enforced' ? 'success' : 'outline'}>{state}</Badge></div><p className="mt-2 text-xs leading-5 text-muted-foreground">{detail}</p></div>;
}
