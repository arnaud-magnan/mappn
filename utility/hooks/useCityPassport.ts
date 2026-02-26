/**
 * TanStack Query hook for fetching city passport with neighborhood stamps.
 *
 * Fetches from GET /passports?city=<city> with a 10-minute stale time.
 * Returns neighborhood stamps, visited count, total count, badge status, explored percentage.
 *
 * @param city - City name to fetch passport for.
 */

import { useQuery } from '@tanstack/react-query';

import { STALE_TIME } from '@/constants/config';
import { getCityPassport } from '@/services/utilityService';
import { CityPassportResponse } from '@/types/api';

export function useCityPassport(city: string) {
  return useQuery<CityPassportResponse, Error>({
    queryKey: ['passport', city],
    queryFn: () => getCityPassport(city),
    staleTime: STALE_TIME.PASSPORT, // 10 minutes
    enabled: city.length > 0,
  });
}
