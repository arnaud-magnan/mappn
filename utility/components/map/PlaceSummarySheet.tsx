/**
 * Bottom sheet showing a place summary on pin tap.
 *
 * Displays the place name, current busyness level (text + color badge),
 * a mini popular times bar chart for the current day showing 24 hourly
 * busyness values as thin vertical bars colored by level, and a
 * "View Details" button that navigates to /place/{id}.
 *
 * Uses @gorhom/bottom-sheet for smooth gesture-driven sheet behavior.
 * Fetches PlaceDetailResponse to obtain popular_times data for the chart.
 */

import React, { useCallback, useMemo, useRef, forwardRef, useImperativeHandle } from 'react';
import { StyleSheet, Text, View } from 'react-native';
import BottomSheet, { BottomSheetView } from '@gorhom/bottom-sheet';
import { useQuery } from '@tanstack/react-query';
import { router } from 'expo-router';

import { BUSYNESS_COLORS, THEME_COLORS } from '@/constants/colors';
import { PlaceResponse } from '@/types/api';
import { getPlaceDetail } from '@/services/placesService';
import { STALE_TIME } from '@/constants/config';
import { Button } from '@/components/ui/Button';
import { getBusynessLevel, getBusynessLabel } from './PlacePin';

/** Day name abbreviations indexed by JS getDay() (0=Sunday). */
const DAY_NAMES = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];

/**
 * Map JavaScript getDay() (0=Sunday..6=Saturday) to the API's day index
 * (0=Monday..6=Sunday).
 */
const jsToApiDay = (jsDay: number): number => {
  return jsDay === 0 ? 6 : jsDay - 1;
};

export interface PlaceSummarySheetProps {
  /** The place to display, or null if no place is selected. */
  place: PlaceResponse | null;
  /** Called when the sheet is dismissed. */
  onDismiss?: () => void;
}

export interface PlaceSummarySheetRef {
  expand: () => void;
  close: () => void;
}

/**
 * Get the busyness color for a single hour value (0-100).
 */
const getBarColor = (value: number): string => {
  if (value <= 33) return BUSYNESS_COLORS.quiet;
  if (value <= 66) return BUSYNESS_COLORS.moderate;
  return BUSYNESS_COLORS.busy;
};

/**
 * Mini popular times chart component.
 *
 * Renders 24 thin vertical bars representing hourly busyness for the
 * current day. Each bar is colored by busyness level (green/yellow/red).
 * The current hour bar is highlighted with a stronger opacity and a
 * bottom indicator.
 */
function MiniPopularTimesChart({
  hours,
  currentHour,
}: {
  hours: number[];
  currentHour: number;
}) {
  const maxValue = Math.max(...hours, 1);

  return (
    <View style={miniStyles.container}>
      <View style={miniStyles.barsRow}>
        {hours.map((value, index) => {
          const heightPct = (value / maxValue) * 100;
          const isCurrentHour = index === currentHour;
          const barColor = getBarColor(value);

          return (
            <View key={index} style={miniStyles.barWrapper}>
              <View style={miniStyles.barTrack}>
                <View
                  style={[
                    miniStyles.bar,
                    {
                      height: `${Math.max(heightPct, 4)}%`,
                      backgroundColor: barColor,
                      opacity: isCurrentHour ? 1 : 0.6,
                    },
                  ]}
                />
              </View>
              {isCurrentHour && <View style={miniStyles.currentIndicator} />}
            </View>
          );
        })}
      </View>
      <View style={miniStyles.labelsRow}>
        <Text style={miniStyles.label}>12am</Text>
        <Text style={miniStyles.label}>6am</Text>
        <Text style={miniStyles.label}>12pm</Text>
        <Text style={miniStyles.label}>6pm</Text>
        <Text style={miniStyles.label}>11pm</Text>
      </View>
    </View>
  );
}

/**
 * Bottom sheet component for place summary display.
 *
 * Shows place name, busyness badge with label, a mini popular times
 * bar chart for the current day, and a "View Details" navigation button.
 */
export const PlaceSummarySheet = forwardRef<
  PlaceSummarySheetRef,
  PlaceSummarySheetProps
>(function PlaceSummarySheet({ place, onDismiss }, ref) {
  const bottomSheetRef = useRef<BottomSheet>(null);
  const snapPoints = useMemo(() => ['30%', '45%'], []);

  useImperativeHandle(ref, () => ({
    expand: () => {
      bottomSheetRef.current?.snapToIndex(0);
    },
    close: () => {
      bottomSheetRef.current?.close();
    },
  }));

  // Fetch place detail to get popular_times data for the mini chart
  const { data: placeDetail } = useQuery({
    queryKey: ['places', place?.id],
    queryFn: () => getPlaceDetail(place!.id),
    staleTime: STALE_TIME.PLACE_DETAIL,
    enabled: place !== null && place !== undefined,
  });

  const handleViewDetails = useCallback(() => {
    if (place) {
      router.push(`/place/${place.id}`);
    }
  }, [place]);

  const handleSheetChanges = useCallback(
    (index: number) => {
      if (index === -1) {
        onDismiss?.();
      }
    },
    [onDismiss]
  );

  if (!place) return null;

  const busynessLevel = getBusynessLevel(place.current_busyness);
  const busynessColor = BUSYNESS_COLORS[busynessLevel];
  const busynessLabel = getBusynessLabel(busynessLevel);

  // Extract current day's popular times hours
  const now = new Date();
  const currentHour = now.getHours();
  const currentApiDay = jsToApiDay(now.getDay());
  const currentDayName = DAY_NAMES[now.getDay()];

  const popularTimes = placeDetail?.busyness_data?.popular_times;
  const todayData = popularTimes?.find((d) => d.day === currentApiDay);
  const todayHours = todayData?.hours;

  return (
    <BottomSheet
      ref={bottomSheetRef}
      index={0}
      snapPoints={snapPoints}
      onChange={handleSheetChanges}
      enablePanDownToClose
      backgroundStyle={styles.sheetBackground}
      handleIndicatorStyle={styles.handleIndicator}>
      <BottomSheetView style={styles.content}>
        {/* Place name */}
        <Text style={styles.placeName} numberOfLines={2}>
          {place.name}
        </Text>

        {/* Category */}
        <Text style={styles.category}>
          {place.category}
        </Text>

        {/* Busyness badge */}
        <View style={styles.busynessRow}>
          <View style={[styles.busynessBadge, { backgroundColor: busynessColor }]}>
            <Text style={styles.busynessBadgeText}>{busynessLabel}</Text>
          </View>
          {place.current_busyness !== null && place.current_busyness !== undefined && (
            <Text style={styles.busynessValue}>{place.current_busyness}%</Text>
          )}
        </View>

        {/* Mini popular times chart for current day */}
        {todayHours && todayHours.length === 24 ? (
          <View style={styles.chartSection}>
            <Text style={styles.chartTitle}>Popular times - {currentDayName}</Text>
            <MiniPopularTimesChart hours={todayHours} currentHour={currentHour} />
          </View>
        ) : (
          <View style={styles.chartSection}>
            <Text style={styles.noDataText}>Popular times data unavailable</Text>
          </View>
        )}

        {/* View Details button */}
        <View style={styles.buttonContainer}>
          <Button
            title="View Details"
            onPress={handleViewDetails}
            variant="primary"
          />
        </View>
      </BottomSheetView>
    </BottomSheet>
  );
});

const miniStyles = StyleSheet.create({
  container: {
    marginTop: 4,
  },
  barsRow: {
    flexDirection: 'row',
    alignItems: 'flex-end',
    height: 40,
    gap: 1,
  },
  barWrapper: {
    flex: 1,
    alignItems: 'center',
    height: '100%',
    justifyContent: 'flex-end',
  },
  barTrack: {
    width: '100%',
    height: '100%',
    justifyContent: 'flex-end',
  },
  bar: {
    width: '100%',
    borderRadius: 1,
    minHeight: 2,
  },
  currentIndicator: {
    width: 6,
    height: 6,
    borderRadius: 3,
    backgroundColor: THEME_COLORS.primary,
    marginTop: 2,
  },
  labelsRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginTop: 2,
  },
  label: {
    fontSize: 9,
    color: THEME_COLORS.textSecondary,
  },
});

const styles = StyleSheet.create({
  sheetBackground: {
    backgroundColor: THEME_COLORS.background,
    borderRadius: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: -2 },
    shadowOpacity: 0.1,
    shadowRadius: 8,
    elevation: 8,
  },
  handleIndicator: {
    backgroundColor: THEME_COLORS.border,
    width: 40,
  },
  content: {
    padding: 16,
    paddingTop: 4,
  },
  placeName: {
    fontSize: 20,
    fontWeight: '700',
    color: THEME_COLORS.text,
    marginBottom: 4,
  },
  category: {
    fontSize: 14,
    color: THEME_COLORS.textSecondary,
    textTransform: 'capitalize',
    marginBottom: 12,
  },
  busynessRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 12,
  },
  busynessBadge: {
    paddingHorizontal: 12,
    paddingVertical: 4,
    borderRadius: 12,
  },
  busynessBadgeText: {
    color: '#ffffff',
    fontSize: 13,
    fontWeight: '600',
  },
  busynessValue: {
    marginLeft: 8,
    fontSize: 14,
    fontWeight: '600',
    color: THEME_COLORS.text,
  },
  chartSection: {
    marginBottom: 12,
  },
  chartTitle: {
    fontSize: 12,
    fontWeight: '600',
    color: THEME_COLORS.textSecondary,
    marginBottom: 4,
  },
  noDataText: {
    fontSize: 12,
    color: THEME_COLORS.textSecondary,
    fontStyle: 'italic',
  },
  buttonContainer: {
    marginTop: 4,
  },
});
