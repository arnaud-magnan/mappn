/**
 * Zustand auth store with SecureStore persistence.
 *
 * Manages authentication state: user profile, access/refresh tokens,
 * and authenticated status. Tokens are persisted to expo-secure-store
 * (Keychain on iOS, Keystore on Android) for security.
 */

import { create } from 'zustand';
import * as SecureStore from 'expo-secure-store';

import { UserResponse } from '../types/api';
import { SECURE_STORE_KEYS } from '../constants/config';

export interface AuthState {
  /** Current authenticated user profile, or null if not logged in. */
  user: UserResponse | null;
  /** Whether the user is currently authenticated. */
  isAuthenticated: boolean;
  /** Short-lived JWT access token for API requests. */
  accessToken: string | null;
  /** Long-lived JWT refresh token for obtaining new access tokens. */
  refreshToken: string | null;
  /** Whether the session expired and the user was redirected to login. */
  sessionExpired: boolean;

  /**
   * Store new token pair in state and SecureStore.
   * Called after successful login, registration, or token refresh.
   */
  setTokens: (accessToken: string, refreshToken: string) => Promise<void>;

  /**
   * Clear all auth state and remove tokens from SecureStore.
   * Called on logout or when token refresh fails.
   */
  clearAuth: () => Promise<void>;

  /**
   * Load tokens from SecureStore into state.
   * Called on app startup to restore authentication session.
   */
  loadTokens: () => Promise<void>;

  /** Set the user profile in state. */
  setUser: (user: UserResponse | null) => void;

  /** Set sessionExpired flag (true when refresh fails and user is redirected to login). */
  setSessionExpired: (expired: boolean) => void;
}

export const useAuthStore = create<AuthState>((set, get) => ({
  user: null,
  isAuthenticated: false,
  accessToken: null,
  refreshToken: null,
  sessionExpired: false,

  setTokens: async (accessToken: string, refreshToken: string) => {
    await SecureStore.setItemAsync(
      SECURE_STORE_KEYS.ACCESS_TOKEN,
      accessToken
    );
    await SecureStore.setItemAsync(
      SECURE_STORE_KEYS.REFRESH_TOKEN,
      refreshToken
    );
    set({
      accessToken,
      refreshToken,
      isAuthenticated: true,
    });
  },

  clearAuth: async () => {
    await SecureStore.deleteItemAsync(SECURE_STORE_KEYS.ACCESS_TOKEN);
    await SecureStore.deleteItemAsync(SECURE_STORE_KEYS.REFRESH_TOKEN);
    set({
      user: null,
      isAuthenticated: false,
      accessToken: null,
      refreshToken: null,
    });
  },

  loadTokens: async () => {
    const accessToken = await SecureStore.getItemAsync(
      SECURE_STORE_KEYS.ACCESS_TOKEN
    );
    const refreshToken = await SecureStore.getItemAsync(
      SECURE_STORE_KEYS.REFRESH_TOKEN
    );

    if (accessToken && refreshToken) {
      set({
        accessToken,
        refreshToken,
        isAuthenticated: true,
      });
    }
  },

  setUser: (user: UserResponse | null) => {
    set({ user });
  },

  setSessionExpired: (expired: boolean) => {
    set({ sessionExpired: expired });
  },
}));
