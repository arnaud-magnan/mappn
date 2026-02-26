/**
 * GPS tracking lifecycle hook for the game app.
 *
 * Manages the full location tracking lifecycle:
 * 1. Requests foreground location permission on mount
 * 2. Starts watchPositionAsync with 15-second interval updates
 * 3. Updates the locationStore with each new position
 * 4. Submits GPS pings to the backend for visit detection
 * 5. Invalidates TanStack Query caches when visits are confirmed
 * 6. Queues pings when offline and flushes on reconnection
 * 7. Stops/resumes tracking based on AppState (foreground-only)
 * 8. Cleans up all subscriptions on unmount
 *
 * Returns the current permission status, low accuracy flag, and any error
 * for UI display.
 */

import { useEffect, useState, useCallback, useRef } from 'react';
import { AppState, AppStateStatus } from 'react-native';
import * as Location from 'expo-location';
import NetInfo from '@react-native-community/netinfo';
import { useQueryClient } from '@tanstack/react-query';

import { useLocationStore } from '../stores/locationStore';
import { startTracking, stopTracking } from '../services/locationService';
import { postGpsPing } from '../services/visitsService';
import { GPS_ACCURACY_THRESHOLD_M } from '../constants/config';

/** Queued GPS ping payload for offline submission. */
interface QueuedPing {
  lat: number;
  lon: number;
  accuracy: number;
  timestamp: string;
}

/** Query keys that must be invalidated when new visits are confirmed. */
const VISIT_QUERY_KEYS = [
  'gameProfile',
  'inventory',
  'creatures',
  'territories',
] as const;

export interface LocationTrackingState {
  /** Whether location permission has been granted. */
  permissionGranted: boolean;
  /** Whether permission status has been determined. */
  permissionChecked: boolean;
  /** Whether GPS accuracy is worse than the configured threshold. */
  lowAccuracy: boolean;
  /** Error message if tracking fails. */
  error: string | null;
}

/**
 * Hook that manages GPS location tracking lifecycle for the game app.
 *
 * On mount: requests foreground permission, then starts tracking.
 * On each location update: sends a GPS ping to the backend, checks for
 * confirmed visits, and invalidates game caches as needed.
 * On background: stops tracking. On foreground: resumes tracking.
 * On unmount: stops tracking and cleans up all subscriptions.
 *
 * @returns Permission status, low accuracy flag, and error info for the UI.
 */
export const useLocationTracking = (): LocationTrackingState => {
  const [permissionGranted, setPermissionGranted] = useState(false);
  const [permissionChecked, setPermissionChecked] = useState(false);
  const [lowAccuracy, setLowAccuracy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const setLocation = useLocationStore((state) => state.setLocation);
  const setTracking = useLocationStore((state) => state.setTracking);
  const setClaimingState = useLocationStore((state) => state.setClaimingState);
  const isMounted = useRef(true);
  const queryClient = useQueryClient();

  // In-memory offline queue for GPS pings
  const pingQueueRef = useRef<QueuedPing[]>([]);
  // Track whether a queue flush is in progress to avoid concurrent flushes
  const isFlushingRef = useRef(false);
  // Track whether permission was granted (for AppState resume logic)
  const permissionGrantedRef = useRef(false);

  /**
   * Sync claimingState with the latest GPS ping response.
   * Called after every successful ping — online or flushed from queue.
   */
  const syncClaiming = useCallback(
    (
      nearbyPlaces: Array<{ place_id: number; name: string }>,
      hasConfirmed: boolean
    ) => {
      if (hasConfirmed || nearbyPlaces.length === 0) {
        setClaimingState(null);
        return;
      }
      const place = nearbyPlaces[0];
      const current = useLocationStore.getState().claimingState;
      // Preserve startedAt if this is the same place (don't reset progress)
      if (current === null || current.placeId !== place.place_id) {
        setClaimingState({
          placeId: place.place_id,
          placeName: place.name,
          startedAt: Date.now(),
        });
      }
    },
    [setClaimingState]
  );

  /**
   * Flush all queued GPS pings sequentially.
   *
   * Sends each queued ping one at a time. If a ping fails (e.g., network
   * drops again), the remaining queue is preserved for the next flush.
   */
  const flushQueue = useCallback(async () => {
    if (isFlushingRef.current) return;
    if (pingQueueRef.current.length === 0) return;

    isFlushingRef.current = true;

    while (pingQueueRef.current.length > 0) {
      const ping = pingQueueRef.current[0];
      try {
        const response = await postGpsPing(
          ping.lat,
          ping.lon,
          ping.accuracy,
          ping.timestamp
        );

        // Remove successfully sent ping from queue
        pingQueueRef.current.shift();

        syncClaiming(
          response.nearby_places ?? [],
          (response.confirmed_visits?.length ?? 0) > 0
        );

        // Invalidate caches if new visits were confirmed
        if (
          response.confirmed_visits &&
          response.confirmed_visits.length > 0
        ) {
          for (const key of VISIT_QUERY_KEYS) {
            queryClient.invalidateQueries({ queryKey: [key] });
          }
        }
      } catch {
        // Network still unavailable or other error - stop flushing,
        // remaining pings stay in the queue for later
        break;
      }
    }

    isFlushingRef.current = false;
  }, [queryClient, syncClaiming]);

  /**
   * Submit a GPS ping to the backend, handling offline scenarios.
   *
   * Checks network connectivity first. If offline, queues the ping.
   * If online, sends the ping and checks the response for confirmed visits.
   */
  const submitGpsPing = useCallback(
    async (lat: number, lon: number, accuracy: number) => {
      const timestamp = new Date().toISOString();
      const pingPayload: QueuedPing = { lat, lon, accuracy, timestamp };

      // Check network connectivity
      const netState = await NetInfo.fetch();
      const isConnected = netState.isConnected ?? false;

      if (!isConnected) {
        // Queue the ping for later submission
        pingQueueRef.current.push(pingPayload);
        return;
      }

      // Flush any previously queued pings first
      if (pingQueueRef.current.length > 0) {
        await flushQueue();
      }

      try {
        const response = await postGpsPing(lat, lon, accuracy, timestamp);

        syncClaiming(
          response.nearby_places ?? [],
          (response.confirmed_visits?.length ?? 0) > 0
        );

        // Invalidate caches if new visits were confirmed
        if (
          response.confirmed_visits &&
          response.confirmed_visits.length > 0
        ) {
          for (const key of VISIT_QUERY_KEYS) {
            queryClient.invalidateQueries({ queryKey: [key] });
          }
        }
      } catch {
        // If the ping fails (e.g., transient network issue), queue it
        pingQueueRef.current.push(pingPayload);
      }
    },
    [queryClient, flushQueue, syncClaiming]
  );

  const handleLocationUpdate = useCallback(
    (location: Location.LocationObject) => {
      if (!isMounted.current) return;

      const { latitude, longitude, accuracy } = location.coords;
      setLocation(latitude, longitude, accuracy);

      // Detect low GPS accuracy
      const isLowAccuracy =
        accuracy !== null && accuracy > GPS_ACCURACY_THRESHOLD_M;
      setLowAccuracy(isLowAccuracy);

      // Submit GPS ping to backend (ping goes through regardless of accuracy)
      submitGpsPing(latitude, longitude, accuracy ?? 0);
    },
    [setLocation, submitGpsPing]
  );

  // Main setup effect: permission request, tracking start, and cleanup
  useEffect(() => {
    isMounted.current = true;

    const setup = async () => {
      try {
        // Request foreground location permission
        const { status } =
          await Location.requestForegroundPermissionsAsync();
        const granted = status === 'granted';

        if (!isMounted.current) return;

        setPermissionGranted(granted);
        setPermissionChecked(true);
        permissionGrantedRef.current = granted;

        if (!granted) {
          setError('Location permission denied');
          return;
        }

        // Start GPS tracking
        await startTracking(handleLocationUpdate);

        if (isMounted.current) {
          setTracking(true);
        }
      } catch (err) {
        if (!isMounted.current) return;

        const message =
          err instanceof Error ? err.message : 'Location tracking failed';
        setError(message);
        setPermissionChecked(true);
      }
    };

    setup();

    return () => {
      isMounted.current = false;
      stopTracking();
      setTracking(false);
    };
  }, [handleLocationUpdate, setTracking]);

  // AppState listener: stop tracking on background, resume on active
  useEffect(() => {
    const handleAppStateChange = async (nextAppState: AppStateStatus) => {
      if (!isMounted.current) return;
      if (!permissionGrantedRef.current) return;

      if (nextAppState === 'active') {
        // Resume GPS tracking when app returns to foreground
        try {
          await startTracking(handleLocationUpdate);
          if (isMounted.current) {
            setTracking(true);
          }
          // Attempt to flush any queued pings
          flushQueue();
        } catch {
          // Tracking resume failed - error will surface on next update
        }
      } else if (nextAppState === 'background' || nextAppState === 'inactive') {
        // Stop GPS tracking when app goes to background or inactive
        stopTracking();
        if (isMounted.current) {
          setTracking(false);
        }
      }
    };

    const subscription = AppState.addEventListener(
      'change',
      handleAppStateChange
    );

    return () => {
      subscription.remove();
    };
  }, [handleLocationUpdate, setTracking, flushQueue]);

  // NetInfo listener: flush queued pings when connectivity is restored
  useEffect(() => {
    const unsubscribe = NetInfo.addEventListener((state) => {
      if (state.isConnected && pingQueueRef.current.length > 0) {
        flushQueue();
      }
    });

    return unsubscribe;
  }, [flushQueue]);

  return {
    permissionGranted,
    permissionChecked,
    lowAccuracy,
    error,
  };
};
