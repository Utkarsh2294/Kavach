import React, { useState, useRef, useEffect, useCallback } from 'react';
import { useLiveDataContext } from '@/context/useLiveDataContext';
import { DelegationGraph } from '@/components/DelegationGraph';
import { AgentSlideOver } from '@/components/AgentSlideOver';
import { Badge } from '@/components/ui/badge';
import { Card } from '@/components/ui/card';

export function GraphPage() {
  const { nodes, edges, pulsingIds, txnRef, killAgent, stats, agents } = useLiveDataContext();
  const [selectedAgent, setSelectedAgent] = useState(null);
  const [slideOpen, setSlideOpen] = useState(false);
  const containerRef = useRef(null);
  const [size, setSize] = useState({ width: 900, height: 600 });

  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;
    const ro = new ResizeObserver(entries => {
      for (const e of entries) {
        setSize({ width: e.contentRect.width, height: e.contentRect.height });
      }
    });
    ro.observe(el);
    return () => ro.disconnect();
  }, []);

  const handleNodeClick = useCallback((node) => {
    const agent = agents[node.id];
    if (agent) {
      setSelectedAgent(agent);
      setSlideOpen(true);
    }
  }, [agents]);

  return (
    <div className="space-y-4 h-full flex flex-col" style={{ minHeight: 'calc(100vh - 120px)' }}>
      {/* Header */}
      <div className="flex items-center justify-between shrink-0">
        <div className="flex items-center gap-4">
          <h1 className="text-2xl font-bold tracking-tight text-foreground">Delegation Graph</h1>
          <div className="flex items-center gap-3 text-xs text-muted-foreground">
            <span className="inline-flex items-center gap-1"><span className="w-2 h-2 rounded-full" style={{ backgroundColor: 'var(--color-success-500)' }} /> Active</span>
            <span className="inline-flex items-center gap-1"><span className="w-2 h-2 rounded-full" style={{ backgroundColor: 'var(--color-warning-500)' }} /> Degraded</span>
            <span className="inline-flex items-center gap-1"><span className="w-2 h-2 rounded-full" style={{ backgroundColor: 'var(--color-danger-500)' }} /> Critical</span>
            <span className="inline-flex items-center gap-1"><span className="w-2 h-2 rounded-full" style={{ backgroundColor: 'var(--color-surface-500)' }} /> Revoked</span>
          </div>
        </div>
        <Badge variant="outline" className="text-xs">
          {nodes.length} agents · {stats.activeAgents} active
        </Badge>
      </div>

      {/* Stats row */}
      <div className="grid grid-cols-3 gap-3 shrink-0">
        <Card className="p-3">
          <div className="text-xs text-muted-foreground">Avg Trust</div>
          <div className="text-lg font-bold text-foreground">{stats.avgTrustScore}%</div>
        </Card>
        <Card className="p-3">
          <div className="text-xs text-muted-foreground">Max Blast Radius</div>
          <div className="text-lg font-bold text-foreground">${stats.maxBlastRadius.toLocaleString()}</div>
        </Card>
        <Card className="p-3">
          <div className="text-xs text-muted-foreground">Transactions</div>
          <div className="text-lg font-bold text-foreground">{stats.transactionsLastHour}</div>
        </Card>
      </div>

      {/* Graph Canvas */}
      <div
        ref={containerRef}
        className="flex-1 min-h-[400px] rounded-xl border border-border bg-card/40 overflow-hidden relative"
      >
        <DelegationGraph
          nodes={nodes}
          edges={edges}
          pulsingIds={pulsingIds}
          txnRef={txnRef}
          width={size.width}
          height={size.height}
          onNodeClick={handleNodeClick}
        />
      </div>

      <AgentSlideOver
        agent={selectedAgent}
        open={slideOpen}
        onClose={() => setSlideOpen(false)}
        onKill={killAgent}
      />
    </div>
  );
}