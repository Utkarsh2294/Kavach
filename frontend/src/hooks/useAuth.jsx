import React from 'react';

export const AuthProvider = ({ children }) => {
  return <>{children}</>;
};

export const useAuth = () => {
  return { user: { name: 'Operator', role: 'admin' }, isAuthenticated: true, isLoading: false };
};
