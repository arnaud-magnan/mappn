/**
 * ClaimingProgressHUD — floating overlay shown while the player is
 * inside a place's geofence and accumulating dwell time.
 *
 * Displays the place name and a fill-bar progress indicator.
 * Progress is computed client-side from time elapsed since the first
 * geofence detection ping. The backend requires 300 seconds of dwell
 * time for visit confirmation (visit_min_duration_seconds = 300).
 *
 * Positioned absolutely at the top of the map screen (below the safe
 * area inset) so it does not overlap the tab bar or bottom sheet.
 */

import React, { memo, useEffect, useState } from 'react';
import { StyleSheet, Text, View } from 'react-native';
import MaterialIcons from '@expo/vector-icons/MaterialIcons';

import { GAME_COLORS } from '@/constants/colors';

/** Mirrors backend visit_min_duration_seconds = 300. */
const VISIT_MIN_DURATION_MS = 300_000;

export interface ClaimingProgressHUDProps {
  /** Human-readable name of the place being unlocked. */
  placeName: string;
  /**
   * Local timestamp (Date.now()) when the geofence was first entered.
   * Progress is computed as elapsed / VISIT_MIN_DURATION_MS.
   */
  startedAt: number;
}

export const ClaimingProgressHUD = memo(function ClaimingProgressHUD({
  placeName,
  startedAt,
}: ClaimingProgressHUDProps) {
  const [progress, setProgress] = useState(() =>
    Math.min((Date.now() - startedAt) / VISIT_MIN_DURATION_MS, 1)
  );

  useEffect(() => {
    const update = () => {
      setProgress(Math.min((Date.now() - startedAt) / VISIT_MIN_DURATION_MS, 1));
    };
    update();
    const id = setInterval(update, 1000);
    return () => clearInterval(id);
  }, [startedAt]);

  const pct = Math.round(progress * 100);

  return (
    <View style={styles.container}>
      <View style={styles.titleRow}>
        <MaterialIcons name="lock-open" size={15} color={GAME_COLORS.primary} />
        <Text style={styles.title} numberOfLines={1}>
          Unlocking "{placeName}"
        </Text>
      </View>
      <View style={styles.barTrack}>
        <View style={[styles.barFill, { width: `${pct}%` as `${number}%` }]} />
      </View>
      <Text style={styles.pctLabel}>{pct}%</Text>
    </View>
  );
});

const styles = StyleSheet.create({
  container: {
    position: 'absolute',
    top: 60,
    left: 16,
    right: 16,
    backgroundColor: 'rgba(17, 24, 39, 0.92)',
    borderRadius: 12,
    padding: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.3,
    shadowRadius: 6,
    elevation: 6,
  },
  titleRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    marginBottom: 8,
  },
  title: {
    flex: 1,
    fontSize: 13,
    fontWeight: '600',
    color: '#ffffff',
  },
  barTrack: {
    height: 6,
    backgroundColor: 'rgba(99, 102, 241, 0.25)',
    borderRadius: 3,
    overflow: 'hidden',
  },
  barFill: {
    height: 6,
    backgroundColor: GAME_COLORS.primary,
    borderRadius: 3,
  },
  pctLabel: {
    fontSize: 11,
    color: GAME_COLORS.textSecondary,
    textAlign: 'right',
    marginTop: 4,
  },
});
