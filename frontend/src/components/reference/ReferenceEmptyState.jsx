import { Inbox } from 'lucide-react';
import { cn } from '@/lib/utils';

/* Phase 01C — empty state. Used across Phase 04 (no escalations, no
   transactions matching a filter, etc.). Variant drives icon accent. */
const ICON_COLOR = {
  info: 'var(--color-info-500)',
  warning: 'var(--color-warning-500)',
  muted: 'var(--color-muted-foreground)',
};

export function ReferenceEmptyState({
  title = 'Nothing here yet',
  description,
  action,
  variant = 'muted',
  icon: Icon = Inbox,
  className,
}) {
  const color = ICON_COLOR[variant] ?? ICON_COLOR.muted;
  return (
    <div className={cn('flex flex-col items-center justify-center text-center py-12 px-6', className)}>
      <div
        className="w-14 h-14 rounded-2xl flex items-center justify-center mb-4"
        style={{ backgroundColor: `color-mix(in srgb, ${color} 16%, transparent)` }}
      >
        <Icon className="h-6 w-6" style={{ color }} />
      </div>
      <h3 className="text-base font-semibold text-foreground">{title}</h3>
      {description && (
        <p className="mt-1 text-sm text-muted-foreground max-w-sm">{description}</p>
      )}
      {action && <div className="mt-4">{action}</div>}
    </div>
  );
}
