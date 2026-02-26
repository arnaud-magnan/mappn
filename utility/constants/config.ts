/**
 * App configuration constants.
 *
 * API_BASE_URL is read from the EXPO_PUBLIC_API_URL environment variable,
 * which is set in .env and injected by Expo at build time.
 */

/** Base URL for all API requests. Falls back to localhost for development. */
export const API_BASE_URL: string =
  process.env.EXPO_PUBLIC_API_URL ?? 'http://localhost:8000';

/** GPS coordinate submission interval in milliseconds (15 seconds). */
export const GPS_INTERVAL_MS = 15000;

/** GPS accuracy threshold in meters. Pings with worse accuracy are skipped. */
export const GPS_ACCURACY_THRESHOLD_M = 100;

/**
 * TanStack Query stale time constants (in milliseconds).
 *
 * These control how long data is considered fresh before a background
 * refetch is triggered.
 */
export const STALE_TIME = {
  /** Nearby places - moderate refresh rate (5 minutes). */
  PLACES: 5 * 60 * 1000,
  /** Place detail - longer cache (10 minutes). */
  PLACE_DETAIL: 10 * 60 * 1000,
  /** Live busyness / forecast - shorter refresh (1 minute). */
  BUSYNESS: 1 * 60 * 1000,
  /** User stats - moderate refresh (5 minutes). */
  USER_STATS: 5 * 60 * 1000,
  /** Achievements - longer cache (10 minutes). */
  ACHIEVEMENTS: 10 * 60 * 1000,
  /** Visit history - moderate refresh (5 minutes). */
  VISITS: 5 * 60 * 1000,
  /** Journal entries - moderate refresh (5 minutes). */
  JOURNAL: 5 * 60 * 1000,
  /** Heatmap data - longer cache (10 minutes). */
  HEATMAP: 10 * 60 * 1000,
  /** City passport - longer cache (10 minutes). */
  PASSPORT: 10 * 60 * 1000,
} as const;

/** SecureStore keys used for token persistence. */
export const SECURE_STORE_KEYS = {
  ACCESS_TOKEN: 'access_token',
  REFRESH_TOKEN: 'refresh_token',
} as const;
