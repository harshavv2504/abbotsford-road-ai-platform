import { API_BASE_URL } from '../config/api';

const AUTH_TOKEN_KEY = 'authToken';
const USER_KEY = 'user';

interface LoginResponse {
  access_token: string;
  token_type: string;
  user: {
    id: string;
    email: string;
    name: string;
    role: string;
  };
}

/**
 * Login with email and password
 */
export const login = async (email: string, password: string): Promise<string | null> => {
  try {
    const response = await fetch(`${API_BASE_URL}/auth/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ email, password }),
    });

    if (!response.ok) {
      const error = await response.json();
      console.error('Login failed:', error.detail);
      return null;
    }

    const data: LoginResponse = await response.json();
    
    // Store token and user info
    localStorage.setItem(AUTH_TOKEN_KEY, data.access_token);
    localStorage.setItem(USER_KEY, JSON.stringify(data.user));
    
    // Initialize fresh chat session on login
    const { initChat } = await import('./chatService');
    initChat();
    
    return data.access_token;
  } catch (error) {
    console.error('Login error:', error);
    return null;
  }
};

/**
 * Logout and clear stored data
 */
export const logout = async (): Promise<void> => {
  try {
    const token = getToken();
    if (token) {
      await fetch(`${API_BASE_URL}/auth/logout`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });
    }
  } catch (error) {
    console.error('Logout error:', error);
  } finally {
    localStorage.removeItem(AUTH_TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
    
    // Clear chat session on logout
    const { clearSession } = await import('./chatService');
    clearSession();
  }
};

/**
 * Retrieves the authentication token from storage.
 * @returns The token if it exists, otherwise null.
 */
export const getToken = (): string | null => {
  return localStorage.getItem(AUTH_TOKEN_KEY);
};

/**
 * Checks if a user is currently authenticated by verifying the presence of a token.
 * @returns True if the user is authenticated, otherwise false.
 */
export const isAuthenticated = (): boolean => {
  return !!getToken();
};

/**
 * Get stored user information
 */
export const getUser = (): { id: string; email: string; name: string; role: string } | null => {
  const userStr = localStorage.getItem(USER_KEY);
  if (!userStr) return null;
  
  try {
    return JSON.parse(userStr);
  } catch {
    return null;
  }
};

/**
 * Get current user from backend (validates token)
 */
export const getCurrentUser = async () => {
  const token = getToken();
  if (!token) return null;

  try {
    const response = await fetch(`${API_BASE_URL}/auth/me`, {
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    });

    if (!response.ok) {
      // Token is invalid, clear it
      localStorage.removeItem(AUTH_TOKEN_KEY);
      localStorage.removeItem(USER_KEY);
      return null;
    }

    const user = await response.json();
    localStorage.setItem(USER_KEY, JSON.stringify(user));
    return user;
  } catch (error) {
    console.error('Get current user error:', error);
    return null;
  }
};
