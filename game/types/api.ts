/**
 * TypeScript interfaces mirroring all backend API response shapes.
 *
 * These types are derived directly from the backend Pydantic schemas in:
 * - backend/app/schemas/game.py
 * - backend/app/schemas/territory.py
 * - backend/app/schemas/event.py
 * - backend/app/schemas/social.py
 * - backend/app/schemas/auth.py
 * - backend/app/schemas/user.py
 */

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

// ---------------------------------------------------------------------------
// Game Profile Schemas (backend/app/schemas/game.py)
// ---------------------------------------------------------------------------

/** Player game stats overview. */
export interface GameProfileResponse {
  user_id: number;
  username: string;
  xp: number;
  level: number;
  creature_count: number;
  territory_count: number;
}

// ---------------------------------------------------------------------------
// Creature Schemas (backend/app/schemas/game.py)
// ---------------------------------------------------------------------------

/** Single creature with full details. */
export interface CreatureResponse {
  id: number;
  user_id: number;
  template_id: number;
  name: string;
  rarity: string;
  level: number;
  xp: number;
  power: number;
  defense: number;
  stamina: number;
  evolution_stage: number;
  assigned_territory_id: number | null;
  created_at: string;
}

/** Paginated list of player creatures. */
export interface CreatureListResponse {
  creatures: CreatureResponse[];
  total: number;
}

// ---------------------------------------------------------------------------
// Item Schemas (backend/app/schemas/game.py)
// ---------------------------------------------------------------------------

/** Single item with stat boosts. */
export interface ItemResponse {
  id: number;
  user_id: number;
  template_id: number;
  name: string;
  rarity: string;
  power_boost: number;
  defense_boost: number;
  stamina_boost: number;
  equipped_creature_id: number | null;
  created_at: string;
}

// ---------------------------------------------------------------------------
// Inventory Schemas (backend/app/schemas/game.py)
// ---------------------------------------------------------------------------

/** Component type with quantity held by the player. */
export interface ComponentInventory {
  type: string;
  quantity: number;
}

/** Loot box state (unopened or opened). */
export interface LootBoxResponse {
  id: number;
  user_id: number;
  source: string;
  rarity: string | null;
  is_opened: boolean;
  contents_type: string | null;
  contents_id: number | null;
  created_at: string;
  opened_at: string | null;
}

/** Result of opening a loot box. */
export interface LootBoxOpenResult {
  loot_box_id: number;
  contents_type: string;
  rarity: string;
  creature: CreatureResponse | null;
  item: ItemResponse | null;
}

/** Full inventory: components, items, and loot boxes. */
export interface InventoryResponse {
  components: ComponentInventory[];
  items: ItemResponse[];
  loot_boxes: LootBoxResponse[];
}

// ---------------------------------------------------------------------------
// Territory Schemas (backend/app/schemas/territory.py)
// ---------------------------------------------------------------------------

/** Coordinate pair for polygon boundary points. */
export interface LatLng {
  latitude: number;
  longitude: number;
}

/** Single territory with zone type, owner, and familiarity data. */
export interface TerritoryResponse {
  id: number;
  area_id: number;
  /** Human-readable area name for display in territory info sheets. */
  area_name: string | null;
  owner_id: number | null;
  owner_username: string | null;
  chief_creature_id: number | null;
  /** Display name of the chief creature (nullable if no chief assigned). */
  chief_creature_name: string | null;
  zone_type: string | null;
  familiarity_scores: Record<string, unknown> | null;
  familiar_score_for_user: number | null;
  passive_reward_rate: number;
  familiarity_rankings: Array<Record<string, unknown>> | null;
  /** Polygon boundary coordinates for map overlay rendering. */
  boundary_coordinates: LatLng[] | null;
  /** Center latitude of the territory area (for marker positioning). */
  center_lat: number | null;
  /** Center longitude of the territory area (for marker positioning). */
  center_lon: number | null;
  /** Whether the territory owner is a friend of the requesting user. */
  is_friend: boolean;
  /** Whether the current user has a prior visit to the territory's area. */
  has_visited?: boolean;
}

/** List of territories with total count. */
export interface TerritoryListResponse {
  territories: TerritoryResponse[];
  total: number;
}

/** Result of a PvP territory challenge. */
export interface ChallengeResult {
  winner: string;
  attacker_power: number;
  defender_power: number;
  breakdown: Record<string, unknown>;
}

/** A resident of a personal zone territory. */
export interface ResidentResponse {
  user_id: number;
  username: string;
  home_claimed_at: string | null;
}

// ---------------------------------------------------------------------------
// Event Schemas (backend/app/schemas/event.py)
// ---------------------------------------------------------------------------

/** Single game event with location, timing, and rewards. */
export interface EventResponse {
  id: number;
  name: string;
  tier: string;
  description: string | null;
  lat: number | null;
  lon: number | null;
  radius: number;
  city: string | null;
  starts_at: string;
  ends_at: string;
  rewards: Record<string, unknown>;
  quest_steps: Record<string, unknown> | null;
  created_at: string;
  is_active: boolean;
  time_remaining_seconds: number;
}

/** List of events with total count. */
export interface EventListResponse {
  events: EventResponse[];
  total: number;
}

/** Multi-step quest progress tracking. */
export interface QuestProgress {
  steps_completed: number;
  total_steps: number;
  current_step_description: string;
}

/** Result of an event check-in. */
export interface EventCheckInResult {
  success: boolean;
  rewards_granted: Record<string, unknown> | null;
  quest_progress: QuestProgress | null;
}

// ---------------------------------------------------------------------------
// Social Schemas (backend/app/schemas/social.py)
// ---------------------------------------------------------------------------

/** Single friendship record. */
export interface FriendResponse {
  id: number;
  user_id: number;
  friend_id: number;
  username: string;
  status: string;
  territory_count: number;
  creature_count: number;
  created_at: string;
}

/** List of friends with total count. */
export interface FriendListResponse {
  friends: FriendResponse[];
  total: number;
}

/** Single trade proposal with offered and requested items. */
export interface TradeResponse {
  id: number;
  sender_id: number;
  sender_username: string;
  receiver_id: number;
  offered_creature_ids: number[];
  offered_item_ids: number[];
  requested_creature_ids: number[];
  requested_item_ids: number[];
  status: string;
  created_at: string;
  resolved_at: string | null;
}

/** List of trades with total count. */
export interface TradeListResponse {
  trades: TradeResponse[];
  total: number;
}

/** Single leaderboard ranking entry. */
export interface LeaderboardEntryResponse {
  rank: number;
  user_id: number;
  username: string | null;
  value: number;
  is_me: boolean;
}

/** Full leaderboard with entries, scope, and metric. */
export interface LeaderboardResponse {
  entries: LeaderboardEntryResponse[];
  scope: string;
  metric: string;
  total: number;
}

/** Activity feed entry from social service. */
export interface ActivityFeedEntry {
  type: string;
  user_id: number;
  username: string;
  description: string;
  timestamp: string;
  [key: string]: unknown;
}
