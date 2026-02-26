/**
 * TanStack Query infinite query hook for fetching journal entries.
 *
 * Uses useInfiniteQuery to implement paginated loading with limit=20
 * per page. getNextPageParam returns the next offset when a full page
 * of results is returned, or undefined when there are no more pages.
 */

import { useInfiniteQuery } from '@tanstack/react-query';

import { getJournal } from '@/services/utilityService';
import { JournalEntryResponse } from '@/types/api';
import { STALE_TIME } from '@/constants/config';

const JOURNAL_PAGE_LIMIT = 20;

/**
 * Fetch paginated journal entries for the current user.
 *
 * @returns TanStack InfiniteQuery result with pages of JournalEntryResponse arrays.
 *   Each page contains up to 20 entries ordered by visit date (most recent first).
 */
export function useJournal() {
  return useInfiniteQuery<JournalEntryResponse[], Error>({
    queryKey: ['journal'],
    queryFn: ({ pageParam = 0 }) =>
      getJournal(JOURNAL_PAGE_LIMIT, pageParam as number),
    initialPageParam: 0,
    getNextPageParam: (lastPage, _allPages, lastPageParam) => {
      const currentOffset = lastPageParam as number;
      if (lastPage.length === JOURNAL_PAGE_LIMIT) {
        return currentOffset + JOURNAL_PAGE_LIMIT;
      }
      return undefined;
    },
    staleTime: STALE_TIME.JOURNAL,
  });
}
