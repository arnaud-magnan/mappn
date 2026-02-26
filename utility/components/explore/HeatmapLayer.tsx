/**
 * HeatmapLayer renders neighborhood polygon overlays on the MapView.
 *
 * Each area from the heatmap response is drawn as a Polygon component.
 * Visited areas are filled with a semi-transparent green (#22c55e at 0.3
 * opacity). Unvisited areas are shown as a grey outline (#9ca3af) with no
 * fill.
 *
 * The boundary_geojson field from the API is expected to be a GeoJSON
 * Polygon or MultiPolygon Feature/FeatureCollection. Coordinates in GeoJSON
 * are [longitude, latitude] pairs (opposite to react-native-maps LatLng
 * which uses { latitude, longitude }).
 */

import React from 'react';
import { Polygon } from 'react-native-maps';
import type { LatLng } from 'react-native-maps';

import { HeatmapAreaResponse } from '@/types/api';
import { BUSYNESS_COLORS } from '@/constants/colors';

// react-native-maps fillColor requires an rgba or hex string with alpha.
// We express the visited fill as rgba for cross-platform support.
const VISITED_FILL_COLOR = 'rgba(34, 197, 94, 0.3)'; // #22c55e at 30% opacity
const VISITED_STROKE_COLOR = BUSYNESS_COLORS.quiet; // #22c55e
const UNVISITED_STROKE_COLOR = BUSYNESS_COLORS.noData; // #9ca3af
const UNVISITED_FILL_COLOR = 'rgba(0, 0, 0, 0)'; // transparent

interface GeoJSONPosition {
  0: number; // longitude
  1: number; // latitude
}

/**
 * Parse a GeoJSON boundary_geojson value into one or more arrays of LatLng
 * coordinates suitable for react-native-maps Polygon.
 *
 * Supports:
 * - GeoJSON Polygon geometry: { type: "Polygon", coordinates: [...] }
 * - GeoJSON Feature with Polygon geometry
 * - GeoJSON FeatureCollection (uses the first feature's geometry)
 * - GeoJSON MultiPolygon geometry (returns multiple coordinate arrays)
 *
 * Returns an array of LatLng arrays. Each inner array represents one polygon
 * ring to be rendered.
 */
function parseBoundaryGeoJSON(boundary: unknown): LatLng[][] {
  if (!boundary || typeof boundary !== 'object') {
    return [];
  }

  const geo = boundary as Record<string, unknown>;

  // Helper to convert GeoJSON coordinate ring to LatLng array
  const ringToLatLng = (ring: GeoJSONPosition[]): LatLng[] =>
    ring.map((pos) => ({
      latitude: pos[1],
      longitude: pos[0],
    }));

  let geometry: Record<string, unknown> | null = null;

  if (geo.type === 'FeatureCollection') {
    const features = geo.features as Array<Record<string, unknown>>;
    if (!features || features.length === 0) return [];
    geometry = features[0].geometry as Record<string, unknown>;
  } else if (geo.type === 'Feature') {
    geometry = geo.geometry as Record<string, unknown>;
  } else if (geo.type === 'Polygon' || geo.type === 'MultiPolygon') {
    geometry = geo;
  }

  if (!geometry) return [];

  if (geometry.type === 'Polygon') {
    // coordinates: [outerRing, ...holeRings]
    // We render the outer ring only; holes can be handled via the `holes`
    // prop if needed in future.
    const coords = geometry.coordinates as GeoJSONPosition[][];
    if (!coords || coords.length === 0) return [];
    return [ringToLatLng(coords[0])];
  }

  if (geometry.type === 'MultiPolygon') {
    // coordinates: [[[outerRing, ...holeRings], ...], ...]
    const polys = geometry.coordinates as GeoJSONPosition[][][];
    return polys
      .filter((poly) => poly.length > 0 && poly[0].length > 0)
      .map((poly) => ringToLatLng(poly[0]));
  }

  return [];
}

export interface HeatmapLayerProps {
  /** Areas from the heatmap API response. */
  areas: HeatmapAreaResponse[];
}

/**
 * Renders polygon overlays on the parent MapView for each heatmap area.
 *
 * Must be rendered as a direct child of MapView so that react-native-maps
 * can correctly position the overlays in the map's coordinate space.
 */
export function HeatmapLayer({ areas }: HeatmapLayerProps) {
  return (
    <>
      {areas.map((area) => {
        const polygonRings = parseBoundaryGeoJSON(area.boundary_geojson);

        return polygonRings.map((coordinates, ringIndex) => {
          if (coordinates.length < 3) {
            // A polygon needs at least 3 points to be valid
            return null;
          }

          return (
            <Polygon
              key={`${area.id}-ring-${ringIndex}`}
              coordinates={coordinates}
              fillColor={
                area.visited ? VISITED_FILL_COLOR : UNVISITED_FILL_COLOR
              }
              strokeColor={
                area.visited ? VISITED_STROKE_COLOR : UNVISITED_STROKE_COLOR
              }
              strokeWidth={area.visited ? 2 : 1}
            />
          );
        });
      })}
    </>
  );
}
