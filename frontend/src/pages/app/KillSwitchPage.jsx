import React, { useState, useRef, useEffect, useCallback } from 'react';
import { Shield, AlertTriangle } from 'lucide-react';
import { useLiveDataContext } from '@/context/useLiveDataContext';
import { DelegationGraph } from '@/components/DelegationGraph';
import { agentNodeColor } from '@/mocks/livedata';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { SegmentedControl } from '@/components/ui/segmented-control';
import { Separator } from '@/components/ui/separator';

const KILL_MODES = [
  { value: 'node', label: 'Revoke Node' },
  { value: 'subtree', label: 'Revoke Subtree' },
  { value: 'fleet', label: 'Revoke Fleet' },
];

export function KillSwitchPage() {
  const {
    nodes, edges, pulsingIds, txnRef, agents,
    killAgent, killSubtree, killFleet, getAffectedAgents,
  } = useLiveDataContext();

  const [mode, setMode] = useState('node');
  const [selectedNodeId, setSelectedNodeId] = useState(null);
  const [confirmStep, setConfirmStep] = useState(0);
  const containerRef = useRef(null);
  const [size, setSize] = useState({ width: 900, height: 420 });

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
    setSelectedNodeId(node.id);
    setConfirmStep(0);
  }, []);

  const handleModeChange = useCallback((v) => {
    setMode(v);
    setConfirmStep(0);
  }, []);

  const selectedAgent = selectedNodeId ? agents[selectedNodeId] : null;
  const affectedIds = selectedNodeId ? getAffectedAgents(mode, selectedNodeId) : [];
  const affectedAgents = affectedIds.map(id => agents[id]).filter(Boolean);

  const handleExecute = () => {
    if (confirmStep === 0) {
      setConfirmStep(1);
      return;
    }
    if (mode === 'fleet') {
      killFleet();
    } else if (mode === 'subtree' && selectedNodeId) {
      killSubtree(selectedNodeId);
    } else if (mode === 'node' && selectedNodeId) {
      killAgent(selectedNodeId);
    }
    setConfirmStep(0);
    setSelectedNodeId(null);
  };

  const modeNames = { node: 'Revoke Node', subtree: 'Revoke Subtree', fleet: 'Revoke Fleet' };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <h1 className="text-2xl font-bold tracking-tight text-foreground">Kill Switch Console</h1>
          <Badge variant="danger" className="text-xs">
            <Shield className="mr-1 h-3 w-3" />
            Restricted
          </Badge>
        </div>
        <SegmentedControl
          options={KILL_MODES}
          value={mode}
          onChange={handleModeChange}
        />
      </div>

      <Card className="overflow-hidden">
        <div ref={containerRef} className="relative w-full" style={{ height: 420 }}>
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
      </Card>

      {!selectedAgent ? (
        <Card>
          <CardContent className="py-10 text-center text-muted-foreground">
            Select an agent node on the graph and choose a kill mode
          </CardContent>
        </Card>
      ) : (
        <Card className="border-danger-500/40">
          <CardContent className="p-5 space-y-4">
            <div className="flex items-center gap-3">
              <AlertTriangle className="h-5 w-5 text-danger-500" />
              <Badge variant="danger" className="text-xs uppercase tracking-wider">
                {modeNames[mode]}
              </Badge>
              <span className="text-sm text-muted-foreground">
                Target: <span className="font-semibold text-foreground">{selectedAgent.name}</span>
              </span>
            </div>

            <Separator />

            <div>
              <div className="text-sm font-medium text-foreground mb-2">
                Affected Agents ({affectedAgents.length})
              </div>
              <div className="max-h-[200px] overflow-y-auto space-y-1.5">
                {affectedAgents.map(agent => (
                  <div
                    key={agent.id}
                    className="flex items-center gap-2 text-sm px-3 py-1.5 rounded-md bg-muted/40"
                  >
                    <span
                      className="w-2 h-2 rounded-full shrink-0"
                      style={{ backgroundColor: agentNodeColor(agent) }}
                    />
                    <span className="text-foreground">{agent.name}</span>
                    <span className="text-muted-foreground text-xs capitalize ml-auto">
                      {agent.active ? 'active' : 'revoked'}
                    </span>
                  </div>
                ))}
              </div>
            </div>

            <Separator />

            <div className="flex items-center gap-3">
              <Button
                variant="destructive"
                onClick={handleExecute}
                className="px-6"
              >
                <AlertTriangle className="mr-2 h-4 w-4" />
                {confirmStep === 0
                  ? 'I understand the impact'
                  : 'Execute Revoke — IRREVERSIBLE'}
              </Button>
              <Button
                variant="ghost"
                onClick={() => { setSelectedNodeId(null); setConfirmStep(0); }}
              >
                Cancel
              </Button>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}