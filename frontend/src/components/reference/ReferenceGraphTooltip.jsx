/* Phase 01C — graph node tooltip (Phase 03's hover state). Uses the same
   token colors as the canvas-drawn nodes (success / warning / danger /
   surface-500), so the tooltip matches the on-canvas node visually. */

const STATUS_COLOR = (active, trustScore) => {
  if (!active) return 'var(--color-surface-500)';
  if (trustScore >= 80) return 'var(--color-success-500)';
  if (trustScore >= 50) return 'var(--color-warning-500)';
  return 'var(--color-danger-500)';
};
const STATUS_LABEL = (active, trustScore) => {
  if (!active) return 'revoked';
  if (trustScore >= 80) return 'active';
  if (trustScore >= 50) return 'degraded';
  return 'critical';
};

export function ReferenceGraphTooltip({ agent }) {
  const color = STATUS_COLOR(agent.active, agent.trustScore);
  return (
    <div className="w-60 rounded-lg border border-border bg-popover text-popover-foreground shadow-md p-3 text-xs space-y-1.5">
      <div className="flex items-center gap-2 font-semibold">
        <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: color }} />
        {agent.name}
      </div>
      <div className="text-muted-foreground capitalize">{agent.type} · {agent.role}</div>
      <div className="flex justify-between">
        <span className="text-muted-foreground">Trust</span>
        <span style={{ color }}>{Math.round(agent.trustScore)}% ({STATUS_LABEL(agent.active, agent.trustScore)})</span>
      </div>
      <div className="flex justify-between">
        <span className="text-muted-foreground">Spend</span>
        <span className="font-mono">${agent.totalSpend.toFixed(0)} / ${agent.cap.toLocaleString()}</span>
      </div>
      <div className="flex justify-between">
        <span className="text-muted-foreground">Agent ID</span>
        <span className="font-mono text-[10px]">{agent.id}</span>
      </div>
    </div>
  );
}

const fakeAgent = {
  id: 'ag_8a3f22',
  name: 'Refund Handler',
  type: 'payment',
  role: 'worker',
  trustScore: 76,
  active: true,
  cap: 1500,
  totalSpend: 980,
};
export { fakeAgent };
