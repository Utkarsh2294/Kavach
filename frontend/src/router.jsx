import { createBrowserRouter, Navigate } from 'react-router-dom';
import { RootLayout } from './layouts/RootLayout';
import { PublicLayout } from './layouts/PublicLayout';
import { AppLayout } from './layouts/AppLayout';
import { LiveDataProvider } from './context/LiveDataContext';
import { AuthGuard } from './components/auth/AuthGuard';
import { DashboardPage } from './pages/app/DashboardPage';
import { GraphPage } from './pages/app/GraphPage';
import { ReferencePage } from './pages/app/ReferencePage';
import { PolicyBuilderPage } from './pages/app/PolicyBuilderPage';
import { KillSwitchPage } from './pages/app/KillSwitchPage';
import { BlastRadiusPage } from './pages/app/BlastRadiusPage';
import { DryRunPage } from './pages/app/DryRunPage';
import { AuditLogPage } from './pages/app/AuditLogPage';
import { CompliancePage } from './pages/app/CompliancePage';
import { EscalationsPage } from './pages/app/EscalationsPage';
import { AgentsPage, AgentDetailPage } from './pages/app/AgentsPage';
import { PoliciesPage } from './pages/app/PoliciesPage';
import { SandboxPage } from './pages/app/SandboxPage';
import { SettingsPage } from './pages/app/SettingsPage';
import { LoginPage } from './pages/auth/LoginPage';
import { SignupPage } from './pages/auth/SignupPage';
import { ForgotPasswordPage } from './pages/auth/ForgotPasswordPage';
import { ResetPasswordPage } from './pages/auth/ResetPasswordPage';
import LandingPage from './pages/public/LandingPage';
import {
  NotFoundPage,
} from './pages/app/stubs';

export const router = createBrowserRouter([
  {
    element: <RootLayout />,
    children: [
      {
        path: '/',
        element: <PublicLayout />,
        children: [
          { index: true, element: <LandingPage /> },
          { path: 'login', element: <LoginPage /> },
          { path: 'signup', element: <SignupPage /> },
          { path: 'forgot-password', element: <ForgotPasswordPage /> },
          { path: 'reset-password', element: <ResetPasswordPage /> },
        ],
      },
      {
        path: '/app',
        element: (
          <AuthGuard>
            <LiveDataProvider>
              <AppLayout />
            </LiveDataProvider>
          </AuthGuard>
        ),
        children: [
          { index: true, element: <Navigate to="/app/dashboard" replace /> },
          { path: 'dashboard', element: <DashboardPage /> },
          { path: 'graph', element: <GraphPage /> },
          { path: 'reference', element: <ReferencePage /> },
          { path: 'agents', element: <AgentsPage /> },
          { path: 'agents/:id', element: <AgentDetailPage /> },
          { path: 'policies', element: <PoliciesPage /> },
          { path: 'policies/new', element: <PolicyBuilderPage /> },
          { path: 'policies/:id/edit', element: <PolicyBuilderPage /> },
          { path: 'kill-switch', element: <KillSwitchPage /> },
          { path: 'blast-radius', element: <BlastRadiusPage /> },
          { path: 'dry-run', element: <DryRunPage /> },
          { path: 'audit-log', element: <AuditLogPage /> },
          { path: 'compliance', element: <CompliancePage /> },
          { path: 'escalations', element: <EscalationsPage /> },
          { path: 'sandbox', element: <SandboxPage /> },
          { path: 'settings', element: <SettingsPage /> },
        ],
      },
      {
        path: '*',
        element: <NotFoundPage />,
      },
    ],
  },
]);
