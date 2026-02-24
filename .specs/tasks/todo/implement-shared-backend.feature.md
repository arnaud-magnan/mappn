---
title: Implement shared backend with FastAPI and PostGIS
---

> **Required Skill**: You MUST use and analyse `fastapi-postgis-backend` skill before doing any modification to task file or starting implementation of it!
>
> Skill location: `.claude/skills/fastapi-postgis-backend/SKILL.md`

## Initial User Prompt

Build the shared backend platform for both Mappn apps: FastAPI gateway, PostgreSQL/PostGIS database, auth service, places service, visit tracking with GPS + time-spent geofencing, and the Google Maps Popular Times scraping pipeline. See `.specs/plans/mappn-platform.design.md` for full architecture.

# Description

The Mappn platform consists of two mobile apps -- Mappn Utility (place discovery and exploration tracking) and Mappn Game (location-based RPG) -- both built on a single shared backend. This task delivers that shared backend: the foundational infrastructure that both apps depend on before any app-specific features can be built.

The backend provides four core capabilities. First, an authentication service that manages user accounts shared across both apps, allowing registration, login, credential refresh, and authenticated access control. Second, a places service that stores and serves geographic place data enriched with busyness information, supporting spatial queries ("show me all cafes within 500m"). Third, a visit tracking system that detects when a user has physically visited a place by matching GPS coordinates to nearby places and confirming the user remained within the geofence for a minimum duration, with safeguards for GPS inaccuracy and proximity to multiple places. Fourth, a scraping pipeline that collects Google Maps Popular Times data -- both weekly busyness histograms and live busyness levels -- to keep place data current and useful, with measurable prioritization based on user activity.

This task focuses exclusively on shared infrastructure. Both apps will consume these API endpoints, but all app-specific logic (game creatures, territories, exploration maps, achievements, social features) belongs to separate tasks. The backend must produce stable, well-defined API contracts so that mobile app development can proceed in parallel. The database schema created in this task covers only shared entities (users, places, areas, visits). Game and social entity tables (creatures, items, territories, events, friends, trades, leaderboards) are deferred to their respective feature tasks. The shared schema must support future extension through foreign key references from future tables without requiring modifications to the shared tables themselves.

**Scope**:
- Included: User registration and authentication (including credential refresh, input validation, rate limiting, and duplicate prevention), places database with spatial queries, nearby places search with category filtering, place detail with busyness data, busyness forecast, visit tracking with geofence-based confirmation (including GPS accuracy handling and multi-place proximity), scraping pipeline for popular times and live busyness with activity-based prioritization, database schema for shared entities only (users, places, areas, visits)
- Excluded: Game engine (creatures, territories, PvP, events, loot), gamification service (exploration maps, stats, achievements, passports), social features (friends, trading, leaderboards), game and social database tables, mobile app code, WebSocket real-time features, admin dashboard, push notifications, deployment infrastructure

**User Scenarios**:
1. **Primary Flow**: User registers an account with valid credentials, logs in, searches nearby places with busyness data, visits a place for 5+ minutes, and the visit is automatically confirmed and recorded -- available to both apps.
2. **Alternative Flows**: User refreshes credentials before they expire to maintain their session; user queries busyness forecast for a future time slot; user filters places by category; user views a place with no busyness data yet (returns null busyness fields without error); user is near multiple places simultaneously and all are returned in nearby search.
3. **Edge Cases**: User attempts to register with an email or username already in use and receives a clear rejection message; user submits GPS coordinates with accuracy worse than 100 meters and the system rejects them; user is within geofence radius of two places at once and the system tracks each qualifying visit independently; busyness data older than 7 days is flagged as potentially outdated when returned.
4. **Error Handling**: Invalid credentials return a generic authentication error without revealing which field was wrong; expired credentials return an error with a clear message prompting re-authentication; empty search results return an empty list without error; scraping failures are logged and retried without interrupting other places; excessive authentication attempts from the same source are temporarily blocked.

---

## Acceptance Criteria

### Functional Requirements

#### Authentication

- [ ] **User Registration**: Users can create an account with required information
  - Given: A new user provides email, username, and password
  - When: The user submits the registration request
  - Then: An account is created, credentials are stored securely (hashed, never plaintext), and the user can immediately log in

- [ ] **Registration Input Validation**: Registration enforces minimum quality requirements on inputs
  - Given: A user submits a registration request
  - When: The email format is invalid, the username is shorter than 3 characters, or the password is shorter than 8 characters
  - Then: The system rejects the request with a message identifying which field(s) failed validation, without creating an account

- [ ] **Duplicate Registration Prevention**: The system prevents duplicate accounts
  - Given: An account already exists with a specific email or username
  - When: A new user attempts to register with that same email or username
  - Then: The system rejects the request with a message indicating the email or username is already taken, without revealing details about the existing account

- [ ] **User Login**: Registered users can authenticate and receive access credentials
  - Given: A registered user provides valid email and password
  - When: The user submits the login request
  - Then: The system returns authentication credentials that grant access to protected endpoints

- [ ] **Credential Refresh**: Users can extend their session without re-entering their password
  - Given: A user has valid, non-expired authentication credentials
  - When: The user requests a credential refresh
  - Then: The system issues new credentials with an extended validity period and the previous credentials are no longer valid

- [ ] **Protected Endpoint Access**: Valid credentials grant access to protected resources
  - Given: A user has valid, non-expired authentication credentials
  - When: The user makes a request to a protected endpoint with the credentials
  - Then: The request is processed and the appropriate response is returned

- [ ] **Expired Credential Rejection**: Expired credentials are denied access
  - Given: A user has expired authentication credentials
  - When: The user makes a request to a protected endpoint
  - Then: The system returns an error response with a message indicating the credentials have expired and the user must re-authenticate

- [ ] **Invalid Credentials Handling**: Failed login does not leak account information
  - Given: A user provides an incorrect email or password
  - When: The login request is submitted
  - Then: The system returns a generic authentication error without revealing whether the email or password was incorrect

- [ ] **Authentication Rate Limiting**: The system protects against brute-force attacks on authentication endpoints
  - Given: A client sends more than 10 failed authentication requests within a 5-minute window
  - When: The next authentication request is received from the same source
  - Then: The system temporarily blocks further authentication attempts from that source for at least 15 minutes and returns an error indicating too many attempts

#### Places Service

- [ ] **Nearby Places Search**: Users can discover places around their location
  - Given: A user provides geographic coordinates and a search radius (e.g., 500m)
  - When: The user queries for nearby places
  - Then: The system returns all places within the specified radius, each including name, category, coordinates, and current busyness level (if available)

- [ ] **Place Category Filtering**: Users can narrow search results by place type
  - Given: A user provides coordinates, radius, and one or more category filters (e.g., "restaurant", "park")
  - When: The user queries for nearby places with filters applied
  - Then: Only places matching the specified categories are returned

- [ ] **Place Detail with Busyness Data**: Users can view comprehensive place information
  - Given: A valid place identifier
  - When: The user requests place details
  - Then: The system returns full place information including name, address, category, coordinates, popular times histogram (hourly busyness data for each day of the week), and current live busyness level

- [ ] **Busyness Forecast**: Users can check predicted busyness for future times
  - Given: A valid place identifier and a future date/time
  - When: The user requests a busyness forecast
  - Then: The system returns the predicted busyness level for that day and hour, derived from historical popular times data

- [ ] **Place with No Busyness Data**: Places without scraped data still return useful information
  - Given: A place exists in the database but has not yet been scraped for busyness data
  - When: A user requests details for that place
  - Then: The system returns the place details with busyness fields set to null or empty, without returning an error

- [ ] **Busyness Data Staleness Indicator**: Users can determine how current the busyness data is
  - Given: A place has busyness data that was last updated more than 7 days ago
  - When: A user requests details or busyness information for that place
  - Then: The response includes a staleness indicator showing when the data was last updated, and the data is flagged as potentially outdated

#### Visit Tracking

- [ ] **Visit Detection via Geofencing**: Physical presence at a place is automatically detected
  - Given: A user's GPS coordinates are within 75m (configurable) of a known place and GPS accuracy is 100m or better
  - When: The user remains within that radius for at least 5 minutes (configurable minimum duration)
  - Then: The system confirms the visit and records it with user, place, area, start time, end time, and duration

- [ ] **GPS Accuracy Threshold**: Low-confidence location data is rejected
  - Given: A user submits GPS coordinates with reported accuracy worse than 100 meters
  - When: The system receives these coordinates for visit tracking
  - Then: The coordinates are discarded for visit tracking purposes and the client is informed that location accuracy is insufficient

- [ ] **Concurrent Place Proximity**: Users near multiple places have each visit tracked independently
  - Given: A user's GPS coordinates are within the geofence radius of two or more distinct places simultaneously
  - When: The user remains within the geofence of each place for the minimum required duration
  - Then: A separate visit is confirmed and recorded for each qualifying place

- [ ] **No Duplicate Visits**: The same visit is not recorded multiple times
  - Given: A visit to a specific place has already been confirmed for the current session
  - When: The user continues to remain near the same place
  - Then: No additional visit record is created for that session

- [ ] **Cross-App Visit Availability**: Visit data is shared across both apps
  - Given: A visit has been confirmed (regardless of which app the user was using)
  - When: Either the Utility app or the Game app queries the user's visit history
  - Then: The confirmed visit appears in the results for both apps

#### Scraping Pipeline

- [ ] **Popular Times Scraping**: Historical busyness patterns are collected on schedule
  - Given: The scraping pipeline is running on its configured schedule
  - When: A weekly scraping cycle executes
  - Then: Popular times histograms are updated for scraped places, with data reflecting hourly busyness patterns for each day of the week

- [ ] **Live Busyness Refresh**: Real-time busyness is updated for active places at a predictable interval
  - Given: Users are actively viewing or located near certain places
  - When: The refresh cycle runs
  - Then: Live busyness levels are updated for those active places no longer than 20 minutes after the previous refresh

- [ ] **Activity-Based Scraping Prioritization**: Scraping resources are allocated proportionally to user activity
  - Given: Some places have high user activity (being viewed or near active users) and others have had no user activity in the past 24 hours
  - When: The scraping pipeline runs over a 24-hour period
  - Then: High-activity places are scraped at least 3 times more frequently than inactive places

- [ ] **Scraping Failure Resilience**: Pipeline failures do not cascade
  - Given: The scraping pipeline encounters a failure for a specific place (data unavailable, timeout, etc.)
  - When: The failure occurs
  - Then: The system logs the failure, marks the place for retry in the next cycle, and continues scraping remaining places without interruption

### Non-Functional Requirements

- [ ] **Search Response Time**: Nearby places query returns results within 2 seconds for a 500m radius with up to 200 places in the area
- [ ] **Concurrent Users**: System supports at least 1,000 concurrent authenticated users
- [ ] **Auth Overhead**: Authentication credential validation adds no more than 100ms overhead per request
- [ ] **Scraping Throughput**: Pipeline processes at least 100 places per hour without triggering external rate limits
- [ ] **Error Consistency**: All error responses follow a consistent format with meaningful error messages and appropriate categorization

### Definition of Done

- [ ] All acceptance criteria pass
- [ ] Tests written and passing for each service (auth, places, visits, scraping)
- [ ] API endpoint documentation available for mobile app developers
- [ ] Database schema deployed with spatial extensions enabled, containing only shared entity tables (users, places, areas, visits)
- [ ] Scraping pipeline runs successfully on schedule
- [ ] Code reviewed

---

## Architecture

### References

- **Skill**: `.claude/skills/fastapi-postgis-backend/SKILL.md`
- **Codebase Analysis**: `.specs/analysis/analysis-implement-shared-backend.md`
- **Scratchpad**: `.specs/scratchpad/f57765f5.md`

### Solution Strategy

**Approach**: Build a fully async FastAPI backend following the skill file's recommended stack -- AsyncSession + asyncpg + GeoAlchemy2 for the ORM/spatial layer, ARQ + Redis for the scraping task queue, PyJWT + passlib for authentication. Visit tracking uses server-side UserPresence state (stored in Redis) that auto-confirms visits when dwell time threshold is met, matching the acceptance criteria requirement for automatic confirmation. The database schema includes only shared entities (users, places, areas, visits) with PostGIS Geography columns and GIST indexes for meter-accurate spatial queries. The scraping pipeline abstracts behind an interface to allow swapping populartimes (MVP) for outscraper (production).

**Key Decisions**:
1. **ARQ over Celery**: ARQ is async-native and fits the async ecosystem (asyncpg, AsyncSession, FastAPI). Celery adds sync worker complexity without benefit for this workload of ~100 places/hour.
2. **Server-side visit auto-confirmation**: The acceptance criteria says visits are "automatically confirmed and recorded". Server-side UserPresence tracking prevents client spoofing and matches the skill file's recommendation to not trust client-reported visit completions.
3. **Shared-only ORM models**: Only users, places, areas, visits tables created. Game/social models deferred to their feature tasks per explicit task scope. Shared tables use integer PKs to support future FK references without modification.
4. **Geography(srid=4326) for all spatial columns**: Enables meter-accurate ST_DWithin queries without manual unit conversion. GIST indexes mandatory for performance.
5. **`api/` directory naming**: Clearer than `routers/` for communicating HTTP layer purpose, consistent with analysis file conventions.

**Trade-offs Accepted**:
- ARQ is less widely adopted than Celery, but its async-native design eliminates the sync/async impedance mismatch
- Server-side visit tracking requires more frequent GPS pings from clients (battery/data overhead), but provides tamper-proof visit verification
- Excluding game/social models means future tasks need their own migrations, but keeps this task focused

---

### Architecture Decomposition

**Components**:

| Component | Responsibility | Dependencies |
|-----------|---------------|--------------|
| FastAPI App (main.py) | HTTP entry point, lifespan management, router registration | All routers, config, db, redis |
| Auth Service | User registration, login, JWT issuance/refresh, rate limiting | User model, security core |
| Places Service | Spatial queries (nearby, detail), staleness detection | Place model, GeoAlchemy2 |
| Visit Service | GPS ping processing, UserPresence state, auto-confirm | Places service, Redis, Visit model |
| Forecast Service | Busyness prediction from histogram data | Place model (busyness_data JSONB) |
| Scraping Workers | Popular times + live busyness collection, priority scheduling | ARQ, populartimes, Place model |
| Database Layer | Async engine, session factory, ORM models, migrations | asyncpg, GeoAlchemy2, Alembic |
| Core Utilities | Security (JWT, bcrypt), Redis client, error handling | PyJWT, passlib, redis |

**Interactions**:

```
Client Apps (Utility + Game)
        |
        v
  FastAPI Gateway (main.py)
        |
   +----+------------+----------------+
   v    v            v                v
 Auth  Places     Visits          Forecast
 API   API        API             (via Places API)
   |    |            |
   v    v            v
 Auth  Places     Visit           Forecast
 Svc   Svc        Svc             Svc
   |    |         |  |                |
   |    |         |  +---> Places <---+
   |    |         |        Svc
   |    |         v
   |    |       Redis
   |    |       (UserPresence)
   v    v         v
  PostgreSQL / PostGIS
        ^
        |
  ARQ Workers (Scraping)
        |
        v
  External APIs (Google Maps)
```

---

### Expected Changes

```
backend/
+-- docker-compose.yml                    # NEW: PostGIS 16-3.5 + Redis 7 + API + ARQ worker
+-- Dockerfile                            # NEW: Python 3.11 container
+-- .env.example                          # NEW: Environment variable template
+-- requirements.txt                      # NEW: Pinned Python dependencies
+-- alembic.ini                           # NEW: Alembic config
+-- alembic/
|   +-- env.py                            # NEW: Async Alembic environment
|   +-- versions/
|       +-- 001_initial_schema.py         # NEW: PostGIS ext + shared tables + GIST indexes
+-- app/
    +-- main.py                           # NEW: FastAPI app, lifespan, router includes
    +-- config.py                         # NEW: Pydantic BaseSettings
    +-- db/
    |   +-- __init__.py                   # NEW
    |   +-- session.py                    # NEW: Async engine (pool_size=20, max_overflow=80)
    |   +-- base.py                       # NEW: DeclarativeBase
    +-- models/
    |   +-- __init__.py                   # NEW: Re-exports shared models
    |   +-- user.py                       # NEW: User (id, username, email, password_hash, xp, level, created_at)
    |   +-- place.py                      # NEW: Place (Geography POINT, busyness_data JSONB, busyness_updated_at)
    |   +-- area.py                       # NEW: Area (Geography POLYGON, zone_type)
    |   +-- visit.py                      # NEW: Visit (FK user, place, area)
    +-- schemas/
    |   +-- __init__.py                   # NEW
    |   +-- auth.py                       # NEW: RegisterRequest, LoginRequest, TokenResponse
    |   +-- place.py                      # NEW: PlaceResponse, NearbyQueryParams, ForecastResponse
    |   +-- visit.py                      # NEW: GPSPingRequest, GPSPingResponse, VisitResponse
    |   +-- user.py                       # NEW: UserResponse
    +-- api/
    |   +-- __init__.py                   # NEW
    |   +-- deps.py                       # NEW: get_db(), get_current_user(), rate limiter
    |   +-- auth.py                       # NEW: POST /auth/register, /auth/login, /auth/refresh
    |   +-- places.py                     # NEW: GET /places/nearby, /places/{id}, /places/{id}/forecast
    |   +-- visits.py                     # NEW: POST /visits/ping, GET /visits/history
    +-- services/
    |   +-- __init__.py                   # NEW
    |   +-- auth_service.py              # NEW: register, authenticate, token create/refresh
    |   +-- places_service.py            # NEW: PostGIS spatial queries, staleness check
    |   +-- visit_service.py             # NEW: GPS ping, UserPresence state, auto-confirm
    |   +-- forecast_service.py          # NEW: Busyness histogram lookup
    +-- workers/
    |   +-- __init__.py                   # NEW
    |   +-- scraping.py                   # NEW: ARQ WorkerSettings + scrape tasks
    +-- core/
        +-- __init__.py                   # NEW
        +-- security.py                   # NEW: JWT + bcrypt helpers
        +-- redis.py                      # NEW: Redis client + UserPresence helpers
        +-- exceptions.py                 # NEW: Error handlers
tests/
    +-- __init__.py                       # NEW
    +-- conftest.py                       # NEW: Async test fixtures (testcontainers PostGIS)
    +-- test_auth.py                      # NEW
    +-- test_places.py                    # NEW
    +-- test_visits.py                    # NEW
    +-- test_scraping.py                  # NEW
```

Total: 7 infrastructure + 27 app files + 6 test files = 40 files

---

### Runtime Scenarios

**Scenario: Visit Detection and Auto-Confirmation**

```
Mobile App --POST /visits/ping--> API Layer --> Visit Service --> Result
                                      |              |
                                      v              v
                                  JWT Validate    Places Service
                                                     |
                                              ST_DWithin(75m)
                                                     |
                                              +------+------+
                                              |             |
                                        No matches    Matches found
                                              |             |
                                              v             v
                                        Return empty   Upsert UserPresence
                                                        in Redis
                                                           |
                                                    +------+------+
                                                    |             |
                                              dwell < 5min   dwell >= 5min
                                                    |         & reads >= 3
                                                    v             |
                                              Return            v
                                              "tracking"   CREATE Visit
                                                           DELETE Presence
                                                           Return "confirmed"
```

**State Transitions for UserPresence**:

```
[None] --- GPS within 75m ---> [Tracking] --- dwell >= 5min ---> [Confirmed]
                                    |              & reads >= 3       |
                                    |                                 v
                                    | N consecutive              [Visit Record]
                                    | out-of-range               [Presence Deleted]
                                    v
                               [Cleared]
```

**Scenario: Scraping Priority**

```
ARQ Cron (15 min) --triggers--> scrape_live_busyness()
                                     |
                              Query active places
                              (GPS pings in last 30 min)
                                     |
                              +------+------+
                              |             |
                        Active places   Inactive places
                        (scrape now)    (skip until weekly)
                              |
                        Fetch live data --> UPDATE Place.busyness_data
                                           + busyness_updated_at
                                           Cache in Redis (TTL=20min)
```

---

### Architecture Decisions

#### ARQ over Celery for Task Queue

**Status**: Accepted

**Context**: The scraping pipeline needs scheduled background tasks. The entire stack is async (asyncpg, AsyncSession, FastAPI).

**Options**:
1. Celery with Redis broker (mature, widely adopted, sync-first)
2. ARQ with Redis (async-native, built by Pydantic author, lighter weight)
3. APScheduler (in-process, no external broker)

**Decision**: ARQ -- because the entire stack is async. ARQ is async-native, integrates cleanly, and the workload (100 places/hour) is well within its capacity. The skill file explicitly recommends it over Celery.

**Consequences**:
- Simpler worker configuration (single WorkerSettings class vs Celery app + beat)
- No sync/async bridge needed in worker code
- Smaller community than Celery, but sufficient for this use case

#### Server-Side Visit Auto-Confirmation

**Status**: Accepted

**Context**: Visit tracking can be client-driven (client timer + POST /confirm) or server-driven (server tracks dwell via GPS pings).

**Options**:
1. Client-confirms: client starts timer, calls POST /visits/confirm after 5 min
2. Server-side: server tracks UserPresence in Redis, auto-confirms when threshold met
3. Hybrid: server tracks but client also calls confirm as fallback

**Decision**: Server-side auto-confirmation -- because the acceptance criteria says visits are "automatically confirmed and recorded" and the skill file warns "Do not trust client-reported visit completions."

**Consequences**:
- Requires more frequent GPS pings from clients (every 30-60 seconds while in foreground)
- Prevents client-side spoofing of visit completion
- Redis stores UserPresence state with TTL as safety net against orphaned entries

#### Shared-Only Database Schema

**Status**: Accepted

**Context**: The full platform data model includes 13+ entity types. The task scope explicitly limits to shared entities.

**Options**:
1. Create all tables now (full schema, game/social included)
2. Create only shared tables (users, places, areas, visits)
3. Create shared tables + stub tables with minimal columns

**Decision**: Only shared tables. The task states "Database schema created in this task covers only shared entities" and "Game and social entity tables are deferred to their respective feature tasks."

**Consequences**:
- Future tasks must create their own Alembic migrations for game/social tables
- Shared tables support FK references from future tables without modification (integer PKs)
- User.id, Place.id, Area.id use stable integer primary keys

---

### High-Level Structure

```
Feature: Shared Backend
+-- Entry Point: FastAPI app (main.py) with lifespan managing DB pool + Redis + ARQ
+-- Auth Module: Registration, login, JWT refresh with rate limiting
|   +-- API: POST /auth/register, /auth/login, /auth/refresh
|   +-- Service: auth_service.py (user CRUD, token management)
|   +-- Core: security.py (JWT encode/decode, bcrypt hash/verify)
+-- Places Module: Spatial search and busyness data
|   +-- API: GET /places/nearby, /places/{id}, /places/{id}/forecast
|   +-- Service: places_service.py (ST_DWithin queries, staleness)
|   +-- Service: forecast_service.py (histogram lookup)
+-- Visits Module: GPS-based visit detection
|   +-- API: POST /visits/ping, GET /visits/history
|   +-- Service: visit_service.py (UserPresence state machine)
|   +-- Core: redis.py (UserPresence storage)
+-- Scraping Module: Busyness data collection
|   +-- Worker: scraping.py (ARQ tasks for popular times + live busyness)
+-- Data Layer: PostgreSQL/PostGIS with async SQLAlchemy
|   +-- Models: user, place, area, visit (shared only)
|   +-- Migration: 001_initial_schema (PostGIS extension + tables + GIST indexes)
|   +-- Session: async engine with connection pooling (pool_size=20, max_overflow=80)
+-- Infrastructure: Docker Compose, env config, Alembic
```

---

### Workflow Steps

```
Phase 1: Foundation --> Phase 2: DB Layer --> Phase 4: Schemas
     |                       |                      |
     +--> Phase 3: Core -----+                      |
                   |                                |
                   +-----------> Phase 5: Services <-+
                                     |
                              Phase 6: API Layer
                                     |
                              Phase 7: App Entry
                                     |
               Phase 8: Workers      |
                    |                |
                    +--------> Phase 9: Tests
```

**Phase 1: Foundation** (no dependencies)
- `backend/requirements.txt`, `.env.example`, `Dockerfile`, `docker-compose.yml`, `app/config.py`

**Phase 2: Database Layer** (depends on Phase 1)
- `app/db/base.py`, `app/db/session.py`, ORM models (user, place, area, visit), `app/models/__init__.py`, `alembic.ini`, `alembic/env.py`, `alembic/versions/001_initial_schema.py`

**Phase 3: Core Utilities** (depends on Phase 1)
- `app/core/security.py`, `app/core/redis.py`, `app/core/exceptions.py`

**Phase 4: Pydantic Schemas** (depends on Phase 2)
- `app/schemas/auth.py`, `app/schemas/place.py`, `app/schemas/visit.py`, `app/schemas/user.py`

**Phase 5: Service Layer** (depends on Phase 2, 3, 4)
- `app/services/auth_service.py`, `app/services/places_service.py`, `app/services/visit_service.py`, `app/services/forecast_service.py`

**Phase 6: API Layer** (depends on Phase 3, 4, 5)
- `app/api/deps.py`, `app/api/auth.py`, `app/api/places.py`, `app/api/visits.py`

**Phase 7: App Entry Point** (depends on Phase 6)
- `app/main.py` (FastAPI init, lifespan, router registration)

**Phase 8: Scraping Workers** (depends on Phase 2, 3)
- `app/workers/scraping.py` (ARQ WorkerSettings + tasks)

**Phase 9: Tests** (depends on all previous phases)
- `tests/conftest.py`, `tests/test_auth.py`, `tests/test_places.py`, `tests/test_visits.py`, `tests/test_scraping.py`

---

### Contracts

**Auth API**:

```
POST /auth/register
Input: { email: string, username: string (>=3 chars), password: string (>=8 chars) }
Output: { access_token: string, refresh_token: string, token_type: "bearer", expires_in: int }
Errors: 400 (validation), 409 (duplicate email/username)

POST /auth/login
Input: { email: string, password: string }
Output: { access_token: string, refresh_token: string, token_type: "bearer", expires_in: int }
Errors: 401 (invalid credentials -- generic message), 429 (rate limited)

POST /auth/refresh
Input: Header Authorization: Bearer {refresh_token}
Output: { access_token: string, refresh_token: string, token_type: "bearer", expires_in: int }
Errors: 401 (invalid/expired token)
```

**Places API**:

```
GET /places/nearby?lat=float&lon=float&radius_m=int&category=string(optional)
Output: [ { id, name, category, lat, lon, address, current_busyness: int|null,
            busyness_stale: bool, busyness_updated_at: datetime|null } ]
Errors: 401 (unauthorized)

GET /places/{id}
Output: { id, name, category, lat, lon, address, city, country,
          busyness_data: { popular_times: [{day: int, hours: [int]}],
                          current_popularity: int|null },
          busyness_updated_at: datetime|null, busyness_stale: bool }
Errors: 401, 404

GET /places/{id}/forecast?day=int(0-6)&hour=int(0-23)
Output: { place_id: int, day: int, hour: int, predicted_busyness: int, data_stale: bool }
Errors: 401, 404
```

**Visits API**:

```
POST /visits/ping
Input: { lat: float, lon: float, accuracy: float, timestamp: datetime }
Output: { nearby_places: [{ place_id, name, distance_m }],
          confirmed_visits: [{ visit_id, place_id, duration_seconds }],
          rejected: bool, rejection_reason: string|null }
Errors: 401, 422 (accuracy > 100m)

GET /visits/history?limit=int&offset=int
Output: [ { id, place_id, place_name, area_id, started_at, ended_at, duration_seconds } ]
Errors: 401
```

**Data Model -- busyness_data JSONB Structure**:

```json
{
  "popular_times": [
    { "day": 0, "hours": [0,0,0,5,10,25,45,60,75,80,70,55,40,35,30,40,55,70,80,65,45,25,10,0] },
    { "day": 1, "hours": ["...24 values..."] },
    { "day": 6, "hours": ["...24 values..."] }
  ],
  "current_popularity": 65,
  "time_spent": [15, 30]
}
```

**Data Model -- UserPresence Redis Structure**:

```
Key: user_presence:{user_id}:{place_id}
Value: JSON { "first_seen": "ISO datetime", "last_seen": "ISO datetime", "reading_count": int }
TTL: 30 minutes (safety net for abandoned sessions)
```

---

## Implementation Process

You MUST launch for each step a separate agent, instead of performing all steps yourself. And for each step marked as parallel, you MUST launch separate agents in parallel.

**CRITICAL:** For each agent you MUST:
1. Use the **Agent** type specified in the step (e.g., `haiku`, `sonnet`, `sdd:developer`)
2. Provide path to task file and prompt which step to implement
3. Require agent to implement exactly that step, not more, not less, not other steps

### Implementation Strategy

**Approach**: Bottom-Up (Building-Blocks-First)
**Rationale**: This is a greenfield project where complexity concentrates in the data layer (PostGIS spatial queries, GeoAlchemy2 ORM integration) and the visit tracking state machine. Building from foundational infrastructure upward ensures each layer is validated before dependent layers are built on top. The PostGIS + GeoAlchemy2 + asyncpg integration is the highest-risk area and must be proven early. Once the foundation and data layers are solid, vertical domain slices (auth, places, visits, scraping) each deliver complete, independently testable functionality.

### Parallelization Overview

```
Step 1: Project Setup [haiku]
    |
    +-------------------+
    |                   |
    v                   v
Step 2a: DB Layer    Step 2b: Core Utilities
[sdd:developer]      [sdd:developer]
(MUST be parallel)   (MUST be parallel)
    |                   |
    v                   |
Step 3: ORM Models     |
[sdd:developer]        |
    |                   |
    +----------+--------+
    |          |        |
    v          v        v
Step 4       Step 5a   Step 9: Scraping Pipeline
Schemas      deps.py   [sdd:developer]
[sdd:dev]    [sdd:dev] (MUST be parallel with 4, 5a)
(parallel)   (parallel)    |
    |          |           | (independent chain, continues alongside Steps 5b-8)
    +-----+----+           |
          |                |
          v                |
     Step 5b: Test Infra   |
     [sdd:developer]       |
          |                |
    +-----+-----+         |
    |           |          |
    v           v          |
Step 6:     Step 7:        |
Auth        Places         |
[sdd:dev]   [sdd:dev]     |
(parallel)  (parallel)     |
    |           |          |
    |           v          |
    |       Step 8:        |
    |       Visits         |
    |       [sdd:dev]      |
    |           |          |
    +-----+----+----------+
          |
          v
     Step 10: Integration
     [sdd:developer]
```

**Key Parallelization Decisions:**
- **Step 2 split into 2a + 2b**: Database layer (base.py, session.py) and core utilities (security.py, redis.py, exceptions.py) depend only on Step 1 and have no dependency on each other. Splitting them enables parallel execution, and Step 3 starts as soon as 2a completes without waiting for 2b.
- **deps.py extracted as Step 5a**: `api/deps.py` (get_db, get_current_user, rate_limiter) depends only on Steps 2a, 2b, and 3 -- NOT on Step 4 (schemas). Extracting it from the old Step 5 lets it run in parallel with Step 4, so Step 5b (test infra) starts sooner.
- **Step 8 depends only on Step 7 (not Step 6)**: `visit_service` calls `places_service.get_nearby_places()` but never calls `auth_service`. The visit API endpoints use `get_current_user` from `deps.py` (Step 5a) and `places_service` (Step 7). Removing the false Step 6 dependency lets Step 8 start as soon as Step 7 finishes, while Step 6 continues independently.
- **Step 9 independent chain**: Scraping workers depend only on Steps 2a, 2b, and 3 (db/session.py, redis.py, Place model). They create their own AsyncSession and have no dependency on schemas, test infrastructure, or API layer.
- **Max parallel depth**: 3 agents simultaneously at two points: Steps 4 + 5a + 9 after Step 3; Steps 6 + 7 + 9 after Step 5b.

---

### Step 1: Project Setup and Infrastructure

**Model:** haiku
**Agent:** haiku
**Depends on:** None
**Parallel with:** None (first step)

**Goal**: Create the project skeleton with all infrastructure files needed to build Docker images, install Python dependencies, and configure environment variables.

**Phase**: Setup | **Complexity**: Small | **Uncertainty**: Low

#### Expected Output

- `backend/docker-compose.yml`: PostGIS 16-3.5 + Redis 7-alpine + API service + ARQ worker service
- `backend/Dockerfile`: Python 3.11 container for API and worker
- `backend/.env.example`: Template with DATABASE_URL, REDIS_URL, SECRET_KEY, token expiry settings, geofence radius, dwell time
- `backend/requirements.txt`: All Python dependencies with pinned versions (fastapi, uvicorn, sqlalchemy, asyncpg, geoalchemy2, alembic, pydantic, pydantic-settings, PyJWT, passlib, arq, redis, httpx, populartimes, pytest-asyncio, testcontainers)
- `backend/alembic.ini`: Alembic configuration file
- `backend/app/config.py`: Pydantic BaseSettings class reading from .env

#### Success Criteria

- [ ] `docker compose build` completes without errors
- [ ] `docker compose up db redis` starts PostGIS and Redis containers successfully
- [ ] `backend/requirements.txt` contains all dependencies listed in the skill file with pinned versions
- [ ] `backend/.env.example` contains all required environment variables with example values
- [ ] `backend/app/config.py` defines Settings class with fields for database_url, redis_url, secret_key, access_token_expire_minutes, refresh_token_expire_days, geofence_radius_m, visit_min_duration_seconds, visit_min_readings
- [ ] Settings class loads values from .env file using pydantic-settings

#### Subtasks

| Sub-task | Description | Agent | Can Parallel |
|----------|-------------|-------|--------------|
| Directory structure | Create `backend/` with empty `__init__.py` for all packages | haiku | Yes |
| requirements.txt | Pinned versions matching skill file | haiku | Yes |
| .env.example | All environment variable templates | haiku | Yes |
| Dockerfile | Python 3.11 base image | haiku | Yes |
| docker-compose.yml | PostGIS, Redis, API, worker services | haiku | Yes |
| alembic.ini | Pointing to alembic/ directory | haiku | Yes |
| config.py | Pydantic BaseSettings with lru_cache getter | haiku | Yes |

- [ ] Create `backend/` directory structure with empty `__init__.py` files for all packages (app, app/db, app/models, app/schemas, app/api, app/services, app/workers, app/core, tests)
- [ ] Create `backend/requirements.txt` with pinned versions matching skill file recommendations
- [ ] Create `backend/.env.example` with all environment variable templates
- [ ] Create `backend/Dockerfile` with Python 3.11 base image
- [ ] Create `backend/docker-compose.yml` with postgis/postgis:16-3.5, redis:7-alpine, api, and worker services
- [ ] Create `backend/alembic.ini` pointing to alembic/ directory
- [ ] Create `backend/app/config.py` with Pydantic BaseSettings and lru_cache getter

#### Dependencies

- None (Level 0)

#### Blockers

- None

#### Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Docker image pull failures | Low | Use specific image tags, not latest |

#### Verification

**Level:** Single Judge
**Artifact:** `backend/` (docker-compose.yml, Dockerfile, .env.example, requirements.txt, alembic.ini, app/config.py)
**Threshold:** 4.0/5.0

**Rubric:**

| Criterion | Weight | Description |
|-----------|--------|-------------|
| Correctness | 0.30 | Docker Compose defines all 4 services (PostGIS 16-3.5, Redis 7-alpine, API, worker), Dockerfile uses Python 3.11, requirements.txt includes all specified packages |
| Completeness | 0.25 | All files listed in Expected Output exist: docker-compose.yml, Dockerfile, .env.example, requirements.txt, alembic.ini, config.py, all __init__.py package files |
| Config Accuracy | 0.25 | config.py Settings class has all specified fields (database_url, redis_url, secret_key, access_token_expire_minutes, refresh_token_expire_days, geofence_radius_m, visit_min_duration_seconds, visit_min_readings), uses pydantic-settings BaseSettings |
| Consistency | 0.20 | File structure matches Expected Changes tree, naming conventions consistent, requirements versions pinned |

---

### Step 2a: Database Layer

**Model:** opus
**Agent:** sdd:developer
**Depends on:** Step 1
**Parallel with:** Step 2b (both depend on Step 1; MUST be launched in parallel)

**Goal**: Create the async database engine with connection pooling and SQLAlchemy DeclarativeBase. These are the foundational database components that ORM models (Step 3) build upon.

**Phase**: Foundation | **Complexity**: Small | **Uncertainty**: Low

#### Expected Output

- `backend/app/db/base.py`: DeclarativeBase class
- `backend/app/db/session.py`: Async engine (pool_size=20, max_overflow=80), async_sessionmaker, get_db async generator
- `backend/app/db/__init__.py`: Package init

#### Success Criteria

- [ ] `db/session.py` creates async engine with `postgresql+asyncpg://` URL from config, pool_size=20, max_overflow=80
- [ ] `async_sessionmaker` configured with `expire_on_commit=False`
- [ ] `get_db()` yields an AsyncSession and properly closes it
- [ ] `db/base.py` exports a DeclarativeBase subclass usable by ORM models

#### Subtasks

| Sub-task | Description | Agent | Can Parallel |
|----------|-------------|-------|--------------|
| base.py | DeclarativeBase class | sdd:developer | Yes |
| session.py | Async engine, sessionmaker, get_db | sdd:developer | Yes |

- [ ] Create `backend/app/db/__init__.py`
- [ ] Create `backend/app/db/base.py` with DeclarativeBase
- [ ] Create `backend/app/db/session.py` with create_async_engine, async_sessionmaker, get_db dependency

#### Dependencies

- Step 1 (config.py for DATABASE_URL, requirements.txt for packages)

#### Blockers

- None

#### Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| asyncpg connection string format issues | Low | Use the exact format from skill file: postgresql+asyncpg://user:pass@host/db |

#### Verification

**Level:** Single Judge
**Artifact:** `backend/app/db/` (base.py, session.py, __init__.py)
**Threshold:** 4.0/5.0

**Rubric:**

| Criterion | Weight | Description |
|-----------|--------|-------------|
| Correctness | 0.35 | Async engine uses postgresql+asyncpg:// URL from config, pool_size=20, max_overflow=80; async_sessionmaker with expire_on_commit=False; get_db yields AsyncSession and closes properly |
| Code Quality | 0.25 | Follows skill file async patterns, proper imports from sqlalchemy.ext.asyncio |
| Error Handling | 0.20 | get_db properly handles session lifecycle (try/finally or async context manager) |
| Consistency | 0.20 | DeclarativeBase follows SQLAlchemy 2.0 pattern, naming matches project conventions |

---

### Step 2b: Core Utilities

**Model:** opus
**Agent:** sdd:developer
**Depends on:** Step 1
**Parallel with:** Step 2a (both depend on Step 1; MUST be launched in parallel)

**Goal**: Create the core utility modules for security (JWT + bcrypt), Redis client (with UserPresence helpers), and consistent error handling. These are independent of the database layer and can be built in parallel.

**Phase**: Foundation | **Complexity**: Medium | **Uncertainty**: Low

#### Expected Output

- `backend/app/core/security.py`: hash_password(), verify_password(), create_access_token(), create_refresh_token(), decode_token()
- `backend/app/core/redis.py`: Redis client initialization, get_user_presence(), set_user_presence(), delete_user_presence(), increment_rate_limit()
- `backend/app/core/exceptions.py`: Custom exception classes (CredentialsException, DuplicateEntityException, EntityNotFoundException, GPSAccuracyException), global exception handler producing consistent JSON error format
- `backend/app/core/__init__.py`: Package init
- `backend/tests/test_core_security.py`: Unit tests for security.py

#### Success Criteria

- [ ] `security.py` hash_password() returns a bcrypt hash that verify_password() can validate
- [ ] `security.py` create_access_token() returns a JWT string with sub, exp, type claims
- [ ] `security.py` decode_token() raises appropriate errors for expired or invalid tokens
- [ ] `redis.py` provides async Redis client that connects using config.redis_url
- [ ] `redis.py` UserPresence helpers handle set/get/delete with JSON serialization and TTL
- [ ] `exceptions.py` defines custom exceptions that produce consistent JSON error responses with status_code, error_type, and message fields
- [ ] Unit tests for security.py pass (hash/verify password, create/decode token, expired token)

#### Subtasks

| Sub-task | Description | Agent | Can Parallel |
|----------|-------------|-------|--------------|
| security.py | JWT + bcrypt helpers | sdd:developer | Yes |
| redis.py | Async client + UserPresence + rate limit helpers | sdd:developer | Yes |
| exceptions.py | Custom exceptions + handler | sdd:developer | Yes |
| test_core_security.py | Unit tests for security | sdd:developer | After security.py |

- [ ] Create `backend/app/core/__init__.py`
- [ ] Create `backend/app/core/security.py` with password hashing (passlib bcrypt) and JWT functions (PyJWT)
- [ ] Create `backend/app/core/redis.py` with async Redis client, UserPresence CRUD helpers, rate limiting counter helpers
- [ ] Create `backend/app/core/exceptions.py` with custom exceptions and FastAPI exception handlers
- [ ] Write unit tests for security.py (hash/verify password, create/decode token, expired token handling) in `backend/tests/test_core_security.py`

#### Dependencies

- Step 1 (config.py for SECRET_KEY and REDIS_URL, requirements.txt for packages)

#### Blockers

- None

#### Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| PyJWT vs python-jose API differences | Low | Use PyJWT (import jwt) consistently; skill file recommends PyJWT |

#### Verification

**Level:** CRITICAL - Panel of 2 Judges with Aggregated Voting
**Artifact:** `backend/app/core/` (security.py, redis.py, exceptions.py) + `backend/tests/test_core_security.py`
**Threshold:** 4.0/5.0

**Rubric:**

| Criterion | Weight | Description |
|-----------|--------|-------------|
| Security | 0.30 | bcrypt hashing (not MD5/SHA), JWT tokens include sub/exp/type claims, decode_token validates expiry and token type, no secret keys hardcoded |
| Correctness | 0.25 | hash_password/verify_password round-trip correctly, create/decode token round-trip correctly, Redis UserPresence CRUD with JSON serialization and TTL, rate limit counter with window expiry |
| Error Handling | 0.20 | Expired tokens raise specific errors, invalid tokens raise specific errors, Redis connection failures handled gracefully, exceptions produce consistent JSON format with status_code/error_type/message |
| Test Coverage | 0.15 | test_core_security.py covers hash/verify password, create/decode token, expired token, invalid token |
| Code Quality | 0.10 | Uses PyJWT (not python-jose), uses passlib bcrypt, async Redis client, proper type hints |

**Reference Pattern:** `.claude/skills/fastapi-postgis-backend/SKILL.md` (JWT and bcrypt patterns)

---

### Step 3: ORM Models and Alembic Migration

**Model:** opus
**Agent:** sdd:developer
**Depends on:** Step 2a
**Parallel with:** None (Step 2b continues in parallel if not yet finished)

**Goal**: Define the four shared ORM models (User, Place, Area, Visit) with PostGIS Geography columns for spatial data, and create the initial Alembic migration that enables the PostGIS extension and creates all tables with GIST indexes.

**Phase**: Data Models | **Complexity**: Medium | **Uncertainty**: Medium

#### Expected Output

- `backend/app/models/user.py`: User model (id, username, email, password_hash, xp, level, created_at)
- `backend/app/models/place.py`: Place model (id, google_place_id, name, category, coordinates Geography POINT, address, city, country, busyness_data JSONB, busyness_updated_at)
- `backend/app/models/area.py`: Area model (id, name, city, boundary Geography POLYGON, zone_type, busyness_score)
- `backend/app/models/visit.py`: Visit model (id, user_id FK, place_id FK, area_id FK nullable, started_at, ended_at, duration_seconds)
- `backend/app/models/__init__.py`: Re-exports all models for Alembic autodiscovery
- `backend/alembic/env.py`: Async Alembic environment importing all models
- `backend/alembic/versions/001_initial_schema.py`: Migration creating PostGIS extension, all tables, GIST indexes, and standard indexes

#### Success Criteria

- [ ] User model has unique constraints on email and username columns
- [ ] Place.coordinates uses `Geography(geometry_type="POINT", srid=4326)`
- [ ] Area.boundary uses `Geography(geometry_type="POLYGON", srid=4326)`
- [ ] Visit model has foreign keys to users.id, places.id, and areas.id (nullable)
- [ ] All shared models use integer primary keys (supporting future FK references)
- [ ] `alembic/env.py` uses run_async() pattern for async engine compatibility
- [ ] Migration 001 executes `CREATE EXTENSION IF NOT EXISTS postgis`
- [ ] Migration 001 creates GIST indexes on places.coordinates and areas.boundary
- [ ] Migration 001 creates standard indexes on visits.user_id, visits.place_id, places.category
- [ ] `alembic upgrade head` runs successfully against a PostGIS database
- [ ] `alembic downgrade base` cleanly drops all tables

#### Subtasks

**Note:** Individual ORM model files MUST be created in parallel by the agent, as they are independent of each other (all inherit from the same DeclarativeBase).

| Sub-task | Description | Agent | Can Parallel |
|----------|-------------|-------|--------------|
| user.py | User ORM model (unique email, username, hashed password) | sdd:developer | Yes |
| place.py | Place ORM model (Geography POINT, JSONB busyness_data) | sdd:developer | Yes |
| area.py | Area ORM model (Geography POLYGON, zone_type) | sdd:developer | Yes |
| visit.py | Visit ORM model (FKs to users, places, areas) | sdd:developer | Yes |
| models/__init__.py | Re-export all models | sdd:developer | After all models |
| alembic/env.py | Async engine support for migrations | sdd:developer | After models |
| 001_initial_schema.py | PostGIS extension, tables, GIST indexes | sdd:developer | After env.py |

- [ ] Create `backend/app/models/user.py` with User ORM model (unique email, unique username, hashed password, xp default 0, level default 1)
- [ ] Create `backend/app/models/place.py` with Place ORM model (Geography POINT coordinates, JSONB busyness_data, nullable busyness_updated_at)
- [ ] Create `backend/app/models/area.py` with Area ORM model (Geography POLYGON boundary, zone_type enum string)
- [ ] Create `backend/app/models/visit.py` with Visit ORM model (ForeignKey to users, places, areas; computed duration_seconds)
- [ ] Create `backend/app/models/__init__.py` re-exporting User, Place, Area, Visit
- [ ] Create `backend/alembic/env.py` with async engine support (run_sync pattern for migrations)
- [ ] Create `backend/alembic/versions/001_initial_schema.py` with PostGIS extension, tables, GIST indexes
- [ ] Verify migration runs against Docker PostGIS container: `docker compose up db && alembic upgrade head`

#### Dependencies

- Step 2a (db/base.py for DeclarativeBase, db/session.py for engine)

#### Blockers

- PostGIS Docker container must be running for migration verification

#### Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| GeoAlchemy2 + asyncpg version incompatibility | Medium | Pin geoalchemy2>=0.15, sqlalchemy>=2.0, asyncpg>=0.30 as per skill file; test with raw SQL if ORM spatial functions fail |
| Alembic async engine issues | Medium | Use synchronous connection URL in alembic/env.py for migrations (replace asyncpg with psycopg2 in migration URL) |

#### Verification

**Level:** CRITICAL - Panel of 2 Judges with Aggregated Voting
**Artifact:** `backend/app/models/` (user.py, place.py, area.py, visit.py, __init__.py) + `backend/alembic/` (env.py, versions/001_initial_schema.py)
**Threshold:** 4.0/5.0

**Rubric:**

| Criterion | Weight | Description |
|-----------|--------|-------------|
| Data Integrity | 0.30 | User has unique constraints on email and username; Visit has FKs to users.id, places.id, areas.id (nullable); all models use integer PKs for future FK references |
| Spatial Correctness | 0.25 | Place.coordinates uses Geography(geometry_type="POINT", srid=4326); Area.boundary uses Geography(geometry_type="POLYGON", srid=4326); GIST indexes on both spatial columns |
| Migration Safety | 0.20 | Migration 001 executes CREATE EXTENSION IF NOT EXISTS postgis; creates all tables, GIST indexes, standard indexes (visits.user_id, visits.place_id, places.category); downgrade drops cleanly |
| Completeness | 0.15 | All 4 models present with all specified columns; models/__init__.py re-exports; alembic/env.py uses run_async pattern; busyness_data is JSONB type |
| Naming | 0.10 | Table names, column names, index names follow project conventions; consistent with Expected Changes tree |

**Reference Pattern:** `.claude/skills/fastapi-postgis-backend/SKILL.md` (GeoAlchemy2 model patterns)

---

### Step 4: Pydantic Schemas

**Model:** opus
**Agent:** sdd:developer
**Depends on:** Step 3
**Parallel with:** Step 5a, Step 9 (all three depend on Step 3; MUST be launched in parallel)

**Goal**: Define all request and response Pydantic models that form the API contract between backend and mobile apps. These schemas enforce input validation and shape output serialization.

**Phase**: Schemas | **Complexity**: Small | **Uncertainty**: Low

#### Expected Output

- `backend/app/schemas/auth.py`: RegisterRequest (email validator, username min 3 chars, password min 8 chars), LoginRequest, TokenResponse (access_token, refresh_token, token_type, expires_in)
- `backend/app/schemas/place.py`: PlaceResponse, PlaceDetailResponse (with busyness_data, busyness_stale, busyness_updated_at), NearbyQueryParams (lat, lon, radius_m default 500, category optional), ForecastResponse
- `backend/app/schemas/visit.py`: GPSPingRequest (lat, lon, accuracy, timestamp), GPSPingResponse (nearby_places, confirmed_visits, rejected, rejection_reason), VisitResponse (id, place_id, place_name, area_id, started_at, ended_at, duration_seconds)
- `backend/app/schemas/user.py`: UserResponse
- `backend/app/schemas/__init__.py`: Package init

#### Success Criteria

- [ ] RegisterRequest rejects email without @ symbol, username under 3 characters, password under 8 characters (Pydantic field validators)
- [ ] NearbyQueryParams uses Query() annotations for GET parameter binding (not request body)
- [ ] PlaceDetailResponse includes busyness_stale boolean field and busyness_updated_at datetime nullable field
- [ ] GPSPingRequest includes accuracy float field for GPS accuracy validation
- [ ] GPSPingResponse includes nested lists for nearby_places and confirmed_visits
- [ ] TokenResponse includes refresh_token field alongside access_token
- [ ] All response schemas have `model_config = ConfigDict(from_attributes=True)` for ORM compatibility

#### Subtasks

**Note:** Individual schema files MUST be created in parallel by the agent, as they are independent of each other (standalone Pydantic models).

| Sub-task | Description | Agent | Can Parallel |
|----------|-------------|-------|--------------|
| auth.py | RegisterRequest, LoginRequest, TokenResponse | sdd:developer | Yes |
| place.py | PlaceResponse, PlaceDetailResponse, NearbyQueryParams, ForecastResponse | sdd:developer | Yes |
| visit.py | GPSPingRequest, GPSPingResponse, VisitResponse, NearbyPlaceInfo, ConfirmedVisitInfo | sdd:developer | Yes |
| user.py | UserResponse | sdd:developer | Yes |
| __init__.py | Package init | sdd:developer | Yes |
| test_schemas.py | Validation tests for registration rules, query defaults | sdd:developer | After schema files |

- [ ] Create `backend/app/schemas/auth.py` with RegisterRequest, LoginRequest, TokenResponse (including refresh_token)
- [ ] Create `backend/app/schemas/place.py` with PlaceResponse, PlaceDetailResponse, NearbyQueryParams, ForecastResponse
- [ ] Create `backend/app/schemas/visit.py` with GPSPingRequest, GPSPingResponse, VisitResponse, NearbyPlaceInfo, ConfirmedVisitInfo
- [ ] Create `backend/app/schemas/user.py` with UserResponse
- [ ] Create `backend/app/schemas/__init__.py`
- [ ] Write unit tests for schema validation in `backend/tests/test_schemas.py` (registration validation rules, NearbyQueryParams defaults)

#### Dependencies

- Step 3 (ORM models for field alignment)

#### Blockers

- None

#### Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Schema/model field mismatch | Low | Cross-reference schema fields against ORM model columns during implementation |

#### Verification

**Level:** Single Judge
**Artifact:** `backend/app/schemas/` (auth.py, place.py, visit.py, user.py, __init__.py) + `backend/tests/test_schemas.py`
**Threshold:** 4.0/5.0

**Rubric:**

| Criterion | Weight | Description |
|-----------|--------|-------------|
| Validation Correctness | 0.30 | RegisterRequest rejects invalid email, username < 3 chars, password < 8 chars; GPSPingRequest includes accuracy field; NearbyQueryParams uses Query() annotations |
| Contract Completeness | 0.25 | All schemas from Expected Output present; TokenResponse has both access_token and refresh_token; PlaceDetailResponse has busyness_stale and busyness_updated_at; GPSPingResponse has nested lists |
| ORM Compatibility | 0.20 | All response schemas have model_config = ConfigDict(from_attributes=True) |
| Consistency | 0.15 | Field types match ORM model columns; naming matches API Contracts section |
| Test Coverage | 0.10 | test_schemas.py validates registration rules and NearbyQueryParams defaults |

---

### Step 5a: API Dependencies (deps.py)

**Model:** opus
**Agent:** sdd:developer
**Depends on:** Step 2b, Step 3
**Parallel with:** Step 4, Step 9 (MUST be launched in parallel with Step 4 and Step 9 after Step 3 completes; Step 2b must also be complete)

**Goal**: Create the shared API dependency injection module that all API routers need: database session provider, authenticated user extraction from JWT, and Redis-backed rate limiter.

**Note**: deps.py depends only on session.py (Step 2a), security.py + redis.py (Step 2b), and User model (Step 3). It does NOT depend on schemas (Step 4). Extracting it as a separate step enables Steps 4 and 5a to run in parallel, shortening the critical path.

**Phase**: API Dependencies | **Complexity**: Small | **Uncertainty**: Low

#### Expected Output

- `backend/app/api/__init__.py`: Package init
- `backend/app/api/deps.py`: get_db(), get_current_user() dependencies, rate_limiter dependency

#### Success Criteria

- [ ] `api/deps.py` provides get_db() yielding AsyncSession from session factory
- [ ] `api/deps.py` provides get_current_user() using OAuth2PasswordBearer + decode_token + user lookup
- [ ] `api/deps.py` provides rate_limiter dependency using Redis-backed counters with configurable thresholds

#### Subtasks

| Sub-task | Description | Agent | Can Parallel |
|----------|-------------|-------|--------------|
| get_db() | Session dependency yielding AsyncSession | sdd:developer | Yes |
| get_current_user() | OAuth2PasswordBearer + JWT decode + DB lookup | sdd:developer | Yes |
| rate_limiter | Redis-backed counter with configurable thresholds | sdd:developer | Yes |

- [ ] Create `backend/app/api/__init__.py`
- [ ] Create `backend/app/api/deps.py` with get_db() session dependency
- [ ] Create get_current_user() dependency in deps.py (OAuth2PasswordBearer + decode_token + user lookup)
- [ ] Create rate_limiter dependency in deps.py (Redis-backed, configurable thresholds)

#### Dependencies

- Step 2a (db/session.py for get_db)
- Step 2b (core/security.py for decode_token, core/redis.py for rate_limiter)
- Step 3 (User model for get_current_user DB lookup)

#### Blockers

- None

#### Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| OAuth2PasswordBearer token extraction format | Low | Follow FastAPI security docs exactly; test with both Bearer prefix and raw token |

#### Verification

**Level:** Single Judge
**Artifact:** `backend/app/api/deps.py`
**Threshold:** 4.0/5.0

**Rubric:**

| Criterion | Weight | Description |
|-----------|--------|-------------|
| Security | 0.30 | get_current_user uses OAuth2PasswordBearer + decode_token + DB lookup; rate_limiter uses Redis counters with configurable thresholds (10 attempts/5 min) |
| Correctness | 0.30 | get_db yields AsyncSession from session factory; get_current_user extracts user from JWT; rate_limiter checks and increments counters |
| Code Quality | 0.20 | Uses FastAPI Depends() pattern correctly; proper async/await; type annotations |
| Error Handling | 0.20 | Missing/invalid token raises 401; rate limit exceeded raises 429; user not found raises 401 |

---

### Step 5b: Test Infrastructure

**Model:** opus
**Agent:** sdd:developer
**Depends on:** Step 4, Step 5a
**Parallel with:** None (Step 9 continues independently in parallel)

**Goal**: Create the shared test fixtures and configuration that all domain test suites will use: async test database with testcontainers PostGIS, async HTTP test client, authenticated user fixture, and Redis test instance.

**Phase**: Test Infrastructure | **Complexity**: Medium | **Uncertainty**: Medium

#### Expected Output

- `backend/tests/conftest.py`: Async fixtures for PostGIS test database, async session, FastAPI test client (httpx AsyncClient), seeded test user with valid JWT, Redis test instance
- `backend/tests/__init__.py`: Package init

#### Success Criteria

- [ ] `conftest.py` spins up a PostGIS container via testcontainers for test isolation
- [ ] Async session fixture creates tables, yields session, rolls back after each test
- [ ] Test client fixture provides httpx AsyncClient bound to the FastAPI app
- [ ] Authenticated user fixture registers a test user and provides valid JWT headers
- [ ] Redis fixture provides a clean Redis instance (or fakeredis) for each test
- [ ] A minimal smoke test passes: `pytest backend/tests/ -v` runs without errors

#### Subtasks

| Sub-task | Description | Agent | Can Parallel |
|----------|-------------|-------|--------------|
| __init__.py | Package init | sdd:developer | Yes |
| event_loop fixture | Session-scoped event loop | sdd:developer | Yes |
| PostGIS fixture | Testcontainers PostGIS + async engine + migrations | sdd:developer | Yes |
| session fixture | Function-scoped async session with rollback | sdd:developer | After PostGIS fixture |
| test client fixture | httpx AsyncClient with app override for get_db | sdd:developer | After session fixture |
| auth user fixture | Create test user + return JWT headers | sdd:developer | After test client |
| Redis fixture | fakeredis or test container | sdd:developer | Yes |
| smoke test | Minimal test verifying fixture chain | sdd:developer | After all fixtures |

- [ ] Create `backend/tests/__init__.py`
- [ ] Create `backend/tests/conftest.py` with event_loop fixture (session scope)
- [ ] Add PostGIS testcontainers fixture that creates async engine + runs migrations
- [ ] Add async session fixture (function scope) with rollback after each test
- [ ] Add FastAPI test client fixture using httpx AsyncClient with app override for get_db
- [ ] Add test user fixture that creates a user and returns auth headers
- [ ] Add Redis fixture (fakeredis or test container) for visit tracking and rate limiting tests
- [ ] Write a minimal smoke test to verify fixture chain works

#### Dependencies

- Step 1 (Dockerfile, docker-compose for container images)
- Step 2a (db/session.py for async engine)
- Step 2b (core/security.py for JWT creation in auth fixture, core/redis.py for Redis fixture)
- Step 3 (ORM models for table creation, User model for test user)
- Step 4 (schemas for test user creation helpers)
- Step 5a (deps.py for test client app dependency overrides)

#### Blockers

- Docker must be running for testcontainers

#### Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| testcontainers PostGIS setup complexity | Medium | Fall back to a pre-started Docker PostGIS container if testcontainers has issues; use conftest to detect and skip |
| Async test event loop conflicts | Medium | Use pytest-asyncio with session-scoped event loop; follow pytest-asyncio 0.25 patterns |

#### Verification

**Level:** Single Judge
**Artifact:** `backend/tests/conftest.py`
**Threshold:** 4.0/5.0

**Rubric:**

| Criterion | Weight | Description |
|-----------|--------|-------------|
| Coverage | 0.25 | PostGIS container fixture, async session fixture, test client fixture, auth user fixture, Redis fixture all present |
| Isolation | 0.25 | Each test gets clean DB state (rollback after each test); Redis instance is clean per test; no test pollution |
| Correctness | 0.25 | PostGIS testcontainers spins up; async session creates tables and rolls back; test client uses httpx AsyncClient; auth fixture provides valid JWT headers |
| Clarity | 0.15 | Fixture names are descriptive; scope is appropriate (session for PostGIS, function for session); smoke test passes |
| Maintainability | 0.10 | Fixtures are composable; easy to extend for new test suites; follows pytest-asyncio patterns |

---

### Step 6: Authentication Service, API, and Tests

**Model:** opus
**Agent:** sdd:developer
**Depends on:** Step 5b
**Parallel with:** Step 7 (both depend on Step 5b; MUST be launched in parallel)

**Goal**: Build the complete authentication domain: user registration with input validation and duplicate prevention, login with generic error messages, JWT access/refresh token issuance, credential refresh with token rotation, rate limiting on auth endpoints, and protected endpoint access via dependency injection.

**Note**: deps.py (get_db, get_current_user, rate_limiter) is already created in Step 5a. This step uses those dependencies but does not create them.

**Phase**: Auth Domain (Vertical Slice) | **Complexity**: Medium | **Uncertainty**: Low

#### Expected Output

- `backend/app/services/auth_service.py`: register_user(), authenticate_user(), create_token_pair(), refresh_token()
- `backend/app/api/auth.py`: POST /auth/register, POST /auth/login, POST /auth/refresh
- `backend/tests/test_auth.py`: Tests for all 9 authentication acceptance criteria

#### Success Criteria

- [ ] POST /auth/register creates a user and returns TokenResponse with access_token and refresh_token
- [ ] POST /auth/register returns 400 with field-specific errors for invalid email, short username, or short password
- [ ] POST /auth/register returns 409 when email or username is already taken
- [ ] POST /auth/login returns TokenResponse for valid credentials
- [ ] POST /auth/login returns 401 with generic "Invalid credentials" message (no email/password distinction)
- [ ] POST /auth/refresh accepts refresh_token in Authorization header, returns new token pair, invalidates old refresh token
- [ ] POST /auth/refresh returns 401 for expired refresh token
- [ ] Protected endpoints return 401 when called without Authorization header
- [ ] Protected endpoints return 401 when called with expired access token
- [ ] Rate limiter blocks auth requests after 10 failed attempts in 5 minutes from same IP for at least 15 minutes
- [ ] get_current_user dependency extracts user from JWT and injects into endpoint
- [ ] All tests in `tests/test_auth.py` pass

#### Subtasks

| Sub-task | Description | Agent | Can Parallel |
|----------|-------------|-------|--------------|
| auth_service.py: register_user() | Check duplicates, hash password, insert user | sdd:developer | Yes |
| auth_service.py: authenticate_user() | Lookup by email, verify password | sdd:developer | Yes |
| auth_service.py: create_token_pair() | Generate access + refresh JWTs | sdd:developer | Yes |
| auth_service.py: refresh_token() | Decode refresh, validate, issue new pair | sdd:developer | Yes |
| api/auth.py: register endpoint | POST /auth/register | sdd:developer | After service |
| api/auth.py: login endpoint | POST /auth/login | sdd:developer | After service |
| api/auth.py: refresh endpoint | POST /auth/refresh | sdd:developer | After service |
| test_auth.py | All 9 acceptance criteria tests | sdd:developer | After API |

- [ ] Create `backend/app/services/auth_service.py` with register_user() (check duplicates, hash password, insert user)
- [ ] Create authenticate_user() in auth_service.py (lookup by email, verify password, return user or None)
- [ ] Create create_token_pair() in auth_service.py (generate access + refresh JWTs)
- [ ] Create refresh_token() in auth_service.py (decode refresh token, validate type, issue new pair)
- [ ] Create `backend/app/api/auth.py` with POST /auth/register endpoint
- [ ] Create POST /auth/login endpoint in auth.py
- [ ] Create POST /auth/refresh endpoint in auth.py
- [ ] Write tests in `backend/tests/test_auth.py`: registration success, validation failures, duplicate prevention, login success, invalid credentials, token refresh, expired token, rate limiting

#### Dependencies

- Step 2b (security.py for JWT/bcrypt, redis.py for rate limiting, exceptions.py)
- Step 3 (User model)
- Step 4 (auth schemas)
- Step 5a (api/deps.py)
- Step 5b (test fixtures)

#### Blockers

- None

#### Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Rate limiter Redis interaction complexity | Low | Start with simple counter + TTL pattern; upgrade to sliding window if needed |

#### Verification

**Level:** CRITICAL - Panel of 2 Judges with Aggregated Voting
**Artifact:** `backend/app/services/auth_service.py` + `backend/app/api/auth.py` + `backend/tests/test_auth.py`
**Threshold:** 4.0/5.0

**Rubric:**

| Criterion | Weight | Description |
|-----------|--------|-------------|
| Security | 0.25 | Passwords stored as bcrypt hashes (never plaintext); login returns generic error (no email/password distinction); rate limiter blocks after 10 failed attempts for 15 min; refresh invalidates old token |
| Correctness | 0.25 | Register creates user + returns TokenResponse; login validates credentials + returns TokenResponse; refresh issues new pair; all 9 acceptance criteria behaviors implemented |
| Error Handling | 0.20 | 400 for validation failures with field-specific messages; 409 for duplicate email/username; 401 for invalid/expired credentials; 429 for rate limiting |
| Test Coverage | 0.20 | test_auth.py covers: registration success, validation failures, duplicate prevention, login success, invalid credentials, token refresh, expired token, protected endpoint access, rate limiting |
| Code Quality | 0.10 | Uses deps.py dependencies (not reimplemented); follows FastAPI patterns; async/await throughout |

**Reference Pattern:** `.claude/skills/fastapi-postgis-backend/SKILL.md` (auth patterns)

---

### Step 7: Places Service, Forecast, API, and Tests

**Model:** opus
**Agent:** sdd:developer
**Depends on:** Step 5b
**Parallel with:** Step 6 (both depend on Step 5b; MUST be launched in parallel)

**Goal**: Build the complete places domain: nearby places search using PostGIS ST_DWithin with optional category filtering, place detail with full busyness data, busyness forecast from histogram data, staleness detection for outdated busyness data, and graceful handling of places with no busyness data.

**Note**: deps.py (get_db, get_current_user) is already created in Step 5a, so this step has NO dependency on Step 6 (Auth).

**Phase**: Places Domain (Vertical Slice) | **Complexity**: Medium | **Uncertainty**: Medium

#### Expected Output

- `backend/app/services/places_service.py`: get_nearby_places() with ST_DWithin + category filter + staleness, get_place_detail()
- `backend/app/services/forecast_service.py`: predict_busyness() from histogram lookup
- `backend/app/api/places.py`: GET /places/nearby, GET /places/{id}, GET /places/{id}/forecast
- `backend/tests/test_places.py`: Tests for all 6 places acceptance criteria

#### Success Criteria

- [ ] GET /places/nearby returns places within specified radius using PostGIS ST_DWithin with Geography type (meters)
- [ ] GET /places/nearby accepts optional category query parameter and filters results
- [ ] GET /places/nearby results include current_busyness (int or null) and busyness_stale (bool) per place
- [ ] GET /places/nearby results are ordered by distance from user coordinates
- [ ] GET /places/{id} returns full place detail including busyness_data with popular_times histogram and current_popularity
- [ ] GET /places/{id} returns busyness fields as null when no busyness data exists (no error)
- [ ] GET /places/{id} includes busyness_stale=true and busyness_updated_at when data is older than 7 days
- [ ] GET /places/{id}/forecast returns predicted_busyness for given day (0-6) and hour (0-23)
- [ ] GET /places/{id}/forecast returns 404 for non-existent place
- [ ] Nearby search returns results within 2 seconds for 500m radius (performance target)
- [ ] All tests in `tests/test_places.py` pass

#### Subtasks

| Sub-task | Description | Agent | Can Parallel |
|----------|-------------|-------|--------------|
| places_service.py: get_nearby_places() | ST_DWithin query + category filter + staleness | sdd:developer | Yes |
| places_service.py: get_place_detail() | Full place with busyness data | sdd:developer | Yes |
| forecast_service.py: predict_busyness() | Histogram lookup for day/hour | sdd:developer | Yes |
| api/places.py: nearby endpoint | GET /places/nearby with NearbyQueryParams | sdd:developer | After services |
| api/places.py: detail endpoint | GET /places/{id} | sdd:developer | After services |
| api/places.py: forecast endpoint | GET /places/{id}/forecast | sdd:developer | After services |
| test_places.py | All 6 acceptance criteria + edge cases | sdd:developer | After API |

- [ ] Create `backend/app/services/places_service.py` with get_nearby_places(db, lat, lon, radius_m, category=None)
- [ ] Implement ST_DWithin query with Geography cast: `cast(ST_MakePoint(lon, lat), Geography)`
- [ ] Add optional category WHERE clause to nearby query
- [ ] Add ST_Distance ordering to nearby query results
- [ ] Implement staleness detection: compare busyness_updated_at against 7-day threshold
- [ ] Create get_place_detail(db, place_id) returning full place with busyness data
- [ ] Create `backend/app/services/forecast_service.py` with predict_busyness(busyness_data, day, hour)
- [ ] Implement histogram lookup: busyness_data["popular_times"][day]["hours"][hour]
- [ ] Create `backend/app/api/places.py` with GET /places/nearby using NearbyQueryParams via Depends
- [ ] Create GET /places/{id} endpoint returning PlaceDetailResponse
- [ ] Create GET /places/{id}/forecast endpoint accepting day and hour query params
- [ ] Seed test places with PostGIS coordinates in test fixtures
- [ ] Write tests in `backend/tests/test_places.py`: nearby search, category filter, place detail, no busyness data, staleness indicator, forecast

#### Dependencies

- Step 2a (db/session.py)
- Step 3 (Place model with Geography column)
- Step 4 (place schemas)
- Step 5a (api/deps.py for get_current_user and get_db)
- Step 5b (test fixtures)

#### Blockers

- GIST index must exist on places.coordinates for performance (created in Step 3 migration)

#### Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| GeoAlchemy2 ST_DWithin with AsyncSession issues | Medium | Test with raw SQL first (`SELECT ... WHERE ST_DWithin(...)`) to verify PostGIS works, then wrap in ORM |
| Geography type serialization in Pydantic response | Medium | Extract lat/lon from WKB element using ST_X/ST_Y functions or shapely; do not return raw Geography bytes |

#### Verification

**Level:** CRITICAL - Panel of 2 Judges with Aggregated Voting
**Artifact:** `backend/app/services/places_service.py` + `backend/app/services/forecast_service.py` + `backend/app/api/places.py` + `backend/tests/test_places.py`
**Threshold:** 4.0/5.0

**Rubric:**

| Criterion | Weight | Description |
|-----------|--------|-------------|
| Spatial Correctness | 0.25 | ST_DWithin with Geography type (meters, not degrees); cast(ST_MakePoint(lon, lat), Geography); ST_Distance ordering; GIST index utilized |
| Correctness | 0.25 | Nearby returns places within radius; category filter works; place detail includes busyness_data; forecast returns predicted_busyness from histogram; null busyness handled gracefully; staleness flagged at 7 days |
| API Contract | 0.20 | All 3 endpoints match Contracts section exactly; response shapes match PlaceResponse/PlaceDetailResponse/ForecastResponse; proper error codes (404, 401) |
| Test Coverage | 0.20 | test_places.py covers: nearby search, category filter, place detail, no busyness data, staleness indicator, forecast; test places seeded with PostGIS coordinates |
| Performance | 0.10 | Query should be efficient (uses GIST index, not sequential scan); designed for <2s at 500m/200 places |

**Reference Pattern:** `.claude/skills/fastapi-postgis-backend/SKILL.md` (PostGIS spatial query patterns)

---

### Step 8: Visit Tracking Service, API, and Tests

**Model:** opus
**Agent:** sdd:developer
**Depends on:** Step 7
**Parallel with:** None (Step 6 continues independently in parallel if not yet finished)

**Goal**: Build the complete visit tracking domain: GPS ping processing that finds nearby places, UserPresence state machine in Redis for tracking dwell time, automatic visit confirmation when threshold is met, GPS accuracy rejection, concurrent multi-place tracking, duplicate visit prevention, and visit history retrieval.

**Note**: This step depends on Step 7 (places_service.get_nearby_places) but NOT on Step 6 (Auth). The visit_service never calls auth_service. The visit API endpoints use get_current_user from deps.py (Step 5a, already completed) and places_service (Step 7). Step 6 is NOT a dependency.

**Phase**: Visits Domain (Vertical Slice) | **Complexity**: Large | **Uncertainty**: Medium

#### Expected Output

- `backend/app/services/visit_service.py`: process_gps_ping(), auto_confirm_visit(), get_visit_history()
- `backend/app/api/visits.py`: POST /visits/ping, GET /visits/history
- `backend/tests/test_visits.py`: Tests for all 5 visit tracking acceptance criteria plus edge cases

#### Success Criteria

- [ ] POST /visits/ping with accuracy > 100m returns 422 with rejection reason "GPS accuracy insufficient"
- [ ] POST /visits/ping finds all places within 75m (configurable) using places_service.get_nearby_places()
- [ ] POST /visits/ping creates or updates UserPresence in Redis for each nearby place (first_seen, last_seen, reading_count)
- [ ] When UserPresence dwell time >= 5 minutes AND reading_count >= 3, visit is auto-confirmed: Visit record created in DB, UserPresence deleted from Redis
- [ ] POST /visits/ping response includes nearby_places list, confirmed_visits list, and rejected flag
- [ ] Two places within 75m of user are tracked independently (separate UserPresence keys)
- [ ] Duplicate visits prevented: if Visit already exists for user+place in current session (last 2 hours), no new Visit is created
- [ ] UserPresence entries in Redis have 30-minute TTL (safety net for abandoned sessions)
- [ ] N consecutive out-of-range pings clear UserPresence (GPS jitter protection)
- [ ] GET /visits/history returns paginated list of user visits with place_name, area_id, timestamps, duration
- [ ] Visit records are app-agnostic (no app identifier column) -- shared across both apps
- [ ] All tests in `tests/test_visits.py` pass

#### Subtasks

| Sub-task | Description | Agent | Can Parallel |
|----------|-------------|-------|--------------|
| visit_service.py: process_gps_ping() | GPS accuracy check + find nearby + UserPresence mgmt | sdd:developer | No (core logic) |
| visit_service.py: auto_confirm_visit() | Create Visit record, delete UserPresence | sdd:developer | After process_gps_ping |
| visit_service.py: get_visit_history() | Paginated query with place join | sdd:developer | Yes |
| api/visits.py: ping endpoint | POST /visits/ping with auth | sdd:developer | After service |
| api/visits.py: history endpoint | GET /visits/history with pagination | sdd:developer | After service |
| test_visits.py | All 5 acceptance criteria + edge cases | sdd:developer | After API |

- [ ] Create `backend/app/services/visit_service.py` with process_gps_ping(redis, db, user_id, lat, lon, accuracy, timestamp)
- [ ] Implement GPS accuracy validation (reject if accuracy > 100m)
- [ ] Call places_service.get_nearby_places(db, lat, lon, radius_m=settings.geofence_radius_m) to find geofence matches
- [ ] For each nearby place: get or create UserPresence in Redis (user_presence:{user_id}:{place_id})
- [ ] Update UserPresence: set last_seen=timestamp, increment reading_count
- [ ] Check auto-confirm condition: (last_seen - first_seen >= settings.visit_min_duration_seconds) AND (reading_count >= settings.visit_min_readings)
- [ ] Implement auto_confirm_visit(): create Visit record in DB, delete UserPresence from Redis
- [ ] Implement duplicate visit prevention: check for existing Visit with same user+place within last 2 hours
- [ ] Handle out-of-range tracking: if user previously near a place but not in current ping, track consecutive misses; clear UserPresence after N consecutive misses
- [ ] Create get_visit_history(db, user_id, limit, offset) with joins to places table for place_name
- [ ] Create `backend/app/api/visits.py` with POST /visits/ping endpoint (requires auth)
- [ ] Create GET /visits/history endpoint with limit/offset pagination
- [ ] Write tests in `backend/tests/test_visits.py`: GPS ping with nearby places, accuracy rejection, dwell time auto-confirm, multi-place tracking, duplicate prevention, visit history, out-of-range clearing

#### Dependencies

- Step 2b (redis.py for UserPresence helpers, exceptions.py)
- Step 3 (Visit model, Place model)
- Step 4 (visit schemas)
- Step 5a (api/deps.py for get_current_user and get_db)
- Step 5b (test fixtures with Redis)
- Step 7 (places_service.get_nearby_places -- CRITICAL runtime dependency)

#### Blockers

- Places service (Step 7) must be complete for the geofence proximity query

#### Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Redis UserPresence state machine edge cases (race conditions, TTL expiry during active session) | Medium | Use Redis WATCH/MULTI for atomic updates; set TTL generously (30 min); test extensively with time mocking |
| GPS jitter causing false visit confirmations or premature clears | Medium | Require minimum reading_count (3+) AND dwell time; require N consecutive out-of-range before clearing |

#### Verification

**Level:** CRITICAL - Panel of 2 Judges with Aggregated Voting
**Artifact:** `backend/app/services/visit_service.py` + `backend/app/api/visits.py` + `backend/tests/test_visits.py`
**Threshold:** 4.0/5.0

**Rubric:**

| Criterion | Weight | Description |
|-----------|--------|-------------|
| State Machine Correctness | 0.25 | UserPresence lifecycle: create on first nearby ping, update last_seen/reading_count on subsequent pings, auto-confirm when dwell >= 5min AND readings >= 3, delete after confirm, clear after N consecutive out-of-range |
| Correctness | 0.25 | GPS accuracy > 100m rejected with 422; nearby places found via places_service; concurrent multi-place tracking (separate Redis keys); duplicate visit prevention (same user+place within 2h); UserPresence TTL 30min |
| Error Handling | 0.15 | Accuracy rejection returns clear reason; out-of-range handling with GPS jitter protection; Redis failures handled gracefully |
| Test Coverage | 0.20 | test_visits.py covers: GPS ping with nearby places, accuracy rejection, dwell time auto-confirm, multi-place tracking, duplicate prevention, visit history, out-of-range clearing |
| Code Quality | 0.15 | Visit records are app-agnostic; uses configurable thresholds from settings; proper async/await; clean separation of service/API |

**Reference Pattern:** `.claude/skills/fastapi-postgis-backend/SKILL.md` (visit tracking and Redis patterns)

---

### Step 9: Scraping Pipeline and Tests

**Model:** opus
**Agent:** sdd:developer
**Depends on:** Step 2b, Step 3
**Parallel with:** Step 4, Step 5a (MUST be launched in parallel with Steps 4 and 5a after Step 3 completes). Continues independently alongside Steps 5b, 6, 7, 8.

**Goal**: Build the ARQ-based scraping pipeline with two scheduled tasks: weekly popular times histogram collection and periodic (every 15 min) live busyness refresh for active places. Implement activity-based prioritization so high-activity places are scraped at least 3x more frequently than inactive ones. Ensure failure resilience with logging and retry-on-next-cycle behavior.

**Note**: Scraping workers are fully independent from the API layer. They create their own AsyncSession (not request-scoped) and depend only on the database layer (Step 2a via Step 3), Redis client (Step 2b), and Place model (Step 3).

**Phase**: Scraping Pipeline | **Complexity**: Medium | **Uncertainty**: Medium

#### Expected Output

- `backend/app/workers/scraping.py`: ARQ WorkerSettings, scrape_popular_times() task, scrape_live_busyness() task, priority calculation logic
- `backend/tests/test_scraping.py`: Tests for scraping logic with mocked external calls

#### Success Criteria

- [ ] ARQ WorkerSettings defines cron jobs: scrape_popular_times (weekly), scrape_live_busyness (every 15 min)
- [ ] scrape_popular_times() queries all places, ordered by activity-based priority, and updates busyness_data JSONB + busyness_updated_at
- [ ] scrape_live_busyness() queries only places with recent user activity (GPS pings within last 30 min)
- [ ] Activity-based priority: places with user activity in last 24h are scraped at least 3x more frequently than inactive places
- [ ] Scraping uses populartimes library (abstracted behind function call for future swap to outscraper)
- [ ] Individual place scrape failures are caught, logged, and place is marked for retry in next cycle
- [ ] Failed scrapes do not interrupt processing of remaining places
- [ ] Pipeline respects throughput target of 100 places/hour (with delays between requests)
- [ ] Worker creates its own AsyncSession (not request-scoped)
- [ ] All tests in `tests/test_scraping.py` pass (with mocked populartimes responses)

#### Subtasks

| Sub-task | Description | Agent | Can Parallel |
|----------|-------------|-------|--------------|
| ARQ WorkerSettings | Class with cron_jobs definitions | sdd:developer | Yes |
| scrape_popular_times() | Query places by priority, fetch + update JSONB | sdd:developer | Yes |
| scrape_live_busyness() | Query active places, fetch current_popularity | sdd:developer | Yes |
| Priority scoring | Activity-based prioritization logic | sdd:developer | Yes |
| Scraping abstraction | fetch_place_busyness() wrapper for library swap | sdd:developer | Yes |
| Failure resilience | Per-place try/except + logging + retry marking | sdd:developer | After core tasks |
| test_scraping.py | Mock responses, DB updates, failure, priority | sdd:developer | After implementation |

- [ ] Create `backend/app/workers/scraping.py` with ARQ WorkerSettings class
- [ ] Define cron_jobs in WorkerSettings: weekly popular times, 15-min live busyness
- [ ] Implement scrape_popular_times(ctx) task: query places by priority, call populartimes.get_id(), update Place.busyness_data
- [ ] Implement activity-based priority scoring: count GPS pings near each place in last 24h from Redis or DB
- [ ] Implement scrape_live_busyness(ctx) task: query active places, fetch current_popularity, update JSONB
- [ ] Abstract scraping call behind a function (e.g., fetch_place_busyness(google_place_id)) for future library swap
- [ ] Add try/except per place with logging and retry marking on failure
- [ ] Add inter-request delay to respect 100 places/hour throughput limit
- [ ] Create own AsyncSessionLocal in worker context (per skill file guidance)
- [ ] Write tests in `backend/tests/test_scraping.py`: mock populartimes responses, verify DB updates, verify failure resilience, verify priority ordering

#### Dependencies

- Step 2a (db/session.py for own AsyncSession)
- Step 2b (core/redis.py for activity queries)
- Step 3 (Place model)

#### Blockers

- None (scraping workers are independent from API layer)

#### Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| populartimes library breaks due to Google Maps API changes | High | Abstract behind interface; implement graceful degradation returning stale data; have outscraper as backup |
| Rate limiting by Google Maps | Medium | Add configurable delay between requests; respect 100 places/hour throughput target; implement exponential backoff |

#### Verification

**Level:** Single Judge
**Artifact:** `backend/app/workers/scraping.py` + `backend/tests/test_scraping.py`
**Threshold:** 4.0/5.0

**Rubric:**

| Criterion | Weight | Description |
|-----------|--------|-------------|
| Correctness | 0.25 | ARQ WorkerSettings with cron jobs (weekly popular times, 15-min live busyness); scrape_popular_times updates busyness_data JSONB + busyness_updated_at; scrape_live_busyness targets only active places |
| Priority Logic | 0.20 | Activity-based scoring: places with user activity in last 24h scraped 3x+ more frequently; live busyness targets places with GPS pings in last 30min |
| Failure Resilience | 0.20 | Per-place try/except; failures logged; place marked for retry next cycle; remaining places continue; no cascade failure |
| Architecture | 0.20 | Scraping abstracted behind function (fetch_place_busyness) for library swap; worker creates own AsyncSession; respects 100 places/hour throughput with inter-request delays |
| Test Coverage | 0.15 | test_scraping.py with mocked populartimes: DB updates verified, failure resilience tested, priority ordering tested |

---

### Step 10: Application Entry Point, Integration, and Polish

**Model:** opus
**Agent:** sdd:developer
**Depends on:** Step 6, Step 8, Step 9
**Parallel with:** None (final integration step, waits for all domain slices)

**Goal**: Create the FastAPI application entry point with lifespan management (DB pool, Redis, ARQ connection pool initialization and cleanup), register all API routers, add health check endpoint, and write end-to-end integration tests that exercise the complete primary flow: register, login, search places, ping GPS, confirm visit.

**Phase**: Integration & Polish | **Complexity**: Medium | **Uncertainty**: Low

#### Expected Output

- `backend/app/main.py`: FastAPI app with lifespan, all routers registered, CORS middleware, health check
- `backend/tests/test_integration.py`: End-to-end test of primary user flow

#### Success Criteria

- [ ] `app/main.py` defines FastAPI app with lifespan context manager
- [ ] Lifespan startup initializes: async DB engine, Redis connection, ARQ connection pool
- [ ] Lifespan shutdown closes: DB engine, Redis connection
- [ ] All routers registered: auth (prefix=/auth), places (prefix=/places), visits (prefix=/visits)
- [ ] GET /health returns 200 with {status: "ok"} without authentication
- [ ] CORS middleware configured for mobile app origins
- [ ] Global exception handlers registered from core/exceptions.py
- [ ] Application starts successfully with `uvicorn app.main:app`
- [ ] End-to-end test passes: register user -> login -> search nearby places -> ping GPS near a place -> verify visit auto-confirmed after repeated pings
- [ ] All error responses follow consistent format: {error_type, message, status_code}

#### Subtasks

| Sub-task | Description | Agent | Can Parallel |
|----------|-------------|-------|--------------|
| main.py: app init | FastAPI app with metadata | sdd:developer | Yes |
| main.py: lifespan | DB pool + Redis startup/shutdown | sdd:developer | Yes |
| main.py: routers | Register auth, places, visits routers | sdd:developer | After routers exist |
| main.py: middleware | CORS + exception handlers | sdd:developer | Yes |
| main.py: health check | GET /health endpoint | sdd:developer | Yes |
| test_integration.py | E2E test of primary user flow | sdd:developer | After main.py |

- [ ] Create `backend/app/main.py` with FastAPI app initialization
- [ ] Implement lifespan context manager with DB pool + Redis startup/shutdown
- [ ] Register auth, places, and visits routers with appropriate prefixes and tags
- [ ] Add CORS middleware configuration
- [ ] Add health check endpoint (GET /health, no auth required)
- [ ] Register global exception handlers from core/exceptions.py
- [ ] Write end-to-end integration test in `backend/tests/test_integration.py` covering the primary flow
- [ ] Verify `docker compose up` starts all services and API responds to requests
- [ ] Verify API documentation is accessible at /docs (Swagger UI) and /redoc

#### Dependencies

- Step 6 (auth router and service)
- Step 7 (places router and service -- implicit via Step 8)
- Step 8 (visits router and service)
- Step 9 (scraping worker for ARQ connection in lifespan)

#### Blockers

- All API routers must be implemented before registration

#### Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Lifespan ordering issues (DB before Redis, etc.) | Low | Follow skill file lifespan pattern; test startup/shutdown sequence |

#### Verification

**Level:** CRITICAL - Panel of 2 Judges with Aggregated Voting
**Artifact:** `backend/app/main.py` + `backend/tests/test_integration.py`
**Threshold:** 4.0/5.0

**Rubric:**

| Criterion | Weight | Description |
|-----------|--------|-------------|
| Correctness | 0.25 | FastAPI app with lifespan context manager; startup initializes DB engine, Redis, ARQ pool; shutdown closes all; all routers registered with correct prefixes (/auth, /places, /visits) |
| Integration Completeness | 0.25 | E2E test covers full primary flow: register -> login -> search nearby -> ping GPS -> verify visit auto-confirmed; tests exercise real service interactions |
| Error Handling | 0.20 | Global exception handlers from core/exceptions.py registered; all errors follow consistent format (error_type, message, status_code); CORS middleware configured |
| API Surface | 0.15 | Health check at GET /health (no auth); Swagger UI at /docs; all routers tagged; application starts with uvicorn app.main:app |
| Code Quality | 0.15 | Clean lifespan ordering (DB before Redis); proper middleware registration order; no circular imports |

---

## Implementation Summary

| Step | Phase | Goal | Key Output | Est. Effort | Depends On | Parallel With |
|------|-------|------|------------|-------------|------------|---------------|
| 1 | Setup | Project skeleton and Docker infrastructure | docker-compose.yml, Dockerfile, requirements.txt, config.py | Small | - | - |
| 2a | Foundation | Async DB engine and DeclarativeBase | db/base.py, db/session.py | Small | Step 1 | **Step 2b** |
| 2b | Foundation | Security (JWT/bcrypt), Redis client, error handling | security.py, redis.py, exceptions.py | Medium | Step 1 | **Step 2a** |
| 3 | Data Models | Shared ORM models with PostGIS + Alembic migration | user.py, place.py, area.py, visit.py, 001_initial_schema.py | Medium | Step 2a | - |
| 4 | Schemas | Pydantic request/response models for API contract | schemas/auth.py, place.py, visit.py, user.py | Small | Step 3 | **Steps 5a, 9** |
| 5a | API Deps | Shared API dependency injection (get_db, get_current_user, rate_limiter) | api/deps.py | Small | Steps 2b, 3 | **Steps 4, 9** |
| 5b | Test Infra | Async test fixtures (PostGIS, session, client, auth, Redis) | tests/conftest.py | Medium | Steps 4, 5a | - |
| 6 | Auth Domain | Registration, login, JWT refresh, rate limiting | auth_service.py, api/auth.py, test_auth.py | Medium | Step 5b | **Step 7** |
| 7 | Places Domain | Nearby search with PostGIS, forecast, staleness | places_service.py, forecast_service.py, api/places.py, test_places.py | Medium | Step 5b | **Step 6** |
| 8 | Visits Domain | GPS ping, UserPresence state machine, auto-confirm | visit_service.py, api/visits.py, test_visits.py | Large | Step 7 | - |
| 9 | Scraping | ARQ workers for popular times + live busyness | workers/scraping.py, test_scraping.py | Medium | Steps 2b, 3 | **Steps 4, 5a** |
| 10 | Integration | App entry point, lifespan, E2E tests | main.py, test_integration.py | Medium | Steps 6, 8, 9 | - |

**Total Steps**: 12 (from 10 original, split Steps 2 and 5 for parallelism)
**Total Subtasks**: 95
**Critical Path**: Steps 1 -> 2a -> 3 -> 4 -> 5b -> 7 -> 8 -> 10 (8 stages, but with parallel work reducing wall-clock time at each branch)
**Parallel Opportunities**:
- Steps 2a + 2b MUST run in parallel after Step 1
- Steps 4 + 5a + 9 MUST run in parallel after Step 3 (and 2b)
- Steps 6 + 7 MUST run in parallel after Step 5b
- Step 8 starts when Step 7 finishes (does NOT wait for Step 6)
- Step 9 runs independently alongside Steps 5b-8 (joins only at Step 10)
- Step 6 runs independently alongside Steps 7-8 (joins at Step 10)
**Max Parallel Depth**: 3 agents simultaneously (Steps 4 + 5a + 9; or Steps 6 + 7 + 9)
**Estimated Total Effort**: Large (8-12 development days)

---

## Verification Summary

| Step | Verification Level | Judges | Threshold | Artifacts |
|------|-------------------|--------|-----------|-----------|
| 1 | Single Judge | 1 | 4.0/5.0 | Project skeleton: docker-compose.yml, Dockerfile, .env.example, requirements.txt, alembic.ini, config.py |
| 2a | Single Judge | 1 | 4.0/5.0 | Database layer: db/base.py, db/session.py |
| 2b | CRITICAL - Panel (2) | 2 | 4.0/5.0 | Core utilities: security.py, redis.py, exceptions.py, test_core_security.py |
| 3 | CRITICAL - Panel (2) | 2 | 4.0/5.0 | ORM models + migration: user.py, place.py, area.py, visit.py, alembic env + 001_initial_schema |
| 4 | Single Judge | 1 | 4.0/5.0 | Pydantic schemas: auth.py, place.py, visit.py, user.py, test_schemas.py |
| 5a | Single Judge | 1 | 4.0/5.0 | API dependencies: deps.py (get_db, get_current_user, rate_limiter) |
| 5b | Single Judge | 1 | 4.0/5.0 | Test infrastructure: conftest.py |
| 6 | CRITICAL - Panel (2) | 2 | 4.0/5.0 | Auth domain: auth_service.py, api/auth.py, test_auth.py |
| 7 | CRITICAL - Panel (2) | 2 | 4.0/5.0 | Places domain: places_service.py, forecast_service.py, api/places.py, test_places.py |
| 8 | CRITICAL - Panel (2) | 2 | 4.0/5.0 | Visit tracking: visit_service.py, api/visits.py, test_visits.py |
| 9 | Single Judge | 1 | 4.0/5.0 | Scraping pipeline: workers/scraping.py, test_scraping.py |
| 10 | CRITICAL - Panel (2) | 2 | 4.0/5.0 | Integration: main.py, test_integration.py |

**Total Evaluations:** 18 (6 single-judge + 6 panel-of-2 steps = 6 + 12 = 18)
**Implementation Command:** `/implement .specs/tasks/draft/implement-shared-backend.feature.md`

---

## Risks & Blockers Summary

### High Priority

| Risk/Blocker | Impact | Likelihood | Mitigation |
|--------------|--------|------------|------------|
| GeoAlchemy2 + asyncpg + SQLAlchemy version incompatibility | High | Medium | Pin exact versions from skill file; test spatial queries with raw SQL as fallback |
| populartimes library breaks (Google Maps API changes) | High | High | Abstract scraping behind interface; have outscraper as production backup; degrade gracefully with stale data |
| Redis UserPresence race conditions in concurrent pings | Medium | Medium | Use Redis atomic operations (WATCH/MULTI or Lua scripts); set generous TTLs; test with concurrent requests |
| Alembic async engine migration failures | Medium | Medium | Use sync URL (psycopg2) in alembic/env.py for migrations; keep async URL for runtime only |
| testcontainers PostGIS setup complexity | Medium | Medium | Fall back to pre-started Docker PostGIS if testcontainers fails; document manual setup alternative |
| Connection pool starvation under 1000 concurrent users | High | Low | Set pool_size=20, max_overflow=80; set PostgreSQL max_connections=200; monitor in load tests |

### Low Priority

| Risk/Blocker | Impact | Likelihood | Mitigation |
|--------------|--------|------------|------------|
| GPS jitter causing false visit confirmations | Low | Medium | Require minimum 3 readings + 5 min dwell; N consecutive out-of-range before clearing |
| Scraping rate limiting by Google | Low | Medium | Configurable inter-request delay; exponential backoff; 100 places/hour cap |

---

## Definition of Done (Task Level)

- [ ] All 12 implementation steps completed
- [ ] All 24 functional acceptance criteria verified
- [ ] All 5 non-functional requirements validated
- [ ] Tests written and passing for each service domain (auth, places, visits, scraping)
- [ ] End-to-end integration test passes (register -> login -> search -> visit)
- [ ] Database schema deployed with PostGIS extension and GIST indexes
- [ ] Schema contains only shared entity tables (users, places, areas, visits)
- [ ] API documentation accessible at /docs endpoint
- [ ] Docker Compose starts all services (API, worker, PostGIS, Redis) successfully
- [ ] Scraping pipeline runs on schedule (weekly + 15-min cycles)
- [ ] All error responses follow consistent JSON format
- [ ] No high-priority risks unaddressed
