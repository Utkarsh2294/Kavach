import React, { useEffect, useState } from 'react';
import { CheckCircle2, CircleAlert, CloudCog, LockKeyhole, MonitorCog, Save, ShieldCheck, UserRound } from 'lucide-react';
import { useAuth } from '@/hooks/useAuth';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Input } from '@/components/ui/input';

export function SettingsPage() {
  const { user, updateProfile, logout } = useAuth();
  const [name, setName] = useState(user?.name || '');
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const [health, setHealth] = useState(null);

  useEffect(() => { setName(user?.name || ''); }, [user?.name]);
  useEffect(() => {
    let cancelled = false;
    fetch('/health').then((response) => response.json()).then((body) => { if (!cancelled) setHealth(body); }).catch(() => { if (!cancelled) setHealth({ status: 'unavailable' }); });
    return () => { cancelled = true; };
  }, []);

  const saveProfile = async (event) => {
    event.preventDefault();
    setSaving(true); setError(''); setMessage('');
    try {
      await updateProfile(name.trim());
      setMessage('Profile updated.');
    } catch (err) {
      setError(err.message || 'Unable to update profile');
    } finally { setSaving(false); }
  };

  return (
    <div className="space-y-6 animate-fade-in">
      <div><h1 className="text-2xl font-bold tracking-tight text-foreground">Settings</h1><p className="mt-1 text-sm text-muted-foreground">Manage your profile and review the security posture of this Kavach workspace.</p></div>

      {(message || error) && <div role="status" className={`rounded-lg border px-4 py-3 text-sm ${error ? 'border-danger-500/35 bg-danger-500/10 text-danger-300' : 'border-success-500/30 bg-success-500/10 text-success-300'}`}>{error || message}</div>}

      <div className="grid grid-cols-1 gap-4 xl:grid-cols-3">
        <Card className="p-5 xl:col-span-2"><div className="flex items-center gap-2"><UserRound className="h-4 w-4 text-primary-400" /><h2 className="text-sm font-semibold text-foreground">Profile</h2></div><form className="mt-5 space-y-4" onSubmit={saveProfile}><div><label htmlFor="profile-name" className="mb-1.5 block text-xs font-medium text-muted-foreground">Display name</label><Input id="profile-name" value={name} onChange={(event) => setName(event.target.value)} minLength={1} maxLength={120} required /></div><div><p className="text-xs font-medium text-muted-foreground">Email</p><p className="mt-1 text-sm text-foreground">{user?.email || '—'}</p><p className="mt-1 text-xs text-muted-foreground">Email changes require an administrator workflow and are not available in this console.</p></div><Button type="submit" disabled={saving || !name.trim()}><Save className="mr-2 h-4 w-4" />{saving ? 'Saving…' : 'Save profile'}</Button></form></Card>
        <Card className="p-5"><div className="flex items-center gap-2"><ShieldCheck className="h-4 w-4 text-primary-400" /><h2 className="text-sm font-semibold text-foreground">Access</h2></div><dl className="mt-5 space-y-4 text-sm"><SettingValue label="Role" value={user?.role || '—'} /><SettingValue label="Organization ID" value={user?.organizationId || '—'} mono /><SettingValue label="Workspace theme" value="Dark only" /></dl></Card>
      </div>

      <div className="grid grid-cols-1 gap-4 xl:grid-cols-2">
        <Card className="p-5"><div className="flex items-center gap-2"><CloudCog className="h-4 w-4 text-primary-400" /><h2 className="text-sm font-semibold text-foreground">Service health</h2><Badge variant={health?.status === 'ok' ? 'success' : health ? 'danger' : 'outline'} className="ml-auto">{health?.status === 'ok' ? 'Operational' : health ? 'Needs attention' : 'Checking'}</Badge></div><div className="mt-5 grid grid-cols-3 gap-3"><HealthItem label="Database" ok={health?.database_ready} ready={Boolean(health)} /><HealthItem label="Redis" ok={health?.redis_ready} ready={Boolean(health)} /><HealthItem label="Risk models" ok={health?.ml_ready} ready={Boolean(health)} /></div></Card>
        <Card className="p-5"><div className="flex items-center gap-2"><MonitorCog className="h-4 w-4 text-primary-400" /><h2 className="text-sm font-semibold text-foreground">Console preferences</h2></div><div className="mt-5 rounded-lg border border-border bg-muted/25 p-4"><div className="flex items-center justify-between gap-4"><div><p className="text-sm font-medium text-foreground">Dark operational theme</p><p className="mt-1 text-xs leading-5 text-muted-foreground">Kavach is intentionally dark-only to maintain a consistent high-contrast operations interface.</p></div><Badge variant="success">Locked</Badge></div></div></Card>
      </div>

      <Card className="border-danger-500/25 p-5"><div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between"><div><div className="flex items-center gap-2"><LockKeyhole className="h-4 w-4 text-danger-400" /><h2 className="text-sm font-semibold text-foreground">Session</h2></div><p className="mt-1 text-sm text-muted-foreground">Sign out on this device to revoke the current session.</p></div><Button variant="destructive" onClick={logout}>Sign out</Button></div></Card>
    </div>
  );
}

function SettingValue({ label, value, mono }) {
  return <div><dt className="text-xs font-medium text-muted-foreground">{label}</dt><dd className={`mt-1 truncate text-sm capitalize text-foreground ${mono ? 'font-mono text-xs normal-case' : ''}`}>{value}</dd></div>;
}

function HealthItem({ label, ok, ready }) {
  const Icon = ok ? CheckCircle2 : CircleAlert;
  return <div className="rounded-lg border border-border bg-muted/20 p-3"><Icon className={`h-4 w-4 ${ok ? 'text-success-400' : ready ? 'text-danger-400' : 'text-muted-foreground'}`} /><p className="mt-2 text-xs font-medium text-foreground">{label}</p><p className="mt-1 text-xs text-muted-foreground">{ready ? ok ? 'Ready' : 'Unavailable' : 'Checking'}</p></div>;
}
