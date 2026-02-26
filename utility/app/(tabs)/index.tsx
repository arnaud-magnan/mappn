/**
 * Map View screen - the home tab of the Mappn utility app.
 *
 * Displays a full-screen map with busyness-colored place pins, marker
 * clustering for performance, category filter pills, GPS location
 * tracking, and a bottom sheet summary when a pin is tapped.
 *
 * If location permission is denied, the map centers on a default
 * location (Paris, 48.8566, 2.3522) and displays a guidance message.
 */

import React, { useCallback, useRef, useState, useMemo } from 'react';
import { StyleSheet, Text, View } from 'react-native';
import ClusteredMapView from 'react-native-map-clustering';
import { PROVIDER_DEFAULT, Region } from 'react-native-maps';

import { THEME_COLORS } from '@/constants/colors';
import { PlaceResponse } from '@/types/api';
import { useLocationStore } from '@/stores/locationStore';
import { useMapStore } from '@/stores/mapStore';
import { useNearbyPlaces } from '@/hooks/useNearbyPlaces';
import { useLocationTracking } from '@/hooks/useLocationTracking';
import { PlacePin } from '@/components/map/PlacePin';
import { CategoryFilter } from '@/components/map/CategoryFilter';
import {
  PlaceSummarySheet,
  PlaceSummarySheetRef,
} from '@/components/map/PlaceSummarySheet';
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
const SEARCH_RADIUS = 3000;

export default function MapScreen() {
  const sheetRef = useRef<PlaceSummarySheetRef>(null);

  // Location tracking
  const { permissionGranted, permissionChecked } = useLocationTracking();
  const userLat = useLocationStore((state) => state.latitude);
  const userLon = useLocationStore((state) => state.longitude);

  // Map state
  const region = useMapStore((state) => state.region);
  const setRegion = useMapStore((state) => state.setRegion);

  // Category filter state
  const [selectedCategory, setSelectedCategory] = useState('');

  // Selected place for bottom sheet
  const [selectedPlace, setSelectedPlace] = useState<PlaceResponse | null>(
    null
  );

  // Compute map center based on user location or default
  const mapCenter = useMemo(
    () => ({
      latitude: userLat ?? DEFAULT_LOCATION.latitude,
      longitude: userLon ?? DEFAULT_LOCATION.longitude,
    }),
    [userLat, userLon]
  );

  // Fetch nearby places
  const { data: places, isLoading, isError, refetch } = useNearbyPlaces({
    lat: region.latitude,
    lon: region.longitude,
    radius: SEARCH_RADIUS,
    category: selectedCategory || undefined,
  });

  // Filter places by category if needed (client-side backup filter)
  const filteredPlaces = useMemo(() => {
    if (!places) return [];
    if (!selectedCategory) return places;
    return places.filter(
      (p) => p.category.toLowerCase() === selectedCategory.toLowerCase()
    );
  }, [places, selectedCategory]);

  const handlePinPress = useCallback(
    (place: PlaceResponse) => {
      setSelectedPlace(place);
      sheetRef.current?.expand();
    },
    []
  );

  const handleSheetDismiss = useCallback(() => {
    setSelectedPlace(null);
  }, []);

  const handleRegionChange = useCallback(
    (newRegion: Region) => {
      setRegion(newRegion);
    },
    [setRegion]
  );

  const handleCategorySelect = useCallback((category: string) => {
    setSelectedCategory(category);
  }, []);

  // Show loading while permission is being checked
  if (!permissionChecked) {
    return <LoadingSpinner message="Checking location permission..." />;
  }

  return (
    <View style={styles.container}>
      {/* Full-screen clustered map */}
      <ClusteredMapView
        style={StyleSheet.absoluteFillObject}
        provider={PROVIDER_DEFAULT}
        initialRegion={{
          ...mapCenter,
          ...DEFAULT_DELTA,
        }}
        showsUserLocation={permissionGranted}
        showsMyLocationButton={permissionGranted}
        onRegionChangeComplete={handleRegionChange}
        clusterColor={THEME_COLORS.primary}
        spiralEnabled={false}
        animationEnabled={false}>
        {filteredPlaces.map((place) => (
          <PlacePin
            key={place.id}
            place={place}
            onPress={handlePinPress}
          />
        ))}
      </ClusteredMapView>

      {/* Category filter overlay */}
      <CategoryFilter
        selectedCategory={selectedCategory}
        onSelectCategory={handleCategorySelect}
      />

      {/* Permission denied guidance banner */}
      {!permissionGranted && (
        <View style={styles.permissionBanner}>
          <Text style={styles.permissionText}>
            Location permission denied. Please enable location access in your
            device settings to see your position on the map and enable visit
            tracking.
          </Text>
        </View>
      )}

      {/* Loading indicator for places */}
      {isLoading && (
        <View style={styles.loadingOverlay}>
          <LoadingSpinner message="Loading places..." size="small" />
        </View>
      )}

      {/* Error banner for failed places API */}
      {isError && (
        <View style={styles.errorBanner}>
          <Text style={styles.errorText}>
            Could not load places. Check your connection.
          </Text>
          <Text
            style={styles.errorRetry}
            onPress={() => void refetch()}
            accessibilityRole="button">
            Tap to retry
          </Text>
        </View>
      )}

      {/* Place summary bottom sheet */}
      <PlaceSummarySheet
        ref={sheetRef}
        place={selectedPlace}
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
    backgroundColor: THEME_COLORS.warning,
    borderRadius: 8,
    padding: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.15,
    shadowRadius: 4,
    elevation: 4,
  },
  permissionText: {
    fontSize: 13,
    color: THEME_COLORS.text,
    lineHeight: 18,
  },
  loadingOverlay: {
    position: 'absolute',
    top: 120,
    alignSelf: 'center',
    backgroundColor: THEME_COLORS.background,
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
    top: 120,
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
    color: THEME_COLORS.primary,
    fontWeight: '600',
    marginTop: 4,
  },
});
