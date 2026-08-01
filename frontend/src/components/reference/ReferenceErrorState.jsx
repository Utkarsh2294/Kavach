import { AlertCircle, RefreshCw } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';

/* Phase 01C — error state. Recoverable inline message, not a full-page
   crash. Used by every real network call in Phase 11. */

export function ReferenceErrorState({
  title = 'Something went wrong',
  description = 'We could not reach the server. Please try again.',
  onRetry,
  className,
}) {
  return (
    <div className={cn('flex flex-col items-center justify-center text-center py-10 px-6', className)}>
      <div className="w-12 h-12 rounded-2xl flex items-center justify-center mb-4 bg-danger-500/10">
        <AlertCircle className="h-6 w-6 text-danger-500" />
      </div>
      <h3 className="text-base font-semibold text-foreground">{title}</h3>
      <p className="mt-1 text-sm text-muted-foreground max-w-sm">{description}</p>
      {onRetry && (
        <Button variant="outline" size="sm" className="mt-4" onClick={onRetry}>
          <RefreshCw className="h-3.5 w-3.5 mr-1.5" />
          Retry
        </Button>
      )}
    </div>
  );
}
