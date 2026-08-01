import React, { useState } from 'react';
import { Shield, Activity, TrendingUp, Hash } from 'lucide-react';
import {
  Sheet, SheetContent, SheetHeader, SheetTitle, SheetDescription,
} from '@/components/ui/sheet';
import { Button } from '@/components/ui/button';
import { Separator } from '@/components/ui/separator';
import { agentNodeColor, agentStatusLabel } from '@/mocks/livedata';

export function AgentSlideOver({ agent, open, onClose, onKill }) {
  const [confirmingKill, setConfirmingKill] = useState(false);

  const handleKill = () => {
    if (!confirmingKill) {
      setConfirmingKill(true);
      return;
    }
    onKill?.(agent?.id);
    setConfirmingKill(false);
    onClose?.();
  };

  if (!agent) {
    return (
      <Sheet open={open} onOpenChange={(v) => { if (!v) onClose?.(); }}>
        <SheetContent side="right" className="w-[400px] sm:max-w-[400px] p-0" />
      </Sheet>
    );
  }

  const status = agentStatusLabel(agent);
  const color = agentNodeColor(agent);

  return (
    <Sheet open={open} onOpenChange={(v) => { if (!v) { setConfirmingKill(false); onClose?.(); } }}>
      <SheetContent side="right" className="w-[400px] sm:max-w-[400px] p-0 flex flex-col">
        <SheetHeader className="p-6 pb-2">
          <SheetTitle className="text-xl flex items-center gap-3">
            <div
              className="w-3 h-3 rounded-full shrink-0 ring-2 ring-border"
              style={{ backgroundColor: color }}
            />
            {agent.name}
          </SheetTitle>
          <SheetDescription className="capitalize">
            {agent.agentType} · {agent.role}
          </SheetDescription>
        </SheetHeader>

        <div className="px-6 py-4 flex-1 space-y-5 overflow-y-auto">
          <div className="grid grid-cols-2 gap-3">
            <StatBox icon={Shield} label="Status" value={status} valueColor={color} />
            <StatBox icon={TrendingUp} label="Trust Score" value={`${Math.round(agent.trustScore)}%`}
              valueColor={agent.trustScore >= 80 ? 'var(--color-success-500)' : agent.trustScore >= 50 ? 'var(--color-warning-500)' : 'var(--color-danger-400)'}
            />
            <StatBox icon={Hash} label="Spend Cap" value={`$${agent.cap.toLocaleString()}`} />
            <StatBox icon={Activity} label="Total Spend" value={`$${agent.totalSpend.toFixed(0)}`} />
          </div>

          <Separator />

          <div>
            <div className="flex justify-between text-sm mb-1.5">
              <span className="text-muted-foreground">Spend vs Cap</span>
              <span className="text-foreground font-mono">
                ${agent.totalSpend.toFixed(0)} / ${agent.cap.toLocaleString()}
              </span>
            </div>
            <div className="w-full h-2.5 bg-muted rounded-full overflow-hidden">
              <div
                className="h-full rounded-full transition-all duration-500"
                style={{
                  width: `${Math.min(100, (agent.totalSpend / agent.cap) * 100)}%`,
                  backgroundColor: agent.totalSpend / agent.cap > 0.85 ? 'var(--color-danger-500)' : agent.totalSpend / agent.cap > 0.6 ? 'var(--color-warning-500)' : 'var(--color-success-500)',
                }}
              />
            </div>
          </div>

          <Separator />

          {agent.parentId && (
            <div className="text-sm">
              <span className="text-muted-foreground">Parent:</span>{' '}
              <span className="text-foreground font-mono">{agent.parentId}</span>
            </div>
          )}
        </div>

        <div className="px-6 py-4 border-t border-border">
          {agent.active ? (
            <Button
              onClick={handleKill}
              variant={confirmingKill ? 'destructive' : 'outline'}
              className="w-full"
            >
              <Shield className="mr-2 h-4 w-4" />
              {confirmingKill ? 'Confirm Kill — IRREVERSIBLE' : 'Kill Switch'}
            </Button>
          ) : (
            <div className="text-center text-muted-foreground text-sm py-2">
              Agent is revoked
            </div>
          )}
        </div>
      </SheetContent>
    </Sheet>
  );
}

function StatBox({ icon: Icon, label, value, valueColor }) {
  return (
    <div className="bg-muted/50 rounded-lg p-3 space-y-1">
      <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
        <Icon className="h-3 w-3" />
        {label}
      </div>
      <div className="text-sm font-semibold capitalize" style={valueColor ? { color: valueColor } : undefined}>
        {value}
      </div>
    </div>
  );
}
