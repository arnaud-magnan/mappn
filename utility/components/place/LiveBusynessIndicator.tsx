/**
 * Live busyness indicator badge.
 *
 * Displays the current_popularity value as a color-coded badge when
 * live data is available. Shows "No live data" when the value is
 * null or undefined.
 *
 * Color coding:
 * - Green (Quiet): 0-33
 * - Yellow (Moderate): 34-66
 * - Red (Busy): 67-100
 */

import React from 'react';
import { StyleSheet, Text, View } from 'react-native';

import { BUSYNESS_COLORS, BusynessLevel, THEME_COLORS } from '@/constants/colors';

export interface LiveBusynessIndicatorProps {
  /** Current live busyness value (0-100), or null/undefined when unavailable. */
  currentPopularity: number | null | undefined;
}

/**
 * Determine busyness level from a numeric value.
 */
const getBusynessLevel = (value: number): BusynessLevel => {
  if (value <= 33) return 'quiet';
  if (value <= 66) return 'moderate';
  return 'busy';
};

/**
 * Get the display label for a busyness level.
 */
const getBusynessLabel = (level: BusynessLevel): string => {
  switch (level) {
    case 'quiet':
      return 'Quiet';
    case 'moderate':
      return 'Moderate';
    case 'busy':
      return 'Busy';
    case 'noData':
      return 'No data';
  }
};

/**
 * LiveBusynessIndicator shows the current live busyness as a
 * color-coded badge with label, or "No live data" when unavailable.
 */
export function LiveBusynessIndicator({
  currentPopularity,
}: LiveBusynessIndicatorProps) {
  if (currentPopularity === null || currentPopularity === undefined) {
    return (
      <View style={styles.container}>
        <View style={[styles.badge, { backgroundColor: BUSYNESS_COLORS.noData }]}>
          <Text style={styles.badgeText}>No live data</Text>
        </View>
      </View>
    );
  }

  const level = getBusynessLevel(currentPopularity);
  const color = BUSYNESS_COLORS[level];
  const label = getBusynessLabel(level);

  return (
    <View style={styles.container}>
      <View style={[styles.badge, { backgroundColor: color }]}>
        <Text style={styles.badgeText}>{label}</Text>
      </View>
      <Text style={styles.valueText}>{currentPopularity}% busy</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 8,
  },
  badge: {
    paddingHorizontal: 14,
    paddingVertical: 6,
    borderRadius: 16,
  },
  badgeText: {
    color: '#ffffff',
    fontSize: 14,
    fontWeight: '700',
  },
  valueText: {
    marginLeft: 10,
    fontSize: 14,
    fontWeight: '600',
    color: THEME_COLORS.text,
  },
});
