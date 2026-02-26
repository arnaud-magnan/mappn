import React from 'react';
import { StyleSheet, Text, View, ViewStyle } from 'react-native';

import { THEME_COLORS } from '@/constants/colors';

export interface CardProps {
  children: React.ReactNode;
  title?: string;
  padding?: number;
  style?: ViewStyle;
}

export function Card({ children, title, padding = 16, style }: CardProps) {
  return (
    <View style={[styles.card, { padding }, style]}>
      {title !== undefined && title !== '' && (
        <Text style={styles.title}>{title}</Text>
      )}
      {children}
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: THEME_COLORS.background,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: THEME_COLORS.border,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.08,
    shadowRadius: 4,
    elevation: 2,
  },
  title: {
    fontSize: 16,
    fontWeight: '600',
    color: THEME_COLORS.text,
    marginBottom: 12,
  },
});
