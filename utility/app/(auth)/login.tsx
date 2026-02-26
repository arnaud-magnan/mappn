/**
 * Login screen.
 *
 * Provides email and password fields with validation, error display
 * for failed login attempts, and a link to navigate to the register screen.
 * On successful login, navigates to the (tabs) map view.
 */

import React, { useEffect, useState } from 'react';
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
import { login } from '@/services/authService';
import { useAuthStore } from '@/stores/authStore';

/** Simple email format validation. */
const isValidEmail = (email: string): boolean => {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
};

export default function LoginScreen() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [errors, setErrors] = useState<{ email?: string; password?: string; general?: string }>({});
  const [isLoading, setIsLoading] = useState(false);

  // Check if user was redirected here due to session expiry
  useEffect(() => {
    const { sessionExpired, setSessionExpired } = useAuthStore.getState();
    if (sessionExpired) {
      setErrors({ general: 'Session expired, please log in again' });
      setSessionExpired(false);
    }
  }, []);

  const validate = (): boolean => {
    const newErrors: { email?: string; password?: string } = {};

    if (!email.trim()) {
      newErrors.email = 'Please enter your email address';
    } else if (!isValidEmail(email.trim())) {
      newErrors.email = 'Please enter a valid email address';
    }

    if (!password) {
      newErrors.password = 'Please enter your password';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleLogin = async () => {
    if (!validate()) return;

    setIsLoading(true);
    setErrors({});

    try {
      await login(email.trim(), password);
      router.replace('/(tabs)');
    } catch (err) {
      const axiosError = err as AxiosError<{ detail?: string }>;

      if (!axiosError.response) {
        setErrors({ general: 'Network error. Please check your connection.' });
      } else if (axiosError.response.status === 401) {
        setErrors({ general: 'Invalid email or password. Please try again.' });
      } else if (axiosError.response.status === 429) {
        setErrors({ general: 'Too many login attempts. Please try again later.' });
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
          <Text style={styles.title}>Welcome Back</Text>
          <Text style={styles.subtitle}>Sign in to continue exploring</Text>
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
              testID="login-email-input"
            />
            {errors.email ? (
              <Text style={styles.fieldError}>{errors.email}</Text>
            ) : null}
          </View>

          <View style={styles.fieldGroup}>
            <Text style={styles.label}>Password</Text>
            <TextInput
              style={[styles.input, errors.password ? styles.inputError : null]}
              value={password}
              onChangeText={setPassword}
              placeholder="Enter your password"
              placeholderTextColor={THEME_COLORS.textSecondary}
              secureTextEntry
              autoCapitalize="none"
              autoComplete="password"
              editable={!isLoading}
              testID="login-password-input"
            />
            {errors.password ? (
              <Text style={styles.fieldError}>{errors.password}</Text>
            ) : null}
          </View>

          <View style={styles.buttonContainer}>
            <Button
              title="Sign In"
              onPress={handleLogin}
              loading={isLoading}
              disabled={isLoading}
            />
          </View>
        </View>

        <View style={styles.footer}>
          <Text style={styles.footerText}>Don't have an account? </Text>
          <Button
            title="Register"
            onPress={() => router.replace('/(auth)/register' as const as '/')}
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
