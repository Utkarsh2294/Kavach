import { createContext, useContext, useEffect, useMemo, useState } from 'react';

const AuthContext = createContext(null);
const SESSION_KEY = 'kavach.auth.session';

async function request(path, options = {}) {
  const response = await fetch(path, {
    headers: { 'Content-Type': 'application/json', ...(options.headers || {}) },
    ...options,
  });
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(payload.error?.message || payload.detail?.message || 'Request failed');
  return payload;
}

export function AuthProvider({ children }) {
  const [session, setSession] = useState(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    try {
      const saved = sessionStorage.getItem(SESSION_KEY);
      if (saved) setSession(JSON.parse(saved));
    } catch {
      sessionStorage.removeItem(SESSION_KEY);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const save = (payload) => {
    const next = { user: payload.user, accessToken: payload.accessToken, refreshToken: payload.refreshToken };
    sessionStorage.setItem(SESSION_KEY, JSON.stringify(next));
    setSession(next);
    return payload.user;
  };

  const value = useMemo(() => ({
    user: session?.user ?? null,
    session,
    accessToken: session?.accessToken ?? null,
    isAuthenticated: Boolean(session?.accessToken),
    isLoading,
    async login(email, password) {
      return save(await request('/api/v1/auth/login', {
        method: 'POST', body: JSON.stringify({ email, password }),
      }));
    },
    async signup(name, email, password) {
      return save(await request('/api/v1/auth/signup', {
        method: 'POST', body: JSON.stringify({ name, email, password }),
      }));
    },
    async logout() {
      try {
        await request('/api/v1/auth/logout', {
          method: 'POST', headers: session?.accessToken ? { Authorization: `Bearer ${session.accessToken}` } : {},
        });
      } finally {
        sessionStorage.removeItem(SESSION_KEY);
        setSession(null);
      }
    },
    async refresh() {
      if (!session?.refreshToken) throw new Error('No refresh session');
      const tokens = await request('/api/v1/auth/refresh', {
        method: 'POST', body: JSON.stringify({ refreshToken: session.refreshToken }),
      });
      const next = { ...session, accessToken: tokens.accessToken, refreshToken: tokens.refreshToken };
      sessionStorage.setItem(SESSION_KEY, JSON.stringify(next));
      setSession(next);
      return next.accessToken;
    },
  }), [session, isLoading]);

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const value = useContext(AuthContext);
  if (!value) throw new Error('useAuth must be used inside AuthProvider');
  return value;
}
