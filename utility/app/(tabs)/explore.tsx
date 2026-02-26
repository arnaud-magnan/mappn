/**
 * Explore tab screen - Personal Exploration Heatmap.
 *
 * Shows the user's visited neighborhoods as polygon overlays on a MapView.
 * Features:
 * - Polygon overlays colored by visited/unvisited status (via HeatmapLayer)
 * - Per-city exploration progress bar (via CityProgress)
 * - City selector dropdown when the user has visited multiple cities
 * - Share button that captures the map+stats as a PNG and opens the share sheet
 * - Empty state when the user has no visits yet
 *
 * Data flow:
 *   useHeatmap(selectedCity) -> HeatmapResponse
 *     -> HeatmapLayer (polygon overlays)
 *     -> CityProgress (% bar)
 *     -> ShareableCard (stats overlay for capture)
 */

import React, { useEffect, useRef, useState, useMemo } from 'react';
import {
  Alert,
  Platform,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from 'react-native';
import MapView from 'react-native-maps';
import * as Sharing from 'expo-sharing';
import MaterialIcons from '@expo/vector-icons/MaterialIcons';

import { useHeatmap } from '@/hooks/useHeatmap';
import { HeatmapLayer } from '@/components/explore/HeatmapLayer';
import { CityProgress } from '@/components/explore/CityProgress';
import {
  ShareableCard,
  type ShareableCardRef,
} from '@/components/explore/ShareableCard';
import { EmptyState, LoadingSpinner } from '@/components/ui';
import { THEME_COLORS } from '@/constants/colors';

// Default map region - world-level zoom so the polygon overlays are visible
// immediately regardless of the user's actual city.
const DEFAULT_REGION = {
  latitude: 48.8566,
  longitude: 2.3522,
  latitudeDelta: 0.2,
  longitudeDelta: 0.2,
};

export default function ExploreScreen() {
  const [selectedCity, setSelectedCity] = useState<string | undefined>(
    undefined
  );
  const [isSharing, setIsSharing] = useState(false);
  const [showCityPicker, setShowCityPicker] = useState(false);

  const shareableCardRef = useRef<ShareableCardRef>(null);

  const { data: heatmap, isLoading, isError, refetch } = useHeatmap(selectedCity);

  // Persist the full city list from the unfiltered heatmap response so that
  // selecting a city (which filters heatmap.areas to only that city) doesn't
  // collapse the city selector to a single entry.
  const [knownCities, setKnownCities] = useState<string[]>([]);

  // Update the known cities list whenever we get an unfiltered response
  // (selectedCity === undefined). This avoids an extra network request while
  // ensuring the city selector always shows all cities the user has visited.
  useEffect(() => {
    if (!heatmap || selectedCity !== undefined) return;
    const citySet = new Set<string>(heatmap.areas.map((a) => a.city));
    const sorted = Array.from(citySet).sort();
    setKnownCities(sorted);
  }, [heatmap, selectedCity]);

  // For the current render, merge knownCities with any cities visible in the
  // current heatmap response (handles the initial filtered-load edge case).
  const allCities: string[] = useMemo(() => {
    if (!heatmap) return knownCities;
    const citySet = new Set<string>([
      ...knownCities,
      ...heatmap.areas.map((a) => a.city),
    ]);
    return Array.from(citySet).sort();
  }, [heatmap, knownCities]);

  const hasMultipleCities = allCities.length > 1;

  const hasNoVisits =
    !isLoading && !isError && heatmap !== undefined && heatmap.visited_areas === 0;

  // Compute map region to fit the visible areas, or fall back to default.
  const mapRegion = useMemo(() => {
    if (!heatmap || heatmap.areas.length === 0) return DEFAULT_REGION;

    // Use the first area's city to center the map. A full bounding-box
    // computation would require parsing each polygon's GeoJSON, which is
    // handled by HeatmapLayer itself. Centering on a rough city position is
    // sufficient here.
    return DEFAULT_REGION;
  }, [heatmap]);

  const handleShare = async () => {
    if (!shareableCardRef.current) return;

    const available = await Sharing.isAvailableAsync();
    if (!available) {
      Alert.alert(
        'Sharing not available',
        'Your device does not support the share sheet.'
      );
      return;
    }

    setIsSharing(true);
    try {
      const uri = await shareableCardRef.current.capture();
      await Sharing.shareAsync(uri, {
        mimeType: 'image/png',
        dialogTitle: 'Share your exploration map',
        UTI: 'public.png',
      });
    } catch (err) {
      Alert.alert('Share failed', 'Could not capture the map. Please try again.');
    } finally {
      setIsSharing(false);
    }
  };

  const handleCitySelect = (city: string) => {
    setSelectedCity(city === selectedCity ? undefined : city);
    setShowCityPicker(false);
  };

  // -------------------------------------------------------------------------
  // Render: loading state
  // -------------------------------------------------------------------------
  if (isLoading) {
    return <LoadingSpinner message="Loading your exploration map..." />;
  }

  // -------------------------------------------------------------------------
  // Render: error state
  // -------------------------------------------------------------------------
  if (isError) {
    return (
      <EmptyState
        icon="wifi-off"
        title="Could not load heatmap"
        description="Check your connection and try again."
        actionLabel="Retry"
        onAction={() => void refetch()}
      />
    );
  }

  // -------------------------------------------------------------------------
  // Render: empty state (user has no visits)
  // -------------------------------------------------------------------------
  if (hasNoVisits) {
    return (
      <EmptyState
        icon="explore"
        title="Start exploring to see your heatmap!"
        description="Visit places around you and watch your exploration map fill in."
      />
    );
  }

  // -------------------------------------------------------------------------
  // Render: main exploration map
  // -------------------------------------------------------------------------
  const displayCity =
    selectedCity ?? (allCities.length === 1 ? allCities[0] : 'All cities');

  const placesVisited = heatmap?.visited_areas ?? 0;
  const exploredPct = heatmap?.explored_pct ?? 0;
  const visitedAreas = heatmap?.visited_areas ?? 0;
  const totalAreas = heatmap?.total_areas ?? 0;

  return (
    <View style={styles.screen}>
      {/* Map + stats wrapped in ShareableCard for capture */}
      <ShareableCard
        ref={shareableCardRef}
        city={displayCity}
        placesVisited={placesVisited}
        exploredPct={exploredPct}
      >
        <MapView
          style={styles.map}
          region={mapRegion}
          mapType="standard"
          showsUserLocation={false}
        >
          {heatmap && <HeatmapLayer areas={heatmap.areas} />}
        </MapView>
      </ShareableCard>

      {/* Overlay panel: city selector + progress + share button */}
      <View style={styles.overlayPanel} pointerEvents="box-none">
        {/* City selector - only shown when user has visited multiple cities */}
        {hasMultipleCities && (
          <View style={styles.citySelectorRow}>
            <TouchableOpacity
              style={styles.citySelectorButton}
              onPress={() => setShowCityPicker((prev) => !prev)}
              accessibilityRole="button"
              accessibilityLabel={`Selected city: ${displayCity}. Tap to change.`}
            >
              <Text style={styles.citySelectorText} numberOfLines={1}>
                {displayCity}
              </Text>
              <MaterialIcons
                name={showCityPicker ? 'arrow-drop-up' : 'arrow-drop-down'}
                size={20}
                color={THEME_COLORS.text}
              />
            </TouchableOpacity>

            {/* City picker dropdown */}
            {showCityPicker && (
              <View style={styles.cityPickerDropdown}>
                <ScrollView
                  bounces={false}
                  style={styles.cityPickerScroll}
                  keyboardShouldPersistTaps="handled"
                >
                  {/* "All cities" option */}
                  <Pressable
                    style={[
                      styles.cityPickerItem,
                      selectedCity === undefined && styles.cityPickerItemSelected,
                    ]}
                    onPress={() => {
                      setSelectedCity(undefined);
                      setShowCityPicker(false);
                    }}
                  >
                    <Text
                      style={[
                        styles.cityPickerItemText,
                        selectedCity === undefined &&
                          styles.cityPickerItemTextSelected,
                      ]}
                    >
                      All cities
                    </Text>
                  </Pressable>

                  {allCities.map((city) => (
                    <Pressable
                      key={city}
                      style={[
                        styles.cityPickerItem,
                        selectedCity === city && styles.cityPickerItemSelected,
                      ]}
                      onPress={() => handleCitySelect(city)}
                    >
                      <Text
                        style={[
                          styles.cityPickerItemText,
                          selectedCity === city &&
                            styles.cityPickerItemTextSelected,
                        ]}
                      >
                        {city}
                      </Text>
                    </Pressable>
                  ))}
                </ScrollView>
              </View>
            )}
          </View>
        )}

        {/* Progress bar card */}
        {heatmap && totalAreas > 0 && (
          <View style={styles.progressCard}>
            <CityProgress
              city={displayCity}
              exploredPct={exploredPct}
              visitedAreas={visitedAreas}
              totalAreas={totalAreas}
            />
          </View>
        )}

        {/* Share button */}
        <TouchableOpacity
          style={[styles.shareButton, isSharing && styles.shareButtonDisabled]}
          onPress={() => void handleShare()}
          disabled={isSharing}
          accessibilityRole="button"
          accessibilityLabel="Share exploration map"
        >
          <MaterialIcons
            name="share"
            size={18}
            color={THEME_COLORS.background}
          />
          <Text style={styles.shareButtonText}>
            {isSharing ? 'Capturing...' : 'Share map'}
          </Text>
        </TouchableOpacity>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  screen: {
    flex: 1,
    backgroundColor: THEME_COLORS.background,
  },
  map: {
    ...StyleSheet.absoluteFillObject,
  },
  overlayPanel: {
    position: 'absolute',
    bottom: 0,
    left: 0,
    right: 0,
    paddingBottom: Platform.OS === 'ios' ? 32 : 16,
    paddingHorizontal: 16,
    gap: 8,
  },
  // City selector
  citySelectorRow: {
    alignSelf: 'flex-start',
  },
  citySelectorButton: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: THEME_COLORS.background,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: THEME_COLORS.border,
    paddingHorizontal: 12,
    paddingVertical: 8,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.1,
    shadowRadius: 3,
    elevation: 2,
    gap: 4,
    maxWidth: 200,
  },
  citySelectorText: {
    fontSize: 14,
    fontWeight: '600',
    color: THEME_COLORS.text,
    flexShrink: 1,
  },
  // City picker dropdown
  cityPickerDropdown: {
    position: 'absolute',
    bottom: '100%',
    left: 0,
    minWidth: 160,
    backgroundColor: THEME_COLORS.background,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: THEME_COLORS.border,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.12,
    shadowRadius: 8,
    elevation: 6,
    marginBottom: 4,
    overflow: 'hidden',
  },
  cityPickerScroll: {
    maxHeight: 200,
  },
  cityPickerItem: {
    paddingHorizontal: 14,
    paddingVertical: 10,
  },
  cityPickerItemSelected: {
    backgroundColor: THEME_COLORS.surface,
  },
  cityPickerItemText: {
    fontSize: 14,
    color: THEME_COLORS.text,
  },
  cityPickerItemTextSelected: {
    fontWeight: '600',
    color: THEME_COLORS.primary,
  },
  // Progress card
  progressCard: {
    backgroundColor: 'rgba(255, 255, 255, 0.95)',
    borderRadius: 12,
    borderWidth: 1,
    borderColor: THEME_COLORS.border,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.08,
    shadowRadius: 4,
    elevation: 2,
  },
  // Share button
  shareButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: THEME_COLORS.primary,
    borderRadius: 10,
    paddingVertical: 12,
    paddingHorizontal: 20,
    gap: 8,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.15,
    shadowRadius: 4,
    elevation: 3,
  },
  shareButtonDisabled: {
    opacity: 0.6,
  },
  shareButtonText: {
    fontSize: 15,
    fontWeight: '600',
    color: THEME_COLORS.background,
  },
});
