/**
 * TanStack Query hook for fetching nearby places.
 *
 * Fetches places from GET /places/nearby based on the user's current
 * map region coordinates. Uses a composite queryKey including location
 * and category for proper cache invalidation.
 */

import { useQuery } from '@tanstack/react-query';

import { getNearbyPlaces } from '../services/placesService';
import { PlaceResponse } from '../types/api';
import { STALE_TIME } from '../constants/config';

export interface UseNearbyPlacesParams {
  /** Latitude of the map center. */
  lat: number | null;
  /** Longitude of the map center. */
  lon: number | null;
  /** Search radius in meters. */
  radius: number;
  /** Optional category filter (e.g., "restaurant"). */
  category?: string;
}

/**
 * Fetch nearby places with TanStack Query caching.
 *
 * The query is disabled when lat or lon is null (no location available).
 * Results are cached with a 5-minute stale time per the config.
 *
 * @param params - Location and filter parameters.
 * @returns TanStack Query result with PlaceResponse[] data.
 */
export const useNearbyPlaces = ({
  lat,
  lon,
  radius,
  category,
}: UseNearbyPlacesParams) => {
  return useQuery<PlaceResponse[]>({
    queryKey: ['places', 'nearby', lat, lon, radius, category],
    queryFn: () => getNearbyPlaces(lat!, lon!, radius, category),
    enabled: lat !== null && lon !== null,
    staleTime: STALE_TIME.PLACES,
  });
};
