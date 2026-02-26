/**
 * AchievementBadge component for displaying a single achievement with progress.
 *
 * Unlocked achievements (earned=true) show a highlighted card with a checkmark
 * and colored background accent. Locked achievements (earned=false) are greyed out.
 *
 * Displays: name, description, progress text (e.g. "7/10"), and a progress bar.
 */

import MaterialIcons from '@expo/vector-icons/MaterialIcons';
import React from 'react';
import { StyleSheet, Text, View } from 'react-native';

import { THEME_COLORS } from '@/constants/colors';
import { AchievementResponse } from '@/types/api';

export interface AchievementBadgeProps {
  achievement: AchievementResponse;
  icon: React.ComponentProps<typeof MaterialIcons>['name'];
}

export function AchievementBadge({ achievement, icon }: AchievementBadgeProps) {
  const { name, description, progress, threshold, earned } = achievement;
  const progressClamped = Math.min(progress, threshold);
  const progressRatio = threshold > 0 ? progressClamped / threshold : 0;
  const progressText = `${progressClamped}/${threshold}`;

  return (
    <View style={[styles.container, earned ? styles.containerEarned : styles.containerLocked]}>
      <View style={styles.header}>
        <View style={[styles.iconContainer, earned ? styles.iconContainerEarned : styles.iconContainerLocked]}>
          <MaterialIcons
            name={icon}
            size={22}
            color={earned ? THEME_COLORS.primary : THEME_COLORS.textSecondary}
          />
        </View>
        {earned && (
          <View style={styles.checkmark}>
            <MaterialIcons name="check-circle" size={18} color={THEME_COLORS.success} />
          </View>
        )}
      </View>

      <Text style={[styles.name, earned ? styles.nameEarned : styles.nameLocked]} numberOfLines={1}>
        {name}
      </Text>
      <Text style={[styles.description, earned ? styles.descriptionEarned : styles.descriptionLocked]} numberOfLines={2}>
        {description}
      </Text>

      <View style={styles.progressRow}>
        <Text style={[styles.progressText, earned ? styles.progressTextEarned : styles.progressTextLocked]}>
          {progressText}
        </Text>
      </View>

      <View style={styles.progressBarTrack}>
        <View
          style={[
            styles.progressBarFill,
            earned ? styles.progressBarFillEarned : styles.progressBarFillLocked,
            { width: `${Math.round(progressRatio * 100)}%` },
          ]}
        />
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    borderRadius: 12,
    padding: 12,
    borderWidth: 1,
    margin: 4,
  },
  containerEarned: {
    backgroundColor: '#eff6ff',
    borderColor: THEME_COLORS.primary,
  },
  containerLocked: {
    backgroundColor: THEME_COLORS.surface,
    borderColor: THEME_COLORS.border,
    opacity: 0.7,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: 8,
  },
  iconContainer: {
    width: 40,
    height: 40,
    borderRadius: 20,
    alignItems: 'center',
    justifyContent: 'center',
  },
  iconContainerEarned: {
    backgroundColor: '#dbeafe',
  },
  iconContainerLocked: {
    backgroundColor: THEME_COLORS.border,
  },
  checkmark: {
    marginTop: 2,
  },
  name: {
    fontSize: 13,
    fontWeight: '700',
    marginBottom: 2,
  },
  nameEarned: {
    color: THEME_COLORS.text,
  },
  nameLocked: {
    color: THEME_COLORS.textSecondary,
  },
  description: {
    fontSize: 11,
    lineHeight: 15,
    marginBottom: 6,
  },
  descriptionEarned: {
    color: THEME_COLORS.textSecondary,
  },
  descriptionLocked: {
    color: THEME_COLORS.textSecondary,
  },
  progressRow: {
    flexDirection: 'row',
    justifyContent: 'flex-end',
    marginBottom: 4,
  },
  progressText: {
    fontSize: 11,
    fontWeight: '600',
  },
  progressTextEarned: {
    color: THEME_COLORS.primary,
  },
  progressTextLocked: {
    color: THEME_COLORS.textSecondary,
  },
  progressBarTrack: {
    height: 4,
    backgroundColor: THEME_COLORS.border,
    borderRadius: 2,
    overflow: 'hidden',
  },
  progressBarFill: {
    height: '100%',
    borderRadius: 2,
  },
  progressBarFillEarned: {
    backgroundColor: THEME_COLORS.primary,
  },
  progressBarFillLocked: {
    backgroundColor: THEME_COLORS.textSecondary,
  },
});
