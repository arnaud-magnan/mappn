/**
 * Utility service API client functions.
 *
 * Provides typed API calls for user stats, achievements, journal,
 * heatmap, and city passport endpoints. All functions use the shared
 * Axios instance from api.ts which handles auth token injection and
 * 401 refresh logic.
 */

import { api } from './api';
import {
  UserStatsResponse,
  AchievementResponse,
  JournalEntryResponse,
  HeatmapResponse,
  CityPassportResponse,
} from '../types/api';

/**
 * Get aggregate visit statistics for the current user.
 * Endpoint: GET /users/me/stats
 */
export const getUserStats = async (): Promise<UserStatsResponse> => {
  const { data } = await api.get<UserStatsResponse>('/users/me/stats');
  return data;
};

/**
 * Get all achievements with current progress for the current user.
 * Endpoint: GET /users/me/achievements
 */
export const getAchievements = async (): Promise<AchievementResponse[]> => {
  const { data } = await api.get<AchievementResponse[]>(
    '/users/me/achievements'
  );
  return data;
};

/**
 * Get paginated journal entries for the current user.
 * Endpoint: GET /journal?limit=<limit>&offset=<offset>
 *
 * @param limit - Maximum number of entries to return.
 * @param offset - Number of entries to skip for pagination.
 */
export const getJournal = async (
  limit: number = 20,
  offset: number = 0
): Promise<JournalEntryResponse[]> => {
  const { data } = await api.get<JournalEntryResponse[]>('/journal', {
    params: { limit, offset },
  });
  return data;
};

/**
 * Add or update a note on a journal entry.
 * Endpoint: POST /journal/{visitId}/note
 *
 * @param visitId - The visit ID to attach the note to.
 * @param text - Note text content (max 1000 characters).
 * @param photoUrl - Optional URL/path to a photo.
 */
export const addJournalNote = async (
  visitId: number,
  text: string,
  photoUrl?: string
): Promise<JournalEntryResponse> => {
  const { data } = await api.post<JournalEntryResponse>(
    `/journal/${visitId}/note`,
    {
      text,
      photo_url: photoUrl ?? null,
    }
  );
  return data;
};

/**
 * Get the exploration heatmap for the current user.
 * Endpoint: GET /explore/heatmap?city=<city>
 *
 * @param city - Optional city filter. If omitted, returns all areas.
 */
export const getHeatmap = async (
  city?: string
): Promise<HeatmapResponse> => {
  const { data } = await api.get<HeatmapResponse>('/explore/heatmap', {
    params: city ? { city } : undefined,
  });
  return data;
};

/**
 * Get the city passport with neighborhood stamps.
 * Endpoint: GET /passports?city=<city>
 *
 * @param city - City name to get passport for.
 */
export const getCityPassport = async (
  city: string
): Promise<CityPassportResponse> => {
  const { data } = await api.get<CityPassportResponse>('/passports', {
    params: { city },
  });
  return data;
};
