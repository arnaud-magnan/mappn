/**
 * Zustand store for map UI state.
 *
 * Manages the visible map region, currently selected place, and active
 * category filters. Used by the Map tab screen and related components.
 */

import { create } from 'zustand';

/** Map region matching react-native-maps Region type. */
export interface MapRegion {
  latitude: number;
  longitude: number;
  latitudeDelta: number;
  longitudeDelta: number;
}

export interface MapState {
  /** Current visible map region. */
  region: MapRegion;
  /** ID of the currently selected place (shown in bottom sheet), or null. */
  selectedPlaceId: number | null;
  /** Set of active category filter strings (e.g., "restaurant", "park"). */
  activeFilters: string[];

  /**
   * Update the visible map region.
   *
   * @param region - The new map region.
   */
  setRegion: (region: MapRegion) => void;

  /**
   * Set the selected place ID (when a pin is tapped).
   *
   * @param placeId - The place ID to select, or null to deselect.
   */
  setSelectedPlace: (placeId: number | null) => void;

  /**
   * Toggle a category filter on or off.
   * If the filter is currently active, it is removed.
   * If the filter is not active, it is added.
   *
   * @param filter - The category string to toggle (e.g., "restaurant").
   */
  toggleFilter: (filter: string) => void;
}

/** Default map region centered on Paris, France. */
const DEFAULT_REGION: MapRegion = {
  latitude: 48.8566,
  longitude: 2.3522,
  latitudeDelta: 0.05,
  longitudeDelta: 0.05,
};

export const useMapStore = create<MapState>((set) => ({
  region: DEFAULT_REGION,
  selectedPlaceId: null,
  activeFilters: [],

  setRegion: (region: MapRegion) => {
    set({ region });
  },

  setSelectedPlace: (placeId: number | null) => {
    set({ selectedPlaceId: placeId });
  },

  toggleFilter: (filter: string) => {
    set((state) => {
      const isActive = state.activeFilters.includes(filter);
      return {
        activeFilters: isActive
          ? state.activeFilters.filter((f) => f !== filter)
          : [...state.activeFilters, filter],
      };
    });
  },
}));
