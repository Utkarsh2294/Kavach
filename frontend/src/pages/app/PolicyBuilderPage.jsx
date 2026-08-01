import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Plus, Trash2, Eye } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { SegmentedControl } from '@/components/ui/segmented-control';
import { Separator } from '@/components/ui/separator';

const FIELD_OPTIONS = [
  { value: 'amount', label: 'Amount' },
  { value: 'merchantCategory', label: 'Merchant Category' },
  { value: 'delegationDepth', label: 'Delegation Depth' },
  { value: 'agentType', label: 'Agent Type' },
  { value: 'timeOfDayHour', label: 'Time of Day Hour' },
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
  return {
    logic: logic === 'all' ? 'AND' : 'OR',
    conditions: conditions.map(c => ({
      field: c.field,
      operator: c.op,
      value: c.op === 'in' || c.op === 'not_in'
        ? (typeof c.value === 'string' ? c.value.split(',').map(s => s.trim()).filter(Boolean) : c.value)
        : isNaN(Number(c.value)) ? c.value : Number(c.value),
    })),
  };
}

export function PolicyBuilderPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const isEdit = Boolean(id);

  const [name, setName] = useState('');
  const [logic, setLogic] = useState('all');
  const [conditions, setConditions] = useState([
    { id: 1, field: 'amount', op: '<=', value: '' },
  ]);

  const [nextId, setNextId] = useState(2);

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
    const json = JSON.stringify(policyJSON);
    navigate(`/app/dry-run#${encodeURIComponent(json)}`);
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
        <Button onClick={() => {}} className="px-6">
          Save Policy
        </Button>
        <Button variant="outline" onClick={handleDryRun} className="px-6">
          Test in Dry-Run
        </Button>
      </div>
    </div>
  );
}