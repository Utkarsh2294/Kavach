import { clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

/**
 * Merge Tailwind classes with clsx — the standard shadcn/ui utility.
 * Use this everywhere instead of raw template literals for className.
 */
export function cn(...inputs) {
  return twMerge(clsx(inputs));
}
