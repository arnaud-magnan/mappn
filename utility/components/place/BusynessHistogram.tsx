/**
 * Hour-by-hour busyness bar chart with day selector.
 *
 * Renders 24 bars from the popular_times data for the selected day,
 * where each bar height is proportional to its 0-100 busyness value.
 * Bars are colored by busyness level (green/yellow/red) and the
 * current hour bar is visually highlighted with a border.
 *
 * A row of 7 day buttons (Mon-Sun) allows switching between days.
 */

import React, { useMemo, useState } from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';
import { BarChart } from 'react-native-gifted-charts';

import { BusynessData } from '@/types/api';
import { BUSYNESS_COLORS, THEME_COLORS } from '@/constants/colors';

const DAY_LABELS = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];

export interface BusynessHistogramProps {
  /** Busyness data containing popular_times array. */
  data: BusynessData;
}

/**
 * Get bar color based on busyness value (0-100).
 */
const getBarColor = (value: number): string => {
  if (value <= 33) return BUSYNESS_COLORS.quiet;
  if (value <= 66) return BUSYNESS_COLORS.moderate;
  return BUSYNESS_COLORS.busy;
};

/**
 * BusynessHistogram renders a 24-bar chart for the selected day
 * from the popular_times data with a day selector row.
 */
export function BusynessHistogram({ data }: BusynessHistogramProps) {
  const currentHour = new Date().getHours();
  const currentDay = (new Date().getDay() + 6) % 7; // JS Sunday=0 -> Mon=0
  const [selectedDay, setSelectedDay] = useState(currentDay);

  const dayData = useMemo(() => {
    const dayEntry = data.popular_times.find((d) => d.day === selectedDay);
    if (!dayEntry) return [];
    return dayEntry.hours;
  }, [data.popular_times, selectedDay]);

  const barData = useMemo(() => {
    return dayData.map((value, index) => ({
      value,
      label: index % 3 === 0 ? `${index}` : '',
      frontColor: getBarColor(value),
      barBorderRadius: 2,
      barBorderColor:
        selectedDay === currentDay && index === currentHour
          ? THEME_COLORS.primary
          : 'transparent',
      barBorderWidth:
        selectedDay === currentDay && index === currentHour ? 2 : 0,
      spacing: 2,
    }));
  }, [dayData, selectedDay, currentDay, currentHour]);

  return (
    <View style={styles.container}>
      {/* Day selector */}
      <View style={styles.daySelector}>
        {DAY_LABELS.map((label, index) => (
          <Pressable
            key={label}
            style={[
              styles.dayButton,
              selectedDay === index && styles.dayButtonActive,
            ]}
            onPress={() => setSelectedDay(index)}
            accessibilityRole="button"
            accessibilityLabel={`Select ${label}`}
            accessibilityState={{ selected: selectedDay === index }}>
            <Text
              style={[
                styles.dayButtonText,
                selectedDay === index && styles.dayButtonTextActive,
              ]}>
              {label}
            </Text>
          </Pressable>
        ))}
      </View>

      {/* Bar chart */}
      {barData.length === 24 ? (
        <BarChart
          data={barData}
          barWidth={8}
          noOfSections={4}
          maxValue={100}
          height={150}
          yAxisThickness={0}
          xAxisThickness={1}
          xAxisColor={THEME_COLORS.border}
          yAxisTextStyle={styles.axisText}
          xAxisLabelTextStyle={styles.axisText}
          hideRules
          isAnimated={false}
        />
      ) : (
        <Text style={styles.noDataText}>No data for this day</Text>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    paddingVertical: 8,
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
  axisText: {
    fontSize: 10,
    color: THEME_COLORS.textSecondary,
  },
  noDataText: {
    fontSize: 14,
    color: THEME_COLORS.textSecondary,
    textAlign: 'center',
    paddingVertical: 24,
  },
});
