/**
 * Infinite scroll FlatList for journal entries.
 *
 * Renders JournalEntry cards from paginated data provided by useJournal.
 * Triggers the next page load when the user scrolls within 200px of the
 * bottom. Shows a loading indicator at the bottom during pagination.
 * Supports pull-to-refresh.
 */

import React, { useCallback } from 'react';
import {
  ActivityIndicator,
  FlatList,
  ListRenderItemInfo,
  StyleSheet,
  View,
} from 'react-native';

import { JournalEntryResponse } from '@/types/api';
import { THEME_COLORS } from '@/constants/colors';

import { JournalEntry } from './JournalEntry';

export interface JournalEntryListProps {
  entries: JournalEntryResponse[];
  onEndReached: () => void;
  onRefresh: () => void;
  isRefreshing: boolean;
  isFetchingNextPage: boolean;
}

export function JournalEntryList({
  entries,
  onEndReached,
  onRefresh,
  isRefreshing,
  isFetchingNextPage,
}: JournalEntryListProps) {
  const renderItem = useCallback(
    ({ item }: ListRenderItemInfo<JournalEntryResponse>) => (
      <JournalEntry entry={item} />
    ),
    []
  );

  const keyExtractor = useCallback(
    (item: JournalEntryResponse) => String(item.visit_id),
    []
  );

  const renderFooter = () => {
    if (!isFetchingNextPage) return null;
    return (
      <View style={styles.footer}>
        <ActivityIndicator size="small" color={THEME_COLORS.primary} />
      </View>
    );
  };

  return (
    <FlatList
      data={entries}
      renderItem={renderItem}
      keyExtractor={keyExtractor}
      onEndReached={onEndReached}
      onEndReachedThreshold={0.2}
      onRefresh={onRefresh}
      refreshing={isRefreshing}
      ListFooterComponent={renderFooter}
      contentContainerStyle={styles.list}
      showsVerticalScrollIndicator={false}
    />
  );
}

const styles = StyleSheet.create({
  list: {
    paddingTop: 8,
    paddingBottom: 24,
  },
  footer: {
    paddingVertical: 16,
    alignItems: 'center',
  },
});
