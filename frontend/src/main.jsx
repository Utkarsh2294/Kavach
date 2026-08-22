import React from 'react';
import ReactDOM from 'react-dom/client';
import { RouterProvider } from 'react-router-dom';
import { router } from './router';
import { AuthProvider } from './hooks/useAuth';
import './index.css';

// Start MSW in development
async function enableMocking() {
  if (import.meta.env.DEV && import.meta.env.VITE_USE_MOCKS === 'true') {
    try {
      const { worker } = await import('./mocks/browser');
      return worker.start({ onUnhandledRequest: 'bypass' });
    } catch (error) {
      console.warn('MSW not setup yet, skipping mocking');
    }
  }
}

enableMocking().then(() => {
  ReactDOM.createRoot(document.getElementById('root')).render(
    <React.StrictMode>
      <AuthProvider><RouterProvider router={router} /></AuthProvider>
    </React.StrictMode>
  );
});
