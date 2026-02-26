/**
 * Bottom tab bar layout with 4 tabs.
 *
 * Tabs:
 * - Map (map icon, index.tsx) - home screen with busyness map
 * - Explore (explore icon, explore.tsx) - personal exploration heatmap
 * - Journal (book icon, journal.tsx) - chronological visit timeline
 * - Profile (person icon, profile.tsx) - stats and achievements
 *
 * Active tab is visually highlighted with the primary theme color.
 */

import React from 'react';
import MaterialIcons from '@expo/vector-icons/MaterialIcons';
import { Tabs } from 'expo-router';

import { THEME_COLORS } from '@/constants/colors';

export default function TabLayout() {
  return (
    <Tabs
      screenOptions={{
        tabBarActiveTintColor: THEME_COLORS.primary,
        tabBarInactiveTintColor: THEME_COLORS.textSecondary,
        tabBarStyle: {
          backgroundColor: THEME_COLORS.background,
          borderTopColor: THEME_COLORS.border,
        },
        headerShown: true,
      }}>
      <Tabs.Screen
        name="index"
        options={{
          title: 'Map',
          headerShown: false,
          tabBarIcon: ({ color }) => (
            <MaterialIcons name="map" size={28} color={color} />
          ),
        }}
      />
      <Tabs.Screen
        name="explore"
        options={{
          title: 'Explore',
          tabBarIcon: ({ color }) => (
            <MaterialIcons name="explore" size={28} color={color} />
          ),
        }}
      />
      <Tabs.Screen
        name="journal"
        options={{
          title: 'Journal',
          tabBarIcon: ({ color }) => (
            <MaterialIcons name="book" size={28} color={color} />
          ),
        }}
      />
      <Tabs.Screen
        name="profile"
        options={{
          title: 'Profile',
          tabBarIcon: ({ color }) => (
            <MaterialIcons name="person" size={28} color={color} />
          ),
        }}
      />
    </Tabs>
  );
}
