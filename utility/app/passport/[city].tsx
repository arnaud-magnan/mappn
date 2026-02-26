/**
 * City Passport screen showing neighborhood stamps and progress for a specific city.
 *
 * Features:
 * - Stamp grid: all neighborhoods shown as stamps
 *   - Stamped (visited=true): colored stamp icon
 *   - Unstamped (visited=false): grey outline icon
 * - Progress bar showing "X of Y neighborhoods" visited
 * - City completion badge displayed prominently when explored_pct = 100%
 * - Loading and empty states
 */

import MaterialIcons from '@expo/vector-icons/MaterialIcons';
import { useLocalSearchParams } from 'expo-router';
import React from 'react';
import {
  ScrollView,
  StyleSheet,
  Text,
  View,
} from 'react-native';

import { THEME_COLORS } from '@/constants/colors';
import { EmptyState } from '@/components/ui/EmptyState';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import { useCityPassport } from '@/hooks/useCityPassport';
import { PassportStampResponse } from '@/types/api';

function StampItem({ stamp }: { stamp: PassportStampResponse }) {
  return (
    <View style={[styles.stampItem, stamp.visited ? styles.stampVisited : styles.stampUnvisited]}>
      <MaterialIcons
        name={stamp.visited ? 'verified' : 'radio-button-unchecked'}
        size={32}
        color={stamp.visited ? THEME_COLORS.primary : THEME_COLORS.border}
      />
      <Text
        style={[
          styles.stampName,
          stamp.visited ? styles.stampNameVisited : styles.stampNameUnvisited,
        ]}
        numberOfLines={2}>
        {stamp.name}
      </Text>
    </View>
  );
}

export default function CityPassportScreen() {
  const { city } = useLocalSearchParams<{ city: string }>();
  const cityName = Array.isArray(city) ? city[0] : (city ?? '');

  const { data: passport, isLoading, error } = useCityPassport(cityName);

  if (isLoading) {
    return <LoadingSpinner message={`Loading ${cityName} passport...`} />;
  }

  if (error != null || passport == null) {
    return (
      <EmptyState
        icon="book"
        title="Passport not found"
        description={`No passport data found for ${cityName}. Visit neighborhoods in this city to get started!`}
      />
    );
  }

  const { total_neighborhoods, visited_count, stamps, badge_earned, explored_pct } = passport;
  const progressRatio = total_neighborhoods > 0 ? visited_count / total_neighborhoods : 0;
  const progressPercent = Math.round(progressRatio * 100);
  const isComplete = explored_pct >= 100;

  return (
    <ScrollView
      style={styles.container}
      contentContainerStyle={styles.content}
      showsVerticalScrollIndicator={false}>
      {/* City Header */}
      <View style={styles.header}>
        <Text style={styles.cityTitle}>{cityName}</Text>
        <Text style={styles.citySubtitle}>City Passport</Text>
      </View>

      {/* City Completion Badge */}
      {(isComplete || badge_earned) && (
        <View style={styles.completionBadge}>
          <MaterialIcons name="emoji-events" size={48} color="#f59e0b" />
          <Text style={styles.completionBadgeTitle}>City Completed!</Text>
          <Text style={styles.completionBadgeDescription}>
            You have explored all neighborhoods in {cityName}
          </Text>
        </View>
      )}

      {/* Progress Bar */}
      <View style={styles.progressSection}>
        <View style={styles.progressLabelRow}>
          <Text style={styles.progressLabel}>
            {visited_count} of {total_neighborhoods} neighborhoods
          </Text>
          <Text style={styles.progressPercent}>{progressPercent}%</Text>
        </View>
        <View style={styles.progressBarTrack}>
          <View
            style={[
              styles.progressBarFill,
              isComplete ? styles.progressBarFillComplete : styles.progressBarFillPartial,
              { width: `${progressPercent}%` },
            ]}
          />
        </View>
      </View>

      {/* Stamp Grid */}
      {stamps.length === 0 ? (
        <EmptyState
          icon="book"
          title="No neighborhoods yet"
          description="Visit places in this city to collect neighborhood stamps!"
        />
      ) : (
        <View style={styles.stampGrid}>
          {stamps.map((stamp) => (
            <StampItem key={stamp.area_id} stamp={stamp} />
          ))}
        </View>
      )}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: THEME_COLORS.surface,
  },
  content: {
    padding: 16,
    paddingBottom: 32,
  },
  header: {
    marginBottom: 16,
  },
  cityTitle: {
    fontSize: 28,
    fontWeight: '800',
    color: THEME_COLORS.text,
  },
  citySubtitle: {
    fontSize: 14,
    color: THEME_COLORS.textSecondary,
    marginTop: 2,
  },
  completionBadge: {
    backgroundColor: '#fef3c7',
    borderRadius: 16,
    borderWidth: 2,
    borderColor: '#f59e0b',
    padding: 20,
    alignItems: 'center',
    marginBottom: 20,
  },
  completionBadgeTitle: {
    fontSize: 20,
    fontWeight: '800',
    color: '#92400e',
    marginTop: 8,
  },
  completionBadgeDescription: {
    fontSize: 13,
    color: '#92400e',
    textAlign: 'center',
    marginTop: 4,
  },
  progressSection: {
    marginBottom: 20,
  },
  progressLabelRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 6,
  },
  progressLabel: {
    fontSize: 14,
    fontWeight: '600',
    color: THEME_COLORS.text,
  },
  progressPercent: {
    fontSize: 14,
    fontWeight: '700',
    color: THEME_COLORS.primary,
  },
  progressBarTrack: {
    height: 8,
    backgroundColor: THEME_COLORS.border,
    borderRadius: 4,
    overflow: 'hidden',
  },
  progressBarFill: {
    height: '100%',
    borderRadius: 4,
  },
  progressBarFillPartial: {
    backgroundColor: THEME_COLORS.primary,
  },
  progressBarFillComplete: {
    backgroundColor: THEME_COLORS.success,
  },
  stampGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
  },
  stampItem: {
    width: '33.33%',
    padding: 8,
    alignItems: 'center',
  },
  stampVisited: {
    opacity: 1,
  },
  stampUnvisited: {
    opacity: 0.45,
  },
  stampName: {
    fontSize: 11,
    textAlign: 'center',
    marginTop: 4,
    lineHeight: 14,
  },
  stampNameVisited: {
    color: THEME_COLORS.text,
    fontWeight: '600',
  },
  stampNameUnvisited: {
    color: THEME_COLORS.textSecondary,
  },
});
