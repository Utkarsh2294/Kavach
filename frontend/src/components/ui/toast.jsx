import { Toaster as SonnerToaster, toast } from 'sonner';

/* Phase 01B — toast/notification system. sonner is already a dependency;
   this wires it into our token set. Used by kill-switch confirmations
   (Phase 04) and transaction denials (Phase 10). Re-exports toast() so
   call sites import from `@/components/ui/toast` rather than sonner directly,
   so theme/scope decisions live in one place. */

export function Toaster({ position = 'bottom-right', ...props }) {
  return (
    <SonnerToaster
      position={position}
      toastOptions={{
        style: {
          background: 'var(--card)',
          color: 'var(--card-foreground)',
          border: '1px solid var(--border)',
        },
      }}
      {...props}
    />
  );
}

export { toast };
