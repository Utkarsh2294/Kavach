import React, { useState, useRef, useEffect, useCallback } from 'react';
import { Link } from 'react-router-dom';
import {
  Bot, Activity, Shield, Target, ArrowUpRight, TrendingUp,
} from 'lucide-react';
import { useLiveDataContext } from '@/context/useLiveDataContext';
import { AnimatedCounter } from '@/components/AnimatedCounter';
import { DelegationGraph } from '@/components/DelegationGraph';
import { AgentSlideOver } from '@/components/AgentSlideOver';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { BentoGrid, BentoCard } from '@/components/ui/bento-grid';
import {
  agentNodeColor,
  decisionBadgeVariant,
  riskScoreToColor,
} from '@/mocks/livedata';

export function DashboardPage() {
  const { nodes, edges, transactions, stats, agents, killAgent, pulsingIds, txnRef } = useLiveDataContext();
  const [selectedAgent, setSelectedAgent] = useState(null);
  const [slideOpen, setSlideOpen] = useState(false);
  const previewRef = useRef(null);
  const [previewSize, setPreviewSize] = useState({ width: 520, height: 280 });

  useEffect(() => {
    const el = previewRef.current;
    if (!el) return;
    const ro = new ResizeObserver(entries => {
      for (const e of entries) {
        setPreviewSize({
          width: e.contentRect.width - 24,
          height: Math.min(280, e.contentRect.height - 24),
        });
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
    <div className="space-y-6 animate-fade-in">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-foreground">Dashboard</h1>
        <p className="text-muted-foreground text-sm mt-1">Live fleet overview — simulated data</p>
      </div>

      {/* Bento grid */}
      <BentoGrid columns={4}>
        <StatTile
          icon={Bot}
          label="Active Agents"
          accent="primary"
          value={stats.activeAgents}
          sub={`${stats.totalAgents} total`}
          decimals={0}
        />
        <StatTile
          icon={Activity}
          label="Transactions"
          accent="info"
          value={stats.transactionsLastHour}
          sub="last 30 entries"
          decimals={0}
        />
        <StatTile
          icon={Shield}
          label="Avg Trust Score"
          accent="success"
          value={stats.avgTrustScore}
          suffix="%"
          decimals={0}
        />
        <StatTile
          icon={Target}
          label="Max Blast Radius"
          accent="warning"
          value={stats.maxBlastRadius}
          prefix="$"
          decimals={0}
        />
      </BentoGrid>

      {/* Main row: graph preview + transaction feed */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Graph preview */}
        <Card className="lg:col-span-2 p-3 relative min-h-[320px]">
          <div className="flex items-center justify-between mb-2 px-1">
            <div className="flex items-center gap-2">
              <TrendingUp className="h-4 w-4 text-muted-foreground" />
              <span className="text-sm font-medium text-foreground">Delegation Graph</span>
              <Badge variant="outline" className="text-xs">
                live
              </Badge>
            </div>
            <Link
              to="/app/graph"
              className="text-xs inline-flex items-center gap-1 text-muted-foreground hover:text-foreground transition-colors"
            >
              Full view <ArrowUpRight className="h-3 w-3" />
            </Link>
          </div>
          <div ref={previewRef} className="relative w-full h-[280px] rounded-lg overflow-hidden bg-background/40">
            <DelegationGraph
              nodes={nodes}
              edges={edges}
              pulsingIds={pulsingIds}
              txnRef={txnRef}
              width={previewSize.width}
              height={previewSize.height}
              onNodeClick={handleNodeClick}
            />
          </div>
        </Card>

        {/* Transaction feed */}
        <Card className="flex flex-col min-h-[320px]">
          <div className="flex items-center justify-between p-4 pb-3 border-b border-border">
            <span className="text-sm font-medium text-foreground">Transaction Feed</span>
            <Badge variant="outline" className="text-xs">
              last 30
            </Badge>
          </div>
          <div className="flex-1 overflow-y-auto max-h-[300px]">
            {transactions.length === 0 ? (
              <div className="p-6 text-center text-muted-foreground text-sm">
                Waiting for transactions…
              </div>
            ) : (
              <TransactionFeed transactions={transactions} />
            )}
          </div>
        </Card>
      </div>

      {/* Agent overview row */}
      <Card>
        <div className="p-4 pb-3 border-b border-border flex items-center justify-between">
          <span className="text-sm font-medium text-foreground">Agents</span>
          <Link
            to="/app/agents"
            className="text-xs inline-flex items-center gap-1 text-muted-foreground hover:text-foreground transition-colors"
          >
            All agents <ArrowUpRight className="h-3 w-3" />
          </Link>
        </div>
        <div className="p-4 grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-3">
          {Object.values(agents)
            .sort((a, b) => b.cap - a.cap)
            .map(agent => (
              <AgentWidget
                key={agent.id}
                agent={agent}
                onClick={() => {
                  setSelectedAgent(agent);
                  setSlideOpen(true);
                }}
              />
            ))}
        </div>
      </Card>

      <AgentSlideOver
        agent={selectedAgent}
        open={slideOpen}
        onClose={() => setSlideOpen(false)}
        onKill={killAgent}
      />
    </div>
  );
}

/* ---- Bento tile with animated counter ---- */
const ACCENT_COLOR = {
  primary: 'var(--color-primary-500)',
  success: 'var(--color-success-500)',
  warning: 'var(--color-warning-500)',
  danger:  'var(--color-danger-500)',
  info:    'var(--color-info-500)',
};

function StatTile({ icon: Icon, label, accent = 'primary', value, prefix, suffix, sub, decimals }) {
  const color = ACCENT_COLOR[accent] ?? ACCENT_COLOR.primary;
  return (
    <BentoCard className="p-5 relative overflow-hidden">
      <div className="absolute top-0 left-0 w-full h-px" style={{ backgroundColor: color, opacity: 0.5 }} />
      <div className="flex items-start justify-between">
        <div>
          <div className="text-xs font-medium text-muted-foreground">{label}</div>
          <div className="text-3xl font-bold mt-2" style={{ color }}>
            <AnimatedCounter
              value={value}
              prefix={prefix || ''}
              suffix={suffix || ''}
              decimals={decimals ?? 0}
            />
          </div>
        </div>
        <div
          className="w-9 h-9 rounded-lg flex items-center justify-center"
          style={{ backgroundColor: `color-mix(in srgb, ${color} 16%, transparent)` }}
        >
          <Icon className="h-4 w-4" style={{ color }} />
        </div>
      </div>
      {sub && (
        <div className="text-xs text-muted-foreground mt-3">{sub}</div>
      )}
    </BentoCard>
  );
}

/* ---- Transaction feed ---- */
function TransactionFeed({ transactions }) {
  return (
    <div className="divide-y divide-border/60">
      {transactions.map(tx => (
        <div
          key={tx.id}
          className="px-4 py-2.5 flex items-center gap-3 hover:bg-muted/40 transition-colors animate-fade-in"
        >
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-0.5">
              <span className="text-xs text-foreground font-medium truncate">{tx.agentName}</span>
              <Badge variant={decisionBadgeVariant(tx.decision)} className="text-[10px] py-0.5 px-1.5 capitalize">
                {tx.decision}
              </Badge>
            </div>
            <div className="flex items-center gap-2 text-[10px] text-muted-foreground">
              <span className="font-mono">${tx.amount.toFixed(2)}</span>
              <span className="truncate">{tx.merchantCategory}</span>
            </div>
          </div>
          <div className="text-right shrink-0">
            <div className="text-xs font-mono font-semibold" style={{ color: riskScoreToColor(tx.riskScore) }}>
              {tx.riskScore}
            </div>
            <div className="text-[10px] text-muted-foreground">risk</div>
          </div>
        </div>
      ))}
    </div>
  );
}

/* ---- Agent widget: spend bar + trust ticker ---- */
function AgentWidget({ agent, onClick }) {
  const color = agentNodeColor(agent);
  const trustColor = agent.trustScore >= 80
    ? 'var(--color-success-500)'
    : agent.trustScore >= 50
    ? 'var(--color-warning-500)'
    : 'var(--color-danger-500)';

  const spendPct = Math.min(100, (agent.totalSpend / agent.cap) * 100);

  return (
    <button
      onClick={onClick}
      className="text-left bg-muted/40 hover:bg-muted/70 border border-border hover:border-muted-foreground/40 rounded-lg p-3 transition-colors w-full"
    >
      <div className="flex items-start justify-between gap-2 mb-2">
        <div className="flex items-center gap-2 min-w-0">
          <span className="w-2 h-2 rounded-full shrink-0" style={{ backgroundColor: color }} />
          <span className="text-sm font-medium text-foreground truncate">{agent.name}</span>
        </div>
        <span className="text-[10px] text-muted-foreground capitalize shrink-0">{agent.role}</span>
      </div>

      {/* Trust ticker */}
      <div className="flex items-center gap-2 mb-2">
        <span className="text-[10px] text-muted-foreground shrink-0 w-10">Trust</span>
        <div className="h-1.5 flex-1 bg-muted rounded-full overflow-hidden">
          <div
            className="h-full rounded-full transition-all duration-700"
            style={{ width: `${agent.trustScore}%`, backgroundColor: trustColor }}
          />
        </div>
        <span className="text-[10px] font-mono w-7 text-right" style={{ color: trustColor }}>
          {Math.round(agent.trustScore)}
        </span>
      </div>

      {/* Spend bar */}
      <div className="flex items-center gap-2">
        <span className="text-[10px] text-muted-foreground shrink-0 w-10">Spend</span>
        <div className="h-1.5 flex-1 bg-muted rounded-full overflow-hidden">
          <div
            className="h-full rounded-full transition-all duration-700"
            style={{
              width: `${spendPct}%`,
              backgroundColor: spendPct > 85 ? 'var(--color-danger-500)' : spendPct > 60 ? 'var(--color-warning-500)' : 'var(--color-primary-500)',
            }}
          />
        </div>
        <span className="text-[10px] font-mono text-muted-foreground w-16 text-right">
          ${agent.totalSpend.toFixed(0)}
        </span>
      </div>
    </button>
  );
}