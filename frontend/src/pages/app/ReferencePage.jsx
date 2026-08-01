import { Link } from 'react-router-dom';
import { ArrowLeft } from 'lucide-react';
import { ThemeToggle } from '@/components/ui/theme-toggle';
import { AnimatedCounter } from '@/components/AnimatedCounter';
import { RiskBadge } from '@/components/ui/risk-badge';
import { ReferenceMetricCard } from '@/components/reference/ReferenceMetricCard';
import { ReferenceRiskRowGallery } from '@/components/reference/ReferenceRiskRow';
import { ReferenceGraphTooltip, fakeAgent } from '@/components/reference/ReferenceGraphTooltip';
import { ReferenceEmptyState } from '@/components/reference/ReferenceEmptyState';
import { ReferenceSkeleton, ReferenceMetricSkeleton, ReferenceRowSkeleton } from '@/components/reference/ReferenceSkeleton';
import { ReferenceErrorState } from '@/components/reference/ReferenceErrorState';

/* Phase 01C — reference showcase. Wired at /app/reference so the visual
   contract is verifiable in both themes. Throwaway after later phases build
   the real screens, but kept in-repo until then. */

export function ReferencePage() {
  return (
    <div className="space-y-8 max-w-5xl mx-auto animate-fade-in">
      <div className="flex items-center justify-between">
        <div>
          <Link to="/app/dashboard" className="inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground mb-2 transition-colors">
            <ArrowLeft className="h-3.5 w-3.5" /> Back to dashboard
          </Link>
          <h1 className="text-2xl font-bold tracking-tight text-foreground">Reference Showcase</h1>
          <p className="text-muted-foreground text-sm mt-1">
            The 6 Phase 01 reference components in one place — flip theme to verify parity.
          </p>
        </div>
        <ThemeToggle />
      </div>

      {/* Risk badges in every threshold */}
      <Section title="Risk-score badge (canonical thresholds)">
        <div className="flex flex-wrap items-center gap-3">
          <RiskBadge score={18} />
          <RiskBadge score={45} />
          <RiskBadge score={72} />
          <RiskBadge score={91} />
          <RiskBadge score={18} showScore={false} showLabel />
        </div>
      </Section>

      {/* Metric cards */}
      <Section title="Metric card (bento-grid tile)">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <ReferenceMetricCard label="Active Agents" value={12} accent="primary" delta={3} deltaLabel="vs last week" decimals={0} />
          <ReferenceMetricCard label="Transactions" value={184} accent="info" delta={12} deltaLabel="in last hour" decimals={0} />
          <ReferenceMetricCard label="Avg Trust Score" value={87} accent="success" suffix="%" decimals={0} />
          <ReferenceMetricCard label="Max Blast Radius" value={62500} accent="warning" prefix="$" delta={-4} deltaLabel="vs cap" decimals={0} />
        </div>
      </Section>

      {/* Risk row */}
      <Section title="Table row with risk-score badge">
        <ReferenceRiskRowGallery />
      </Section>

      {/* Graph node tooltip */}
      <Section title="Graph-node tooltip">
        <div className="bg-background border border-border rounded-xl p-8 inline-flex">
          <ReferenceGraphTooltip agent={fakeAgent} />
        </div>
      </Section>

      {/* Empty / Loading / Error states */}
      <Section title="Empty / Loading / Error states">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="rounded-xl border border-border bg-card">
            <ReferenceEmptyState
              title="No agents yet"
              description="Once agents start transacting they will show up here as a delegation graph."
              variant="muted"
            />
          </div>
          <div className="rounded-xl border border-border bg-card p-5">
            <div className="text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-3">Loading</div>
            <ReferenceMetricSkeleton />
            <div className="mt-3 space-y-1 border-t border-border pt-3">
              <ReferenceRowSkeleton />
              <ReferenceRowSkeleton />
            </div>
          </div>
          <div className="rounded-xl border border-border bg-card">
            <ReferenceErrorState
              onRetry={() => {}}
              description="A network error occurred. Your changes are safe — retry will re-attempt the call."
            />
          </div>
        </div>
      </Section>
    </div>
  );
}

function Section({ title, children }) {
  return (
    <section>
      <h2 className="text-sm font-semibold text-foreground mb-3 uppercase tracking-wider">{title}</h2>
      {children}
    </section>
  );
}
