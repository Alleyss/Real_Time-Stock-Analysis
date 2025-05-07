// src/components/auth/SignupForm.tsx
import React, { useState } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import Input from '../common/Input';
import Button from '../common/Button';
// Import SignupData if you created a specific type, or use UserCreate directly
// Import SignupData if you created a specific type, or use UserCreate directly
import type { UserCreate } from '../../types/user'; 

interface SignupFormProps {
  onSignupSuccess: () => void; // Callback to toggle to login form
}

const SignupForm: React.FC<SignupFormProps> = ({ onSignupSuccess }) => {
  const [email, setEmail] = useState('');
  const [username, setUsername] = useState(''); // Optional username
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const { signup, isLoading, error: authError } = useAuth();
  const [formError, setFormError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setFormError(null);
    if (password !== confirmPassword) {
      setFormError("Passwords do not match.");
      return;
    }
    if (password.length < 8) {
        setFormError("Password must be at least 8 characters long.");
        return;
    }

    const userData: UserCreate = { email, password };
    if (username.trim()) { // Only include username if it's not empty
        userData.username = username.trim();
    }

    try {
      await signup(userData);
      // alert('Signup successful! Please login.'); // Or a more user-friendly notification
      onSignupSuccess(); // Call the callback to switch view
    } catch (err) {
      setFormError(err instanceof Error ? err.message : "Signup failed");
      console.error("Signup submission error:", err);
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
        label="Username (Optional)"
        type="text"
        name="username"
        value={username}
        onChange={(e) => setUsername(e.target.value)}
        autoComplete="username"
      />
      <Input
        label="Password (min. 8 characters)"
        type="password"
        name="password"
        value={password}
        onChange={(e) => setPassword(e.target.value)}
        required
        autoComplete="new-password"
      />
      <Input
        label="Confirm Password"
        type="password"
        name="confirmPassword"
        value={confirmPassword}
        onChange={(e) => setConfirmPassword(e.target.value)}
        required
        autoComplete="new-password"
      />
      <div>
        <Button type="submit" isLoading={isLoading}>
          Create Account
        </Button>
      </div>
    </form>
  );
};

export default SignupForm;