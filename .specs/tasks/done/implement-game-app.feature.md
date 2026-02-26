---
title: Implement Mappn game app with creatures, territories, and events
depends_on:
  - implement-shared-backend.feature.md
---

## Initial User Prompt

Build the Mappn game app (React Native/Expo): game map with territory overlays, creature collection and evolution, item/component inventory with crafting, territory claiming with home turf bonus, PvP/cooperative/personal zones, tiered events system (daily/weekly/monthly), friends and trading, leaderboards. See `.specs/plans/mappn-platform.design.md` for full game design.

## Description

> **Required Skill**: You MUST use and analyse `mappn-game-app` skill before doing any modification to task file or starting implementation of it!
>
> Skill location: `.claude/skills/mappn-game-app/SKILL.md`
>
> Also read prerequisite skills: `.claude/skills/react-native-expo-mobile-app/SKILL.md` and `.claude/skills/fastapi-postgis-backend/SKILL.md`

The Mappn Game app is the location-based RPG component of the Mappn platform. While the companion Utility app provides practical value through busyness data and exploration tracking, the Game app transforms confirmed real-world visits into a competitive RPG experience designed to drive sustained daily engagement and long-term player retention. The core game loop -- visit real places to earn XP, components, and loot boxes; collect and evolve creatures; claim and defend territories; earn passive rewards; visit more places -- creates a self-reinforcing cycle that motivates players to explore their city repeatedly. Territory PvP creates ongoing competition, events create time-limited urgency, and social features (friends, trading, leaderboards) create network effects that grow the player base organically.

The app consists of eight screens organized under a five-tab navigation bar (Map, Creatures, Inventory, Events, Profile). The Game Map is the home screen displaying territory overlays color-coded by ownership and zone type, creature icons on claimed territories, and event markers with countdown timers. The Creature Collection and Creature Detail screens let players browse, filter, and inspect their creatures including stats, equipped items, evolution progress, and territory assignments. The Inventory screen manages components by type, items by rarity, and unopened loot boxes, with access to a crafting interface. The Territory View shows ownership details, familiarity rankings, passive reward rates, and challenge or contribute actions depending on zone type. The Events screen lists active and upcoming events across all three tiers with location, time window, rewards, and quest progress. The Social screen (accessible from Profile) handles friends management, trading proposals, an activity feed, and leaderboards. The Profile screen displays player level, XP, creatures collected, territories held, and game achievements.

This task includes both the mobile app and the required backend extensions. The shared backend (authentication, places service, visit tracking, scraping pipeline) is already complete and will be consumed by this app without modification. However, the game requires new backend endpoints for the game engine (creature management, territory operations, loot and reward processing, event participation, PvP resolution) and the social service (friends, trading, leaderboards), as well as new database tables for all game and social entities (creatures, creature templates, items, components, territories, events, friends, trades, leaderboard entries). The existing shared database tables (users, places, areas, visits) must not be modified; new tables reference them via foreign keys.

**Scope**:
- Included: All 8 game screens (Game Map, Creature Collection, Creature Detail, Inventory, Territory View, Events, Social, Profile), 5-tab navigation (Map, Creatures, Inventory, Events, Profile), authentication flow (reusing shared auth with session persistence and automatic credential refresh), GPS coordinate submission for visit tracking, game map with territory overlays color-coded by ownership and zone type, creature icons on territories, event markers with countdowns, creature collection with rarity-weighted loot box drops (Common 60%, Uncommon 25%, Rare 10%, Epic 4%, Legendary 1%), creature leveling via XP from visits and passive income, creature evolution at level thresholds (10, 25, 50), creature stat management (power, defense, stamina), item slots per creature by rarity (Common/Uncommon: 1, Rare/Epic: 2, Legendary: 3), item equipping and unequipping, component collection from visits (1-3 per visit based on place category), item crafting from components, loot box opening with rarity rolls, territory claiming by assigning a creature chief (requires prior visit), personal zones (single owner, safe passive income), cooperative zones (multiple contributors, pooled rewards), PvP zones (contestable, highest passive rewards), home turf familiarity bonus from physical time spent in area, PvP territory challenges (stat + item + familiarity comparison), passive reward generation (hourly creature XP + components scaled by territory busyness and creature power), daily events (3-5 per city/day, 2-4 hours, bonus components and 50% loot box chance), weekly events (1 per city/week, 24 hours, guaranteed rare+ loot box and exclusive items), monthly events (1 global, 3-7 days, legendary creature chance, unique cosmetics, multi-step quests), friends management (add via username or QR code), friends territory visibility on map, friends collection and stats viewing, activity feed of friends actions, creature and item trading with mutual confirmation and 24-hour cooldown, leaderboards (local/global/friends by territory count, creature power, and exploration percentage), player profile with level/XP/collection/territory stats, new backend endpoints for game engine and social service, new database tables for all game and social entities, first-time player onboarding experience, empty states for all screens, error handling for all failure scenarios
- Excluded: Modifications to existing shared backend tables or endpoints, real-money transactions or premium currency, push notifications, augmented reality features, admin or content management tools, chat or messaging between players, guild or clan system, creature cosmetics marketplace, app store deployment, full offline mode, analytics infrastructure, WebSocket real-time features, deployment infrastructure

**User Scenarios**:
1. **Primary Flow**: Player logs in (or registers via shared auth), views the game map with color-coded territory overlays and event markers, physically visits a place (GPS coordinates sent every 15 seconds, visit confirmed by backend after 5+ minutes in geofence), receives XP, 1-3 components, and potentially a loot box (30% base chance), opens the loot box to receive a creature or item with rarity-weighted probability, views the creature in their collection, equips an item, navigates to an unclaimed territory they have previously visited, assigns the creature as chief to claim the territory, earns passive rewards hourly, and checks leaderboard rankings.
2. **Alternative Flows**: Player crafts an item from accumulated components and equips it on a creature to boost stats; player challenges another player's creature in a PvP zone and wins based on combined power (stats + items + familiarity), becoming the new territory chief; player contributes a creature to a cooperative zone alongside other players for pooled rewards; player participates in a daily event by visiting the event location within the time window and receives bonus components and increased loot box chance; player adds a friend via QR code, views their territories on the map, and proposes a creature trade; player's creature reaches level 10 and evolves into a stronger form with improved base stats; player's authentication token expires mid-session and the app silently refreshes it.
3. **Error Handling**: Player attempts to claim a territory they have never visited and sees a message requiring at least one prior visit to the area; player attempts to equip an item when all creature slots are full and sees a message indicating no available slots; player attempts to trade during the 24-hour cooldown period and sees the remaining cooldown time; player opens the game map in an area with no busyness data and territories display as uncategorized until data becomes available; network connection is lost and the app displays cached game data with a connectivity warning; player attempts to assign a creature that is already chief of another territory and is prompted to reassign; location permission denied shows guidance explaining why location is needed, with the map still viewable but game actions requiring location disabled.

---

## Acceptance Criteria

### Functional Requirements

#### Authentication

- [ ] **User Registration and Login**: Players can create accounts and authenticate using the shared authentication system
  - Given: A new or returning player opens the game app
  - When: The player registers with email, username, and password, or logs in with existing credentials
  - Then: The player is authenticated and the game map is displayed with their game data

- [ ] **Session Persistence and Token Refresh**: Players remain logged in across app launches and tokens refresh transparently
  - Given: A player has previously logged in and their access credential expires during active use
  - When: The app makes a request that is rejected due to expired credentials
  - Then: The app automatically refreshes the credential, retries the original request, and the player's experience continues without interruption; if refresh fails, the player is redirected to login with a clear message

- [ ] **First-Time Player Onboarding**: New players receive a starter experience to begin the game loop
  - Given: A player logs in for the first time with no creatures, items, or territories
  - When: The player completes authentication
  - Then: The player receives a starter loot box containing at least one creature, and the app guides them to open it, view their first creature, and understand the game map

#### Game Map

- [ ] **Territory Overlay Display**: The game map shows territories color-coded by ownership and zone type
  - Given: The player is on the game map screen
  - When: The map loads or the player pans to a new area
  - Then: Territory boundaries are displayed with color overlays: blue for player-owned, green for friend-owned, red for PvP zones, purple for cooperative zones, and grey for unclaimed territories

- [ ] **Creature Icons on Territories**: Claimed territories show the assigned chief creature
  - Given: The player has claimed one or more territories with assigned creature chiefs
  - When: The player views the game map
  - Then: An icon representing the assigned chief creature appears on each of the player's claimed territories

- [ ] **Event Markers**: Active and upcoming events appear on the map with countdown timers
  - Given: There are active or upcoming events within the visible map area
  - When: The player views the game map
  - Then: Glowing markers appear at event locations showing the event tier (daily/weekly/monthly) and a countdown timer to the event end (if active) or start (if upcoming)

- [ ] **Territory Tap Detail**: Tapping a territory reveals its details
  - Given: The game map is displaying territory overlays
  - When: The player taps on a territory
  - Then: A detail card appears showing the zone type (personal/cooperative/PvP), current owner (if claimed), chief creature name and power, passive reward rate, and the player's familiarity score for that area

- [ ] **Visit Reward Indicators**: The map signals when the player is near a place eligible for visit rewards
  - Given: The player has granted location permission and is physically near a place
  - When: The player's GPS coordinates indicate proximity to a place within geofence range
  - Then: A reward indicator appears on the map near that place, signaling potential XP, components, and loot box rewards upon confirmed visit

#### Creatures

- [ ] **Loot Box Creature Drops**: Creatures are obtained from loot boxes with defined rarity distribution
  - Given: A player has an unopened loot box
  - When: The player opens the loot box and it contains a creature
  - Then: The creature's rarity is determined by weighted probability: Common (60%), Uncommon (25%), Rare (10%), Epic (4%), Legendary (1%), and the creature is themed to a place category

- [ ] **Creature XP and Leveling**: Creatures gain XP from visits and passive territory income
  - Given: A player has one or more creatures
  - When: The player completes a confirmed visit or a creature is assigned as chief of a territory generating passive rewards
  - Then: The creature gains XP, and the creature's current XP and progress toward the next level are displayed on the creature detail screen

- [ ] **Creature Evolution**: Creatures evolve at defined level thresholds
  - Given: A creature has reached level 10, 25, or 50
  - When: The creature accumulates enough XP to reach the evolution threshold
  - Then: The creature evolves into its next form with improved base stats (power, defense, stamina), the evolution is visually indicated, and the creature's evolution stage is updated

- [ ] **Creature Collection View**: Players can browse and filter their creature collection
  - Given: A player has collected one or more creatures
  - When: The player navigates to the Creature Collection screen
  - Then: All owned creatures are displayed in a grid view with filtering options for rarity (Common through Legendary), level range, and category affinity, and each creature shows its name, rarity indicator, level, and power rating

- [ ] **Creature Detail View**: Players can inspect individual creature details
  - Given: A player taps on a creature in their collection
  - When: The Creature Detail screen opens
  - Then: The screen displays the creature's stats (power, defense, stamina), equipped items in their slots, evolution progress bar showing XP toward next evolution threshold, current territory assignment (if any), and creature history

- [ ] **Creature Item Slots**: Creatures have a defined number of item slots based on rarity
  - Given: A player views a creature's detail screen
  - When: The player inspects the item slot area
  - Then: The creature displays the correct number of equippable item slots: 1 slot for Common and Uncommon creatures, 2 slots for Rare and Epic creatures, and 3 slots for Legendary creatures

#### Items and Inventory

- [ ] **Component Collection from Visits**: Players earn components from confirmed visits
  - Given: A player completes a confirmed visit to a place
  - When: The visit is recorded by the backend
  - Then: The player receives 1-3 components, with the component type determined by the place's category (e.g., restaurant visits yield food-themed components, park visits yield nature-themed components)

- [ ] **Loot Box Chance from Visits**: Each confirmed visit has a chance to grant a loot box
  - Given: A player completes a confirmed visit
  - When: The visit reward is calculated
  - Then: The player has a 30% base chance of receiving a loot box (increased to 50% during daily events), and the loot box contains either a creature or an item with rarity determined by weighted probability

- [ ] **Loot Box Opening**: Players can open loot boxes to receive creatures or items
  - Given: A player has one or more unopened loot boxes in their inventory
  - When: The player selects a loot box and opens it
  - Then: The loot box reveals its contents (a creature or an item) with a visual reveal sequence, and the received creature or item is added to the player's collection or inventory

- [ ] **Item Crafting**: Players can craft items by combining components
  - Given: A player has sufficient components of the required types
  - When: The player selects a crafting recipe and confirms
  - Then: The required components are consumed, a new item is created with the specified rarity and stat boosts, and the item appears in the player's inventory

- [ ] **Item Equipping**: Players can equip items on creatures in available slots
  - Given: A player has an item in their inventory and a creature with at least one empty item slot
  - When: The player selects the item and assigns it to the creature
  - Then: The item is equipped in one of the creature's available slots, the creature's effective stats are updated to reflect the item's boosts, and the item is removed from the unequipped inventory

- [ ] **Item Unequipping**: Players can remove items from creatures
  - Given: A creature has one or more items equipped
  - When: The player selects an equipped item and chooses to unequip it
  - Then: The item is returned to the player's inventory, and the creature's effective stats are reduced by the item's boost values

- [ ] **Inventory Display**: The inventory screen organizes all player assets
  - Given: A player navigates to the Inventory screen
  - When: The screen loads
  - Then: The inventory displays three sections: components listed by type with current quantities, items listed by rarity with stat boost summaries, and a count of unopened loot boxes with an option to open them

#### Territories

- [ ] **Territory Claiming**: Players can claim unclaimed territories after visiting the area
  - Given: A player has at least one confirmed visit to a place within a territory's area and has an available creature
  - When: The player selects the unclaimed territory and assigns a creature as chief
  - Then: The territory is claimed by the player, the creature is assigned as chief, and the territory overlay changes to blue (player-owned) on the game map

- [ ] **Territory Claiming Prerequisite**: Players cannot claim territories they have never visited
  - Given: A player has never had a confirmed visit to any place within a territory's area
  - When: The player attempts to claim that territory
  - Then: The system displays a message indicating the player must visit the area at least once before claiming, and the claim action is blocked

- [ ] **Personal Zone Behavior**: Quiet areas function as personal territories with safe passive income
  - Given: A territory's area has a low busyness score, classifying it as a personal zone
  - When: A player claims this territory
  - Then: Only that one player can own the territory, no other players can challenge for it, and it generates passive rewards at the personal zone rate

- [ ] **Cooperative Zone Behavior**: Moderate-activity areas allow multiple players to contribute
  - Given: A territory's area has a moderate busyness score, classifying it as a cooperative zone
  - When: Multiple players assign creatures to contribute to the territory
  - Then: All contributing players share the territory, pooling creature power yields improved passive rewards compared to individual claiming, and all contributors receive a share of the passive rewards

- [ ] **PvP Zone Behavior**: High-activity areas are contestable with the best rewards
  - Given: A territory's area has a high busyness score, classifying it as a PvP zone
  - When: A player claims or currently holds the territory
  - Then: Other players can challenge the current chief, the territory generates passive rewards at the highest rate among zone types, and the territory overlay shows red on the game map

- [ ] **Zone Type Classification**: Territory zone types are derived from real-world busyness data
  - Given: An area has busyness data from the scraping pipeline
  - When: The system determines the area's zone type
  - Then: The zone type (personal, cooperative, or PvP) is assigned based on the area's aggregate busyness score, with quieter areas becoming personal zones, moderately busy areas becoming cooperative zones, and the busiest areas becoming PvP zones [NEEDS CLARIFICATION: What are the specific busyness score thresholds for each zone type classification?]

- [ ] **Passive Reward Generation**: Claimed territories generate rewards over time
  - Given: A player has claimed one or more territories with creature chiefs assigned
  - When: Each hourly reward cycle completes
  - Then: Each territory generates creature XP for the chief creature and components for the player, with reward amounts scaled by the territory's busyness level and the chief creature's power rating

- [ ] **Home Turf Familiarity Bonus**: Physical time spent in an area strengthens defending creatures
  - Given: A player has spent cumulative physical time in a territory's area (tracked via GPS and visit confirmations)
  - When: The player's creature defends the territory in a PvP challenge
  - Then: The defending creature receives a familiarity bonus to its effective power proportional to the player's accumulated time in that area, giving local players a natural defensive advantage

#### PvP

- [ ] **Territory Challenge**: Players can challenge the current chief of a PvP territory
  - Given: A player has a creature available (not currently assigned as chief elsewhere or willing to reassign) and is viewing a PvP territory owned by another player
  - When: The player selects the challenge action and assigns their attacking creature
  - Then: A challenge is initiated comparing the attacker's creature (stats + equipped item boosts) against the defender's creature (stats + equipped item boosts + home turf familiarity bonus)

- [ ] **Challenge Resolution**: PvP challenges resolve deterministically based on combined power
  - Given: A PvP challenge has been initiated between an attacking creature and a defending chief
  - When: The system calculates the outcome
  - Then: The creature with the higher combined power (base stats + item boosts, plus familiarity bonus for the defender) wins; the winner becomes or remains the territory chief, and both players see the challenge result with a breakdown of the power comparison

- [ ] **Familiarity Retention After Loss**: Defenders keep their familiarity score when losing a territory
  - Given: A defender loses a PvP challenge and their territory is taken by the attacker
  - When: The defender later views the lost territory or initiates a challenge to reclaim it
  - Then: The defender's familiarity score for that area remains unchanged, giving them a stronger position for reclaiming compared to a new challenger with no familiarity

#### Events

- [ ] **Daily Events**: Short-duration events appear multiple times per day with bonus rewards
  - Given: The events system has scheduled daily events
  - When: A daily event is active in the player's city
  - Then: The event appears on both the game map (as a glowing marker) and the Events screen, lasts 2-4 hours, and grants bonus components and a 50% loot box chance (up from 30% base) to players who physically visit the event location and meet the visit time threshold

- [ ] **Weekly Events**: Longer events with guaranteed high-value rewards appear once per week per city
  - Given: The events system has scheduled a weekly event
  - When: A weekly event is active in the player's city
  - Then: The event appears on the map and Events screen, lasts 24 hours, and grants a guaranteed loot box of Rare rarity or higher plus exclusive items not available through normal gameplay

- [ ] **Monthly Events**: Global multi-day events with the highest-value rewards and multi-step quests
  - Given: The events system has scheduled a monthly global event
  - When: A monthly event is active
  - Then: The event appears globally on all players' maps and Events screens, lasts 3-7 days, offers a chance at Legendary creature drops and unique cosmetics, and includes multi-step quest objectives that players can track and complete over the event duration

- [ ] **Event Participation**: Events require physical presence within the time window
  - Given: An event is currently active at a specific location
  - When: A player physically visits the event location (confirmed via GPS within geofence, standard visit time threshold met) during the event's active time window
  - Then: The player's participation is recorded, event rewards are granted, and quest progress (if applicable) is updated

- [ ] **Events Screen**: Players can view all active and upcoming events
  - Given: A player navigates to the Events screen
  - When: The screen loads
  - Then: The screen displays a list of active events (with remaining time) and upcoming events (with start countdowns), each showing event tier (daily/weekly/monthly), location, time window, available rewards, and quest progress for events the player has started

#### Social

- [ ] **Add Friends**: Players can connect with other players via username or QR code
  - Given: A player navigates to the Social screen
  - When: The player enters another player's username or scans their QR code and sends a friend request
  - Then: A friend request is sent to the target player, and when the target player accepts, both players appear in each other's friends lists

- [ ] **Friends on Map**: Friends' territories are visible on the game map
  - Given: A player has one or more friends who own territories
  - When: The player views the game map
  - Then: Friends' territories are displayed with green overlays, distinguishable from the player's own territories (blue) and other zone colors

- [ ] **View Friends' Profiles**: Players can see friends' collections and stats
  - Given: A player taps on a friend in their friends list
  - When: The friend's profile loads
  - Then: The player can see the friend's creature collection (names, rarities, levels), territory count, player level, and exploration percentage, but cannot modify any of the friend's data

- [ ] **Activity Feed**: Players see recent actions from their friends
  - Given: A player has friends who have performed game actions (claimed territories, evolved creatures, completed events)
  - When: The player views the activity feed on the Social screen
  - Then: A chronological list of recent friend activities is displayed, showing the friend's name, the action taken, and when it occurred

- [ ] **Trade Proposal**: Players can propose trades of creatures and items to friends
  - Given: A player and a friend both have creatures or items available for trading
  - When: The player selects items/creatures to offer and items/creatures to request, then submits the trade proposal to the friend
  - Then: The friend receives the trade proposal showing what is offered and what is requested, and can accept or decline

- [ ] **Trade Confirmation and Execution**: Both parties must confirm for a trade to complete
  - Given: A trade proposal has been sent to a friend
  - When: The receiving friend accepts the trade
  - Then: The offered creatures/items transfer from the sender to the receiver, the requested creatures/items transfer from the receiver to the sender, and both players see updated inventories and collections reflecting the trade

- [ ] **Trade Cooldown**: A 24-hour cooldown prevents rapid repeated trading
  - Given: A player has just completed a trade
  - When: The player attempts to initiate another trade within 24 hours
  - Then: The system blocks the new trade and displays the remaining cooldown time until the player can trade again

- [ ] **Leaderboard Display**: Players can view rankings across multiple scopes and metrics
  - Given: A player navigates to the leaderboards section
  - When: The player selects a scope (local city, global, or friends) and a metric (territory count, total creature power, or exploration percentage)
  - Then: A ranked list of players is displayed showing rank position, player name, and the selected metric value, with the current player's position highlighted

- [ ] **No Real-Money Trading**: The trading system prevents any real-money exchange
  - Given: The trading system is available between friends
  - When: Any trade is proposed or completed
  - Then: Only in-game creatures and items can be included in trades; there is no mechanism for attaching, requesting, or transferring real-world currency or premium currency

#### Player Profile

- [ ] **Profile Overview**: Players can view their overall game progress
  - Given: A player navigates to the Profile screen
  - When: The screen loads
  - Then: The screen displays the player's current level, total XP with progress toward next level, total creatures collected, total territories currently held, and game achievements earned

- [ ] **Game Achievements**: Players earn achievements for game milestones
  - Given: A player reaches a defined game milestone (e.g., first territory claimed, first creature evolved, first PvP victory)
  - When: The milestone condition is met
  - Then: The corresponding achievement is unlocked, displayed on the Profile screen, and the player is notified of the achievement

- [ ] **Social Access from Profile**: The Social screen is accessible from the Profile tab
  - Given: A player is on the Profile screen
  - When: The player taps the social/friends section
  - Then: The player is navigated to the Social screen showing friends list, trading, activity feed, and leaderboards

#### Error Handling and Edge Cases

- [ ] **Location Permission Denied**: The app handles missing location permissions gracefully
  - Given: The player has not granted location permission or has revoked it
  - When: The player opens the game map or attempts a location-dependent action
  - Then: A guidance message explains why location is needed for the game, the map is still viewable but territory claiming, event participation, and visit tracking are disabled, and a prompt to enable location is accessible

- [ ] **Network Loss**: The app handles connectivity interruptions without data loss
  - Given: The player is actively using the game app
  - When: The network connection is lost
  - Then: The app displays previously loaded game data (map, collection, inventory) with a visible connectivity warning, and location-dependent actions are queued or paused until connectivity is restored

- [ ] **Creature Assignment Conflict**: The app handles reassignment of already-assigned creatures
  - Given: A player's creature is currently assigned as chief of one territory
  - When: The player attempts to assign the same creature as chief of a different territory
  - Then: The app prompts the player to confirm reassignment, explaining that the creature will be removed from its current territory, and only proceeds upon confirmation

- [ ] **Empty States**: All screens display helpful guidance when no data is available
  - Given: A new player has not yet collected creatures, claimed territories, or completed events
  - When: The player navigates to any game screen (Collection, Inventory, Events, Social, etc.)
  - Then: Each screen displays an empty state with a clear message guiding the player on how to start populating that screen (e.g., "Visit places to earn your first loot box!" on the Collection screen)

### Non-Functional Requirements

- [ ] **Map Loading Performance**: The game map loads territory overlays and event markers within 3 seconds of opening the map screen
- [ ] **Collection Loading Performance**: The creature collection screen loads and displays up to 100 creatures within 2 seconds
- [ ] **Loot Box Reveal Performance**: Loot box opening animation completes and reveals the result within 5 seconds
- [ ] **PvP Resolution Performance**: Territory challenge calculations complete and display results within 3 seconds
- [ ] **Leaderboard Loading Performance**: Leaderboard data loads and displays rankings within 3 seconds
- [ ] **GPS Tracking Consistency**: GPS coordinates are submitted every 15 seconds while the app is in the foreground, consistent with the utility app's tracking frequency

### Definition of Done

- [ ] All acceptance criteria pass
- [ ] All 8 game screens are navigable and functional
- [ ] The complete game loop works end-to-end: visit -> rewards -> loot box -> creature -> territory claim -> passive rewards
- [ ] All 3 territory zone types (personal, cooperative, PvP) function according to their specified behaviors
- [ ] All 3 event tiers (daily, weekly, monthly) display and grant correct rewards upon participation
- [ ] Social features (friends, trading, leaderboards) are operational
- [ ] New backend endpoints for game engine and social service are implemented and tested
- [ ] New database tables for game and social entities are created with proper foreign key references to shared tables
- [ ] Existing shared backend tables and endpoints are unmodified
- [ ] Empty states and error handling cover all documented scenarios
- [ ] Tests written and passing
- [ ] Documentation updated
- [ ] Code reviewed

---

## Architecture

### References

- **Skill**: `.claude/skills/mappn-game-app/SKILL.md`
- **Codebase Analysis**: `.specs/analysis/analysis-implement-game-app.md`
- **Scratchpad**: `.specs/scratchpad/02873aab.md`

### Solution Strategy

**Approach**: Mirror the existing utility app architecture (Expo SDK ~54 + expo-router + TanStack Query + Zustand) for the game frontend, and extend the shared FastAPI backend with additive-only database migrations, new API routers, services, and an ARQ game worker -- all following the exact patterns already established in the codebase.

**Key Decisions**:
1. **Copy utility app patterns verbatim for shared infrastructure**: `api.ts`, `authStore.ts`, `locationStore.ts` are copied from `utility/` to `game/` rather than extracting into a shared package -- because the risk of breaking the working utility app with monorepo restructuring outweighs the DRY benefit for ~5 small files that rarely change.
2. **ARQ (not Celery) for passive rewards worker**: The analysis mentions Celery, but the existing codebase uses ARQ exclusively (see `backend/app/workers/scraping.py`). A new `GameWorkerSettings` class follows the `WorkerSettings` pattern from `scraping.py`.
3. **No WebSocket for MVP**: The task scope explicitly excludes "WebSocket real-time features". TanStack Query with appropriate staleTime values (30s for territories, 60s for events) provides near-real-time updates via polling.
4. **Lazy import for visit_service -> game_service**: Prevents circular module dependency by importing `dispatch_visit_rewards` inside the `auto_confirm_visit` function body.
5. **Row-level locking for PvP**: `SELECT ... FOR UPDATE` on Territory row before challenge resolution prevents concurrent challenge race conditions.
6. **Server-side rarity rolls only**: All loot box rarity determination happens in `open_loot_box()` on the backend -- never expose RNG logic to the client.

**Trade-offs Accepted**:
- Code duplication of ~5 files between `utility/` and `game/` -- accepted for isolation and simplicity over monorepo complexity
- Polling instead of WebSocket for territory/event updates -- accepted because WebSocket is out of scope and polling at 30-60s intervals is sufficient for the game's pace
- Single `passive_rewards_tick` per hour may become slow with many territories -- accepted for MVP, can batch/parallelize later

---

### Architecture Decomposition

**Components**:

| Component | Responsibility | Dependencies |
|-----------|---------------|--------------|
| 003_game_schema migration | Create 10+ new DB tables + 1 column addition | 002 migration, existing users/places/areas/visits tables |
| Game ORM Models (5 files) | Creature, Item, Territory, Event, Social models | Base class, ForeignKey refs to shared tables |
| Game Pydantic Schemas (4 files) | Request/response validation for all game endpoints | Model field definitions |
| Game Services (4 files) | Business logic: rewards, creatures, territories, events, social | ORM models, PostGIS functions |
| Game API Routers (4 files) | HTTP endpoints under /game/* prefix | Services, schemas, auth deps |
| Game ARQ Worker | Hourly passive rewards, periodic leaderboard refresh | Services, AsyncSessionLocal |
| visit_service modification | Hook to dispatch game rewards after visit confirmation | game_service.dispatch_visit_rewards |
| Game Expo App (~60 files) | Full React Native game client | Shared backend API, same stack as utility |

**Interactions**:

```
[Game App (Expo)] ----REST----> [FastAPI Backend]
       |                              |
       |  GPS pings                   |---> [visit_service] ---> [game_service.dispatch_visit_rewards]
       |  API calls                   |---> [game router] ---> [game_service]
       |  Territory calls             |---> [territory router] ---> [territory_service] ---> [PostGIS]
       |  Event calls                 |---> [events router] ---> [event_service] ---> [PostGIS]
       |  Social calls                |---> [social router] ---> [social_service]
       |                              |
       |                         [ARQ Game Worker]
       |                              |---> [passive_rewards_tick] (hourly)
       |                              |---> [refresh_leaderboards] (every 15 min)
       |                              |
       |                         [PostgreSQL/PostGIS]
       |                              |---> shared tables (users, places, areas, visits)
       |                              |---> game tables (creatures, items, territories, events, ...)
```

---

### Expected Changes

```
backend/
├── alembic/versions/
│   └── 003_game_schema.py                    # NEW: All game tables + rewards_granted column
├── app/
│   ├── main.py                               # UPDATE: Include 4 new game routers
│   ├── models/
│   │   ├── __init__.py                       # UPDATE: Import 12 new model classes
│   │   ├── creature.py                       # NEW: Creature + CreatureTemplate
│   │   ├── item.py                           # NEW: Item + ItemTemplate + Component + LootBox
│   │   ├── territory.py                      # NEW: Territory
│   │   ├── event.py                          # NEW: GameEvent + EventParticipation
│   │   └── social.py                         # NEW: Friend + Trade + LeaderboardEntry
│   ├── schemas/
│   │   ├── game.py                           # NEW: Game profile, creature, inventory schemas
│   │   ├── territory.py                      # NEW: Territory schemas
│   │   ├── event.py                          # NEW: Event schemas
│   │   └── social.py                         # NEW: Social schemas
│   ├── api/
│   │   ├── game.py                           # NEW: /game/* routes
│   │   ├── territories.py                    # NEW: /game/territories/* routes
│   │   ├── events.py                         # NEW: /game/events/* routes
│   │   └── social_game.py                    # NEW: /game/social/* routes
│   ├── services/
│   │   ├── visit_service.py                  # UPDATE: Add dispatch_visit_rewards call
│   │   ├── game_service.py                   # NEW: Core game logic
│   │   ├── territory_service.py              # NEW: Territory + PvP logic
│   │   ├── event_service.py                  # NEW: Event logic
│   │   └── social_service.py                 # NEW: Social logic
│   └── workers/
│       └── game.py                           # NEW: GameWorkerSettings + passive rewards
├── tests/
│   ├── conftest.py                           # UPDATE: Add game model imports + routers
│   ├── test_game.py                          # NEW: Game endpoint tests
│   ├── test_territories.py                   # NEW: Territory endpoint tests
│   ├── test_events.py                        # NEW: Event endpoint tests
│   └── test_social_game.py                   # NEW: Social endpoint tests

game/                                          # NEW: Entire Expo app (~60 files)
├── app.config.ts                             # NEW
├── package.json                              # NEW
├── tsconfig.json                             # NEW
├── eas.json                                  # NEW
├── app/
│   ├── _layout.tsx                           # NEW: Root layout (auth gate, providers)
│   ├── (auth)/{_layout,login,register}.tsx   # NEW: Auth screens
│   ├── (tabs)/                               # NEW: 5-tab layout
│   │   ├── _layout.tsx                       # NEW: Tab bar (Map|Creatures|Inventory|Events|Profile)
│   │   ├── index.tsx                         # NEW: Game Map (territory overlays, events)
│   │   ├── creatures.tsx                     # NEW: Creature collection grid
│   │   ├── inventory.tsx                     # NEW: Components, items, loot boxes, crafting
│   │   ├── events.tsx                        # NEW: Active + upcoming events
│   │   └── profile.tsx                       # NEW: Player level, XP, stats, social link
│   ├── creature/[id].tsx                     # NEW: Creature detail
│   ├── territory/[id].tsx                    # NEW: Territory detail
│   ├── event/[id].tsx                        # NEW: Event detail
│   └── social/                               # NEW: Social screens
│       ├── index.tsx                         # NEW: Social hub
│       ├── friends.tsx                       # NEW: Friends list
│       ├── trades.tsx                        # NEW: Trade management
│       └── leaderboard.tsx                   # NEW: Leaderboards
├── components/                               # NEW: ~25 component files
│   ├── map/                                  # TerritoryOverlay, EventMarker, CreatureMarker,
│   │                                         # LootIndicator, TerritoryInfoSheet
│   ├── creature/                             # CreatureCard, CreatureGrid, RarityFilter,
│   │                                         # StatBar, EvolutionProgress, ItemSlot
│   ├── inventory/                            # ComponentList, ItemCard, LootBoxCard,
│   │                                         # LootBoxOpenAnimation, CraftingScreen
│   ├── territory/                            # FamiliarityRanking, PassiveRateDisplay, ChallengeButton
│   ├── event/                                # EventCard, QuestStepList, CheckInButton
│   ├── social/                               # FriendCard, TradeCard, LeaderboardRow, ActivityFeedItem
│   └── ui/                                   # Button, Card, LoadingSpinner, ErrorBoundary,
│                                             # NetworkBanner, RarityBadge, EmptyState
├── hooks/                                    # NEW: ~12 hook files
│   ├── useLocationTracking.ts                # Copy from utility (game-specific query keys)
│   ├── useGameProfile.ts                     # TanStack Query: GET /game/me
│   ├── useCreatures.ts                       # TanStack Query: GET /game/creatures
│   ├── useCreatureDetail.ts                  # TanStack Query: GET /game/creatures/{id}
│   ├── useInventory.ts                       # TanStack Query: GET /game/inventory
│   ├── useNearbyTerritories.ts               # TanStack Query: GET /game/territories/nearby
│   ├── useTerritoryDetail.ts                 # TanStack Query: GET /game/territories/{id}
│   ├── useNearbyEvents.ts                    # TanStack Query: GET /game/events
│   ├── useEventDetail.ts                     # TanStack Query: GET /game/events/{id}
│   ├── useFriends.ts                         # TanStack Query: GET /game/social/friends
│   ├── useTrades.ts                          # TanStack Query: GET /game/social/trades
│   └── useLeaderboard.ts                     # TanStack Query: GET /game/leaderboards
├── services/                                 # NEW: ~8 service files
│   ├── api.ts                                # Copy from utility (same interceptors)
│   ├── authService.ts                        # Copy from utility
│   ├── gameService.ts                        # Game profile, creatures, inventory, loot, craft
│   ├── territoryService.ts                   # Territory CRUD, claim, challenge, contribute
│   ├── eventService.ts                       # Events, check-in
│   ├── socialService.ts                      # Friends, trades, leaderboards
│   ├── visitsService.ts                      # GPS ping submission (copy from utility)
│   └── locationService.ts                    # Start/stop tracking (copy from utility)
├── stores/                                   # NEW: 4 store files
│   ├── authStore.ts                          # Copy from utility
│   ├── locationStore.ts                      # Copy from utility
│   ├── gameStore.ts                          # Selected territory, loot queue
│   └── mapStore.ts                           # Map region state
├── constants/                                # NEW: 2 files
│   ├── colors.ts                             # GAME_COLORS, RARITY_COLORS, ZONE_COLORS
│   └── config.ts                             # API_BASE_URL, STALE_TIME, GPS constants
└── types/                                    # NEW: 2 files
    ├── api.ts                                # TypeScript interfaces for all game schemas
    └── navigation.ts                         # Expo Router typed params
```

---

### Runtime Scenarios

**Scenario: Complete Game Loop (Visit -> Rewards -> Territory Claim)**

```
Player opens app ──> Auth gate (loadTokens) ──> Game Map loads
     |
     v
GPS tracking starts (15s interval)
     |
     v
Player physically visits a place (5+ min dwell)
     |
     v
visit_service.auto_confirm_visit()
     |
     ├──> Visit row created in DB
     └──> game_service.dispatch_visit_rewards()
              |
              ├──> +25 XP to user
              ├──> +2 nature components (park category)
              └──> 30% roll -> LootBox created
     |
     v
Client receives confirmed_visits with rewards
     |
     v
TanStack Query invalidates ['inventory', 'creatures', 'game-profile']
     |
     v
Player opens loot box from Inventory tab
     |
     v
game_service.open_loot_box() -> Rarity roll -> Uncommon Creature
     |
     v
LootBoxOpenAnimation plays (Reanimated spring + confetti)
     |
     v
Player views new creature in Collection tab
     |
     v
Player navigates to unclaimed territory on map
     |
     v
territory_service.claim_territory() -> Assigns creature as chief
     |
     v
Territory overlay changes to blue on map
     |
     v
ARQ hourly tick -> passive_rewards_tick() -> XP + components generated
```

**State Transitions (Territory Lifecycle)**:

```
[Unclaimed] ── player claims ──> [Personal Zone: single owner]
                                     |
                                  hourly tick
                                     |
                                     v
                              [Generating Passive Rewards]

[Unclaimed] ── player claims ──> [PvP Zone: owner + chief]
                                     |
                              challenger attacks
                                     |
                                     v
                              [Challenge Resolution]
                                  /        \
                           attacker wins   defender wins
                              /                \
                             v                  v
                    [New Owner + Chief]    [Same Owner]
                    familiarity resets     familiarity retained
                    for new owner         for defender

[Unclaimed] ── player contributes ──> [Coop Zone: multiple contributors]
                                          |
                                       more players contribute
                                          |
                                          v
                                    [Pooled Rewards]
                                    (scaled by total creature power)
```

---

### Architecture Decisions

#### Decision 1: ARQ over Celery for Game Worker

**Status**: Accepted

**Context**: The analysis file mentions "Celery periodic task" for passive rewards, but the existing codebase exclusively uses ARQ (see `backend/app/workers/scraping.py`).

**Decision**: Use ARQ with a separate `GameWorkerSettings` class, following the exact pattern from `scraping.py` `WorkerSettings`. Run as separate process: `python -m arq app.workers.game.GameWorkerSettings`.

**Consequences**:
- Consistent with existing worker infrastructure
- Same deployment pattern, single Redis dependency
- No additional Celery/RabbitMQ infrastructure needed

#### Decision 2: Polling over WebSocket for Real-Time Updates

**Status**: Accepted

**Context**: The skill file describes a `useGameSocket` WebSocket hook, but the task scope explicitly excludes "WebSocket real-time features."

**Decision**: Use TanStack Query polling with short staleTime: 30s for territories, 60s for events, 120s for leaderboards.

**Consequences**:
- Compliant with task scope exclusions
- Slightly delayed updates (30-60s) for territory changes -- acceptable for game pace
- No additional infrastructure (Redis Pub/Sub, WebSocket endpoint)

#### Decision 3: Copy Shared Files over Monorepo Extraction

**Status**: Accepted

**Context**: `game/` and `utility/` share ~5 identical files (`api.ts`, `authStore.ts`, `locationStore.ts`, `authService.ts`, config patterns).

**Decision**: Copy files between apps. The ~5 files change infrequently and the risk of disrupting the working utility app with monorepo restructuring exceeds the DRY benefit.

**Consequences**:
- Minor code duplication (~5 files)
- Zero risk to working utility app
- Independent modification if game-specific needs arise

#### Decision 4: Deterministic PvP with Row-Level Locking

**Status**: Accepted

**Context**: PvP territory challenges must resolve consistently even under concurrent access.

**Decision**: Use `SELECT FOR UPDATE` on the Territory row before computing challenge resolution. This prevents two simultaneous challengers from both winning.

**Consequences**:
- Atomic territory state transitions
- Brief lock contention under simultaneous challenges (acceptable at game scale)

#### Decision 5: Familiarity Bonus Formula

**Status**: Accepted

**Context**: The design doc states "familiarity score" provides a defensive bonus but does not specify the formula.

**Decision**: `familiarity_bonus = min(score / 1000, 0.5)` where score is cumulative seconds spent in the area. Caps at 50% of base stats (~16.7 min total for max bonus).

**Consequences**:
- Capped at 50% to prevent unchallengeably strong defenders
- Linear scaling incentivizes repeated visits
- Score persists after territory loss (per task requirement)
- Easy to tune by adjusting the divisor (1000) or cap (0.5)

---

### High-Level Structure

```
Mappn Game App Feature
├── Backend Extensions (additive to shared backend)
│   ├── Database Layer: 003_game_schema migration + 5 model files (12 models)
│   ├── Schema Layer: 4 Pydantic schema files
│   ├── Service Layer: 4 service files (game, territory, event, social)
│   ├── API Layer: 4 router files under /game/* prefix
│   ├── Worker Layer: 1 ARQ worker (passive rewards + leaderboard refresh)
│   └── Integration: 3 existing file modifications (visit_service, main, models/__init__)
├── Game Mobile App (new Expo project at /game/)
│   ├── Infrastructure: api.ts, authStore, locationStore, gameStore (mirrors utility)
│   ├── Navigation: 5-tab layout + stack screens for detail views
│   ├── Screens: 8 game screens + 4 social screens + 2 auth screens
│   ├── Components: ~25 UI components across 6 domains
│   └── Hooks: ~12 TanStack Query + tracking hooks
└── Backend Tests: 4 new test modules
```

---

### Workflow Steps

```
Phase 1: DB Foundation    ──> Phase 2: Schemas    ──> Phase 3: Services
    (models, migration)       (Pydantic types)        (business logic)
                                                           |
                                                           v
Phase 4: API Routers  ──> Phase 5: Workers  ──> Phase 6: Backend Tests
    (HTTP endpoints)       (ARQ game worker)     (integration tests)
         |
         v
Phase 7: App Bootstrap  ──> Phase 8: App Foundation  ──> Phase 9: Game Map
    (Expo project setup)     (auth, services, stores)     (territories, events)
                                     |                          |
                                     v                          v
                             Phase 10: Creatures/Inventory   Phase 11: Territory/Event Detail
                                     |                          |
                                     v                          v
                             Phase 12: Social/Profile  ──> Phase 13: Polish & E2E Testing
```

**Phase dependencies**:
- Phases 1-6 are backend (sequential)
- Phase 7 starts after Phase 4 (needs running API)
- Phases 8-12 are frontend (Phase 10 and 12 can run in parallel, both depend on Phase 8)
- Phase 13 depends on all previous phases

---

### Contracts

**Visit Reward Dispatch (internal service call)**:
```
Function: game_service.dispatch_visit_rewards(db, user_id, place_id, visit_id)
Input: { db: AsyncSession, user_id: int, place_id: int, visit_id: int }
Output: { xp_gained: int, components: [{type: str, quantity: int}], loot_box_id: int | None }
Side Effects: Updates User.xp, creates/updates Component rows, optionally creates LootBox row
```

**Loot Box Opening**:
```
Endpoint: POST /game/inventory/loot-boxes/{loot_box_id}/open
Input: {} (loot_box_id in path, user from JWT)
Output: { type: "creature"|"item", rarity: str, creature?: CreatureResponse, item?: ItemResponse }
Errors: 404 (not found), 400 (already opened), 403 (not owner)
```

**Territory Claim**:
```
Endpoint: POST /game/territories/{territory_id}/claim
Input: { creature_id: int }
Output: TerritoryResponse
Errors: 400 (no prior visit to area), 400 (creature not available), 404 (territory not found)
```

**PvP Challenge**:
```
Endpoint: POST /game/territories/{territory_id}/challenge
Input: { creature_id: int }
Output: { winner: "attacker"|"defender", attacker_power: float, defender_power: float,
          breakdown: {...}, territory: TerritoryResponse }
Errors: 400 (not PvP zone), 400 (own territory), 404 (territory not found)
```

**Nearby Territories**:
```
Endpoint: GET /game/territories/nearby?lat={lat}&lon={lon}&radius_m={radius}
Input: { lat: float, lon: float, radius_m: int (default 2000) }
Output: { territories: TerritoryResponse[], count: int }
```

**Event Check-In**:
```
Endpoint: POST /game/events/{event_id}/check-in
Input: { lat: float, lon: float }
Output: { participation_id: int, rewards: {...}, quest_progress?: {...} }
Errors: 400 (event not active), 400 (not within radius), 409 (already checked in)
```

**Trade Creation**:
```
Endpoint: POST /game/social/trades
Input: { receiver_id: int, offered_creature_ids: int[], offered_item_ids: int[],
         requested_creature_ids: int[], requested_item_ids: int[] }
Output: TradeResponse
Errors: 400 (24h cooldown active), 400 (not friends), 400 (creature/item not owned)
```

**GameWorkerSettings Interface**:
```python
class GameWorkerSettings:
    functions = [passive_rewards_tick, refresh_leaderboards]
    cron_jobs = [
        cron(passive_rewards_tick, hour=None, minute=0),      # Every hour
        cron(refresh_leaderboards, minute={0, 15, 30, 45}),   # Every 15 min
    ]
    redis_settings = _LazyRedisSettings()  # Same lazy pattern as scraping.py
```

---

## Implementation Process

You MUST launch for each step a separate agent, instead of performing all steps yourself. And for each step marked as parallel, you MUST launch separate agents in parallel.

**CRITICAL:** For each agent you MUST:
1. Use the **Agent** type specified in the step (e.g., `haiku`, `sonnet`, `sdd:developer`)
2. Provide path to task file and prompt which step to implement
3. Require agent to implement exactly that step, not more, not less, not other steps

### Implementation Strategy

**Approach**: Mixed (Bottom-Up for backend, Top-Down for frontend)

**Rationale**: The backend complexity lies in data models, business logic algorithms (PvP resolution, rarity rolls, passive rewards), and PostGIS queries -- these are best built bottom-up from models through services to routers. The frontend complexity lies in screen workflow and navigation -- the game loop UX is well-defined, so screens are built top-down from navigation structure through screens to extracted components.

### Parallelization Overview

```
Step 1 (DB Schema & Models) [sdd:developer/opus]       Step 8 (Expo Setup) [haiku]
        |                                                       |
        v                                                       |
Step 2 (Pydantic Schemas) [sdd:developer/opus]                  |
        |                                                       |
        +------------------+                                    |
        |                  |                                    |
        v                  v                                    |
Step 3 (Game Svc)    Step 4 (Territory +                        |
[sdd:developer/opus]  Event Svc)                                |
  |  PARALLEL      [sdd:developer/opus]                         |
  |                    |                                        |
  v                    |                                        |
Step 5 (Social Svc     |                                        |
+ Visit Integration)   |                                        |
[sdd:developer/opus]   |                                        |
        |              |                                        |
        +------+-------+                                        |
               |                                                |
               v                                                |
      Step 6 (API Routers + Worker) [sdd:developer/opus]        |
               |                                                |
               +--------------------+---------------------------+
               |                    |
               v                    v
      Step 7 (Backend Tests)     Step 9 (App Foundation)
      [sdd:developer/opus]      [sdd:developer/opus]
      PARALLEL                      |
                  +---------+-------+-------+---------+---------+
                  |         |       |       |         |         |
                  v         v       v       v         v         v
               Step 10   Step 11 Step 12 Step 13   Step 14   Step 15
              (Game Map) (Creat) (Inv)  (Detail)  (Terr+Evt)(Social)
              [dev/opus] [dev]   [dev]  [dev]     [dev]     [dev]
                  |   PARALLEL -- ALL 6 STEPS MUST RUN IN PARALLEL  |
                  +----+--------+-------+---------+---------+-------+
                                        |
                                        v
                                Step 16 (Profile + Polish)
                                [sdd:developer/opus]
```

---

### Step 1: Database Schema Migration & ORM Models

**Model:** opus
**Agent:** sdd:developer
**Depends on:** None
**Parallel with:** Step 8

**Goal**: Create the database foundation for all game entities -- 12 new ORM model classes across 5 files and a single Alembic migration that creates all game tables plus adds the `rewards_granted` column to the existing `visits` table.

#### Expected Output

- `backend/alembic/versions/003_game_schema.py`: Migration creating 10+ tables and 1 column addition
- `backend/app/models/creature.py`: Creature + CreatureTemplate models
- `backend/app/models/item.py`: Item + ItemTemplate + Component + LootBox models
- `backend/app/models/territory.py`: Territory model
- `backend/app/models/event.py`: GameEvent + EventParticipation models
- `backend/app/models/social.py`: Friend + Trade + LeaderboardEntry models
- `backend/app/models/__init__.py`: Updated with imports for all 12 new model classes

#### Success Criteria

- [ ] Migration `003_game_schema.py` runs successfully after `002_utility_schema.py`
- [ ] All 12 model classes are importable from `backend/app/models`
- [ ] Foreign keys correctly reference existing tables: `users.id`, `places.id`, `areas.id`, `visits.id`
- [ ] `Territory.area_id` has UNIQUE constraint (one territory per area)
- [ ] `GameEvent.location` uses `Geography(geometry_type="POINT", srid=4326)`
- [ ] `Territory.familiarity_scores` uses JSONB type
- [ ] GIST index created on `GameEvent.location` for spatial queries
- [ ] `rewards_granted` JSONB column added to `visits` table (nullable)
- [ ] `alembic upgrade head` completes without errors
- [ ] `alembic downgrade -1` cleanly reverses the migration

#### Subtasks

- [ ] Create `backend/app/models/creature.py` with `Creature` and `CreatureTemplate` classes following `backend/app/models/visit.py` patterns (mapped_column, ForeignKey, relationships)
- [ ] Create `backend/app/models/item.py` with `Item`, `ItemTemplate`, `Component`, `LootBox` classes
- [ ] Create `backend/app/models/territory.py` with `Territory` class including JSONB `familiarity_scores` and UNIQUE constraint on `area_id`
- [ ] Create `backend/app/models/event.py` with `GameEvent` and `EventParticipation` classes; `GameEvent.location` uses `Geography(geometry_type="POINT", srid=4326)`
- [ ] Create `backend/app/models/social.py` with `Friend`, `Trade`, `LeaderboardEntry` classes
- [ ] Update `backend/app/models/__init__.py` to import and export all 12 new model classes
- [ ] Create `backend/alembic/versions/003_game_schema.py` following `002_utility_schema.py` pattern: all game tables + `rewards_granted` column on visits + GIST index on `game_events.location`
- [ ] Run `alembic upgrade head` and verify success
- [ ] Run `alembic downgrade -1` and verify clean reversal

#### Verification

**Level:** CRITICAL - Panel of 2 Judges with Aggregated Voting
**Artifact:** `backend/alembic/versions/003_game_schema.py`, `backend/app/models/creature.py`, `backend/app/models/item.py`, `backend/app/models/territory.py`, `backend/app/models/event.py`, `backend/app/models/social.py`, `backend/app/models/__init__.py`
**Threshold:** 4.0/5.0

**Rubric:**

| Criterion | Weight | Description |
|-----------|--------|-------------|
| Data Integrity | 0.25 | All 12 models have correct column types, constraints (UNIQUE on Territory.area_id), and JSONB fields (familiarity_scores, rewards_granted) |
| Migration Safety | 0.25 | Migration runs forward and rolls back cleanly; tables created in FK dependency order; additive-only to shared tables |
| Foreign Key Correctness | 0.20 | All FKs correctly reference existing tables (users.id, places.id, areas.id, visits.id) without modifying shared table structure |
| PostGIS Usage | 0.15 | GameEvent.location uses Geography(POINT, 4326); GIST index created on game_events.location |
| Pattern Conformance | 0.15 | Models follow existing visit.py patterns (mapped_column, ForeignKey, relationships, Base class) |

**Reference Pattern:** `backend/app/models/visit.py`, `backend/alembic/versions/002_utility_schema.py`

---

### Step 2: Pydantic Request/Response Schemas

**Model:** opus
**Agent:** sdd:developer
**Depends on:** Step 1
**Parallel with:** None

**Goal**: Define all Pydantic v2 schemas for game API request validation and response serialization, covering game profile, creatures, inventory, territories, events, and social features.

#### Expected Output

- `backend/app/schemas/game.py`: GameProfileResponse, CreatureResponse, CreatureListResponse, InventoryResponse, ComponentInventory, LootBoxResponse, LootBoxOpenResult, CraftItemRequest, EquipItemRequest
- `backend/app/schemas/territory.py`: TerritoryResponse, TerritoryListResponse, ClaimTerritoryRequest, ChallengeTerritoryRequest, ChallengeResult, ContributeRequest
- `backend/app/schemas/event.py`: EventResponse, EventListResponse, EventCheckInRequest, EventCheckInResult, QuestProgress
- `backend/app/schemas/social.py`: FriendResponse, FriendListResponse, AddFriendRequest, TradeResponse, TradeListResponse, CreateTradeRequest, RespondTradeRequest, LeaderboardEntryResponse, LeaderboardResponse

#### Success Criteria

- [ ] All schema files import successfully
- [ ] All response schemas use `model_config = ConfigDict(from_attributes=True)` for ORM compatibility
- [ ] Request schemas validate required fields (e.g., `ClaimTerritoryRequest` requires `creature_id: int`)
- [ ] Response schemas include all fields needed by frontend TypeScript types (as defined in analysis)
- [ ] `ChallengeResult` includes `winner`, `attacker_power`, `defender_power`, `breakdown` fields
- [ ] `LeaderboardEntryResponse` includes `rank`, `user_id`, `username`, `value`, `is_me` fields
- [ ] Schemas are importable from `backend/app/schemas/` submodules

#### Subtasks

- [ ] Create `backend/app/schemas/game.py` with all game profile, creature, and inventory schemas following `backend/app/schemas/utility.py` pattern
- [ ] Create `backend/app/schemas/territory.py` with territory request/response schemas
- [ ] Create `backend/app/schemas/event.py` with event request/response schemas
- [ ] Create `backend/app/schemas/social.py` with friend, trade, and leaderboard schemas
- [ ] Verify all schemas align with model field types from Step 1

#### Verification

**Level:** Per-Schema File Judges (4 separate evaluations in parallel)
**Artifacts:** `backend/app/schemas/{game,territory,event,social}.py`
**Threshold:** 4.0/5.0

**Rubric (per schema file):**

| Criterion | Weight | Description |
|-----------|--------|-------------|
| Contract Correctness | 0.30 | All request/response fields match model definitions and frontend TypeScript type expectations |
| ORM Compatibility | 0.25 | All response schemas use model_config = ConfigDict(from_attributes=True) |
| Validation Completeness | 0.25 | Request schemas validate all required fields with proper types |
| Pattern Conformance | 0.20 | Follows backend/app/schemas/utility.py patterns and naming conventions |

**Reference Pattern:** `backend/app/schemas/utility.py`

---

### Step 3: Game Service -- Core Game Logic

**Model:** opus
**Agent:** sdd:developer
**Depends on:** Step 1, Step 2
**Parallel with:** Step 4

**Goal**: Implement the central game business logic: visit reward dispatch (XP + components + loot box chance), loot box opening with server-side rarity rolls, creature evolution, item crafting, and item equip/unequip operations.

#### Expected Output

- `backend/app/services/game_service.py`: Complete game service with `dispatch_visit_rewards()`, `open_loot_box()`, `evolve_creature()`, `craft_item()`, `equip_item()`, `unequip_item()`, `get_game_profile()`, `get_creatures()`, `get_creature_detail()`, `get_inventory()`

#### Success Criteria

- [ ] `dispatch_visit_rewards()` grants 25 XP to user, creates 1-3 components based on place category, rolls 30% loot box chance
- [ ] `open_loot_box()` performs server-side rarity roll: Common 60%, Uncommon 25%, Rare 10%, Epic 4%, Legendary 1%
- [ ] `open_loot_box()` creates either a Creature or Item from a template based on the rarity roll
- [ ] `evolve_creature()` validates level thresholds (10, 25, 50) before evolving
- [ ] `craft_item()` validates component inventory before deducting and creating item
- [ ] `equip_item()` validates creature slot availability based on rarity (Common/Uncommon: 1, Rare/Epic: 2, Legendary: 3)
- [ ] `unequip_item()` returns item to inventory and updates creature stats
- [ ] All rarity determination happens server-side only (no RNG exposed to client)
- [ ] All database operations use proper async/await with AsyncSession

#### Subtasks

- [ ] Implement `get_game_profile(db, user_id)` returning user game stats (xp, level, creature_count, territory_count)
- [ ] Implement `get_creatures(db, user_id)` returning paginated creature list with filters
- [ ] Implement `get_creature_detail(db, user_id, creature_id)` returning full creature details with equipped items
- [ ] Implement `get_inventory(db, user_id)` returning components, items, and loot boxes
- [ ] Implement `dispatch_visit_rewards(db, user_id, place_id, visit_id)` with XP grant, component drops by place category, 30% loot box roll
- [ ] Implement `open_loot_box(db, user_id, loot_box_id)` with server-side weighted rarity roll and creature/item creation from templates
- [ ] Implement `evolve_creature(db, user_id, creature_id)` with level threshold validation (10/25/50) and stat recalculation
- [ ] Implement `craft_item(db, user_id, item_template_id)` with component cost validation and deduction
- [ ] Implement `equip_item(db, user_id, creature_id, item_id)` with slot count validation by rarity
- [ ] Implement `unequip_item(db, user_id, creature_id, item_id)` with stat recalculation
- [ ] Write unit tests for rarity roll distribution (verify weighted random selection logic)
- [ ] Write unit tests for creature slot count validation by rarity

#### Verification

**Level:** CRITICAL - Panel of 2 Judges with Aggregated Voting
**Artifact:** `backend/app/services/game_service.py`
**Threshold:** 4.0/5.0

**Rubric:**

| Criterion | Weight | Description |
|-----------|--------|-------------|
| Algorithm Correctness | 0.30 | Rarity roll weights match spec (60/25/10/4/1), evolution thresholds (10/25/50) correct, XP/component formulas correct |
| Security | 0.25 | All rarity determination server-side only, no RNG exposed to client, proper ownership validation before mutations |
| Error Handling | 0.20 | Handles edge cases: already opened loot box, insufficient components, full item slots, non-existent entities |
| Code Quality | 0.15 | Follows existing service patterns (async/await, AsyncSession), proper type hints |
| Completeness | 0.10 | All 10 functions implemented as specified in Expected Output |

**Reference Pattern:** `backend/app/services/visit_service.py`

---

### Step 4: Territory Service & Event Service

**Model:** opus
**Agent:** sdd:developer
**Depends on:** Step 1, Step 2
**Parallel with:** Step 3

**Goal**: Implement territory management with PostGIS spatial queries, PvP challenge resolution with row-level locking, familiarity bonus calculation, cooperative zone contribution, and event management with geofenced check-in.

#### Expected Output

- `backend/app/services/territory_service.py`: `get_nearby_territories()`, `get_territory_detail()`, `claim_territory()`, `challenge_territory()`, `contribute_to_territory()`, `compute_familiarity_bonus()`, `compute_effective_power()`
- `backend/app/services/event_service.py`: `get_nearby_events()`, `get_event_detail()`, `check_in_event()`, `compute_event_loot_box_bonus()`

#### Success Criteria

- [ ] `get_nearby_territories()` uses PostGIS `ST_DWithin` on `Area.boundary` (following `backend/app/services/visit_service.py:241-253` pattern)
- [ ] `claim_territory()` validates at least one prior Visit exists in the territory's area
- [ ] `claim_territory()` blocks claiming if territory is personal zone and already owned by another player
- [ ] `challenge_territory()` uses `SELECT ... FOR UPDATE` on Territory row to prevent concurrent challenge race conditions
- [ ] `challenge_territory()` computes effective power = base stats + item boosts + familiarity bonus (defender only)
- [ ] `compute_familiarity_bonus()` implements `min(score / 1000, 0.5)` formula (caps at 50%)
- [ ] `contribute_to_territory()` allows multiple players to assign creatures on cooperative zones
- [ ] Familiarity scores persist after territory loss (per acceptance criteria)
- [ ] `get_nearby_events()` uses PostGIS `ST_DWithin` on `GameEvent.location`, filtered by `ends_at > now()`
- [ ] `check_in_event()` validates player GPS is within event radius using `ST_DWithin`
- [ ] `check_in_event()` prevents duplicate check-ins (409 Conflict)
- [ ] `check_in_event()` grants event-specific rewards and updates quest progress if applicable
- [ ] All PostGIS queries use Geography type (meter-accurate distances)

#### Subtasks

- [ ] Implement `get_nearby_territories(db, lat, lon, radius_m)` with PostGIS ST_DWithin on Area.boundary, JOINing Territory data
- [ ] Implement `get_territory_detail(db, territory_id, user_id)` returning territory info with user's familiarity score
- [ ] Implement `claim_territory(db, user_id, territory_id, creature_id)` with visit prerequisite validation and zone-type rules
- [ ] Implement `compute_effective_power(creature, items, familiarity_score)` computing total power with item boosts and familiarity bonus
- [ ] Implement `compute_familiarity_bonus(familiarity_score)` with `min(score / 1000, 0.5)` formula
- [ ] Implement `challenge_territory(db, user_id, territory_id, attacker_creature_id)` with `SELECT FOR UPDATE` row locking and deterministic power comparison
- [ ] Implement `contribute_to_territory(db, user_id, territory_id, creature_id)` for cooperative zones
- [ ] Implement `get_nearby_events(db, lat, lon, radius_m)` with PostGIS ST_DWithin on GameEvent.location
- [ ] Implement `get_event_detail(db, event_id, user_id)` returning event info with user's participation status
- [ ] Implement `check_in_event(db, user_id, event_id, lat, lon)` with radius validation, duplicate check, reward granting
- [ ] Implement `compute_event_loot_box_bonus(event_tier)` returning bonus probability (50% for daily events)
- [ ] Write unit tests for familiarity bonus formula edge cases (0, 500, 1000, 2000 seconds)
- [ ] Write unit tests for effective power computation

#### Verification

**Level:** Per-Service File Judges (2 separate evaluations in parallel)
**Artifacts:** `backend/app/services/{territory_service,event_service}.py`
**Threshold:** 4.0/5.0

**Rubric (per service file):**

| Criterion | Weight | Description |
|-----------|--------|-------------|
| Correctness | 0.25 | PvP challenge uses deterministic power comparison; familiarity_bonus = min(score/1000, 0.5); claim validates prior visit; event check-in validates GPS within radius |
| Concurrency Safety | 0.25 | SELECT FOR UPDATE on Territory row before challenge resolution; prevents race conditions |
| PostGIS Usage | 0.20 | ST_DWithin used correctly on Area.boundary and GameEvent.location with Geography type (meter-accurate distances) |
| Error Handling | 0.15 | Proper validation: no prior visit blocks claim, non-PvP zone blocks challenge, duplicate check-in returns 409 |
| Pattern Conformance | 0.15 | Follows visit_service.py PostGIS patterns (lines 241-253), async/await with AsyncSession |

**Reference Pattern:** `backend/app/services/visit_service.py` (lines 241-253 for PostGIS pattern)

---

### Step 5: Social Service & Visit Service Integration

**Model:** opus
**Agent:** sdd:developer
**Depends on:** Step 1, Step 2, Step 3
**Parallel with:** None

**Goal**: Implement friends management, trade lifecycle with 24-hour cooldown and ownership validation, leaderboard aggregation, and integrate game reward dispatch into the existing visit confirmation flow.

#### Expected Output

- `backend/app/services/social_service.py`: `get_friends()`, `add_friend()`, `respond_friend_request()`, `get_trades()`, `create_trade()`, `respond_trade()`, `get_leaderboard()`, `get_activity_feed()`
- `backend/app/services/visit_service.py`: Modified `auto_confirm_visit()` with lazy import call to `dispatch_visit_rewards()`

#### Success Criteria

- [ ] `add_friend()` creates a Friend record with `status=pending`
- [ ] `respond_friend_request()` updates status to `accepted` or `blocked`
- [ ] `create_trade()` validates 24-hour cooldown since last completed trade
- [ ] `create_trade()` validates all offered creatures/items are owned by sender and not currently equipped
- [ ] `respond_trade()` uses `SELECT FOR UPDATE` on Item/Creature rows to prevent concurrent trade acceptance
- [ ] `respond_trade()` atomically transfers ownership of all offered and requested items/creatures
- [ ] `get_leaderboard()` supports three scopes (local/global/friends) and three metrics (territory_count/creature_power/exploration_pct)
- [ ] `get_activity_feed()` returns recent friend actions (territory claims, evolutions, event completions)
- [ ] `visit_service.auto_confirm_visit()` calls `game_service.dispatch_visit_rewards()` using lazy import (import inside function body) to avoid circular dependency
- [ ] Existing visit tests continue to pass after the modification

#### Subtasks

- [ ] Implement `get_friends(db, user_id)` returning friends list with game stats
- [ ] Implement `add_friend(db, user_id, friend_username)` creating pending friend request
- [ ] Implement `respond_friend_request(db, user_id, friend_id, accept)` updating friend status
- [ ] Implement `create_trade(db, sender_id, receiver_id, offered_ids, requested_ids)` with cooldown and ownership validation
- [ ] Implement `respond_trade(db, user_id, trade_id, accept)` with `SELECT FOR UPDATE` row locking on traded items/creatures
- [ ] Implement `get_leaderboard(db, scope, metric, user_id, city)` querying LeaderboardEntry with user highlighting
- [ ] Implement `get_activity_feed(db, user_id)` querying recent friend actions
- [ ] Modify `backend/app/services/visit_service.py`: In `auto_confirm_visit()`, add lazy import `from app.services.game_service import dispatch_visit_rewards` inside function body, then call `await dispatch_visit_rewards(db, user_id, place_id, visit.id)` after visit commit
- [ ] Verify existing `backend/tests/test_visits.py` tests still pass (mock `dispatch_visit_rewards` if needed)

#### Verification

**Level:** CRITICAL - Panel of 2 Judges with Aggregated Voting
**Artifact:** `backend/app/services/social_service.py`, `backend/app/services/visit_service.py` (modified)
**Threshold:** 4.0/5.0

**Rubric:**

| Criterion | Weight | Description |
|-----------|--------|-------------|
| Trade Atomicity | 0.25 | SELECT FOR UPDATE on traded items/creatures; atomic ownership transfer; 24h cooldown enforcement |
| Visit Integration Safety | 0.25 | Lazy import (inside function body) prevents circular dependency; existing visit tests still pass |
| Correctness | 0.20 | Friend lifecycle (pending -> accepted/blocked), leaderboard scopes (local/global/friends) x metrics (territory_count/creature_power/exploration_pct) |
| Error Handling | 0.15 | Validates ownership, friendship status, cooldown period, equipped creature trade prevention |
| Completeness | 0.15 | All 8 social service functions implemented; activity feed queries recent friend actions |

**Reference Pattern:** `backend/app/services/visit_service.py` (for integration pattern)

---

### Step 6: API Routers, Main Integration & ARQ Game Worker

**Model:** opus
**Agent:** sdd:developer
**Depends on:** Step 3, Step 4, Step 5
**Parallel with:** None

**Goal**: Create all 4 game API routers exposing service functions as HTTP endpoints, register them in main.py, and implement the ARQ game worker for passive rewards and leaderboard refresh.

#### Expected Output

- `backend/app/api/game.py`: Routes for `/game/me`, `/game/creatures`, `/game/creatures/{id}`, `/game/inventory`, `/game/inventory/loot-boxes/{id}/open`, `/game/inventory/craft`, `/game/creatures/{id}/evolve`, `/game/creatures/{creature_id}/items/{item_id}/equip`, `/game/creatures/{creature_id}/items/{item_id}/unequip`
- `backend/app/api/territories.py`: Routes for `/game/territories/nearby`, `/game/territories/{id}`, `/game/territories/{id}/claim`, `/game/territories/{id}/challenge`, `/game/territories/{id}/contribute`
- `backend/app/api/events.py`: Routes for `/game/events`, `/game/events/{id}`, `/game/events/{id}/check-in`
- `backend/app/api/social_game.py`: Routes for `/game/social/friends`, `/game/social/friends/add`, `/game/social/friends/{id}/respond`, `/game/social/trades`, `/game/social/trades/{id}/respond`, `/game/leaderboards`, `/game/social/activity`
- `backend/app/main.py`: Updated with 4 new router includes
- `backend/app/workers/game.py`: `GameWorkerSettings` with `passive_rewards_tick` and `refresh_leaderboards` cron jobs

#### Success Criteria

- [ ] All endpoints require JWT authentication via `Depends(get_current_user)` (following `backend/app/api/utility.py` pattern)
- [ ] All routes use appropriate HTTP methods (GET for reads, POST for mutations)
- [ ] All routes use response_model for Pydantic schema validation on responses
- [ ] `main.py` includes all 4 new routers; existing routers are unmodified
- [ ] ARQ `GameWorkerSettings` follows `backend/app/workers/scraping.py` `WorkerSettings` pattern exactly
- [ ] `passive_rewards_tick` runs hourly (minute=0), iterates all territories with owner+chief, computes XP + component rewards
- [ ] `refresh_leaderboards` runs every 15 minutes, aggregates and upserts LeaderboardEntry rows
- [ ] Server starts successfully with `uvicorn app.main:app`
- [ ] All new endpoints are accessible (200/401 responses)

#### Subtasks

- [ ] Create `backend/app/api/game.py` router with all game profile, creature, and inventory endpoints following `backend/app/api/utility.py` pattern
- [ ] Create `backend/app/api/territories.py` router with territory CRUD and PvP endpoints
- [ ] Create `backend/app/api/events.py` router with event listing and check-in endpoints
- [ ] Create `backend/app/api/social_game.py` router with friends, trades, leaderboard, and activity feed endpoints
- [ ] Update `backend/app/main.py` to include all 4 new routers after `app.include_router(utility_router)`
- [ ] Create `backend/app/workers/game.py` with `passive_rewards_tick` cron function and `refresh_leaderboards` cron function
- [ ] Create `GameWorkerSettings` class following `backend/app/workers/scraping.py` `WorkerSettings` pattern with cron_jobs list
- [ ] Verify server starts and all new endpoints respond

#### Verification

**Level:** Single Judge
**Artifact:** `backend/app/api/game.py`, `backend/app/api/territories.py`, `backend/app/api/events.py`, `backend/app/api/social_game.py`, `backend/app/main.py`, `backend/app/workers/game.py`
**Threshold:** 4.0/5.0

**Rubric:**

| Criterion | Weight | Description |
|-----------|--------|-------------|
| Auth & Routing | 0.25 | All endpoints require JWT via Depends(get_current_user); correct HTTP methods (GET for reads, POST for mutations) |
| Response Validation | 0.20 | All routes use response_model for Pydantic schema validation on responses |
| Worker Correctness | 0.20 | GameWorkerSettings follows scraping.py WorkerSettings pattern; passive_rewards_tick hourly (minute=0); refresh_leaderboards every 15 min |
| Integration | 0.20 | main.py includes all 4 new routers; existing routers unmodified; server starts successfully |
| Completeness | 0.15 | All specified endpoints present across 4 router files |

**Reference Pattern:** `backend/app/api/utility.py`, `backend/app/workers/scraping.py`

---

### Step 7: Backend Integration Tests

**Model:** opus
**Agent:** sdd:developer
**Depends on:** Step 6
**Parallel with:** Step 9

**Goal**: Write integration tests for all game backend endpoints, covering the complete game loop, PvP resolution, event check-in, and social features.

#### Expected Output

- `backend/tests/test_game.py`: Tests for game profile, creatures, inventory, loot box opening, crafting, evolution, equip/unequip
- `backend/tests/test_territories.py`: Tests for nearby territories, claim, challenge (PvP), contribute, passive rewards
- `backend/tests/test_events.py`: Tests for event listing, event detail, check-in (within radius, outside radius, duplicate)
- `backend/tests/test_social_game.py`: Tests for friends CRUD, trade lifecycle (create, accept, decline, cooldown), leaderboard
- `backend/tests/conftest.py`: Updated with game model imports and test fixtures

#### Success Criteria

- [ ] All new tests pass with `pytest backend/tests/test_game.py backend/tests/test_territories.py backend/tests/test_events.py backend/tests/test_social_game.py`
- [ ] Existing tests in `backend/tests/` continue to pass (no regressions)
- [ ] Test coverage includes: loot box rarity roll, territory claim with visit prerequisite, PvP challenge resolution, event radius check-in, trade cooldown enforcement, friend request lifecycle
- [ ] Tests use async patterns following `backend/tests/conftest.py` fixtures
- [ ] Tests mock PostGIS spatial data where needed for territory and event tests

#### Subtasks

- [ ] Update `backend/tests/conftest.py` to import all 12 game models and add game-specific test fixtures (test creature templates, test items, test territories, test events)
- [ ] Create `backend/tests/test_game.py` with tests for: GET /game/me, GET /game/creatures, GET /game/inventory, POST loot box open, POST craft item, POST evolve creature, POST equip/unequip item
- [ ] Create `backend/tests/test_territories.py` with tests for: GET nearby territories, POST claim (success + no prior visit), POST challenge (attacker wins + defender wins), POST contribute (cooperative zone)
- [ ] Create `backend/tests/test_events.py` with tests for: GET events, GET event detail, POST check-in (within radius, outside radius, already checked in)
- [ ] Create `backend/tests/test_social_game.py` with tests for: GET friends, POST add friend, POST respond friend request, POST create trade (success + cooldown), POST respond trade (accept + decline)
- [ ] Run full test suite and verify no regressions

#### Verification

**Level:** Per-Test File Judges (5 separate evaluations in parallel)
**Artifacts:** `backend/tests/{conftest.py,test_game.py,test_territories.py,test_events.py,test_social_game.py}`
**Threshold:** 4.0/5.0

**Rubric (per test file):**

| Criterion | Weight | Description |
|-----------|--------|-------------|
| Coverage | 0.30 | Tests cover all endpoints in the corresponding router with success and error cases |
| Edge Cases | 0.25 | Tests include: rarity roll, visit prerequisite, PvP resolution, event radius, trade cooldown, friend lifecycle |
| Isolation | 0.20 | Tests use async fixtures from conftest.py; PostGIS spatial data mocked where needed |
| Clarity | 0.15 | Test names clearly describe the scenario being tested |
| No Regressions | 0.10 | Existing tests in backend/tests/ continue to pass |

**Reference Pattern:** `backend/tests/conftest.py`, `backend/tests/test_visits.py`

---

### Step 8: Game App Expo Project Setup

**Model:** haiku
**Agent:** haiku
**Depends on:** None
**Parallel with:** Step 1

**Goal**: Bootstrap the game Expo project with all dependencies installed, configured for the same stack as the utility app (Expo SDK ~54, expo-router ~6, TanStack Query v5, Zustand v5, react-native-maps).

#### Expected Output

- `game/` directory with complete Expo project scaffolding
- `game/package.json`: All dependencies installed
- `game/app.config.ts`: Configured with game-specific bundle ID, Maps API keys, location permissions
- `game/eas.json`: EAS build profiles (development, preview, production)
- `game/tsconfig.json`: TypeScript configuration

#### Success Criteria

- [ ] `npx expo start` runs successfully in the `game/` directory
- [ ] All required dependencies installed: react-native-maps, @shopify/flash-list, expo-notifications, react-native-confetti-cannon, expo-location, expo-task-manager, @tanstack/react-query, zustand, axios, expo-secure-store, @react-native-async-storage/async-storage, react-native-reanimated, react-native-gesture-handler, expo-blur, react-native-gifted-charts, react-native-map-clustering, @expo/vector-icons
- [ ] `app.config.ts` includes plugins for react-native-maps (API keys) and expo-location (permissions)
- [ ] `eas.json` has development, preview, and production build profiles
- [ ] Bundle identifier is `com.mappn.game` (distinct from utility `com.mappn.utility`)

#### Subtasks

- [ ] Run `npx create-expo-app@latest game --template tabs` in project root
- [ ] Install all game-specific dependencies (see SKILL.md Installation section)
- [ ] Create `game/app.config.ts` following `utility/app.config.ts` pattern but with `com.mappn.game` bundle ID and game-specific name
- [ ] Create `game/eas.json` following `utility/eas.json` pattern
- [ ] Verify `npx expo start` launches without errors

#### Verification

**Level:** NOT NEEDED
**Rationale:** Simple project scaffolding operation. Success is binary -- Expo starts or it does not. Dependencies install or they do not. No judgment needed beyond the success criteria checks.

---

### Step 9: Game App Foundation -- Infrastructure, Auth, Navigation & Hooks

**Model:** opus
**Agent:** sdd:developer
**Depends on:** Step 6, Step 8
**Parallel with:** Step 7

**Goal**: Set up all shared infrastructure (API client, stores, services, hooks, types, constants), auth flow, and navigation structure. This step makes the app functional with login/register, 5-tab navigation, and all data-fetching hooks ready for screens.

#### Expected Output

- `game/services/api.ts`: Axios client (copy from utility)
- `game/services/authService.ts`: Auth service (copy from utility)
- `game/services/gameService.ts`: Game API calls (creatures, inventory, loot, craft, evolve, equip)
- `game/services/territoryService.ts`: Territory API calls (nearby, detail, claim, challenge, contribute)
- `game/services/eventService.ts`: Event API calls (list, detail, check-in)
- `game/services/socialService.ts`: Social API calls (friends, trades, leaderboard, activity)
- `game/services/visitsService.ts`: GPS ping submission (copy from utility)
- `game/services/locationService.ts`: Location tracking (copy from utility)
- `game/stores/authStore.ts`: Auth state (copy from utility)
- `game/stores/locationStore.ts`: Location state (copy from utility)
- `game/stores/gameStore.ts`: Game state (selected territory, loot queue)
- `game/stores/mapStore.ts`: Map region state
- `game/hooks/useLocationTracking.ts`: GPS tracking (adapted from utility)
- `game/hooks/useGameProfile.ts`, `useCreatures.ts`, `useCreatureDetail.ts`, `useInventory.ts`, `useNearbyTerritories.ts`, `useTerritoryDetail.ts`, `useNearbyEvents.ts`, `useEventDetail.ts`, `useFriends.ts`, `useTrades.ts`, `useLeaderboard.ts`: TanStack Query hooks
- `game/types/api.ts`: TypeScript interfaces for all game API responses
- `game/types/navigation.ts`: Expo Router typed params
- `game/constants/colors.ts`: GAME_COLORS, RARITY_COLORS, ZONE_COLORS
- `game/constants/config.ts`: API_BASE_URL, staleTime values, GPS constants
- `game/app/_layout.tsx`: Root layout with QueryClientProvider, GestureHandlerRootView, auth gate
- `game/app/(auth)/_layout.tsx`, `login.tsx`, `register.tsx`: Auth screens (adapted from utility)
- `game/app/(tabs)/_layout.tsx`: 5-tab bottom navigation (Map, Creatures, Inventory, Events, Profile)
- `game/components/ui/Button.tsx`, `Card.tsx`, `LoadingSpinner.tsx`, `ErrorBoundary.tsx`, `NetworkBanner.tsx`, `RarityBadge.tsx`, `EmptyState.tsx`: Shared UI components

#### Success Criteria

- [ ] App launches and shows login screen for unauthenticated users
- [ ] Login with valid credentials navigates to the game map (tabs) screen
- [ ] Registration creates a new account and navigates to tabs
- [ ] Token refresh works transparently (401 interceptor in api.ts)
- [ ] 5-tab bottom navigation displays: Map, Creatures, Inventory, Events, Profile
- [ ] All TanStack Query hooks return loading/error/data states correctly
- [ ] `useLocationTracking` hook starts GPS tracking and submits pings to `/visits/ping`
- [ ] `gameStore` manages selectedTerritoryId and lootQueue state
- [ ] All TypeScript types compile without errors
- [ ] `RARITY_COLORS`, `ZONE_COLORS`, `GAME_COLORS` constants are defined
- [ ] `EmptyState` component renders placeholder text for empty screens

#### Subtasks

- [ ] Copy `utility/services/api.ts` to `game/services/api.ts` (same interceptors, update import paths)
- [ ] Copy `utility/services/authService.ts` to `game/services/authService.ts`
- [ ] Copy `utility/services/visitsService.ts` to `game/services/visitsService.ts`
- [ ] Copy `utility/services/locationService.ts` to `game/services/locationService.ts`
- [ ] Create `game/services/gameService.ts` with functions for all `/game/*` endpoints
- [ ] Create `game/services/territoryService.ts` with functions for all `/game/territories/*` endpoints
- [ ] Create `game/services/eventService.ts` with functions for all `/game/events/*` endpoints
- [ ] Create `game/services/socialService.ts` with functions for all `/game/social/*` and `/game/leaderboards` endpoints
- [ ] Copy `utility/stores/authStore.ts` to `game/stores/authStore.ts`
- [ ] Copy `utility/stores/locationStore.ts` to `game/stores/locationStore.ts`
- [ ] Create `game/stores/gameStore.ts` with `selectedTerritoryId`, `lootQueue`, `setSelectedTerritory`, `enqueueLoot`, `dequeueLoot` (following SKILL.md pattern)
- [ ] Create `game/stores/mapStore.ts` following `utility/stores/mapStore.ts` pattern
- [ ] Create `game/types/api.ts` with all TypeScript interfaces: GameProfileResponse, CreatureResponse, ItemResponse, ComponentInventory, LootBoxResponse, TerritoryResponse, EventResponse, FriendResponse, TradeResponse, LeaderboardEntryResponse
- [ ] Create `game/types/navigation.ts` with Expo Router typed params for creature/[id], territory/[id], event/[id]
- [ ] Create `game/constants/colors.ts` with GAME_COLORS, RARITY_COLORS, ZONE_COLORS, TERRITORY_OVERLAY_COLORS
- [ ] Create `game/constants/config.ts` with API_BASE_URL, STALE_TIMES (territories: 30s, events: 60s, leaderboard: 120s), GPS_INTERVAL
- [ ] Create all 12 TanStack Query hooks in `game/hooks/` following `utility/hooks/useNearbyPlaces.ts` pattern with appropriate staleTime values
- [ ] Adapt `utility/hooks/useLocationTracking.ts` for game app (change query keys to game-specific)
- [ ] Create `game/app/_layout.tsx` root layout following `utility/app/_layout.tsx` pattern (QueryClientProvider, GestureHandlerRootView, auth gate)
- [ ] Create `game/app/(auth)/_layout.tsx`, `login.tsx`, `register.tsx` following utility auth screens pattern
- [ ] Create `game/app/(tabs)/_layout.tsx` with 5 tabs: Map (map icon), Creatures (catching-pokemon icon), Inventory (inventory icon), Events (event icon), Profile (person icon)
- [ ] Create shared UI components: `game/components/ui/Button.tsx`, `Card.tsx`, `LoadingSpinner.tsx`, `ErrorBoundary.tsx`, `NetworkBanner.tsx`, `RarityBadge.tsx`, `EmptyState.tsx`
- [ ] Add placeholder content to each tab screen file so navigation works
- [ ] Verify login -> tabs navigation flow works end-to-end

#### Verification

**Level:** CRITICAL - Panel of 2 Judges with Aggregated Voting
**Artifact:** `game/services/`, `game/stores/`, `game/hooks/`, `game/types/`, `game/constants/`, `game/app/_layout.tsx`, `game/app/(auth)/`, `game/app/(tabs)/_layout.tsx`, `game/components/ui/`
**Threshold:** 4.0/5.0

**Rubric:**

| Criterion | Weight | Description |
|-----------|--------|-------------|
| Auth Flow | 0.25 | Login/register works; token refresh transparent (401 interceptor); auth gate redirects unauthenticated users to login |
| Hook Correctness | 0.20 | All 12 TanStack Query hooks return loading/error/data states; appropriate staleTime values (territories: 30s, events: 60s, leaderboard: 120s) |
| Navigation Structure | 0.20 | 5-tab layout correct (Map, Creatures, Inventory, Events, Profile); stack screens configured for detail views |
| Type Safety | 0.15 | All TypeScript interfaces compile without errors; types match backend Pydantic schema field definitions |
| Pattern Conformance | 0.20 | Copied files (api.ts, authStore, locationStore) match utility app patterns; stores follow Zustand v5 patterns; hooks follow useNearbyPlaces.ts pattern |

**Reference Pattern:** `utility/services/api.ts`, `utility/stores/authStore.ts`, `utility/hooks/useNearbyPlaces.ts`, `utility/app/_layout.tsx`

---

### Step 10: Game Map Screen

**Model:** opus
**Agent:** sdd:developer
**Depends on:** Step 9
**Parallel with:** Step 11, Step 12, Step 13, Step 14, Step 15
**Note:** All 6 screen steps (10-15) MUST be launched in parallel by separate agents

**Goal**: Build the Game Map home screen with territory polygon overlays color-coded by ownership and zone type, creature icons on claimed territories, event markers with countdown timers, loot indicators near places, and a bottom sheet for territory details on tap.

#### Expected Output

- `game/app/(tabs)/index.tsx`: Game Map screen with MapView, territory overlay, event markers, loot indicators
- `game/components/map/TerritoryOverlay.tsx`: Polygon overlays colored by zone type and ownership (blue=own, green=friend, red=PvP, purple=coop, grey=unclaimed)
- `game/components/map/EventMarker.tsx`: Glowing event marker with countdown timer
- `game/components/map/CreatureMarker.tsx`: Creature icon on claimed territories
- `game/components/map/LootIndicator.tsx`: Animated indicator for nearby loot-eligible places
- `game/components/map/TerritoryInfoSheet.tsx`: Bottom sheet showing territory details on tap

#### Success Criteria

- [ ] Map loads and displays territory polygons within 3 seconds
- [ ] Territory overlays use correct colors: blue (own), green (friend), red (PvP), purple (cooperative), grey (unclaimed)
- [ ] Tapping a territory opens TerritoryInfoSheet showing zone type, owner, chief creature, passive rate, familiarity score
- [ ] Event markers display with tier-specific styling (daily/weekly/monthly) and countdown timers
- [ ] Creature icons appear on player's claimed territories
- [ ] Loot indicators pulse near eligible places when player is in range
- [ ] Only viewport-visible territories are rendered (performance: memoize with useMemo, filter by map bounds)
- [ ] `tracksViewChanges={false}` set on all static markers
- [ ] Territory data refreshes every 30 seconds via TanStack Query polling

#### Subtasks

- [ ] Create `game/components/map/TerritoryOverlay.tsx` using `react-native-maps Polygon` component with zone type color mapping (following SKILL.md TerritoryLayer pattern)
- [ ] Create `game/components/map/EventMarker.tsx` with `react-native-maps Marker` and countdown timer text
- [ ] Create `game/components/map/CreatureMarker.tsx` with creature icon overlay on territories
- [ ] Create `game/components/map/LootIndicator.tsx` with Reanimated pulsing animation
- [ ] Create `game/components/map/TerritoryInfoSheet.tsx` using `@gorhom/bottom-sheet` with territory detail card
- [ ] Implement `game/app/(tabs)/index.tsx` composing MapView with all overlay components, using `useNearbyTerritories` and `useNearbyEvents` hooks
- [ ] Add viewport-based territory filtering (only render polygons within visible map bounds)
- [ ] Add GPS tracking integration (useLocationTracking starts on map mount)
- [ ] Test map loads within 3 seconds with territory data

#### Verification

**Level:** Single Judge
**Artifact:** `game/app/(tabs)/index.tsx`, `game/components/map/TerritoryOverlay.tsx`, `game/components/map/EventMarker.tsx`, `game/components/map/CreatureMarker.tsx`, `game/components/map/LootIndicator.tsx`, `game/components/map/TerritoryInfoSheet.tsx`
**Threshold:** 4.0/5.0

**Rubric:**

| Criterion | Weight | Description |
|-----------|--------|-------------|
| Visual Correctness | 0.25 | Territory overlays use correct colors: blue (own), green (friend), red (PvP), purple (coop), grey (unclaimed) |
| Interactivity | 0.25 | Tapping territory opens TerritoryInfoSheet; event markers show countdown timers; creature icons on claimed territories |
| Performance | 0.25 | Viewport-based filtering limits rendered polygons, useMemo memoization applied, tracksViewChanges=false on static markers, map loads within 3s |
| Data Integration | 0.15 | useNearbyTerritories and useNearbyEvents hooks integrated correctly; territory data refreshes every 30s via polling |
| Completeness | 0.10 | All 5 map components + screen file implemented as specified in Expected Output |

**Reference Pattern:** `utility/app/(tabs)/index.tsx` (for MapView integration pattern)

---

### Step 11: Creature Collection Screen

**Model:** opus
**Agent:** sdd:developer
**Depends on:** Step 9
**Parallel with:** Step 10, Step 12, Step 13, Step 14, Step 15
**Note:** All 6 screen steps (10-15) MUST be launched in parallel by separate agents

**Goal**: Build the Creature Collection tab screen with a FlashList grid of creature cards, rarity filtering, and navigation to creature detail.

#### Expected Output

- `game/app/(tabs)/creatures.tsx`: Creature Collection screen with grid and filters
- `game/components/creature/CreatureCard.tsx`: Grid card with rarity border color, level badge, mini stats
- `game/components/creature/CreatureGrid.tsx`: FlashList v2 grid wrapper with numColumns=3
- `game/components/creature/RarityFilter.tsx`: Filter pills (All/Common/Uncommon/Rare/Epic/Legendary)

#### Success Criteria

- [ ] Creature collection displays in a 3-column grid using `@shopify/flash-list` v2
- [ ] Each creature card shows name, rarity-colored border, level, and power rating
- [ ] Rarity filter pills filter the displayed creatures by rarity tier
- [ ] Tapping a creature card navigates to `creature/[id]` detail screen
- [ ] Collection loads and displays up to 100 creatures within 2 seconds
- [ ] Empty state displays when player has no creatures ("Visit places to earn your first loot box!")
- [ ] Grid scrolls at 60fps with 100+ items

#### Subtasks

- [ ] Create `game/components/creature/CreatureCard.tsx` with rarity-colored border (using RARITY_COLORS), level badge, name, and power display
- [ ] Create `game/components/creature/CreatureGrid.tsx` wrapping `FlashList` with `numColumns={3}` and `estimatedItemSize={120}`
- [ ] Create `game/components/creature/RarityFilter.tsx` with horizontally scrollable filter pills that update filter state
- [ ] Implement `game/app/(tabs)/creatures.tsx` composing RarityFilter + CreatureGrid, using `useCreatures` hook with filter params
- [ ] Add empty state using `EmptyState` component when creature list is empty
- [ ] Add navigation to `creature/[id]` on card tap via expo-router `router.push()`

#### Verification

**Level:** Single Judge
**Artifact:** `game/app/(tabs)/creatures.tsx`, `game/components/creature/CreatureCard.tsx`, `game/components/creature/CreatureGrid.tsx`, `game/components/creature/RarityFilter.tsx`
**Threshold:** 4.0/5.0

**Rubric:**

| Criterion | Weight | Description |
|-----------|--------|-------------|
| Display Correctness | 0.25 | 3-column grid with FlashList v2; rarity-colored borders using RARITY_COLORS; level and power display per card |
| Filtering | 0.25 | Rarity filter pills work correctly (All/Common/Uncommon/Rare/Epic/Legendary); filter state updates grid |
| Performance | 0.20 | Loads 100 creatures within 2 seconds; FlashList with estimatedItemSize and numColumns=3; scrolls at 60fps |
| Navigation | 0.15 | Tapping card navigates to creature/[id] detail screen via expo-router |
| Empty State | 0.15 | Empty state shows "Visit places to earn your first loot box!" when player has no creatures |

**Reference Pattern:** `utility/` FlashList usage patterns (if any)

---

### Step 12: Inventory & Crafting Screen

**Model:** opus
**Agent:** sdd:developer
**Depends on:** Step 9
**Parallel with:** Step 10, Step 11, Step 13, Step 14, Step 15
**Note:** All 6 screen steps (10-15) MUST be launched in parallel by separate agents

**Goal**: Build the Inventory tab screen displaying components by type, items by rarity, loot boxes with open action, and a crafting interface for creating items from components.

#### Expected Output

- `game/app/(tabs)/inventory.tsx`: Inventory screen with three sections (components, items, loot boxes) and crafting access
- `game/components/inventory/ComponentList.tsx`: Component counts grouped by type
- `game/components/inventory/ItemCard.tsx`: Item card with rarity badge and stat boosts
- `game/components/inventory/LootBoxCard.tsx`: Loot box card with "Open" button
- `game/components/inventory/CraftingScreen.tsx`: Recipe selector, component cost display, craft button

#### Success Criteria

- [ ] Inventory displays three sections: Components (by type with quantities), Items (by rarity with stat boosts), Loot Boxes (with open action)
- [ ] Tapping "Open" on a loot box calls the open endpoint and shows the result
- [ ] Crafting screen shows available recipes with component costs and current inventory
- [ ] Craft button is disabled when insufficient components
- [ ] Successful crafting deducts components and adds new item to inventory
- [ ] Loot box count and inventory update in real-time after opening or crafting (TanStack Query invalidation)
- [ ] Empty states for each section when no items/components/loot boxes exist

#### Subtasks

- [ ] Create `game/components/inventory/ComponentList.tsx` displaying component types with quantities in a grouped list
- [ ] Create `game/components/inventory/ItemCard.tsx` with RarityBadge, item name, and stat boost summary
- [ ] Create `game/components/inventory/LootBoxCard.tsx` with loot box visual and "Open" button triggering `gameService.openLootBox()`
- [ ] Create `game/components/inventory/CraftingScreen.tsx` with recipe list, component cost display, and craft action calling `gameService.craftItem()`
- [ ] Implement `game/app/(tabs)/inventory.tsx` composing all inventory sections with `useInventory` hook, tab or accordion UI for sections
- [ ] Add TanStack Query cache invalidation on loot box open and craft success (invalidate `['inventory']`, `['creatures']`)
- [ ] Add empty states for each inventory section

#### Verification

**Level:** Single Judge
**Artifact:** `game/app/(tabs)/inventory.tsx`, `game/components/inventory/ComponentList.tsx`, `game/components/inventory/ItemCard.tsx`, `game/components/inventory/LootBoxCard.tsx`, `game/components/inventory/CraftingScreen.tsx`
**Threshold:** 4.0/5.0

**Rubric:**

| Criterion | Weight | Description |
|-----------|--------|-------------|
| Section Completeness | 0.25 | Three sections displayed: components by type with quantities, items by rarity with stat boosts, loot boxes with open action |
| Crafting Logic | 0.25 | Recipe display with component costs and current inventory; craft button disabled when insufficient components; successful craft updates inventory |
| Real-Time Updates | 0.20 | TanStack Query cache invalidation on loot box open and craft success (invalidates ['inventory'], ['creatures']) |
| Loot Box Opening | 0.15 | Tapping "Open" calls gameService.openLootBox() endpoint and shows result |
| Empty States | 0.15 | Empty states for each section when no items/components/loot boxes exist |

---

### Step 13: Creature Detail Screen & Loot Box Animation

**Model:** opus
**Agent:** sdd:developer
**Depends on:** Step 9
**Parallel with:** Step 10, Step 11, Step 12, Step 14, Step 15
**Note:** All 6 screen steps (10-15) MUST be launched in parallel by separate agents

**Goal**: Build the creature detail screen showing full stats, equipped items with equip/unequip, evolution progress, territory assignment, and the loot box opening animation with confetti.

#### Expected Output

- `game/app/creature/[id].tsx`: Creature Detail screen with stats, items, evolution, territory
- `game/components/creature/StatBar.tsx`: Power/Defense/Stamina bar visualization
- `game/components/creature/EvolutionProgress.tsx`: Progress bar toward next evolution threshold (10/25/50)
- `game/components/creature/ItemSlot.tsx`: Equipment slot (empty or filled, tap to equip/unequip)
- `game/components/inventory/LootBoxOpenAnimation.tsx`: Reanimated spring animation + confetti cannon for loot reveal

#### Success Criteria

- [ ] Creature detail shows all stats (power, defense, stamina) with visual bars
- [ ] Item slots display correctly by rarity: 1 slot (Common/Uncommon), 2 slots (Rare/Epic), 3 slots (Legendary)
- [ ] Tapping empty slot opens item selector; tapping filled slot offers unequip option
- [ ] Equipping an item updates creature stats in real-time
- [ ] Evolution progress bar shows XP toward next threshold with "Evolve" button at threshold
- [ ] Clicking "Evolve" triggers evolution and updates creature display
- [ ] Territory assignment section shows current territory or "Assign to Territory" CTA
- [ ] Loot box animation plays spring zoom-in with confetti burst, then reveals creature/item
- [ ] Animation completes within 5 seconds

#### Subtasks

- [ ] Create `game/components/creature/StatBar.tsx` with animated horizontal bar for each stat (power, defense, stamina)
- [ ] Create `game/components/creature/EvolutionProgress.tsx` with XP progress bar and evolution threshold markers at levels 10, 25, 50
- [ ] Create `game/components/creature/ItemSlot.tsx` with empty/filled states and tap action for equip/unequip
- [ ] Implement `game/app/creature/[id].tsx` composing all creature detail components with `useCreatureDetail` hook
- [ ] Add equip item flow: tap empty slot -> show available items -> select -> call `gameService.equipItem()` -> invalidate queries
- [ ] Add unequip item flow: tap filled slot -> confirm unequip -> call `gameService.unequipItem()` -> invalidate queries
- [ ] Add evolution flow: show "Evolve" button at threshold -> call `gameService.evolveCreature()` -> display updated creature
- [ ] Create `game/components/inventory/LootBoxOpenAnimation.tsx` using Reanimated v4 `withSpring` scale animation + `react-native-confetti-cannon` burst (following SKILL.md LootRevealModal pattern)
- [ ] Integrate LootBoxOpenAnimation into loot box opening flow (triggered from Inventory screen)

#### Verification

**Level:** Single Judge
**Artifact:** `game/app/creature/[id].tsx`, `game/components/creature/StatBar.tsx`, `game/components/creature/EvolutionProgress.tsx`, `game/components/creature/ItemSlot.tsx`, `game/components/inventory/LootBoxOpenAnimation.tsx`
**Threshold:** 4.0/5.0

**Rubric:**

| Criterion | Weight | Description |
|-----------|--------|-------------|
| Stat Display | 0.20 | Power, defense, stamina shown with visual bars; stats update in real-time on equip/unequip |
| Item Slot Logic | 0.25 | Correct slot count by rarity (Common/Uncommon: 1, Rare/Epic: 2, Legendary: 3); equip/unequip flows work with TanStack Query invalidation |
| Evolution Flow | 0.20 | Progress bar shows XP toward next threshold (10/25/50); Evolve button appears at threshold; evolution updates creature display |
| Animation Quality | 0.20 | Loot box animation uses Reanimated withSpring + react-native-confetti-cannon burst; completes within 5 seconds |
| Completeness | 0.15 | Territory assignment section present; all 4 components + screen + animation implemented as specified |

**Reference Pattern:** SKILL.md LootRevealModal pattern

---

### Step 14: Territory Detail & Event Detail Screens

**Model:** opus
**Agent:** sdd:developer
**Depends on:** Step 9
**Parallel with:** Step 10, Step 11, Step 12, Step 13, Step 15
**Note:** All 6 screen steps (10-15) MUST be launched in parallel by separate agents

**Goal**: Build territory detail screen with owner info, familiarity rankings, passive reward rates, claim/challenge/contribute actions, and event detail screen with quest steps, rewards, and check-in.

#### Expected Output

- `game/app/territory/[id].tsx`: Territory Detail screen with owner, familiarity, actions
- `game/app/event/[id].tsx`: Event Detail screen with quest steps, rewards, check-in
- `game/components/territory/FamiliarityRanking.tsx`: Sorted list of users by familiarity score
- `game/components/territory/PassiveRateDisplay.tsx`: Hourly reward rate display
- `game/components/territory/ChallengeButton.tsx`: PvP challenge CTA with creature selector modal
- `game/components/event/EventCard.tsx`: Event summary card with tier badge and countdown
- `game/components/event/QuestStepList.tsx`: Multi-step quest progress checklist
- `game/components/event/CheckInButton.tsx`: GPS-validated check-in action button

#### Success Criteria

- [ ] Territory detail shows zone type, owner, chief creature, familiarity rankings, and passive reward rate
- [ ] Unclaimed territory shows "Claim" button (disabled if no prior visit to area)
- [ ] PvP territory shows "Challenge" button with creature selector modal
- [ ] Cooperative territory shows "Contribute" button
- [ ] Challenge result displays winner, power breakdown (attacker vs defender including familiarity)
- [ ] Claim action assigns creature as chief and updates territory overlay to blue
- [ ] Event detail shows tier badge, time window, location, rewards, and quest steps (if monthly)
- [ ] Check-in button validates GPS proximity and records participation
- [ ] Quest progress updates after successful check-in
- [ ] Events screen tab shows list of active and upcoming events sorted by time

#### Subtasks

- [ ] Create `game/components/territory/FamiliarityRanking.tsx` showing top players by familiarity score for the territory
- [ ] Create `game/components/territory/PassiveRateDisplay.tsx` showing hourly XP and component generation rates
- [ ] Create `game/components/territory/ChallengeButton.tsx` with creature selection modal and challenge API call
- [ ] Implement `game/app/territory/[id].tsx` composing territory detail with `useTerritoryDetail` hook; conditional rendering of Claim/Challenge/Contribute based on zone type and ownership
- [ ] Add creature assignment flow for claiming: select creature -> call `territoryService.claimTerritory()` -> navigate back to map
- [ ] Add challenge flow: select creature -> call `territoryService.challengeTerritory()` -> display ChallengeResult with power breakdown
- [ ] Create `game/components/event/EventCard.tsx` with tier-specific styling (daily=blue, weekly=gold, monthly=purple) and countdown
- [ ] Create `game/components/event/QuestStepList.tsx` displaying multi-step quest progress with checkmarks
- [ ] Create `game/components/event/CheckInButton.tsx` with GPS validation before calling `eventService.checkIn()`
- [ ] Implement `game/app/event/[id].tsx` composing event detail with `useEventDetail` hook
- [ ] Implement `game/app/(tabs)/events.tsx` with active/upcoming event list using `useNearbyEvents` hook and EventCard components

#### Verification

**Level:** Per-Screen Judges (2 separate evaluations in parallel)
**Artifacts:** `game/app/territory/[id].tsx` (+ territory components), `game/app/event/[id].tsx` (+ event components + events tab)
**Threshold:** 4.0/5.0

**Rubric (per screen group):**

| Criterion | Weight | Description |
|-----------|--------|-------------|
| Conditional Actions | 0.25 | Correct action buttons per context: Claim (unclaimed territory), Challenge (PvP), Contribute (coop); Check-in (event within radius); disabled states when preconditions not met |
| Data Display | 0.25 | Territory: zone type, owner, chief creature, familiarity rankings, passive rate. Event: tier badge, time window, location, rewards, quest steps |
| Action Flows | 0.25 | Claim assigns creature as chief; Challenge shows power breakdown with familiarity; Check-in validates GPS proximity and records participation |
| Component Quality | 0.15 | FamiliarityRanking, PassiveRateDisplay, ChallengeButton, EventCard, QuestStepList, CheckInButton all render and function correctly |
| Navigation | 0.10 | Events tab shows active/upcoming list sorted by time; detail screens accessible from map taps and list taps |

---

### Step 15: Social Screens -- Friends, Trading & Leaderboards

**Model:** opus
**Agent:** sdd:developer
**Depends on:** Step 9
**Parallel with:** Step 10, Step 11, Step 12, Step 13, Step 14
**Note:** All 6 screen steps (10-15) MUST be launched in parallel by separate agents

**Goal**: Build all social feature screens: friends list with add/accept actions, trading interface with offer/request/confirm flow, activity feed of friend actions, and leaderboards with scope and metric selectors.

#### Expected Output

- `game/app/social/index.tsx`: Social hub with tabs for Friends, Trades, Activity, Leaderboards
- `game/app/social/friends.tsx`: Friends list with add friend (username/QR) and friend request management
- `game/app/social/trades.tsx`: Trade list with create trade, view pending, accept/decline
- `game/app/social/leaderboard.tsx`: Leaderboard with scope (local/global/friends) and metric (territory/power/exploration) selectors
- `game/components/social/FriendCard.tsx`: Friend card with game stats summary
- `game/components/social/TradeCard.tsx`: Trade offer card with offered/requested items display
- `game/components/social/LeaderboardRow.tsx`: Ranked leaderboard entry with highlighting for current player
- `game/components/social/ActivityFeedItem.tsx`: Social activity entry (territory claimed, creature evolved, etc.)

#### Success Criteria

- [ ] Friends list displays all accepted friends with territory count and creature count
- [ ] Add friend by username sends pending friend request
- [ ] Friend requests can be accepted or declined
- [ ] Tapping a friend navigates to view their profile (read-only: collection, territories, stats)
- [ ] Friends' territories appear green on the game map
- [ ] Trade creation allows selecting creatures/items to offer and request
- [ ] Trade proposal is sent to the selected friend
- [ ] Pending trades can be accepted or declined by the receiver
- [ ] 24-hour trade cooldown is displayed when active
- [ ] Activity feed shows recent friend actions in chronological order
- [ ] Leaderboard displays ranked players with scope/metric selectors
- [ ] Current player's position is highlighted in the leaderboard
- [ ] Leaderboard loads within 3 seconds
- [ ] No mechanism exists for real-money trading (only in-game items)

#### Subtasks

- [ ] Create `game/components/social/FriendCard.tsx` with friend name, level, territory count, creature count
- [ ] Create `game/components/social/TradeCard.tsx` with offered items, requested items, status badge, accept/decline buttons
- [ ] Create `game/components/social/LeaderboardRow.tsx` with rank, name, value, highlight for current user
- [ ] Create `game/components/social/ActivityFeedItem.tsx` with action icon, friend name, action description, timestamp
- [ ] Implement `game/app/social/friends.tsx` with friend list using `useFriends` hook, add friend input (username), pending requests section
- [ ] Implement `game/app/social/trades.tsx` with trade list using `useTrades` hook, create trade flow with item/creature selection
- [ ] Implement `game/app/social/leaderboard.tsx` with scope/metric selector and ranked list using `useLeaderboard` hook
- [ ] Implement `game/app/social/index.tsx` as social hub with navigation to friends, trades, leaderboard, and activity feed section
- [ ] Add empty states for friends ("Add friends to see them here"), trades ("No pending trades"), activity feed ("Your friends have been quiet")

#### Verification

**Level:** Per-Screen Judges (4 separate evaluations in parallel)
**Artifacts:** `game/app/social/{index,friends,trades,leaderboard}.tsx` (+ social components)
**Threshold:** 4.0/5.0

**Rubric (per social screen):**

| Criterion | Weight | Description |
|-----------|--------|-------------|
| Friends Management | 0.20 | Friends list with add/accept/decline; friend profile viewing (read-only: collection, territories, stats) |
| Trade Lifecycle | 0.25 | Create trade (select items/creatures to offer/request), pending display, accept/decline, 24h cooldown shown when active |
| Leaderboard | 0.20 | Scope selector (local/global/friends), metric selector (territory/power/exploration), current player highlighted, loads within 3s |
| Activity Feed | 0.15 | Chronological friend actions (territory claims, evolutions, event completions) displayed correctly |
| Empty States | 0.20 | Each social screen has appropriate empty state message when no data available |

---

### Step 16: Profile Screen, Onboarding & Polish

**Model:** opus
**Agent:** sdd:developer
**Depends on:** Step 10, Step 11, Step 12, Step 13, Step 14, Step 15
**Parallel with:** None

**Goal**: Build the player profile screen, implement first-time player onboarding experience (starter loot box), add comprehensive empty states and error handling to all screens, and ensure network loss is handled gracefully.

#### Expected Output

- `game/app/(tabs)/profile.tsx`: Profile screen with level, XP progress, collection stats, territory stats, achievements, social link
- First-time onboarding flow: Starter loot box on first login, guided opening, introduction to game map
- Empty states added to all screens that lack them
- Error handling for all documented scenarios (location denied, network loss, creature assignment conflict, slot full, no prior visit)

#### Success Criteria

- [ ] Profile screen displays player level, XP with progress bar, total creatures, total territories, achievements
- [ ] Tapping "Social" on profile navigates to the Social screen
- [ ] Game achievements display (first territory, first evolution, first PvP win, etc.)
- [ ] First-time player receives a starter loot box upon initial login
- [ ] Onboarding guides player to open starter loot box, view creature, and understand game map
- [ ] Location permission denied shows explanation with map still viewable but game actions disabled
- [ ] Network loss shows cached data with connectivity warning banner (NetworkBanner component)
- [ ] Creature already assigned to another territory prompts reassignment confirmation
- [ ] Equipping item when slots full shows "No available slots" message
- [ ] Claiming territory without prior visit shows "Visit this area first" message
- [ ] Trading during cooldown shows remaining cooldown time
- [ ] All screens have appropriate empty states for new players

#### Subtasks

- [ ] Implement `game/app/(tabs)/profile.tsx` with `useGameProfile` hook displaying level, XP progress bar, creature count, territory count, achievements list
- [ ] Add achievements display section (first territory claimed, first evolution, first PvP win, etc.)
- [ ] Add "Social" navigation button linking to `social/index`
- [ ] Implement first-time onboarding: detect new player (0 creatures, 0 territories), auto-grant starter loot box via backend, guide through opening and creature viewing
- [ ] Add location permission denied handling in Game Map: show explanation overlay, disable claim/challenge/check-in buttons, keep map viewable
- [ ] Add `NetworkBanner` component integration in root layout (detect connectivity via NetInfo, show/hide banner)
- [ ] Add creature reassignment confirmation dialog when assigning creature already chief of another territory
- [ ] Add "No available slots" error message in equip flow when creature slots are full
- [ ] Add "Visit this area first" message on territory claim attempt without prior visit
- [ ] Add cooldown time display in trade creation flow when 24h cooldown is active
- [ ] Review all screens and add EmptyState components where missing
- [ ] End-to-end test: complete game loop (login -> visit -> rewards -> loot box -> creature -> territory -> passive rewards -> leaderboard)

#### Verification

**Level:** Single Judge
**Artifact:** `game/app/(tabs)/profile.tsx`, onboarding flow, error handling additions across all screens
**Threshold:** 4.0/5.0

**Rubric:**

| Criterion | Weight | Description |
|-----------|--------|-------------|
| Profile Completeness | 0.20 | Level, XP progress bar, creature count, territory count, achievements displayed; social navigation link works |
| Onboarding Flow | 0.25 | New player detection (0 creatures, 0 territories), starter loot box auto-grant, guided opening, game map introduction |
| Error Handling | 0.30 | All documented scenarios covered: location denied (map viewable, actions disabled), network loss (cached data + banner), creature conflict (reassignment confirmation), full slots message, no prior visit message, trade cooldown display |
| Empty States | 0.15 | All screens reviewed and EmptyState components added where missing |
| Integration | 0.10 | NetworkBanner integrated in root layout; all error messages match acceptance criteria specification |

---

## Implementation Summary

| Step | Phase | Goal | Agent | Model | Depends on | Parallel with | Est. Effort |
|------|-------|------|-------|-------|------------|---------------|-------------|
| 1 | Backend DB | Create 12 ORM models + migration | sdd:developer | opus | None | Step 8 | M |
| 2 | Backend Schemas | Pydantic request/response schemas | sdd:developer | opus | Step 1 | None | M |
| 3 | Backend Services | Core game logic (rewards, loot, evolution, crafting) | sdd:developer | opus | Step 1, 2 | Step 4 | L |
| 4 | Backend Services | Territory + PvP + Events (PostGIS) | sdd:developer | opus | Step 1, 2 | Step 3 | L |
| 5 | Backend Services | Social + visit integration | sdd:developer | opus | Step 1, 2, 3 | None | M |
| 6 | Backend API | API routers + main.py + ARQ worker | sdd:developer | opus | Step 3, 4, 5 | None | M |
| 7 | Backend Tests | Integration tests for all endpoints | sdd:developer | opus | Step 6 | Step 9 | M |
| 8 | App Bootstrap | Expo project setup + dependencies | haiku | haiku | None | Step 1 | S |
| 9 | App Foundation | Auth, stores, services, hooks, nav, UI | sdd:developer | opus | Step 6, 8 | Step 7 | L |
| 10 | Core Screens | Game Map with territory overlays | sdd:developer | opus | Step 9 | Steps 11-15 | L |
| 11 | Core Screens | Creature Collection grid | sdd:developer | opus | Step 9 | Steps 10,12-15 | M |
| 12 | Core Screens | Inventory & Crafting | sdd:developer | opus | Step 9 | Steps 10-11,13-15 | M |
| 13 | Detail Screens | Creature Detail + Loot animation | sdd:developer | opus | Step 9 | Steps 10-12,14-15 | M |
| 14 | Detail Screens | Territory + Event detail | sdd:developer | opus | Step 9 | Steps 10-13,15 | L |
| 15 | Social & Profile | Social screens (friends, trading, leaderboards) | sdd:developer | opus | Step 9 | Steps 10-14 | M |
| 16 | Polish | Profile, onboarding, error handling | sdd:developer | opus | Steps 10-15 | None | M |

**Total Steps**: 16
**Total Subtasks**: ~150
**Max Parallelization Depth**: 6 steps simultaneously (Steps 10-15 after Step 9)
**Critical Path**: Steps 1 -> 2 -> 3 -> 5 -> 6 -> 9 -> any(10-15) -> 16
**Key Parallel Opportunities**:
- Steps 1 and 8 MUST start in parallel (no dependencies)
- Steps 3 and 4 MUST run in parallel (both depend only on Steps 1, 2)
- Steps 7 and 9 MUST run in parallel (both depend on Step 6; Step 9 also needs Step 8)
- Steps 10, 11, 12, 13, 14, 15 MUST all run in parallel (all depend only on Step 9)

---

## Verification Summary

| Step | Verification Level | Judges | Threshold | Artifacts |
|------|-------------------|--------|-----------|-----------|
| 1 | Panel (2) | 2 | 4.0/5.0 | DB migration + 5 ORM model files + __init__.py |
| 2 | Per-Item (4) | 4 | 4.0/5.0 | 4 Pydantic schema files (game, territory, event, social) |
| 3 | Panel (2) | 2 | 4.0/5.0 | game_service.py (core game logic) |
| 4 | Per-Item (2) | 2 | 4.0/5.0 | territory_service.py + event_service.py |
| 5 | Panel (2) | 2 | 4.0/5.0 | social_service.py + visit_service.py modification |
| 6 | Single | 1 | 4.0/5.0 | 4 API routers + main.py + ARQ worker |
| 7 | Per-Item (5) | 5 | 4.0/5.0 | conftest.py + 4 test files |
| 8 | None | - | - | Expo project scaffold |
| 9 | Panel (2) | 2 | 4.0/5.0 | ~40 foundation files (services, stores, hooks, types, auth, nav, UI) |
| 10 | Single | 1 | 4.0/5.0 | Game Map screen + 5 map components |
| 11 | Single | 1 | 4.0/5.0 | Creature Collection screen + 3 components |
| 12 | Single | 1 | 4.0/5.0 | Inventory screen + 4 components |
| 13 | Single | 1 | 4.0/5.0 | Creature Detail screen + 3 components + animation |
| 14 | Per-Item (2) | 2 | 4.0/5.0 | Territory Detail screen + Event Detail screen + components |
| 15 | Per-Item (4) | 4 | 4.0/5.0 | 4 social screens (hub, friends, trades, leaderboard) |
| 16 | Single | 1 | 4.0/5.0 | Profile screen + onboarding + error handling |

**Total Evaluations:** 31
**Implementation Command:** `/implement .specs/tasks/draft/implement-game-app.feature.md`

---

## Risks & Blockers Summary

### High Priority

| Risk/Blocker | Impact | Likelihood | Mitigation |
|--------------|--------|------------|------------|
| Circular import in visit_service -> game_service | High | High | Use lazy import inside `auto_confirm_visit()` function body (import inside function, not at module top) |
| PvP concurrent challenge race condition | High | Medium | `SELECT ... FOR UPDATE` on Territory row before challenge resolution in territory_service |
| Trade concurrent acceptance race condition | High | Medium | `SELECT FOR UPDATE` on Item/Creature rows before ownership transfer in social_service |
| react-native-maps Polygon performance with many territories | High | Medium | Memoize with useMemo, filter territories by viewport bounds, limit to 50 visible polygons |
| PostGIS territorial queries slow without indexes | High | Low | GIST index on `GameEvent.location` in migration; existing GIST index on `areas.boundary` |
| Loot box rarity manipulation | High | Low | All rarity rolls happen server-side in `open_loot_box()`, never expose RNG to client |
| Passive rewards ARQ task slow at scale | Medium | Low | Batch UPDATE SQL for territory rewards; add index on `Territory.owner_id` |
| Alembic migration FK ordering | Medium | Low | Create tables in dependency order (templates before creatures, creatures before territories) |

### Medium Priority

| Risk/Blocker | Impact | Likelihood | Mitigation |
|--------------|--------|------------|------------|
| FlashList v2 API differences from v1 | Medium | Low | Use `numColumns` prop (confirmed in SKILL.md); `estimatedItemSize` still accepted |
| Event quest_steps JSONB schema undefined | Medium | Medium | Define simple `{step_id, description, completed}` structure; can evolve later |
| Zone type busyness thresholds not specified | Medium | Medium | Define reasonable defaults in territory_service (low=personal, medium=coop, high=PvP); flag for tuning |
| Passive reward formula not quantified | Medium | Medium | Define `xp = busyness_score * creature_power * 0.1` as starting formula; tune post-launch |

---

## Definition of Done (Task Level)

- [ ] All 16 implementation steps completed
- [ ] All acceptance criteria from the task file verified
- [ ] Backend: All 12 game models created with migration
- [ ] Backend: All 4 service files implement full game logic
- [ ] Backend: All 4 API routers expose endpoints correctly
- [ ] Backend: ARQ game worker runs passive rewards and leaderboard refresh
- [ ] Backend: visit_service dispatches game rewards on visit confirmation
- [ ] Backend: All integration tests pass (`pytest`)
- [ ] Backend: Existing tests pass with no regressions
- [ ] Frontend: All 8 game screens + 4 social screens + 2 auth screens functional
- [ ] Frontend: 5-tab navigation works correctly
- [ ] Frontend: Complete game loop works end-to-end (visit -> rewards -> loot -> creature -> territory -> passive rewards)
- [ ] Frontend: All 3 territory zone types function correctly
- [ ] Frontend: All 3 event tiers display and grant correct rewards
- [ ] Frontend: Social features (friends, trading, leaderboards) operational
- [ ] Frontend: Empty states and error handling cover all documented scenarios
- [ ] Frontend: First-time player onboarding experience works
- [ ] No modifications to existing shared backend tables or endpoints
- [ ] Tests written and passing for all backend endpoints
- [ ] Documentation updated (API contracts documented in router docstrings)
