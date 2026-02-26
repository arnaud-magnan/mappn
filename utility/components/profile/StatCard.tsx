/**
 * StatCard component for displaying a single user statistic.
 *
 * Shows a MaterialIcons icon, a large numeric value, and a descriptive label.
 * Used in a row of 3 on the Profile screen.
 */

import MaterialIcons from '@expo/vector-icons/MaterialIcons';
import React from 'react';
import { StyleSheet, Text, View } from 'react-native';

import { THEME_COLORS } from '@/constants/colors';
import { Card } from '@/components/ui/Card';

export interface StatCardProps {
  icon: React.ComponentProps<typeof MaterialIcons>['name'];
  value: number;
  label: string;
}

export function StatCard({ icon, value, label }: StatCardProps) {
  return (
    <Card style={styles.card} padding={12}>
      <View style={styles.content}>
        <MaterialIcons
          name={icon}
          size={28}
          color={THEME_COLORS.primary}
          style={styles.icon}
        />
        <Text style={styles.value}>{value}</Text>
        <Text style={styles.label}>{label}</Text>
      </View>
    </Card>
  );
}

const styles = StyleSheet.create({
  card: {
    flex: 1,
    marginHorizontal: 4,
  },
  content: {
    alignItems: 'center',
  },
  icon: {
    marginBottom: 4,
  },
  value: {
    fontSize: 28,
    fontWeight: '700',
    color: THEME_COLORS.text,
    lineHeight: 34,
  },
  label: {
    fontSize: 11,
    fontWeight: '500',
    color: THEME_COLORS.textSecondary,
    textAlign: 'center',
    marginTop: 2,
  },
});
