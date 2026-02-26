/**
 * Busyness forecast selector with day picker and hour picker.
 *
 * Allows the user to select a future day (Mon-Sun) and hour (0-23),
 * then queries GET /places/{id}/forecast via the useForecast hook
 * and displays the predicted busyness with color coding.
 */

import React, { useState } from 'react';
import {
  ActivityIndicator,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from 'react-native';

import { useForecast } from '@/hooks/useForecast';
import { BUSYNESS_COLORS, BusynessLevel, THEME_COLORS } from '@/constants/colors';

const DAY_LABELS = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];

export interface ForecastSliderProps {
  /** The place ID to query forecast for. */
  placeId: number;
}

/**
 * Get busyness level from a predicted value.
 */
const getBusynessLevel = (value: number): BusynessLevel => {
  if (value <= 33) return 'quiet';
  if (value <= 66) return 'moderate';
  return 'busy';
};

/**
 * Get label for busyness level.
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
 * Format an hour number (0-23) to a display string.
 */
const formatHour = (hour: number): string => {
  if (hour === 0) return '12am';
  if (hour < 12) return `${hour}am`;
  if (hour === 12) return '12pm';
  return `${hour - 12}pm`;
};

/**
 * ForecastSlider lets the user select a day and hour to see the
 * predicted busyness for a place at that future time.
 */
export function ForecastSlider({ placeId }: ForecastSliderProps) {
  const [selectedDay, setSelectedDay] = useState<number | undefined>(undefined);
  const [selectedHour, setSelectedHour] = useState<number | undefined>(
    undefined
  );

  const { data: forecast, isLoading } = useForecast(
    placeId,
    selectedDay,
    selectedHour
  );

  const predicted_busyness = forecast?.predicted_busyness;
  const hasResult =
    predicted_busyness !== undefined && predicted_busyness !== null;
  const level = hasResult ? getBusynessLevel(predicted_busyness) : null;
  const color = level ? BUSYNESS_COLORS[level] : BUSYNESS_COLORS.noData;
  const label = level ? getBusynessLabel(level) : '';

  return (
    <View style={styles.container}>
      {/* Day picker */}
      <Text style={styles.sectionLabel}>Select day</Text>
      <View style={styles.daySelector}>
        {DAY_LABELS.map((dayLabel, index) => (
          <Pressable
            key={dayLabel}
            style={[
              styles.dayButton,
              selectedDay === index && styles.dayButtonActive,
            ]}
            onPress={() => setSelectedDay(index)}
            accessibilityRole="button"
            accessibilityLabel={`Forecast ${dayLabel}`}>
            <Text
              style={[
                styles.dayButtonText,
                selectedDay === index && styles.dayButtonTextActive,
              ]}>
              {dayLabel}
            </Text>
          </Pressable>
        ))}
      </View>

      {/* Hour picker */}
      <Text style={styles.sectionLabel}>Select hour</Text>
      <ScrollView
        horizontal
        showsHorizontalScrollIndicator={false}
        style={styles.hourScroll}
        contentContainerStyle={styles.hourScrollContent}>
        {Array.from({ length: 24 }, (_, i) => i).map((hour) => (
          <Pressable
            key={hour}
            style={[
              styles.hourButton,
              selectedHour === hour && styles.hourButtonActive,
            ]}
            onPress={() => setSelectedHour(hour)}
            accessibilityRole="button"
            accessibilityLabel={`Forecast at ${formatHour(hour)}`}>
            <Text
              style={[
                styles.hourButtonText,
                selectedHour === hour && styles.hourButtonTextActive,
              ]}>
              {formatHour(hour)}
            </Text>
          </Pressable>
        ))}
      </ScrollView>

      {/* Forecast result */}
      {isLoading && (
        <View style={styles.resultContainer}>
          <ActivityIndicator size="small" color={THEME_COLORS.primary} />
          <Text style={styles.loadingText}>Loading forecast...</Text>
        </View>
      )}

      {!isLoading && hasResult && (
        <View style={styles.resultContainer}>
          <View style={[styles.resultBadge, { backgroundColor: color }]}>
            <Text style={styles.resultBadgeText}>{label}</Text>
          </View>
          <Text style={styles.resultValue}>
            {predicted_busyness}% predicted busyness
          </Text>
        </View>
      )}

      {!isLoading &&
        !hasResult &&
        selectedDay !== undefined &&
        selectedHour !== undefined && (
          <View style={styles.resultContainer}>
            <Text style={styles.noDataText}>
              No forecast data available
            </Text>
          </View>
        )}

      {selectedDay === undefined || selectedHour === undefined ? (
        <View style={styles.resultContainer}>
          <Text style={styles.hintText}>
            Select a day and hour to see the forecast
          </Text>
        </View>
      ) : null}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    paddingVertical: 8,
  },
  sectionLabel: {
    fontSize: 13,
    fontWeight: '600',
    color: THEME_COLORS.textSecondary,
    marginBottom: 8,
  },
  daySelector: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 16,
  },
  dayButton: {
    paddingHorizontal: 10,
    paddingVertical: 6,
    borderRadius: 16,
    backgroundColor: THEME_COLORS.surface,
    borderWidth: 1,
    borderColor: THEME_COLORS.border,
  },
  dayButtonActive: {
    backgroundColor: THEME_COLORS.primary,
    borderColor: THEME_COLORS.primary,
  },
  dayButtonText: {
    fontSize: 12,
    fontWeight: '600',
    color: THEME_COLORS.textSecondary,
  },
  dayButtonTextActive: {
    color: '#ffffff',
  },
  hourScroll: {
    marginBottom: 16,
  },
  hourScrollContent: {
    paddingRight: 16,
  },
  hourButton: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 16,
    backgroundColor: THEME_COLORS.surface,
    borderWidth: 1,
    borderColor: THEME_COLORS.border,
    marginRight: 6,
  },
  hourButtonActive: {
    backgroundColor: THEME_COLORS.primary,
    borderColor: THEME_COLORS.primary,
  },
  hourButtonText: {
    fontSize: 12,
    fontWeight: '600',
    color: THEME_COLORS.textSecondary,
  },
  hourButtonTextActive: {
    color: '#ffffff',
  },
  resultContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 8,
  },
  resultBadge: {
    paddingHorizontal: 14,
    paddingVertical: 6,
    borderRadius: 16,
  },
  resultBadgeText: {
    color: '#ffffff',
    fontSize: 14,
    fontWeight: '700',
  },
  resultValue: {
    marginLeft: 10,
    fontSize: 14,
    fontWeight: '600',
    color: THEME_COLORS.text,
  },
  loadingText: {
    marginLeft: 8,
    fontSize: 14,
    color: THEME_COLORS.textSecondary,
  },
  noDataText: {
    fontSize: 14,
    color: THEME_COLORS.textSecondary,
  },
  hintText: {
    fontSize: 14,
    color: THEME_COLORS.textSecondary,
    fontStyle: 'italic',
  },
});
