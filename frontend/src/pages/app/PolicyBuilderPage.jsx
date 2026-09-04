import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Plus, Trash2 } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { SegmentedControl } from '@/components/ui/segmented-control';
import { Separator } from '@/components/ui/separator';
import { useAuth } from '@/hooks/useAuth';

const FIELD_OPTIONS = [
  { value: 'amount', label: 'Amount' },
  { value: 'merchant_category', label: 'Merchant Category' },
  { value: 'delegation_depth', label: 'Delegation Depth' },
  { value: 'agent_type', label: 'Agent Type' },
  { value: 'time_of_day_hour', label: 'Time of Day Hour' },
];

const OP_OPTIONS = [
  { value: '<=', label: '<=' },
  { value: '>', label: '>' },
  { value: '==', label: '==' },
  { value: '!=', label: '!=' },
  { value: 'in', label: 'in' },
  { value: 'not_in', label: 'not in' },
];

const LOGIC_OPTIONS = [
  { value: 'all', label: 'all of the following rules must match' },
  { value: 'any', label: 'any of the following rules must match' },
];

function buildJsonPreview(conditions, logic) {
  const rules = conditions.map(c => ({
      field: c.field,
      op: c.op,
      value: c.op === 'in' || c.op === 'not_in'
        ? (typeof c.value === 'string' ? c.value.split(',').map(s => s.trim()).filter(Boolean) : c.value)
        : isNaN(Number(c.value)) ? c.value : Number(c.value),
    }));
  return rules.length === 1 ? rules[0] : { [logic]: rules };
}

export function PolicyBuilderPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const isEdit = Boolean(id);
  const { accessToken } = useAuth();

  const [name, setName] = useState('');
  const [priority, setPriority] = useState(100);
  const [active, setActive] = useState(true);
  const [logic, setLogic] = useState('all');
  const [conditions, setConditions] = useState([
    { id: 1, field: 'amount', op: '<=', value: '' },
  ]);

  const [nextId, setNextId] = useState(2);
  const [loading, setLoading] = useState(isEdit);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!isEdit || !accessToken) return;
    let cancelled = false;
    const loadPolicy = async () => {
      setLoading(true);
      try {
        const response = await fetch(`/api/v1/policies/${id}`, {
          headers: { Authorization: `Bearer ${accessToken}` },
        });
        if (!response.ok) throw new Error('Unable to load policy');
        const policy = await response.json();
        if (cancelled) return;
        const rule = policy.ruleJson || {};
        const nested = Array.isArray(rule.all) ? rule.all : Array.isArray(rule.any) ? rule.any : null;
        const restored = (nested || [rule]).filter(Boolean).map((condition, index) => ({
          id: index + 1,
          field: condition.field || 'amount',
          op: condition.op || '<=',
          value: Array.isArray(condition.value) ? condition.value.join(', ') : String(condition.value ?? ''),
        }));
        setName(policy.name || '');
        setPriority(policy.priority ?? 100);
        setActive(policy.active !== false);
        setLogic(Array.isArray(rule.any) ? 'any' : 'all');
        setConditions(restored.length ? restored : [{ id: 1, field: 'amount', op: '<=', value: '' }]);
        setNextId(Math.max(2, restored.length + 1));
      } catch (err) {
        if (!cancelled) setError(err.message || 'Unable to load policy');
      } finally {
        if (!cancelled) setLoading(false);
      }
    };
    loadPolicy();
    return () => { cancelled = true; };
  }, [id, isEdit, accessToken]);

  const addRow = () => {
    setConditions(prev => [...prev, { id: nextId, field: 'amount', op: '<=', value: '' }]);
    setNextId(n => n + 1);
  };

  const removeRow = (rowId) => {
    if (conditions.length <= 1) return;
    setConditions(prev => prev.filter(c => c.id !== rowId));
  };

  const updateRow = (rowId, key, val) => {
    setConditions(prev => prev.map(c => c.id === rowId ? { ...c, [key]: val } : c));
  };

  const policyJSON = buildJsonPreview(conditions, logic);

  const handleDryRun = () => {
    const json = JSON.stringify({ conditions });
    navigate(`/app/dry-run#${encodeURIComponent(json)}`);
  };

  const handleSave = async () => {
    setError('');
    const endpoint = isEdit ? `/api/v1/policies/${id}` : '/api/v1/policies';
    try {
      const response = await fetch(endpoint, {
        method: isEdit ? 'PUT' : 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${accessToken}` },
        body: JSON.stringify({ name: name || 'Untitled policy', ruleJson: policyJSON, priority, active }),
      });
      if (!response.ok) throw new Error('Unable to save policy');
      navigate('/app/policies');
    } catch (err) {
      setError(err.message || 'Unable to save policy');
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-foreground">
          {isEdit ? 'Edit Policy' : 'New Policy'}
        </h1>
        <p className="text-sm text-muted-foreground mt-1">
          {isEdit ? `Editing policy: ${id}` : 'Define a new governance policy'}
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Policy Details</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <label className="text-xs font-medium text-muted-foreground block mb-1.5">Policy Name</label>
            <Input
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g. Amount Cap Policy"
            />
          </div>

          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <div>
              <label className="text-xs font-medium text-muted-foreground block mb-1.5">Priority</label>
              <Input type="number" min="1" value={priority} onChange={(e) => setPriority(Number(e.target.value) || 1)} />
              <p className="mt-1 text-xs text-muted-foreground">Lower numbers run first.</p>
            </div>
            <div className="flex items-center gap-3 pt-6">
              <input id="policy-active" type="checkbox" checked={active} onChange={(e) => setActive(e.target.checked)} className="h-4 w-4 accent-primary-500" />
              <label htmlFor="policy-active" className="text-sm text-foreground">Enable this policy immediately</label>
            </div>
          </div>

          <Separator />

          <div>
            <div className="flex items-center justify-between mb-3">
              <span className="text-sm font-medium text-foreground">Conditions</span>
              <Button variant="outline" size="sm" onClick={addRow}>
                <Plus className="mr-1 h-3.5 w-3.5" />
                Add Rule
              </Button>
            </div>

            <div className="space-y-2">
              {conditions.map(row => (
                <div key={row.id} className="flex items-center gap-2 bg-muted/40 rounded-lg p-2">
                  <select
                    value={row.field}
                    onChange={(e) => updateRow(row.id, 'field', e.target.value)}
                    className="h-9 rounded-md border border-border bg-card text-foreground text-sm px-2 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                  >
                    {FIELD_OPTIONS.map(f => (
                    <option key={f.value} value={f.value}>{f.label}</option>
                    ))}
                  </select>
                  <select
                    value={row.op}
                    onChange={(e) => updateRow(row.id, 'op', e.target.value)}
                    className="h-9 w-20 rounded-md border border-border bg-card text-foreground text-sm px-2 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                  >
                    {OP_OPTIONS.map(o => (
                      <option key={o.value} value={o.value}>{o.label}</option>
                    ))}
                  </select>
                  <Input
                    value={row.value}
                    onChange={(e) => updateRow(row.id, 'value', e.target.value)}
                    placeholder={row.op === 'in' || row.op === 'not_in' ? 'comma,sep, values' : 'Value'}
                    className="flex-1"
                  />
                  {conditions.length > 1 && (
                    <Button
                      variant="ghost"
                      size="icon"
                      onClick={() => removeRow(row.id)}
                      className="shrink-0 text-muted-foreground hover:text-danger-500"
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  )}
                </div>
              ))}
            </div>
          </div>

          <Separator />

          <div>
            <label className="text-xs font-medium text-muted-foreground block mb-2">Rule Matching Logic</label>
            <SegmentedControl
              options={LOGIC_OPTIONS}
              value={logic}
              onChange={setLogic}
            />
          </div>
        </CardContent>
      </Card>

      {error && <p role="alert" className="text-sm text-danger-400">{error}</p>}

      <Card>
        <CardHeader>
          <CardTitle className="text-base">JSON Preview</CardTitle>
        </CardHeader>
        <CardContent>
          <pre className="bg-muted/50 border border-border rounded-lg p-4 text-xs font-mono text-foreground whitespace-pre-wrap overflow-x-auto max-h-64 overflow-y-auto">
            {JSON.stringify(policyJSON, null, 2)}
          </pre>
        </CardContent>
      </Card>

      <div className="flex items-center gap-3">
        <Button onClick={handleSave} className="px-6" disabled={loading}>
          {loading ? 'Loading policy…' : 'Save Policy'}
        </Button>
        <Button variant="outline" onClick={handleDryRun} className="px-6">
          Test in Dry-Run
        </Button>
      </div>
    </div>
  );
}
