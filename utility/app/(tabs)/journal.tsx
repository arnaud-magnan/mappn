/**
 * Journal tab screen – chronological visit timeline.
 *
 * Renders an infinite-scroll list of journal entries using useJournal.
 * Shows a LoadingSpinner on initial load, an EmptyState when no visits
 * exist, and an error message when the query fails. Pull-to-refresh
 * invalidates and refetches the first page.
 */

import React, { useCallback } from 'react';
import { StyleSheet, Text, View } from 'react-native';

import { useJournal } from '@/hooks/useJournal';
import { JournalEntryResponse } from '@/types/api';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import { EmptyState } from '@/components/ui/EmptyState';
import { THEME_COLORS } from '@/constants/colors';
import { JournalEntryList } from '@/components/journal/JournalEntryList';

export default function JournalScreen() {
  const {
    data,
    isLoading,
    isError,
    isFetchingNextPage,
    fetchNextPage,
    hasNextPage,
    refetch,
    isRefetching,
  } = useJournal();

  // Flatten pages into a single entries array
  const entries: JournalEntryResponse[] = data?.pages.flat() ?? [];

  const handleEndReached = useCallback(() => {
    if (hasNextPage && !isFetchingNextPage) {
      fetchNextPage();
    }
  }, [hasNextPage, isFetchingNextPage, fetchNextPage]);

  const handleRefresh = useCallback(() => {
    refetch();
  }, [refetch]);

  if (isLoading) {
    return <LoadingSpinner message="Loading your journal..." />;
  }

  if (isError) {
    return (
      <EmptyState
        icon="wifi-off"
        title="Could not load journal"
        description="Check your connection and try again."
        actionLabel="Retry"
        onAction={() => void refetch()}
      />
    );
  }

  if (entries.length === 0) {
    return (
      <EmptyState
        icon="menu-book"
        title="Your Journal is Empty"
        description="Visit places to start your journal!"
      />
    );
  }

  return (
    <View style={styles.container}>
      <JournalEntryList
        entries={entries}
        onEndReached={handleEndReached}
        onRefresh={handleRefresh}
        isRefreshing={isRefetching && !isLoading}
        isFetchingNextPage={isFetchingNextPage}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: THEME_COLORS.surface,
  },
  errorContainer: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    padding: 24,
  },
  errorText: {
    fontSize: 14,
    color: THEME_COLORS.error,
    textAlign: 'center',
    lineHeight: 20,
  },
});
