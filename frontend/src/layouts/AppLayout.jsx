import React, { useState, useEffect } from 'react';
import { Outlet, Link, useLocation, useNavigate } from 'react-router-dom';
import {
  Shield, LayoutDashboard, Network, Bot, FileText, Power, Target, PlayCircle,
  ScrollText, ShieldCheck, AlertTriangle, FlaskConical, Settings,
  ChevronLeft, ChevronRight, Search, LogOut, Settings as SettingsIcon,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { Switch } from '@/components/ui/switch';
import {
  DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuLabel,
  DropdownMenuSeparator, DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';
import {
  CommandDialog, CommandEmpty, CommandGroup, CommandInput, CommandItem, CommandList,
} from '@/components/ui/command';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { ThemeToggle } from '@/components/ui/theme-toggle';
import { useAuth } from '@/hooks/useAuth';

const NavItem = ({ to, icon: Icon, label, collapsed, active }) => {
  const content = (
    <Link
      to={to}
      className={cn(
        'flex items-center gap-3 px-3 py-2 rounded-lg transition-colors group relative',
        active
          ? 'bg-primary-500/10 text-primary-500 font-medium'
          : 'text-muted-foreground hover:text-foreground hover:bg-muted/70',
      )}
    >
      {active && (
        <div className="absolute left-0 top-1/2 -translate-y-1/2 w-1 h-6 bg-primary-500 rounded-r-full" />
      )}
      <Icon className={cn('h-5 w-5 shrink-0', active ? 'text-primary-500' : 'text-muted-foreground group-hover:text-foreground')} />
      {!collapsed && <span className="truncate">{label}</span>}
    </Link>
  );

  if (collapsed) {
    return (
      <Tooltip delayDuration={0}>
        <TooltipTrigger asChild>{content}</TooltipTrigger>
        <TooltipContent side="right" className="ml-2">
          {label}
        </TooltipContent>
      </Tooltip>
    );
  }
  return content;
};

export function AppLayout() {
  const { logout } = useAuth();
  const [collapsed, setCollapsed] = useState(() => localStorage.getItem('sidebar-collapsed') === 'true');
  const [sandboxMode, setSandboxMode] = useState(false);
  const [cmdOpen, setCmdOpen] = useState(false);
  const location = useLocation();
  const navigate = useNavigate();

  useEffect(() => { localStorage.setItem('sidebar-collapsed', collapsed); }, [collapsed]);

  useEffect(() => {
    const down = (e) => {
      if (e.key === 'k' && (e.metaKey || e.ctrlKey)) {
        e.preventDefault();
        setCmdOpen((open) => !open);
      }
    };
    document.addEventListener('keydown', down);
    return () => document.removeEventListener('keydown', down);
  }, []);

  const navGroups = [
    { label: 'Overview', items: [{ label: 'Dashboard', to: '/app/dashboard', icon: LayoutDashboard }] },
    {
      label: 'Fleet',
      items: [
        { label: 'Graph', to: '/app/graph', icon: Network },
        { label: 'Agents', to: '/app/agents', icon: Bot },
        { label: 'Reference', to: '/app/reference', icon: Shield },
      ],
    },
    {
      label: 'Governance',
      items: [
        { label: 'Policies', to: '/app/policies', icon: FileText },
        { label: 'Kill Switch', to: '/app/kill-switch', icon: Power },
        { label: 'Blast Radius', to: '/app/blast-radius', icon: Target },
        { label: 'Dry-Run', to: '/app/dry-run', icon: PlayCircle },
        { label: 'Audit Log', to: '/app/audit-log', icon: ScrollText },
        { label: 'Compliance', to: '/app/compliance', icon: ShieldCheck },
      ],
    },
    {
      label: 'Review',
      items: [{ label: 'Escalations', to: '/app/escalations', icon: AlertTriangle }],
    },
    {
      label: 'Other',
      items: [
        { label: 'Sandbox', to: '/app/sandbox', icon: FlaskConical },
        { label: 'Settings', to: '/app/settings', icon: Settings },
      ],
    },
  ];

  const handleCommandSelect = (path) => {
    setCmdOpen(false);
    navigate(path);
  };

  return (
    <TooltipProvider>
      <div className="min-h-screen bg-background text-foreground flex font-sans">
        {/* Sidebar */}
        <aside className={cn(
          'flex flex-col border-r border-border bg-[var(--sidebar-bg)] transition-all duration-200 z-20 sticky top-0 h-screen',
          collapsed ? 'w-[68px]' : 'w-[260px]',
        )}>
          <div className="h-16 flex items-center px-4 border-b border-border shrink-0">
            <Link to="/app/dashboard" className="flex items-center gap-2 overflow-hidden">
              <Shield className="h-6 w-6 text-primary-500 shrink-0" />
              {!collapsed && <span className="font-bold text-xl tracking-tight">Kavach</span>}
            </Link>
          </div>

          <div className="flex-1 overflow-y-auto py-4 flex flex-col gap-6 px-2">
            {navGroups.map((group, i) => (
              <div key={i} className="flex flex-col gap-1">
                {!collapsed && (
                  <span className="px-3 text-xs font-semibold text-muted-foreground/80 uppercase tracking-wider mb-1">
                    {group.label}
                  </span>
                )}
                {group.items.map((item) => (
                  <NavItem
                    key={item.to}
                    to={item.to}
                    icon={item.icon}
                    label={item.label}
                    collapsed={collapsed}
                    active={location.pathname.startsWith(item.to)}
                  />
                ))}
              </div>
            ))}
          </div>

          <div className="p-2 border-t border-border shrink-0">
            <button
              onClick={() => setCollapsed(!collapsed)}
              className="w-full flex items-center justify-center p-2 rounded-lg text-muted-foreground hover:text-foreground hover:bg-muted/70 transition-colors"
            >
              {collapsed ? <ChevronRight className="h-5 w-5" /> : <ChevronLeft className="h-5 w-5" />}
            </button>
          </div>
        </aside>

        {/* Main */}
        <div className="flex-1 flex flex-col min-w-0">
          {/* Topbar */}
          <header className="h-[56px] shrink-0 border-b border-border bg-background/80 backdrop-blur sticky top-0 z-10 px-6 flex items-center justify-between">
            <div className="flex-1 flex items-center">
              <ThemeToggle />
            </div>

            <div className="flex-1 flex justify-center">
              <button
                onClick={() => setCmdOpen(true)}
                className="flex items-center gap-2 px-3 py-1.5 w-64 bg-muted/60 border border-border hover:border-muted-foreground/40 rounded-lg text-sm text-muted-foreground transition-colors"
              >
                <Search className="h-4 w-4" />
                <span className="flex-1 text-left">Search...</span>
                <kbd className="hidden sm:inline-flex h-5 items-center gap-1 rounded border border-border bg-muted px-1.5 font-mono text-[10px] font-medium text-muted-foreground">
                  <span className="text-xs">⌘</span>K
                </kbd>
              </button>
            </div>

            <div className="flex-1 flex items-center justify-end gap-6">
              <div className="flex items-center gap-3">
                <FlaskConical className={cn('h-4 w-4', sandboxMode ? 'text-warning-500' : 'text-muted-foreground')} />
                <span className="text-sm font-medium text-foreground">Sandbox</span>
                <Switch checked={sandboxMode} onCheckedChange={setSandboxMode} />
              </div>

              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <button className="flex items-center outline-none">
                    <Avatar className="h-8 w-8 border border-border hover:border-muted-foreground/40 transition-colors">
                      <AvatarImage src="" alt="User" />
                      <AvatarFallback className="bg-primary-500/20 text-primary-500 text-sm font-semibold">US</AvatarFallback>
                    </Avatar>
                  </button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end" className="w-56">
                  <DropdownMenuLabel>
                    <div className="flex flex-col space-y-1">
                      <p className="text-sm font-medium leading-none">User</p>
                      <p className="text-xs leading-none text-muted-foreground">user@example.com</p>
                    </div>
                  </DropdownMenuLabel>
                  <DropdownMenuSeparator />
                  <DropdownMenuItem onClick={() => navigate('/app/settings')} className="cursor-pointer">
                    <SettingsIcon className="mr-2 h-4 w-4 text-muted-foreground" />
                    <span>Settings</span>
                  </DropdownMenuItem>
                  <DropdownMenuSeparator />
                  <DropdownMenuItem onClick={async () => { await logout(); navigate('/login'); }} className="cursor-pointer text-danger-500 focus:text-danger-500">
                    <LogOut className="mr-2 h-4 w-4" />
                    <span>Sign out</span>
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            </div>
          </header>

          <main className="flex-1 p-6 overflow-y-auto relative">
            <Outlet />
          </main>
        </div>

        <CommandDialog open={cmdOpen} onOpenChange={setCmdOpen}>
          <CommandInput placeholder="Type a command or search..." />
          <CommandList>
            <CommandEmpty>No results found.</CommandEmpty>
            {navGroups.map((group) => (
              <CommandGroup key={group.label} heading={group.label}>
                {group.items.map((item) => (
                  <CommandItem
                    key={item.to}
                    onSelect={() => handleCommandSelect(item.to)}
                    className="flex items-center gap-2 cursor-pointer"
                  >
                    <item.icon className="h-4 w-4 text-muted-foreground" />
                    <span>{item.label}</span>
                    <span className="ml-auto text-xs text-muted-foreground">{item.to}</span>
                  </CommandItem>
                ))}
              </CommandGroup>
            ))}
            <CommandGroup heading="Actions">
              <CommandItem
                onSelect={() => { setCollapsed(!collapsed); setCmdOpen(false); }}
                className="flex items-center gap-2 cursor-pointer"
              >
                {collapsed ? <ChevronRight className="h-4 w-4 text-muted-foreground" /> : <ChevronLeft className="h-4 w-4 text-muted-foreground" />}
                <span>Toggle Sidebar</span>
              </CommandItem>
              <CommandItem
                onSelect={() => handleCommandSelect('/login')}
                className="flex items-center gap-2 cursor-pointer text-danger-500 data-[selected=true]:text-danger-500"
              >
                <LogOut className="h-4 w-4" />
                <span>Sign Out</span>
              </CommandItem>
            </CommandGroup>
          </CommandList>
        </CommandDialog>
      </div>
    </TooltipProvider>
  );
}
