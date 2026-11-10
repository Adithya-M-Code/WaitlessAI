"""
Unit and integration tests for Phase 2 API endpoints:
- /places/search & /places/nearby
- /plan & /plan/predict
- /routes/{id}/shape
- /recommend/v2
- /leave-time
- /whatif/v2
- /weather/live
"""

import unittest
from fastapi.testclient import TestClient
from backend.main import app

class TestPhase2Endpoints(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_place_search_english_and_tamil(self):
        # English query
        res1 = self.client.get("/places/search?q=Central&lang=en")
        self.assertEqual(res1.status_code, 200)
        places1 = res1.json()
        self.assertGreater(len(places1), 0)
        self.assertIn("Chennai Central", places1[0]["name"])

        # Tamil query
        res2 = self.client.get("/places/search?q=சென்ட்ரல்&lang=ta")
        self.assertEqual(res2.status_code, 200)
        places2 = res2.json()
        self.assertGreater(len(places2), 0)

    def test_places_nearby(self):
        # Chennai Central coords
        res = self.client.get("/places/nearby?lat=13.0827&lon=80.2755&radius=1000")
        self.assertEqual(res.status_code, 200)
        stops = res.json()
        self.assertGreater(len(stops), 0)

    def test_journey_planner_and_button_gated_predict(self):
        # 1. Unpredicted plan
        plan_payload = {
            "from": {"name": "Chennai Central", "lat": 13.0827, "lon": 80.2755},
            "to": {"name": "Airport", "lat": 12.9856, "lon": 80.1706}
        }
        res_plan = self.client.post("/plan", json=plan_payload)
        self.assertEqual(res_plan.status_code, 200)
        data = res_plan.json()
        self.assertIn("options", data)
        self.assertGreater(len(data["options"]), 0)

        # 2. Button-gated prediction for an option
        first_option = data["options"][0]
        res_pred = self.client.post("/plan/predict", json={"option": first_option})
        self.assertEqual(res_pred.status_code, 200)
        pred_data = res_pred.json()
        self.assertIn("itinerary_prediction", pred_data)
        self.assertIn("predicted_total_minutes", pred_data["itinerary_prediction"])

    def test_route_shape_and_tier(self):
        res = self.client.get("/routes/17D/shape")
        self.assertEqual(res.status_code, 200)
        shape = res.json()
        self.assertEqual(shape["route_id"], "17D")
        self.assertEqual(shape["tier"], "live")
        self.assertGreater(len(shape["polyline"]), 5)

    def test_best_bus_v2_slider(self):
        res = self.client.post("/recommend/v2", json={"route_id": "17D", "stop_id": "Central", "preference": 0.8})
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("candidates", data)

    def test_leave_time_optimizer(self):
        res = self.client.post("/leave-time", json={"route_id": "17D", "stop_id": "Central"})
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("recommended_window", data)

    def test_whatif_v2_simulation(self):
        res = self.client.post("/whatif/v2", json={"hour": 8, "day_type": "weekday", "rain_intensity_mm": 5.0, "upstream_delay_min": 4.0})
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertGreater(data["scenario"]["delay_min"], data["baseline"]["delay_min"])

    def test_live_weather(self):
        res = self.client.get("/weather/live")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("temperature_c", data)

if __name__ == "__main__":
    unittest.main()

