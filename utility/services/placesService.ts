/**
 * Places service API client functions.
 *
 * Provides typed API calls for nearby places, place detail, and
 * busyness forecast endpoints. All functions use the shared Axios
 * instance from api.ts which handles auth token injection and
 * 401 refresh logic.
 */

import { api } from './api';
import {
  PlaceResponse,
  PlaceDetailResponse,
  ForecastResponse,
} from '../types/api';

/**
 * Get nearby places based on geographic coordinates.
 * Endpoint: GET /places/nearby
 *
 * @param lat - Latitude in decimal degrees.
 * @param lon - Longitude in decimal degrees.
 * @param radius - Search radius in meters.
 * @param category - Optional category filter (e.g., "restaurant", "park").
 * @returns Array of nearby place summaries.
 */
export const getNearbyPlaces = async (
  lat: number,
  lon: number,
  radius: number,
  category?: string
): Promise<PlaceResponse[]> => {
  const params: Record<string, unknown> = { lat, lon, radius };
  if (category) {
    params.category = category;
  }

  const { data } = await api.get<PlaceResponse[]>('/places/nearby', {
    params,
  });
  return data;
};

/**
 * Get full detail for a single place.
 * Endpoint: GET /places/{id}
 *
 * @param id - The place ID.
 * @returns Full place detail including busyness data.
 */
export const getPlaceDetail = async (
  id: number
): Promise<PlaceDetailResponse> => {
  const { data } = await api.get<PlaceDetailResponse>(`/places/${id}`);
  return data;
};

/**
 * Get busyness forecast for a place at a specific day and hour.
 * Endpoint: GET /places/{id}/forecast
 *
 * @param id - The place ID.
 * @param day - Day of the week (0=Monday .. 6=Sunday).
 * @param hour - Hour of the day (0-23).
 * @returns Forecast response with predicted busyness.
 */
export const getForecast = async (
  id: number,
  day: number,
  hour: number
): Promise<ForecastResponse> => {
  const { data } = await api.get<ForecastResponse>(
    `/places/${id}/forecast`,
    {
      params: { day, hour },
    }
  );
  return data;
};
