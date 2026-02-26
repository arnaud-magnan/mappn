---
title: Codebase Impact Analysis - Implement Mappn utility app with React Native and Expo
task_file: .specs/tasks/draft/implement-utility-app.feature.md
scratchpad: .specs/scratchpad/e8caba9b.md
created: 2026-02-25
status: complete
---

# Codebase Impact Analysis: Implement Mappn utility app with React Native and Expo

## Summary

- **Files to Modify**: 1 file (backend/app/main.py)
- **Files to Create**: 5 backend files + ~50 utility app files
- **Files to Delete**: 0 files
- **Test Files Affected**: 5 new test files (backend utility endpoints)
- **Risk Level**: Medium (greenfield utility app, but backend integration is well-defined)

---

## Context: Existing Backend

The shared backend is fully built at `/Users/arnaudmagnan/development/mappn/backend/`. The utility app consumes these existing API endpoints:

| Endpoint | Method | Used by Screen |
|----------|--------|---------------|
| `/auth/register` | POST | Auth flow |
| `/auth/login` | POST | Auth flow |
| `/auth/refresh` | POST | Token refresh |
| `/auth/me` | GET | Profile screen |
| `/places/nearby?lat&lon&radius_m&category` | GET | Map screen |
| `/places/{id}` | GET | Place Detail screen |
| `/places/{id}/forecast?day=0-6&hour=0-23` | GET | Place Detail forecast slider |
| `/visits/ping` | POST | Background GPS tracking |
| `/visits/history?limit&offset` | GET | Journal screen base data |

Key backend data shapes (verified from source):
- `PlaceResponse`: `{id, name, category, lat, lon, address, current_busyness: 0-100, busyness_stale, busyness_updated_at}`
- `PlaceDetailResponse`: `{id, name, category, lat, lon, address, city, country, busyness_data: {popular_times: [{day: 0-6, hours: [int*24]}], current_popularity: int}, busyness_updated_at, busyness_stale}`
- `GPSPingResponse`: `{nearby_places: [{place_id, name, distance_m}], confirmed_visits: [{visit_id, place_id, duration_seconds}], rejected, rejection_reason}`
- `VisitResponse`: `{id, place_id, place_name, area_id, started_at, ended_at, duration_seconds}`

---

## Files to be Modified/Created

### Backend Additions (new endpoints for utility-specific features)

```
backend/
├── app/
│   ├── main.py                               # UPDATE: add include_router(utility_router) at line ~151
│   ├── models/
│   │   └── journal.py                        # NEW: JournalNote ORM model
│   ├── schemas/
│   │   └── utility.py                        # NEW: Pydantic schemas for utility endpoints
│   ├── api/
│   │   └── utility.py                        # NEW: Router - /users/me/stats, /users/me/achievements,
│   │                                         #       /journal, /explore/heatmap, /passports
│   └── services/
│       └── utility_service.py                # NEW: Service functions for exploration/stats/achievements
└── alembic/
    └── versions/
        └── 002_utility_schema.py             # NEW: Migration for journal_notes table
```

**backend/app/models/journal.py** - NEW ORM model:
- `JournalNote`: id, visit_id (FK visits.id), user_id (FK users.id), text (nullable), photo_url (nullable), created_at

**backend/app/schemas/utility.py** - NEW Pydantic schemas:
- `UserStatsResponse`: places_count, cities_count, countries_count, total_duration_seconds
- `AchievementResponse`: id, name, description, category, earned_at
- `JournalEntryResponse`: visit_id, place_id, place_name, area_id, city, started_at, duration_seconds, note (nullable), photo_url (nullable)
- `JournalNoteRequest`: text (max 1000 chars), photo_url (optional)
- `HeatmapAreaResponse`: id, name, city, boundary_geojson, visited, visited_at (nullable)
- `HeatmapResponse`: areas (list), total_areas, visited_areas, explored_pct
- `PassportStampResponse`: area_id, name, visited_at
- `CityPassportResponse`: city, total_neighborhoods, visited_count, stamps (list), badge_earned, explored_pct

**backend/app/api/utility.py** - NEW API routes:
- `GET /users/me/stats` -> UserStatsResponse (auth required)
- `GET /users/me/achievements` -> list[AchievementResponse] (auth required)
- `GET /journal?limit&offset` -> list[JournalEntryResponse] (auth required)
- `POST /journal/{visit_id}/note` -> JournalEntryResponse (auth required)
- `GET /explore/heatmap?city=<optional>` -> HeatmapResponse (auth required)
- `GET /passports?city=Lyon` -> CityPassportResponse (auth required)

**backend/app/services/utility_service.py** - NEW service functions:
- `get_user_stats(db, user_id)` -> counts from Visit JOIN Place, distinct cities/countries
- `get_user_achievements(db, user_id)` -> checks achievement criteria against visit history
- `get_journal_entries(db, user_id, limit, offset)` -> Visit JOIN JournalNote
- `add_journal_note(db, user_id, visit_id, text, photo_url)` -> upsert JournalNote
- `get_heatmap(db, user_id, city=None)` -> areas with visited flag from Visit.area_id
- `get_city_passport(db, user_id, city)` -> neighborhood stamps for city

**Achievement criteria** (implemented in utility_service.py):
- "Wanderer": 10 distinct neighborhoods visited (10 distinct area_ids in visits)
- "Globe Trotter": 5 distinct cities visited (5 distinct place.city values in visits)
- "Night Owl": 10 places visited after midnight (started_at hour >= 0 and < 4)
- "Early Bird": 10 places visited before 7am (started_at hour < 7)
- "Foodie": 50 visits to places with category="restaurant"
- "Culture Vulture": 20 visits to places with category="museum"

### Utility App (new Expo project)

```
utility/
├── app.json                                  # NEW: Expo config, permissions, bundle identifier
├── package.json                              # NEW: Dependencies
├── tsconfig.json                             # NEW: TypeScript config
├── babel.config.js                           # NEW: Babel config for Expo
├── metro.config.js                           # NEW: Metro bundler config
├── .env.example                              # NEW: API base URL, environment variables
│
├── app/                                      # Expo Router file-based routing
│   ├── _layout.tsx                           # NEW: Root layout, auth gate, providers setup
│   ├── (auth)/
│   │   ├── _layout.tsx                       # NEW: Auth stack layout (no tab bar)
│   │   ├── login.tsx                         # NEW: Login screen
│   │   └── register.tsx                      # NEW: Register screen
│   └── (tabs)/
│       ├── _layout.tsx                       # NEW: Bottom tab bar layout (Map|Explore|Journal|Profile)
│       ├── index.tsx                         # NEW: Map tab (home) - full-screen map
│       ├── explore.tsx                       # NEW: Explore tab - heatmap + city selector
│       ├── journal.tsx                       # NEW: Journal tab - visit timeline
│       └── profile.tsx                       # NEW: Profile tab - stats + achievements
│
├── screens/                                  # Full-screen modal/stack screens
│   ├── PlaceDetailScreen.tsx                 # NEW: Place detail with histogram, forecast
│   ├── JournalNoteScreen.tsx                 # NEW: Add/edit note for journal entry
│   └── CityPassportScreen.tsx               # NEW: City passport stamps view
│
├── components/
│   ├── map/
│   │   ├── PlacePin.tsx                      # NEW: Colored map pin (green/yellow/red by busyness)
│   │   ├── PlaceCluster.tsx                  # NEW: Clustered pins when zoomed out
│   │   └── CategoryFilter.tsx                # NEW: Horizontal filter pills (All/Restaurant/Park/...)
│   ├── place/
│   │   ├── BusynessHistogram.tsx             # NEW: Hour-by-hour bar chart from popular_times data
│   │   ├── LiveBusynessIndicator.tsx         # NEW: Current busyness badge (color + number)
│   │   ├── ForecastSlider.tsx                # NEW: Day/hour slider to query forecast endpoint
│   │   └── VisitHistoryList.tsx              # NEW: Past user visits to this place
│   ├── explore/
│   │   ├── HeatmapLayer.tsx                  # NEW: Polygon overlay on map for visited areas
│   │   ├── CityProgress.tsx                  # NEW: "23% of Lyon explored" progress bar
│   │   └── ShareableCard.tsx                 # NEW: Shareable exploration summary image
│   ├── journal/
│   │   ├── JournalEntry.tsx                  # NEW: Single timeline entry card
│   │   └── JournalEntryList.tsx              # NEW: Infinite scroll list of journal entries
│   ├── profile/
│   │   ├── StatCard.tsx                      # NEW: Stat display (places visited, cities, countries)
│   │   ├── AchievementBadge.tsx              # NEW: Achievement card with icon + earned status
│   │   └── AchievementGrid.tsx              # NEW: Grid layout of all achievements
│   └── ui/
│       ├── Button.tsx                        # NEW: Shared button component
│       ├── Card.tsx                          # NEW: Shared card container
│       ├── LoadingSpinner.tsx                # NEW: Loading state indicator
│       └── ErrorBoundary.tsx                # NEW: Error boundary wrapper
│
├── services/
│   ├── api.ts                                # NEW: Axios instance, auth token injection, refresh logic
│   ├── authService.ts                        # NEW: login(), register(), refreshToken(), logout()
│   ├── placesService.ts                      # NEW: getNearbyPlaces(), getPlaceDetail(), getForecast()
│   ├── visitsService.ts                      # NEW: postGpsPing(), getVisitHistory()
│   ├── utilityService.ts                     # NEW: getUserStats(), getAchievements(), getJournal(),
│   │                                         #       addJournalNote(), getHeatmap(), getCityPassport()
│   └── locationService.ts                    # NEW: startBackgroundTracking(), stopTracking()
│
├── stores/
│   ├── authStore.ts                          # NEW: Zustand store - tokens, user info, isAuthenticated
│   ├── locationStore.ts                      # NEW: Zustand store - current GPS coords, accuracy
│   └── mapStore.ts                           # NEW: Zustand store - map region, active filters
│
├── hooks/
│   ├── useNearbyPlaces.ts                    # NEW: TanStack Query hook for /places/nearby
│   ├── usePlaceDetail.ts                     # NEW: TanStack Query hook for /places/{id}
│   ├── useForecast.ts                        # NEW: TanStack Query hook for /places/{id}/forecast
│   ├── useJournal.ts                         # NEW: TanStack Query infinite query for /journal
│   ├── useUserStats.ts                       # NEW: TanStack Query hook for /users/me/stats
│   ├── useAchievements.ts                    # NEW: TanStack Query hook for /users/me/achievements
│   ├── useHeatmap.ts                         # NEW: TanStack Query hook for /explore/heatmap
│   └── useCityPassport.ts                    # NEW: TanStack Query hook for /passports?city=
│
├── tasks/
│   └── backgroundLocation.ts                # NEW: Expo TaskManager background GPS ping task
│
└── types/
    ├── api.ts                                # NEW: TypeScript types mirroring backend schemas
    ├── navigation.ts                         # NEW: Expo Router typed navigation params
    └── place.ts                              # NEW: Place, BusynessData, ForecastResult types
```

### Test Files (backend utility endpoints)

```
backend/
└── tests/
    └── test_utility.py                       # NEW: Tests for all utility endpoints
```

---

## Useful Resources for Implementation

### Pattern References

```
backend/
├── app/
│   ├── api/
│   │   ├── places.py              # Pattern: router definition, Depends injection, response_model
│   │   └── visits.py              # Pattern: POST endpoint with body schema, auth required
│   ├── services/
│   │   ├── visit_service.py       # Pattern: async service with db session, JOIN queries
│   │   └── places_service.py      # Pattern: PostGIS query, dict result serialization
│   └── models/
│       └── visit.py               # Pattern: FK relationships, DateTime fields
└── tests/
    ├── conftest.py                # Pattern: async test fixtures, test user, test DB
    └── test_places.py             # Pattern: test structure for API endpoint tests
```

---

## Key Interfaces and Contracts

### Backend Functions to Create

| Location | Name | Signature | Purpose |
|----------|------|-----------|---------|
| `backend/app/services/utility_service.py` | `get_user_stats` | `async fn(db: AsyncSession, user_id: int) -> dict` | COUNT visits, distinct cities/countries |
| `backend/app/services/utility_service.py` | `get_user_achievements` | `async fn(db: AsyncSession, user_id: int) -> list[dict]` | Check achievement criteria |
| `backend/app/services/utility_service.py` | `get_journal_entries` | `async fn(db: AsyncSession, user_id: int, limit: int, offset: int) -> list[dict]` | JOIN Visit + JournalNote |
| `backend/app/services/utility_service.py` | `add_journal_note` | `async fn(db: AsyncSession, user_id: int, visit_id: int, text: str, photo_url: str \| None) -> dict` | Upsert JournalNote |
| `backend/app/services/utility_service.py` | `get_heatmap` | `async fn(db: AsyncSession, user_id: int, city: str \| None) -> dict` | Distinct visited area_ids |
| `backend/app/services/utility_service.py` | `get_city_passport` | `async fn(db: AsyncSession, user_id: int, city: str) -> dict` | Stamps per area in city |

### Backend File to Modify

| Location | Change Required |
|----------|-----------------|
| `backend/app/main.py:149-151` | Add `from app.api.utility import router as utility_router` and `app.include_router(utility_router)` after existing router registrations |
| `backend/app/models/__init__.py:8-20` | Add `from app.models.journal import JournalNote` and `"JournalNote"` to `__all__` |

### Frontend Services to Create

| Location | Name | Backend Endpoint |
|----------|------|-----------------|
| `utility/services/placesService.ts` | `getNearbyPlaces(lat, lon, radius_m, category?)` | GET /places/nearby |
| `utility/services/placesService.ts` | `getPlaceDetail(placeId)` | GET /places/{id} |
| `utility/services/placesService.ts` | `getForecast(placeId, day, hour)` | GET /places/{id}/forecast |
| `utility/services/visitsService.ts` | `postGpsPing(lat, lon, accuracy, timestamp)` | POST /visits/ping |
| `utility/services/visitsService.ts` | `getVisitHistory(limit, offset)` | GET /visits/history |
| `utility/services/utilityService.ts` | `getUserStats()` | GET /users/me/stats |
| `utility/services/utilityService.ts` | `getAchievements()` | GET /users/me/achievements |
| `utility/services/utilityService.ts` | `getJournal(limit, offset)` | GET /journal |
| `utility/services/utilityService.ts` | `addJournalNote(visitId, text, photoUrl?)` | POST /journal/{visit_id}/note |
| `utility/services/utilityService.ts` | `getHeatmap(city?)` | GET /explore/heatmap |
| `utility/services/utilityService.ts` | `getCityPassport(city)` | GET /passports |

### TypeScript Types to Create (utility/types/api.ts)

Key types mirroring backend schemas:
- `PlaceResponse`, `PlaceDetailResponse`, `ForecastResponse` (from backend schemas/place.py)
- `BusynessData`: `{popular_times: Array<{day: number, hours: number[]}>, current_popularity?: number}`
- `GPSPingResponse`, `VisitResponse` (from backend schemas/visit.ts)
- `UserStatsResponse`, `AchievementResponse`, `JournalEntryResponse`, `HeatmapResponse`, `CityPassportResponse` (from new utility endpoints)

---

## Integration Points

### Backend Integration

| File | Relationship | Impact | Action Needed |
|------|--------------|--------|---------------|
| `backend/app/main.py:149-151` | Must include new utility_router | High | Add include_router call |
| `backend/app/models/__init__.py` | Must re-export JournalNote for Alembic | High | Add JournalNote import |
| `backend/app/models/visit.py` | JournalNote has FK to visits.id | High | Verify Visit.id is accessible; no change needed to Visit model |
| `backend/app/models/area.py` | Area has city field used in heatmap/passport queries | High | No change needed; city field already exists |
| `backend/app/models/place.py` | Place has city, country fields used in stats queries | High | No change needed |
| `backend/alembic/versions/001_initial_schema.py` | First migration must run before 002 | Critical | 002 depends on visits table existing |

### Frontend Integration

| File | Relationship | Impact | Action Needed |
|------|--------------|--------|---------------|
| `utility/services/api.ts` | All service files import axios instance from here | High | Implement token injection + 401 refresh logic |
| `utility/stores/authStore.ts` | All services read token from auth store | High | Zustand persist with SecureStore for token persistence |
| `utility/tasks/backgroundLocation.ts` | Registered in app/_layout.tsx on app load | High | expo-task-manager TaskManager.defineTask() |
| `utility/app/_layout.tsx` | Root layout gates auth, sets up QueryClient, registers bg task | Critical | Must wrap with QueryClientProvider and ZustandProvider |

---

## Similar Implementations

### Pattern 1: Backend places API pattern (to follow for utility endpoints)

- **Location**: `backend/app/api/places.py` + `backend/app/services/places_service.py`
- **Why relevant**: Shows correct pattern for: router with Depends(get_db) + Depends(get_current_user), service function returning dict, schema with model_config = ConfigDict(from_attributes=True)
- **Key files**:
  - `backend/app/api/places.py` - Router definition with response_model, auth dependency
  - `backend/app/services/places_service.py` - Async service with SQLAlchemy select, dict serialization

### Pattern 2: Visit service for complex DB queries

- **Location**: `backend/app/services/visit_service.py:280-326`
- **Why relevant**: `get_visit_history()` shows how to JOIN two tables (Visit + Place) and return dict list - exact same pattern needed for `get_journal_entries()` (Visit JOIN JournalNote JOIN Place)
- **Key files**:
  - `backend/app/services/visit_service.py:280` - `get_visit_history()` function with JOIN pattern

### Pattern 3: Test conftest and fixture pattern

- **Location**: `backend/tests/conftest.py`
- **Why relevant**: Contains async test DB setup, test user creation, authenticated test client - all needed for new utility endpoint tests
- **Key files**:
  - `backend/tests/conftest.py` - All fixtures
  - `backend/tests/test_places.py` - Shows test structure for GET endpoints with auth

---

## Test Coverage

### New Tests Needed

| Test Type | Location | Coverage Target |
|-----------|----------|-----------------|
| Unit + Integration | `backend/tests/test_utility.py` | GET /users/me/stats, GET /users/me/achievements, GET /journal, POST /journal/{id}/note, GET /explore/heatmap, GET /passports |

---

## Risk Assessment

### High Risk Areas

| Area | Risk | Mitigation |
|------|------|------------|
| Background GPS on iOS | expo-location background mode requires explicit iOS permission and entitlement in app.json | Set `ios.infoPlist.NSLocationAlwaysUsageDescription`, add `location` to `ios.infoPlist.UIBackgroundModes` |
| Area-to-city mapping | Heatmap/passport requires visits have area_id populated, but current visit_service.py sets area_id=None (no spatial containment check) | The `auto_confirm_visit()` in visit_service.py:234-241 explicitly leaves area_id=None; needs ST_Contains query to assign area before utility heatmap works |
| popular_times JSONB structure | The forecast_service.py reads `busyness_data["popular_times"]` as list of `{day: int, hours: [int*24]}` dicts - the histogram component must match this exact structure | Validate against `forecast_service.py:1-19` docstring before building BusynessHistogram component |
| Token persistence on mobile | JWT access token must survive app restart; must use expo-secure-store not AsyncStorage | Use `expo-secure-store` for token storage in Zustand auth store |
| Android location permissions | POST /visits/ping accuracy field must be <= 100m threshold; Android GPS can be < 100m outdoors but > 100m indoors | Implement graceful degradation: show "GPS too inaccurate" message, do not ping |

### Critical Gap: area_id Assignment in visit_service.py

The exploration heatmap and city passport features depend on `Visit.area_id` being set when a visit is confirmed. Currently in `backend/app/services/visit_service.py:232-241`, the area lookup is a stub that always sets `area_id = None`:

```python
# From visit_service.py:234-241
place = await db.get(Place, place_id)
area_id = None
if place is not None:
    # The Place model does not have a direct area_id. We leave area_id
    # as None unless the place has an associated area...
    pass
```

**This must be fixed as part of this task** by adding a ST_Contains query:
- File to update: `backend/app/services/visit_service.py:232-241`
- Change: Add PostGIS `ST_Contains(Area.boundary, user_point)` query to find which area the place falls within, then set `area_id` on the Visit

---

## Recommended Exploration

Before implementation, developer should read:

1. `/Users/arnaudmagnan/development/mappn/.specs/plans/mappn-platform.design.md` - Full platform design, all screen specifications
2. `/Users/arnaudmagnan/development/mappn/backend/app/services/visit_service.py:232-241` - Critical: area_id stub that must be fixed before heatmap/passport works
3. `/Users/arnaudmagnan/development/mappn/backend/app/services/forecast_service.py:1-19` - busyness_data JSONB structure (docstring) that the histogram component must match
4. `/Users/arnaudmagnan/development/mappn/backend/app/api/places.py` - Template for new utility API router structure
5. `/Users/arnaudmagnan/development/mappn/backend/tests/conftest.py` - Test fixture patterns to reuse for utility endpoint tests

---

## Verification Summary

| Check | Status | Notes |
|-------|--------|-------|
| All affected files identified | Done | 5 new backend files + ~50 utility app files + 1 backend file to modify |
| Integration points mapped | Done | 10 integration points documented including critical area_id gap |
| Similar patterns found | Done | 3 patterns identified (places API, visit service JOIN, test conftest) |
| Test coverage analyzed | Done | 1 new test file for all 6 new backend endpoints |
| Risks assessed | Done | 5 risk areas; 1 critical gap (area_id stub) documented |

**Limitations/Caveats:**
- The utility app (~50 files) is a greenfield Expo project; exact component structure may evolve during implementation.
- Achievement criteria are defined based on the design doc; final criteria and unlock counts may need product input.
- The Expo SDK version (52+) and exact dependency versions should be confirmed at implementation time as Expo releases frequently.
- Journal photo upload requires a backend file storage solution (S3/local disk) not yet specified; `photo_url` is included as a nullable string field but the upload mechanism (multipart POST or pre-signed URL) is left to implementation.
- The visit_service.py area_id gap is a **blocking dependency** for the heatmap and city passport screens; it must be resolved early in the implementation.
