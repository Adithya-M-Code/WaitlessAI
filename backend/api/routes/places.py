"""
Place search and nearby stop lookup endpoints (Phase 2).
"""

from typing import List, Optional
from fastapi import APIRouter, Query, HTTPException
from backend.analytics.places import PlaceIndex

router = APIRouter(prefix="/places", tags=["Places & Geocoding"])
place_index = PlaceIndex()

@router.get("/search")
def search_places(
    q: str = Query("", description="Search query string"),
    lang: str = Query("en", description="Language: en or ta"),
    limit: int = Query(6, ge=1, le=20)
):
    if lang not in {"en", "ta"}:
        raise HTTPException(status_code=422, detail="lang must be 'en' or 'ta'")
    return place_index.search(query=q, lang=lang, limit=limit)

@router.get("/nearby")
def get_nearby_stops(
    lat: float = Query(..., description="Latitude"),
    lon: float = Query(..., description="Longitude"),
    radius: float = Query(800.0, description="Radius in meters"),
    limit: int = Query(5, ge=1, le=15)
):
    if radius < 0 or radius > 50000:
        raise HTTPException(status_code=422, detail="radius must be between 0 and 50000 metres")
    return place_index.find_nearby_stops(lat=lat, lon=lon, radius_m=radius, limit=limit)
