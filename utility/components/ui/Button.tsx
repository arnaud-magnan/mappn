import React from 'react';
import {
  ActivityIndicator,
  Pressable,
  StyleSheet,
  Text,
  View,
} from 'react-native';

import { THEME_COLORS } from '@/constants/colors';

export type ButtonVariant = 'primary' | 'secondary' | 'text';

export interface ButtonProps {
  title: string;
  onPress: () => void;
  loading?: boolean;
  disabled?: boolean;
  variant?: ButtonVariant;
}

export function Button({
  title,
  onPress,
  loading = false,
  disabled = false,
  variant = 'primary',
}: ButtonProps) {
  const isDisabled = disabled || loading;

  return (
    <Pressable
      onPress={onPress}
      disabled={isDisabled}
      style={({ pressed }) => [
        styles.base,
        variant === 'primary' && styles.primary,
        variant === 'secondary' && styles.secondary,
        variant === 'text' && styles.text,
        isDisabled && styles.disabled,
        pressed && !isDisabled && styles.pressed,
      ]}>
      <View style={styles.content}>
        {loading && (
          <ActivityIndicator
            size="small"
            color={variant === 'primary' ? '#ffffff' : THEME_COLORS.primary}
            style={styles.spinner}
          />
        )}
        <Text
          style={[
            styles.label,
            variant === 'primary' && styles.labelPrimary,
            variant === 'secondary' && styles.labelSecondary,
            variant === 'text' && styles.labelText,
            isDisabled && styles.labelDisabled,
          ]}>
          {title}
        </Text>
      </View>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  base: {
    borderRadius: 8,
    paddingVertical: 12,
    paddingHorizontal: 20,
    alignItems: 'center',
    justifyContent: 'center',
  },
  primary: {
    backgroundColor: THEME_COLORS.primary,
  },
  secondary: {
    backgroundColor: THEME_COLORS.background,
    borderWidth: 1,
    borderColor: THEME_COLORS.primary,
  },
  text: {
    backgroundColor: 'transparent',
    paddingVertical: 8,
    paddingHorizontal: 4,
  },
  disabled: {
    opacity: 0.5,
  },
  pressed: {
    opacity: 0.8,
  },
  content: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  spinner: {
    marginRight: 8,
  },
  label: {
    fontSize: 16,
    fontWeight: '600',
  },
  labelPrimary: {
    color: '#ffffff',
  },
  labelSecondary: {
    color: THEME_COLORS.primary,
  },
  labelText: {
    color: THEME_COLORS.primary,
  },
  labelDisabled: {
    color: THEME_COLORS.textSecondary,
  },
});
