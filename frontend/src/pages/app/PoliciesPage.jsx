import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import { Activity, ArrowRight, CheckCircle2, CircleAlert, FileCode2, Plus, ShieldCheck, SlidersHorizontal, Trash2 } from 'lucide-react';
import { useAuth } from '@/hooks/useAuth';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';

const API = import.meta.env.VITE_API_BASE_URL || '';

function describeRule(rule) {
  if (!rule || typeof rule !== 'object') return 'No rule definition';
  if (Array.isArray(rule.all)) return `${rule.all.length} conditions — all must match`;
  if (Array.isArray(rule.any)) return `${rule.any.length} conditions — any may match`;
  if (rule.field) return `${String(rule.field).replaceAll('_', ' ')} ${rule.op || ''} ${Array.isArray(rule.value) ? rule.value.join(', ') : String(rule.value ?? '')}`;
  return 'Custom policy expression';
}

function policyError(body) {
  return body?.detail?.message || body?.detail || body?.error?.message || 'Unable to update policy';
}

export function PoliciesPage() {
  const { accessToken } = useAuth();
  const [policies, setPolicies] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [busyId, setBusyId] = useState(null);

  const request = useCallback(async (path, options = {}) => {
    const response = await fetch(`${API}${path}`, {
      ...options,
      headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${accessToken}`, ...(options.headers || {}) },
    });
    const body = response.status === 204 ? null : await response.json().catch(() => null);
    if (!response.ok) throw new Error(policyError(body));
    return body;
  }, [accessToken]);

  const loadPolicies = useCallback(async () => {
    if (!accessToken) return;
    setLoading(true);
    setError('');
    try {
      const rows = await request('/api/v1/policies');
      setPolicies(rows.sort((left, right) => left.priority - right.priority));
    } catch (err) {
      setError(err.message || 'Unable to load policies');
    } finally {
      setLoading(false);
    }
  }, [accessToken, request]);

  useEffect(() => { loadPolicies(); }, [loadPolicies]);

  const activeCount = useMemo(() => policies.filter((policy) => policy.active).length, [policies]);

  const setActive = async (policy, active) => {
    setBusyId(policy.id);
    setError('');
    try {
      const updated = await request(`/api/v1/policies/${policy.id}`, { method: 'PUT', body: JSON.stringify({ active }) });
      setPolicies((current) => current.map((item) => item.id === updated.id ? updated : item));
    } catch (err) {
      setError(err.message || 'Unable to update policy');
    } finally {
      setBusyId(null);
    }
  };

  const remove = async (policy) => {
    if (!window.confirm(`Delete “${policy.name}”? This cannot be undone.`)) return;
    setBusyId(policy.id);
    setError('');
    try {
      await request(`/api/v1/policies/${policy.id}`, { method: 'DELETE' });
      setPolicies((current) => current.filter((item) => item.id !== policy.id));
    } catch (err) {
      setError(err.message || 'Unable to delete policy');
    } finally {
      setBusyId(null);
    }
  };

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-foreground">Policies</h1>
          <p className="mt-1 text-sm text-muted-foreground">Hard governance controls evaluated before ML risk scoring.</p>
        </div>
        <Button asChild><Link to="/app/policies/new"><Plus className="mr-2 h-4 w-4" />Create policy</Link></Button>
      </div>

      <Card className="border-primary-500/25 bg-card">
        <div className="flex flex-col gap-4 p-5 lg:flex-row lg:items-center lg:justify-between">
          <div className="flex gap-3"><div className="rounded-lg bg-primary-500/15 p-2 text-primary-400"><ShieldCheck className="h-5 w-5" /></div><div><h2 className="text-sm font-semibold text-foreground">Rules remain the non-negotiable safety layer</h2><p className="mt-1 text-sm text-muted-foreground">A policy denial stops the transaction before Isolation Forest and XGBoost are evaluated. This keeps mandatory limits explainable and deterministic.</p></div></div>
          <Link to="/app/dry-run" className="inline-flex shrink-0 items-center gap-1 text-sm font-medium text-primary-400 hover:text-primary-300">Open dry-run <ArrowRight className="h-4 w-4" /></Link>
        </div>
      </Card>

      <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
        <Metric icon={FileCode2} label="Total policies" value={policies.length} sub="organization controls" />
        <Metric icon={CheckCircle2} label="Active policies" value={activeCount} sub="currently enforced" />
        <Metric icon={SlidersHorizontal} label="Priority order" value={policies.length ? `${policies[0].priority}–${policies[policies.length - 1].priority}` : '—'} sub="lower values evaluate first" />
      </div>

      {error && <div role="alert" className="flex items-center gap-2 rounded-lg border border-danger-500/35 bg-danger-500/10 px-4 py-3 text-sm text-danger-300"><CircleAlert className="h-4 w-4" />{error}</div>}

      <Card className="overflow-hidden">
        <div className="flex items-center justify-between border-b border-border px-5 py-4"><div><h2 className="text-sm font-semibold text-foreground">Governance rules</h2><p className="mt-0.5 text-xs text-muted-foreground">Changes take effect for the next eligible transaction.</p></div><Badge variant="outline">Priority ordered</Badge></div>
        {loading ? <div className="p-10 text-center text-sm text-muted-foreground">Loading policies…</div> : policies.length === 0 ? <EmptyState /> : <div className="divide-y divide-border">{policies.map((policy) => <PolicyRow key={policy.id} policy={policy} busy={busyId === policy.id} onSetActive={setActive} onDelete={remove} />)}</div>}
      </Card>
    </div>
  );
}

function Metric({ icon: Icon, label, value, sub }) {
  return <Card className="p-4"><div className="flex items-start justify-between"><div><p className="text-xs font-medium text-muted-foreground">{label}</p><p className="mt-2 text-2xl font-bold text-foreground">{value}</p><p className="mt-1 text-xs text-muted-foreground">{sub}</p></div><Icon className="h-4 w-4 text-primary-400" /></div></Card>;
}

function PolicyRow({ policy, busy, onSetActive, onDelete }) {
  return (
    <div className="flex flex-col gap-4 px-5 py-4 lg:flex-row lg:items-center">
      <div className="min-w-0 flex-1"><div className="flex flex-wrap items-center gap-2"><Link to={`/app/policies/${policy.id}/edit`} className="truncate text-sm font-semibold text-foreground hover:text-primary-300">{policy.name}</Link><Badge variant={policy.active ? 'success' : 'outline'}>{policy.active ? 'Enforced' : 'Disabled'}</Badge></div><p className="mt-1 truncate text-sm text-muted-foreground">{describeRule(policy.ruleJson)}</p></div>
      <div className="flex flex-wrap items-center gap-2 lg:justify-end"><span className="font-mono text-xs text-muted-foreground">P{policy.priority}</span><Button variant="outline" size="sm" disabled={busy} onClick={() => onSetActive(policy, !policy.active)}><Activity className="mr-1.5 h-3.5 w-3.5" />{policy.active ? 'Disable' : 'Enable'}</Button><Button variant="ghost" size="icon" disabled={busy} aria-label={`Delete ${policy.name}`} className="text-muted-foreground hover:text-danger-400" onClick={() => onDelete(policy)}><Trash2 className="h-4 w-4" /></Button></div>
    </div>
  );
}

function EmptyState() {
  return <div className="p-10 text-center"><FileCode2 className="mx-auto h-6 w-6 text-muted-foreground" /><p className="mt-3 text-sm font-medium text-foreground">No policies yet</p><p className="mt-1 text-sm text-muted-foreground">Create a deterministic control before agents begin transacting.</p><Button asChild className="mt-4"><Link to="/app/policies/new"><Plus className="mr-2 h-4 w-4" />Create first policy</Link></Button></div>;
}
