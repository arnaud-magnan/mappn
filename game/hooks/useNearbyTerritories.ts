/**
 * TanStack Query hook for fetching nearby territories.
 *
 * Fetches territories from GET /game/territories/nearby based on the
 * user's current GPS coordinates. Uses a composite queryKey including
 * location for proper cache invalidation.
 */

import { keepPreviousData, useQuery } from '@tanstack/react-query';

import { getNearbyTerritories } from '../services/territoryService';
import { TerritoryResponse } from '../types/api';
import { STALE_TIME } from '../constants/config';

export interface UseNearbyTerritoriesParams {
  /** Latitude of the map center. */
  lat: number | null;
  /** Longitude of the map center. */
  lon: number | null;
  /** Search radius in meters. */
  radius?: number;
}

/**
 * Fetch nearby territories with TanStack Query caching.
 *
 * The query is disabled when lat or lon is null (no location available).
 * Results are cached with a 30-second stale time for competitive freshness.
 *
 * @param params - Location and radius parameters.
 * @returns TanStack Query result with TerritoryResponse[] data.
 */
export const useNearbyTerritories = ({
  lat,
  lon,
  radius = 5000,
}: UseNearbyTerritoriesParams) => {
  // Round coordinates to ~100m precision to avoid refetching on every pixel pan.
  const roundedLat = lat !== null ? Math.round(lat * 1000) / 1000 : null;
  const roundedLon = lon !== null ? Math.round(lon * 1000) / 1000 : null;

  return useQuery<TerritoryResponse[]>({
    queryKey: ['territories', 'nearby', roundedLat, roundedLon, radius],
    queryFn: () => getNearbyTerritories(lat!, lon!, radius),
    enabled: lat !== null && lon !== null,
    staleTime: STALE_TIME.TERRITORIES,
    refetchInterval: STALE_TIME.TERRITORIES,
    placeholderData: keepPreviousData,
  });
};
