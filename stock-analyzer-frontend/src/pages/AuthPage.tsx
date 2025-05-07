// src/pages/AuthPage.tsx
import React, { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import LoginForm from '../components/auth/LoginForm';
import SignupForm from '../components/auth/SignupForm';
import { useAuth } from '../contexts/AuthContext';

const AuthPage: React.FC = () => {
  const [isLoginView, setIsLoginView] = React.useState(true);
  const { isAuthenticated, isLoading: authIsLoading } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    if (isAuthenticated && !authIsLoading) { // Redirect if authenticated and not in initial loading state
      navigate('/dashboard');
    }
  }, [isAuthenticated, authIsLoading, navigate]);

  if (authIsLoading) {
    return ( // Optional: Show a loading spinner for the whole page during initial auth check
        <div className="flex justify-center items-center min-h-[calc(100vh-200px)]"> {/* Adjust height as needed */}
            <div className="animate-spin rounded-full h-16 w-16 border-t-4 border-blue-500"></div>
        </div>
    );
  }
  if (isAuthenticated) return null; // Or redirect, already handled by useEffect

  const toggleView = () => setIsLoginView(!isLoginView);

  return (
    <div className="flex flex-col items-center justify-center pt-8 md:pt-12">
      <div className="w-full max-w-md bg-white dark:bg-gray-800 shadow-xl rounded-lg p-8">
        <h2 className="text-3xl font-bold text-center text-gray-800 dark:text-white mb-8">
          {isLoginView ? 'Welcome Back!' : 'Create Your Account'}
        </h2>
        
        {isLoginView ? (
          <LoginForm />
        ) : (
          <SignupForm onSignupSuccess={() => setIsLoginView(true)} /> // Switch to login after successful signup
        )}

        <div className="mt-6 text-center">
          <button
            onClick={toggleView}
            className="text-sm text-blue-600 dark:text-blue-400 hover:underline focus:outline-none"
          >
            {isLoginView ? "Don't have an account? Sign Up" : 'Already have an account? Login'}
          </button>
        </div>
      </div>
    </div>
  );
};

export default AuthPage;