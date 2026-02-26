/**
 * Location tracking service.
 *
 * Provides startTracking() and stopTracking() functions that use
 * expo-location's watchPositionAsync to receive GPS position updates
 * at a defined interval. The subscription reference is stored in module
 * scope so it can be cleanly removed when tracking stops.
 */

import * as Location from 'expo-location';

import { GPS_INTERVAL_MS } from '../constants/config';

/** Module-scoped reference to the active location subscription. */
let locationSubscription: Location.LocationSubscription | null = null;

/**
 * Start GPS location tracking using watchPositionAsync.
 *
 * Subscribes to position updates with a distanceInterval derived from
 * the GPS_INTERVAL_MS config (15 seconds = ~15m at walking speed).
 * The callback receives each new position for the caller to process.
 *
 * @param callback - Function called with each new GPS position.
 * @returns The location subscription for manual management if needed.
 */
export const startTracking = async (
  callback: (location: Location.LocationObject) => void
): Promise<Location.LocationSubscription> => {
  // Remove any existing subscription before starting a new one
  if (locationSubscription) {
    locationSubscription.remove();
    locationSubscription = null;
  }

  locationSubscription = await Location.watchPositionAsync(
    {
      accuracy: Location.Accuracy.High,
      distanceInterval: 15, // meters - roughly 15s at walking speed
      timeInterval: GPS_INTERVAL_MS,
    },
    callback
  );

  return locationSubscription;
};

/**
 * Stop GPS location tracking.
 *
 * Removes the active location subscription if one exists.
 */
export const stopTracking = (): void => {
  if (locationSubscription) {
    locationSubscription.remove();
    locationSubscription = null;
  }
};
