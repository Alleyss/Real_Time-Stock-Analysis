// src/contexts/AuthContext.tsx
import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import type { User } from '../types/user'; // Your user type
 // Your user type
import { getCurrentUser, loginUser as apiLogin, type LoginCredentials, signupUser as apiSignup, type SignupData, logoutUser as apiLogout } from '../services/authService'; // Your auth service

interface AuthContextType {
  isAuthenticated: boolean;
  user: User | null;
  isLoading: boolean; // To handle loading state during auth checks
  login: (credentials: LoginCredentials) => Promise<void>;
  signup: (userData: SignupData) => Promise<void>;
  logout: () => void;
  error: string | null; // To store login/signup errors
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(false);
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true); // Start true to check initial auth status
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // Check for existing token and fetch user on initial load
    const checkAuthStatus = async () => {
      setIsLoading(true);
      const token = localStorage.getItem('accessToken');
      if (token) {
        try {
          const currentUser = await getCurrentUser();
          if (currentUser) {
            setUser(currentUser);
            setIsAuthenticated(true);
          } else {
            localStorage.removeItem('accessToken'); // Token might be invalid
            setIsAuthenticated(false);
            setUser(null);
          }
        } catch (err) {
          console.error("Error fetching current user on load:", err);
          localStorage.removeItem('accessToken');
          setIsAuthenticated(false);
          setUser(null);
        }
      } else {
        setIsAuthenticated(false);
        setUser(null);
      }
      setIsLoading(false);
    };
    checkAuthStatus();
  }, []);

  const login = async (credentials: LoginCredentials) => {
    setIsLoading(true);
    setError(null);
    try {
      const loginResponse = await apiLogin(credentials);
      if (loginResponse.access_token) {
        // Fetch user details after successful login
        const currentUser = await getCurrentUser();
        setUser(currentUser);
        setIsAuthenticated(true);
      } else {
        // Should not happen if apiLogin throws error on failure
        throw new Error("Login succeeded but no access token received.");
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Login failed');
      setIsAuthenticated(false);
      setUser(null);
      throw err; // Re-throw to allow form to handle it
    } finally {
      setIsLoading(false);
    }
  };

  const signup = async (userData: SignupData) => {
    setIsLoading(true);
    setError(null);
    try {
      const newUser = await apiSignup(userData);
      // Optionally, log the user in directly after signup
      // For now, let's require them to login separately.
      // Or, if signup returns a token:
      // const loginResponse = await apiLogin({ username: userData.email, password: userData.password });
      // if (loginResponse.access_token) { ... }
      console.log("Signup successful, user created:", newUser);
      // You might want to redirect to login or show a success message
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Signup failed');
      throw err; // Re-throw to allow form to handle it
    } finally {
      setIsLoading(false);
    }
  };

  const logout = () => {
    apiLogout(); // Clears localStorage token via authService
    setUser(null);
    setIsAuthenticated(false);
    setError(null);
    // Navigation to /auth will be handled by component or ProtectedRoute
  };

  return (
    <AuthContext.Provider value={{ isAuthenticated, user, isLoading, login, signup, logout, error }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};