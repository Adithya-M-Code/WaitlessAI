"""
Integration test suite for all Waitless AI v2 FastAPI endpoints.
"""

import unittest
from fastapi.testclient import TestClient
from backend.main import app

class TestAPIIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_health_endpoint(self):
        resp = self.client.get("/health")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["status"], "ok")
        self.assertEqual(data["version"], "2.0.0")
        self.assertIn("champion_delay", data)

    def test_routes_endpoint(self):
        resp = self.client.get("/routes")
        self.assertEqual(resp.status_code, 200)
        routes = resp.json()
        self.assertGreaterEqual(len(routes), 5)
        route_ids = [r["route_id"] for r in routes]
        self.assertIn("17D", route_ids)

    def test_route_stops_endpoint(self):
        resp = self.client.get("/routes/17D/stops")
        self.assertEqual(resp.status_code, 200)
        stops = resp.json()
        self.assertGreaterEqual(len(stops), 10)

    def test_vehicles_endpoint(self):
        resp = self.client.get("/vehicles?route_id=17D")
        self.assertEqual(resp.status_code, 200)
        vehicles = resp.json()
        self.assertGreaterEqual(len(vehicles), 1)

    def test_joint_prediction_endpoint(self):
        payload = {
            "route_id": "17D",
            "stop_id": "Central",
            "is_rain": False,
            "previous_delay": 3.5
        }
        resp = self.client.post("/predict/joint", json=payload)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["route_id"], "17D")
        self.assertEqual(data["status"], "ok")
        self.assertIn("minutes", data["delay"])
        self.assertIn("interval80", data["delay"])
        self.assertIn("probabilities", data["crowding"])

    def test_journey_ribbon_endpoint(self):
        resp = self.client.get("/journey/17D?stop_id=Central")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("stops_forecast", data)
        self.assertEqual(len(data["stops_forecast"]), 6)

    def test_recommender_endpoint(self):
        resp = self.client.get("/recommend?route_id=17D&mode=balanced")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("recommendations", data)
        self.assertGreaterEqual(len(data["recommendations"]), 1)

    def test_explain_endpoint(self):
        resp = self.client.get("/explain?route_id=17D&lang=ta")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("top_drivers", data)
        self.assertIn("narrative", data)

    def test_whatif_endpoint(self):
        payload = {"base_delay": 3.0, "hour": 8, "is_rain": True, "is_peak": True, "upstream_delay": 4.0}
        resp = self.client.post("/whatif", json=payload)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertGreater(data["simulated_delay_min"], data["original_delay_min"])

    def test_health_index_and_bunching(self):
        resp1 = self.client.get("/health-index/17D")
        self.assertEqual(resp1.status_code, 200)
        self.assertIn("health_index", resp1.json())

        resp2 = self.client.get("/alerts/bunching?route_id=17D")
        self.assertEqual(resp2.status_code, 200)

    def test_arena_endpoints(self):
        resp1 = self.client.get("/arena/leaderboard")
        self.assertEqual(resp1.status_code, 200)
        self.assertIn("models", resp1.json())

        resp2 = self.client.get("/arena/scorecard")
        self.assertEqual(resp2.status_code, 200)

        resp3 = self.client.get("/models/registry")
        self.assertEqual(resp3.status_code, 200)
        self.assertIn("champion", resp3.json()["delay"])

    def test_admin_reload_security(self):
        # Missing or invalid token should fail
        resp_bad = self.client.post("/admin/reload", headers={"admin-token": "wrong"})
        self.assertEqual(resp_bad.status_code, 403)

        # Valid token should succeed
        resp_good = self.client.post("/admin/reload", headers={"admin-token": "change-me"})
        self.assertEqual(resp_good.status_code, 200)

if __name__ == "__main__":
    unittest.main()

