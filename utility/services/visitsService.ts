/**
 * Visits service API client functions.
 *
 * Provides typed API calls for GPS ping submission and visit history
 * retrieval. All functions use the shared Axios instance from api.ts
 * which handles auth token injection and 401 refresh logic.
 */

import { api } from './api';
import { GPSPingResponse, VisitResponse } from '../types/api';

/**
 * Submit a GPS coordinate ping for visit detection.
 * Endpoint: POST /visits/ping
 *
 * The backend uses these pings to detect when a user is dwelling
 * at a place (>= 5 minutes within geofence) and creates a visit record.
 *
 * @param lat - Latitude in decimal degrees.
 * @param lon - Longitude in decimal degrees.
 * @param accuracy - GPS accuracy in meters.
 * @param timestamp - ISO 8601 timestamp of the position reading.
 * @returns Ping response with nearby places and any confirmed visits.
 */
export const postGpsPing = async (
  lat: number,
  lon: number,
  accuracy: number,
  timestamp: string
): Promise<GPSPingResponse> => {
  const { data } = await api.post<GPSPingResponse>('/visits/ping', {
    lat,
    lon,
    accuracy,
    timestamp,
  });
  return data;
};

/**
 * Get paginated visit history for the current user.
 * Endpoint: GET /visits/history
 *
 * @param limit - Maximum number of visits to return. Defaults to 20.
 * @param offset - Number of visits to skip for pagination. Defaults to 0.
 * @returns Array of confirmed visit records.
 */
export const getVisitHistory = async (
  limit: number = 20,
  offset: number = 0
): Promise<VisitResponse[]> => {
  const { data } = await api.get<VisitResponse[]>('/visits/history', {
    params: { limit, offset },
  });
  return data;
};
