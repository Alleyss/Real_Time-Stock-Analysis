// src/components/auth/LoginForm.tsx
import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import Input from '../common/Input';
import Button from '../common/Button';

const LoginForm: React.FC = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const { login, isLoading, error: authError } = useAuth(); // Get error from context
  const [formError, setFormError] = useState<string | null>(null);
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setFormError(null); // Clear previous form-specific errors
    try {
      await login({ username: email, password }); // username is email for OAuth2PasswordRequestForm
      navigate('/dashboard'); // Redirect on successful login
    } catch (err) {
      // The error is already set in AuthContext, but we can also set a local form error
      // if we want to distinguish API errors handled by AuthContext vs form validation errors
      setFormError(err instanceof Error ? err.message : "Login failed");
      console.error("Login submission error:", err);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      {authError && !formError && <p className="text-red-500 text-sm text-center">{authError}</p>}
      {formError && <p className="text-red-500 text-sm text-center">{formError}</p>}
      <Input
        label="Email address"
        type="email"
        name="email"
        value={email}
        onChange={(e) => setEmail(e.target.value)}
        required
        autoComplete="email"
      />
      <Input
        label="Password"
        type="password"
        name="password"
        value={password}
        onChange={(e) => setPassword(e.target.value)}
        required
        autoComplete="current-password"
      />
      <div>
        <Button type="submit" isLoading={isLoading}>
          Sign in
        </Button>
      </div>
    </form>
  );
};

export default LoginForm;