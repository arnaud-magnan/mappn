/**
 * List of the user's past visits to a specific place.
 *
 * Renders a FlatList of visit records, each showing the date
 * (formatted) and visit duration. Uses the VisitResponse type
 * from the API types.
 */

import React from 'react';
import { FlatList, StyleSheet, Text, View } from 'react-native';

import { VisitResponse } from '@/types/api';
import { THEME_COLORS } from '@/constants/colors';

export interface VisitHistoryListProps {
  /** Array of visit records for this place. */
  visits: VisitResponse[];
}

/**
 * Format a duration in seconds to a human-readable string.
 *
 * @param seconds - Duration in seconds, or null.
 * @returns Formatted string (e.g., "45 min", "1h 30min").
 */
const formatDuration = (seconds: number | null): string => {
  if (seconds === null || seconds === 0) return 'Unknown duration';
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.round((seconds % 3600) / 60);
  if (hours > 0) {
    return minutes > 0 ? `${hours}h ${minutes}min` : `${hours}h`;
  }
  return `${minutes} min`;
};

/**
 * Format an ISO date string to a readable date.
 */
const formatDate = (isoDate: string): string => {
  const date = new Date(isoDate);
  return date.toLocaleDateString(undefined, {
    weekday: 'short',
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
};

/**
 * VisitHistoryList renders a FlatList of past visits with
 * date and duration for each entry.
 */
export function VisitHistoryList({ visits }: VisitHistoryListProps) {
  if (visits.length === 0) {
    return (
      <View style={styles.emptyContainer}>
        <Text style={styles.emptyText}>No visits to this place yet</Text>
      </View>
    );
  }

  const renderItem = ({ item }: { item: VisitResponse }) => (
    <View style={styles.visitItem}>
      <Text style={styles.visitDate}>{formatDate(item.started_at)}</Text>
      <Text style={styles.visitDuration}>
        {formatDuration(item.duration_seconds)}
      </Text>
    </View>
  );

  return (
    <FlatList
      data={visits}
      renderItem={renderItem}
      keyExtractor={(item) => item.id.toString()}
      scrollEnabled={false}
      ItemSeparatorComponent={() => <View style={styles.separator} />}
    />
  );
}

const styles = StyleSheet.create({
  emptyContainer: {
    paddingVertical: 16,
    alignItems: 'center',
  },
  emptyText: {
    fontSize: 14,
    color: THEME_COLORS.textSecondary,
    fontStyle: 'italic',
  },
  visitItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 10,
  },
  visitDate: {
    fontSize: 14,
    color: THEME_COLORS.text,
    flex: 1,
  },
  visitDuration: {
    fontSize: 14,
    fontWeight: '600',
    color: THEME_COLORS.textSecondary,
    marginLeft: 8,
  },
  separator: {
    height: 1,
    backgroundColor: THEME_COLORS.border,
  },
});
