/**
 * AchievementGrid component displaying achievements grouped by category.
 *
 * Groups the 6 achievements into 3 categories: Explorer, Habits, Categories.
 * Shows a section header for each category and renders AchievementBadge for each
 * achievement in a 2-column grid layout.
 */

import MaterialIcons from '@expo/vector-icons/MaterialIcons';
import React from 'react';
import { StyleSheet, Text, View } from 'react-native';

import { THEME_COLORS } from '@/constants/colors';
import {
  ACHIEVEMENT_CATEGORIES,
  ACHIEVEMENT_DEFINITIONS,
} from '@/constants/achievements';
import { AchievementResponse } from '@/types/api';
import { AchievementBadge } from './AchievementBadge';

export interface AchievementGridProps {
  achievements: AchievementResponse[];
}

export function AchievementGrid({ achievements }: AchievementGridProps) {
  // Build a lookup map from achievement id -> AchievementResponse for progress data
  const progressMap = new Map<string, AchievementResponse>(
    achievements.map((a) => [a.id, a])
  );

  return (
    <View>
      {ACHIEVEMENT_CATEGORIES.map((category) => {
        const categoryDefinitions = ACHIEVEMENT_DEFINITIONS.filter(
          (def) => def.category === category.key
        );

        return (
          <View key={category.key} style={styles.categorySection}>
            <Text style={styles.categoryHeader}>{category.label}</Text>
            <View style={styles.badgeRow}>
              {categoryDefinitions.map((def) => {
                const progressData = progressMap.get(def.id);
                // Construct a synthetic AchievementResponse if not returned by API
                const achievement: AchievementResponse = progressData ?? {
                  id: def.id,
                  name: def.name,
                  description: def.description,
                  category: def.category,
                  progress: 0,
                  threshold: def.threshold,
                  earned: false,
                  earned_at: null,
                };
                return (
                  <AchievementBadge
                    key={def.id}
                    achievement={achievement}
                    icon={def.icon as React.ComponentProps<typeof MaterialIcons>['name']}
                  />
                );
              })}
            </View>
          </View>
        );
      })}
    </View>
  );
}

const styles = StyleSheet.create({
  categorySection: {
    marginBottom: 16,
  },
  categoryHeader: {
    fontSize: 14,
    fontWeight: '700',
    color: THEME_COLORS.textSecondary,
    textTransform: 'uppercase',
    letterSpacing: 0.8,
    marginBottom: 8,
    marginHorizontal: 4,
  },
  badgeRow: {
    flexDirection: 'row',
  },
});
