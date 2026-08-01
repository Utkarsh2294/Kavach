import { createContext, useContext } from 'react';

export const LiveDataContext = createContext(null);

export function useLiveDataContext() {
  const ctx = useContext(LiveDataContext);
  if (!ctx) throw new Error('useLiveDataContext must be used within LiveDataProvider');
  return ctx;
}
