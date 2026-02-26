/**
 * Place Detail screen.
 *
 * Displays comprehensive information about a place including:
 * - Header with name, category, address, and city
 * - LiveBusynessIndicator showing current busyness
 * - BusynessHistogram with day selector (when busyness data available)
 * - ForecastSlider for future predictions (when busyness data available)
 * - VisitHistoryList showing the user's past visits
 *
 * Loads data via usePlaceDetail hook from GET /places/{id}.
 * Shows a placeholder when busyness_data is null.
 * Uses LoadingSpinner during initial load.
 */

import React, { useCallback, useMemo } from 'react';
import {
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from 'react-native';
import { router, useLocalSearchParams } from 'expo-router';
import MaterialIcons from '@expo/vector-icons/MaterialIcons';

import { usePlaceDetail } from '@/hooks/usePlaceDetail';
import { useVisitHistory } from '@/hooks/useVisitHistory';
import { BusynessHistogram } from '@/components/place/BusynessHistogram';
import { LiveBusynessIndicator } from '@/components/place/LiveBusynessIndicator';
import { ForecastSlider } from '@/components/place/ForecastSlider';
import { VisitHistoryList } from '@/components/place/VisitHistoryList';
import { Card } from '@/components/ui/Card';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import { EmptyState } from '@/components/ui/EmptyState';
import { THEME_COLORS } from '@/constants/colors';

export default function PlaceDetailScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const placeId = Number(id);

  const { data, isLoading, isError } = usePlaceDetail(placeId);
  const { data: allVisits } = useVisitHistory();

  const handleBack = useCallback(() => {
    router.back();
  }, []);

  // Filter visit history to show only visits to this specific place.
  const visits = useMemo(
    () => (allVisits ?? []).filter((v) => v.place_id === placeId),
    [allVisits, placeId]
  );

  if (isLoading) {
    return <LoadingSpinner message="Loading place details..." />;
  }

  if (isError || !data) {
    return (
      <View style={styles.container}>
        <View style={styles.header}>
          <Pressable onPress={handleBack} style={styles.backButton}>
            <MaterialIcons
              name="arrow-back"
              size={24}
              color={THEME_COLORS.text}
            />
          </Pressable>
        </View>
        <EmptyState
          icon="error-outline"
          title="Failed to load"
          description="Could not load place details. Please try again."
          actionLabel="Go Back"
          onAction={handleBack}
        />
      </View>
    );
  }

  const hasBusynessData = data.busyness_data !== null && data.busyness_data !== undefined;

  return (
    <View style={styles.container}>
      {/* Top bar with back button */}
      <View style={styles.header}>
        <Pressable
          onPress={handleBack}
          style={styles.backButton}
          accessibilityRole="button"
          accessibilityLabel="Back">
          <MaterialIcons
            name="arrow-back"
            size={24}
            color={THEME_COLORS.text}
          />
          <Text style={styles.backText}>Back</Text>
        </Pressable>
      </View>

      <ScrollView
        style={styles.scrollView}
        contentContainerStyle={styles.scrollContent}
        showsVerticalScrollIndicator={false}>
        {/* Place info header */}
        <View style={styles.placeHeader}>
          <Text style={styles.placeName}>{data.name}</Text>
          <Text style={styles.placeCategory}>{data.category}</Text>
          {data.address !== null && data.address !== undefined && (
            <Text style={styles.placeAddress}>{data.address}</Text>
          )}
          {data.city !== null && data.city !== undefined && (
            <Text style={styles.placeCity}>{data.city}</Text>
          )}
        </View>

        {/* Live busyness indicator */}
        <Card title="Current Busyness" style={styles.section}>
          <LiveBusynessIndicator
            currentPopularity={
              hasBusynessData
                ? data.busyness_data!.current_popularity ?? null
                : null
            }
          />
        </Card>

        {/* Busyness histogram */}
        {hasBusynessData && data.busyness_data && (
          <Card title="Popular Times" style={styles.section}>
            <BusynessHistogram data={data.busyness_data} />
          </Card>
        )}

        {/* Forecast slider */}
        {hasBusynessData && data.busyness_data && (
          <Card title="Busyness Forecast" style={styles.section}>
            <ForecastSlider placeId={placeId} />
          </Card>
        )}

        {/* No busyness data placeholder */}
        {!hasBusynessData && (
          <Card style={styles.section}>
            <View style={styles.noDataContainer}>
              <MaterialIcons
                name="info-outline"
                size={32}
                color={THEME_COLORS.textSecondary}
              />
              <Text style={styles.noDataText}>
                Busyness data not yet available
              </Text>
              <Text style={styles.noDataSubtext}>
                Check back later for popular times and forecasts.
              </Text>
            </View>
          </Card>
        )}

        {/* Visit history */}
        <Card title="Your Visits" style={styles.section}>
          <VisitHistoryList visits={visits} />
        </Card>
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: THEME_COLORS.surface,
  },
  header: {
    paddingTop: 56,
    paddingHorizontal: 16,
    paddingBottom: 12,
    backgroundColor: THEME_COLORS.background,
    borderBottomWidth: 1,
    borderBottomColor: THEME_COLORS.border,
  },
  backButton: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  backText: {
    fontSize: 16,
    color: THEME_COLORS.text,
    marginLeft: 4,
  },
  scrollView: {
    flex: 1,
  },
  scrollContent: {
    padding: 16,
    paddingBottom: 32,
  },
  placeHeader: {
    marginBottom: 16,
  },
  placeName: {
    fontSize: 24,
    fontWeight: '700',
    color: THEME_COLORS.text,
    marginBottom: 4,
  },
  placeCategory: {
    fontSize: 15,
    color: THEME_COLORS.textSecondary,
    textTransform: 'capitalize',
    marginBottom: 4,
  },
  placeAddress: {
    fontSize: 14,
    color: THEME_COLORS.textSecondary,
    marginBottom: 2,
  },
  placeCity: {
    fontSize: 14,
    color: THEME_COLORS.textSecondary,
  },
  section: {
    marginBottom: 16,
  },
  noDataContainer: {
    alignItems: 'center',
    paddingVertical: 24,
  },
  noDataText: {
    fontSize: 16,
    fontWeight: '600',
    color: THEME_COLORS.text,
    marginTop: 12,
    textAlign: 'center',
  },
  noDataSubtext: {
    fontSize: 14,
    color: THEME_COLORS.textSecondary,
    marginTop: 4,
    textAlign: 'center',
  },
});
