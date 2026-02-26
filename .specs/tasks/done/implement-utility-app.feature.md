---
title: Implement Mappn utility app with React Native and Expo
depends_on:
  - implement-shared-backend.feature.md
---

> **Required Skill**: You MUST use and analyse `react-native-expo-mobile-app` skill before doing any modification to task file or starting implementation of it!
>
> Skill location: `.claude/skills/react-native-expo-mobile-app/SKILL.md`

## Initial User Prompt

Build the Mappn utility app (React Native/Expo): map view with busyness-colored pins, place detail with popular times and forecast, personal exploration heatmap, profile with stats and achievements, travel journal, and city passports. See `.specs/plans/mappn-platform.design.md` for full screen designs.

# Description

The Mappn Utility app is the consumer-facing mobile application of the Mappn platform. It transforms backend place data, busyness information, and visit tracking into an engaging exploration experience. The app serves two purposes: first, it provides immediate utility by showing users real-time and forecasted busyness for nearby places, helping them decide when and where to go; second, it creates a gamified exploration loop through a personal heatmap, themed achievements, a travel journal, and city passports, motivating users to discover more places and return to the app regularly.

The app consists of six screens accessible through a four-tab navigation bar (Map, Explore, Journal, Profile). The Map View is the home screen with a full-screen map showing place pins color-coded by busyness level and filterable by category. The Place Detail screen shows comprehensive busyness data including popular times histograms and a forecast slider. The Exploration Map shows a personal heatmap of neighborhoods visited with per-city progress percentages. The Profile screen displays aggregate statistics and themed achievements. The Travel Journal presents a chronological timeline of visits with optional user-added notes and photos stored on-device. City Passports let users collect neighborhood stamps and earn city completion badges.

This task covers the mobile app only. It consumes the shared backend that has already been built (authentication, places service, visit tracking, scraping pipeline). The app presents data from backend APIs, sends GPS coordinates every 15 seconds for visit detection, and tracks user progress toward achievements and city passport completion. No backend modifications are included.

**Scope**:
- Included: All 6 screens (Map View, Place Detail, Exploration Map, Profile and Stats, Travel Journal, City Passports), bottom tab navigation (Map, Explore, Journal, Profile), authentication flow (register, login, session persistence, automatic credential refresh on token expiration), backend API integration for places, visits, and busyness data, GPS coordinate submission every 15 seconds for visit tracking, location permission handling, busyness color coding on map pins, popular times histogram visualization, busyness forecast interaction, personal exploration heatmap with per-city progress, shareable exploration map image generation, aggregate visit statistics, 6 themed achievements across 3 categories with progress tracking -- Explorer: "Wanderer" (10 neighborhoods visited) and "Globe Trotter" (5 cities visited); Habits: "Night Owl" (10 places visited after midnight) and "Early Bird" (10 places visited before 7am); Categories: "Foodie" (50 restaurant visits) and "Culture Vulture" (20 museum visits) -- chronological travel journal with optional user notes and photos, city passport stamps per neighborhood with progress bars and city badges, empty states for all screens, error handling for all failure scenarios
- Excluded: Backend modifications or new endpoints, game app features (creatures, territories, PvP, loot, events), social features (friends, trading, leaderboards), push notifications, full offline mode, name-based place search, app store deployment, admin or content management tools, analytics infrastructure

**User Scenarios**:
1. **Primary Flow**: User registers (or logs in), views the busyness map with color-coded pins, taps a pin to see its summary, opens place detail to view popular times and check the forecast for Saturday evening, physically visits the place with GPS tracking active (coordinates sent every 15 seconds), and after the backend confirms the visit, sees it appear in the travel journal, the exploration heatmap, the profile stats, and as a new stamp in city passports.
2. **Alternative Flows**: User filters the map by "restaurants" to narrow visible pins; user views a place that has no busyness data yet and sees a placeholder indicating data is unavailable; user adds a photo and note to a journal entry; user views the exploration map for a previously visited city; user generates and shares an image of their exploration map with stats overlay; user swipes through different days on the popular times histogram; user's authentication token expires mid-session and the app silently refreshes it without interrupting the experience.
3. **Error Handling**: Location permission denied shows a guidance message explaining why location is needed, with the map still functional but centered on a default location; GPS accuracy too low displays a notice while map browsing continues; network loss displays previously loaded data with a connectivity warning; automatic token refresh is attempted when a session expires -- if refresh fails, the user is redirected to the login screen with a clear message; all screens with no data yet show empty states with helpful guidance (e.g., "Visit places to start your journal!").

---

## Acceptance Criteria

### Functional Requirements

#### Authentication

- [ ] **User Registration**: Users can create an account directly in the app
  - Given: A new user opens the app for the first time
  - When: The user fills in email, username, and password and submits the registration form
  - Then: The account is created, the user is logged in, and the map view is displayed

- [ ] **User Login**: Returning users can authenticate and access their data
  - Given: A user has an existing account
  - When: The user enters valid email and password on the login screen
  - Then: The user is authenticated and the map view is displayed with their data

- [ ] **Session Persistence**: Users remain logged in across app launches
  - Given: A user has previously logged in and their credentials have not expired
  - When: The user reopens the app
  - Then: The user is taken directly to the map view without needing to log in again

- [ ] **Automatic Token Refresh**: Authentication tokens are renewed transparently during active use
  - Given: A user is actively using the app and their access token expires
  - When: The app makes a request to the backend that is rejected due to an expired token
  - Then: The app automatically requests a new access token using the refresh credential, retries the original request, and the user's experience continues without interruption or visible error

- [ ] **Authentication Error Handling**: Invalid credentials and unrecoverable session failures are handled clearly
  - Given: A user submits incorrect credentials, or the automatic token refresh fails (e.g., refresh token is also expired)
  - When: The authentication cannot be recovered
  - Then: The user sees a clear error message explaining the issue and is directed to log in again

#### Map View

- [ ] **Busyness-Colored Pins**: Map displays nearby places as pins colored by busyness level
  - Given: The user is on the map view and has granted location permission
  - When: The map loads or the user pans to a new area
  - Then: Place pins appear within the visible area, color-coded as green (quiet), yellow (moderate), red (busy), or grey (no busyness data available)

- [ ] **Pin Summary Card**: Tapping a pin reveals key place information
  - Given: The map is showing place pins
  - When: The user taps on a pin
  - Then: A summary card appears showing the place name, current busyness level, and a mini popular times chart for the current day

- [ ] **Category Filtering**: Users can filter map pins by place type
  - Given: The map is showing multiple place pins of different categories
  - When: The user selects one or more category filters (e.g., "restaurant", "park")
  - Then: Only pins matching the selected categories remain visible on the map

- [ ] **Map Loading Performance**: The map loads promptly with place data
  - Given: The user opens the app with a standard mobile data connection
  - When: The map view loads for the first time
  - Then: Place pins appear on the map within 3 seconds

#### Place Detail

- [ ] **Popular Times Histogram**: Users can view hourly busyness patterns for each day
  - Given: The user opens the detail screen for a place that has busyness data
  - When: The place detail screen loads
  - Then: A histogram is displayed showing hour-by-hour busyness levels for the selected day, and the user can switch between days of the week

- [ ] **Live Busyness Indicator**: Current busyness is prominently displayed
  - Given: The user is viewing a place detail screen
  - When: The place has live busyness data available
  - Then: The current busyness level is displayed as a prominent indicator (label and visual) distinct from the historical histogram

- [ ] **Busyness Forecast**: Users can check predicted busyness for a future time
  - Given: The user is on a place detail screen with busyness data
  - When: The user selects a future day and hour using the forecast control
  - Then: The predicted busyness level for that specific time is displayed within 500 milliseconds of the selection

- [ ] **Place Visit History**: Users can see their past visits to a specific place
  - Given: The user has previously visited this place at least once
  - When: The user views the place detail screen
  - Then: A list of the user's past visits to this place is displayed, showing date and duration for each visit

#### Exploration Map

- [ ] **Personal Heatmap**: Visited neighborhoods appear as colored areas on the map
  - Given: The user has confirmed visits in one or more neighborhoods
  - When: The user opens the Exploration Map screen
  - Then: Each neighborhood where the user has visited at least one place is displayed as a colored overlay on the map, and unvisited neighborhoods remain uncolored

- [ ] **City Exploration Percentage**: Users see their exploration progress per city
  - Given: The user has visits in a city that has defined neighborhoods
  - When: The user views the exploration map for that city
  - Then: A percentage is displayed showing the ratio of neighborhoods visited to total neighborhoods in the city (e.g., "23% of Lyon explored")

- [ ] **Shareable Exploration Image**: Users can generate and share their exploration map
  - Given: The user is viewing their exploration map with at least one visited neighborhood
  - When: The user taps the share action
  - Then: An image is generated showing the heatmap with a stats overlay (places visited, exploration percentage) and the device share sheet opens

#### Profile and Stats

- [ ] **Aggregate Statistics**: Users see a summary of their exploration activity
  - Given: The user has at least one confirmed visit
  - When: The user opens the Profile screen
  - Then: The screen displays total places visited, total cities explored, and total countries reached

- [ ] **Themed Achievements with Progress**: Users can track progress toward specific exploration milestones
  - Given: The user opens the Profile screen
  - When: The achievements section loads
  - Then: The following 6 achievements are displayed across 3 categories, each showing its name, description, current progress count, and required threshold:
    - Explorer category: "Wanderer" -- visit 10 distinct neighborhoods; "Globe Trotter" -- visit 5 distinct cities
    - Habits category: "Night Owl" -- visit 10 places after midnight; "Early Bird" -- visit 10 places before 7am
    - Categories category: "Foodie" -- visit 50 restaurants; "Culture Vulture" -- visit 20 museums

- [ ] **Achievement Unlocking**: Achievements are awarded when thresholds are met
  - Given: A user's visit activity meets or exceeds an achievement threshold (e.g., visiting 10 different neighborhoods unlocks "Wanderer", visiting 5 different cities unlocks "Globe Trotter")
  - When: The user views the Profile screen
  - Then: The achievement is displayed as unlocked with a visual distinction from locked achievements, and the progress indicator shows the threshold as fully met

#### Travel Journal

- [ ] **Visit Timeline**: All confirmed visits appear in chronological order
  - Given: The user has one or more confirmed visits
  - When: The user opens the Journal screen
  - Then: A chronological timeline is displayed with each entry showing the place name, visit date, and visit duration

- [ ] **Journal Notes and Photos**: Users can enrich journal entries with personal content
  - Given: The user is viewing a journal entry for a confirmed visit
  - When: The user adds a text note or attaches a photo from their device
  - Then: The note and/or photo are saved and displayed on the journal entry on subsequent views

#### City Passports

- [ ] **Neighborhood Stamps**: Each city shows stamp status per neighborhood
  - Given: The user selects a city that has defined neighborhoods
  - When: The city passport screen loads
  - Then: All neighborhoods in the city are listed, each showing either a "stamped" state (user has visited at least one place there) or an "unstamped" state

- [ ] **City Progress Bar**: Users see their completion progress for each city
  - Given: The user is viewing a city passport
  - When: The passport screen loads
  - Then: A progress bar displays the ratio of stamped neighborhoods to total neighborhoods (e.g., "5 of 20 neighborhoods")

- [ ] **City Completion Badge**: Full city exploration is rewarded
  - Given: A user has earned stamps for every neighborhood in a city
  - When: The user views that city's passport
  - Then: A city completion badge is displayed, visually distinct from the progress state

#### Location and Connectivity

- [ ] **GPS Coordinate Submission**: App sends location data at a defined frequency for visit tracking
  - Given: The user has granted location permission and the app is in the foreground
  - When: The user is actively using the app
  - Then: GPS coordinates are sent to the backend every 15 seconds for visit detection

- [ ] **Location Permission Handling**: Users are guided when location access is needed
  - Given: The user has not yet granted location permission or has denied it
  - When: The app needs location access for map centering or visit tracking
  - Then: A message is displayed explaining why location is needed and how to enable it, and the app remains functional with the map centered on a default location

- [ ] **Low GPS Accuracy Notification**: Users are informed when location quality is poor
  - Given: The device reports GPS accuracy worse than 100 meters
  - When: The app attempts to use location data
  - Then: A notice is displayed informing the user that location accuracy is insufficient for visit tracking

- [ ] **Network Connectivity Handling**: App remains usable during connectivity loss
  - Given: The user was previously using the app with a network connection
  - When: The network connection is lost
  - Then: Previously loaded data remains visible, a connectivity warning is displayed, and GPS coordinates are queued for submission when connectivity returns

- [ ] **Empty State Guidance**: All screens handle absence of data gracefully
  - Given: The user has no confirmed visits (new user)
  - When: The user navigates to the Journal, Exploration Map, Profile, or City Passports screen
  - Then: Each screen displays an appropriate empty state message with guidance on how to get started (e.g., "Visit places to start your journal!")

#### Navigation

- [ ] **Bottom Tab Navigation**: All main sections are accessible via tab bar
  - Given: The user is authenticated and on any screen in the app
  - When: The user taps a tab in the bottom navigation bar
  - Then: The app navigates to the corresponding section (Map, Explore, Journal, or Profile) and the active tab is visually highlighted

### Non-Functional Requirements

- [ ] **Map Rendering Performance**: Map remains smooth with many pins visible
  - The map view maintains at least 30 frames per second while scrolling and panning with up to 200 place pins visible on screen simultaneously
- [ ] **Interaction Responsiveness**: Data visualizations respond promptly to user input
  - The popular times histogram day selector and the busyness forecast control respond to user interaction within 500 milliseconds
- [ ] **Cross-Platform Consistency**: Both mobile platforms deliver the same features
  - All acceptance criteria in this specification pass on both iOS and Android with no platform-specific feature gaps
- [ ] **Accessibility in Color Coding**: Busyness colors are distinguishable by colorblind users
  - The busyness color palette uses colors that are distinguishable by users with the most common forms of color vision deficiency (protanopia and deuteranopia), supplemented by labels or icons

### Definition of Done

- [X] All acceptance criteria pass
- [X] Tests written and passing for core user flows (authentication, map loading, place detail, journal entry, passport progress)
- [X] All 6 screens implemented and navigable
- [X] App runs on both iOS and Android
- [X] Empty states implemented for all screens
- [X] Error states implemented for all failure scenarios
- [ ] Code reviewed

---

## Architecture

- **Skill**: `.claude/skills/react-native-expo-mobile-app/SKILL.md`
- **Codebase Analysis**: `.specs/analysis/analysis-implement-utility-app.md`
- **Scratchpad**: `.specs/scratchpad/545e90d8.md`

### Solution Strategy

**Approach**: Build the Mappn utility app as a greenfield Expo SDK 52 project (`utility/`) within the existing monorepo, following the feature-sliced architecture prescribed by the skill file. The app uses Expo Router v4 for file-based navigation with bottom tabs, react-native-maps for the busyness map with clustered colored markers, TanStack Query v5 for all API data fetching and caching, Zustand for client state (auth, location, map UI), and Axios with interceptors for authenticated API communication. The backend receives 6 new utility-specific endpoints (stats, achievements, journal, heatmap, passports) plus a critical fix to the area_id assignment in visit tracking that unblocks the exploration and passport features.

**Key Decisions**:
1. **Feature-sliced flat architecture over domain modules**: Because the skill file prescribes this structure, the project has ~50 files (not enough to justify deeper nesting), and it creates a clear 1:1 mapping to backend router/service/schema patterns.
2. **Polygon overlays over Heatmap for exploration map**: Because MapView.Heatmap is Google Maps-only (fails on iOS Apple Maps), and Polygon overlays directly support the "neighborhoods fill in" UX with per-neighborhood visited/unvisited state and city progress percentage calculation.
3. **Foreground-only GPS tracking**: Because background location complicates App Store review, drains battery, and is explicitly not required for MVP. Foreground tracking via `watchPositionAsync` at 15-second intervals is sufficient while the app is open.
4. **On-device journal photo storage**: Because backend file upload (S3/pre-signed URLs) is not specified in scope. Photos are stored locally via expo-image-picker and referenced by visit_id in AsyncStorage. Text notes are persisted to the backend via POST /journal/{visit_id}/note.
5. **expo-secure-store for JWT tokens**: Because AsyncStorage is insecure for sensitive data (skill file pitfall). Keychain (iOS) and Keystore (Android) provide OS-level encryption.
6. **ST_Contains query for area_id assignment**: Because the existing visit_service.py stub always sets area_id=None, which makes heatmap and passport features non-functional. The PostGIS GIST index on areas.boundary already exists (from migration 001), making ST_Contains performant.

**Trade-offs Accepted**:
- No offline mode: accepting that the app requires connectivity for data fetching. Previously loaded data is preserved via TanStack Query cache and a connectivity warning is shown.
- No background GPS: accepting that visits are only tracked while the app is in the foreground. This simplifies permissions and App Store review.
- No photo upload to backend: journal photos exist only on-device and are lost if the app is uninstalled. This avoids the complexity of file upload infrastructure for MVP.

---

### Architecture Decomposition

**Components**:

| Component | Responsibility | Dependencies |
|-----------|---------------|--------------|
| Backend: Utility Endpoints | Stats, achievements, journal, heatmap, passports API | FastAPI, SQLAlchemy, existing Visit/Place/Area models |
| Backend: area_id Fix | Assign area_id via PostGIS ST_Contains on visit confirmation | visit_service.py, Area model, PostGIS |
| Frontend: Auth Layer | Login, register, token persistence, auto-refresh | Axios, expo-secure-store, Zustand |
| Frontend: Map Screen | Clustered busyness pins, category filter, bottom sheet preview | react-native-maps, map-clustering, bottom-sheet |
| Frontend: Place Detail | Popular times histogram, live indicator, forecast, visit history | gifted-charts, TanStack Query |
| Frontend: Exploration Map | Polygon district overlays, city progress, share image | react-native-maps Geojson, view-shot, sharing |
| Frontend: Journal | Chronological timeline, notes, photos | TanStack infinite query, image-picker |
| Frontend: Profile & Passports | Stats, achievements, neighborhood stamps, city badges | TanStack Query |
| Frontend: GPS Tracking | Foreground location at 15s, POST /visits/ping | expo-location, visitsService |

**Interactions**:

```
User ──► Auth Layer ──► API (Axios + interceptors)
              │                    │
              ▼                    ▼
         Zustand Stores      TanStack Query Cache
         (auth, location,    (places, visits, stats,
          map UI state)       achievements, journal,
              │               heatmap, passports)
              ▼                    │
         GPS Tracking              ▼
         (expo-location)      Screen Components
              │               (Map, Place Detail,
              ▼               Explore, Journal,
         POST /visits/ping    Profile, Passports)
              │
              ▼
         Backend (FastAPI)
              │
              ▼
         PostgreSQL/PostGIS
```

---

### Expected Changes

```
backend/
├── app/
│   ├── main.py                               # UPDATE: add utility_router registration
│   ├── models/
│   │   ├── __init__.py                       # UPDATE: add JournalNote import
│   │   └── journal.py                        # NEW: JournalNote ORM model
│   ├── schemas/
│   │   └── utility.py                        # NEW: utility endpoint schemas
│   ├── api/
│   │   └── utility.py                        # NEW: utility router (6 endpoints)
│   └── services/
│       ├── visit_service.py                  # UPDATE: fix area_id assignment (ST_Contains)
│       └── utility_service.py                # NEW: utility service functions
├── alembic/
│   └── versions/
│       └── 002_utility_schema.py             # NEW: journal_notes table migration
└── tests/
    ├── conftest.py                           # UPDATE: add utility_router to test app
    └── test_utility.py                       # NEW: utility endpoint tests

utility/                                       # NEW: entire Expo project (~50 files)
├── app.config.ts
├── package.json
├── tsconfig.json
├── eas.json
├── app/
│   ├── _layout.tsx                           # Root layout with providers + auth gate
│   ├── (auth)/
│   │   ├── _layout.tsx
│   │   ├── login.tsx
│   │   └── register.tsx
│   ├── (tabs)/
│   │   ├── _layout.tsx                       # Bottom tabs: Map|Explore|Journal|Profile
│   │   ├── index.tsx                         # Map View
│   │   ├── explore.tsx                       # Exploration Map
│   │   ├── journal.tsx                       # Travel Journal
│   │   └── profile.tsx                       # Profile & Stats
│   ├── place/
│   │   └── [id].tsx                          # Place Detail
│   ├── journal/
│   │   └── [visitId].tsx                     # Journal Note Edit
│   └── passport/
│       └── [city].tsx                        # City Passport
├── components/
│   ├── map/
│   │   ├── PlacePin.tsx                      # Busyness-colored marker (green/yellow/red/grey)
│   │   ├── CategoryFilter.tsx                # Horizontal filter pills
│   │   └── PlaceSummarySheet.tsx             # Bottom sheet with place preview
│   ├── place/
│   │   ├── BusynessHistogram.tsx             # Hour-by-hour bar chart per day
│   │   ├── LiveBusynessIndicator.tsx         # Current busyness badge
│   │   ├── ForecastSlider.tsx                # Day+hour picker with prediction
│   │   └── VisitHistoryList.tsx              # Past visits to this place
│   ├── explore/
│   │   ├── HeatmapLayer.tsx                  # Polygon overlays for visited areas
│   │   ├── CityProgress.tsx                  # Progress bar + percentage
│   │   └── ShareableCard.tsx                 # Capturable view for sharing
│   ├── journal/
│   │   ├── JournalEntry.tsx                  # Single timeline entry card
│   │   └── JournalEntryList.tsx              # Infinite scroll list
│   ├── profile/
│   │   ├── StatCard.tsx                      # Stat display (icon, value, label)
│   │   ├── AchievementBadge.tsx              # Achievement card with progress
│   │   └── AchievementGrid.tsx               # Grid of achievements by category
│   └── ui/
│       ├── Button.tsx                        # Shared button with loading state
│       ├── Card.tsx                          # Shared card container
│       ├── LoadingSpinner.tsx                # Activity indicator
│       ├── EmptyState.tsx                    # Empty state with guidance
│       ├── ErrorBoundary.tsx                 # Error boundary wrapper
│       └── NetworkBanner.tsx                 # Connectivity warning banner
├── services/
│   ├── api.ts                                # Axios instance + interceptors
│   ├── authService.ts                        # login, register, refresh, logout
│   ├── placesService.ts                      # getNearbyPlaces, getPlaceDetail, getForecast
│   ├── visitsService.ts                      # postGpsPing, getVisitHistory
│   ├── utilityService.ts                     # stats, achievements, journal, heatmap, passport
│   └── locationService.ts                    # startTracking, stopTracking
├── stores/
│   ├── authStore.ts                          # Zustand: user, tokens, isAuthenticated
│   ├── locationStore.ts                      # Zustand: coords, accuracy, isTracking
│   └── mapStore.ts                           # Zustand: region, filters, selectedPlaceId
├── hooks/
│   ├── useNearbyPlaces.ts                    # TanStack Query for /places/nearby
│   ├── usePlaceDetail.ts                     # TanStack Query for /places/{id}
│   ├── useForecast.ts                        # TanStack Query for /places/{id}/forecast
│   ├── useJournal.ts                         # TanStack infinite query for /journal
│   ├── useUserStats.ts                       # TanStack Query for /users/me/stats
│   ├── useAchievements.ts                    # TanStack Query for /users/me/achievements
│   ├── useHeatmap.ts                         # TanStack Query for /explore/heatmap
│   ├── useCityPassport.ts                    # TanStack Query for /passports
│   └── useLocationTracking.ts                # GPS tracking lifecycle hook
├── types/
│   └── api.ts                                # TypeScript types mirroring backend schemas
└── constants/
    ├── colors.ts                             # Busyness colors, theme colors
    ├── config.ts                             # API URL, tracking interval
    └── achievements.ts                       # Achievement definitions
```

---

### Runtime Scenarios

**Scenario: User Visits a Place**

```
App foreground ──► GPS ping (15s) ──► POST /visits/ping ──► Backend checks geofence
                       │                                         │
                       ▼                                         ▼
                  locationStore                          UserPresence (Redis)
                  updates coords                         dwell >= 5min?
                                                              │
                                                    YES ──────┘
                                                    │
                                                    ▼
                                              Create Visit record
                                              (area_id via ST_Contains)
                                                    │
                                                    ▼
                                              Return confirmed_visits[]
                                                    │
                                                    ▼
                                              App invalidates:
                                              journal, stats, achievements,
                                              heatmap, passport caches
```

**Scenario: Token Refresh on 401**

```
API request ──► Axios interceptor adds Bearer token ──► Backend returns 401
                                                              │
                                                              ▼
                                                    Response interceptor:
                                                    1. Get refresh_token
                                                    2. POST /auth/refresh
                                                         │           │
                                                      SUCCESS      FAIL
                                                         │           │
                                                         ▼           ▼
                                                    Store new     Clear tokens
                                                    tokens +      Navigate to
                                                    retry         /auth/login
                                                    original
                                                    request
```

**Scenario: Map View Data Loading**

```
User opens Map tab
  ──► useLocationTracking() requests foreground permission
       │                            │
     GRANTED                     DENIED
       │                            │
       ▼                            ▼
  watchPositionAsync(15s)      Show guidance message
  locationStore.setLocation    Center on default location
  POST /visits/ping each tick
       │
       ▼
  useNearbyPlaces(lat, lon, radius, category)
       │
       ▼
  GET /places/nearby ──► Render PlacePin components
                         (colored by busyness level)
       │
  User taps pin ──► BottomSheet opens (PlaceSummarySheet)
       │
  "View Details" ──► router.push(/place/{id})
```

---

### Architecture Decisions

#### Polygon Overlays vs Heatmap for Exploration Map

**Status**: Accepted

**Context**: The exploration map needs to show visited vs unvisited neighborhoods with per-city progress percentages.

**Options**:
1. react-native-maps Heatmap component (density-based heat visualization)
2. react-native-maps Geojson/Polygon overlays (per-neighborhood colored fills)
3. Custom SVG overlay on top of MapView

**Decision**: Use Geojson/Polygon overlays (Option 2).

**Consequences**:
- Each neighborhood is individually addressable as visited/unvisited (required for stamps and progress %)
- Works on both iOS Apple Maps and Android Google Maps (Heatmap is Google-only)
- Backend must serve area boundary GeoJSON (Area.boundary is already PostGIS POLYGON)
- Rendering many polygons may need optimization if cities have 100+ neighborhoods

#### On-Device vs Backend Photo Storage for Journal

**Status**: Accepted

**Context**: Journal entries support optional photos, but no backend file storage (S3/pre-signed URLs) is specified in scope.

**Options**:
1. Upload photos to backend (requires S3 or equivalent)
2. Store photos on-device only (expo-file-system + AsyncStorage reference)
3. Defer photo feature entirely

**Decision**: Store photos on-device only (Option 2).

**Consequences**:
- Photos are lost if app is uninstalled or user switches devices
- No backend complexity for file upload/storage
- Text notes ARE persisted to backend via POST /journal/{visit_id}/note
- Can upgrade to backend storage later without changing the UI layer

#### Busyness Color Palette Design

**Status**: Accepted

**Context**: Busyness colors must be distinguishable by colorblind users (protanopia, deuteranopia).

**Options**:
1. Standard red/yellow/green only
2. Colorblind-safe palette with text label supplements
3. Shape-based differentiation only (no color)

**Decision**: Use a colorblind-safe palette supplemented by labels and distinct pin shapes (Option 2).

**Consequences**:
- Colors: `#22c55e` (green/quiet), `#eab308` (yellow/moderate), `#ef4444` (red/busy), `#9ca3af` (grey/no data) -- supplemented with text labels ("Quiet", "Moderate", "Busy") on the summary sheet and pin callouts
- Pin shapes vary by busyness level for additional non-color differentiation
- Meets accessibility acceptance criteria for protanopia and deuteranopia

---

### High-Level Structure

```
Mappn Utility App
├── Entry Point: app/_layout.tsx (auth gate + providers)
├── Auth Flow: (auth)/ group (login, register)
├── Main Navigation: (tabs)/ bottom bar
│   ├── Map Tab: Busyness map + pin interaction
│   ├── Explore Tab: Heatmap + city progress
│   ├── Journal Tab: Visit timeline
│   └── Profile Tab: Stats + achievements
├── Detail Screens:
│   ├── place/[id].tsx: Histogram + forecast
│   ├── journal/[visitId].tsx: Note + photo edit
│   └── passport/[city].tsx: Stamps + progress
├── Core Logic:
│   ├── services/: API communication layer
│   ├── hooks/: TanStack Query data hooks
│   └── stores/: Zustand client state
├── Data Layer:
│   ├── Backend API: 15 endpoints consumed
│   ├── expo-secure-store: JWT tokens
│   └── AsyncStorage: Local journal photos
└── Background: GPS tracking (foreground-only, 15s interval)
```

---

### Workflow Steps

```
Phase 0: Backend Fix          Phase 1: Backend Endpoints     Phase 2: Expo Scaffold
(area_id ST_Contains)    ──►  (6 new endpoints + tests)      (project init + deps)
         │                           │                              │
         └───────────────────────────┼──────────────────────────────┘
                                     │
                               Phase 3: Core Infra
                               (api.ts, auth store,
                                location store, UI kit)
                                     │
                               Phase 4: Auth Flow
                               (login, register screens)
                                     │
                    ┌────────────────┼────────────────┐
                    ▼                ▼                 ▼
             Phase 5: Map     Phase 7: Journal   Phase 9: Profile
             (pins, filter,   (timeline, notes,  (stats, badges,
              GPS tracking,    photos)            passports)
              bottom sheet)
                    │
                    ▼
             Phase 6: Place     Phase 8: Explore
             Detail             (polygon heatmap,
             (histogram,         city progress,
              forecast)          share image)
                    │
                    └────────────────┐
                                     ▼
                               Phase 10: Polish
                               (empty states, errors,
                                connectivity, a11y)
```

**Phase dependencies:**
- Phase 0 -> Phase 1 (area_id fix enables heatmap/passport queries)
- Phase 2 runs in parallel with Phases 0-1
- Phase 3 depends on Phase 2
- Phase 4 depends on Phase 3
- Phases 5, 7, 9 depend on Phase 4 (can run in parallel)
- Phase 6 depends on Phase 5
- Phase 8 depends on Phase 5 + Phase 1
- Phase 10 depends on all prior phases

---

### Contracts

**New Backend API Contracts:**

```
GET /users/me/stats (auth required)
Response: {
  places_count: int,
  cities_count: int,
  countries_count: int,
  total_duration_seconds: int
}

GET /users/me/achievements (auth required)
Response: [{
  id: str,
  name: str,
  description: str,
  category: str,          // "explorer" | "habits" | "categories"
  progress: int,
  threshold: int,
  earned: bool,
  earned_at: datetime | null
}]

GET /journal?limit=20&offset=0 (auth required)
Response: [{
  visit_id: int,
  place_id: int,
  place_name: str,
  area_id: int | null,
  city: str | null,
  started_at: datetime,
  duration_seconds: int,
  note: str | null,
  photo_url: str | null
}]

POST /journal/{visit_id}/note (auth required)
Request: { text: str (max 1000), photo_url: str | null }
Response: JournalEntryResponse (same shape as GET /journal entry)

GET /explore/heatmap?city=Lyon (auth required)
Response: {
  areas: [{
    id: int,
    name: str,
    city: str,
    boundary_geojson: GeoJSON FeatureCollection,
    visited: bool,
    visited_at: datetime | null
  }],
  total_areas: int,
  visited_areas: int,
  explored_pct: float
}

GET /passports?city=Lyon (auth required)
Response: {
  city: str,
  total_neighborhoods: int,
  visited_count: int,
  stamps: [{ area_id: int, name: str, visited_at: datetime }],
  badge_earned: bool,
  explored_pct: float
}
```

**Existing Backend API Contracts (consumed as-is):**

```
POST /auth/register   -> { access_token, refresh_token, token_type, expires_in }
POST /auth/login      -> { access_token, refresh_token, token_type, expires_in }
POST /auth/refresh    -> { access_token, refresh_token, token_type, expires_in }
GET  /auth/me         -> { id, username, email }
GET  /places/nearby   -> [{ id, name, category, lat, lon, address, current_busyness, busyness_stale, busyness_updated_at }]
GET  /places/{id}     -> { id, name, category, lat, lon, address, city, country, busyness_data, busyness_updated_at, busyness_stale }
GET  /places/{id}/forecast -> { place_id, day, hour, predicted_busyness, data_stale }
POST /visits/ping     -> { nearby_places, confirmed_visits, rejected, rejection_reason }
GET  /visits/history  -> [{ id, place_id, place_name, area_id, started_at, ended_at, duration_seconds }]
```

**Key TypeScript Interface (utility/types/api.ts):**

```typescript
interface BusynessData {
  popular_times: Array<{ day: number; hours: number[] }>; // day: 0=Mon..6=Sun, hours: 24 values 0-100
  current_popularity?: number;                             // 0-100, present only when live data available
  time_spent?: [number, number];                           // [min, max] minutes
}
```

**busyness_data note:** The `popular_times` array uses `day: 0` for Monday through `day: 6` for Sunday. Each `hours` array contains exactly 24 integer values (0-100) representing hourly busyness. The BusynessHistogram component must render these 24 bars for the selected day, with the day selector cycling 0-6.

---

## Implementation Process

You MUST launch for each step a separate agent, instead of performing all steps yourself. And for each step marked as parallel, you MUST launch separate agents in parallel.

**CRITICAL:** For each agent you MUST:
1. Use the **Agent** type specified in the step (e.g., `haiku`, `sonnet`, `sdd:developer`)
2. Provide path to task file and prompt which step to implement
3. Require agent to implement exactly that step, not more, not less, not other steps

### Parallelization Overview

```
  Step 1 [sdd:developer]    Step 2 [sdd:developer]    Step 5 [sdd:developer]
  (area_id fix)              (Model+schemas)            (Expo scaffold)
  Depends: None              Depends: None              Depends: None
       │                          │                          │
       └──────────┬───────────────┘                          │
                  ▼                                          ▼
             Step 3 [sdd:developer]                 Step 6 [sdd:developer]
             (Service functions)                    (Types, API client, stores,
             Depends: 1, 2                           utilityService)
                  │                                  Depends: 5
                  ▼                                          │
             Step 4 [sdd:developer]                          ▼
             (Router + tests)                       Step 7 [sdd:developer]
             Depends: 3                             (UI components)
                  │                                  Depends: 6
                  │                                          │
                  │                                          ▼
                  │                                 Step 8 [sdd:developer]
                  │                                 (Auth flow)
                  │                                  Depends: 6, 7
                  │                                          │
                  │                    ┌─────────────────────┼──────────────────────┐
                  │                    │                     │                      │
                  │                    │                     ▼                      │
                  │                    │             Step 9 [sdd:developer]         │
                  │                    │             (Map screen)                   │
                  │                    │              Depends: 8                    │
                  │                    │                │          │                │
                  │                    │                ▼          ▼                │
                  │                    │          Step 10     Step 14               │
                  │                    │        [sdd:developer] [sdd:developer]     │
                  │                    │       (Place detail) (GPS ping)            │
                  │                    │        Depends: 9    Depends: 9            │
                  │                    │                │          │                │
                  ├────────────────────┼────────────────┼──────────┼────────────────┤
                  │                    │                │          │                │
                  ▼                    ▼                │          │                ▼
             Step 11            Step 12                │          │           Step 13
           [sdd:developer]    [sdd:developer]          │          │         [sdd:developer]
           (Explore map)      (Journal)                │          │         (Profile+Passports)
            Depends: 8, 4      Depends: 8, 4, 6       │          │          Depends: 8, 4, 6
                  │                    │                │          │                │
                  └────────────────────┴────────────────┴──────────┴────────────────┘
                                                       │
                                                       ▼
                                                  Step 15 [sdd:developer]
                                                  (Polish)
                                                   Depends: 9, 10, 11, 12, 13, 14
```

**Key parallelization points:**
- **Level 0 (3 parallel):** Steps 1, 2, 5 MUST start simultaneously -- no dependencies
- **Level 1 (2 parallel):** Step 3 (after 1+2) and Step 6 (after 5) MUST run in parallel
- **Level 2 (2 parallel):** Step 4 (after 3) and Step 7 (after 6) MUST run in parallel
- **Level 3:** Step 8 (after 6+7) -- frontend auth flow
- **Level 4 (up to 4 parallel):** Step 9 (after 8), Steps 11, 12, 13 (after 8+4) MUST run in parallel once all dependencies are met
- **Level 5 (2 parallel):** Steps 10, 14 (after 9) MUST run in parallel
- **Level 6:** Step 15 (after all screens completed)

### Implementation Strategy

**Approach**: Mixed (Bottom-Up for backend, Top-Down for frontend)

**Rationale**: The backend requires a Bottom-Up approach because models, migrations, and service functions must be solid before the API router layer can expose them. The frontend uses a Top-Down approach because the navigation workflow is clear (auth gate then tabs then screens), so we start with root layout and navigation structure, then implement each screen and its components. Infrastructure layers (API client, stores, types) are built Bottom-Up within the frontend as foundational blocks.

### Phase Overview

```
Phase 1: Backend Foundations (area_id fix, JournalNote model, migration)
    │
    ▼
Phase 2: Backend Utility Endpoints (schemas, service, router, tests)
    │                                          ┌──────────────────────────┐
    │                                          │ Phase 3: Expo Scaffold   │
    │                                          │ (runs parallel with 1-2) │
    │                                          └──────────┬───────────────┘
    ▼                                                     ▼
Phase 4: Frontend Core Infrastructure (types, api.ts, stores, UI kit)
    │
    ▼
Phase 5: Auth Flow (auth service, auth screens, root layout)
    │
    ▼
Phase 6: Map Screen (tabs, location tracking, pins, filter, bottom sheet)
    │
    ├───────────────────────┬──────────────────────────────┐
    ▼                       ▼                              ▼
Phase 7: Place Detail   Phase 8: Explore + Journal     Phase 9: Profile
(histogram, forecast)   (heatmap, timeline, notes)     (stats, achievements,
    │                       │                           passports)
    └───────────────────────┼──────────────────────────────┘
                            ▼
                     Phase 10: Polish
                     (empty states, errors, GPS,
                      network banner, accessibility)
```

---

### Step 1: Fix area_id Assignment in visit_service.py [DONE]

**Model:** opus
**Agent:** sdd:developer
**Depends on:** None
**Parallel with:** Step 2, Step 5

**Goal**: Replace the area_id stub in `visit_service.py` with a PostGIS `ST_Contains` query so that confirmed visits are assigned to the correct geographic area. This is a blocking prerequisite for the heatmap and city passport features.

**Phase**: 1 - Backend Foundations
**Complexity**: Small

#### Expected Output

- `backend/app/services/visit_service.py`: Updated `auto_confirm_visit()` function (lines 232-241) with ST_Contains query

#### Success Criteria

- [X] The `auto_confirm_visit()` function queries the `areas` table using `ST_Contains(Area.boundary, place_point)` to find the area containing the place
- [X] When a place falls within an area boundary, the visit record is created with the correct `area_id`
- [X] When a place does not fall within any area boundary, the visit record is created with `area_id = None`
- [X] Existing backend tests continue to pass after the change

#### Verification

**Level:** CRITICAL - Panel of 2 Judges with Aggregated Voting
**Artifact:** `backend/app/services/visit_service.py`
**Threshold:** 4.0/5.0

**Rubric:**

| Criterion | Weight | Description |
|-----------|--------|-------------|
| Query Correctness | 0.35 | ST_Contains query correctly finds the area containing the place's coordinates using proper PostGIS function syntax |
| Null Handling | 0.25 | When no area contains the place, area_id is set to None without raising an error |
| Integration Safety | 0.20 | Existing auto_confirm_visit() flow is preserved; imports are correct; no regressions to existing tests |
| Code Quality | 0.20 | Follows project patterns from visit_service.py; async SQLAlchemy select() pattern used correctly |

**Reference Pattern:** `backend/app/services/visit_service.py` (existing code in same file)

#### Subtasks

- [X] Read `backend/app/services/visit_service.py` lines 232-241 to understand the current stub
- [X] Read `backend/app/models/area.py` to confirm Area.boundary is Geography POLYGON with SRID 4326
- [X] Replace the stub at lines 232-241 with a `select(Area.id).where(ST_Contains(Area.boundary, place_point))` query using the Place's coordinates
- [X] Import `ST_Contains` from `geoalchemy2.functions` and `Area` from models
- [X] Run existing backend tests to verify no regressions: `pytest backend/tests/`

---

### Step 2: Create JournalNote Model, Migration, and Utility Schemas [DONE]

**Model:** opus
**Agent:** sdd:developer
**Depends on:** None
**Parallel with:** Step 1, Step 5

**Goal**: Add the JournalNote ORM model and database migration, then create all Pydantic schemas needed by the utility endpoints. This establishes the data layer foundation for the utility API.

**Phase**: 1 - Backend Foundations
**Complexity**: Medium

#### Expected Output

- `backend/app/models/journal.py`: JournalNote ORM model
- `backend/app/models/__init__.py`: Updated with JournalNote import
- `backend/alembic/versions/002_utility_schema.py`: Migration creating `journal_notes` table
- `backend/app/schemas/utility.py`: All utility Pydantic schemas

#### Success Criteria

- [ ] `JournalNote` model has columns: `id` (PK), `visit_id` (FK visits.id), `user_id` (FK users.id), `text` (nullable, max 1000), `photo_url` (nullable), `created_at` (DateTime with timezone)
- [ ] `JournalNote` is imported and re-exported in `backend/app/models/__init__.py` and added to `__all__`
- [ ] Migration `002_utility_schema.py` creates `journal_notes` table with appropriate columns, FKs, and indexes
- [ ] Migration depends on `001_initial_schema` revision
- [ ] Pydantic schemas created: `UserStatsResponse`, `AchievementResponse`, `JournalEntryResponse`, `JournalNoteRequest`, `HeatmapAreaResponse`, `HeatmapResponse`, `PassportStampResponse`, `CityPassportResponse`
- [ ] All schemas use `ConfigDict(from_attributes=True)` where applicable
- [ ] `JournalNoteRequest` validates text max length of 1000 characters
- [ ] Migration runs successfully: `alembic upgrade head`

#### Verification

**Level:** CRITICAL - Panel of 2 Judges with Aggregated Voting
**Artifact:** `backend/app/models/journal.py`, `backend/app/models/__init__.py`, `backend/alembic/versions/002_utility_schema.py`, `backend/app/schemas/utility.py`
**Threshold:** 4.0/5.0

**Rubric:**

| Criterion | Weight | Description |
|-----------|--------|-------------|
| Model Correctness | 0.25 | JournalNote ORM model has all required columns (id PK, visit_id FK, user_id FK, text, photo_url, created_at) with proper types and constraints |
| Migration Safety | 0.25 | Migration creates journal_notes table with correct columns, FK constraints, indexes; depends on 001_initial_schema; reversible |
| Schema Completeness | 0.25 | All 8 Pydantic schemas defined with correct fields, types, ConfigDict(from_attributes=True), and JournalNoteRequest text max_length=1000 |
| Pattern Consistency | 0.15 | Follows existing patterns from visit.py model and place.py schemas |
| Module Integration | 0.10 | JournalNote properly imported/exported in models/__init__.py and added to __all__ |

**Reference Pattern:** `backend/app/models/visit.py` (model pattern), `backend/app/schemas/place.py` (schema pattern)

#### Subtasks

- [X] Create `backend/app/models/journal.py` with JournalNote class following the pattern in `backend/app/models/visit.py`
- [X] Update `backend/app/models/__init__.py` to import JournalNote and add to `__all__`
- [X] Create `backend/alembic/versions/002_utility_schema.py` migration with `op.create_table("journal_notes", ...)` including FK constraints and index on `(user_id, visit_id)`
- [X] Create `backend/app/schemas/utility.py` with all 8 Pydantic schema classes, following patterns from `backend/app/schemas/place.py`
- [ ] Verify migration applies cleanly on a fresh database

---

### Step 3: Implement Utility Service Functions [DONE]

**Model:** opus
**Agent:** sdd:developer
**Depends on:** Step 1, Step 2
**Parallel with:** Step 6

**Goal**: Create the 6 async service functions that implement the business logic for stats, achievements, journal, heatmap, and passport features. These functions query the database and return structured data consumed by the API router.

**Phase**: 2 - Backend Utility Endpoints
**Complexity**: Large

#### Expected Output

- `backend/app/services/utility_service.py`: 6 async service functions

#### Success Criteria

- [ ] `get_user_stats(db, user_id)` returns dict with `places_count`, `cities_count`, `countries_count`, `total_duration_seconds` by querying Visit JOIN Place
- [ ] `get_user_achievements(db, user_id)` returns list of 6 achievement dicts, each with `id`, `name`, `description`, `category`, `progress`, `threshold`, `earned`, `earned_at` -- computed from visit history
- [ ] Achievement criteria match spec: Wanderer (10 distinct area_ids), Globe Trotter (5 distinct cities), Night Owl (10 visits after midnight), Early Bird (10 visits before 7am), Foodie (50 restaurant visits), Culture Vulture (20 museum visits)
- [ ] `get_journal_entries(db, user_id, limit, offset)` returns paginated list of journal entries with Visit JOIN Place LEFT JOIN JournalNote
- [ ] `add_journal_note(db, user_id, visit_id, text, photo_url)` upserts a JournalNote record and returns the updated journal entry
- [ ] `get_heatmap(db, user_id, city)` returns areas with visited flag, boundary GeoJSON, and exploration percentage
- [ ] `get_city_passport(db, user_id, city)` returns neighborhood stamps, visited count, total count, badge earned status, and exploration percentage
- [ ] All functions use async SQLAlchemy with `select()`, `join()`, `where()` following the pattern in `backend/app/services/visit_service.py`

#### Verification

**Level:** CRITICAL - Panel of 2 Judges with Aggregated Voting
**Artifact:** `backend/app/services/utility_service.py`
**Threshold:** 4.0/5.0

**Rubric:**

| Criterion | Weight | Description |
|-----------|--------|-------------|
| Query Correctness | 0.30 | All 6 functions produce correct SQL queries: stats aggregation, achievement counting (6 distinct criteria), journal pagination with JOIN, heatmap with boundary GeoJSON, passport stamps |
| Achievement Logic | 0.25 | All 6 achievement definitions match spec exactly: Wanderer=10 neighborhoods, Globe Trotter=5 cities, Night Owl=10 after midnight, Early Bird=10 before 7am, Foodie=50 restaurants, Culture Vulture=20 museums |
| Async Pattern | 0.15 | All functions are async, use select()/join()/where() pattern following visit_service.py conventions |
| Error Handling | 0.15 | Functions handle edge cases: zero visits, missing area_id, nonexistent visit_id for journal note |
| Return Types | 0.15 | Return shapes match the Pydantic schemas from Step 2 (UserStatsResponse, AchievementResponse, etc.) |

**Reference Pattern:** `backend/app/services/visit_service.py` (async SQLAlchemy query pattern)

#### Subtasks

- [X] Create `backend/app/services/utility_service.py` with module docstring
- [X] Implement `get_user_stats()` with COUNT DISTINCT on places, cities, countries from Visit JOIN Place
- [X] Implement `get_user_achievements()` with 6 achievement definitions and progress counting queries
- [X] Implement `get_journal_entries()` with Visit JOIN Place LEFT JOIN JournalNote, ordered by started_at DESC, with limit/offset pagination
- [X] Implement `add_journal_note()` with upsert logic (check if JournalNote exists for visit_id+user_id, create or update)
- [X] Implement `get_heatmap()` with Area query filtered by city, LEFT JOIN with Visit to determine visited status, returning GeoJSON from ST_AsGeoJSON(boundary)
- [X] Implement `get_city_passport()` with Area query for city, stamp status per neighborhood, badge_earned when all are visited

---

### Step 4: Create Utility API Router and Backend Tests [DONE]

**Model:** opus
**Agent:** sdd:developer
**Depends on:** Step 3
**Parallel with:** Step 7

**Goal**: Create the FastAPI router exposing 6 utility endpoints, register it in main.py and test conftest, and write integration tests for all endpoints.

**Phase**: 2 - Backend Utility Endpoints
**Complexity**: Large

#### Expected Output

- `backend/app/api/utility.py`: Router with 6 endpoints
- `backend/app/main.py`: Updated with utility_router registration
- `backend/tests/conftest.py`: Updated with utility_router in test app
- `backend/tests/test_utility.py`: Integration tests for all 6 endpoints

#### Success Criteria

- [X] Router defines: `GET /users/me/stats`, `GET /users/me/achievements`, `GET /journal`, `POST /journal/{visit_id}/note`, `GET /explore/heatmap`, `GET /passports`
- [X] All endpoints require authentication via `Depends(get_current_user)`
- [X] All endpoints use `Depends(get_db)` for database access
- [X] Each endpoint has correct `response_model` from utility schemas
- [X] Router is registered in `backend/app/main.py` after existing routers (line ~151)
- [X] Router is registered in `backend/tests/conftest.py` `_create_test_app()` function
- [X] Tests cover: stats with 0 visits, stats with multiple visits, achievements progress at various levels, journal pagination, journal note creation, heatmap with/without city filter, passport with partial/full completion
- [X] All tests pass: `pytest backend/tests/test_utility.py`

#### Verification

**Level:** CRITICAL - Panel of 2 Judges with Aggregated Voting
**Artifact:** `backend/app/api/utility.py`, `backend/app/main.py`, `backend/tests/conftest.py`, `backend/tests/test_utility.py`
**Threshold:** 4.0/5.0

**Rubric:**

| Criterion | Weight | Description |
|-----------|--------|-------------|
| Contract Correctness | 0.25 | All 6 endpoints have correct paths, methods, query params, and response_model matching the API contracts defined in the task Contracts section |
| Authentication | 0.20 | All endpoints use Depends(get_current_user) and Depends(get_db) correctly |
| Test Coverage | 0.25 | Tests cover: stats with 0/multiple visits, achievement progress levels, journal pagination, note creation, heatmap with/without city, passport partial/full completion |
| Registration | 0.15 | Router registered in main.py and tests/conftest.py correctly |
| Consistency | 0.15 | Follows patterns from existing places.py router; tags, error handling, response codes |

**Reference Pattern:** `backend/app/api/places.py` (router pattern), `backend/tests/test_places.py` (test pattern)

#### Subtasks

- [X] Create `backend/app/api/utility.py` with `APIRouter(tags=["utility"])` and 6 endpoint functions following pattern from `backend/app/api/places.py`
- [X] Implement GET `/users/me/stats` endpoint calling `get_user_stats`
- [X] Implement GET `/users/me/achievements` endpoint calling `get_user_achievements`
- [X] Implement GET `/journal` endpoint with `limit` and `offset` query params calling `get_journal_entries`
- [X] Implement POST `/journal/{visit_id}/note` endpoint with `JournalNoteRequest` body calling `add_journal_note`
- [X] Implement GET `/explore/heatmap` endpoint with optional `city` query param calling `get_heatmap`
- [X] Implement GET `/passports` endpoint with required `city` query param calling `get_city_passport`
- [X] Update `backend/app/main.py` line ~151: add `from app.api.utility import router as utility_router` and `app.include_router(utility_router)`
- [X] Update `backend/tests/conftest.py` `_create_test_app()`: add utility_router registration
- [X] Create `backend/tests/test_utility.py` with test fixtures (test visits, test places in areas) and tests for each endpoint
- [X] Run full test suite: `pytest backend/tests/`

---

### Step 5: Create Expo Project Scaffold [DONE]

**Model:** opus
**Agent:** sdd:developer
**Depends on:** None
**Parallel with:** Step 1, Step 2

**Goal**: Initialize the Expo SDK 52 project in the `utility/` directory with all required dependencies, configuration files, and directory structure. This creates the foundation for all frontend development.

**Phase**: 3 - Expo Scaffold (parallel with Steps 1-4)
**Complexity**: Medium

#### Expected Output

- `utility/` directory with complete Expo project structure
- `utility/package.json`: All dependencies installed
- `utility/app.config.ts`: Expo config with plugins for maps, location, image-picker
- `utility/tsconfig.json`: TypeScript configuration
- `utility/eas.json`: EAS build profiles
- Empty directory structure: `app/`, `components/`, `services/`, `stores/`, `hooks/`, `types/`, `constants/`

#### Success Criteria

- [X] `npx create-expo-app` creates the project in `utility/` with tabs template
- [X] All dependencies from the skill file are installed: react-native-maps, expo-location, @tanstack/react-query, zustand, axios, expo-secure-store, expo-image-picker, expo-image, expo-sharing, react-native-view-shot, @gorhom/bottom-sheet, react-native-gifted-charts, react-native-map-clustering, @react-native-async-storage/async-storage
- [X] `app.config.ts` configures react-native-maps (via android.config.googleMaps), expo-location plugin, expo-image-picker plugin with permission strings (Note: react-native-maps v1.20.1 does not ship a config plugin; Google Maps API key configured via android.config.googleMaps.apiKey instead)
- [X] `eas.json` has development, preview, and production build profiles
- [X] `tsconfig.json` has strict mode enabled
- [X] Project compiles without errors: `npx expo start` launches successfully
- [X] Directory structure created: `app/(auth)/`, `app/(tabs)/`, `app/place/`, `app/journal/`, `app/passport/`, `components/map/`, `components/place/`, `components/explore/`, `components/journal/`, `components/profile/`, `components/ui/`, `services/`, `stores/`, `hooks/`, `types/`, `constants/`

#### Verification

**Level:** Single Judge
**Artifact:** `utility/` directory (project scaffold)
**Threshold:** 4.0/5.0

**Rubric:**

| Criterion | Weight | Description |
|-----------|--------|-------------|
| Dependency Completeness | 0.30 | All required dependencies installed: react-native-maps, expo-location, @tanstack/react-query@5, zustand, axios, expo-secure-store, expo-image-picker, expo-image, expo-sharing, react-native-view-shot, @gorhom/bottom-sheet, react-native-gifted-charts, react-native-map-clustering, @react-native-async-storage/async-storage |
| Config Correctness | 0.25 | app.config.ts has correct plugins for maps, location, image-picker with permission strings; tsconfig strict mode; eas.json build profiles |
| Directory Structure | 0.20 | All required directories created: app/(auth)/, app/(tabs)/, app/place/, app/journal/, app/passport/, components/{map,place,explore,journal,profile,ui}/, services/, stores/, hooks/, types/, constants/ |
| Project Viability | 0.15 | Project compiles and starts without errors |
| Consistency | 0.10 | Follows skill file patterns for Expo SDK 52 project setup |

**Reference Pattern:** `.claude/skills/react-native-expo-mobile-app/SKILL.md` (skill file project setup pattern)

#### Subtasks

- [X] Run `npx create-expo-app@latest utility --template tabs` from the monorepo root
- [X] Install map and location dependencies: `npx expo install react-native-maps expo-location`
- [X] Install state management: `npm install @tanstack/react-query@5 zustand axios`
- [X] Install storage: `npx expo install @react-native-async-storage/async-storage expo-secure-store`
- [X] Install UI and media: `npx expo install expo-image expo-image-picker expo-sharing && npm install react-native-view-shot @gorhom/bottom-sheet react-native-gifted-charts react-native-map-clustering`
- [X] Create `utility/app.config.ts` with plugins configuration following skill file pattern
- [X] Create `utility/eas.json` with build profiles following skill file pattern
- [X] Create empty directory structure for all feature folders
- [X] Clean up template files not needed (remove default tab screens content)
- [X] Verify project starts: `cd utility && npx expo start`

---

### Step 6: Create TypeScript Types, Constants, API Client, and Utility Service [DONE]

**Model:** opus
**Agent:** sdd:developer
**Depends on:** Step 5
**Parallel with:** Step 3

**Goal**: Build the frontend data layer foundation: TypeScript types mirroring all backend schemas, app constants (colors, config, achievement definitions), the Axios API client with auth token injection and 401 refresh interceptor, the auth Zustand store with SecureStore persistence, and the utility service API client functions.

**Phase**: 4 - Frontend Core Infrastructure
**Complexity**: Medium

**Note**: This step includes `utilityService.ts` (moved here from the original Exploration Map step) because it is a shared API client dependency consumed by Steps 11, 12, and 13. Creating it here enables those three steps to run in parallel.

#### Expected Output

- `utility/types/api.ts`: All TypeScript interfaces mirroring backend response shapes
- `utility/constants/colors.ts`: Busyness color palette and theme colors
- `utility/constants/config.ts`: API URL, GPS tracking interval, stale times
- `utility/constants/achievements.ts`: Achievement definitions (id, name, description, category, threshold)
- `utility/services/api.ts`: Axios instance with request interceptor (token injection) and response interceptor (401 refresh + retry)
- `utility/stores/authStore.ts`: Zustand store for auth state with SecureStore persistence
- `utility/services/utilityService.ts`: getUserStats(), getAchievements(), getJournal(), addJournalNote(), getHeatmap(), getCityPassport()

#### Success Criteria

- [X] `types/api.ts` defines: `PlaceResponse`, `PlaceDetailResponse`, `BusynessData`, `ForecastResponse`, `GPSPingResponse`, `VisitResponse`, `UserStatsResponse`, `AchievementResponse`, `JournalEntryResponse`, `HeatmapAreaResponse`, `HeatmapResponse`, `CityPassportResponse`, `AuthTokenResponse`, `UserResponse`
- [X] `BusynessData` type matches: `{ popular_times: Array<{ day: number; hours: number[] }>; current_popularity?: number; time_spent?: [number, number] }`
- [X] `constants/colors.ts` exports `BUSYNESS_COLORS`: quiet `#22c55e`, moderate `#eab308`, busy `#ef4444`, noData `#9ca3af`
- [X] `constants/config.ts` exports `API_BASE_URL` from env var `EXPO_PUBLIC_API_URL`, `GPS_INTERVAL_MS` = 15000, query stale times
- [X] `constants/achievements.ts` exports 6 achievement definitions matching the spec
- [X] `api.ts` creates Axios instance with `baseURL` from config, request interceptor reads access_token from SecureStore, response interceptor catches 401 and attempts refresh via POST /auth/refresh, on refresh success retries original request, on refresh failure clears tokens and navigates to login
- [X] `authStore.ts` provides: `user`, `isAuthenticated`, `accessToken`, `refreshToken`, `setTokens()`, `clearAuth()`, `loadTokens()` (from SecureStore on app start), `setUser()`
- [X] Tokens are stored in and read from `expo-secure-store` (not AsyncStorage)
- [X] `utilityService.ts` implements all 6 utility API functions (getUserStats, getAchievements, getJournal, addJournalNote, getHeatmap, getCityPassport)

#### Verification

**Level:** CRITICAL - Panel of 2 Judges with Aggregated Voting
**Artifact:** `utility/types/api.ts`, `utility/constants/colors.ts`, `utility/constants/config.ts`, `utility/constants/achievements.ts`, `utility/services/api.ts`, `utility/stores/authStore.ts`, `utility/services/utilityService.ts`
**Threshold:** 4.0/5.0

**Rubric:**

| Criterion | Weight | Description |
|-----------|--------|-------------|
| Type Fidelity | 0.20 | All TypeScript interfaces exactly match backend API response shapes from Contracts section; BusynessData type includes popular_times, current_popularity, time_spent with correct types |
| Auth Security | 0.25 | Tokens stored in expo-secure-store (NOT AsyncStorage); interceptor reads from SecureStore; refresh logic on 401 is correct with retry |
| Interceptor Logic | 0.20 | Request interceptor injects Bearer token; response interceptor catches 401, attempts refresh, retries original request on success, clears auth and redirects on failure |
| Store Completeness | 0.15 | authStore has all required fields and methods: user, isAuthenticated, accessToken, refreshToken, setTokens(), clearAuth(), loadTokens(), setUser() |
| Service Functions | 0.20 | utilityService.ts implements all 6 functions (getUserStats, getAchievements, getJournal, addJournalNote, getHeatmap, getCityPassport) calling correct endpoints |

**Reference Pattern:** Contracts section of this task file (API response shapes)

#### Subtasks

- [X] Create `utility/types/api.ts` with all TypeScript interfaces matching backend contract shapes from the Contracts section
- [X] Create `utility/constants/colors.ts` with busyness color map and theme colors
- [X] Create `utility/constants/config.ts` with API URL, GPS interval, and staleTime constants
- [X] Create `utility/constants/achievements.ts` with achievement definition objects
- [X] Create `utility/stores/authStore.ts` using Zustand `create()` with SecureStore read/write for tokens
- [X] Create `utility/services/api.ts` with Axios instance, request interceptor for Bearer token injection, response interceptor for 401 handling with refresh + retry logic
- [X] Create `utility/services/utilityService.ts` with all 6 functions calling the API client
- [X] Add `.env.example` file with `EXPO_PUBLIC_API_URL=http://localhost:8000`

---

### Step 7: Build Shared UI Components [DONE]

**Model:** opus
**Agent:** sdd:developer
**Depends on:** Step 6
**Parallel with:** Step 4

**Goal**: Create the reusable UI component library used across all screens: buttons, cards, loading indicators, empty states, error boundaries, and network connectivity banner.

**Phase**: 4 - Frontend Core Infrastructure
**Complexity**: Medium

#### Expected Output

- `utility/components/ui/Button.tsx`: Button with loading state, variants (primary, secondary, text)
- `utility/components/ui/Card.tsx`: Card container with shadow and rounded corners
- `utility/components/ui/LoadingSpinner.tsx`: Centered ActivityIndicator with optional message
- `utility/components/ui/EmptyState.tsx`: Icon + title + description + optional CTA button
- `utility/components/ui/ErrorBoundary.tsx`: React error boundary with fallback UI
- `utility/components/ui/NetworkBanner.tsx`: Connectivity warning banner using NetInfo

#### Success Criteria

- [X] `Button` accepts `title`, `onPress`, `loading`, `disabled`, `variant` props and renders appropriately
- [X] `Card` wraps children with consistent padding, border radius, and shadow styling
- [X] `LoadingSpinner` renders a centered `ActivityIndicator` with optional `message` text
- [X] `EmptyState` renders an icon, title, description, and optional action button with consistent styling
- [X] `ErrorBoundary` catches JS errors in children, renders a fallback UI with retry option, and logs the error
- [X] `NetworkBanner` monitors network state and shows/hides a warning banner when connectivity is lost
- [X] All components use colors from `constants/colors.ts`

#### Verification

**Level:** Per-Component Judges (6 separate evaluations in parallel)
**Artifacts:** `utility/components/ui/{Button,Card,LoadingSpinner,EmptyState,ErrorBoundary,NetworkBanner}.tsx`
**Threshold:** 4.0/5.0

**Rubric (per component):**

| Criterion | Weight | Description |
|-----------|--------|-------------|
| Props Interface | 0.25 | Component accepts all required props as defined in Success Criteria; TypeScript types are correct |
| Visual Correctness | 0.30 | Component renders the correct UI elements (ActivityIndicator for spinner, icon+title+description for EmptyState, error boundary fallback, etc.) |
| Reusability | 0.20 | Component is generic enough to be used across multiple screens without modification |
| Theme Consistency | 0.15 | Uses colors from constants/colors.ts; follows consistent styling patterns |
| Edge Cases | 0.10 | Handles optional props, undefined values, and loading states appropriately |

#### Subtasks

- [X] Create `utility/components/ui/Button.tsx` with loading state and variant support
- [X] Create `utility/components/ui/Card.tsx` as a styled container component
- [X] Create `utility/components/ui/LoadingSpinner.tsx` with ActivityIndicator and message prop
- [X] Create `utility/components/ui/EmptyState.tsx` with icon (MaterialIcons), title, description, and action button
- [X] Create `utility/components/ui/ErrorBoundary.tsx` as a class component with componentDidCatch
- [X] Create `utility/components/ui/NetworkBanner.tsx` using `@react-native-community/netinfo` or expo NetInfo to monitor connectivity
- [X] Install `@react-native-community/netinfo` if not already included: `npx expo install @react-native-community/netinfo` (already installed)

---

### Step 8: Implement Auth Flow (Service, Screens, Root Layout) [DONE]

**Model:** opus
**Agent:** sdd:developer
**Depends on:** Step 6, Step 7
**Parallel with:** None

**Goal**: Build the complete authentication flow: auth service functions (login, register, refresh, logout), location and map Zustand stores, the root layout with provider setup and auth gate, and the login/register screens.

**Phase**: 5 - Auth Flow
**Complexity**: Large

#### Expected Output

- `utility/services/authService.ts`: login, register, refreshToken, logout functions
- `utility/stores/locationStore.ts`: Zustand store for GPS coordinates and accuracy
- `utility/stores/mapStore.ts`: Zustand store for map region and category filters
- `utility/app/_layout.tsx`: Root layout with QueryClientProvider, GestureHandlerRootView, auth gate logic
- `utility/app/(auth)/_layout.tsx`: Auth stack layout (no tab bar)
- `utility/app/(auth)/login.tsx`: Login screen with email/password form
- `utility/app/(auth)/register.tsx`: Register screen with email/username/password form

#### Success Criteria

- [X] `authService.login(email, password)` calls POST /auth/login and stores tokens via auth store
- [X] `authService.register(email, username, password)` calls POST /auth/register and stores tokens
- [X] `authService.refreshToken()` calls POST /auth/refresh with current refresh token
- [X] `authService.logout()` clears tokens from SecureStore and auth store
- [X] `locationStore` provides: `latitude`, `longitude`, `accuracy`, `isTracking`, `setLocation()`, `setTracking()`
- [X] `mapStore` provides: `region`, `selectedPlaceId`, `activeFilters`, `setRegion()`, `setSelectedPlace()`, `toggleFilter()`
- [X] Root layout wraps the app in `GestureHandlerRootView` and `QueryClientProvider`
- [X] Root layout checks SecureStore for existing tokens on mount and redirects accordingly: tokens valid -> (tabs), no tokens -> (auth)/login
- [X] Login screen has email and password fields with validation, error display, and link to register
- [X] Register screen has email, username, and password fields with validation, error display, and link to login
- [X] On successful login/register, user is navigated to (tabs)/ map view
- [X] Invalid credentials show a clear error message on the form
- [X] Session persistence works: closing and reopening app maintains authentication

#### Verification

**Level:** CRITICAL - Panel of 2 Judges with Aggregated Voting
**Artifact:** `utility/services/authService.ts`, `utility/stores/locationStore.ts`, `utility/stores/mapStore.ts`, `utility/app/_layout.tsx`, `utility/app/(auth)/_layout.tsx`, `utility/app/(auth)/login.tsx`, `utility/app/(auth)/register.tsx`
**Threshold:** 4.0/5.0

**Rubric:**

| Criterion | Weight | Description |
|-----------|--------|-------------|
| Auth Service Correctness | 0.25 | login, register, refreshToken, logout correctly call backend endpoints and manage tokens via authStore |
| Root Layout Gate | 0.25 | Root layout checks SecureStore on mount; redirects to (auth) or (tabs) based on token presence; wraps in QueryClientProvider and GestureHandlerRootView |
| Screen Functionality | 0.20 | Login and register screens have correct form fields, validation, error display, and navigation links between them |
| Session Persistence | 0.15 | Tokens persist in SecureStore across app launches; reopening app maintains authentication |
| Error Handling | 0.15 | Invalid credentials show clear error message; failed token refresh redirects to login |

**Reference Pattern:** `.claude/skills/react-native-expo-mobile-app/SKILL.md` (auth patterns)

#### Subtasks

- [X] Create `utility/services/authService.ts` with login(), register(), refreshToken(), logout() calling the API client
- [X] Create `utility/stores/locationStore.ts` with Zustand store for GPS state
- [X] Create `utility/stores/mapStore.ts` with Zustand store for map region and filters
- [X] Create `utility/app/_layout.tsx` as root layout with QueryClientProvider, GestureHandlerRootView, ErrorBoundary, and auth state checking on mount
- [X] Implement auth gate logic in root layout: redirect to (auth) or (tabs) based on token presence
- [X] Create `utility/app/(auth)/_layout.tsx` as a Stack layout without tab bar
- [X] Create `utility/app/(auth)/login.tsx` with form fields, validation, error handling, and register link
- [X] Create `utility/app/(auth)/register.tsx` with form fields, validation, error handling, and login link
- [X] Test auth flow: register -> lands on map, close app -> reopen -> stays on map, logout -> lands on login

---

### Step 9: Build Map Screen with Pins, Filters, and Bottom Sheet [DONE]

**Model:** opus
**Agent:** sdd:developer
**Depends on:** Step 8
**Parallel with:** Step 11, Step 12, Step 13 (if Step 4 is also complete)

**Goal**: Build the map tab (home screen) with busyness-colored pins, marker clustering, category filter pills, GPS location tracking, and the place summary bottom sheet that appears on pin tap.

**Phase**: 6 - Map Screen
**Complexity**: Large

#### Expected Output

- `utility/app/(tabs)/_layout.tsx`: Bottom tab bar with Map, Explore, Journal, Profile tabs
- `utility/app/(tabs)/index.tsx`: Map View screen (home tab)
- `utility/services/placesService.ts`: getNearbyPlaces(), getPlaceDetail(), getForecast()
- `utility/services/visitsService.ts`: postGpsPing(), getVisitHistory()
- `utility/services/locationService.ts`: startTracking(), stopTracking()
- `utility/hooks/useNearbyPlaces.ts`: TanStack Query hook for nearby places
- `utility/hooks/useLocationTracking.ts`: GPS tracking lifecycle hook
- `utility/components/map/PlacePin.tsx`: Busyness-colored marker component
- `utility/components/map/CategoryFilter.tsx`: Horizontal scrollable filter pills
- `utility/components/map/PlaceSummarySheet.tsx`: Bottom sheet with place preview and mini chart

#### Success Criteria

- [X] Tab layout shows 4 tabs with icons: Map (map icon), Explore (explore icon), Journal (book icon), Profile (person icon)
- [X] Active tab is visually highlighted
- [X] Map screen renders a full-screen MapView centered on user location (or default location if permission denied)
- [X] `useLocationTracking` hook requests foreground permission, starts `watchPositionAsync` with 15s interval, updates locationStore
- [X] When location permission is denied, a guidance message is shown and map centers on a default location
- [X] `useNearbyPlaces` hook fetches places from GET /places/nearby based on current map region
- [X] Place pins are rendered as colored markers: green (#22c55e) for quiet (0-33), yellow (#eab308) for moderate (34-66), red (#ef4444) for busy (67-100), grey (#9ca3af) for no data
- [X] All markers have `tracksViewChanges={false}` for performance
- [X] Markers are clustered when zoomed out using react-native-map-clustering
- [X] Category filter pills (All, Restaurant, Park, Cafe, Museum, etc.) filter visible pins
- [X] Tapping a pin opens a bottom sheet showing place name, current busyness level, and a mini popular times indicator for the current day
- [X] Bottom sheet has a "View Details" button that navigates to `/place/{id}`
- [X] Map maintains 30fps with 200 pins visible (via clustering + tracksViewChanges=false)

#### Verification

**Level:** CRITICAL - Panel of 2 Judges with Aggregated Voting
**Artifact:** `utility/app/(tabs)/_layout.tsx`, `utility/app/(tabs)/index.tsx`, `utility/services/placesService.ts`, `utility/services/visitsService.ts`, `utility/services/locationService.ts`, `utility/hooks/useNearbyPlaces.ts`, `utility/hooks/useLocationTracking.ts`, `utility/components/map/PlacePin.tsx`, `utility/components/map/CategoryFilter.tsx`, `utility/components/map/PlaceSummarySheet.tsx`
**Threshold:** 4.0/5.0

**Rubric:**

| Criterion | Weight | Description |
|-----------|--------|-------------|
| Map Rendering | 0.25 | Full-screen MapView centered on user location with clustered markers; tracksViewChanges={false} on all markers; react-native-map-clustering used |
| Pin Colors | 0.20 | Pins correctly colored: green (#22c55e) for 0-33, yellow (#eab308) for 34-66, red (#ef4444) for 67-100, grey (#9ca3af) for no data |
| Category Filtering | 0.15 | Filter pills correctly filter visible pins by category; "All" option shows all pins |
| Bottom Sheet | 0.15 | Tapping a pin opens bottom sheet with place name, busyness level, mini chart; "View Details" navigates to /place/{id} |
| Services and Hooks | 0.15 | placesService, visitsService, locationService, useNearbyPlaces, useLocationTracking all implemented correctly with proper query keys and stale times |
| Tab Navigation | 0.10 | 4 tabs (Map, Explore, Journal, Profile) with icons; active tab highlighted |

**Reference Pattern:** `.claude/skills/react-native-expo-mobile-app/SKILL.md` (map and navigation patterns)

#### Subtasks

- [X] Create `utility/app/(tabs)/_layout.tsx` with Tabs component and 4 tab screens with MaterialIcons
- [X] Create `utility/services/placesService.ts` with getNearbyPlaces(lat, lon, radius, category), getPlaceDetail(id), getForecast(id, day, hour)
- [X] Create `utility/services/visitsService.ts` with postGpsPing(lat, lon, accuracy, timestamp), getVisitHistory(limit, offset)
- [X] Create `utility/services/locationService.ts` with startTracking() using watchPositionAsync and stopTracking()
- [X] Create `utility/hooks/useNearbyPlaces.ts` with TanStack Query, queryKey: ['places', 'nearby', lat, lon, radius, category], staleTime: 5min
- [X] Create `utility/hooks/useLocationTracking.ts` combining location permission request, watchPositionAsync at 15s, locationStore updates, and GPS ping posting
- [X] Create `utility/components/map/PlacePin.tsx` rendering a colored circle marker based on busyness level, with tracksViewChanges={false}
- [X] Create `utility/components/map/CategoryFilter.tsx` as a horizontal ScrollView of TouchableOpacity pills
- [X] Create `utility/components/map/PlaceSummarySheet.tsx` using @gorhom/bottom-sheet with place name, busyness badge, mini popular times chart, and "View Details" navigation
- [X] Create `utility/app/(tabs)/index.tsx` composing MapView (with ClusteredMapView from react-native-map-clustering), PlacePin markers, CategoryFilter overlay, PlaceSummarySheet, and location tracking
- [X] Test: map loads with pins, category filter narrows pins, pin tap opens bottom sheet with mini chart, "View Details" navigates
- [X] Fix: PlaceSummarySheet now fetches PlaceDetailResponse and renders MiniPopularTimesChart with 24 hourly bars for current day (was missing)
- [X] Fix: mapStore default region aligned to Paris (48.8566, 2.3522) to match index.tsx (was Lyon)

---

### Step 10: Build Place Detail Screen [DONE]

**Model:** opus
**Agent:** sdd:developer
**Depends on:** Step 9
**Parallel with:** Step 14

**Goal**: Create the place detail screen showing popular times histogram with day selector, live busyness indicator, forecast slider for future predictions, and the user's visit history to this place.

**Phase**: 7 - Place Detail
**Complexity**: Medium

#### Expected Output

- `utility/app/place/[id].tsx`: Place Detail screen
- `utility/hooks/usePlaceDetail.ts`: TanStack Query hook for place detail
- `utility/hooks/useForecast.ts`: TanStack Query hook for forecast
- `utility/components/place/BusynessHistogram.tsx`: Hour-by-hour bar chart with day selector
- `utility/components/place/LiveBusynessIndicator.tsx`: Current busyness badge
- `utility/components/place/ForecastSlider.tsx`: Day + hour picker showing prediction
- `utility/components/place/VisitHistoryList.tsx`: Past user visits to this place

#### Success Criteria

- [X] Place detail screen loads data from GET /places/{id} using `usePlaceDetail` hook
- [X] Place name, category, address, city are displayed at the top
- [X] `BusynessHistogram` renders 24 bars for the selected day from `popular_times` data, each bar height proportional to its 0-100 value
- [X] Day selector allows switching between Monday (0) through Sunday (6) and the histogram updates within 500ms
- [X] Current hour bar is visually highlighted in the histogram
- [X] `LiveBusynessIndicator` shows `current_popularity` value with busyness color when live data is available, or "No live data" when absent
- [X] `ForecastSlider` allows selecting a future day and hour, queries GET /places/{id}/forecast, and displays predicted busyness within 500ms
- [X] `VisitHistoryList` shows the user's past visits to this place (date and duration) from visit history data
- [X] When place has no busyness data, a placeholder message indicates data is unavailable
- [X] Back navigation returns to the map screen

#### Verification

**Level:** Single Judge
**Artifact:** `utility/app/place/[id].tsx`, `utility/hooks/usePlaceDetail.ts`, `utility/hooks/useForecast.ts`, `utility/components/place/BusynessHistogram.tsx`, `utility/components/place/LiveBusynessIndicator.tsx`, `utility/components/place/ForecastSlider.tsx`, `utility/components/place/VisitHistoryList.tsx`
**Threshold:** 4.0/5.0

**Rubric:**

| Criterion | Weight | Description |
|-----------|--------|-------------|
| Histogram Correctness | 0.25 | BusynessHistogram renders 24 bars from popular_times[day].hours array; day selector cycles Mon(0)-Sun(6); current hour bar is visually highlighted |
| Forecast Interaction | 0.20 | ForecastSlider allows day+hour selection; queries GET /places/{id}/forecast; displays predicted busyness within 500ms |
| Live Indicator | 0.15 | LiveBusynessIndicator shows current_popularity with busyness color when available; "No live data" when absent |
| Visit History | 0.15 | VisitHistoryList shows past visits with date and duration from visit history data |
| Screen Composition | 0.15 | place/[id].tsx composes all components in ScrollView with loading and error states |
| Empty States | 0.10 | Place without busyness_data shows "Busyness data not yet available" placeholder |

#### Subtasks

- [X] Create `utility/hooks/usePlaceDetail.ts` with TanStack Query for GET /places/{id}, staleTime 5min
- [X] Create `utility/hooks/useForecast.ts` with TanStack Query for GET /places/{id}/forecast with day and hour params, staleTime 1min
- [X] Create `utility/components/place/BusynessHistogram.tsx` using react-native-gifted-charts BarChart rendering 24 bars from popular_times[selectedDay].hours array, with day selector (horizontal pills or buttons for Mon-Sun)
- [X] Create `utility/components/place/LiveBusynessIndicator.tsx` showing current_popularity as a colored badge with label (Quiet/Moderate/Busy)
- [X] Create `utility/components/place/ForecastSlider.tsx` with day picker and hour slider, calling useForecast hook, displaying predicted busyness
- [X] Create `utility/components/place/VisitHistoryList.tsx` rendering a FlatList of past visits with date and duration
- [X] Create `utility/app/place/[id].tsx` composing all place detail components with ScrollView, loading state, and error handling
- [X] Handle empty state: place with no busyness_data shows "Busyness data not yet available" placeholder

---

### Step 11: Build Exploration Map Screen [DONE]

**Model:** opus
**Agent:** sdd:developer
**Depends on:** Step 8, Step 4
**Parallel with:** Step 9, Step 12, Step 13

**Goal**: Create the Explore tab screen showing a personal heatmap of visited neighborhoods as polygon overlays, per-city exploration percentage, city selector, and shareable exploration image.

**Phase**: 8 - Explore, Journal, Profile Screens
**Complexity**: Medium

#### Expected Output

- `utility/app/(tabs)/explore.tsx`: Exploration Map screen
- `utility/hooks/useHeatmap.ts`: TanStack Query hook for heatmap data
- `utility/components/explore/HeatmapLayer.tsx`: Polygon overlays for visited/unvisited areas
- `utility/components/explore/CityProgress.tsx`: Progress bar with exploration percentage
- `utility/components/explore/ShareableCard.tsx`: Capturable view for sharing

#### Success Criteria

- [X] `useHeatmap` hook fetches heatmap data from GET /explore/heatmap with optional city parameter
- [X] Explore screen renders a MapView with Geojson/Polygon overlays for each area
- [X] Visited neighborhoods appear as filled green polygons, unvisited neighborhoods appear as unfilled/grey outlines
- [X] `CityProgress` shows "X% of [City] explored" with a visual progress bar
- [X] City selector (if user has visited multiple cities) allows switching between cities
- [X] `ShareableCard` wraps the map and stats overlay in a view captured by react-native-view-shot
- [X] Share button generates a PNG image and opens the device share sheet via expo-sharing
- [X] Empty state shown when user has no visits: "Start exploring to see your heatmap!"

#### Verification

**Level:** Single Judge
**Artifact:** `utility/app/(tabs)/explore.tsx`, `utility/hooks/useHeatmap.ts`, `utility/components/explore/HeatmapLayer.tsx`, `utility/components/explore/CityProgress.tsx`, `utility/components/explore/ShareableCard.tsx`
**Threshold:** 4.0/5.0

**Rubric:**

| Criterion | Weight | Description |
|-----------|--------|-------------|
| Polygon Rendering | 0.30 | Visited neighborhoods rendered as filled green polygons; unvisited as grey outlines; correct GeoJSON parsing from boundary_geojson |
| City Progress | 0.20 | CityProgress shows "X% of [City] explored" with visual progress bar; city selector works for multi-city users |
| Heatmap Hook | 0.15 | useHeatmap correctly fetches from GET /explore/heatmap with optional city param and staleTime 10min |
| Share Functionality | 0.20 | ShareableCard captures view as PNG via react-native-view-shot; share button opens device share sheet via expo-sharing |
| Empty State | 0.15 | "Start exploring to see your heatmap!" shown when no visits exist |

#### Subtasks

- [X] Create `utility/hooks/useHeatmap.ts` with TanStack Query for GET /explore/heatmap, staleTime 10min
- [X] Create `utility/components/explore/HeatmapLayer.tsx` rendering Geojson/Polygon components from area boundary_geojson, coloring visited areas green and unvisited areas grey
- [X] Create `utility/components/explore/CityProgress.tsx` with progress bar component showing visited_areas / total_areas percentage
- [X] Create `utility/components/explore/ShareableCard.tsx` wrapping map + stats in a View with ref for react-native-view-shot
- [X] Create `utility/app/(tabs)/explore.tsx` composing MapView with HeatmapLayer, CityProgress overlay, city selector, and share button
- [X] Implement share functionality: capture view as PNG, open share sheet
- [X] Add empty state when no heatmap data available

---

### Step 12: Build Journal Screen and Note Edit Screen [DONE]

**Model:** opus
**Agent:** sdd:developer
**Depends on:** Step 8, Step 4, Step 6
**Parallel with:** Step 9, Step 11, Step 13

**Goal**: Create the Journal tab showing a chronological timeline of visits with infinite scroll, and the journal note edit screen for adding text notes and photos to entries.

**Phase**: 8 - Explore, Journal, Profile Screens
**Complexity**: Medium

#### Expected Output

- `utility/app/(tabs)/journal.tsx`: Journal screen with visit timeline
- `utility/app/journal/[visitId].tsx`: Journal note edit screen
- `utility/hooks/useJournal.ts`: TanStack infinite query hook for journal entries
- `utility/components/journal/JournalEntry.tsx`: Single timeline entry card
- `utility/components/journal/JournalEntryList.tsx`: Infinite scroll list

#### Success Criteria

- [X] `useJournal` hook uses TanStack `useInfiniteQuery` for paginated GET /journal with limit=20
- [X] Journal screen shows chronological timeline with most recent visits first
- [X] Each journal entry card displays: place name, visit date (formatted), visit duration, city name
- [X] Entries with notes show a truncated preview of the note text
- [X] Entries with photos show a thumbnail
- [X] Tapping an entry navigates to `/journal/{visitId}` for editing
- [X] Journal note edit screen allows adding/editing a text note (max 1000 chars)
- [X] Journal note edit screen allows picking a photo from device gallery via expo-image-picker
- [X] Text notes are saved to backend via POST /journal/{visit_id}/note
- [X] Photos are saved on-device (URI stored in AsyncStorage keyed by visit_id)
- [X] Infinite scroll loads more entries when user reaches the bottom
- [X] Empty state shown when no visits: "Visit places to start your journal!"

#### Verification

**Level:** Single Judge
**Artifact:** `utility/app/(tabs)/journal.tsx`, `utility/app/journal/[visitId].tsx`, `utility/hooks/useJournal.ts`, `utility/components/journal/JournalEntry.tsx`, `utility/components/journal/JournalEntryList.tsx`
**Threshold:** 4.0/5.0

**Rubric:**

| Criterion | Weight | Description |
|-----------|--------|-------------|
| Infinite Scroll | 0.20 | useJournal uses useInfiniteQuery with limit=20 and getNextPageParam based on offset; FlatList onEndReached triggers next page load |
| Entry Display | 0.20 | Each entry shows place name, formatted date, duration, city; note preview and photo thumbnail if present |
| Note Editing | 0.20 | Text note input (max 1000 chars); saved via POST /journal/{visit_id}/note through utilityService.addJournalNote |
| Photo Handling | 0.20 | expo-image-picker for gallery selection; URI stored in AsyncStorage keyed by visit_id; displayed on entry |
| Empty State | 0.10 | "Visit places to start your journal!" shown when no visits exist |
| Navigation | 0.10 | Tapping entry navigates to /journal/{visitId}; back navigation works correctly |

#### Subtasks

- [X] Create `utility/hooks/useJournal.ts` with useInfiniteQuery for GET /journal, getNextPageParam based on offset
- [X] Create `utility/components/journal/JournalEntry.tsx` as a Card displaying place name, date, duration, note preview, and optional photo thumbnail
- [X] Create `utility/components/journal/JournalEntryList.tsx` using FlatList with onEndReached for infinite loading, rendering JournalEntry items
- [X] Create `utility/app/(tabs)/journal.tsx` composing JournalEntryList with loading state and empty state
- [X] Create `utility/app/journal/[visitId].tsx` with TextInput for notes, expo-image-picker for photo selection, save button calling addJournalNote
- [X] Implement on-device photo storage: save picked image URI to AsyncStorage keyed by visit_id
- [X] On journal entry display, check AsyncStorage for local photo URI and display if present

---

### Step 13: Build Profile Screen with Stats, Achievements, and City Passports [DONE]

**Model:** opus
**Agent:** sdd:developer
**Depends on:** Step 8, Step 4, Step 6
**Parallel with:** Step 9, Step 11, Step 12

**Goal**: Create the Profile tab showing aggregate statistics and themed achievements, plus the city passport screen accessible from the profile with neighborhood stamps and city completion badges.

**Phase**: 9 - Profile and Passports
**Complexity**: Medium

#### Expected Output

- `utility/app/(tabs)/profile.tsx`: Profile screen with stats and achievements
- `utility/app/passport/[city].tsx`: City passport screen
- `utility/hooks/useUserStats.ts`: TanStack Query hook for user stats
- `utility/hooks/useAchievements.ts`: TanStack Query hook for achievements
- `utility/hooks/useCityPassport.ts`: TanStack Query hook for city passport
- `utility/components/profile/StatCard.tsx`: Stat display component
- `utility/components/profile/AchievementBadge.tsx`: Achievement card with progress
- `utility/components/profile/AchievementGrid.tsx`: Grid of achievements by category

#### Success Criteria

- [X] `useUserStats` hook fetches from GET /users/me/stats with staleTime 10min
- [X] `useAchievements` hook fetches from GET /users/me/achievements with staleTime 10min
- [X] `useCityPassport` hook fetches from GET /passports?city= with staleTime 10min
- [X] Profile screen displays 3 stat cards: total places visited, total cities explored, total countries reached
- [X] Achievements section shows 6 achievements across 3 categories (Explorer, Habits, Categories)
- [X] Each achievement shows: name, description, progress (e.g., "7/10"), and visual progress bar
- [X] Unlocked achievements have a distinct visual style (highlighted, with checkmark/glow) vs locked achievements (greyed out)
- [X] Profile screen has a "City Passports" section listing visited cities with links to passport screens
- [X] City passport screen shows all neighborhoods in the city as stamps (stamped = colored, unstamped = greyed)
- [X] City passport shows progress bar: "X of Y neighborhoods" visited
- [X] When all neighborhoods are stamped, a city completion badge is displayed prominently
- [X] Empty state on profile when no visits: "Start exploring to track your stats!"

#### Verification

**Level:** Single Judge
**Artifact:** `utility/app/(tabs)/profile.tsx`, `utility/app/passport/[city].tsx`, `utility/hooks/useUserStats.ts`, `utility/hooks/useAchievements.ts`, `utility/hooks/useCityPassport.ts`, `utility/components/profile/StatCard.tsx`, `utility/components/profile/AchievementBadge.tsx`, `utility/components/profile/AchievementGrid.tsx`
**Threshold:** 4.0/5.0

**Rubric:**

| Criterion | Weight | Description |
|-----------|--------|-------------|
| Stats Display | 0.15 | 3 StatCards showing total places, total cities, total countries; useUserStats hook fetches correct endpoint with staleTime 10min |
| Achievement Grid | 0.25 | 6 achievements across 3 categories (Explorer, Habits, Categories); each shows name, description, progress (X/Y), progress bar; unlocked vs locked have distinct visual styles |
| Passport Stamps | 0.25 | City passport shows all neighborhoods as stamps (colored=stamped, grey=unstamped); progress bar "X of Y neighborhoods" |
| City Badge | 0.10 | When explored_pct=100%, city completion badge displayed prominently and distinct from progress state |
| Hooks Correctness | 0.15 | useUserStats, useAchievements, useCityPassport fetch correct endpoints with staleTime 10min |
| Empty State | 0.10 | "Start exploring to track your stats!" shown when no visits exist |

#### Subtasks

- [X] Create `utility/hooks/useUserStats.ts` with TanStack Query for GET /users/me/stats
- [X] Create `utility/hooks/useAchievements.ts` with TanStack Query for GET /users/me/achievements
- [X] Create `utility/hooks/useCityPassport.ts` with TanStack Query for GET /passports?city=
- [X] Create `utility/components/profile/StatCard.tsx` with icon (MaterialIcons), value, and label
- [X] Create `utility/components/profile/AchievementBadge.tsx` with name, description, progress bar, earned/locked visual state
- [X] Create `utility/components/profile/AchievementGrid.tsx` grouping achievements by category with section headers
- [X] Create `utility/app/(tabs)/profile.tsx` composing StatCards, AchievementGrid, and city passport links with loading/empty states
- [X] Create `utility/app/passport/[city].tsx` with neighborhood stamp grid, progress bar, and city badge display
- [X] Implement stamp visual: stamped neighborhoods show with a colored stamp icon, unstamped show as greyed outlines
- [X] Implement city badge: when explored_pct = 100%, display a prominent completion badge

---

### Step 14: Integrate GPS Ping and Visit Confirmation Cache Invalidation [DONE]

**Model:** opus
**Agent:** sdd:developer
**Depends on:** Step 9
**Parallel with:** Step 10

**Goal**: Wire up the GPS coordinate submission to the backend every 15 seconds, handle the ping response to detect newly confirmed visits, and invalidate relevant TanStack Query caches when visits are confirmed so all screens update.

**Phase**: 10 - Integration
**Complexity**: Medium

#### Expected Output

- Updated `utility/hooks/useLocationTracking.ts`: Integrated GPS ping submission
- Cache invalidation logic in location tracking or a dedicated hook

#### Success Criteria

- [X] GPS coordinates are sent to POST /visits/ping every 15 seconds while the app is in the foreground and location permission is granted
- [X] The ping request includes: latitude, longitude, accuracy, timestamp
- [X] When POST /visits/ping returns `confirmed_visits` with new entries, the following TanStack Query caches are invalidated: `['journal']`, `['stats']`, `['achievements']`, `['heatmap']`, `['passport']`
- [X] Cache invalidation triggers automatic refetch on screens that are currently mounted
- [X] When GPS accuracy is worse than 100 meters, a low accuracy notice is displayed and pings continue but include the accuracy value
- [X] When the network is unavailable, GPS coordinates are queued and submitted when connectivity returns
- [X] GPS tracking stops when the app goes to background (foreground-only)
- [X] GPS tracking resumes when the app returns to foreground

#### Verification

**Level:** CRITICAL - Panel of 2 Judges with Aggregated Voting
**Artifact:** `utility/hooks/useLocationTracking.ts` (updated)
**Threshold:** 4.0/5.0

**Rubric:**

| Criterion | Weight | Description |
|-----------|--------|-------------|
| GPS Ping Integration | 0.25 | Coordinates sent to POST /visits/ping every 15s with latitude, longitude, accuracy, and timestamp |
| Cache Invalidation | 0.25 | When confirmed_visits returned in ping response, invalidates query keys: journal, stats, achievements, heatmap, passport |
| Lifecycle Management | 0.20 | Stops tracking on background; resumes on foreground via AppState listener; foreground-only as specified |
| Low Accuracy Handling | 0.15 | Detects accuracy > 100m; displays warning notice; pings continue with accuracy value included |
| Offline Queue | 0.15 | Queues GPS coordinates when offline; flushes queued coordinates when connectivity returns |

#### Subtasks

- [X] Update `utility/hooks/useLocationTracking.ts` to call `visitsService.postGpsPing()` on each location update
- [X] Parse the ping response for `confirmed_visits` array
- [X] When new confirmed visits are returned, use `queryClient.invalidateQueries()` to invalidate journal, stats, achievements, heatmap, and passport query keys
- [X] Add low GPS accuracy detection (> 100m) and display a warning notice
- [X] Implement simple GPS coordinate queue (array in memory or AsyncStorage) for offline scenarios
- [X] Flush queued coordinates when network connectivity is restored
- [X] Handle app state changes: stop tracking on background, resume on foreground using React Native AppState

---

### Step 15: Polish -- Empty States, Error Handling, Accessibility [DONE]

**Model:** opus
**Agent:** sdd:developer
**Depends on:** Step 9, Step 10, Step 11, Step 12, Step 13, Step 14
**Parallel with:** None

**Goal**: Implement empty states for all screens, comprehensive error handling for all failure scenarios, the network connectivity banner, and accessibility improvements for busyness color coding.

**Phase**: 10 - Polish
**Complexity**: Medium

#### Expected Output

- Empty state implementations across all screens
- Error handling for all API failure scenarios
- Network connectivity handling
- Accessibility enhancements for busyness colors

#### Success Criteria

- [X] Map screen shows guidance message when location permission is denied, with map centered on default location
- [X] Journal screen shows "Visit places to start your journal!" when no visits exist
- [X] Exploration map shows "Start exploring to see your heatmap!" when no visits exist
- [X] Profile screen shows "Start exploring to track your stats!" when no visits exist
- [X] City passports shows "Visit a city to earn stamps!" when no cities visited
- [X] Place detail shows "Busyness data not yet available" for places without busyness_data
- [X] All API error responses display user-friendly error messages (not raw error objects)
- [X] Network loss shows the NetworkBanner component at the top of the screen
- [X] Previously loaded data remains visible during network loss (TanStack Query cache)
- [X] When token refresh fails, user is redirected to login with "Session expired, please log in again"
- [X] Busyness color coding includes text labels ("Quiet", "Moderate", "Busy") on pin summary sheets and place detail, making colors accessible to colorblind users (protanopia, deuteranopia)
- [X] Pin shapes or icons vary by busyness level for additional non-color differentiation
- [X] All screens handle loading state with LoadingSpinner component
- [ ] App runs on both iOS and Android without platform-specific feature gaps

#### Subtasks

- [X] Add EmptyState component to `utility/app/(tabs)/journal.tsx` when journal entries list is empty
- [X] Add EmptyState component to `utility/app/(tabs)/explore.tsx` when heatmap has no data
- [X] Add EmptyState component to `utility/app/(tabs)/profile.tsx` when stats show zero visits
- [X] Add EmptyState component to `utility/app/passport/[city].tsx` placeholder
- [X] Add location permission denied guidance in `utility/app/(tabs)/index.tsx` with default location fallback
- [X] Add "No busyness data" placeholder in `utility/app/place/[id].tsx`
- [X] Integrate NetworkBanner in `utility/app/_layout.tsx` root layout so it appears on all screens
- [X] Add text labels ("Quiet", "Moderate", "Busy") to `PlaceSummarySheet.tsx` and `LiveBusynessIndicator.tsx`
- [X] Vary PlacePin shape/icon by busyness level for non-color differentiation
- [X] Add error message display for failed API calls on all screens (use TanStack Query error state)
- [X] Add loading states (LoadingSpinner) to all screens during initial data fetch
- [X] Verify token refresh failure redirects to login with clear message
- [ ] Test on both iOS simulator and Android emulator for cross-platform consistency

#### Verification

**Level:** Single Judge
**Artifact:** Updates across all screen files (utility/app/(tabs)/, utility/app/place/, utility/app/journal/, utility/app/passport/, utility/components/map/, utility/components/place/, utility/app/_layout.tsx)
**Threshold:** 4.0/5.0

**Rubric:**

| Criterion | Weight | Description |
|-----------|--------|-------------|
| Empty States | 0.25 | All 6 screens have appropriate empty states with guidance text matching spec (journal, explore, profile, passports, place detail, map permission denied) |
| Error Handling | 0.25 | All API errors show user-friendly messages; TanStack Query error states used; no raw error objects exposed to users |
| Accessibility | 0.20 | Busyness labels ("Quiet", "Moderate", "Busy") on pin summaries and place detail; pin shapes/icons vary by busyness level for non-color differentiation |
| Network Handling | 0.15 | NetworkBanner integrated in root layout; previously loaded data remains visible during network loss via TanStack Query cache |
| Loading States | 0.15 | All screens show LoadingSpinner during initial data fetch; cross-platform consistency verified |

---

## Implementation Summary

| Step | Phase | Goal | Key Output | Est. Effort |
|------|-------|------|------------|-------------|
| 1 | Backend Foundations | Fix area_id assignment via ST_Contains | `visit_service.py` update | S |
| 2 | Backend Foundations | JournalNote model + migration + schemas | 4 new files | M |
| 3 | Backend Endpoints | Utility service functions (6 functions) | `utility_service.py` | L |
| 4 | Backend Endpoints | Utility API router + tests | Router + test file | L |
| 5 | Expo Scaffold | Create Expo project with deps | `utility/` directory | M |
| 6 | Frontend Infra | Types, constants, API client, auth store, utilityService | 8 files | M |
| 7 | Frontend Infra | Shared UI components | 6 component files | M |
| 8 | Auth Flow | Auth service, stores, screens, root layout | 7 files | L |
| 9 | Map Screen | Tabs, location tracking, map with pins | 10 files | L |
| 10 | Place Detail | Histogram, forecast, visit history | 7 files | M |
| 11 | Exploration Map | Polygon heatmap, city progress, share | 5 files | M |
| 12 | Journal | Timeline, infinite scroll, note edit | 5 files | M |
| 13 | Profile + Passports | Stats, achievements, passport stamps | 8 files | M |
| 14 | GPS Integration | Ping submission, cache invalidation | Hook updates | M |
| 15 | Polish | Empty states, errors, accessibility | Updates across screens | M |

**Total Steps**: 15
**Critical Path**: Steps 1 -> 2 -> 3 -> 4 (backend), then Steps 5 -> 6 -> 8 -> 9 -> 10 (frontend critical path)
**Parallel Opportunities**:
- Steps 1, 2, 5 MUST run in parallel (all Level 0, no dependencies)
- Steps 3 and 6 MUST run in parallel (different dependency chains)
- Steps 4 and 7 MUST run in parallel (different dependency chains)
- Steps 9, 11, 12, 13 MUST run in parallel (once Steps 8 and 4 are complete)
- Steps 10 and 14 MUST run in parallel (both depend only on Step 9)

---

## Verification Summary

| Step | Verification Level | Judges | Threshold | Artifacts |
|------|-------------------|--------|-----------|-----------|
| 1 | CRITICAL - Panel (2) | 2 | 4.0/5.0 | visit_service.py area_id fix |
| 2 | CRITICAL - Panel (2) | 2 | 4.0/5.0 | JournalNote model, migration, schemas |
| 3 | CRITICAL - Panel (2) | 2 | 4.0/5.0 | utility_service.py (6 functions) |
| 4 | CRITICAL - Panel (2) | 2 | 4.0/5.0 | Utility router, main.py, conftest, tests |
| 5 | Single Judge | 1 | 4.0/5.0 | Expo project scaffold |
| 6 | CRITICAL - Panel (2) | 2 | 4.0/5.0 | Types, constants, API client, auth store, utilityService |
| 7 | Per-Component (6) | 6 | 4.0/5.0 | 6 shared UI components |
| 8 | CRITICAL - Panel (2) | 2 | 4.0/5.0 | Auth service, stores, root layout, auth screens |
| 9 | CRITICAL - Panel (2) | 2 | 4.0/5.0 | Tab layout, map screen, services, hooks, map components |
| 10 | Single Judge | 1 | 4.0/5.0 | Place detail screen, hooks, components |
| 11 | Single Judge | 1 | 4.0/5.0 | Exploration map screen, hook, components |
| 12 | Single Judge | 1 | 4.0/5.0 | Journal screen, note edit, hook, components |
| 13 | Single Judge | 1 | 4.0/5.0 | Profile screen, passport screen, hooks, components |
| 14 | CRITICAL - Panel (2) | 2 | 4.0/5.0 | GPS ping integration, cache invalidation |
| 15 | Single Judge | 1 | 4.0/5.0 | Polish across all screens |

**Total Evaluations:** 28
- Panel (2 evaluations each): 8 steps = 16 evaluations
- Per-Component evaluations: 1 step = 6 evaluations
- Single Judge: 6 steps = 6 evaluations

**Implementation Command:** `/implement .specs/tasks/draft/implement-utility-app.feature.md`

---

## Risks & Blockers Summary

### High Priority

| Risk/Blocker | Impact | Likelihood | Mitigation |
|--------------|--------|------------|------------|
| area_id stub blocks heatmap/passport | High | Certain | Step 1 is first task; PostGIS GIST index on areas.boundary already exists |
| Token refresh interceptor race conditions | High | Medium | Use Axios interceptor queue pattern: hold concurrent 401 requests while refresh is in flight, retry all after refresh completes |
| react-native-maps + New Architecture compatibility | High | Low | Verified v1.14+ supports New Architecture; lock version in package.json |
| Map performance with 200+ markers | Medium | Medium | react-native-map-clustering + tracksViewChanges={false} on all markers |
| Polygon rendering performance for cities with 100+ neighborhoods | Medium | Low | Geojson component handles this natively; can add area count threshold if needed |
| expo-location permissions on iOS | Medium | Medium | Clear permission strings in app.config.ts; graceful fallback when denied |
| On-device photos lost on uninstall | Low | Certain (by design) | Documented trade-off; can upgrade to backend storage later |

---

## Definition of Done (Task Level)

- [ ] All 15 implementation steps completed
- [ ] All acceptance criteria from the task file verified
- [ ] Backend: 6 new utility endpoints operational and tested
- [ ] Backend: area_id assignment working via ST_Contains
- [ ] Backend: All tests pass (`pytest backend/tests/`)
- [ ] Frontend: All 6 screens implemented and navigable
- [ ] Frontend: Auth flow works (register, login, session persistence, token refresh)
- [ ] Frontend: GPS pings sent every 15 seconds in foreground
- [ ] Frontend: Empty states on all screens
- [ ] Frontend: Error handling for all failure scenarios
- [ ] Frontend: App runs on both iOS and Android
- [ ] Accessibility: Busyness colors supplemented with labels for colorblind users
- [ ] No high-priority risks unaddressed
