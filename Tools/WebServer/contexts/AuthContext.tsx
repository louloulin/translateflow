import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { AuthService, User, LoginRequest, RegisterRequest, LoginResponse } from '../services/AuthService';

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
  login: (credentials: LoginRequest) => Promise<void>;
  register: (data: RegisterRequest) => Promise<void>;
  logout: () => Promise<void>;
  refreshUser: () => Promise<void>;
  clearError: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Initialize auth state on mount
  useEffect(() => {
    const initAuth = async () => {
      const storedUser = AuthService.getStoredUser();
      const token = AuthService.getStoredToken();

      if (storedUser && token) {
        setUser(storedUser);
        // Optionally verify token is still valid
        try {
          const currentUser = await AuthService.getCurrentUser(token);
          setUser(currentUser);
        } catch {
          // Token invalid, clear storage
          AuthService.clearTokens();
          setUser(null);
        }
      }
      setIsLoading(false);
    };

    initAuth();
  }, []);

  const login = async (credentials: LoginRequest) => {
    setIsLoading(true);
    setError(null);
    try {
      const response: LoginResponse = await AuthService.login(credentials);
      AuthService.setTokens(response.access_token, response.refresh_token, response.user);
      setUser(response.user);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Login failed';
      setError(message);
      throw err;
    } finally {
      setIsLoading(false);
    }
  };

  const register = async (data: RegisterRequest) => {
    setIsLoading(true);
    setError(null);
    try {
      const response: LoginResponse = await AuthService.register(data);
      AuthService.setTokens(response.access_token, response.refresh_token, response.user);
      setUser(response.user);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Registration failed';
      setError(message);
      throw err;
    } finally {
      setIsLoading(false);
    }
  };

  const logout = async () => {
    const token = AuthService.getStoredToken();
    if (token) {
      try {
        await AuthService.logout(token);
      } catch {
        // Ignore logout errors
      }
    }
    AuthService.clearTokens();
    setUser(null);
  };

  const clearError = () => setError(null);

  const refreshUser = async () => {
    const token = AuthService.getStoredToken();
    if (!token) return;

    try {
      const currentUser = await AuthService.getUserProfile(token);
      setUser(currentUser);
      localStorage.setItem('user', JSON.stringify(currentUser));
    } catch (err) {
      console.error('Failed to refresh user:', err);
    }
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        isAuthenticated: !!user,
        isLoading,
        error,
        login,
        register,
        logout,
        refreshUser,
        clearError,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export const getAuthToken = (): string | null => {
  return AuthService.getStoredToken();
};
