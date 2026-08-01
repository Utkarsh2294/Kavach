import React from 'react';
import { LiveDataContext } from './useLiveDataContext';
import { useLiveData } from '@/mocks/livedata';

export function LiveDataProvider({ children }) {
  const data = useLiveData();
  return (
    <LiveDataContext.Provider value={data}>
      {children}
    </LiveDataContext.Provider>
  );
}
