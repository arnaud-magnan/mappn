# Versailles Territories & POIs Design

**Date:** 2026-02-26
**Status:** Approved

## Overview

Seed the Mappn game with territories and points of interest in Versailles, Quartier Notre-Dame. This provides a real-world demo area with a mix of PvP, cooperative, and personal territories.

## Territory Layout

### 6 Named Territories

| Territory | Zone Type | Description |
|---|---|---|
| Château de Versailles & Jardins | PvP | The palace + formal gardens |
| Marché Notre-Dame | Cooperative | The market square + surrounding streets |
| Cathédrale Saint-Louis | Cooperative | Cathedral + Place Saint-Louis area |
| Place d'Armes | PvP | The grand avenue leading to the palace |
| Rue de la Paroisse | Cooperative | The main shopping street corridor |
| Parc Balbi / Pièce d'Eau des Suisses | PvP | The southern park/water feature |

Hand-drawn GeoJSON polygons, centered around 48.8049°N, 2.1204°E.

### Personal Hex Grid

- All remaining space within the neighborhood bounding box (~1.5km radius) is tessellated into hex tiles
- **Hex size:** 100m edge length (~200m point-to-point, roughly one city block)
- Hexes whose centroid falls inside a named territory are excluded
- Estimated 50-80 personal hexes
- Named auto-generated: "Hex-A1", "Hex-A2", etc.

## Data Model Changes

### User Model Additions

- `home_territory_id` (FK → territories, nullable) — the one personal hex claimed as home
- `home_claimed_at` (timestamp, nullable) — for relocation cooldown tracking

### Personal Hex Mechanics

- **One home per user** enforced by single FK on User model
- **Multiple residents per hex** — query `users WHERE home_territory_id = ?`
- **Co-ownership:** shared familiarity scores, shared passive rewards
- **Relocation:** update FK + reset `home_claimed_at`, 24h cooldown

### No Changes to Territory Model

Personal hexes are just territories with `zone_type = 'personal'`. The existing `owner_id` stays unused for personal zones.

## New API Endpoints

- `POST /game/territories/{id}/claim-home` — claim a personal hex as home (24h relocation cooldown)
- `GET /game/territories/{id}/residents` — list users living in a personal hex

## POI Strategy

- ~100 notable/famous real places sourced via existing Outscraper pipeline
- Search queries: restaurants, cafes, monuments, museums, parks, shops, churches, bars in Versailles Quartier Notre-Dame
- Target ~15-17 POIs per named territory
- POIs assigned to containing territory via PostGIS `ST_Contains`
- Underserved territories get targeted follow-up scrapes
- POIs in hex tiles are kept — they add value to personal zones

## Implementation Scope

### Migration 005: Versailles Territories

1. Add `home_territory_id` (FK) and `home_claimed_at` columns to `users` table
2. Insert 6 named Areas with hand-drawn GeoJSON polygons + zone_type
3. Insert 6 corresponding Territories (unclaimed, matching zone_type)
4. Generate hex grid via PostGIS `ST_HexagonGrid`, exclude overlaps, insert as Areas + Territories

### Backend Changes

- User model: add `home_territory_id` and `home_claimed_at` fields
- Territory service: add `claim_home()` (24h cooldown) and `get_residents()`
- Territory API: add claim-home and residents endpoints
- Territory schema: add `residents_count` to TerritoryResponse for personal zones

### POI Seed Script

- Standalone script using Outscraper to scrape ~100 places
- Assigns each POI to its containing territory
- Validates even distribution

### Frontend

- No structural changes — existing map renders territory polygons, detail screen handles zone-specific actions
- Personal hexes show "Claim as Home" button (new action for `zone_type = 'personal'`)

## Out of Scope

- Passive reward worker
- Relocation cost/currency
- Hex renaming/customization
- Leaderboard refresh
