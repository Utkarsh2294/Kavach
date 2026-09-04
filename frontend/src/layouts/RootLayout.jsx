import { useEffect } from 'react';
import { Outlet } from 'react-router-dom';
import { AuthProvider } from '../hooks/useAuth';
import { Toaster } from '../components/ui/toast';

export function RootLayout() {
  useEffect(() => {
    // Kavach is intentionally a dark-only operations console. Clear a legacy
    // preference so an existing browser session cannot revive light mode.
    document.documentElement.classList.remove('light');
    document.documentElement.style.colorScheme = 'dark';
    localStorage.removeItem('kavach-theme');
  }, []);

  return (
    <AuthProvider>
      <Outlet />
      <Toaster position="bottom-right" />
    </AuthProvider>
  );
}
