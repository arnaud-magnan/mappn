# Mappn Platform Design

## Overview

Two mobile apps built on a shared backend:

- **Mappn Utility** — Discover places, see real-time and forecasted busyness. Light gamification focused on exploration bragging rights (exploration map, stats, journal, city passports).
- **Mappn Game** — Location-based RPG. Collect creatures, claim territories, compete in PvP zones, participate in events.

**Approach:** Parallel build, simultaneous launch. Shared backend means most infrastructure benefits both apps.

**Tech Stack:**
- Mobile: React Native / Expo (both apps)
- Backend: Python (FastAPI) + PostgreSQL/PostGIS
- Busyness data: Google Maps Popular Times via scraping (open-source)

---

## Architecture

```
+----------------+   +----------------+
| Mappn Utility  |   |  Mappn Game    |
| (Expo/RN)      |   |  (Expo/RN)     |
+-------+--------+   +-------+--------+
        |                     |
        +----------+----------+
                   | REST + WebSocket
        +----------v----------+
        |   FastAPI Gateway    |
        |   (Python)           |
        +----------------------+
        | Places Service       | <- busyness, search, details
        | Scraping Pipeline    | <- Google Popular Times
        | Auth Service         | <- shared accounts
        | Gamification Service | <- utility app (maps, stats, passports)
        | Game Engine          | <- creatures, territories, events, loot
        | Social Service       | <- friends, trading, leaderboards
        +----------+-----------+
                   |
        +----------v----------+
        | PostgreSQL / PostGIS |
        +---------------------+
```

Single user account across both apps. Visit data collected in either app feeds both systems.

---

## Shared Backend

### Places Database

Each place stored with Google Place ID, name, category (restaurant, bar, park...), coordinates, and address. PostGIS enables fast spatial queries ("all places within 500m").

### Scraping Pipeline

Scheduled worker scrapes Google Maps Popular Times (e.g., `populartimes` or `outscraper`):

- **Popular Times** — Weekly histogram of typical busyness per hour (refreshed weekly)
- **Live Busyness** — Real-time busyness level (refreshed every 15-30 min for active areas)

Pipeline prioritizes scraping based on user activity. Places users are viewing/near get refreshed more frequently. Cold areas scraped less often.

### Visit Tracking & Geofencing

Both apps share the same visit detection:

1. App sends GPS coordinates periodically when in foreground
2. Backend matches coordinates to nearby places (PostGIS radius query)
3. Visit confirmed when user stays within geofence (50-100m) for minimum duration (5 minutes)
4. Recorded with: user, place, timestamp, duration

Confirmed visits feed both apps:
- Utility: exploration map, stats, journal, passports
- Game: XP, component drops, loot box chances

### Shared API Endpoints

- `GET /places/nearby` — Places around coordinates with busyness data
- `GET /places/{id}` — Place details + popular times + live busyness
- `GET /places/{id}/forecast` — Predicted busyness for future hours/days
- `POST /visits/confirm` — Confirm a visit after time threshold met

---

## Utility App — Mappn

### Screens

1. **Map View (home)** — Full-screen map with place pins. Color-coded by busyness (green=quiet, yellow=moderate, red=busy). Tap pin for name, current busyness, popular times chart. Filter by category.

2. **Place Detail** — Full popular times histogram (hour by hour, day by day). Live busyness indicator. Forecast slider: "How busy at 8pm Saturday?" Visit history for this place.

3. **Exploration Map** — Personal heatmap. Neighborhoods fill in as you visit. Progress percentage per city ("23% of Lyon explored"). Shareable as image with stats overlay.

4. **Profile & Stats** — Places visited, cities explored, countries reached. Themed achievements:
   - Explorer: "Wanderer" (10 neighborhoods), "Globe Trotter" (5 cities)
   - Habits: "Night Owl" (10 places after midnight), "Early Bird" (10 before 7am)
   - Categories: "Foodie" (50 restaurants), "Culture Vulture" (20 museums)

5. **Travel Journal** — Chronological timeline. Auto-generated entries with place name, date, duration. Optional user note or photo per entry.

6. **City Passports** — Select a city, see neighborhoods/districts. Earn stamp per neighborhood visited. Complete all stamps for city badge. Progress bar per city.

### Navigation

Bottom tab bar: Map | Explore | Journal | Profile

---

## Game App — Mappn Game

### Core Game Loop

Visit real places -> earn XP + components + loot box chance -> level up creatures -> claim territories -> earn passive rewards -> visit more places.

### Creatures

Each creature has:
- **Rarity**: Common (60%), Uncommon (25%), Rare (10%), Epic (4%), Legendary (1%)
- **Level**: Starts at 1, gains XP from visits and passive territory income
- **Stats**: Power, Defense, Stamina — determine territory control strength
- **Evolution**: At level thresholds (10, 25, 50), evolve into stronger forms
- **Item slots**: 1-3 slots depending on rarity

Creatures themed around place category where they drop. Restaurant creatures look different from park creatures. Encourages visiting diverse place types.

### Items

- Dropped from loot boxes or crafted from components
- Rarity tiers matching creatures
- Types: stat boosters, passive boosters (+XP, +component yield), territory boosters
- Crafting: combine components (earned per visit) to create items. Different place categories yield different component types.

### Loot Boxes

Every confirmed visit grants:
- **Guaranteed**: XP + 1-3 components (type based on place category)
- **Chance**: loot box (30% base, higher during events). Contains creature or item. Rarity roll determines what you get.

### Territories

Map divided into areas (neighborhoods/districts, real-world boundaries). Each area has a type:

- **Personal zones** (quieter residential areas) — Only you can claim. Safe passive income.
- **Cooperative zones** (parks, cultural districts) — Multiple players co-own. Pooling stronger creatures yields better passive rewards.
- **PvP zones** (popular commercial areas, landmarks) — Contested. Others can challenge your chief. Best passive rewards.

Zone type determined by real-world busyness level of the area.

### Claiming

1. Must have discovered the area (visited at least once)
2. Assign a creature as "chief"
3. Effective power = base stats + items + home turf bonus

### Home Turf Bonus

Time spent in an area accumulates into "familiarity" score. More physical time there = stronger creatures when defending. Locals have natural advantage. Encourages repeated real-world visits.

### PvP

Attacker assigns creature to challenge current chief. Power comparison (stats + items + familiarity) determines winner. Defender keeps familiarity even if they lose — easier to reclaim than a stranger.

### Passive Rewards

Claimed territories generate hourly: creature XP + components. Scales with territory busyness level and creature power.

### Events (Platform-Curated, Tiered)

| Tier | Frequency | Duration | Rewards |
|------|-----------|----------|---------|
| Daily | 3-5 per city/day | 2-4 hours | Bonus components, 50% loot box chance |
| Weekly | 1 per city/week | 24 hours | Guaranteed rare+ loot box, exclusive items |
| Monthly | 1 global | 3-7 days | Legendary creature chance, unique cosmetics |

Events appear as glowing markers on the map. Must physically visit + meet time threshold. Monthly events can include multi-step quests.

### Social

**Friends:** Add via username or QR code. See friends' territories on map. View collections/stats. Activity feed.

**Trading:** Trade creatures and items with friends. Both confirm. 24h cooldown after trade. No real-money trading.

**Leaderboards:** Local (city), Global, Friends — by territory count, creature power, exploration %.

### Screens

1. **Game Map (home)** — Territory overlays (blue=yours, green=friends, red=PvP, purple=cooperative, grey=unclaimed). Creature icons on territories. Event markers with countdowns. Loot indicators.

2. **Creature Collection** — Grid view, filter by rarity/level/element. Tap for details.

3. **Creature Detail** — Stats, equipped items, evolution progress, territory assignment, history.

4. **Inventory** — Components by type, items by rarity, loot boxes. Crafting screen.

5. **Territory View** — Current chief/owner, familiarity rankings, passive reward rates, challenge/contribute buttons.

6. **Events** — Active and upcoming. Details: location, time window, rewards, quest progress.

7. **Social** — Friends, trading, activity feed, leaderboards.

8. **Profile** — Player level, XP, creatures collected, territories held, achievements.

### Navigation

Bottom tab bar: Map | Creatures | Inventory | Events | Profile. Social accessible from Profile.

---

## Data Model

```
Users
  id, username, email, password_hash
  xp, level
  created_at

Places
  id, google_place_id, name, category
  coordinates (PostGIS POINT)
  address, city, country
  busyness_data (jsonb: popular_times + live)

Areas
  id, name, city
  boundary (PostGIS POLYGON)
  zone_type (personal | cooperative | pvp)
  busyness_score

Visits
  id, user_id, place_id, area_id
  started_at, ended_at, duration
  rewards_granted (jsonb)

Creatures
  id, user_id, template_id
  rarity, level, xp
  power, defense, stamina
  evolution_stage
  assigned_territory_id (nullable)

Creature_Templates
  id, name, rarity, category_affinity
  base_stats, evolution_chain
  visual_asset_id

Items
  id, user_id, template_id
  rarity, stat_boosts (jsonb)
  equipped_creature_id (nullable)

Components
  user_id, type, quantity

Territories
  id, area_id, owner_id
  chief_creature_id
  familiarity_scores (jsonb: {user_id: score})
  passive_reward_rate

Events
  id, tier (daily | weekly | monthly)
  location (PostGIS), radius
  starts_at, ends_at
  rewards (jsonb)
  quest_steps (jsonb, nullable)

Friends
  user_id, friend_id, status, created_at

Trades
  id, sender_id, receiver_id
  offered_items (jsonb), requested_items (jsonb)
  status, created_at

Leaderboard_Entries
  user_id, scope (local | global | friends)
  metric, value, rank
```

---

## Approach

**Parallel Build, Simultaneous Launch**

Build both apps and the shared backend concurrently. Single launch for maximum impact. Shared infrastructure (places, scraping, visits, auth) is built once and consumed by both apps.
