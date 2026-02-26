/**
 * Profile screen showing aggregate stats, themed achievements, and city passport links.
 *
 * Layout (ScrollView):
 * - 3 StatCards in a row: places visited, cities explored, countries reached
 * - AchievementGrid section grouped by category (Explorer, Habits, Categories)
 * - "City Passports" section listing visited cities as tappable links
 * - Loading state while fetching data
 * - Empty state when no visits exist: "Start exploring to track your stats!"
 */

import MaterialIcons from '@expo/vector-icons/MaterialIcons';
import { router } from 'expo-router';
import React from 'react';
import {
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from 'react-native';

import { THEME_COLORS } from '@/constants/colors';
import { EmptyState } from '@/components/ui/EmptyState';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import { StatCard } from '@/components/profile/StatCard';
import { AchievementGrid } from '@/components/profile/AchievementGrid';
import { useUserStats } from '@/hooks/useUserStats';
import { useAchievements } from '@/hooks/useAchievements';
import { useHeatmap } from '@/hooks/useHeatmap';

export default function ProfileScreen() {
  const { data: stats, isLoading: statsLoading, isError: statsError } = useUserStats();
  const { data: achievements, isLoading: achievementsLoading, isError: achievementsError } = useAchievements();

  // Fetch heatmap to derive visited cities for City Passports section
  const { data: heatmap, isLoading: heatmapLoading, isError: heatmapError } = useHeatmap();

  const isLoading = statsLoading || achievementsLoading || heatmapLoading;
  const isError = statsError || achievementsError || heatmapError;

  // Derive the set of visited cities from heatmap areas
  const visitedCities = React.useMemo(() => {
    if (!heatmap) return [];
    const cities = new Set<string>();
    for (const area of heatmap.areas) {
      if (area.visited && area.city) {
        cities.add(area.city);
      }
    }
    return Array.from(cities).sort();
  }, [heatmap]);

  if (isLoading) {
    return <LoadingSpinner message="Loading your profile..." />;
  }

  if (isError) {
    return (
      <EmptyState
        icon="wifi-off"
        title="Could not load profile"
        description="Check your connection and try again."
      />
    );
  }

  const hasNoVisits = !stats || stats.places_count === 0;

  if (hasNoVisits) {
    return (
      <EmptyState
        icon="explore"
        title="No visits yet"
        description="Start exploring to track your stats!"
      />
    );
  }

  return (
    <ScrollView
      style={styles.container}
      contentContainerStyle={styles.content}
      showsVerticalScrollIndicator={false}>
      {/* Stats Row */}
      <View style={styles.statsRow}>
        <StatCard
          icon="place"
          value={stats.places_count}
          label="Places Visited"
        />
        <StatCard
          icon="location-city"
          value={stats.cities_count}
          label="Cities Explored"
        />
        <StatCard
          icon="public"
          value={stats.countries_count}
          label="Countries Reached"
        />
      </View>

      {/* Achievements Section */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Achievements</Text>
        <AchievementGrid achievements={achievements ?? []} />
      </View>

      {/* City Passports Section */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>City Passports</Text>
        {visitedCities.length === 0 ? (
          <Text style={styles.emptyPassports}>
            Visit a city to earn stamps!
          </Text>
        ) : (
          visitedCities.map((city) => (
            <Pressable
              key={city}
              style={({ pressed }) => [
                styles.passportLink,
                pressed && styles.passportLinkPressed,
              ]}
              onPress={() =>
                router.push(`/passport/${encodeURIComponent(city)}` as const as '/')
              }>
              <View style={styles.passportLinkInner}>
                <MaterialIcons
                  name="book"
                  size={20}
                  color={THEME_COLORS.primary}
                  style={styles.passportIcon}
                />
                <Text style={styles.passportCity}>{city}</Text>
                <MaterialIcons
                  name="chevron-right"
                  size={20}
                  color={THEME_COLORS.textSecondary}
                />
              </View>
            </Pressable>
          ))
        )}
      </View>
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
  statsRow: {
    flexDirection: 'row',
    marginBottom: 24,
  },
  section: {
    marginBottom: 24,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: THEME_COLORS.text,
    marginBottom: 12,
  },
  emptyPassports: {
    fontSize: 14,
    color: THEME_COLORS.textSecondary,
    textAlign: 'center',
    paddingVertical: 16,
  },
  passportLink: {
    backgroundColor: THEME_COLORS.background,
    borderRadius: 10,
    borderWidth: 1,
    borderColor: THEME_COLORS.border,
    marginBottom: 8,
    overflow: 'hidden',
  },
  passportLinkPressed: {
    opacity: 0.7,
  },
  passportLinkInner: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 14,
  },
  passportIcon: {
    marginRight: 10,
  },
  passportCity: {
    flex: 1,
    fontSize: 15,
    fontWeight: '600',
    color: THEME_COLORS.text,
  },
});
