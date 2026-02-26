/**
 * TypeScript interfaces mirroring all backend API response shapes.
 *
 * These types are derived directly from the backend Pydantic schemas in:
 * - backend/app/schemas/place.py
 * - backend/app/schemas/visit.py
 * - backend/app/schemas/auth.py
 * - backend/app/schemas/user.py
 * - backend/app/schemas/utility.py
 */

// ---------------------------------------------------------------------------
// Place Schemas
// ---------------------------------------------------------------------------

/** Place summary for list results (e.g., nearby search). */
export interface PlaceResponse {
  id: number;
  name: string;
  category: string;
  lat: number;
  lon: number;
  address: string | null;
  current_busyness: number | null;
  busyness_stale: boolean;
  busyness_updated_at: string | null;
}

/** Full place detail including busyness data. */
export interface PlaceDetailResponse {
  id: number;
  name: string;
  category: string;
  lat: number;
  lon: number;
  address: string | null;
  city: string | null;
  country: string | null;
  busyness_data: BusynessData | null;
  busyness_updated_at: string | null;
  busyness_stale: boolean;
}

/**
 * Busyness data shape stored in the place's JSONB busyness_data column.
 *
 * popular_times: Array of objects, one per day (day 0=Monday .. 6=Sunday).
 *   Each entry has an `hours` array of 24 integer values (0-100).
 * current_popularity: Live busyness 0-100, present only when live data is available.
 * time_spent: Typical visit duration as [min_minutes, max_minutes].
 */
export interface BusynessData {
  popular_times: Array<{ day: number; hours: number[] }>;
  current_popularity?: number;
  time_spent?: [number, number];
}

/** Busyness forecast for a specific day and hour. */
export interface ForecastResponse {
  place_id: number;
  day: number;
  hour: number;
  predicted_busyness: number;
  data_stale: boolean;
}

// ---------------------------------------------------------------------------
// Visit Schemas
// ---------------------------------------------------------------------------

/** Info about a nearby place detected in a GPS ping. */
export interface NearbyPlaceInfo {
  place_id: number;
  name: string;
  distance_m: number;
}

/** Info about a visit confirmed by a GPS ping. */
export interface ConfirmedVisitInfo {
  visit_id: number;
  place_id: number;
  duration_seconds: number;
}

/** Response to a GPS ping. */
export interface GPSPingResponse {
  nearby_places: NearbyPlaceInfo[];
  confirmed_visits: ConfirmedVisitInfo[];
  rejected: boolean;
  rejection_reason: string | null;
}

/** Confirmed visit detail for visit history. */
export interface VisitResponse {
  id: number;
  place_id: number;
  place_name: string;
  area_id: number | null;
  started_at: string;
  ended_at: string | null;
  duration_seconds: number | null;
}

// ---------------------------------------------------------------------------
// Auth Schemas
// ---------------------------------------------------------------------------

/** JWT token pair response returned after login, registration, or refresh. */
export interface AuthTokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

// ---------------------------------------------------------------------------
// User Schemas
// ---------------------------------------------------------------------------

/** User profile response. */
export interface UserResponse {
  id: number;
  username: string;
  email: string;
  xp: number;
  level: number;
  created_at: string;
}

// ---------------------------------------------------------------------------
// Utility Schemas
// ---------------------------------------------------------------------------

/** Aggregate visit statistics for the current user. */
export interface UserStatsResponse {
  places_count: number;
  cities_count: number;
  countries_count: number;
  total_duration_seconds: number;
}

/** Single achievement with current progress. */
export interface AchievementResponse {
  id: string;
  name: string;
  description: string;
  category: string;
  progress: number;
  threshold: number;
  earned: boolean;
  earned_at: string | null;
}

/** Journal entry combining visit data with optional user note. */
export interface JournalEntryResponse {
  visit_id: number;
  place_id: number;
  place_name: string;
  area_id: number | null;
  city: string | null;
  started_at: string;
  duration_seconds: number | null;
  note: string | null;
  photo_url: string | null;
}

/** Single area with visited status for the exploration heatmap. */
export interface HeatmapAreaResponse {
  id: number;
  name: string;
  city: string;
  boundary_geojson: unknown;
  visited: boolean;
  visited_at: string | null;
}

/** Full heatmap response with area list and exploration metrics. */
export interface HeatmapResponse {
  areas: HeatmapAreaResponse[];
  total_areas: number;
  visited_areas: number;
  explored_pct: number;
}

/** Single neighborhood stamp in a city passport. */
export interface PassportStampResponse {
  area_id: number;
  name: string;
  visited: boolean;
  visited_at: string | null;
}

/** City passport with neighborhood stamps and completion status. */
export interface CityPassportResponse {
  city: string;
  total_neighborhoods: number;
  visited_count: number;
  stamps: PassportStampResponse[];
  badge_earned: boolean;
  explored_pct: number;
}
