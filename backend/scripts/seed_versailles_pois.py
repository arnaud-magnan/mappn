#!/usr/bin/env python3
"""Seed ~100 notable POIs in Versailles Quartier Notre-Dame via Outscraper.

Usage:
    cd backend
    python scripts/seed_versailles_pois.py

Requires OUTSCRAPER_API_KEY environment variable (from .env or export).
"""

import asyncio
import os
import sys

# Ensure the backend package is importable
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from outscraper import ApiClient
from sqlalchemy import text

from app.db.session import engine as async_engine

OUTSCRAPER_API_KEY = os.environ.get("OUTSCRAPER_API_KEY", "")
TARGET_COUNT = 100

# Queries targeting notable/famous places, with per-query limits.
SEARCH_QUERIES = [
    ("restaurants Versailles centre-ville, France", 15),
    ("cafés Versailles Quartier Notre-Dame, France", 12),
    ("monuments historiques Versailles, France", 12),
    ("musées Versailles, France", 10),
    ("parcs jardins Versailles, France", 10),
    ("boutiques Versailles Rue de la Paroisse, France", 12),
    ("églises Versailles, France", 8),
    ("bars Versailles centre, France", 10),
    ("boulangeries pâtisseries Versailles centre, France", 11),
]

# Map Outscraper place types to our Place.category values.
TYPE_TO_CATEGORY = {
    "restaurant": "restaurant",
    "cafe": "cafe",
    "bar": "bar",
    "museum": "museum",
    "park": "park",
    "church": "church",
    "store": "shop",
    "clothing_store": "shop",
    "bakery": "restaurant",
    "tourist_attraction": "landmark",
    "point_of_interest": "landmark",
    "establishment": "general",
    "food": "restaurant",
    "night_club": "bar",
    "library": "library",
    "book_store": "shop",
    "gym": "gym",
    "art_gallery": "museum",
    "shopping_mall": "shop",
    "spa": "general",
    "lodging": "general",
}


def _extract_category(place: dict) -> str:
    """Extract our category from Outscraper place type string."""
    raw_type = place.get("type", "") or ""
    for part in raw_type.split(","):
        part = part.strip().lower()
        if part in TYPE_TO_CATEGORY:
            return TYPE_TO_CATEGORY[part]
    # Fallback: try subtypes
    for subtype in (place.get("subtypes") or "").split(","):
        subtype = subtype.strip().lower()
        if subtype in TYPE_TO_CATEGORY:
            return TYPE_TO_CATEGORY[subtype]
    return "general"


async def seed_pois() -> None:
    if not OUTSCRAPER_API_KEY:
        print("ERROR: Set OUTSCRAPER_API_KEY environment variable")
        sys.exit(1)

    client = ApiClient(api_key=OUTSCRAPER_API_KEY)
    all_places: dict[str, dict] = {}  # google_place_id -> place data

    for query, limit in SEARCH_QUERIES:
        if len(all_places) >= TARGET_COUNT:
            break
        print(f"  Searching: {query} (limit={limit})")
        try:
            results = client.google_maps_search([query], limit=limit, language="en")
        except Exception as e:
            print(f"  ERROR: {e}")
            continue

        if results and results[0]:
            for place in results[0]:
                place_id = place.get("place_id")
                if place_id and place_id not in all_places:
                    all_places[place_id] = place
        print(f"  Running total: {len(all_places)} unique places")

    # Trim to target
    places_list = list(all_places.items())[:TARGET_COUNT]
    print(f"\nInserting {len(places_list)} places into database...")

    async with async_engine.begin() as conn:
        inserted = 0
        skipped = 0
        for place_id, place in places_list:
            lat = place.get("latitude")
            lng = place.get("longitude")
            name = place.get("name", "Unknown")
            category = _extract_category(place)
            address = place.get("full_address")

            if not lat or not lng:
                skipped += 1
                continue

            try:
                result = await conn.execute(
                    text(
                        "INSERT INTO places "
                        "(google_place_id, name, category, coordinates, address, city, country) "
                        "VALUES (:pid, :name, :cat, ST_GeogFromText(:coords), :addr, 'Versailles', 'France') "
                        "ON CONFLICT (google_place_id) DO NOTHING "
                        "RETURNING id"
                    ),
                    {
                        "pid": place_id,
                        "name": name,
                        "cat": category,
                        "coords": f"SRID=4326;POINT({lng} {lat})",
                        "addr": address,
                    },
                )
                if result.scalar_one_or_none() is not None:
                    inserted += 1
            except Exception as e:
                print(f"  Error inserting {name}: {e}")
                skipped += 1

        print(f"Inserted: {inserted}, Skipped: {skipped}")

    # Report distribution across named territories
    print("\nPOI distribution across named territories:")
    async with async_engine.connect() as conn:
        result = await conn.execute(
            text(
                "SELECT a.name, a.zone_type, COUNT(p.id) AS poi_count "
                "FROM areas a "
                "LEFT JOIN places p "
                "  ON ST_Contains(a.boundary::geometry, p.coordinates::geometry) "
                "WHERE a.city = 'Versailles' "
                "  AND a.zone_type IN ('pvp', 'cooperative') "
                "GROUP BY a.name, a.zone_type "
                "ORDER BY poi_count DESC"
            )
        )
        for row in result:
            print(f"  {row[0]} ({row[1]}): {row[2]} POIs")

        # Total in personal hexes
        result = await conn.execute(
            text(
                "SELECT COUNT(DISTINCT p.id) "
                "FROM areas a "
                "JOIN places p "
                "  ON ST_Contains(a.boundary::geometry, p.coordinates::geometry) "
                "WHERE a.city = 'Versailles' AND a.zone_type = 'personal'"
            )
        )
        print(f"  Personal hexes (total): {result.scalar()} POIs")


if __name__ == "__main__":
    print("=== Versailles POI Seeder ===\n")
    asyncio.run(seed_pois())
