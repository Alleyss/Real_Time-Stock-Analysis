// src/services/authService.ts
import apiClient from './api'; // Your pre-configured Axios instance
import type { UserCreate, User } from '../types/user'; // We'll define these types soon
 // We'll define these types soon
// We'll define these types soon
import type { Token } from '../types/token'; // We'll define these types soon
 // We'll define these types soon

// Define types for request/response payloads (can be moved to a types/ folder)
// Placeholder - these should match your Pydantic schemas more closely
export interface LoginCredentials {
  username: string; // This will be the email for OAuth2PasswordRequestForm
  password: string;
}

// Corresponds to schemas.user.UserCreate from backend
export interface SignupData extends UserCreate {} 

// Corresponds to schemas.token.Token from backend
interface LoginResponse extends Token {}

// Corresponds to schemas.user.User from backend
interface UserResponse extends User {}


export const loginUser = async (credentials: LoginCredentials): Promise<LoginResponse> => {
  // FastAPI's OAuth2PasswordRequestForm expects form data
  const formData = new URLSearchParams();
  formData.append('username', credentials.username); // 'username' here is the email
  formData.append('password', credentials.password);
  // formData.append('grant_type', 'password'); // Optional, depends on server strictness
  // formData.append('scope', ''); // Optional
  // formData.append('client_id', ''); // Optional
  // formData.append('client_secret', ''); // Optional
  
  try {
    const response = await apiClient.post<LoginResponse>('/auth/token', formData, {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
    });
    if (response.data.access_token) {
      localStorage.setItem('accessToken', response.data.access_token);
    }
    return response.data;
  } catch (error) {
    // Axios errors have a 'response' property for API errors
    console.error('Login error:', error);
    if (axios.isAxiosError(error) && error.response) {
      throw new Error(error.response.data.detail || 'Login failed');
    }
    throw new Error('Login failed due to an unexpected error.');
  }
};

export const signupUser = async (userData: SignupData): Promise<UserResponse> => {
  try {
    const response = await apiClient.post<UserResponse>('/auth/register', userData);
    return response.data;
  } catch (error) {
    console.error('Signup error:', error);
    if (axios.isAxiosError(error) && error.response) {
      throw new Error(error.response.data.detail || 'Signup failed');
    }
    throw new Error('Signup failed due to an unexpected error.');
  }
};

export const getCurrentUser = async (): Promise<UserResponse | null> => {
  const token = localStorage.getItem('accessToken');
  if (!token) return null; // No token, so no user

  try {
    // The token is automatically added by the interceptor in api.ts
    const response = await apiClient.get<UserResponse>('/auth/me');
    return response.data;
  } catch (error) {
    console.error('Get current user error:', error);
    // If 401, token might be invalid/expired - interceptor in api.ts might handle some of this
    if (axios.isAxiosError(error) && error.response && error.response.status === 401) {
        localStorage.removeItem('accessToken'); // Clear invalid token
    }
    return null; // Return null if fetching user fails
  }
};

// Helper for checking authentication status
export const isAuthenticated = (): boolean => {
  return !!localStorage.getItem('accessToken');
};

export const logoutUser = (): void => {
  localStorage.removeItem('accessToken');
  // Potentially call a backend /auth/logout endpoint if it exists to invalidate server-side session/token
  // For simple JWT, client-side removal is often sufficient.
};

// Need to import axios to use isAxiosError
import axios from 'axios';