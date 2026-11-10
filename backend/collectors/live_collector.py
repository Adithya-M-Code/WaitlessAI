"""
MTC Live bus API collector.
Collects and archives raw live vehicle telemetry from Chennai MTC portal.
"""

import os
import json
import asyncio
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional, Iterable, Tuple
import httpx
import random

MTC_LIVE_URL = os.getenv(
    "MTC_LIVE_URL",
    "https://mobilegatewayapi.mtcbusits.in/passengermobileapi/WebAPI/SearchByRouteDetails_v4"
)

class LiveCollector:
    def __init__(self, raw_live_dir: str = "data/raw/live"):
        self.raw_dir = Path(raw_live_dir)
        self.raw_dir.mkdir(parents=True, exist_ok=True)
        self.last_fetch_time: Optional[datetime] = None
        self.failures = 0
        self._route_cursor = 0
        self._last_positions: Dict[str, Tuple[float, float, datetime]] = {}

    @staticmethod
    def bearing_degrees(previous_lat: float, previous_lon: float, lat: float, lon: float) -> Optional[float]:
        """Return a compass bearing, or None for a stationary/invalid fix."""
        try:
            phi1, phi2 = map(math.radians, (previous_lat, lat))
            delta_lon = math.radians(lon - previous_lon)
            y = math.sin(delta_lon) * math.cos(phi2)
            x = math.cos(phi1) * math.sin(phi2) - math.sin(phi1) * math.cos(phi2) * math.cos(delta_lon)
            if abs(x) < 1e-12 and abs(y) < 1e-12:
                return None
            return round((math.degrees(math.atan2(y, x)) + 360) % 360, 1)
        except (TypeError, ValueError):
            return None

    def enrich_vehicle(self, vehicle: Dict[str, Any]) -> Dict[str, Any]:
        """Add freshness and GPS-derived heading without fabricating coordinates."""
        result = dict(vehicle)
        vehicle_id = str(result.get("vehicle_no") or result.get("vehicleNo") or "")
        try:
            lat = float(result.get("lat", result.get("latitude")))
            lon = float(result.get("lon", result.get("longitude")))
        except (TypeError, ValueError):
            return result
        now = datetime.now(timezone.utc)
        previous = self._last_positions.get(vehicle_id)
        if previous:
            heading = self.bearing_degrees(previous[0], previous[1], lat, lon)
            if heading is not None:
                result["heading_deg"] = heading
        self._last_positions[vehicle_id] = (lat, lon, now)
        result["observed_at"] = now.isoformat()
        result["tier"] = "live"
        result["source"] = "mtc_live"
        return result

    @staticmethod
    def parse_vehicle_payload(data: Any) -> List[Dict[str, Any]]:
        """Tolerate known MTC envelope/key variations without inventing fields."""
        if isinstance(data, list):
            items = data
        elif isinstance(data, dict):
            items = data.get("vehicleDetails") or data.get("vehicles") or data.get("data") or []
        else:
            items = []
        if isinstance(items, dict):
            items = items.get("vehicleDetails") or items.get("vehicles") or []
        return [item for item in items if isinstance(item, dict)]

    async def fetch_route_vehicles(self, route_id: str) -> List[Dict[str, Any]]:
        """Fetches live vehicles for a given route and archives raw response."""
        payload = {"routeId": route_id}
        headers = {"User-Agent": "Waitless-AI-Collector/2.0", "Content-Type": "application/json"}
        
        if self.failures >= int(os.getenv("LIVE_CIRCUIT_BREAKER_THRESHOLD", "5")):
            return []
        for attempt in range(3):
            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    resp = await client.post(MTC_LIVE_URL, json=payload, headers=headers)
                self.last_fetch_time = datetime.now(timezone.utc)
                if resp.status_code == 200:
                    data = resp.json()
                    # Archive untouched raw JSON (Rule R1)
                    now_str = self.last_fetch_time.strftime("%Y%m%d_%H%M%S")
                    archive_path = self.raw_dir / f"mtc_live_{route_id}_{now_str}.json"
                    with open(archive_path, "w", encoding="utf-8") as f:
                        json.dump(data, f, ensure_ascii=False)
                    self.failures = 0
                    return [self.enrich_vehicle(vehicle) for vehicle in self.parse_vehicle_payload(data)]
                self.failures += 1
            except (httpx.HTTPError, ValueError, OSError):
                self.failures += 1
            if attempt < 2:
                await asyncio.sleep((2 ** attempt) + random.uniform(0.1, 0.5))
        return []

    async def poll_round_robin(self, route_ids: Iterable[str], max_routes: Optional[int] = None) -> List[Dict[str, Any]]:
        """Poll a bounded route slice; callers can schedule this method every interval."""
        routes = [str(route) for route in route_ids if str(route).strip()]
        if not routes:
            return []
        limit = max(1, max_routes or int(os.getenv("LIVE_ROUTES_PER_TICK", "1")))
        selected = [routes[(self._route_cursor + offset) % len(routes)] for offset in range(min(limit, len(routes)))]
        self._route_cursor = (self._route_cursor + len(selected)) % len(routes)
        results: List[Dict[str, Any]] = []
        for route_id in selected:
            results.extend(await self.fetch_route_vehicles(route_id))
            await asyncio.sleep(float(os.getenv("LIVE_ROUTE_JITTER_SECONDS", "0.2")) + random.uniform(0, 0.3))
        return results
