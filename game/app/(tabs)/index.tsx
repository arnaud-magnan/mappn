/**
 * Game Map screen - the home tab of the Mappn game app.
 *
 * Displays a full-screen map with territory polygon overlays color-coded
 * by ownership and zone type, creature icons on claimed territories,
 * event markers with countdown timers, loot indicators near eligible
 * places, and a bottom sheet for territory details on tap.
 *
 * If location permission is denied, the map centers on a default
 * location (Paris, 48.8566, 2.3522) and displays a guidance message.
 *
 * Performance optimizations:
 * - Viewport-based territory filtering via useMemo (only render visible polygons)
 * - tracksViewChanges={false} on all static markers
 * - Territory data refreshes every 30s via TanStack Query polling
 * - GPS tracking via useLocationTracking
 */

import React, { useCallback, useRef, useState, useMemo } from 'react';
import { StyleSheet, Text, View } from 'react-native';
import MapView, { PROVIDER_DEFAULT, Region } from 'react-native-maps';
import MaterialIcons from '@expo/vector-icons/MaterialIcons';
import { useRouter } from 'expo-router';

import { GAME_COLORS } from '@/constants/colors';
import { TerritoryResponse, EventResponse } from '@/types/api';
import { useLocationStore } from '@/stores/locationStore';
import { useMapStore } from '@/stores/mapStore';
import { useAuthStore } from '@/stores/authStore';
import { useGameStore } from '@/stores/gameStore';
import { useNearbyTerritories } from '@/hooks/useNearbyTerritories';
import { useNearbyEvents } from '@/hooks/useNearbyEvents';
import { useLocationTracking } from '@/hooks/useLocationTracking';
import { TerritoryOverlay } from '@/components/map/TerritoryOverlay';
import { EventMarker } from '@/components/map/EventMarker';
import { CreatureMarker } from '@/components/map/CreatureMarker';
import { LootIndicator } from '@/components/map/LootIndicator';
import { GeofenceCircle } from '@/components/map/GeofenceCircle';
import { ClaimingProgressHUD } from '@/components/map/ClaimingProgressHUD';
import {
  TerritoryInfoSheet,
  TerritoryInfoSheetRef,
} from '@/components/map/TerritoryInfoSheet';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';

/** Default map center: Paris, France. */
const DEFAULT_LOCATION = {
  latitude: 48.8566,
  longitude: 2.3522,
};

/** Default map zoom level. */
const DEFAULT_DELTA = {
  latitudeDelta: 0.05,
  longitudeDelta: 0.05,
};

/** Default search radius in meters. */
const SEARCH_RADIUS = 5000;

/**
 * Check if a territory's center point is within the visible map region.
 *
 * Used for viewport-based filtering to limit rendered polygons to those
 * within the visible map bounds, improving performance on dense maps.
 */
const isInViewport = (
  territory: TerritoryResponse,
  region: Region
): boolean => {
  if (
    territory.center_lat === null ||
    territory.center_lon === null
  ) {
    // If no center point, include it (fallback to rendering)
    return true;
  }

  const latMin = region.latitude - region.latitudeDelta / 2;
  const latMax = region.latitude + region.latitudeDelta / 2;
  const lonMin = region.longitude - region.longitudeDelta / 2;
  const lonMax = region.longitude + region.longitudeDelta / 2;

  return (
    territory.center_lat >= latMin &&
    territory.center_lat <= latMax &&
    territory.center_lon >= lonMin &&
    territory.center_lon <= lonMax
  );
};

export default function MapScreen() {
  const router = useRouter();
  const sheetRef = useRef<TerritoryInfoSheetRef>(null);

  // Auth state (for determining territory ownership colors)
  const currentUserId = useAuthStore((state) => state.user?.id ?? null);

  // Location tracking
  const { permissionGranted, permissionChecked } = useLocationTracking();
  const userLat = useLocationStore((state) => state.latitude);
  const userLon = useLocationStore((state) => state.longitude);
  const claimingState = useLocationStore((state) => state.claimingState);

  // Map state
  const region = useMapStore((state) => state.region);
  const setRegion = useMapStore((state) => state.setRegion);

  // Game state
  const setSelectedTerritory = useGameStore(
    (state) => state.setSelectedTerritory
  );

  // Selected territory for bottom sheet
  const [selectedTerritory, setSelectedTerritoryLocal] =
    useState<TerritoryResponse | null>(null);

  // Compute map center based on user location or default
  const mapCenter = useMemo(
    () => ({
      latitude: userLat ?? DEFAULT_LOCATION.latitude,
      longitude: userLon ?? DEFAULT_LOCATION.longitude,
    }),
    [userLat, userLon]
  );

  // Fetch nearby territories with 30s polling via TanStack Query
  const {
    data: territories,
    isLoading: isLoadingTerritories,
    isError: isTerritoriesError,
    refetch: refetchTerritories,
  } = useNearbyTerritories({
    lat: region.latitude,
    lon: region.longitude,
    radius: SEARCH_RADIUS,
  });

  // Fetch nearby events
  const {
    data: events,
    isLoading: isLoadingEvents,
  } = useNearbyEvents({
    lat: region.latitude,
    lon: region.longitude,
    radius: SEARCH_RADIUS * 2,
  });

  // Viewport-based territory filtering (performance optimization)
  const visibleTerritories = useMemo(() => {
    if (!territories) return [];
    return territories.filter((t) => isInViewport(t, region));
  }, [territories, region]);

  // Filter territories owned by the current user (for creature markers)
  const ownedTerritories = useMemo(() => {
    if (!territories || currentUserId === null) return [];
    return territories.filter(
      (t) =>
        t.owner_id === currentUserId &&
        t.chief_creature_id !== null &&
        t.center_lat !== null &&
        t.center_lon !== null
    );
  }, [territories, currentUserId]);

  // Loot indicators: territories with nearby places where player can earn rewards
  // For now, show loot indicators on unclaimed territories near the player
  const lootTerritories = useMemo(() => {
    if (!territories || userLat === null || userLon === null) return [];
    return territories.filter((t) => {
      if (t.center_lat === null || t.center_lon === null) return false;
      // Show loot indicator for nearby unclaimed territories
      const dlat = t.center_lat - userLat;
      const dlon = t.center_lon - userLon;
      const approxDistKm = Math.sqrt(dlat * dlat + dlon * dlon) * 111;
      return approxDistKm < 0.5 && t.owner_id === null;
    });
  }, [territories, userLat, userLon]);

  const handleTerritoryPress = useCallback(
    (territory: TerritoryResponse) => {
      setSelectedTerritoryLocal(territory);
      setSelectedTerritory(territory.id);
      sheetRef.current?.expand();
    },
    [setSelectedTerritory]
  );

  const handleSheetDismiss = useCallback(() => {
    setSelectedTerritoryLocal(null);
    setSelectedTerritory(null);
  }, [setSelectedTerritory]);

  const handleRegionChange = useCallback(
    (newRegion: Region) => {
      setRegion(newRegion);
    },
    [setRegion]
  );

  const handleEventPress = useCallback(
    (event: EventResponse) => {
      router.push(`/event/${event.id}`);
    },
    [router]
  );

  // Show loading while permission is being checked
  if (!permissionChecked) {
    return <LoadingSpinner message="Checking location permission..." />;
  }

  const isLoading = isLoadingTerritories || isLoadingEvents;

  return (
    <View style={styles.container}>
      {/* Full-screen map */}
      <MapView
        style={StyleSheet.absoluteFillObject}
        provider={PROVIDER_DEFAULT}
        initialRegion={{
          ...mapCenter,
          ...DEFAULT_DELTA,
        }}
        showsUserLocation={permissionGranted}
        showsMyLocationButton={permissionGranted}
        onRegionChangeComplete={handleRegionChange}>
        {/* Territory polygon overlays */}
        <TerritoryOverlay
          territories={visibleTerritories}
          currentUserId={currentUserId}
          onPress={handleTerritoryPress}
        />

        {/* Event markers with countdown timers */}
        {events?.map((event) => (
          <EventMarker
            key={event.id}
            event={event}
            onPress={handleEventPress}
          />
        ))}

        {/* Creature icons on player's claimed territories */}
        {ownedTerritories.map((territory) => (
          <CreatureMarker
            key={`creature-${territory.id}`}
            territory={territory}
            onPress={handleTerritoryPress}
          />
        ))}

        {/* Loot indicators near eligible places */}
        {lootTerritories.map((territory) => (
          <LootIndicator
            key={`loot-${territory.id}`}
            latitude={territory.center_lat!}
            longitude={territory.center_lon!}
            placeName={territory.area_name ?? undefined}
          />
        ))}

        {/* Geofence circle: shows 75m boundary while actively claiming a territory.
            Note: centered on player position (place lat/lon not in ping response).
            TODO: add lat/lon to NearbyPlaceInfo to center on the actual place. */}
        {claimingState !== null && userLat !== null && userLon !== null && (
          <GeofenceCircle latitude={userLat} longitude={userLon} />
        )}
      </MapView>

      {/* Claiming progress HUD: shown while player is inside a place geofence */}
      {claimingState !== null && (
        <ClaimingProgressHUD
          placeName={claimingState.placeName}
          startedAt={claimingState.startedAt}
        />
      )}

      {/* Permission denied guidance banner - map remains viewable but game actions disabled */}
      {!permissionGranted && permissionChecked && (
        <View style={styles.permissionBanner}>
          <MaterialIcons
            name="location-off"
            size={20}
            color={GAME_COLORS.text}
            style={styles.permissionIcon}
          />
          <Text style={styles.permissionText}>
            Location permission denied. Please enable location access in
            your device settings to see your position on the map and
            enable game actions.
          </Text>
          <Text style={styles.permissionSubtext}>
            Game actions disabled: claim territory, challenge, and check-in
            buttons require location permission. The map remains viewable.
          </Text>
        </View>
      )}

      {/* Loading indicator for territories */}
      {isLoading && (
        <View style={styles.loadingOverlay}>
          <LoadingSpinner message="Loading map data..." size="small" />
        </View>
      )}

      {/* Error banner for failed territory API */}
      {isTerritoriesError && (
        <View style={styles.errorBanner}>
          <Text style={styles.errorText}>
            Could not load territories. Check your connection.
          </Text>
          <Text
            style={styles.errorRetry}
            onPress={() => void refetchTerritories()}
            accessibilityRole="button">
            Tap to retry
          </Text>
        </View>
      )}

      {/* Territory detail bottom sheet */}
      <TerritoryInfoSheet
        ref={sheetRef}
        territory={selectedTerritory}
        onDismiss={handleSheetDismiss}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  permissionBanner: {
    position: 'absolute',
    bottom: 100,
    left: 16,
    right: 16,
    backgroundColor: GAME_COLORS.warning,
    borderRadius: 8,
    padding: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.15,
    shadowRadius: 4,
    elevation: 4,
  },
  permissionIcon: {
    marginBottom: 8,
  },
  permissionText: {
    fontSize: 13,
    color: GAME_COLORS.text,
    lineHeight: 18,
  },
  permissionSubtext: {
    fontSize: 11,
    color: GAME_COLORS.textSecondary,
    lineHeight: 16,
    marginTop: 6,
    fontStyle: 'italic',
  },
  loadingOverlay: {
    position: 'absolute',
    top: 200,  // was 120 — moved down to clear ClaimingProgressHUD (~80px tall)
    alignSelf: 'center',
    backgroundColor: GAME_COLORS.background,
    borderRadius: 8,
    padding: 8,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  errorBanner: {
    position: 'absolute',
    top: 200,  // was 120 — moved down to clear ClaimingProgressHUD (~80px tall)
    left: 16,
    right: 16,
    backgroundColor: '#fef2f2',
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#fecaca',
    padding: 12,
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  errorText: {
    fontSize: 13,
    color: '#991b1b',
    textAlign: 'center',
  },
  errorRetry: {
    fontSize: 13,
    color: GAME_COLORS.primary,
    fontWeight: '600',
    marginTop: 4,
  },
});
