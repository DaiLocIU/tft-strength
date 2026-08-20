/// <reference types="vite/client" />
import axios, { AxiosError, InternalAxiosRequestConfig } from 'axios';
import { Match, TokensResponse, User } from '../types';

const API_BASE_URL = (import.meta.env?.VITE_API_URL as string) || 'http://localhost:3000';

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 10000,
});

const ACCESS_TOKEN_KEY = 'tft_access_token';
const REFRESH_TOKEN_KEY = 'tft_refresh_token';
const USER_KEY = 'tft_user';

let currentAccessToken: string | null = localStorage.getItem(ACCESS_TOKEN_KEY);
let currentRefreshToken: string | null = localStorage.getItem(REFRESH_TOKEN_KEY);
let currentUser: User | null = localStorage.getItem(USER_KEY)
  ? JSON.parse(localStorage.getItem(USER_KEY)!)
  : null;

type AuthListener = () => void;
const authListeners: Set<AuthListener> = new Set();
export const onAuthChange = (listener: AuthListener) => {
  authListeners.add(listener);
  return () => authListeners.delete(listener);
};
const notifyAuth = () => authListeners.forEach((l) => l());

export const getAuthTokens = () => ({
  accessToken: currentAccessToken,
  refreshToken: currentRefreshToken,
});

export const getUser = () => currentUser;

export const setAuthData = (tokens: TokensResponse | null, user?: User | null) => {
  if (tokens) {
    currentAccessToken = tokens.accessToken;
    currentRefreshToken = tokens.refreshToken;
    localStorage.setItem(ACCESS_TOKEN_KEY, tokens.accessToken);
    localStorage.setItem(REFRESH_TOKEN_KEY, tokens.refreshToken);
  } else {
    currentAccessToken = null;
    currentRefreshToken = null;
    localStorage.removeItem(ACCESS_TOKEN_KEY);
    localStorage.removeItem(REFRESH_TOKEN_KEY);
  }

  if (user !== undefined) {
    currentUser = user;
    if (user) {
      localStorage.setItem(USER_KEY, JSON.stringify(user));
    } else {
      localStorage.removeItem(USER_KEY);
    }
  }

  notifyAuth();
};

// Queue helper for handling concurrent requests during silent refresh
let isRefreshing = false;
let failedQueue: Array<{
  resolve: (value?: any) => void;
  reject: (reason?: any) => void;
}> = [];

const processQueue = (error: any, token: string | null = null) => {
  failedQueue.forEach((promise) => {
    if (error) {
      promise.reject(error);
    } else {
      promise.resolve(token);
    }
  });
  failedQueue = [];
};

// 1. REQUEST INTERCEPTOR: Attach Authorization Bearer
apiClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    if (currentAccessToken && !config.headers.Authorization) {
      config.headers.Authorization = `Bearer ${currentAccessToken}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// 2. RESPONSE INTERCEPTOR: Silent Token Refresh on 401
apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as any;

    if (error.response?.status === 401 && !originalRequest._retry) {
      if (originalRequest.url?.includes('/auth/refresh')) {
        setAuthData(null, null);
        return Promise.reject(error);
      }

      if (!currentRefreshToken) {
        return Promise.reject(error);
      }

      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject });
        })
          .then((token) => {
            originalRequest.headers.Authorization = `Bearer ${token}`;
            originalRequest._retry = true;
            return apiClient(originalRequest);
          })
          .catch((err) => Promise.reject(err));
      }

      originalRequest._retry = true;
      isRefreshing = true;

      try {
        const refreshResponse = await axios.post<TokensResponse>(
          `${API_BASE_URL}/auth/refresh`,
          { refreshToken: currentRefreshToken },
          {
            headers: {
              'Content-Type': 'application/json',
              Authorization: `Bearer ${currentRefreshToken}`,
            },
          }
        );

        const newTokens = refreshResponse.data;
        setAuthData(newTokens, currentUser);

        processQueue(null, newTokens.accessToken);

        originalRequest.headers.Authorization = `Bearer ${newTokens.accessToken}`;
        return apiClient(originalRequest);
      } catch (refreshErr) {
        processQueue(refreshErr, null);
        setAuthData(null, null);
        return Promise.reject(refreshErr);
      } finally {
        isRefreshing = false;
      }
    }

    return Promise.reject(error);
  }
);

export const api = {
  // Real Google OAuth Redirect to backend
  loginWithGoogle: () => {
    window.location.href = `${API_BASE_URL}/auth/google`;
  },

  // Fetch Protected Matches
  getMatches: async (): Promise<Match[]> => {
    const res = await apiClient.get<Match[]>('/matches');
    return res.data;
  },

  // Create new match record
  createMatch: async (matchData?: Partial<Match>): Promise<Match> => {
    const defaultData = {
      placement: matchData?.placement ?? 1,
      gameMode: matchData?.gameMode ?? 'Ranked (Set 13)',
      damageDealt: matchData?.damageDealt ?? 145000,
      goldLeft: matchData?.goldLeft ?? 38,
      roundsSurvived: matchData?.roundsSurvived ?? 35,
      augments: matchData?.augments ?? ['Prismatic Ticket', 'Cybernetic Uplink III', 'Binary Airdrop'],
      traits: matchData?.traits ?? [
        { name: 'Rebel', tier: 3, activeCount: 7 },
        { name: 'Sorcerer', tier: 2, activeCount: 4 },
        { name: 'Bruiser', tier: 1, activeCount: 2 },
      ],
      champions: matchData?.champions ?? [
        { name: 'Jinx', cost: 4, stars: 3, items: ['Infinity Edge', 'Guinsoo Rageblade', 'Giant Slayer'] },
        { name: 'Vi', cost: 4, stars: 2, items: ['Warmog Armor', 'Sunfire Cape', 'Dragon Claw'] },
        { name: 'Ekko', cost: 3, stars: 3, items: ['Hand of Justice', 'Ionic Spark'] },
        { name: 'Sevika', cost: 5, stars: 2, items: ['Bloodthirster', 'Titan Resolve'] },
      ],
    };

    const res = await apiClient.post<Match>('/matches', defaultData);
    return res.data;
  },

  // Manual token refresh
  refreshToken: async (): Promise<TokensResponse> => {
    if (!currentRefreshToken) throw new Error('No refresh token available');
    const res = await apiClient.post<TokensResponse>('/auth/refresh', {
      refreshToken: currentRefreshToken,
    });
    setAuthData(res.data, currentUser);
    return res.data;
  },

  // Logout
  logout: async () => {
    try {
      await apiClient.post('/auth/logout');
    } catch {
      // ignore
    } finally {
      setAuthData(null, null);
    }
  },
};
