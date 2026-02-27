// Auth Service - API calls for authentication
const API_BASE = '/api/v1/auth';

export interface LoginRequest {
  username: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  user: {
    id: string;
    email: string;
    username: string;
    role: string;
  };
}

export interface RegisterRequest {
  email: string;
  username: string;
  password: string;
}

export interface User {
  id: string;
  email: string;
  username: string;
  role: string;
  avatar_url?: string;
  tenant_id?: string;
  status: string;
  email_verified: boolean;
  created_at: string;
  last_login_at?: string;
}

export const AuthService = {
  async login(credentials: LoginRequest): Promise<LoginResponse> {
    const formData = new URLSearchParams();
    formData.append('username', credentials.username);
    formData.append('password', credentials.password);

    const res = await fetch(`${API_BASE}/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: formData,
    });

    if (!res.ok) {
      const error = await res.json().catch(() => ({ detail: 'Login failed' }));
      throw new Error(error.detail || 'Login failed');
    }

    return await res.json();
  },

  async register(data: RegisterRequest): Promise<LoginResponse> {
    const res = await fetch(`${API_BASE}/register`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
    });

    if (!res.ok) {
      const error = await res.json().catch(() => ({ detail: 'Registration failed' }));
      throw new Error(error.detail || 'Registration failed');
    }

    return await res.json();
  },

  async getCurrentUser(token: string): Promise<User> {
    const res = await fetch(`${API_BASE}/me`, {
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    });

    if (!res.ok) {
      throw new Error('Failed to get current user');
    }

    return await res.json();
  },

  async refreshToken(refreshToken: string): Promise<LoginResponse> {
    const formData = new URLSearchParams();
    formData.append('refresh_token', refreshToken);

    const res = await fetch(`${API_BASE}/refresh`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: formData,
    });

    if (!res.ok) {
      throw new Error('Token refresh failed');
    }

    return await res.json();
  },

  async logout(token: string): Promise<void> {
    await fetch(`${API_BASE}/logout`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    });
  },

  async getOAuthUrl(provider: string): Promise<{ authorization_url: string; state: string }> {
    const res = await fetch(`${API_BASE}/oauth/${provider}/authorize`);
    if (!res.ok) {
      throw new Error('Failed to get OAuth URL');
    }
    return await res.json();
  },

  // Token management
  getStoredToken(): string | null {
    return localStorage.getItem('access_token');
  },

  getStoredRefreshToken(): string | null {
    return localStorage.getItem('refresh_token');
  },

  getStoredUser(): User | null {
    const userStr = localStorage.getItem('user');
    return userStr ? JSON.parse(userStr) : null;
  },

  setTokens(accessToken: string, refreshToken: string, user: User): void {
    localStorage.setItem('access_token', accessToken);
    localStorage.setItem('refresh_token', refreshToken);
    localStorage.setItem('user', JSON.stringify(user));
  },

  clearTokens(): void {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user');
  },
};
