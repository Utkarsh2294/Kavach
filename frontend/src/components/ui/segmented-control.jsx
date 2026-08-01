import { cn } from '@/lib/utils';

/* Phase 01B — segmented control (view toggles: graph view / list view).
   Radix ToggleGroup is available but a lightweight controlled impl keeps
   keyboard navigation tight and avoids the cva noise. */

export function SegmentedControl({
  options,
  value,
  onChange,
  size = 'md',
  className,
}) {
  const padding = size === 'sm' ? 'px-2.5 py-1 text-xs' : 'px-3.5 py-1.5 text-sm';
  return (
    <div
      role="tablist"
      className={cn(
        'inline-flex items-center rounded-lg border border-border bg-muted/70 p-0.5',
        className,
      )}
    >
      {options.map((opt) => {
        const selected = opt.value === value;
        return (
          <button
            key={opt.value}
            role="tab"
            aria-selected={selected}
            onClick={() => onChange?.(opt.value)}
            className={cn(
              'rounded-md font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring',
              padding,
              selected
                ? 'bg-card text-foreground shadow-sm'
                : 'text-muted-foreground hover:text-foreground',
            )}
          >
            {opt.icon && <opt.icon className="inline -mt-0.5 mr-1 h-3.5 w-3.5" />}
            {opt.label}
          </button>
        );
      })}
    </div>
  );
}
