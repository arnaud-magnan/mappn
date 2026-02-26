/**
 * TanStack Query hook for fetching busyness forecast.
 *
 * Fetches predicted busyness from GET /places/{id}/forecast for a specific
 * day and hour. The query is only enabled when both day and hour are
 * defined, preventing unnecessary requests before user selection.
 */

import { useQuery } from '@tanstack/react-query';

import { getForecast } from '../services/placesService';
import { ForecastResponse } from '../types/api';
import { STALE_TIME } from '../constants/config';

/**
 * Fetch busyness forecast with TanStack Query caching.
 *
 * @param id - The place ID.
 * @param day - Day of the week (0=Monday .. 6=Sunday), or undefined.
 * @param hour - Hour of the day (0-23), or undefined.
 * @returns TanStack Query result with ForecastResponse data.
 */
export function useForecast(
  id: number,
  day: number | undefined,
  hour: number | undefined
) {
  return useQuery<ForecastResponse>({
    queryKey: ['forecast', id, day, hour],
    queryFn: () => getForecast(id, day!, hour!),
    enabled: day !== undefined && hour !== undefined,
    staleTime: STALE_TIME.BUSYNESS,
  });
}
