import { Outlet } from 'react-router-dom';
import { AuthProvider } from '../hooks/useAuth';
import { Toaster } from '../components/ui/toast';

export function RootLayout() {
  return (
    <AuthProvider>
      <Outlet />
      <Toaster position="bottom-right" />
    </AuthProvider>
  );
}
