/**
 * GeofenceCircle — map overlay showing the active 75-metre visit geofence.
 *
 * Rendered on the MapView only when the player is inside a place's
 * geofence (claimingState is active). The circle radius matches the
 * backend `geofence_radius_m = 75` setting, giving the player a clear
 * spatial boundary of the area they must stay within.
 */

import React, { memo } from 'react';
import { Circle } from 'react-native-maps';

export interface GeofenceCircleProps {
  /** Player's current latitude. */
  latitude: number;
  /** Player's current longitude. */
  longitude: number;
}

export const GeofenceCircle = memo(function GeofenceCircle({
  latitude,
  longitude,
}: GeofenceCircleProps) {
  return (
    <Circle
      center={{ latitude, longitude }}
      radius={75}
      fillColor="rgba(99, 102, 241, 0.15)"
      strokeColor="rgba(99, 102, 241, 0.6)"
      strokeWidth={1.5}
    />
  );
});
