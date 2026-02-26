import React from 'react';
import { ActivityIndicator, StyleSheet, Text, View } from 'react-native';

import { THEME_COLORS } from '@/constants/colors';

export interface LoadingSpinnerProps {
  message?: string;
  size?: 'small' | 'large';
  color?: string;
}

export function LoadingSpinner({
  message,
  size = 'large',
  color = THEME_COLORS.primary,
}: LoadingSpinnerProps) {
  return (
    <View style={styles.container}>
      <ActivityIndicator size={size} color={color} />
      {message !== undefined && message !== '' && (
        <Text style={styles.message}>{message}</Text>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    padding: 24,
  },
  message: {
    marginTop: 12,
    fontSize: 14,
    color: THEME_COLORS.textSecondary,
    textAlign: 'center',
  },
});
