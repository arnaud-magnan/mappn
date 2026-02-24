---
name: FastAPI + PostGIS Backend
description: Patterns, libraries, and tooling for building async FastAPI backends with PostgreSQL/PostGIS for geospatial applications, visit tracking, scraping pipelines, and real-time features.
topics: fastapi, postgis, geoalchemy2, sqlalchemy-async, geofencing, visit-tracking, scraping, arq, jwt, websocket, python
created: 2026-02-24
updated: 2026-02-24
scratchpad: .specs/scratchpad/dbd1e11c.md
---

# FastAPI + PostGIS Backend

## Overview

FastAPI with SQLAlchemy 2.0 async + GeoAlchemy2 is the production-ready stack for geospatial Python backends. PostGIS handles spatial queries (nearby places, geofencing, territory containment) with meter-accurate distance calculations via the `geography` type. ARQ provides async-native task queuing for scraping pipelines.

---

## Key Concepts

- **APIRouter**: FastAPI's modular routing — one router per service domain (auth, places, visits, game)
- **AsyncSession**: SQLAlchemy 2.0 async session for non-blocking DB operations
- **GeoAlchemy2**: SQLAlchemy extension mapping PostGIS geometry/geography types
- **ST_DWithin**: PostGIS function for radius-based "nearby" queries (meter-accurate with `geography`)
- **ST_Contains**: PostGIS function for point-in-polygon geofencing
- **GIST index**: Spatial index required on geometry columns for query performance
- **geography vs geometry**: `geography` uses earth curvature — required for accurate meter distances
- **ARQ**: Async Redis job queue, async-native counterpart to Celery, built by Pydantic author
- **Lifespan**: FastAPI's startup/shutdown context manager (replaces deprecated `on_event`)

---

## Documentation & References

| Resource | Description | Link |
|----------|-------------|------|
| FastAPI official docs | Routing, DI, WebSocket, security | https://fastapi.tiangolo.com |
| FastAPI bigger applications | Multi-router project structure | https://fastapi.tiangolo.com/tutorial/bigger-applications |
| FastAPI OAuth2 JWT | JWT auth with OAuth2PasswordBearer | https://fastapi.tiangolo.com/tutorial/security/oauth2-jwt |
| GeoAlchemy2 docs | PostGIS types and spatial functions | https://geoalchemy-2.readthedocs.io |
| GeoAlchemy2 spatial functions | ST_DWithin, ST_Contains, ST_Distance | https://geoalchemy-2.readthedocs.io/en/latest/spatial_functions.html |
| SQLAlchemy 2.0 async | AsyncSession, async_sessionmaker | https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html |
| ARQ docs | Async Redis task queue | https://arq-docs.helpmanual.io |
| PostGIS docs | Spatial extensions for PostgreSQL | https://postgis.net/documentation |
| FastAPI + GeoAlchemy tutorial | Working with spatial data in FastAPI | https://medium.com/@notarious2/working-with-spatial-data-using-fastapi-and-geoalchemy-797d414d2fe7 |
| fastapi-postgis reference repo | Integration example | https://github.com/grillazz/fastapi-postgis |

---

## Recommended Libraries & Tools

| Name | Purpose | Maturity | Notes |
|------|---------|----------|-------|
| fastapi 0.115.x | Web framework | Stable | Pydantic v2, lifespan events |
| uvicorn[standard] 0.34.x | ASGI server | Stable | Use gunicorn+uvicorn workers in production |
| SQLAlchemy 2.0.x | Async ORM | Stable | AsyncSession, async_sessionmaker |
| asyncpg 0.30.x | Async PostgreSQL driver | Stable | Fastest async PG driver |
| GeoAlchemy2 0.15.x | PostGIS + SQLAlchemy bridge | Stable | Geometry/geography types, spatial functions |
| alembic 1.14.x | DB migrations | Stable | Works with GeoAlchemy2 types |
| pydantic 2.x | Data validation | Stable | Required by FastAPI 0.100+ |
| pydantic-settings 2.x | Env var config | Stable | BaseSettings with .env support |
| PyJWT 2.x | JWT encode/decode | Stable | 3M+ weekly downloads, actively maintained |
| passlib[bcrypt] 1.7.x | Password hashing | Stable | Use bcrypt backend |
| python-multipart 0.0.20+ | Form data (OAuth2 forms) | Stable | Required for OAuth2PasswordRequestForm |
| arq 0.26.x | Async task queue | Stable | Redis-backed, async-native, retry support |
| redis 5.x | Redis Python client | Stable | Async support built-in |
| httpx 0.28.x | Async HTTP client | Stable | Use for external API calls (scraping) |
| fastapi-cache2[redis] | Route-level response caching | Stable | Decorator-based Redis caching |
| populartimes | Google Maps Popular Times scraper | Maintained (OSS) | Free, uses undocumented API — dev/MVP only |
| outscraper | Paid Google Maps scraping API | Stable | Production-grade, ToS-compliant |
| pytest-asyncio | Async test runner | Stable | Required for async endpoint tests |
| httpx AsyncClient | Async test client for FastAPI | Stable | Replaces TestClient for async tests |
| testcontainers | Real PostGIS in tests | Stable | Spins up Docker containers in pytest |

### Recommended Stack

Use SQLAlchemy 2.0 async + asyncpg + GeoAlchemy2 for the ORM layer. ARQ + Redis for the scraping/job queue. PyJWT + passlib for auth. postgis/postgis:16-3.5 Docker image for the database. FastAPI's built-in WebSocket + Redis Pub/Sub for real-time features at scale.

---

## Patterns & Best Practices

### Modular APIRouter Structure

**When to use**: Always — every service domain gets its own router.

**Example**:
```python
# app/routers/places.py
from fastapi import APIRouter, Depends
router = APIRouter(prefix="/places", tags=["places"])

# app/main.py
from app.routers import places, auth, visits, game
app = FastAPI(lifespan=lifespan)
app.include_router(auth.router)
app.include_router(places.router)
app.include_router(visits.router)
app.include_router(game.router)
```

### Lifespan for Startup/Shutdown

**When to use**: For DB pool initialization, Redis connection, ARQ worker startup.

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI

@asynccontextmanager
async def lifespan(app: FastAPI):
    # startup
    await init_db()
    await init_redis()
    yield
    # shutdown
    await close_db()

app = FastAPI(lifespan=lifespan)
```

### Async Database Session Dependency

**When to use**: Inject into every endpoint that needs DB access.

```python
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

engine = create_async_engine("postgresql+asyncpg://user:pass@db/dbname")
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)

async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session
```

### PostGIS Nearby Places Query

**When to use**: Finding places within a radius (e.g., 500m from user).

```python
from geoalchemy2.functions import ST_DWithin, ST_Distance, ST_MakePoint
from geoalchemy2.types import Geography
from sqlalchemy import cast, select

async def get_nearby_places(session: AsyncSession, lat: float, lon: float, radius_m: float = 500):
    user_point = cast(ST_MakePoint(lon, lat), Geography)
    stmt = (
        select(Place)
        .where(ST_DWithin(Place.coordinates, user_point, radius_m))
        .order_by(ST_Distance(Place.coordinates, user_point))
    )
    result = await session.execute(stmt)
    return result.scalars().all()
```

### PostGIS Geofence Containment

**When to use**: Checking if a user point is inside an area boundary (territory/district).

```python
from geoalchemy2.functions import ST_Contains, ST_MakePoint
from geoalchemy2 import WKTElement

def is_point_in_area(lat: float, lon: float, area_boundary) -> bool:
    # Use ST_Contains in SQL query
    stmt = select(Area).where(
        ST_Contains(Area.boundary, ST_MakePoint(lon, lat))
    )
```

### PostGIS Model Column Definition

```python
from geoalchemy2 import Geometry, Geography
from sqlalchemy.orm import DeclarativeBase, mapped_column

class Place(Base):
    __tablename__ = "places"
    id: Mapped[int] = mapped_column(primary_key=True)
    # Use Geography for meter-accurate distance queries
    coordinates: Mapped[Any] = mapped_column(Geography(geometry_type="POINT", srid=4326))

class Area(Base):
    __tablename__ = "areas"
    boundary: Mapped[Any] = mapped_column(Geography(geometry_type="POLYGON", srid=4326))
```

### Spatial Index (Required)

Add in Alembic migration for query performance:
```sql
CREATE INDEX ix_places_coordinates ON places USING GIST (coordinates);
CREATE INDEX ix_areas_boundary ON areas USING GIST (boundary);
```

### JWT Authentication Dependency

**When to use**: Protect endpoints requiring authenticated users.

```python
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
import jwt

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        user_id = payload.get("sub")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    return user
```

### ARQ Task for Scraping Pipeline

**When to use**: Scheduled or priority-based scraping jobs.

```python
# app/workers/scraping.py
async def scrape_place_popularity(ctx, place_id: int, google_place_id: str):
    # ctx contains redis connection pool
    data = await fetch_popular_times(google_place_id)
    async with AsyncSessionLocal() as session:
        await update_place_busyness(session, place_id, data)

class WorkerSettings:
    functions = [scrape_place_popularity]
    redis_settings = RedisSettings(host="redis", port=6379)
    max_jobs = 20
    job_timeout = 300

# Enqueue from FastAPI endpoint:
await arq_pool.enqueue_job("scrape_place_popularity", place_id, google_place_id)
```

### Visit Geofencing State Machine

**When to use**: Server-side visit confirmation logic.

```python
# UserPresence table tracks active dwell sessions
# On each GPS update:
# 1. ST_DWithin query: find places within 75m of user
# 2. Upsert UserPresence(user_id, place_id, first_seen, last_seen, reading_count)
# 3. If last_seen - first_seen >= 5 minutes AND reading_count >= 3: confirm visit
# 4. Create Visit record; delete UserPresence entry; grant rewards
```

### Pydantic Settings Config

```python
from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    database_url: str
    redis_url: str = "redis://localhost:6379"
    secret_key: str
    access_token_expire_minutes: int = 30
    class Config:
        env_file = ".env"

@lru_cache
def get_settings() -> Settings:
    return Settings()
```

---

## Similar Implementations

### fastapi-postgis (grillazz)

- **Source**: https://github.com/grillazz/fastapi-postgis
- **Approach**: FastAPI + SQLAlchemy + PostGIS with psycopg3 driver
- **Applicability**: Direct reference for model and query patterns

### notarious2/geolocations

- **Source**: https://github.com/notarious2/geolocations
- **Approach**: Async FastAPI + GeoAlchemy2 + Alembic spatial data storage
- **Applicability**: Shows GeoAlchemy2 async patterns with migrations

### TIXXETY (gitEricsson)

- **Source**: https://github.com/gitEricsson/TIXXETY
- **Approach**: FastAPI + async SQLAlchemy + PostGIS + Celery + geospatial event recommendations
- **Applicability**: Shows geospatial event matching, similar to territory/place system

---

## Common Pitfalls & Solutions

| Issue | Impact | Solution |
|-------|--------|----------|
| Using `geometry` instead of `geography` | High — distances in degrees, not meters | Always use `Geography(srid=4326)` for distance/radius queries |
| Missing GIST index on geometry columns | High — table scans on spatial queries | Add `CREATE INDEX USING GIST` in initial migration |
| ST_DWithin with wrong units | High — query returns wrong results | With geography type, distance is in meters automatically |
| Google Popular Times scraping breaks | High — no busyness data | Abstract behind interface; swap to outscraper in production |
| AsyncSession in ARQ worker | Medium — no session available | Create separate AsyncSessionLocal in worker context |
| Duplicate visit creation | Medium — rewards granted twice | Check last visit timestamp; enforce cooldown per user+place |
| GPS jitter causing false exit | Medium — visit interrupted prematurely | Require N consecutive out-of-range readings before ending session |
| Alembic with async engine | Medium — migration fails | Use synchronous URL in alembic env.py (asyncpg -> psycopg2 for migrations) |
| WebSocket on multiple API instances | Medium — missed broadcasts | Use Redis Pub/Sub or `broadcast` library for cross-instance messages |

---

## Recommendations

1. **Use `Geography(srid=4326)` for all coordinate columns**: Enables meter-accurate ST_DWithin queries without manual unit conversion.
2. **Always add GIST indexes in initial migration**: Spatial queries without GIST indexes will full-scan tables — catastrophic at scale.
3. **Abstract the scraping layer behind an interface**: Start with populartimes (free), swap to outscraper/SerpAPI for production without changing business logic.
4. **Use ARQ over Celery**: ARQ is async-native and integrates cleanly with FastAPI's async ecosystem; Celery adds complexity without benefit for this workload.
5. **Track UserPresence server-side**: Do not trust client-reported visit completions; use server-side dwell time tracking with PostGIS proximity checks.
6. **Cache busyness data in Redis with TTL**: Popular times = 1 week TTL; live busyness = 15-30 min TTL. Avoid re-scraping on every request.

---

## Implementation Guidance

### Installation

```bash
# Core framework
pip install "fastapi==0.115.13" "uvicorn[standard]==0.34.0" "python-multipart==0.0.20"

# Database
pip install "sqlalchemy==2.0.40" "asyncpg==0.30.0" "geoalchemy2==0.15.2" "alembic==1.14.0"

# Config and validation
pip install "pydantic==2.11.0" "pydantic-settings==2.7.0"

# Auth
pip install "PyJWT==2.10.1" "passlib[bcrypt]==1.7.4"

# Task queue and caching
pip install "arq==0.26.1" "redis==5.2.0" "fastapi-cache2[redis]==0.2.2"

# HTTP client (scraping, external APIs)
pip install "httpx==0.28.0"

# Scraping
pip install "populartimes==0.1.0"  # dev/MVP
# pip install "outscraper==3.0.0"  # production

# Testing
pip install "pytest-asyncio==0.25.0" "testcontainers==4.9.0"
```

### Docker Compose Setup

```yaml
services:
  db:
    image: postgis/postgis:16-3.5
    environment:
      POSTGRES_DB: mappn
      POSTGRES_USER: mappn
      POSTGRES_PASSWORD: secret
    volumes:
      - pgdata:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine

  api:
    build: .
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
    depends_on: [db, redis]
    env_file: .env

  worker:
    build: .
    command: python -m arq app.workers.scraping.WorkerSettings
    depends_on: [db, redis]
    env_file: .env

volumes:
  pgdata:
```

### Initial Alembic Migration (PostGIS)

```python
# migrations/versions/001_initial.py
def upgrade():
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis")
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
    # ... create tables
    op.execute("CREATE INDEX ix_places_coordinates ON places USING GIST (coordinates)")
    op.execute("CREATE INDEX ix_areas_boundary ON areas USING GIST (boundary)")
```

### Project Directory Structure

```
app/
  main.py              # FastAPI app, lifespan, router includes
  config.py            # pydantic-settings Settings
  database.py          # engine, AsyncSessionLocal, get_db dependency
  models/              # SQLAlchemy ORM models (User, Place, Area, Visit, ...)
  schemas/             # Pydantic request/response schemas
  routers/
    auth.py            # POST /auth/token, POST /auth/register
    places.py          # GET /places/nearby, GET /places/{id}
    visits.py          # POST /visits/location, POST /visits/confirm
    game.py            # territories, creatures, events
    social.py          # friends, leaderboards, trading
  services/
    geofencing.py      # visit dwell time logic
    busyness.py        # scraping abstraction layer
  workers/
    scraping.py        # ARQ worker functions + WorkerSettings
```

---

## Sources & Verification

| Source | Type | Last Verified |
|--------|------|---------------|
| https://fastapi.tiangolo.com | Official | 2026-02-24 |
| https://geoalchemy-2.readthedocs.io | Official | 2026-02-24 |
| https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html | Official | 2026-02-24 |
| https://arq-docs.helpmanual.io | Official | 2026-02-24 |
| https://github.com/grillazz/fastapi-postgis | Community reference | 2026-02-24 |
| https://github.com/notarious2/geolocations | Community reference | 2026-02-24 |
| https://pypi.org/project/GeoAlchemy2 | PyPI registry | 2026-02-24 |
| https://hub.docker.com/r/postgis/postgis | Docker Hub | 2026-02-24 |

---

## Changelog

| Date | Changes |
|------|---------|
| 2026-02-24 | Initial creation for task: implement-shared-backend.feature.md |
