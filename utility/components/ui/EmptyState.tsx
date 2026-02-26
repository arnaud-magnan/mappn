import MaterialIcons from '@expo/vector-icons/MaterialIcons';
import React from 'react';
import { StyleSheet, Text, View } from 'react-native';

import { THEME_COLORS } from '@/constants/colors';

import { Button } from './Button';

export interface EmptyStateProps {
  icon?: React.ComponentProps<typeof MaterialIcons>['name'];
  title: string;
  description: string;
  actionLabel?: string;
  onAction?: () => void;
}

export function EmptyState({
  icon = 'inbox',
  title,
  description,
  actionLabel,
  onAction,
}: EmptyStateProps) {
  return (
    <View style={styles.container}>
      <MaterialIcons
        name={icon}
        size={64}
        color={THEME_COLORS.textSecondary}
        style={styles.icon}
      />
      <Text style={styles.title}>{title}</Text>
      <Text style={styles.description}>{description}</Text>
      {actionLabel !== undefined && actionLabel !== '' && onAction !== undefined && (
        <View style={styles.buttonContainer}>
          <Button title={actionLabel} onPress={onAction} variant="primary" />
        </View>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    padding: 32,
  },
  icon: {
    marginBottom: 16,
  },
  title: {
    fontSize: 20,
    fontWeight: '700',
    color: THEME_COLORS.text,
    textAlign: 'center',
    marginBottom: 8,
  },
  description: {
    fontSize: 14,
    color: THEME_COLORS.textSecondary,
    textAlign: 'center',
    lineHeight: 20,
  },
  buttonContainer: {
    marginTop: 24,
    alignSelf: 'stretch',
  },
});
