import { Sun, Moon } from 'lucide-react';
import { useTheme } from '@/hooks/useTheme';
import { cn } from '@/lib/utils';

/* Phase 01A — theme switcher. Hooked into the topbar of the authenticated
   AppLayout and the footer of the public layout so the choice is reachable
   from anywhere. Persisted via localStorage (default: dark). */

export function ThemeToggle({ className }) {
  const { theme, toggleTheme } = useTheme();
  return (
    <button
      onClick={toggleTheme}
      aria-label={theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'}
      title={theme === 'dark' ? 'Light mode' : 'Dark mode'}
      className={cn(
        'inline-flex h-8 w-8 items-center justify-center rounded-lg',
        'text-muted-foreground hover:text-foreground hover:bg-muted/70 transition-colors',
        'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring',
        className,
      )}
    >
      {theme === 'dark' ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
    </button>
  );
}
