/**
 * Register screen.
 *
 * Provides email, username, and password fields with validation,
 * error display for failed registration attempts, and a link to
 * navigate to the login screen. On successful registration, navigates
 * to the (tabs) map view.
 */

import React, { useState } from 'react';
import {
  KeyboardAvoidingView,
  Platform,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
} from 'react-native';
import { router } from 'expo-router';
import { AxiosError } from 'axios';

import { Button } from '@/components/ui/Button';
import { THEME_COLORS } from '@/constants/colors';
import { register } from '@/services/authService';

/** Simple email format validation. */
const isValidEmail = (email: string): boolean => {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
};

/** Minimum password length matching backend validation. */
const MIN_PASSWORD_LENGTH = 8;

export default function RegisterScreen() {
  const [email, setEmail] = useState('');
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [errors, setErrors] = useState<{
    email?: string;
    username?: string;
    password?: string;
    general?: string;
  }>({});
  const [isLoading, setIsLoading] = useState(false);

  const validate = (): boolean => {
    const newErrors: { email?: string; username?: string; password?: string } = {};

    if (!email.trim()) {
      newErrors.email = 'Please enter your email address';
    } else if (!isValidEmail(email.trim())) {
      newErrors.email = 'Please enter a valid email address';
    }

    if (!username.trim()) {
      newErrors.username = 'Please enter a username';
    } else if (username.trim().length < 3) {
      newErrors.username = 'Username must be at least 3 characters';
    }

    if (!password) {
      newErrors.password = 'Please enter a password';
    } else if (password.length < MIN_PASSWORD_LENGTH) {
      newErrors.password = `Password must be at least ${MIN_PASSWORD_LENGTH} characters`;
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleRegister = async () => {
    if (!validate()) return;

    setIsLoading(true);
    setErrors({});

    try {
      await register(email.trim(), username.trim(), password);
      router.replace('/(tabs)');
    } catch (err) {
      const axiosError = err as AxiosError<{ detail?: string }>;

      if (!axiosError.response) {
        setErrors({ general: 'Network error. Please check your connection.' });
      } else if (axiosError.response.status === 409) {
        setErrors({ general: 'An account with this email or username already exists.' });
      } else if (axiosError.response.status === 422) {
        setErrors({ general: 'Please check your input and try again.' });
      } else if (axiosError.response.data?.detail) {
        setErrors({ general: axiosError.response.data.detail });
      } else {
        setErrors({ general: 'An unexpected error occurred. Please try again.' });
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <KeyboardAvoidingView
      style={styles.container}
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}>
      <ScrollView
        contentContainerStyle={styles.scrollContent}
        keyboardShouldPersistTaps="handled">
        <View style={styles.header}>
          <Text style={styles.title}>Create Account</Text>
          <Text style={styles.subtitle}>Join Mappn and start exploring</Text>
        </View>

        {errors.general ? (
          <View style={styles.errorBanner}>
            <Text style={styles.errorBannerText}>{errors.general}</Text>
          </View>
        ) : null}

        <View style={styles.form}>
          <View style={styles.fieldGroup}>
            <Text style={styles.label}>Email</Text>
            <TextInput
              style={[styles.input, errors.email ? styles.inputError : null]}
              value={email}
              onChangeText={setEmail}
              placeholder="your@email.com"
              placeholderTextColor={THEME_COLORS.textSecondary}
              keyboardType="email-address"
              autoCapitalize="none"
              autoComplete="email"
              autoCorrect={false}
              editable={!isLoading}
              testID="register-email-input"
            />
            {errors.email ? (
              <Text style={styles.fieldError}>{errors.email}</Text>
            ) : null}
          </View>

          <View style={styles.fieldGroup}>
            <Text style={styles.label}>Username</Text>
            <TextInput
              style={[styles.input, errors.username ? styles.inputError : null]}
              value={username}
              onChangeText={setUsername}
              placeholder="Choose a username"
              placeholderTextColor={THEME_COLORS.textSecondary}
              autoCapitalize="none"
              autoComplete="username"
              autoCorrect={false}
              editable={!isLoading}
              testID="register-username-input"
            />
            {errors.username ? (
              <Text style={styles.fieldError}>{errors.username}</Text>
            ) : null}
          </View>

          <View style={styles.fieldGroup}>
            <Text style={styles.label}>Password</Text>
            <TextInput
              style={[styles.input, errors.password ? styles.inputError : null]}
              value={password}
              onChangeText={setPassword}
              placeholder="At least 8 characters"
              placeholderTextColor={THEME_COLORS.textSecondary}
              secureTextEntry
              autoCapitalize="none"
              autoComplete="new-password"
              editable={!isLoading}
              testID="register-password-input"
            />
            {errors.password ? (
              <Text style={styles.fieldError}>{errors.password}</Text>
            ) : null}
          </View>

          <View style={styles.buttonContainer}>
            <Button
              title="Create Account"
              onPress={handleRegister}
              loading={isLoading}
              disabled={isLoading}
            />
          </View>
        </View>

        <View style={styles.footer}>
          <Text style={styles.footerText}>Already have an account? </Text>
          <Button
            title="Login"
            onPress={() => router.replace('/(auth)/login' as const as '/')}
            variant="text"
            disabled={isLoading}
          />
        </View>
      </ScrollView>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: THEME_COLORS.background,
  },
  scrollContent: {
    flexGrow: 1,
    justifyContent: 'center',
    padding: 24,
  },
  header: {
    marginBottom: 32,
    alignItems: 'center',
  },
  title: {
    fontSize: 28,
    fontWeight: '700',
    color: THEME_COLORS.text,
    marginBottom: 8,
  },
  subtitle: {
    fontSize: 16,
    color: THEME_COLORS.textSecondary,
  },
  errorBanner: {
    backgroundColor: '#fef2f2',
    borderWidth: 1,
    borderColor: THEME_COLORS.error,
    borderRadius: 8,
    padding: 12,
    marginBottom: 16,
  },
  errorBannerText: {
    color: THEME_COLORS.error,
    fontSize: 14,
    textAlign: 'center',
  },
  form: {
    gap: 16,
  },
  fieldGroup: {
    gap: 4,
  },
  label: {
    fontSize: 14,
    fontWeight: '600',
    color: THEME_COLORS.text,
    marginBottom: 4,
  },
  input: {
    borderWidth: 1,
    borderColor: THEME_COLORS.border,
    borderRadius: 8,
    paddingVertical: 12,
    paddingHorizontal: 16,
    fontSize: 16,
    color: THEME_COLORS.text,
    backgroundColor: THEME_COLORS.surface,
  },
  inputError: {
    borderColor: THEME_COLORS.error,
  },
  fieldError: {
    color: THEME_COLORS.error,
    fontSize: 12,
    marginTop: 4,
  },
  buttonContainer: {
    marginTop: 8,
  },
  footer: {
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
    marginTop: 24,
  },
  footerText: {
    fontSize: 14,
    color: THEME_COLORS.textSecondary,
  },
});
