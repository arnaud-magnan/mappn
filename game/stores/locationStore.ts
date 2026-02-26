/**
 * Zustand store for GPS location state.
 *
 * Manages the device's current GPS coordinates, accuracy, tracking
 * status, and the active territory-claiming state (set when the player
 * is inside a place's geofence and accumulating dwell time).
 */

import { create } from 'zustand';

/** Active state while a player is inside a geofence and unlocking a place. */
export interface ClaimingState {
  /** Backend place ID being tracked. */
  placeId: number;
  /** Human-readable place name for display in the progress HUD. */
  placeName: string;
  /**
   * Local timestamp (Date.now()) when this place first appeared in a ping
   * response. Used to compute frontend-side progress estimate.
   *
   * Note: progress is an approximation — actual visit confirmation requires
   * 300 seconds of dwell time tracked server-side.
   */
  startedAt: number;
}

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
   * Active claiming state, or null when not inside any geofence.
   * Set by useLocationTracking when a GPS ping returns nearby_places.
   */
  claimingState: ClaimingState | null;

  setLocation: (
    latitude: number,
    longitude: number,
    accuracy: number | null
  ) => void;
  setTracking: (isTracking: boolean) => void;
  setClaimingState: (state: ClaimingState | null) => void;
}

export const useLocationStore = create<LocationState>((set) => ({
  latitude: null,
  longitude: null,
  accuracy: null,
  isTracking: false,
  claimingState: null,

  setLocation: (latitude, longitude, accuracy) => {
    set({ latitude, longitude, accuracy });
  },

  setTracking: (isTracking) => {
    set({ isTracking });
  },

  setClaimingState: (claimingState) => {
    set({ claimingState });
  },
}));
