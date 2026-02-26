/**
 * Authentication service functions.
 *
 * Provides login, register, refreshToken, and logout operations.
 * All functions interact with the backend auth API endpoints and
 * manage token persistence through the Zustand auth store, which
 * in turn persists tokens to expo-secure-store.
 */

import axios from 'axios';

import { api } from './api';
import { useAuthStore } from '../stores/authStore';
import { AuthTokenResponse } from '../types/api';
import { API_BASE_URL } from '../constants/config';

/**
 * Authenticate a user with email and password.
 *
 * Calls POST /auth/login, stores the returned token pair in the auth store
 * (which persists to SecureStore), and returns the token response.
 *
 * @param email - User's email address.
 * @param password - User's password.
 * @returns The token pair response from the backend.
 * @throws AxiosError if credentials are invalid (401) or network error.
 */
export const login = async (
  email: string,
  password: string
): Promise<AuthTokenResponse> => {
  const { data } = await api.post<AuthTokenResponse>('/auth/login', {
    email,
    password,
  });

  const { setTokens } = useAuthStore.getState();
  await setTokens(data.access_token, data.refresh_token);

  return data;
};

/**
 * Register a new user account.
 *
 * Calls POST /auth/register, stores the returned token pair in the auth store
 * (which persists to SecureStore), and returns the token response.
 *
 * @param email - User's email address.
 * @param username - Desired username (min 3 characters).
 * @param password - Desired password (min 8 characters).
 * @returns The token pair response from the backend.
 * @throws AxiosError if validation fails (422) or email/username taken (409).
 */
export const register = async (
  email: string,
  username: string,
  password: string
): Promise<AuthTokenResponse> => {
  const { data } = await api.post<AuthTokenResponse>('/auth/register', {
    email,
    username,
    password,
  });

  const { setTokens } = useAuthStore.getState();
  await setTokens(data.access_token, data.refresh_token);

  return data;
};

/**
 * Refresh the authentication token pair.
 *
 * Reads the current refresh token from the auth store and sends it
 * to POST /auth/refresh as a Bearer token in the Authorization header
 * (matching the backend's expected format). On success, stores the
 * new token pair.
 *
 * Uses a standalone axios instance (not the api client) to avoid
 * triggering the 401 interceptor during the refresh itself.
 *
 * @returns The new token pair response from the backend.
 * @throws Error if no refresh token is available.
 * @throws AxiosError if the refresh token is invalid or expired.
 */
export const refreshToken = async (): Promise<AuthTokenResponse> => {
  const { refreshToken: currentRefreshToken } = useAuthStore.getState();

  if (!currentRefreshToken) {
    throw new Error('No refresh token available');
  }

  const { data } = await axios.post<AuthTokenResponse>(
    `${API_BASE_URL}/auth/refresh`,
    {},
    {
      headers: {
        Authorization: `Bearer ${currentRefreshToken}`,
      },
    }
  );

  const { setTokens } = useAuthStore.getState();
  await setTokens(data.access_token, data.refresh_token);

  return data;
};

/**
 * Log out the current user.
 *
 * Clears all authentication state from the Zustand store and removes
 * tokens from SecureStore. After calling this, the user will need to
 * log in again.
 */
export const logout = async (): Promise<void> => {
  const { clearAuth } = useAuthStore.getState();
  await clearAuth();
};
