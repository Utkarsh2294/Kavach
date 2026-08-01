import * as React from 'react';
import { cva } from 'class-variance-authority';

import { cn } from '@/lib/utils';

const badgeVariants = cva(
  'inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 focus:ring-offset-background',
  {
    variants: {
      variant: {
        default:
          'border-transparent bg-primary-500 text-primary-foreground hover:bg-primary-600',
        success:
          'border-transparent bg-success-500 text-white hover:bg-success-600',
        warning:
          'border-transparent bg-warning-500 text-white hover:bg-warning-600',
        danger:
          'border-transparent bg-danger-500 text-white hover:bg-danger-600',
        info:
          'border-transparent bg-info-500 text-white hover:bg-info-600',
        secondary:
          'border-transparent bg-secondary text-secondary-foreground hover:bg-secondary/80',
        outline: 'text-foreground border-border',
      },
    },
    defaultVariants: {
      variant: 'default',
    },
  }
);

function Badge({ className, variant, ...props }) {
  return (
    <div className={cn(badgeVariants({ variant }), className)} {...props} />
  );
}

export { Badge, badgeVariants };
