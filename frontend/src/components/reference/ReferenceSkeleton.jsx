/* Phase 01C — loading skeleton. Shimmer placeholders, not spinners.
   Drop-in for cards and table rows. */

import { cn } from '@/lib/utils';

export function ReferenceSkeleton({ className }) {
  return <div className={cn('animate-shimmer rounded-lg h-4 w-full', className)} />;
}

export function ReferenceMetricSkeleton() {
  return (
    <div className="rounded-xl border border-border bg-card p-5 space-y-3">
      <ReferenceSkeleton className="h-3 w-24" />
      <ReferenceSkeleton className="h-8 w-32" />
      <div className="flex items-center gap-2">
        <ReferenceSkeleton className="h-3 w-10" />
        <ReferenceSkeleton className="h-3 w-16" />
      </div>
    </div>
  );
}

export function ReferenceRowSkeleton() {
  return (
    <div className="px-3.5 py-3 space-y-2">
      <ReferenceSkeleton className="h-3 w-40" />
      <ReferenceSkeleton className="h-2.5 w-24" />
    </div>
  );
}
