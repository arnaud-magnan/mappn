/**
 * TanStack Query hook for fetching user achievements with progress.
 *
 * Fetches from GET /users/me/achievements with a 10-minute stale time.
 * Returns all 6 achievements across 3 categories with progress and earned status.
 */

import { useQuery } from '@tanstack/react-query';

import { STALE_TIME } from '@/constants/config';
import { getAchievements } from '@/services/utilityService';
import { AchievementResponse } from '@/types/api';

export function useAchievements() {
  return useQuery<AchievementResponse[], Error>({
    queryKey: ['achievements'],
    queryFn: getAchievements,
    staleTime: STALE_TIME.ACHIEVEMENTS, // 10 minutes
  });
}
