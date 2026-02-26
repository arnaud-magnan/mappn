/**
 * Color constants for the Mappn utility app.
 *
 * BUSYNESS_COLORS are used for map pins, histograms, and indicators.
 * Colors are chosen to be distinguishable by colorblind users (protanopia,
 * deuteranopia) and are supplemented by text labels in the UI.
 */

export const BUSYNESS_COLORS = {
  quiet: '#22c55e',
  moderate: '#eab308',
  busy: '#ef4444',
  noData: '#9ca3af',
} as const;

export type BusynessLevel = keyof typeof BUSYNESS_COLORS;

/** Theme colors used across the app. */
export const THEME_COLORS = {
  primary: '#3b82f6',
  secondary: '#6366f1',
  background: '#ffffff',
  surface: '#f9fafb',
  text: '#111827',
  textSecondary: '#6b7280',
  border: '#e5e7eb',
  error: '#ef4444',
  success: '#22c55e',
  warning: '#eab308',
} as const;

/**
 * Legacy theme colors default export.
 * Kept for backward compatibility with template components (e.g., Themed.tsx).
 */
const tintColorLight = '#2f95dc';
const tintColorDark = '#fff';

export default {
  light: {
    text: '#000',
    background: '#fff',
    tint: tintColorLight,
    tabIconDefault: '#ccc',
    tabIconSelected: tintColorLight,
  },
  dark: {
    text: '#fff',
    background: '#000',
    tint: tintColorDark,
    tabIconDefault: '#ccc',
    tabIconSelected: tintColorDark,
  },
};
