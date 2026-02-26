/**
 * CityProgress displays the user's exploration progress for a city.
 *
 * Shows:
 * - "X% of [City] explored" heading
 * - A visual progress bar where the filled portion matches explored_pct
 * - "X of Y neighborhoods visited" sub-text
 */

import React from 'react';
import { StyleSheet, Text, View } from 'react-native';

import { THEME_COLORS } from '@/constants/colors';

export interface CityProgressProps {
  /** City name to display in the heading. */
  city: string;
  /** Exploration percentage (0-100). */
  exploredPct: number;
  /** Number of neighborhoods the user has visited. */
  visitedAreas: number;
  /** Total number of neighborhoods in the city. */
  totalAreas: number;
}

export function CityProgress({
  city,
  exploredPct,
  visitedAreas,
  totalAreas,
}: CityProgressProps) {
  // Clamp percentage to [0, 100] to avoid rendering artefacts
  const clampedPct = Math.min(100, Math.max(0, exploredPct));
  const fillWidth = `${clampedPct}%` as const;
  const displayPct = Math.round(clampedPct);

  return (
    <View style={styles.container}>
      <Text style={styles.heading}>
        {displayPct}% of {city} explored
      </Text>

      <View style={styles.progressTrack}>
        <View style={[styles.progressFill, { width: fillWidth }]} />
      </View>

      <Text style={styles.subText}>
        {visitedAreas} of {totalAreas} neighborhoods visited
      </Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    padding: 12,
  },
  heading: {
    fontSize: 15,
    fontWeight: '700',
    color: THEME_COLORS.text,
    marginBottom: 8,
  },
  progressTrack: {
    height: 8,
    borderRadius: 4,
    backgroundColor: THEME_COLORS.border,
    overflow: 'hidden',
    marginBottom: 6,
  },
  progressFill: {
    height: '100%',
    borderRadius: 4,
    backgroundColor: THEME_COLORS.success,
  },
  subText: {
    fontSize: 12,
    color: THEME_COLORS.textSecondary,
  },
});
