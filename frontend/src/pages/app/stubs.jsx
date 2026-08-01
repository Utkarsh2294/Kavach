import { useParams, Link } from 'react-router-dom';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';

// A generic wrapper for stub pages
const StubPage = ({ title, phase, description, children }) => (
  <div className="space-y-6">
    <div className="flex items-center gap-4">
      <h1 className="text-2xl font-bold tracking-tight text-zinc-100">{title}</h1>
      <Badge variant="outline" className="border-indigo-500 text-indigo-400 bg-indigo-500/10">
        {phase}
      </Badge>
    </div>
    <Card className="border-zinc-800 bg-zinc-900/50">
      <CardHeader>
        <CardTitle className="text-zinc-100">Coming Soon</CardTitle>
        <CardDescription className="text-zinc-400">{description}</CardDescription>
      </CardHeader>
      {children && <CardContent>{children}</CardContent>}
    </Card>
  </div>
);

export const DashboardPage = () => <StubPage title="Dashboard" phase="Phase 03" description="Overview — bento grid + graph preview" />;
export const GraphPage = () => <StubPage title="Delegation Graph" phase="Phase 03" description="Full delegation graph visualization" />;
export const AgentsPage = () => <StubPage title="Agents" phase="Phase 03" description="Agent fleet management list" />;
export const AgentDetailPage = () => {
  const { id } = useParams();
  return (
    <StubPage title="Agent Details" phase="Phase 03" description="Agent details, policies, history, sub-agents">
      <p className="text-zinc-300 font-mono text-sm mt-4">Agent ID: {id}</p>
    </StubPage>
  );
};
export const PoliciesPage = () => <StubPage title="Policies" phase="Phase 04" description="Policy management list" />;
export const PolicyBuilderPage = () => {
  const { id } = useParams();
  return (
    <StubPage title={id ? "Edit Policy" : "New Policy Builder"} phase="Phase 04" description="Visual policy builder">
      {id && <p className="text-zinc-300 font-mono text-sm mt-4">Policy ID: {id}</p>}
    </StubPage>
  );
};
export const KillSwitchPage = () => <StubPage title="Kill Switch" phase="Phase 04" description="Emergency kill switch console" />;
export const BlastRadiusPage = () => <StubPage title="Blast Radius" phase="Phase 04" description="Blast radius impact simulator" />;
export const DryRunPage = () => <StubPage title="Dry Run Sandbox" phase="Phase 04" description="Policy dry-run sandbox" />;
export const AuditLogPage = () => <StubPage title="Audit Log" phase="Phase 04" description="Tamper-evident audit log explorer" />;
export const CompliancePage = () => <StubPage title="Compliance" phase="Phase 04" description="NIST RMF compliance dashboard" />;
export const EscalationsPage = () => <StubPage title="Escalations" phase="Phase 04" description="Human-in-the-loop escalation queue" />;
export const SandboxPage = () => <StubPage title="Sandbox" phase="Phase 09" description="Sandbox environment controls" />;
export const SettingsPage = () => <StubPage title="Settings" phase="Phase 04" description="Organization & user settings, API keys" />;

export const LandingPage = () => <StubPage title="Landing Page" phase="Phase 01" description="Public landing page" />;
export const LoginPage = () => <StubPage title="Login" phase="Phase 02" description="User login" />;
export const SignupPage = () => <StubPage title="Sign Up" phase="Phase 02" description="User registration" />;
export const ForgotPasswordPage = () => <StubPage title="Forgot Password" phase="Phase 02" description="Password recovery" />;
export const ResetPasswordPage = () => <StubPage title="Reset Password" phase="Phase 02" description="Set new password" />;

export const NotFoundPage = () => (
  <div className="flex flex-col items-center justify-center min-h-[60vh] space-y-4">
    <h1 className="text-4xl font-bold text-zinc-100">404</h1>
    <p className="text-zinc-400">Page not found</p>
    <Link to="/app/dashboard" className="text-indigo-400 hover:text-indigo-300 transition-colors">
      Return to Dashboard
    </Link>
  </div>
);
