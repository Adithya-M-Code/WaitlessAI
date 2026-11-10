"""
Open-Meteo weather client for Chennai bus transit (Phase 2).
Provides live precipitation and rain flags without requiring an API key.
Caches responses for 10 minutes (Section 3.1).
"""

from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional
import httpx

# Chennai Central coordinates
CHENNAI_LAT = 13.0827
CHENNAI_LON = 80.2755

class OpenMeteoWeatherCollector:
    def __init__(self):
        self.cached_weather: Dict[str, Any] = {
            "rain_flag": 0,
            "rain_intensity_mm": 0.0,
            "temperature_c": 31.5,
            "weather_condition": "Clear / Partly Cloudy",
            "condition_ta": "தெளிவான வானிலை",
            "is_cached": False,
            "last_fetched_utc": None
        }
        self.last_fetch_time: Optional[datetime] = None

    async def get_live_weather(self) -> Dict[str, Any]:
        now = datetime.now(timezone.utc)
        # 10 minute cache check
        if self.last_fetch_time and (now - self.last_fetch_time) < timedelta(minutes=10):
            res = dict(self.cached_weather)
            res["is_cached"] = True
            return res

        url = (
            f"https://api.open-meteo.com/v1/forecast?"
            f"latitude={CHENNAI_LAT}&longitude={CHENNAI_LON}&current=temperature_2m,precipitation,rain,weather_code"
        )
        try:
            async with httpx.AsyncClient(timeout=4.0) as client:
                resp = await client.get(url)
                if resp.status_code == 200:
                    data = resp.json()
                    current = data.get("current", {})
                    rain_mm = float(current.get("rain", 0.0))
                    temp_c = float(current.get("temperature_2m", 31.0))
                    rain_flag = 1 if rain_mm > 0.1 else 0

                    if rain_mm > 5.0:
                        cond_en = "Heavy Monsoon Rain"
                        cond_ta = "கனமழை"
                    elif rain_mm > 0.5:
                        cond_en = "Moderate Rain / Drizzle"
                        cond_ta = "மிதமான மழை"
                    else:
                        cond_en = "Dry / Normal Road Conditions"
                        cond_ta = "வழக்கமான வானிலை"

                    self.cached_weather = {
                        "rain_flag": rain_flag,
                        "rain_intensity_mm": round(rain_mm, 1),
                        "temperature_c": round(temp_c, 1),
                        "weather_condition": cond_en,
                        "condition_ta": cond_ta,
                        "is_cached": False,
                        "last_fetched_utc": now.isoformat()
                    }
                    self.last_fetch_time = now
        except Exception:
            # Tolerant fallback to cached value
            pass

        return self.cached_weather

# Singleton instance
weather_collector = OpenMeteoWeatherCollector()
