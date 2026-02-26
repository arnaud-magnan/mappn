/**
 * TanStack Query hook for fetching the current user's visit history.
 *
 * Fetches all confirmed visits from GET /visits/history using the
 * visitsService. Uses a queryKey of ['visits', 'history'] for proper
 * cache invalidation.
 */

import { useQuery } from '@tanstack/react-query';

import { getVisitHistory } from '../services/visitsService';
import { VisitResponse } from '../types/api';
import { STALE_TIME } from '../constants/config';

/**
 * Fetch the current user's visit history with TanStack Query caching.
 *
 * @returns TanStack Query result with VisitResponse[] data.
 */
export function useVisitHistory() {
  return useQuery<VisitResponse[]>({
    queryKey: ['visits', 'history'],
    queryFn: () => getVisitHistory(),
    staleTime: STALE_TIME.VISITS,
  });
}
