import { useState, useEffect, useCallback } from 'react';

/* Phase 01A — class-based theme control. `:root` is dark by default;
   applying the `.light` class on <html> switches to light tokens.
   The choice is persisted to localStorage. */
const STORAGE_KEY = 'kavach-theme';
const DEFAULT_THEME = 'dark'; // control-room default

function readInitialTheme() {
  if (typeof window === 'undefined') return DEFAULT_THEME;
  const saved = localStorage.getItem(STORAGE_KEY);
  if (saved === 'light' || saved === 'dark') return saved;
  // Respect OS preference only on first visit, before any explicit choice.
  if (window.matchMedia?.('(prefers-color-scheme: light)').matches) return 'light';
  return DEFAULT_THEME;
}

function applyThemeClass(theme) {
  if (typeof document === 'undefined') return;
  const root = document.documentElement;
  if (theme === 'light') root.classList.add('light');
  else root.classList.remove('light');
  root.style.colorScheme = theme;
}

export function useTheme() {
  const [theme, setThemeState] = useState(readInitialTheme);

  useEffect(() => {
    applyThemeClass(theme);
    localStorage.setItem(STORAGE_KEY, theme);
  }, [theme]);

  const toggleTheme = useCallback(() => {
    setThemeState((t) => (t === 'dark' ? 'light' : 'dark'));
  }, []);

  const setTheme = useCallback((next) => {
    setThemeState(next === 'light' ? 'light' : 'dark');
  }, []);

  return { theme, toggleTheme, setTheme, isDark: theme === 'dark' };
}
