---
title: Codebase Impact Analysis - Implement Mappn game app with creatures, territories, and events
task_file: .specs/tasks/draft/implement-game-app.feature.md
scratchpad: .specs/scratchpad/d769fb6d.md
created: 2026-02-26
status: complete
---

# Codebase Impact Analysis: Implement Mappn game app with creatures, territories, and events

## Summary

- **Files to Modify**: 4 backend files
- **Files to Create**: ~30 backend files + ~60 game app files
- **Files to Delete**: 0 files
- **Test Files Affected**: 4 new backend test files
- **Risk Level**: High (complex game mechanics, PvP resolution, PostGIS territorial queries, Celery passive reward ticking, new Expo project with real-time concerns)

---

## Context: What Already Exists

The shared backend at `/Users/arnaudmagnan/development/mappn/backend/` and the utility app at `/Users/arnaudmagnan/development/mappn/utility/` are fully built. The game app is a new parallel Expo project.

**Existing backend endpoints the game app consumes directly (no changes needed):**

| Endpoint | Method | Used By |
|----------|--------|---------|
| `/auth/register` | POST | Game app auth flow |
| `/auth/login` | POST | Game app auth flow |
| `/auth/refresh` | POST | Token refresh |
| `/auth/me` | GET | Game profile screen |
| `/places/nearby` | GET | Game map screen (event/territory proximity) |
| `/visits/ping` | POST | Background GPS visit tracking (same visit system) |
| `/visits/history` | GET | (reference for reward history display) |

**Existing backend models confirmed via `/Users/arnaudmagnan/development/mappn/backend/app/models/__init__.py`:**
- User, Place, Area, Visit, JournalNote - ALL exist
- Creature, CreatureTemplate, Item, ItemTemplate, Component, LootBox, Territory, Event, EventParticipation, Friend, Trade, LeaderboardEntry - NONE exist (must be created)

**Existing alembic migrations:**
- `001_initial_schema.py` - base schema
- `002_utility_schema.py` - journal_notes table
- Next migration must be: `003_game_schema.py`

---

## Files to be Modified/Created

### Backend Modifications (existing files)

```
backend/
├── app/
│   ├── main.py                                   # UPDATE: add game, territory, event, social routers
│   ├── models/
│   │   └── __init__.py                           # UPDATE: add all game model imports + __all__ entries
│   └── services/
│       └── visit_service.py                      # UPDATE: auto_confirm_visit() must call
│                                                 #   game_service.dispatch_visit_rewards() after commit
└── alembic/
    └── versions/
        └── 003_game_schema.py                    # NEW: all game tables migration
```

**Critical modification - `backend/app/services/visit_service.py:256-289`**:
After `await db.commit()` in `auto_confirm_visit()`, add:
```python
from app.services.game_service import dispatch_visit_rewards
await dispatch_visit_rewards(db=db, user_id=user_id, place_id=place_id, visit_id=visit.id)
```

### Backend New Files

```
backend/
├── app/
│   ├── models/
│   │   ├── creature.py                           # NEW: Creature + CreatureTemplate ORM models
│   │   ├── item.py                               # NEW: Item + ItemTemplate + Component + LootBox ORM models
│   │   ├── territory.py                          # NEW: Territory ORM model
│   │   ├── event.py                              # NEW: Event + EventParticipation ORM models
│   │   └── social.py                            # NEW: Friend + Trade + LeaderboardEntry ORM models
│   ├── schemas/
│   │   ├── game.py                               # NEW: Game profile, creature, inventory schemas
│   │   ├── territory.py                          # NEW: Territory request/response schemas
│   │   ├── event.py                              # NEW: Event request/response schemas
│   │   └── social.py                            # NEW: Friend, trade, leaderboard schemas
│   ├── api/
│   │   ├── game.py                               # NEW: /game/me, /game/creatures, /game/inventory routes
│   │   ├── territories.py                        # NEW: /game/territories routes
│   │   ├── events.py                             # NEW: /game/events routes
│   │   └── social_game.py                       # NEW: /game/social routes
│   └── services/
│       ├── game_service.py                       # NEW: dispatch_visit_rewards(), open_loot_box(),
│       │                                         #   evolve_creature(), craft_item()
│       ├── territory_service.py                  # NEW: claim_territory(), challenge_territory(),
│       │                                         #   contribute_to_territory(), get_nearby_territories()
│       ├── event_service.py                      # NEW: get_nearby_events(), check_in_event(),
│       │                                         #   compute_event_loot_box_bonus()
│       └── social_service.py                    # NEW: friends CRUD, trade lifecycle, leaderboard
```

### Backend Worker Addition

```
backend/
└── app/
    └── workers/
        └── tasks/
            └── passive_rewards.py               # NEW: Celery periodic task - hourly territory reward tick
```

### Game App (new Expo project)

```
game/
├── app.json                                     # NEW: Expo config, permissions, bundle ID
├── package.json                                 # NEW: Dependencies (same stack as utility)
├── tsconfig.json                                # NEW: TypeScript config
├── eas.json                                     # NEW: EAS Build config
├── expo-env.d.ts                                # NEW: Expo env types
│
├── app/                                         # Expo Router file-based routing
│   ├── _layout.tsx                              # NEW: Root layout - auth gate, QueryClient, providers
│   ├── (auth)/
│   │   ├── _layout.tsx                          # NEW: Auth stack layout
│   │   ├── login.tsx                            # NEW: Login screen
│   │   └── register.tsx                         # NEW: Register screen
│   └── (tabs)/
│       ├── _layout.tsx                          # NEW: Bottom tab bar (Map|Creatures|Inventory|Events|Profile)
│       ├── index.tsx                            # NEW: Game Map tab - territory overlays, event markers
│       ├── creatures.tsx                        # NEW: Creature Collection tab - grid, filters
│       ├── inventory.tsx                        # NEW: Inventory tab - components, items, loot boxes, crafting
│       ├── events.tsx                           # NEW: Events tab - active/upcoming event list
│       └── profile.tsx                          # NEW: Profile tab - XP, level, stats, social link
│
├── app/creature/                                # Stack screens (push navigation)
│   └── [id].tsx                                 # NEW: Creature Detail - stats, items, evolution, territory
├── app/territory/
│   └── [id].tsx                                 # NEW: Territory Detail - owner, familiarity, challenge
├── app/event/
│   └── [id].tsx                                 # NEW: Event Detail - quest steps, rewards, check-in
└── app/social/
    ├── index.tsx                                # NEW: Social hub - friends, activity feed
    ├── friends.tsx                              # NEW: Friends list + add friend
    ├── trades.tsx                               # NEW: Trade list + create trade
    └── leaderboard.tsx                          # NEW: Leaderboard (local/global/friends)
│
├── components/
│   ├── map/
│   │   ├── TerritoryOverlay.tsx                 # NEW: Polygon overlays colored by zone type and ownership
│   │   ├── EventMarker.tsx                      # NEW: Glowing event pin with countdown timer
│   │   ├── LootIndicator.tsx                    # NEW: Animated loot drop indicator on map
│   │   └── TerritoryInfoSheet.tsx              # NEW: Bottom sheet on territory tap
│   ├── creature/
│   │   ├── CreatureCard.tsx                     # NEW: Grid card - rarity badge, level, mini-stats
│   │   ├── CreatureGrid.tsx                     # NEW: Paginated grid of creature cards
│   │   ├── RarityFilter.tsx                     # NEW: Filter pills: All/Common/Uncommon/Rare/Epic/Legendary
│   │   ├── StatBar.tsx                          # NEW: Power/Defense/Stamina bar visualization
│   │   ├── EvolutionProgress.tsx                # NEW: Progress toward next evolution threshold
│   │   └── ItemSlot.tsx                         # NEW: Equipment slot (empty or equipped item)
│   ├── inventory/
│   │   ├── ComponentList.tsx                    # NEW: Component counts by type
│   │   ├── ItemCard.tsx                         # NEW: Item card with rarity, stat boosts
│   │   ├── LootBoxCard.tsx                      # NEW: Unopened loot box with open button
│   │   ├── LootBoxOpenAnimation.tsx             # NEW: Reel/reveal animation for loot box opening
│   │   └── CraftingScreen.tsx                  # NEW: Recipe selector, component cost display, craft button
│   ├── territory/
│   │   ├── FamiliarityRanking.tsx               # NEW: Sorted list of users by familiarity score
│   │   ├── PassiveRateDisplay.tsx               # NEW: Hourly XP + component reward rate display
│   │   └── ChallengeButton.tsx                  # NEW: PvP challenge CTA with creature selector modal
│   ├── event/
│   │   ├── EventCard.tsx                        # NEW: Event summary card with tier badge, countdown
│   │   ├── QuestStepList.tsx                    # NEW: Multi-step quest progress visualization
│   │   └── CheckInButton.tsx                    # NEW: Physical presence check-in CTA
│   ├── social/
│   │   ├── FriendCard.tsx                       # NEW: Friend with territory/creature stats
│   │   ├── TradeCard.tsx                        # NEW: Trade offer with offered/requested items
│   │   ├── LeaderboardRow.tsx                   # NEW: Ranked leaderboard entry row
│   │   └── ActivityFeedItem.tsx                 # NEW: Social activity feed entry
│   └── ui/
│       ├── Button.tsx                           # NEW: Shared button
│       ├── Card.tsx                             # NEW: Shared card container
│       ├── LoadingSpinner.tsx                   # NEW: Loading indicator
│       ├── ErrorBoundary.tsx                    # NEW: Error boundary
│       ├── NetworkBanner.tsx                    # NEW: Offline banner
│       └── RarityBadge.tsx                     # NEW: Colored rarity badge (Common/Uncommon/Rare/Epic/Legendary)
│
├── services/
│   ├── api.ts                                   # NEW: Axios instance - auth token injection + 401 refresh
│   ├── authService.ts                           # NEW: login(), register(), refreshToken(), logout()
│   ├── gameService.ts                           # NEW: getGameProfile(), getCreatures(), getCreatureDetail(),
│   │                                            #   getInventory(), openLootBox(), craftItem(), evolveCreature()
│   ├── territoryService.ts                      # NEW: getNearbyTerritories(), getTerritoryDetail(),
│   │                                            #   claimTerritory(), challengeTerritory(), contributeToTerritory()
│   ├── eventService.ts                          # NEW: getNearbyEvents(), getEventDetail(), checkIn()
│   ├── socialService.ts                         # NEW: getFriends(), addFriend(), getTrades(), createTrade(),
│   │                                            #   respondToTrade(), getLeaderboard()
│   ├── visitsService.ts                         # NEW: postGpsPing() - same as utility
│   └── locationService.ts                       # NEW: startTracking(), stopTracking() - same as utility
│
├── stores/
│   ├── authStore.ts                             # NEW: Zustand - tokens, user, isAuthenticated (same as utility)
│   ├── locationStore.ts                         # NEW: Zustand - GPS coords, accuracy, isTracking
│   ├── gameStore.ts                             # NEW: Zustand - cached player xp/level, territory count
│   └── mapStore.ts                              # NEW: Zustand - map region state
│
├── hooks/
│   ├── useLocationTracking.ts                   # NEW: GPS tracking + visit ping (same as utility)
│   ├── useGameProfile.ts                        # NEW: TanStack Query - GET /game/me
│   ├── useCreatures.ts                          # NEW: TanStack Query infinite - GET /game/creatures
│   ├── useCreatureDetail.ts                     # NEW: TanStack Query - GET /game/creatures/{id}
│   ├── useInventory.ts                          # NEW: TanStack Query - GET /game/inventory
│   ├── useNearbyTerritories.ts                  # NEW: TanStack Query - GET /game/territories/nearby
│   ├── useTerritoryDetail.ts                    # NEW: TanStack Query - GET /game/territories/{id}
│   ├── useNearbyEvents.ts                       # NEW: TanStack Query - GET /game/events
│   ├── useEventDetail.ts                        # NEW: TanStack Query - GET /game/events/{id}
│   ├── useFriends.ts                            # NEW: TanStack Query - GET /game/social/friends
│   ├── useTrades.ts                             # NEW: TanStack Query - GET /game/social/trades
│   └── useLeaderboard.ts                        # NEW: TanStack Query - GET /game/leaderboards
│
├── constants/
│   ├── config.ts                                # NEW: API_BASE_URL, STALE_TIME, SECURE_STORE_KEYS, GPS constants
│   └── colors.ts                                # NEW: RARITY_COLORS, ZONE_TYPE_COLORS, TERRITORY_COLORS, THEME_COLORS
│
└── types/
    ├── api.ts                                   # NEW: TypeScript interfaces mirroring all backend game schemas
    └── navigation.ts                            # NEW: Expo Router typed navigation params
```

### Backend Test Files

```
backend/
└── tests/
    ├── test_game.py                             # NEW: /game/me, /game/creatures, /game/inventory endpoints
    ├── test_territories.py                      # NEW: claim, challenge, nearby territory endpoints
    ├── test_events.py                           # NEW: event listing, check-in endpoint
    └── test_social_game.py                     # NEW: friends, trades, leaderboard endpoints
```

---

## Useful Resources for Implementation

### Pattern References

```
backend/
├── app/
│   ├── api/
│   │   ├── utility.py              # Pattern: router without prefix, Depends injection, response_model
│   │   └── places.py               # Pattern: prefixed router, NearbyQueryParams = Depends(), spatial queries
│   ├── services/
│   │   ├── utility_service.py      # Pattern: complex JOIN queries, subqueries, result dict construction
│   │   └── visit_service.py:auto_confirm_visit()  # THE integration point for game reward dispatch
│   └── models/
│       ├── area.py                 # Pattern: Geography POLYGON with GeoAlchemy2
│       └── visit.py                # Pattern: nullable FK, DateTime fields, relationships
└── tests/
    ├── conftest.py                 # Pattern: async test DB session, test user fixture
    └── test_utility.py             # Pattern: test structure for protected GET/POST endpoints

utility/
├── services/
│   └── api.ts                     # Pattern: Axios + SecureStore + 401 refresh interceptor queue
├── stores/
│   └── authStore.ts               # Pattern: Zustand with SecureStore token persistence
├── hooks/
│   └── useLocationTracking.ts     # Pattern: GPS tracking hook to replicate for game app
└── app/
    ├── _layout.tsx                # Pattern: Root layout with auth gate + QueryClientProvider
    └── (tabs)/_layout.tsx         # Pattern: Bottom tab bar layout (copy and adapt)
```

---

## Key Interfaces and Contracts

### Backend Models to Create

| File | Model | Key Fields | PostGIS |
|------|-------|------------|---------|
| `backend/app/models/creature.py` | `Creature` | id, user_id, template_id, rarity, level, xp, power, defense, stamina, evolution_stage, assigned_territory_id (nullable FK territories.id) | No |
| `backend/app/models/creature.py` | `CreatureTemplate` | id, name, rarity, category_affinity, base_stats (jsonb), evolution_chain (jsonb), visual_asset_id | No |
| `backend/app/models/item.py` | `Item` | id, user_id, template_id, rarity, stat_boosts (jsonb), equipped_creature_id (nullable FK creatures.id) | No |
| `backend/app/models/item.py` | `ItemTemplate` | id, name, rarity, item_type, stat_boosts (jsonb), crafting_cost (jsonb: {component_type: qty}) | No |
| `backend/app/models/item.py` | `Component` | user_id (FK users.id), type (string), quantity (integer) | No |
| `backend/app/models/item.py` | `LootBox` | id, user_id (FK users.id), source_visit_id (FK visits.id), opened_at (nullable DateTime) | No |
| `backend/app/models/territory.py` | `Territory` | id, area_id (FK areas.id UNIQUE), owner_id (nullable FK users.id), chief_creature_id (nullable FK creatures.id), familiarity_scores (jsonb), passive_reward_rate (float) | No |
| `backend/app/models/event.py` | `Event` | id, tier (daily/weekly/monthly), location (Geography POINT 4326), radius (float meters), starts_at, ends_at, rewards (jsonb), quest_steps (jsonb nullable), city (nullable) | Geography POINT |
| `backend/app/models/event.py` | `EventParticipation` | id, event_id (FK events.id), user_id (FK users.id), checked_in_at, quest_progress (jsonb), completed (bool) | No |
| `backend/app/models/social.py` | `Friend` | user_id (FK users.id), friend_id (FK users.id), status (pending/accepted/blocked), created_at | No |
| `backend/app/models/social.py` | `Trade` | id, sender_id (FK users.id), receiver_id (FK users.id), offered_items (jsonb), requested_items (jsonb), status, created_at, completed_at (nullable) | No |
| `backend/app/models/social.py` | `LeaderboardEntry` | user_id (FK users.id), scope (local/global/friends), metric (territory_count/creature_power/exploration_pct), value (float), rank (int), city (nullable), refreshed_at | No |

### Backend Services to Create

| File | Function | Signature | Purpose |
|------|----------|-----------|---------|
| `backend/app/services/game_service.py` | `dispatch_visit_rewards` | `async fn(db: AsyncSession, user_id: int, place_id: int, visit_id: int) -> dict` | XP grant + 1-3 components by place category + 30% loot box roll |
| `backend/app/services/game_service.py` | `open_loot_box` | `async fn(db: AsyncSession, user_id: int, loot_box_id: int) -> dict` | Rarity roll (60/25/10/4/1%), create Creature or Item from template |
| `backend/app/services/game_service.py` | `evolve_creature` | `async fn(db: AsyncSession, user_id: int, creature_id: int) -> Creature` | Check level >= threshold (10/25/50), update template_id, recalculate stats |
| `backend/app/services/game_service.py` | `craft_item` | `async fn(db: AsyncSession, user_id: int, item_template_id: int) -> Item` | Validate component inventory, deduct components, create Item |
| `backend/app/services/territory_service.py` | `get_nearby_territories` | `async fn(db: AsyncSession, lat: float, lon: float, radius_m: int) -> list[dict]` | PostGIS ST_DWithin on Area.boundary, JOIN Territory |
| `backend/app/services/territory_service.py` | `claim_territory` | `async fn(db: AsyncSession, user_id: int, area_id: int, chief_creature_id: int) -> Territory` | Validate Visit.area_id exists, create/update Territory |
| `backend/app/services/territory_service.py` | `challenge_territory` | `async fn(db: AsyncSession, user_id: int, territory_id: int, attacker_creature_id: int) -> dict` | Compute effective power (stats + items + familiarity), determine winner, update Territory.owner_id |
| `backend/app/services/territory_service.py` | `compute_familiarity_bonus` | `fn(familiarity_score: float) -> float` | Multiplier on defender stats; scales with time spent in area |
| `backend/app/services/event_service.py` | `get_nearby_events` | `async fn(db: AsyncSession, lat: float, lon: float, radius_m: int) -> list[dict]` | PostGIS ST_DWithin on Event.location, filter by ends_at > now() |
| `backend/app/services/event_service.py` | `check_in_event` | `async fn(db: AsyncSession, user_id: int, event_id: int, lat: float, lon: float) -> dict` | Validate within event radius, create EventParticipation |
| `backend/app/services/social_service.py` | `create_trade` | `async fn(db: AsyncSession, sender_id: int, receiver_id: int, offered_item_ids: list[int], requested_item_ids: list[int]) -> Trade` | Validate 24h cooldown, validate item ownership, create Trade |
| `backend/app/services/social_service.py` | `respond_trade` | `async fn(db: AsyncSession, user_id: int, trade_id: int, accept: bool) -> Trade` | If accept: transfer item ownership, set completed_at |
| `backend/app/workers/tasks/passive_rewards.py` | `tick_passive_rewards` | `Celery task fn()` | For each Territory with owner+chief: compute XP rate = busyness_score * creature_power * 0.1, apply to user.xp and creature.xp |

### Backend Files to Modify

| File | Location | Change Required |
|------|----------|-----------------|
| `backend/app/services/visit_service.py` | `auto_confirm_visit():265-268` (after `await db.commit()`) | Add `await dispatch_visit_rewards(db, user_id, place_id, visit.id)` call |
| `backend/app/main.py` | After line 153 (`app.include_router(utility_router)`) | Add `app.include_router(game_router)`, `app.include_router(territory_router)`, etc. |
| `backend/app/models/__init__.py` | Lines 8-22 | Add imports: Creature, CreatureTemplate, Item, ItemTemplate, Component, LootBox, Territory, Event, EventParticipation, Friend, Trade, LeaderboardEntry |

### Frontend Types to Create (game/types/api.ts)

Key types mirroring backend game schemas:
- `GameProfileResponse`: `{user_id, username, xp, level, creature_count, territory_count}`
- `CreatureResponse`: `{id, template_id, name, rarity, level, xp, power, defense, stamina, evolution_stage, visual_asset_id, assigned_territory_id}`
- `ItemResponse`: `{id, template_id, name, rarity, item_type, stat_boosts, equipped_creature_id}`
- `ComponentInventory`: `{type: string, quantity: number}`
- `LootBoxResponse`: `{id, source_visit_id, opened_at: string | null}`
- `InventoryResponse`: `{components: ComponentInventory[], items: ItemResponse[], loot_boxes: LootBoxResponse[]}`
- `TerritoryResponse`: `{id, area_id, zone_type, owner_id, owner_username, chief_creature_id, familiar_score_for_user, passive_reward_rate, familiarity_rankings}`
- `EventResponse`: `{id, tier, lat, lon, radius, starts_at, ends_at, rewards, city, is_active, time_remaining_seconds}`
- `FriendResponse`: `{user_id, username, territory_count, creature_count, status}`
- `TradeResponse`: `{id, sender_id, sender_username, receiver_id, offered_items, requested_items, status, created_at}`
- `LeaderboardEntryResponse`: `{rank, user_id, username, value, is_me}`

### Frontend Constants (game/constants/colors.ts)

New color constants needed for game:
- `RARITY_COLORS`: `{common: '#9ca3af', uncommon: '#22c55e', rare: '#3b82f6', epic: '#a855f7', legendary: '#f59e0b'}`
- `ZONE_TYPE_COLORS`: `{personal: '#6366f1', cooperative: '#a855f7', pvp: '#ef4444'}`
- `TERRITORY_OVERLAY_COLORS`: `{mine: 'rgba(59,130,246,0.4)', friend: 'rgba(34,197,94,0.4)', pvp: 'rgba(239,68,68,0.4)', cooperative: 'rgba(168,85,247,0.4)', unclaimed: 'rgba(156,163,175,0.2)'}`

---

## Integration Points

### Critical Backend Integration

| File | Relationship | Impact | Action Needed |
|------|--------------|--------|---------------|
| `backend/app/services/visit_service.py:265` | `auto_confirm_visit()` must call `game_service.dispatch_visit_rewards()` | **Critical** | Add post-commit reward dispatch; circular import risk - use lazy import inside function |
| `backend/app/main.py:153` | Must include 4 new game routers | High | Add 4 `app.include_router()` calls after utility_router |
| `backend/app/models/__init__.py:14-22` | Must re-export all 12 game models for Alembic | Critical | Add all model imports; Alembic autodiscovery fails without this |
| `backend/alembic/versions/003_game_schema.py` | Must run after 002 (journal_notes table) | Critical | FK to visits, users, areas tables must exist before game tables |
| `backend/app/models/territory.py` | Territory.area_id FK -> areas.id | High | area_id must be UNIQUE (one territory per area) |
| `backend/app/workers/scheduler.py` | Add passive_rewards Celery beat schedule | Medium | Add hourly `tick_passive_rewards` to beat schedule |

### Frontend Integration (Game App)

| File | Relationship | Impact | Action Needed |
|------|--------------|--------|---------------|
| `game/services/api.ts` | All service files import from here | Critical | Same SecureStore + 401 refresh pattern as utility/services/api.ts |
| `game/stores/authStore.ts` | All services read token; auth gate in _layout.tsx | Critical | Same Zustand + SecureStore pattern as utility/stores/authStore.ts |
| `game/hooks/useLocationTracking.ts` | GPS pings feed visit confirmation, which triggers game rewards | High | Same pattern as utility/hooks/useLocationTracking.ts but invalidate game query keys on confirmed visit |
| `game/app/_layout.tsx` | Root layout must wrap in QueryClientProvider + auth gate | Critical | Same pattern as utility/app/_layout.tsx |
| `game/app/(tabs)/index.tsx` | Game Map uses territory polygon overlays + event markers on react-native-maps | High | TerritoryOverlay uses MapView `<Polygon>` component; EventMarker uses `<Marker>` |

---

## Similar Implementations

### Pattern 1: Utility backend API + service pattern (follow exactly)

- **Location**: `backend/app/api/utility.py` + `backend/app/services/utility_service.py`
- **Why relevant**: Shows exact pattern for new game API router + service layer. Router with Depends(get_db) + Depends(get_current_user), service function returning dict, schema with ConfigDict(from_attributes=True).
- **Key files**:
  - `backend/app/api/utility.py:38` - Router definition without prefix
  - `backend/app/services/utility_service.py:92-131` - `get_user_stats()` as pattern for complex JOIN queries

### Pattern 2: PostGIS spatial query (for territories and events)

- **Location**: `backend/app/services/places_service.py` + `backend/app/services/visit_service.py:241-253`
- **Why relevant**: `get_nearby_places()` uses ST_DWithin on Geography POINT; `auto_confirm_visit():241-253` uses ST_Contains on Geography POLYGON. Territory nearby query needs ST_DWithin on Area.boundary (POLYGON), same cast pattern.
- **Key files**:
  - `backend/app/services/visit_service.py:241-253` - ST_Contains with Geography->Geometry cast pattern

### Pattern 3: Utility app frontend architecture (replicate for game app)

- **Location**: `utility/` - entire utility app
- **Why relevant**: Game app is a sibling Expo project with identical architecture. Copy and adapt all patterns.
- **Key files**:
  - `utility/services/api.ts` - Axios + SecureStore + 401 refresh (copy entire file, change imports)
  - `utility/stores/authStore.ts` - Zustand auth store (copy entire file)
  - `utility/hooks/useLocationTracking.ts` - GPS tracking hook (copy; change VISIT_QUERY_KEYS to game-specific keys)
  - `utility/app/_layout.tsx` - Root layout with auth gate (copy and adapt)
  - `utility/app/(tabs)/_layout.tsx` - Tab bar layout (copy; change tabs to Map|Creatures|Inventory|Events|Profile)
  - `utility/constants/config.ts` - Config constants (copy; extend STALE_TIME for game entities)

### Pattern 4: Alembic migration (for 003_game_schema.py)

- **Location**: `backend/alembic/versions/002_utility_schema.py`
- **Why relevant**: Shows correct migration structure including depends_on, upgrade/downgrade functions, table creation.

---

## Test Coverage

### Existing Tests (no changes needed unless visit_service modification breaks them)

| Test File | Impact | Action Needed |
|-----------|--------|---------------|
| `backend/tests/test_visits.py` | visit_service.auto_confirm_visit() is modified | Verify existing tests pass after adding game reward dispatch; mock game_service in visit tests |

### New Tests Needed

| Test Type | Location | Coverage Target |
|-----------|----------|-----------------|
| Integration | `backend/tests/test_game.py` | GET /game/me, GET /game/creatures, GET /game/inventory, POST /game/inventory/loot-boxes/{id}/open, POST /game/inventory/craft |
| Integration | `backend/tests/test_territories.py` | GET /game/territories/nearby (PostGIS), POST /game/territories/{id}/claim, POST /game/territories/{id}/challenge (PvP resolution) |
| Integration | `backend/tests/test_events.py` | GET /game/events, GET /game/events/{id}, POST /game/events/{id}/check-in (radius validation) |
| Integration | `backend/tests/test_social_game.py` | GET /game/social/friends, POST /game/social/trades, POST /game/social/trades/{id}/respond, GET /game/leaderboards |

---

## Risk Assessment

### High Risk Areas

| Area | Risk | Mitigation |
|------|------|------------|
| Circular import in visit_service.py | `dispatch_visit_rewards` import from game_service inside visit_service creates circular module dependency (game_service imports models that visit_service already imports) | Use lazy import inside auto_confirm_visit(): `from app.services.game_service import dispatch_visit_rewards` inside the function body, not at module top |
| PvP familiarity calculation | Familiarity scores stored as JSON dict `{user_id: score}` in Territory; reading and comparing user scores for defender advantage requires careful deserialization | Define explicit familiarity_bonus formula (e.g., min(score/1000, 0.5) for max 50% bonus); document in territory_service.py |
| Territory concurrent challenge | Two users may simultaneously challenge the same territory; the last commit wins, creating inconsistent state | Use database row-level locking: `SELECT ... FOR UPDATE` on Territory row before PvP resolution |
| Passive reward Celery task at scale | With many territories, hourly tick across all territories can be O(N) on DB; slow tasks cause reward delays | Batch updates using bulk UPDATE SQL; add index on Territory.owner_id |
| react-native-maps Polygon performance | Rendering many territory polygons (neighborhoods/districts) on map can cause frame drops | Cluster territories by zoom level; only render visible territories within map viewport; limit to 50 polygons at once |
| LootBox rarity roll fairness | Client-side seed manipulation possible if RNG is predictable | Perform all rarity rolls server-side in open_loot_box(); never expose roll seed to client |
| Trade item ownership validation | Concurrent trades could allow same item to be offered in two trades | Before accepting trade: lock Item rows with SELECT FOR UPDATE, validate equipped_creature_id is NULL and item belongs to sender |

---

## Recommended Exploration

Before implementation, developer should read:

1. `/Users/arnaudmagnan/development/mappn/.specs/plans/mappn-platform.design.md` - Full game mechanics, all screen specs, data model, zone type definitions
2. `/Users/arnaudmagnan/development/mappn/backend/app/services/visit_service.py:188-289` - The auto_confirm_visit() function that must be modified to dispatch game rewards
3. `/Users/arnaudmagnan/development/mappn/backend/app/services/visit_service.py:241-253` - ST_Contains PostGIS pattern to replicate in territory_service.get_nearby_territories()
4. `/Users/arnaudmagnan/development/mappn/utility/services/api.ts` - Axios client pattern to copy verbatim for game app
5. `/Users/arnaudmagnan/development/mappn/utility/hooks/useLocationTracking.ts` - GPS tracking hook to copy (change VISIT_QUERY_KEYS to game cache keys)
6. `/Users/arnaudmagnan/development/mappn/backend/app/api/utility.py` + `backend/app/services/utility_service.py` - API + service layer pattern to follow for all game endpoints
7. `/Users/arnaudmagnan/development/mappn/backend/tests/conftest.py` - Test fixture patterns for new game test files

---

## Verification Summary

| Check | Status | Notes |
|-------|--------|-------|
| All affected files identified | Done | 4 backend files to modify + ~30 new backend files + ~60 new game app files |
| Integration points mapped | Done | 6 critical backend integration points; 4 frontend critical points |
| Similar patterns found | Done | 4 patterns identified (utility API, PostGIS spatial, utility frontend, Alembic migration) |
| Test coverage analyzed | Done | 4 new test modules; 1 existing test (test_visits.py) may need mock update |
| Risks assessed | Done | 7 risk areas with mitigations, including circular import and concurrency risks |

**Limitations/Caveats:**
- The game app (~60 files) is a new greenfield Expo project; exact component count may vary during implementation.
- The design doc does not specify a full ItemTemplate crafting recipe system; `crafting_cost` as a JSONB field on ItemTemplate is assumed.
- WebSocket real-time updates for PvP results and territory changes are mentioned in the design doc but not specified in detail; the analysis assumes polling via TanStack Query refetch intervals as the initial implementation.
- The passive reward formula (XP and component rates) is not quantified in the design doc; territory_service must define the formula based on `passive_reward_rate` and creature stats.
- Event quest steps structure (`quest_steps` JSONB field on Event) is not detailed; multi-step quest logic in EventParticipation is a complex sub-system to design at implementation time.
- The leaderboard refresh strategy (real-time vs. scheduled Celery task) is not specified; pre-computed LeaderboardEntry rows refreshed by Celery beat is the assumed approach.
