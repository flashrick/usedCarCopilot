from __future__ import annotations

import sys
import unittest
from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy import delete

REPO_ROOT = Path(__file__).resolve().parents[3]
API_ROOT = Path(__file__).resolve().parents[1]

sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(API_ROOT))

from app.db.connection import engine, get_session
from app.db.orm import RecommendationHistoryRecord, UserRecord, UserSessionRecord, VehicleProfileRecord
from app.main import app


class AuthAndHistoryTests(unittest.TestCase):
    profile_one_id = "test-auth-history-profile-1"
    profile_two_id = "test-auth-history-profile-2"

    @classmethod
    def setUpClass(cls) -> None:
        migration_dir = API_ROOT / "migrations"
        with engine.begin() as connection:
            for migration_path in sorted(migration_dir.glob("*.sql")):
                connection.exec_driver_sql(migration_path.read_text(encoding="utf-8"))

    def setUp(self) -> None:
        self.client = TestClient(app)
        with get_session() as session:
            session.execute(delete(RecommendationHistoryRecord))
            session.execute(delete(UserSessionRecord))
            session.execute(delete(UserRecord))
            session.execute(
                delete(VehicleProfileRecord).where(
                    VehicleProfileRecord.profile_id.in_([self.profile_one_id, self.profile_two_id])
                )
            )
            session.add_all(
                [
                    self._vehicle_profile(
                        self.profile_one_id,
                        "2019-2021 Test Hybrid Hatch",
                        "TestAuto",
                        "Swift",
                        12990,
                        5.1,
                    ),
                    self._vehicle_profile(
                        self.profile_two_id,
                        "2020-2022 Test Family SUV",
                        "TestAuto",
                        "Trail",
                        17990,
                        6.4,
                    ),
                ]
            )

    def test_register_login_logout_and_auth_me(self) -> None:
        response = self.client.post(
            "/auth/register",
            json={"email": " Driver@Example.com ", "password": "secret123"},
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["user"]["email"], "driver@example.com")

        me_response = self.client.get("/auth/me")
        self.assertEqual(me_response.status_code, 200)
        self.assertEqual(me_response.json()["email"], "driver@example.com")

        logout_response = self.client.post("/auth/logout")
        self.assertEqual(logout_response.status_code, 200)
        self.assertTrue(logout_response.json()["ok"])

        self.assertEqual(self.client.get("/auth/me").status_code, 401)
        self.assertEqual(
            self.client.post("/auth/login", json={"email": "driver@example.com", "password": "wrong-pass"}).status_code,
            401,
        )

        login_response = self.client.post(
            "/auth/login",
            json={"email": "driver@example.com", "password": "secret123"},
        )
        self.assertEqual(login_response.status_code, 200)
        self.assertEqual(self.client.get("/auth/me").status_code, 200)

    def test_duplicate_register_and_unauthorized_paths(self) -> None:
        self.client.post("/auth/register", json={"email": "buyer@example.com", "password": "secret123"})
        duplicate_response = self.client.post(
            "/auth/register",
            json={"email": "buyer@example.com", "password": "secret123"},
        )
        self.assertEqual(duplicate_response.status_code, 409)

        anonymous_client = TestClient(app)
        self.assertEqual(anonymous_client.get("/me/history").status_code, 401)
        self.assertEqual(
            anonymous_client.post(
                "/me/recommendations",
                json={"query": "Need a commuter car", "selected_profile_ids": [self.profile_one_id, self.profile_two_id]},
            ).status_code,
            401,
        )

    def test_saved_recommendation_history_uses_persisted_snapshot(self) -> None:
        self.client.post("/auth/register", json={"email": "snapshot@example.com", "password": "secret123"})

        recommend_response = self.client.post(
            "/me/recommendations",
            json={
                "query": "I need a reliable daily commuter with low running costs.",
                "selected_profile_ids": [self.profile_one_id, self.profile_two_id],
            },
        )
        self.assertEqual(recommend_response.status_code, 200)
        payload = recommend_response.json()
        self.assertEqual(len(payload["recommended_profiles"]), 2)

        history_list = self.client.get("/me/history")
        self.assertEqual(history_list.status_code, 200)
        items = history_list.json()
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["selected_profile_ids"], [self.profile_one_id, self.profile_two_id])

        history_id = items[0]["id"]

        with get_session() as session:
            profile = session.get(VehicleProfileRecord, self.profile_one_id)
            assert profile is not None
            profile.title = "Mutated profile title"

        detail_response = self.client.get(f"/me/history/{history_id}")
        self.assertEqual(detail_response.status_code, 200)
        detail_payload = detail_response.json()
        self.assertEqual(
            detail_payload["recommend_response"]["recommended_profiles"][0]["title"],
            payload["recommended_profiles"][0]["title"],
        )

    def test_history_is_isolated_per_user(self) -> None:
        client_one = TestClient(app)
        client_two = TestClient(app)

        client_one.post("/auth/register", json={"email": "one@example.com", "password": "secret123"})
        response_one = client_one.post(
            "/me/recommendations",
            json={"query": "Need a hatchback", "selected_profile_ids": [self.profile_one_id, self.profile_two_id]},
        )
        self.assertEqual(response_one.status_code, 200)
        history_one = client_one.get("/me/history").json()
        history_one_id = history_one[0]["id"]

        client_two.post("/auth/register", json={"email": "two@example.com", "password": "secret123"})
        response_two = client_two.post(
            "/me/recommendations",
            json={"query": "Need a family car", "selected_profile_ids": [self.profile_one_id, self.profile_two_id]},
        )
        self.assertEqual(response_two.status_code, 200)
        history_two = client_two.get("/me/history").json()
        history_two_id = history_two[0]["id"]

        self.assertEqual(len(history_one), 1)
        self.assertEqual(len(history_two), 1)
        self.assertNotEqual(history_one_id, history_two_id)
        self.assertEqual(client_one.get(f"/me/history/{history_two_id}").status_code, 404)
        self.assertEqual(client_two.get(f"/me/history/{history_one_id}").status_code, 404)

    def _vehicle_profile(
        self,
        profile_id: str,
        title: str,
        brand: str,
        model: str,
        estimated_price_mid_nzd: int,
        fuel_consumption: float,
    ) -> VehicleProfileRecord:
        return VehicleProfileRecord(
            profile_id=profile_id,
            title=title,
            brand=brand,
            model=model,
            market="US",
            market_variant_id=f"{profile_id}-variant",
            year_start=2019,
            year_end=2022,
            trim="Base",
            engine_description="1.8L hybrid",
            transmission="cvt",
            fuel_type="hybrid",
            body_type="hatchback" if profile_id == self.profile_one_id else "suv",
            fuel_consumption_l_per_100km=fuel_consumption,
            suitability_summary="Good daily-driver fit.",
            comfort_summary="Comfortable enough for daily use.",
            reliability_summary="Strong reliability reputation.",
            maintenance_cost_band="low",
            estimated_price_min_nzd=estimated_price_mid_nzd - 1000,
            estimated_price_mid_nzd=estimated_price_mid_nzd,
            estimated_price_max_nzd=estimated_price_mid_nzd + 1000,
        )
