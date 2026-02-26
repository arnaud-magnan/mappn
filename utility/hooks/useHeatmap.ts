/**
 * TanStack Query hook for fetching the exploration heatmap.
 *
 * Fetches the user's personal heatmap from GET /explore/heatmap with an
 * optional city filter. Data is cached for 10 minutes (STALE_TIME.HEATMAP)
 * to avoid excessive re-fetching since heatmap data only changes after new
 * visits are confirmed.
 */

import { useQuery } from '@tanstack/react-query';

import { getHeatmap } from '@/services/utilityService';
import { HeatmapResponse } from '@/types/api';
import { STALE_TIME } from '@/constants/config';

/**
 * Fetch the exploration heatmap for the current user.
 *
 * @param city - Optional city name to filter heatmap areas. When undefined,
 *   all areas across all visited cities are returned.
 * @returns TanStack Query result containing HeatmapResponse data.
 */
export function useHeatmap(city?: string) {
  return useQuery<HeatmapResponse>({
    queryKey: ['heatmap', city],
    queryFn: () => getHeatmap(city),
    staleTime: STALE_TIME.HEATMAP,
  });
}
