/**
 * Axios API client with authentication interceptors.
 *
 * Request interceptor: Reads access_token from expo-secure-store and
 * attaches it as a Bearer token in the Authorization header.
 *
 * Response interceptor: Catches 401 responses, attempts to refresh the
 * token via POST /auth/refresh. On success, retries the original request
 * with the new token. On failure, clears auth state and navigates to login.
 */

import axios, { AxiosError, InternalAxiosRequestConfig } from 'axios';
import * as SecureStore from 'expo-secure-store';
import { router } from 'expo-router';

import { API_BASE_URL, SECURE_STORE_KEYS } from '../constants/config';
import { useAuthStore } from '../stores/authStore';
import { AuthTokenResponse } from '../types/api';

/** Axios instance configured with the API base URL. */
export const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 15000,
  headers: {
    'Content-Type': 'application/json',
  },
});

/**
 * Request interceptor: inject Bearer token from SecureStore.
 */
api.interceptors.request.use(
  async (config: InternalAxiosRequestConfig) => {
    const token = await SecureStore.getItemAsync(
      SECURE_STORE_KEYS.ACCESS_TOKEN
    );
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

/**
 * Track whether a token refresh is already in progress to avoid
 * concurrent refresh attempts from multiple failed requests.
 */
let isRefreshing = false;
let failedQueue: Array<{
  resolve: (value: unknown) => void;
  reject: (reason: unknown) => void;
}> = [];

const processQueue = (error: unknown, token: string | null = null) => {
  failedQueue.forEach((pending) => {
    if (error) {
      pending.reject(error);
    } else {
      pending.resolve(token);
    }
  });
  failedQueue = [];
};

/**
 * Response interceptor: handle 401 with token refresh.
 *
 * When a 401 is received:
 * 1. Read refresh_token from SecureStore
 * 2. POST /auth/refresh to obtain new tokens
 * 3. On success: store new tokens, retry the original request
 * 4. On failure: clear auth state, navigate to login screen
 */
api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & {
      _retry?: boolean;
    };

    // Only handle 401 errors, and only retry once
    if (error.response?.status !== 401 || originalRequest._retry) {
      return Promise.reject(error);
    }

    if (isRefreshing) {
      // If a refresh is already in progress, queue this request
      return new Promise((resolve, reject) => {
        failedQueue.push({ resolve, reject });
      })
        .then((token) => {
          if (originalRequest.headers) {
            originalRequest.headers.Authorization = `Bearer ${token}`;
          }
          return api(originalRequest);
        })
        .catch((err) => Promise.reject(err));
    }

    originalRequest._retry = true;
    isRefreshing = true;

    try {
      const refresh_token = await SecureStore.getItemAsync(
        SECURE_STORE_KEYS.REFRESH_TOKEN
      );

      if (!refresh_token) {
        throw new Error('No refresh token available');
      }

      // Request new tokens using the refresh token as Bearer header
      // (matching the backend's expected format: Authorization: Bearer <refresh_token>).
      // Uses a standalone axios instance to avoid triggering the 401 interceptor.
      const { data } = await axios.post<AuthTokenResponse>(
        `${API_BASE_URL}/auth/refresh`,
        {},
        {
          headers: {
            Authorization: `Bearer ${refresh_token}`,
          },
        }
      );

      // Store new tokens
      const { setTokens } = useAuthStore.getState();
      await setTokens(data.access_token, data.refresh_token);

      // Process queued requests with the new token
      processQueue(null, data.access_token);

      // Retry the original request with the new token
      if (originalRequest.headers) {
        originalRequest.headers.Authorization = `Bearer ${data.access_token}`;
      }
      return api(originalRequest);
    } catch (refreshError) {
      // Refresh failed: clear auth and redirect to login
      processQueue(refreshError, null);

      const { clearAuth, setSessionExpired } = useAuthStore.getState();
      await clearAuth();
      setSessionExpired(true);

      // Navigate to login screen.
      // The route path is cast because the (auth) group files are created in Step 8.
      router.replace('/(auth)/login' as const as '/');

      return Promise.reject(refreshError);
    } finally {
      isRefreshing = false;
    }
  }
);

export default api;
