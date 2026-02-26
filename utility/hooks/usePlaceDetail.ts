/**
 * TanStack Query hook for fetching place detail.
 *
 * Fetches full place data from GET /places/{id} including busyness data,
 * popular times, and current popularity. Uses a composite queryKey of
 * ['places', id] for proper cache invalidation.
 */

import { useQuery } from '@tanstack/react-query';

import { getPlaceDetail } from '../services/placesService';
import { PlaceDetailResponse } from '../types/api';
import { STALE_TIME } from '../constants/config';

/**
 * Fetch place detail with TanStack Query caching.
 *
 * @param id - The place ID to fetch detail for.
 * @returns TanStack Query result with PlaceDetailResponse data.
 */
export function usePlaceDetail(id: number) {
  return useQuery<PlaceDetailResponse>({
    queryKey: ['places', id],
    queryFn: () => getPlaceDetail(id),
    staleTime: STALE_TIME.PLACE_DETAIL,
  });
}
