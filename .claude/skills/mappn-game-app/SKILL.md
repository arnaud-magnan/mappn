---
name: Mappn Game App
description: Game-specific patterns, libraries, and architecture for the Mappn Game mobile app — territory polygon overlays, creature collection grids, loot box animations, WebSocket real-time events, game backend models, and social features built on the shared Expo SDK 54 + FastAPI foundation.
topics: location-based-game, territory-claiming, creature-collection, pvp, loot-box, flashlist, websocket, expo-notifications, arq-passive-rewards, game-backend, react-native-maps-polygon, social-trading, leaderboards
created: 2026-02-26
updated: 2026-02-26
scratchpad: .specs/scratchpad/8aadd48d.md
---

# Mappn Game App

## Overview

The Mappn Game app is a new Expo application (at `/game/`) built alongside the utility app, sharing the same FastAPI backend. It uses an identical foundation (Expo SDK ~54, expo-router ~6, TanStack Query v5, Zustand v5, react-native-maps 1.20.1) with game-specific additions: @shopify/flash-list v2 for creature grids, Polygon territory overlays on the map, native WebSocket for real-time events, expo-notifications for game alerts, and new FastAPI game/social/events routers with Creature, Item, Territory, Event, Friends, Trade, and Leaderboard models.

**PREREQUISITE**: Read `react-native-expo-mobile-app` and `fastapi-postgis-backend` skills first. This skill extends both.

---

## Key Concepts

- **Territory Polygons**: react-native-maps `Polygon` component renders colored zone overlays. Zone type (personal/cooperative/pvp) maps to fill color constant.
- **Creature Grid**: `@shopify/flash-list` v2 with `numColumns={3}` for virtualized 60fps creature collection display.
- **Loot Box Reveal**: Reanimated v4 spring modal animation + `react-native-confetti-cannon` burst. No Skia required for MVP.
- **Real-time WebSocket**: Native RN WebSocket API via custom `useGameSocket` hook. Backend: FastAPI WebSocket + Redis Pub/Sub.
- **Passive Rewards**: ARQ cron job runs hourly, computes XP + component rewards for all active territories.
- **Home Turf Bonus**: Visit-time accumulation in `Territory.familiarity_scores` JSONB (user_id -> score). Defenders get bonus from their score.
- **Game Stores**: `gameStore` (Zustand) holds active creature list, inventory snapshot, selected territory. Complements TanStack Query for server state.
- **Area Zone Types**: Existing `Area.zone_type` field updated from generic district/neighborhood to `personal | cooperative | pvp` based on busyness score thresholds.

---

## Documentation & References

| Resource | Description | Link |
|----------|-------------|------|
| react-native-maps Polygon | Polygon overlay props, tappable, colors | https://github.com/react-native-maps/react-native-maps/blob/master/docs/polygon.md |
| FlashList v2 Shopify | Ground-up rewrite for New Architecture, grid/masonry | https://shopify.engineering/flashlist-v2 |
| FlashList v2 Docs | Usage, numColumns, masonry prop | https://shopify.github.io/flash-list/docs/ |
| FlashList Expo Docs | Install via Expo | https://docs.expo.dev/versions/latest/sdk/flash-list/ |
| FastAPI WebSocket | WebSocket endpoints in FastAPI | https://fastapi.tiangolo.com/advanced/websockets/ |
| FastAPI + Redis WebSocket | Scaling WebSocket with Redis Pub/Sub (Jan 2026) | https://oneuptime.com/blog/post/2026-01-25-websocket-servers-fastapi-redis/view |
| expo-notifications | Local + push notifications | https://docs.expo.dev/versions/latest/sdk/notifications/ |
| ARQ Cron Jobs | Scheduled tasks with ARQ WorkerSettings | https://arq-docs.helpmanual.io |
| react-native-confetti-cannon | Pure RN confetti burst | https://www.npmjs.com/package/react-native-confetti-cannon |
| SQLAlchemy JSONB | PostgreSQL JSONB mapped_column | https://docs.sqlalchemy.org/en/20/dialects/postgresql.html |
| Mappn Platform Design | Full game design spec | .specs/plans/mappn-platform.design.md |

---

## Recommended Libraries & Tools

| Name | Purpose | Maturity | Notes |
|------|---------|----------|-------|
| @shopify/flash-list v2 | Virtualized creature grid (numColumns=3) | Stable | JS-only, no native deps, New Arch optimized |
| react-native-confetti-cannon | Confetti burst on loot box reveal | Stable | Pure RN, no Skia needed |
| expo-notifications | Game alerts: event countdown, territory challenged | Stable | FCM (Android) + APNs (iOS) for push |
| react-native-maps (existing) | Territory Polygon overlays | Stable | Already installed v1.20.1 |
| react-native-reanimated (existing) | Loot box modal ZoomIn animation | Stable | Already installed v4.1.1 |
| expo-blur | Blurred background for reveal modals | Stable | In Expo SDK, no extra install |
| Native WebSocket API | Real-time game events | Built-in | Zero deps, built into React Native |

### Recommended Stack for Mappn Game App

Same as utility app (Expo SDK 54 + expo-router v6 + TanStack Query v5 + Zustand v5 + react-native-maps) plus: @shopify/flash-list v2 for creature grid, react-native-confetti-cannon for loot reveals, expo-notifications for game alerts, native WebSocket for real-time PvP/territory events. Skip Skia for MVP.

---

## Patterns & Best Practices

### Game App Tabs Layout (5 tabs)

**When to use**: Root tab navigation for game app.

```typescript
// game/app/(tabs)/_layout.tsx
import { Tabs } from 'expo-router';
import MaterialIcons from '@expo/vector-icons/MaterialIcons';
import { GAME_COLORS } from '@/constants/colors';

export default function TabLayout() {
  return (
    <Tabs screenOptions={{ tabBarActiveTintColor: GAME_COLORS.primary }}>
      <Tabs.Screen name="index" options={{ title: 'Map', headerShown: false,
        tabBarIcon: ({ color }) => <MaterialIcons name="map" size={28} color={color} /> }} />
      <Tabs.Screen name="creatures" options={{ title: 'Creatures',
        tabBarIcon: ({ color }) => <MaterialIcons name="catching-pokemon" size={28} color={color} /> }} />
      <Tabs.Screen name="inventory" options={{ title: 'Inventory',
        tabBarIcon: ({ color }) => <MaterialIcons name="inventory" size={28} color={color} /> }} />
      <Tabs.Screen name="events" options={{ title: 'Events',
        tabBarIcon: ({ color }) => <MaterialIcons name="event" size={28} color={color} /> }} />
      <Tabs.Screen name="profile" options={{ title: 'Profile',
        tabBarIcon: ({ color }) => <MaterialIcons name="person" size={28} color={color} /> }} />
    </Tabs>
  );
}
```

### Territory Polygon Overlay on Map

**When to use**: Game map home screen showing all territory zones with colored fills.

```typescript
import MapView, { Polygon } from 'react-native-maps';
import { useMemo } from 'react';

// Zone type -> color mapping
const ZONE_COLORS = {
  own: { fill: 'rgba(59,130,246,0.35)', stroke: '#3b82f6' },       // blue = yours
  friends: { fill: 'rgba(34,197,94,0.35)', stroke: '#22c55e' },    // green = friends
  pvp: { fill: 'rgba(239,68,68,0.35)', stroke: '#ef4444' },        // red = PvP
  cooperative: { fill: 'rgba(168,85,247,0.35)', stroke: '#a855f7' }, // purple = coop
  unclaimed: { fill: 'rgba(107,114,128,0.2)', stroke: '#6b7280' }, // grey = unclaimed
};

function TerritoryLayer({ territories, currentUserId }) {
  const polygons = useMemo(() => territories.map(t => ({
    ...t,
    colorKey: t.owner_id === currentUserId ? 'own'
      : t.is_friend ? 'friends'
      : t.zone_type === 'pvp' ? 'pvp'
      : t.zone_type === 'cooperative' ? 'cooperative'
      : 'unclaimed',
  })), [territories, currentUserId]);

  return polygons.map(t => (
    <Polygon
      key={t.id}
      coordinates={t.boundary_coordinates}
      fillColor={ZONE_COLORS[t.colorKey].fill}
      strokeColor={ZONE_COLORS[t.colorKey].stroke}
      strokeWidth={1.5}
      tappable
      onPress={() => onTerritoryPress(t.id)}
    />
  ));
}
```

### Creature Grid with FlashList v2

**When to use**: Creature collection screen with numColumns grid.

```typescript
import { FlashList } from '@shopify/flash-list';

function CreatureGrid({ creatures }) {
  return (
    <FlashList
      data={creatures}
      numColumns={3}
      keyExtractor={(item) => item.id.toString()}
      renderItem={({ item }) => <CreatureCard creature={item} />}
      estimatedItemSize={120}  // still accepted, just not required in v2
    />
  );
}
```

### Loot Box Reveal Modal

**When to use**: After confirmed visit grants a loot box.

```typescript
import Animated, { useSharedValue, useAnimatedStyle, withSpring } from 'react-native-reanimated';
import ConfettiCannon from 'react-native-confetti-cannon';

function LootRevealModal({ reward, onClose }) {
  const scale = useSharedValue(0);
  const animStyle = useAnimatedStyle(() => ({ transform: [{ scale: scale.value }] }));

  useEffect(() => {
    scale.value = withSpring(1, { damping: 12, stiffness: 150 });
  }, []);

  return (
    <View style={StyleSheet.absoluteFill}>
      <ConfettiCannon count={80} origin={{ x: width / 2, y: 0 }} fadeOut />
      <Animated.View style={[styles.card, animStyle]}>
        <Text>{reward.rarity} {reward.name}</Text>
        <Button title="Collect" onPress={onClose} />
      </Animated.View>
    </View>
  );
}
```

### useGameSocket Hook

**When to use**: Real-time game events (PvP results, territory changes, event starts).

```typescript
// hooks/useGameSocket.ts
import { useEffect, useRef, useCallback } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import * as SecureStore from 'expo-secure-store';

type GameEvent = { type: string; payload: unknown };

export function useGameSocket() {
  const ws = useRef<WebSocket | null>(null);
  const queryClient = useQueryClient();

  const connect = useCallback(async () => {
    const token = await SecureStore.getItemAsync('access_token');
    ws.current = new WebSocket(`${WS_BASE_URL}/game/ws?token=${token}`);

    ws.current.onmessage = (event) => {
      const msg: GameEvent = JSON.parse(event.data);
      if (msg.type === 'territory_claimed') {
        queryClient.invalidateQueries({ queryKey: ['territories'] });
      } else if (msg.type === 'pvp_result') {
        queryClient.invalidateQueries({ queryKey: ['territories'] });
      } else if (msg.type === 'event_started') {
        queryClient.invalidateQueries({ queryKey: ['events', 'active'] });
      } else if (msg.type === 'reward_tick') {
        queryClient.invalidateQueries({ queryKey: ['inventory'] });
      }
    };

    ws.current.onclose = () => {
      // Reconnect after 3 seconds
      setTimeout(connect, 3000);
    };
  }, [queryClient]);

  useEffect(() => {
    connect();
    return () => ws.current?.close();
  }, [connect]);
}
```

### expo-notifications Game Setup

**When to use**: Register for push notifications on game app startup.

```typescript
// services/notificationsService.ts
import * as Notifications from 'expo-notifications';

Notifications.setNotificationHandler({
  handleNotification: async () => ({
    shouldShowAlert: true, shouldPlaySound: true, shouldSetBadge: false,
  }),
});

export async function setupGameNotifications() {
  const { status } = await Notifications.requestPermissionsAsync();
  if (status !== 'granted') return null;
  const token = await Notifications.getExpoPushTokenAsync();
  return token.data;  // Send to backend to store per user
}

export async function scheduleEventReminder(eventName: string, startsAt: Date) {
  const triggerDate = new Date(startsAt.getTime() - 15 * 60 * 1000); // 15min before
  await Notifications.scheduleNotificationAsync({
    content: { title: 'Event Starting Soon', body: `${eventName} starts in 15 minutes!` },
    trigger: { date: triggerDate },
  });
}
```

### Passive Rewards ARQ Cron Worker

**When to use**: Hourly territory passive income computation.

```python
# app/workers/game.py
from arq import cron
from app.db.session import AsyncSessionLocal
from app.services.game_service import process_all_territory_rewards

async def passive_rewards_tick(ctx):
    """Compute hourly XP + component rewards for all active territories."""
    async with AsyncSessionLocal() as session:
        await process_all_territory_rewards(session)

class GameWorkerSettings:
    functions = [passive_rewards_tick]
    cron_jobs = [cron(passive_rewards_tick, hour=None, minute=0)]  # Every hour
    redis_settings = RedisSettings.from_dsn(settings.redis_url)
```

---

## Game Backend Models

### New SQLAlchemy Models (additive migration)

```python
# app/models/game.py
from sqlalchemy import Integer, String, Float, ForeignKey, DateTime, Enum
from sqlalchemy.dialects.postgresql import JSONB
from geoalchemy2 import Geography
from sqlalchemy.orm import Mapped, mapped_column

class Creature(Base):
    __tablename__ = "creatures"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    template_id: Mapped[int] = mapped_column(ForeignKey("creature_templates.id"))
    rarity: Mapped[str] = mapped_column(String(20))  # common|uncommon|rare|epic|legendary
    level: Mapped[int] = mapped_column(default=1)
    xp: Mapped[int] = mapped_column(default=0)
    power: Mapped[int] = mapped_column(default=10)
    defense: Mapped[int] = mapped_column(default=10)
    stamina: Mapped[int] = mapped_column(default=10)
    evolution_stage: Mapped[int] = mapped_column(default=1)
    assigned_territory_id: Mapped[int | None] = mapped_column(ForeignKey("territories.id"), nullable=True)

class Territory(Base):
    __tablename__ = "territories"
    id: Mapped[int] = mapped_column(primary_key=True)
    area_id: Mapped[int] = mapped_column(ForeignKey("areas.id"), unique=True)
    owner_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    chief_creature_id: Mapped[int | None] = mapped_column(ForeignKey("creatures.id"), nullable=True)
    familiarity_scores: Mapped[dict] = mapped_column(JSONB, default={})  # {user_id: score}
    passive_reward_rate: Mapped[float] = mapped_column(Float, default=1.0)

class GameEvent(Base):
    __tablename__ = "game_events"
    id: Mapped[int] = mapped_column(primary_key=True)
    tier: Mapped[str] = mapped_column(String(20))  # daily|weekly|monthly
    location: Mapped[any] = mapped_column(Geography(geometry_type="POINT", srid=4326))
    radius: Mapped[float] = mapped_column(Float)  # meters
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    ends_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    rewards: Mapped[dict] = mapped_column(JSONB)
    quest_steps: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
```

### Visit Model Migration (add rewards_granted)

```python
# alembic migration: add rewards_granted to visits
def upgrade():
    op.add_column('visits', sa.Column('rewards_granted', JSONB, nullable=True))
```

### New API Routers

```python
# app/api/game.py — creatures, territories, loot
# app/api/events.py — active events, quest progress, participation
# app/api/social.py — friends, trading, leaderboards

# Include in main.py:
from app.api.game import router as game_router
from app.api.events import router as events_router
from app.api.social import router as social_router

app.include_router(game_router)    # prefix="/game"
app.include_router(events_router)  # prefix="/events"
app.include_router(social_router)  # prefix="/social"
```

---

## Game App Project Structure

```
game/                               # New Expo app (separate from utility/)
  app/
    (tabs)/
      index.tsx                     # Game Map (territories, events, loot indicators)
      creatures.tsx                 # Creature Collection grid
      inventory.tsx                 # Components, Items, Crafting
      events.tsx                    # Active + upcoming events
      profile.tsx                   # Player level, XP, achievements, Social link
      _layout.tsx                   # 5-tab bottom bar
    creature/
      [id].tsx                      # Creature Detail (stats, items, evolution)
    territory/
      [id].tsx                      # Territory View (chief, familiarity, challenge)
    social/
      index.tsx                     # Friends, activity feed, leaderboards
      trading.tsx                   # Trade offers
    (auth)/
      login.tsx
      register.tsx
    _layout.tsx                     # Root layout (QueryClient, GestureHandler, auth)

  components/
    map/
      TerritoryLayer.tsx            # Polygon overlays by zone type
      EventMarker.tsx               # Glowing event marker with countdown
      CreatureMarker.tsx            # Creature icon on territory
    creature/
      CreatureCard.tsx              # Grid card (rarity border, level badge)
      CreatureDetail.tsx            # Full stats panel
      LootRevealModal.tsx           # Loot box animated reveal
    inventory/
      ComponentList.tsx             # Components by type
      CraftingScreen.tsx            # Recipe + craft button
    events/
      EventCard.tsx                 # Event tier badge, countdown, rewards
    social/
      LeaderboardTable.tsx
      TradeCard.tsx
    ui/                             # Shared UI (Button, LoadingSpinner, etc.)

  hooks/
    useGameSocket.ts                # Native WebSocket hook
    useCreatures.ts                 # TanStack Query: creature list
    useTerritories.ts               # TanStack Query: nearby territories
    useInventory.ts                 # TanStack Query: components + items
    useActiveEvents.ts              # TanStack Query: active events
    useLeaderboard.ts               # TanStack Query: leaderboard entries
    useLocationTracking.ts          # Reuse from utility (same GPS logic)

  stores/
    authStore.ts                    # Copy from utility (same auth logic)
    locationStore.ts                # Copy from utility (same GPS store)
    gameStore.ts                    # NEW: selected territory, active creature, loot queue

  services/
    api.ts                          # Copy from utility (same axios + interceptors)
    gameService.ts                  # creatures, territories, loot endpoints
    eventsService.ts                # events endpoints
    socialService.ts                # friends, trading, leaderboards

  constants/
    colors.ts                       # GAME_COLORS (darker theme) + ZONE_COLORS
    config.ts                       # API_BASE_URL, WS_BASE_URL, STALE_TIME

  app.config.ts
  eas.json
  package.json
```

---

## Game Store (Zustand)

```typescript
// stores/gameStore.ts
import { create } from 'zustand';

interface GameStore {
  selectedTerritoryId: number | null;
  lootQueue: LootReward[];           // Rewards waiting to be revealed
  setSelectedTerritory: (id: number | null) => void;
  enqueueLoot: (reward: LootReward) => void;
  dequeueLoot: () => LootReward | undefined;
}

export const useGameStore = create<GameStore>((set, get) => ({
  selectedTerritoryId: null,
  lootQueue: [],
  setSelectedTerritory: (id) => set({ selectedTerritoryId: id }),
  enqueueLoot: (reward) => set(s => ({ lootQueue: [...s.lootQueue, reward] })),
  dequeueLoot: () => {
    const [first, ...rest] = get().lootQueue;
    set({ lootQueue: rest });
    return first;
  },
}));
```

---

## Similar Implementations

### Ingress / Pokemon GO Architecture Patterns
- **Source**: Wikipedia/Ingress + Niantic engineering talks
- **Approach**: S2 cell grid for territory division, resonators for claiming, passive AP accumulation, 21-hour gym coin collection
- **Applicability**: Mappn uses real-world district boundaries (PostGIS polygons) instead of S2 cells. Passive reward tick = hourly ARQ job. Chief creature = resonator equivalent.

### Shopify FlashList v2 in Production
- **Source**: https://shopify.engineering/flashlist-v2
- **Approach**: No estimates, masonry prop, numColumns for standard grids
- **Applicability**: Direct use for creature collection (numColumns=3) and inventory

### FastAPI WebSocket + Redis Pub/Sub
- **Source**: https://oneuptime.com/blog/post/2026-01-25-websocket-servers-fastapi-redis/view
- **Approach**: Connection manager tracks WS clients per instance; Redis channel broadcasts to all instances
- **Applicability**: Direct pattern for territory_claimed, pvp_result game events

---

## Common Pitfalls & Solutions

| Issue | Impact | Solution |
|-------|--------|----------|
| Many territory Polygon components cause map jank | High | Memoize with useMemo, render only viewport-visible territories via bbox filter |
| WebSocket token expiry during long sessions | High | Re-read token from SecureStore on WS reconnect, not at connect time |
| `rewards_granted` missing from Visit model | High | Add via additive Alembic migration before game router goes live |
| FlashList v2 in bare workflow without New Arch | Medium | Game app uses managed workflow with New Arch default (SDK 54) — not an issue |
| PvP result race condition (both players claim win) | High | Server-side atomic compare — use DB transaction with SELECT FOR UPDATE on Territory |
| Loot reveal modal blocks map interaction | Medium | Use portal/Modal component that doesn't block map gestures |
| expo-notifications on Expo Go | Low | Push notifications not available in Expo Go; use development build (EAS) for testing |
| Passive rewards ARQ worker competing with itself | Medium | Use ARQ job deduplication or Redis lock per territory_id |
| Familiar_scores JSONB key type mismatch | Medium | Use string keys in JSONB ({"123": 50} not {123: 50}) |

---

## Recommendations

1. **Mirror utility app structure exactly**: Copy package.json, api.ts, authStore, locationStore from utility to game. Same conventions = faster development and easier maintenance.
2. **@shopify/flash-list v2 for creature grid**: Only library that delivers 60fps grid at 100+ creatures on New Architecture without native setup.
3. **Use Polygon overlay with zone-type color constants**: Define ZONE_COLORS object mapping zone type to fill/stroke. Memoize territory list rendering.
4. **Native WebSocket with useGameSocket hook**: No extra dependencies. Invalidate TanStack Query cache on game events for automatic UI refresh.
5. **Additive-only Alembic migration**: Only add new tables and the `rewards_granted` column to visits. Never modify existing columns shared with utility app.
6. **ARQ cron for passive rewards**: Register `GameWorkerSettings` as a separate ARQ worker process alongside existing `WorkerSettings`.
7. **expo-notifications with EAS build**: Push notifications require a development build. Schedule local notifications (event countdowns) for Expo Go testing.
8. **Skip Skia for MVP**: Reanimated v4 + react-native-confetti-cannon achieves good loot box UX without the complexity and bundle size of Skia.

---

## Installation

```bash
# Bootstrap game app (in project root)
npx create-expo-app@latest game --template tabs

# Navigate to game dir
cd game

# Map (already in utility — same version)
npx expo install react-native-maps

# Creature grid
npx expo install @shopify/flash-list

# Notifications
npx expo install expo-notifications

# Confetti for loot reveal
npm install react-native-confetti-cannon

# Location (same as utility)
npx expo install expo-location expo-task-manager

# State + HTTP (same versions as utility)
npm install @tanstack/react-query@5 zustand@5 axios

# Storage
npx expo install @react-native-async-storage/async-storage expo-secure-store

# Animation + gestures (already in Expo)
npx expo install react-native-reanimated react-native-gesture-handler

# Blur (already in Expo)
npx expo install expo-blur

# Charts (for stats screens)
npm install react-native-gifted-charts

# Clustering (for game map markers)
npm install react-native-map-clustering

# Icons
npx expo install @expo/vector-icons

# Build tooling
eas build:configure
```

### Backend: Game Worker (separate process)

```bash
# Start game ARQ worker alongside existing scraping worker
python -m arq app.workers.game.GameWorkerSettings
```

---

## Sources & Verification

| Source | Type | Last Verified |
|--------|------|---------------|
| https://shopify.engineering/flashlist-v2 | Official (Shopify) | 2026-02-26 |
| https://shopify.github.io/flash-list/docs/ | Official | 2026-02-26 |
| https://docs.expo.dev/versions/latest/sdk/flash-list/ | Official (Expo) | 2026-02-26 |
| https://github.com/react-native-maps/react-native-maps/blob/master/docs/polygon.md | Official | 2026-02-26 |
| https://fastapi.tiangolo.com/advanced/websockets/ | Official | 2026-02-26 |
| https://oneuptime.com/blog/post/2026-01-25-websocket-servers-fastapi-redis/view | Community (Jan 2026) | 2026-02-26 |
| https://docs.expo.dev/versions/latest/sdk/notifications/ | Official (Expo) | 2026-02-26 |
| https://arq-docs.helpmanual.io | Official | 2026-02-26 |
| https://www.npmjs.com/package/react-native-confetti-cannon | npm registry | 2026-02-26 |
| https://docs.sqlalchemy.org/en/20/dialects/postgresql.html | Official | 2026-02-26 |
| /Users/arnaudmagnan/development/mappn/utility/package.json | Codebase | 2026-02-26 |
| /Users/arnaudmagnan/development/mappn/backend/requirements.txt | Codebase | 2026-02-26 |
| /Users/arnaudmagnan/development/mappn/.specs/plans/mappn-platform.design.md | Design doc | 2026-02-26 |

---

## Changelog

| Date | Changes |
|------|---------|
| 2026-02-26 | Initial creation for task: implement-game-app.feature.md |
