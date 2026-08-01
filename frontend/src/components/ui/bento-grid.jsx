import { cn } from '@/lib/utils';

/* Phase 01B — bento-grid layout primitive. Mixed-size metric cards compose
   into a 2d-dashboard via the `colSpan` / `rowSpan` slot props. Used by the
   dashboard (Phase 03) and the reference metric card (Phase 01C). */

export function BentoGrid({ children, className, columns = 4, gap = 'md' }) {
  const gapClass = gap === 'sm' ? 'gap-3' : gap === 'lg' ? 'gap-6' : 'gap-4';
  const colClass = {
    2: 'grid-cols-2',
    3: 'grid-cols-3',
    4: 'grid-cols-4',
    6: 'grid-cols-6',
  }[columns] ?? 'grid-cols-4';

  return (
    <div className={cn('grid', colClass, gapClass, className)}>
      {children}
    </div>
  );
}

export function BentoCard({ children, className, colSpan = 1, rowSpan = 1 }) {
  const spanClass = [
    colSpan === 2 && 'sm:col-span-2',
    colSpan === 3 && 'sm:col-span-3',
    colSpan === 4 && 'sm:col-span-4',
    rowSpan === 2 && 'sm:row-span-2',
    rowSpan === 3 && 'sm:row-span-3',
  ].filter(Boolean).join(' ');

  return (
    <div
      className={cn(
        'rounded-xl border border-border bg-card text-card-foreground shadow-sm',
        spanClass,
        className,
      )}
    >
      {children}
    </div>
  );
}
