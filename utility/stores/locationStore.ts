/**
 * Zustand store for GPS location state.
 *
 * Manages the device's current GPS coordinates, accuracy, and tracking
 * status. Updated by the location tracking hook when GPS positions
 * are received from expo-location.
 */

import { create } from 'zustand';

export interface LocationState {
  /** Current latitude in decimal degrees, or null if not yet determined. */
  latitude: number | null;
  /** Current longitude in decimal degrees, or null if not yet determined. */
  longitude: number | null;
  /** GPS accuracy in meters, or null if not yet determined. */
  accuracy: number | null;
  /** Whether GPS tracking is currently active. */
  isTracking: boolean;

  /**
   * Update the current GPS position.
   *
   * @param latitude - Latitude in decimal degrees.
   * @param longitude - Longitude in decimal degrees.
   * @param accuracy - Accuracy in meters.
   */
  setLocation: (
    latitude: number,
    longitude: number,
    accuracy: number | null
  ) => void;

  /**
   * Set whether GPS tracking is active.
   *
   * @param isTracking - True when tracking is running, false when stopped.
   */
  setTracking: (isTracking: boolean) => void;
}

export const useLocationStore = create<LocationState>((set) => ({
  latitude: null,
  longitude: null,
  accuracy: null,
  isTracking: false,

  setLocation: (
    latitude: number,
    longitude: number,
    accuracy: number | null
  ) => {
    set({ latitude, longitude, accuracy });
  },

  setTracking: (isTracking: boolean) => {
    set({ isTracking });
  },
}));
