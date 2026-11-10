"""
Chennai Transit Place Index & Geocoding Module (Phase 2).
Provides fuzzy search and nearby stop lookup across stops, transit terminals,
metro interchanges, and key Chennai landmarks in English and Tamil.
"""

from typing import List, Dict, Any, Optional
import math
from backend.collectors.gtfs_loader import GTFSLoader

# Core Chennai landmarks with English and Tamil names, aliases, and accurate coordinates
CHENNAI_LANDMARKS = [
    {
        "id": "LM_001",
        "name_en": "Chennai Central Railway Station",
        "name_ta": "சென்னை சென்ட்ரல் ரயில் நிலையம்",
        "aliases": ["Central", "Puratchi Thalaivar Dr. M.G. Ramachandran Central", "சென்ட்ரல்", "Park Station"],
        "lat": 13.0827,
        "lon": 80.2755,
        "type": "terminal",
        "popularity": 100
    },
    {
        "id": "LM_002",
        "name_en": "Broadway Bus Terminus",
        "name_ta": "பிராட்வே பேருந்து நிலையம்",
        "aliases": ["Broadway", "Parrys", "High Court", "பாரிஸ்", "பிராட்வே"],
        "lat": 13.0878,
        "lon": 80.2871,
        "type": "terminal",
        "popularity": 95
    },
    {
        "id": "LM_003",
        "name_en": "CMBT Koyambedu",
        "name_ta": "கோயம்பேடு புறநகர் பேருந்து நிலையம்",
        "aliases": ["Koyambedu", "CMBT", "Rohini Silver Screens", "கோயம்பேடு"],
        "lat": 13.0680,
        "lon": 80.1980,
        "type": "terminal",
        "popularity": 98
    },
    {
        "id": "LM_004",
        "name_en": "T. Nagar Bus Terminus",
        "name_ta": "தி. நகர் பேருந்து நிலையம்",
        "aliases": ["T Nagar", "Panagal Park", "Pondy Bazaar", "தி நகர்"],
        "lat": 13.0400,
        "lon": 80.2340,
        "type": "terminal",
        "popularity": 96
    },
    {
        "id": "LM_005",
        "name_en": "Guindy Asiad / Industrial Estate",
        "name_ta": "கிண்டி பேருந்து நிலையம்",
        "aliases": ["Guindy", "Guindy Metro", "Kathipara", "கிண்டி"],
        "lat": 13.0067,
        "lon": 80.2025,
        "type": "interchange",
        "popularity": 92
    },
    {
        "id": "LM_006",
        "name_en": "Tambaram West Bus Stand",
        "name_ta": "தாம்பரம் பேருந்து நிலையம்",
        "aliases": ["Tambaram", "Tambaram Sanatorium", "தாம்பரம்", "MEPZ"],
        "lat": 12.9249,
        "lon": 80.1170,
        "type": "terminal",
        "popularity": 94
    },
    {
        "id": "LM_007",
        "name_en": "Chennai International Airport",
        "name_ta": "சென்னை விமான நிலையம்",
        "aliases": ["Airport", "Meenambakkam", "Trisulam", "விமான நிலையம்"],
        "lat": 12.9856,
        "lon": 80.1706,
        "type": "airport",
        "popularity": 90
    },
    {
        "id": "LM_008",
        "name_en": "Marina Beach / Vivekanandar Illam",
        "name_ta": "மெரினா கடற்கரை",
        "aliases": ["Marina", "Light House", "Kannagi Statue", "மெரினா பீச்"],
        "lat": 13.0500,
        "lon": 80.2824,
        "type": "landmark",
        "popularity": 88
    },
    {
        "id": "LM_009",
        "name_en": "Adyar Depot",
        "name_ta": "அடையார் பணிமனை",
        "aliases": ["Adyar", "Malar Hospital", "Lattice Bridge", "அடையார்"],
        "lat": 13.0060,
        "lon": 80.2550,
        "type": "terminal",
        "popularity": 87
    },
    {
        "id": "LM_010",
        "name_en": "Velachery Vijayanagar",
        "name_ta": "வேளச்சேரி விஜயநகர்",
        "aliases": ["Velachery", "Phoenix Mall", "வேளச்சேரி"],
        "lat": 12.9750,
        "lon": 80.2200,
        "type": "interchange",
        "popularity": 89
    },
    {
        "id": "LM_011",
        "name_en": "K.K. Nagar Depot",
        "name_ta": "கே.கே. நகர் பணிமனை",
        "aliases": ["KK Nagar", "Udhayam Theatre", "கேகே நகர்"],
        "lat": 13.0380,
        "lon": 80.1950,
        "type": "terminal",
        "popularity": 85
    },
    {
        "id": "LM_012",
        "name_en": "Anna Square",
        "name_ta": "அண்ணா சதுக்கம்",
        "aliases": ["Anna Square", "Chepauk", "Ezhilagam", "அண்ணா ஸ்கொயர்"],
        "lat": 13.0650,
        "lon": 80.2840,
        "type": "terminal",
        "popularity": 86
    },
    {
        "id": "LM_013",
        "name_en": "Thiruvanmiyur Bus Depot",
        "name_ta": "திருவான்மியூர் பணிமனை",
        "aliases": ["Thiruvanmiyur", "RTO Beach", "Tidel Park", "திருவான்மியூர்"],
        "lat": 12.9830,
        "lon": 80.2590,
        "type": "terminal",
        "popularity": 86
    },
    {
        "id": "LM_014",
        "name_en": "Siruseri IT Park / SIPCOT",
        "name_ta": "சிறுசேரி சிப்காட் தகவல் தொழில் நுட்ப பூங்கா",
        "aliases": ["Siruseri", "SIPCOT", "OMR IT Corridor", "சிறுசேரி"],
        "lat": 12.8280,
        "lon": 80.2180,
        "type": "landmark",
        "popularity": 82
    },
    {
        "id": "LM_015",
        "name_en": "DMS Teynampet",
        "name_ta": "டி.எம்.எஸ் தேனாம்பேட்டை",
        "aliases": ["DMS", "Teynampet", "Gemini", "தேனாம்பேட்டை"],
        "lat": 13.0450,
        "lon": 80.2480,
        "type": "interchange",
        "popularity": 88
    }
]

def haversine_distance_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371000.0  # Earth radius in meters
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2.0)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2.0)**2
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return r * c

class PlaceIndex:
    def __init__(self):
        self.loader = GTFSLoader()
        self.routes_df, self.stops_df, self.trips_df, self.stop_times_df = self.loader.load_or_generate()
        self.places = list(CHENNAI_LANDMARKS)

        # Merge unique stops into place index
        for _, s_row in self.stops_df.drop_duplicates(subset=["stop_id"]).iterrows():
            self.places.append({
                "id": str(s_row["stop_id"]),
                "name_en": str(s_row["stop_name"]),
                "name_ta": f"{s_row['stop_name']} பேருந்து நிறுத்தம்",
                "aliases": [str(s_row["stop_name"])],
                "lat": float(s_row["stop_lat"]),
                "lon": float(s_row["stop_lon"]),
                "type": "bus_stop",
                "popularity": 50
            })

    def search(self, query: str, lang: str = "en", limit: int = 6) -> List[Dict[str, Any]]:
        q = query.strip().lower()
        if not q:
            # Return top popular landmarks if query is empty
            return sorted(self.places[:12], key=lambda x: x["popularity"], reverse=True)[:limit]

        matches = []
        for p in self.places:
            score = 0
            name_en = p["name_en"].lower()
            name_ta = p["name_ta"].lower()
            
            # Exact or prefix match on names
            if q == name_en or q == name_ta:
                score += 100
            elif name_en.startswith(q) or name_ta.startswith(q):
                score += 70
            elif q in name_en or q in name_ta:
                score += 40
            
            # Alias match
            for alias in p["aliases"]:
                a_lower = alias.lower()
                if q == a_lower:
                    score += 80
                elif q in a_lower:
                    score += 35

            if score > 0:
                score += p["popularity"] * 0.2
                matches.append((score, p))

        matches.sort(key=lambda x: x[0], reverse=True)
        results = []
        for _, p in matches[:limit]:
            results.append({
                "id": p["id"],
                "name": p["name_ta"] if lang == "ta" else p["name_en"],
                "name_en": p["name_en"],
                "name_ta": p["name_ta"],
                "lat": p["lat"],
                "lon": p["lon"],
                "type": p["type"]
            })
        return results

    def find_nearby_stops(self, lat: float, lon: float, radius_m: float = 800.0, limit: int = 5) -> List[Dict[str, Any]]:
        nearby = []
        for p in self.places:
            if p["type"] in ["bus_stop", "terminal", "interchange"]:
                d = haversine_distance_m(lat, lon, p["lat"], p["lon"])
                if d <= radius_m:
                    nearby.append((d, p))
        nearby.sort(key=lambda x: x[0])
        results = []
        for d, p in nearby[:limit]:
            results.append({
                "id": p["id"],
                "name_en": p["name_en"],
                "name_ta": p["name_ta"],
                "lat": p["lat"],
                "lon": p["lon"],
                "distance_m": round(d, 0),
                "walk_minutes": max(1, round(d / 80.0, 1))  # ~80m per min walking speed
            })
        return results

