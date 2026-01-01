import React, { useState } from 'react';
import * as authService from '../services/authService';
import { ButtonSpinner } from './Icons';

interface LoginPageProps {
  onLoginSuccess: () => void;
}

export const LoginPage: React.FC<LoginPageProps> = ({ onLoginSuccess }) => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setIsSubmitting(true);

    try {
      const token = await authService.login(email, password);
      if (token) {
        onLoginSuccess();
      } else {
        setError('Invalid email or password. Please try again.');
      }
    } catch (apiError) {
      setError('An unexpected error occurred. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleInputChange = (setter: React.Dispatch<React.SetStateAction<string>>) => (e: React.ChangeEvent<HTMLInputElement>) => {
    setter(e.target.value);
    if (error) {
      setError('');
    }
  };

  return (
    <div className="w-full max-w-md">
      <div
        className="relative w-full p-8 bg-white/10 backdrop-blur-lg rounded-2xl shadow-2xl border border-white/20"
      >
        <h2 className="text-3xl font-bold text-white text-center mb-6">Welcome Back</h2>
        <form onSubmit={handleLogin}>
          <div className="space-y-4">
            <div>
              <label htmlFor="email" className="block text-sm font-medium text-white/80 mb-1">Email</label>
              <input
                type="email"
                id="email"
                value={email}
                onChange={handleInputChange(setEmail)}
                required
                className="w-full px-3 py-2 bg-white/20 text-white rounded-lg border border-white/30 focus:outline-none focus:ring-2 focus:ring-blue-400"
                placeholder="you@example.com"
              />
            </div>
            <div>
              <label htmlFor="password" className="block text-sm font-medium text-white/80 mb-1">Password</label>
              <input
                type="password"
                id="password"
                value={password}
                onChange={handleInputChange(setPassword)}
                required
                className="w-full px-3 py-2 bg-white/20 text-white rounded-lg border border-white/30 focus:outline-none focus:ring-2 focus:ring-blue-400"
                placeholder="••••••••"
              />
            </div>
          </div>
          {error && (
            <p className="mt-4 text-center text-sm text-red-300 bg-red-500/20 p-2 rounded-md">
              {error}
            </p>
          )}
          <button
            type="submit"
            disabled={isSubmitting}
            className="w-full mt-6 py-2.5 bg-blue-600 text-white rounded-lg font-semibold hover:bg-blue-700 transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 focus:ring-offset-transparent flex items-center justify-center disabled:bg-blue-400 disabled:cursor-wait"
          >
            {isSubmitting ? <ButtonSpinner /> : 'Login'}
          </button>
        </form>
      </div>
    </div>
  );
};
