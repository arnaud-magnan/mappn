import React, { Component, ErrorInfo } from 'react';
import { StyleSheet, Text, View } from 'react-native';

import { THEME_COLORS } from '@/constants/colors';

import { Button } from './Button';

export interface ErrorBoundaryProps {
  children: React.ReactNode;
  fallback?: React.ReactNode;
}

interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
}

/**
 * React class component that catches rendering errors in its children
 * and renders a fallback UI. Uses componentDidCatch per React requirements
 * for error boundaries (function components cannot serve as error boundaries).
 */
export class ErrorBoundary extends Component<
  ErrorBoundaryProps,
  ErrorBoundaryState
> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, info: ErrorInfo): void {
    console.error('[ErrorBoundary] Caught rendering error:', error, info);
  }

  private handleRetry = (): void => {
    this.setState({ hasError: false, error: null });
  };

  render() {
    const { hasError, error } = this.state;
    const { children, fallback } = this.props;

    if (!hasError) {
      return children;
    }

    if (fallback !== undefined) {
      return fallback;
    }

    return (
      <View style={styles.container}>
        <Text style={styles.title}>Something went wrong</Text>
        {error !== null && (
          <Text style={styles.message}>{error.message}</Text>
        )}
        <View style={styles.buttonContainer}>
          <Button title="Try Again" onPress={this.handleRetry} variant="primary" />
        </View>
      </View>
    );
  }
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    padding: 32,
    backgroundColor: THEME_COLORS.background,
  },
  title: {
    fontSize: 20,
    fontWeight: '700',
    color: THEME_COLORS.text,
    marginBottom: 8,
    textAlign: 'center',
  },
  message: {
    fontSize: 14,
    color: THEME_COLORS.textSecondary,
    textAlign: 'center',
    marginBottom: 24,
  },
  buttonContainer: {
    alignSelf: 'stretch',
  },
});
