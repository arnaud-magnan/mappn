/**
 * Root layout for the Mappn utility app.
 *
 * Responsibilities:
 * - Wraps the entire app in GestureHandlerRootView (required for bottom sheet and gestures)
 * - Provides QueryClientProvider for TanStack Query (server state caching)
 * - Wraps children in ErrorBoundary for graceful error handling
 * - Loads fonts before rendering
 * - Checks SecureStore for existing auth tokens on mount
 * - Redirects to (auth)/login or (tabs) based on authentication state
 */

import React, { useEffect, useState } from 'react';
import { GestureHandlerRootView } from 'react-native-gesture-handler';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Stack, router } from 'expo-router';
import * as SplashScreen from 'expo-splash-screen';
import { useFonts } from 'expo-font';
import FontAwesome from '@expo/vector-icons/FontAwesome';

import { ErrorBoundary } from '@/components/ui/ErrorBoundary';
import { NetworkBanner } from '@/components/ui/NetworkBanner';
import { useAuthStore } from '@/stores/authStore';
import { STALE_TIME } from '@/constants/config';

export {
  // Catch any errors thrown by the Layout component.
  ErrorBoundary as ExpoErrorBoundary,
} from 'expo-router';

export const unstable_settings = {
  initialRouteName: '(tabs)',
};

// Prevent the splash screen from auto-hiding before asset loading is complete.
SplashScreen.preventAutoHideAsync();

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: STALE_TIME.PLACES,
      retry: 2,
    },
  },
});

export default function RootLayout() {
  const [loaded, error] = useFonts({
    SpaceMono: require('../assets/fonts/SpaceMono-Regular.ttf'),
    ...FontAwesome.font,
  });

  // Expo Router uses Error Boundaries to catch errors in the navigation tree.
  useEffect(() => {
    if (error) throw error;
  }, [error]);

  useEffect(() => {
    if (loaded) {
      SplashScreen.hideAsync();
    }
  }, [loaded]);

  if (!loaded) {
    return null;
  }

  return <RootLayoutNav />;
}

function RootLayoutNav() {
  const [isReady, setIsReady] = useState(false);
  const loadTokens = useAuthStore((state) => state.loadTokens);
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);

  useEffect(() => {
    const checkAuth = async () => {
      await loadTokens();
      setIsReady(true);
    };
    checkAuth();
  }, [loadTokens]);

  useEffect(() => {
    if (!isReady) return;

    if (isAuthenticated) {
      router.replace('/(tabs)');
    } else {
      router.replace('/(auth)/login' as const as '/');
    }
  }, [isReady, isAuthenticated]);

  if (!isReady) return null;

  return (
    <GestureHandlerRootView style={{ flex: 1 }}>
      <QueryClientProvider client={queryClient}>
        <ErrorBoundary>
          <NetworkBanner />
          <Stack screenOptions={{ headerShown: false }}>
            <Stack.Screen name="(tabs)" options={{ headerShown: false }} />
            <Stack.Screen name="(auth)" options={{ headerShown: false }} />
          </Stack>
        </ErrorBoundary>
      </QueryClientProvider>
    </GestureHandlerRootView>
  );
}
