/**
 * Busyness-colored map marker for a place.
 *
 * Renders a Marker on the map with a colored indicator based on
 * the place's current busyness level:
 * - Green (#22c55e) circle with checkmark icon for quiet (0-33)
 * - Yellow (#eab308) diamond (rotated square) with warning icon for moderate (34-66)
 * - Red (#ef4444) square with priority-high icon for busy (67-100)
 * - Grey (#9ca3af) circle with help-outline icon for no data (null/undefined)
 *
 * Pin shapes and icons vary by busyness level for non-color differentiation,
 * making the map accessible to colorblind users (protanopia, deuteranopia).
 *
 * Uses tracksViewChanges={false} for performance with many markers.
 */

import React, { memo } from 'react';
import { StyleSheet, View } from 'react-native';
import { Marker } from 'react-native-maps';
import MaterialIcons from '@expo/vector-icons/MaterialIcons';

import { BUSYNESS_COLORS, BusynessLevel } from '@/constants/colors';
import { PlaceResponse } from '@/types/api';

export interface PlacePinProps {
  /** Place data including coordinates and busyness. */
  place: PlaceResponse;
  /** Called when the pin is tapped. */
  onPress?: (place: PlaceResponse) => void;
}

/**
 * Determine the busyness level from a numeric value.
 *
 * @param busyness - Busyness value 0-100, or null/undefined for no data.
 * @returns The busyness level key.
 */
export const getBusynessLevel = (
  busyness: number | null | undefined
): BusynessLevel => {
  if (busyness === null || busyness === undefined) return 'noData';
  if (busyness <= 33) return 'quiet';
  if (busyness <= 66) return 'moderate';
  return 'busy';
};

/**
 * Get the busyness label text for accessibility and display.
 */
export const getBusynessLabel = (level: BusynessLevel): string => {
  switch (level) {
    case 'quiet':
      return 'Quiet';
    case 'moderate':
      return 'Moderate';
    case 'busy':
      return 'Busy';
    case 'noData':
      return 'No data';
  }
};

/**
 * Pin shape and icon configuration per busyness level.
 *
 * Each level gets a distinct shape (via borderRadius) and icon so that
 * pins are distinguishable even without color perception:
 * - quiet: circle + check-circle icon
 * - moderate: diamond (45deg rotation) + warning icon
 * - busy: square + priority-high icon
 * - noData: circle + help-outline icon
 */
export const PIN_SHAPES: Record<
  BusynessLevel,
  {
    iconName: React.ComponentProps<typeof MaterialIcons>['name'];
    borderRadius: number;
    rotation: string;
  }
> = {
  quiet: { iconName: 'check-circle', borderRadius: 12, rotation: '0deg' },
  moderate: { iconName: 'warning', borderRadius: 4, rotation: '45deg' },
  busy: { iconName: 'priority-high', borderRadius: 2, rotation: '0deg' },
  noData: { iconName: 'help-outline', borderRadius: 12, rotation: '0deg' },
};

/**
 * Busyness-colored map pin component with shape and icon differentiation.
 *
 * Memoized to prevent unnecessary re-renders when the map moves.
 * tracksViewChanges is set to false for optimal performance with
 * large numbers of markers.
 */
export const PlacePin = memo(function PlacePin({
  place,
  onPress,
}: PlacePinProps) {
  const level = getBusynessLevel(place.current_busyness);
  const color = BUSYNESS_COLORS[level];
  const pinShape = PIN_SHAPES[level];

  return (
    <Marker
      coordinate={{
        latitude: place.lat,
        longitude: place.lon,
      }}
      tracksViewChanges={false}
      onPress={() => onPress?.(place)}
      title={place.name}
      description={getBusynessLabel(level)}>
      <View
        style={[
          styles.pin,
          {
            backgroundColor: color,
            borderRadius: pinShape.borderRadius,
            transform: [{ rotate: pinShape.rotation }],
          },
        ]}>
        <View style={{ transform: [{ rotate: pinShape.rotation === '0deg' ? '0deg' : '-45deg' }] }}>
          <MaterialIcons
            name={pinShape.iconName}
            size={14}
            color="#ffffff"
          />
        </View>
      </View>
    </Marker>
  );
});

const styles = StyleSheet.create({
  pin: {
    width: 26,
    height: 26,
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
