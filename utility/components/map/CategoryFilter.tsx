/**
 * Horizontal scrollable category filter pills.
 *
 * Displays a row of filter buttons for place categories.
 * Selecting a filter narrows the visible pins on the map.
 * "All" shows all categories (no filter applied).
 */

import React from 'react';
import { Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';

import { THEME_COLORS } from '@/constants/colors';

/** Available category filter options. */
const CATEGORIES = [
  { label: 'All', value: '' },
  { label: 'Restaurant', value: 'restaurant' },
  { label: 'Park', value: 'park' },
  { label: 'Cafe', value: 'cafe' },
  { label: 'Museum', value: 'museum' },
  { label: 'Bar', value: 'bar' },
] as const;

export interface CategoryFilterProps {
  /** Currently selected category value (empty string for "All"). */
  selectedCategory: string;
  /** Called when a category filter pill is tapped. */
  onSelectCategory: (category: string) => void;
}

/**
 * Horizontal filter pill bar for map place categories.
 *
 * Renders a horizontally scrollable list of Pressable pills.
 * The active filter is visually highlighted with the primary color.
 */
export const CategoryFilter = ({
  selectedCategory,
  onSelectCategory,
}: CategoryFilterProps) => {
  return (
    <View style={styles.container}>
      <ScrollView
        horizontal
        showsHorizontalScrollIndicator={false}
        contentContainerStyle={styles.scrollContent}>
        {CATEGORIES.map((category) => {
          const isActive = selectedCategory === category.value;

          return (
            <Pressable
              key={category.value}
              onPress={() => onSelectCategory(category.value)}
              style={[styles.pill, isActive && styles.pillActive]}>
              <Text style={[styles.label, isActive && styles.labelActive]}>
                {category.label}
              </Text>
            </Pressable>
          );
        })}
      </ScrollView>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    position: 'absolute',
    top: 60,
    left: 0,
    right: 0,
    zIndex: 10,
  },
  scrollContent: {
    paddingHorizontal: 16,
    gap: 8,
  },
  pill: {
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 20,
    backgroundColor: THEME_COLORS.background,
    borderWidth: 1,
    borderColor: THEME_COLORS.border,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.1,
    shadowRadius: 2,
    elevation: 2,
  },
  pillActive: {
    backgroundColor: THEME_COLORS.primary,
    borderColor: THEME_COLORS.primary,
  },
  label: {
    fontSize: 14,
    fontWeight: '500',
    color: THEME_COLORS.text,
  },
  labelActive: {
    color: '#ffffff',
  },
});
