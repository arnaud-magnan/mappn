---
title: Codebase Impact Analysis - Implement shared backend with FastAPI and PostGIS
task_file: .specs/tasks/draft/implement-shared-backend.feature.md
scratchpad: .specs/scratchpad/ed9ad473.md
created: 2026-02-24
status: complete
---

# Codebase Impact Analysis: Implement shared backend with FastAPI and PostGIS

## Summary

- **Files to Modify**: 0 files (greenfield project - no existing source code)
- **Files to Create**: 47 backend files + 6 test files = 53 total
- **Files to Delete**: 0 files
- **Risk Level**: Medium (greenfield, but complex PostGIS + async + scraping integration)

---

## Files to be Modified/Created

### Primary Changes

```
backend/
├── docker-compose.yml                    # NEW: PostgreSQL/PostGIS + Redis + backend services
├── Dockerfile                            # NEW: Python 3.11 backend container
├── .env.example                          # NEW: Environment variable template
├── requirements.txt                      # NEW: All Python dependencies
├── alembic.ini                           # NEW: Alembic migration configuration
├── alembic/
│   ├── env.py                            # NEW: Alembic env (imports all ORM models)
│   └── versions/
│       └── 001_initial_schema.py         # NEW: Full schema + PostGIS extension enable
└── app/
    ├── main.py                           # NEW: FastAPI app init, router registration, WebSocket
    ├── config.py                         # NEW: Pydantic BaseSettings (DB URL, JWT secret, Redis)
    ├── db/
    │   ├── __init__.py                   # NEW
    │   ├── session.py                    # NEW: Async SQLAlchemy engine + AsyncSession factory (pool_size=20, max_overflow=80)
    │   └── base.py                       # NEW: DeclarativeBase imported by all models
    ├── models/
    │   ├── __init__.py                   # NEW: Re-exports all models (for Alembic autodiscovery)
    │   ├── user.py                       # NEW: User ORM model
    │   ├── place.py                      # NEW: Place ORM model (Geography POINT)
    │   ├── area.py                       # NEW: Area ORM model (Geography POLYGON)
    │   ├── visit.py                      # NEW: Visit ORM model (FK: user, place, area)
    │   ├── creature.py                   # NEW: Creature + CreatureTemplate ORM models
    │   ├── item.py                       # NEW: Item + ItemTemplate + Component ORM models
    │   ├── territory.py                  # NEW: Territory ORM model
    │   ├── event.py                      # NEW: Event ORM model (Geography POINT)
    │   └── social.py                     # NEW: Friends + Trades + LeaderboardEntry ORM models
    ├── schemas/
    │   ├── __init__.py                   # NEW
    │   ├── auth.py                       # NEW: RegisterRequest, LoginRequest, TokenResponse
    │   ├── place.py                      # NEW: PlaceResponse, NearbyRequest (query params via Depends), ForecastResponse
    │   ├── visit.py                      # NEW: GPSPingRequest, GPSPingResponse, VisitConfirmRequest, VisitResponse
    │   └── user.py                       # NEW: UserResponse
    ├── api/
    │   ├── __init__.py                   # NEW
    │   ├── deps.py                       # NEW: get_db(), get_current_user() dependencies
    │   ├── auth.py                       # NEW: POST /auth/register, /auth/login, /auth/refresh
    │   ├── places.py                     # NEW: GET /places/nearby, /places/{id}, /places/{id}/forecast
    │   └── visits.py                     # NEW: POST /visits/ping, POST /visits/confirm, GET /visits/history
    ├── services/
    │   ├── __init__.py                   # NEW
    │   ├── auth_service.py               # NEW: register_user(), authenticate_user(), create_token(), refresh_token()
    │   ├── places_service.py             # NEW: get_nearby_places(), get_place_detail(), PostGIS queries
    │   ├── visit_service.py              # NEW: track_gps_ping(), confirm_visit(), dispatch_rewards()
    │   └── forecast_service.py           # NEW: predict_busyness() from popular_times histogram
    ├── workers/
    │   ├── __init__.py                   # NEW
    │   ├── celery_app.py                 # NEW: Celery app + Redis broker config
    │   ├── tasks/
    │   │   ├── __init__.py               # NEW
    │   │   ├── scrape_popular_times.py   # NEW: Weekly Celery task - full popular_times scrape
    │   │   └── scrape_live_busyness.py   # NEW: Periodic Celery task - live busyness refresh
    │   └── scheduler.py                  # NEW: Celery Beat schedule (weekly + 15-min intervals)
    └── core/
        ├── __init__.py                   # NEW
        ├── security.py                   # NEW: hash_password(), verify_password(), create_access_token(), decode_token()
        ├── redis.py                      # NEW: Redis client setup, pending visit TTL helpers
        └── exceptions.py                 # NEW: HTTPException handlers, custom error types
```

### Test Files

```
backend/
└── tests/
    ├── __init__.py                       # NEW
    ├── conftest.py                       # NEW: pytest fixtures (test DB, test client, test user)
    ├── test_auth.py                      # NEW: register, login, token refresh, invalid token
    ├── test_places.py                    # NEW: nearby query, place detail, forecast
    ├── test_visits.py                    # NEW: GPS ping, visit confirmation, geofencing edge cases
    └── test_scraping.py                  # NEW: mock populartimes responses, DB update verification
```

---

## Useful Resources for Implementation

### Pattern References

There are no existing source files in the codebase. This is a greenfield project. Reference the following external patterns:

- FastAPI official docs: async SQLAlchemy pattern - https://fastapi.tiangolo.com/tutorial/sql-databases/
- GeoAlchemy2 docs: PostGIS Geography type usage
- Alembic docs: async engine configuration for asyncpg
- Celery docs: periodic tasks with Redis broker

---

## Key Interfaces and Contracts

### Functions/Methods to Create

| Location | Name | Signature | Purpose |
|----------|------|-----------|---------|
| `app/core/security.py` | `hash_password` | `fn(password: str) -> str` | bcrypt hash |
| `app/core/security.py` | `verify_password` | `fn(plain: str, hashed: str) -> bool` | bcrypt verify |
| `app/core/security.py` | `create_access_token` | `fn(user_id: int, expires_delta: timedelta) -> str` | JWT creation |
| `app/core/security.py` | `decode_token` | `fn(token: str) -> dict` | JWT decode + validate |
| `app/services/auth_service.py` | `register_user` | `async fn(db: AsyncSession, data: RegisterRequest) -> User` | Create user |
| `app/services/auth_service.py` | `authenticate_user` | `async fn(db: AsyncSession, email: str, password: str) -> User \| None` | Login |
| `app/services/auth_service.py` | `create_token` | `async fn(user: User) -> TokenResponse` | Issue JWT after login |
| `app/services/auth_service.py` | `refresh_token` | `async fn(db: AsyncSession, token: str) -> TokenResponse` | Validate existing token and issue new one |
| `app/services/places_service.py` | `get_nearby_places` | `async fn(db: AsyncSession, lat: float, lon: float, radius_m: int) -> list[Place]` | PostGIS DWithin query |
| `app/services/places_service.py` | `get_place_detail` | `async fn(db: AsyncSession, place_id: int) -> Place` | Single place with busyness |
| `app/services/visit_service.py` | `track_gps_ping` | `async fn(redis, db: AsyncSession, user_id: int, lat: float, lon: float) -> GPSPingResponse` | Call places_service.get_nearby_places(), store pending visit in Redis |
| `app/services/visit_service.py` | `confirm_visit` | `async fn(redis, db: AsyncSession, user_id: int, place_id: int) -> Visit` | Validate Redis TTL + write Visit row |
| `app/services/visit_service.py` | `dispatch_rewards` | `async fn(db: AsyncSession, visit: Visit) -> dict` | Compute and persist rewards_granted on Visit |
| `app/services/forecast_service.py` | `predict_busyness` | `fn(busyness_data: dict, target_day: int, target_hour: int) -> int` | Histogram lookup from Place.busyness_data JSONB |
| `app/workers/tasks/scrape_popular_times.py` | `scrape_all_popular_times` | `Celery task fn()` | Weekly full scrape |
| `app/workers/tasks/scrape_live_busyness.py` | `scrape_active_places` | `Celery task fn()` | 15-min live scrape |
| `app/api/deps.py` | `get_current_user` | `async fn(token: str = Depends(oauth2_scheme), db = Depends(get_db)) -> User` | Calls security.decode_token(); injects authenticated user |

### ORM Models to Create

| Location | Name | Key Fields | PostGIS |
|----------|------|------------|---------|
| `app/models/user.py` | `User` | id, username, email, password_hash, xp, level, created_at | No |
| `app/models/place.py` | `Place` | id, google_place_id, name, category, coordinates, address, city, country, busyness_data | Geography POINT |
| `app/models/area.py` | `Area` | id, name, city, boundary, zone_type, busyness_score | Geography POLYGON |
| `app/models/visit.py` | `Visit` | id, user_id, place_id, area_id, started_at, ended_at, duration, rewards_granted | No |
| `app/models/creature.py` | `Creature` | id, user_id, template_id, rarity, level, xp, power, defense, stamina, evolution_stage, assigned_territory_id | No |
| `app/models/creature.py` | `CreatureTemplate` | id, name, rarity, category_affinity, base_stats, evolution_chain, visual_asset_id | No |
| `app/models/item.py` | `Item` | id, user_id, template_id, rarity, stat_boosts, equipped_creature_id | No |
| `app/models/item.py` | `Component` | user_id, type, quantity | No |
| `app/models/territory.py` | `Territory` | id, area_id, owner_id, chief_creature_id, familiarity_scores, passive_reward_rate | No |
| `app/models/event.py` | `Event` | id, tier, location, radius, starts_at, ends_at, rewards, quest_steps | Geography POINT |
| `app/models/social.py` | `Friend` | user_id, friend_id, status, created_at | No |
| `app/models/social.py` | `Trade` | id, sender_id, receiver_id, offered_items, requested_items, status, created_at | No |
| `app/models/social.py` | `LeaderboardEntry` | user_id, scope, metric, value, rank | No |

### Pydantic Schemas to Create

| Location | Name | Fields | Usage |
|----------|------|--------|-------|
| `app/schemas/auth.py` | `RegisterRequest` | username, email, password | POST body |
| `app/schemas/auth.py` | `LoginRequest` | email, password | POST body |
| `app/schemas/auth.py` | `TokenResponse` | access_token, token_type, expires_in | Response |
| `app/schemas/place.py` | `NearbyRequest` | lat, lon, radius_m (default 500), category (optional) | **Query params via `Depends(NearbyRequest)`** on GET /places/nearby - NOT request body |
| `app/schemas/place.py` | `PlaceResponse` | id, name, category, lat, lon, address, busyness_data | Response |
| `app/schemas/place.py` | `ForecastResponse` | place_id, day, hour, predicted_busyness | Response |
| `app/schemas/visit.py` | `GPSPingRequest` | lat, lon, timestamp | POST body for /visits/ping |
| `app/schemas/visit.py` | `GPSPingResponse` | matched_place_id (nullable), within_geofence, pending_visit_id (nullable) | Response for /visits/ping |
| `app/schemas/visit.py` | `VisitConfirmRequest` | place_id | POST body for /visits/confirm |
| `app/schemas/visit.py` | `VisitResponse` | id, place_id, started_at, ended_at, duration, rewards_granted | Response |
| `app/schemas/user.py` | `UserResponse` | id, username, email, xp, level, created_at | Response |

---

## Integration Points

| Component | Relationship | Impact | Action Needed |
|-----------|--------------|--------|---------------|
| `app/main.py` | Imports all API routers | High | Register auth, places, visits routers + WebSocket |
| `app/api/deps.py` | Imported by all protected API routes | High | Provides get_db() and get_current_user() |
| `app/api/deps.py` -> `app/core/security.py` | `get_current_user()` calls `decode_token()` | High | decode_token() must raise 401 on invalid/expired token for correct error propagation |
| `app/db/base.py` | Imported by all models | High | Must be imported in alembic/env.py for migration discovery |
| `app/models/__init__.py` | Imported by alembic/env.py | High | Must re-export all models so Alembic sees them |
| `app/core/redis.py` | Used by visit_service.py and scrape_live_busyness.py | High | Redis client shared across visit tracking + scraping |
| `app/workers/celery_app.py` | Used by all Celery tasks | High | Must define broker URL from config |
| `app/services/visit_service.py` -> `app/services/places_service.py` | `track_gps_ping()` calls `get_nearby_places()` to match coordinates | High | visit_service imports and calls places_service; radius configured at 75m for geofencing vs 500m for search |
| `app/services/forecast_service.py` -> `Place.busyness_data` | `predict_busyness()` reads the JSONB `busyness_data` field | Medium | forecast_service expects a specific JSON structure for busyness_data; scraper and forecast reader must agree on the schema |
| `alembic/versions/001_initial_schema.py` | Creates all tables | Critical | Must run CREATE EXTENSION postgis before table creation |
| `docker-compose.yml` | Defines postgis image | Critical | Use postgis/postgis:15-3.3 image, not plain postgres |

---

## Similar Implementations

There are no existing source files in this repository. The repository is a fresh project with only a README.md. All files are new.

---

## Test Coverage

### New Tests Needed

| Test Type | Location | Coverage Target |
|-----------|----------|-----------------|
| Unit | `tests/test_auth.py` | register_user(), authenticate_user(), create_token(), refresh_token(), JWT encode/decode |
| Unit | `tests/test_places.py` | get_nearby_places() with PostGIS, get_place_detail(), forecast |
| Integration | `tests/test_visits.py` | GPS ping (POST /visits/ping) -> Redis state -> confirm_visit() -> Visit row created |
| Unit | `tests/test_scraping.py` | Mock populartimes, verify busyness_data JSONB update |
| Fixture | `tests/conftest.py` | Async test DB session, test FastAPI client, seeded test user |

---

## Risk Assessment

### High Risk Areas

| Area | Risk | Mitigation |
|------|------|------------|
| PostGIS + GeoAlchemy2 + asyncpg | async SQLAlchemy does not support GeoAlchemy2 spatial functions natively in all versions; version pinning required | Pin geoalchemy2>=0.14, sqlalchemy>=2.0, asyncpg>=0.28; test ST_DWithin with raw SQL if ORM fails |
| Alembic + async engine | Alembic requires sync connection for migrations; alembic/env.py must use run_sync() wrapper | Follow official async Alembic pattern with connectable.run_sync(do_run_migrations) |
| populartimes library | Google Maps scraping is fragile; rate limits and API changes can break pipeline | Wrap in try/except with exponential backoff; add database fallback to stale data |
| Visit state in Redis | Redis TTL expiry means client must call /visits/confirm within 5 minutes | Document clearly; return 410 Gone if TTL expired; add client-side timer |
| PostGIS Docker image | Must use postgis/postgis image, not plain postgres | Specify postgis/postgis:15-3.3 in docker-compose.yml |
| Connection pool under 1,000 concurrent users | SQLAlchemy async engine defaults to pool_size=5; with 1,000 concurrent authenticated users all making DB-backed requests, pool starvation causes 500 errors | Set pool_size=20, max_overflow=80 in app/db/session.py; set max_connections=200 for PostgreSQL in docker-compose.yml; monitor with pg_stat_activity |

---

## Recommended Exploration

Before implementation, developer should read:

1. `/Users/arnaudmagnan/development/mappn/.specs/plans/mappn-platform.design.md` - Full platform architecture, data model, and all service definitions
2. FastAPI async SQLAlchemy docs - https://fastapi.tiangolo.com/tutorial/sql-databases/ - Async session patterns
3. GeoAlchemy2 docs - Geography type with SRID 4326, ST_DWithin usage in SQLAlchemy queries

---

## Verification Summary

| Check | Status | Notes |
|-------|--------|-------|
| All affected files identified | Done | 47 backend files + 6 test files = 53 total |
| Integration points mapped | Done | 11 integration points documented, including service-to-service |
| Similar patterns found | N/A | Greenfield project; no existing source code |
| Test coverage analyzed | Done | 4 test modules + conftest identified |
| Risks assessed | Done | 6 risk areas with mitigations (added connection pool NFR risk) |

Limitations/Caveats:
- This is a greenfield project with no existing source code. All analysis is based on the design document at `.specs/plans/mappn-platform.design.md`.
- The scraping pipeline's specific library choice (populartimes vs outscraper) is not decided; analysis assumes populartimes.
- Game Engine and Social API routes are excluded from scope; their ORM models are included because the shared database schema requires them.
- WebSocket implementation details are minimal; only the endpoint registration in main.py is scoped here.
- `NearbyRequest` fields are FastAPI query parameters accessed via `Depends(NearbyRequest)` on the GET endpoint, not a JSON request body.
