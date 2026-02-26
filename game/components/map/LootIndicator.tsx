/**
 * Animated loot indicator component for the game map.
 *
 * Displays a pulsing animated marker near places that are eligible
 * for loot rewards when the player is within geofence range.
 *
 * Uses React Native Animated (JS-thread) instead of Reanimated so that
 * each animation frame triggers a React re-render. react-native-maps
 * captures marker bitmaps from React renders — Reanimated bypasses them,
 * causing the bitmap to go stale and the marker to disappear.
 */

import React, { memo, useEffect, useRef, useState } from 'react';
import { Animated, Easing, StyleSheet, View } from 'react-native';
import { Marker } from 'react-native-maps';
import MaterialIcons from '@expo/vector-icons/MaterialIcons';

import { GAME_COLORS } from '@/constants/colors';

export interface LootIndicatorProps {
  /** Latitude of the loot-eligible place. */
  latitude: number;
  /** Longitude of the loot-eligible place. */
  longitude: number;
  /** Name of the place (for marker title). */
  placeName?: string;
  /** Called when the loot indicator is tapped. */
  onPress?: () => void;
}

export const LootIndicator = memo(function LootIndicator({
  latitude,
  longitude,
  placeName,
  onPress,
}: LootIndicatorProps) {
  const scaleAnim = useRef(new Animated.Value(1)).current;
  const opacityAnim = useRef(new Animated.Value(1)).current;
  const [tracksViewChanges, setTracksViewChanges] = useState(true);

  useEffect(() => {
    const id = setTimeout(() => setTracksViewChanges(false), 500);
    return () => clearTimeout(id);
  }, []);

  useEffect(() => {
    const pulse = Animated.loop(
      Animated.parallel([
        Animated.sequence([
          Animated.timing(scaleAnim, {
            toValue: 1.3,
            duration: 800,
            easing: Easing.inOut(Easing.ease),
            useNativeDriver: true,
          }),
          Animated.timing(scaleAnim, {
            toValue: 1,
            duration: 800,
            easing: Easing.inOut(Easing.ease),
            useNativeDriver: true,
          }),
        ]),
        Animated.sequence([
          Animated.timing(opacityAnim, {
            toValue: 0.6,
            duration: 800,
            easing: Easing.inOut(Easing.ease),
            useNativeDriver: true,
          }),
          Animated.timing(opacityAnim, {
            toValue: 1,
            duration: 800,
            easing: Easing.inOut(Easing.ease),
            useNativeDriver: true,
          }),
        ]),
      ])
    );

    pulse.start();
    return () => {
      pulse.stop();
      scaleAnim.setValue(1);
      opacityAnim.setValue(1);
    };
  }, [scaleAnim, opacityAnim]);

  return (
    <Marker
      coordinate={{ latitude, longitude }}
      tracksViewChanges={tracksViewChanges}
      onPress={onPress}
      title={placeName ?? 'Loot nearby'}
      anchor={{ x: 0.5, y: 0.5 }}>
      <View style={styles.container}>
        <Animated.View
          style={[
            styles.pulseRing,
            {
              transform: [{ scale: scaleAnim }],
              opacity: opacityAnim,
            },
          ]}
        />
        <View style={styles.iconContainer}>
          <MaterialIcons name="card-giftcard" size={18} color="#ffffff" />
        </View>
      </View>
    </Marker>
  );
});

const styles = StyleSheet.create({
  container: {
    width: 44,
    height: 44,
    alignItems: 'center',
    justifyContent: 'center',
  },
  pulseRing: {
    position: 'absolute',
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: 'rgba(245, 158, 11, 0.3)',
    borderWidth: 2,
    borderColor: GAME_COLORS.accent,
  },
  iconContainer: {
    width: 28,
    height: 28,
    borderRadius: 14,
    backgroundColor: GAME_COLORS.accent,
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 2,
    borderColor: '#ffffff',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.3,
    shadowRadius: 2,
    elevation: 3,
  },
});
