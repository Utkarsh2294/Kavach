import { TrendingUp, TrendingDown } from 'lucide-react';
import { AnimatedCounter } from '@/components/AnimatedCounter';
import { cn } from '@/lib/utils';

/* Phase 01C — metric card. The bento-grid tile used on the dashboard.
   Token-driven: only semantic colors (`bg-card`, `border-border`,
   `text-foreground`, `text-muted-foreground`) plus an accent color passed
   via the `accent` prop using a status token name (primary | success |
   warning | danger | info). */
const ACCENT_COLOR = {
  primary: 'var(--color-primary-500)',
  success: 'var(--color-success-500)',
  warning: 'var(--color-warning-500)',
  danger: 'var(--color-danger-500)',
  info: 'var(--color-info-500)',
};

export function ReferenceMetricCard({
  label,
  value,
  accent = 'primary',
  delta,
  deltaLabel,
  prefix = '',
  suffix = '',
  decimals = 0,
}) {
  const color = ACCENT_COLOR[accent] ?? ACCENT_COLOR.primary;
  const positive = (delta ?? 0) >= 0;
  return (
    <div className="rounded-xl border border-border bg-card text-card-foreground shadow-sm p-5 relative overflow-hidden">
      <div className="absolute top-0 left-0 w-full h-px" style={{ backgroundColor: color, opacity: 0.5 }} />
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="text-xs font-medium text-muted-foreground">{label}</div>
          <div className="text-3xl font-bold text-foreground mt-2">
            <AnimatedCounter value={value} prefix={prefix} suffix={suffix} decimals={decimals} />
          </div>
        </div>
        <div
          className="w-9 h-9 rounded-lg flex items-center justify-center shrink-0"
          style={{ backgroundColor: `color-mix(in srgb, ${color} 16%, transparent)` }}
        >
          <span className="h-2.5 w-2.5 rounded-full" style={{ backgroundColor: color }} />
        </div>
      </div>
      {delta != null && (
        <div className="flex items-center gap-1.5 mt-3 text-xs">
          <span
            className={cn(
              'inline-flex items-center gap-0.5 font-mono',
              positive ? 'text-success-500' : 'text-danger-500',
            )}
          >
            {positive ? <TrendingUp className="h-3 w-3" /> : <TrendingDown className="h-3 w-3" />}
            {positive ? '+' : ''}{delta}%
          </span>
          {deltaLabel && <span className="text-muted-foreground">{deltaLabel}</span>}
        </div>
      )}
    </div>
  );
}
