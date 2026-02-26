/**
 * TanStack Query hook for fetching aggregate user visit statistics.
 *
 * Fetches from GET /users/me/stats with a 5-minute stale time.
 * Returns places_count, cities_count, countries_count, total_duration_seconds.
 */

import { useQuery } from '@tanstack/react-query';

import { STALE_TIME } from '@/constants/config';
import { getUserStats } from '@/services/utilityService';
import { UserStatsResponse } from '@/types/api';

export function useUserStats() {
  return useQuery<UserStatsResponse, Error>({
    queryKey: ['stats'],
    queryFn: getUserStats,
    staleTime: STALE_TIME.USER_STATS, // 5 minutes
  });
}
