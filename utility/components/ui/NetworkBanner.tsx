import NetInfo, { NetInfoState } from '@react-native-community/netinfo';
import React, { useEffect, useState } from 'react';
import { StyleSheet, Text, View } from 'react-native';

import { THEME_COLORS } from '@/constants/colors';

export interface NetworkBannerProps {
  message?: string;
}

/**
 * Monitors network connectivity using @react-native-community/netinfo and
 * renders a warning banner when the device is offline. Hides automatically
 * when connectivity is restored.
 */
export function NetworkBanner({
  message = 'No internet connection. Some features may be unavailable.',
}: NetworkBannerProps) {
  const [isConnected, setIsConnected] = useState<boolean>(true);

  useEffect(() => {
    // Fetch current state on mount
    NetInfo.fetch().then((state: NetInfoState) => {
      setIsConnected(state.isConnected ?? true);
    });

    // Subscribe to connectivity changes
    const unsubscribe = NetInfo.addEventListener((state: NetInfoState) => {
      setIsConnected(state.isConnected ?? true);
    });

    return unsubscribe;
  }, []);

  if (isConnected) {
    return null;
  }

  return (
    <View style={styles.banner}>
      <Text style={styles.message}>{message}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  banner: {
    backgroundColor: THEME_COLORS.warning,
    paddingVertical: 8,
    paddingHorizontal: 16,
    alignItems: 'center',
    justifyContent: 'center',
  },
  message: {
    fontSize: 13,
    fontWeight: '600',
    color: '#ffffff',
    textAlign: 'center',
  },
});
