from __future__ import annotations

import unittest
from pathlib import Path

from fastapi import HTTPException

from app.api.routes import recommend_cars
from app.core.config import Settings
from app.evaluation.provider_validation import provider_api_key, validate_provider
from app.evaluation.recommendation_eval import capped_model_recall, score_citations, shortlist_profile_ids
from app.models.schemas import RecommendRequest, RetrieveRequest
from app.recommendation import service as recommendation_service
from app.retrieval.service import infer_filters, score_profile, select_diverse_profiles
from app.valuation.service import compute_profile_valuation


class ValuationTests(unittest.TestCase):
    def test_compute_profile_valuation_returns_monotonic_range(self) -> None:
        valuation = compute_profile_valuation(
            {
                "brand": "Toyota",
                "body_type": "hatchback",
                "fuel_type": "petrol hybrid",
                "year_end": 2017,
                "maintenance_cost_band": "low",
                "fuel_consumption_l_per_100km": 4.1,
                "reliability_summary": "Strong reliability reputation",
                "suitability_summary": "Excellent for city commuting and low running costs",
                "title": "2015-2017 Toyota Aqua 1.5 Hybrid S",
                "trim": "S",
                "base_msrp_nzd": 27990,
            }
        )

        self.assertLessEqual(valuation["estimated_price_min_nzd"], valuation["estimated_price_mid_nzd"])
        self.assertLessEqual(valuation["estimated_price_mid_nzd"], valuation["estimated_price_max_nzd"])
        self.assertGreater(valuation["assumed_mileage_km"], 0)
        self.assertEqual(valuation["valuation_market"], "NZ")


class RetrievalParsingTests(unittest.TestCase):
    def test_infers_budget_body_fuel_and_usage_from_query(self) -> None:
        filters = infer_filters(
            RetrieveRequest(query="I need a hybrid hatchback under $20,000 for city commuting.", limit=6)
        )

        self.assertEqual(filters["budget_max"], 20000)
        self.assertEqual(filters["body_type"], "hatchback")
        self.assertEqual(filters["fuel_type"], "hybrid")
        self.assertEqual(filters["usage"], "city")

    def test_infers_compare_models_and_brand_preferences(self) -> None:
        filters = infer_filters(
            RetrieveRequest(query="Between Mazda3 and Honda Civic, which is the better first car?", limit=6)
        )

        self.assertIn("Mazda3", filters["models"])
        self.assertIn("Honda Civic", filters["models"])
        self.assertEqual(filters["usage"], "first_car")

    def test_select_diverse_profiles_prefers_model_coverage_before_duplicates(self) -> None:
        class Profile:
            def __init__(self, profile_id: str, brand: str, model: str) -> None:
                self.profile_id = profile_id
                self.brand = brand
                self.model = model

        profiles = [
            Profile("fit-1", "Honda", "Fit"),
            Profile("fit-2", "Honda", "Fit"),
            Profile("civic-1", "Honda", "Civic"),
            Profile("aqua-1", "Toyota", "Aqua"),
        ]

        selected = select_diverse_profiles(profiles, 3)

        self.assertEqual([profile.profile_id for profile in selected], ["fit-1", "civic-1", "aqua-1"])

    def test_score_profile_rewards_budget_and_running_cost_fit(self) -> None:
        class Profile:
            brand = "Toyota"
            model = "Aqua"
            estimated_price_mid_nzd = 14500
            estimated_price_min_nzd = 13000
            body_type = "hatchback"
            fuel_type = "petrol hybrid"
            transmission = "cvt"
            suitability_summary = "Excellent for city commuting and easy parking."
            comfort_summary = "Comfortable enough for daily use."
            space_summary = "Compact rear seat and boot."
            nvh_summary = "Quiet enough in town."
            maintenance_cost_band = "low"
            fuel_consumption_l_per_100km = 4.1
            reliability_summary = "Strong reliability reputation."

        score = score_profile(
            Profile(),
            {
                "budget_max": 20000,
                "brands": ["Toyota"],
                "models": ["Toyota Aqua"],
                "body_type": "hatchback",
                "fuel_type": "hybrid",
                "transmission": "cvt",
                "usage": "city",
                "priority": "low_running_cost",
                "limit": 6,
            },
        )

        self.assertGreaterEqual(score, 70)


class RecommendationEvalTests(unittest.TestCase):
    def test_shortlist_profile_ids_caps_selection_at_four(self) -> None:
        retrieval_response = {
            "vehicle_profiles": [
                {"profile_id": "car-1"},
                {"profile_id": "car-2"},
                {"profile_id": "car-3"},
                {"profile_id": "car-4"},
                {"profile_id": "car-5"},
            ]
        }

        self.assertEqual(shortlist_profile_ids(retrieval_response, 4), ["car-1", "car-2", "car-3", "car-4"])

    def test_capped_model_recall_is_limited_by_recommendation_cap(self) -> None:
        self.assertEqual(capped_model_recall(hit_count=3, expected_count=6, recommendation_limit=3), 1.0)
        self.assertEqual(capped_model_recall(hit_count=2, expected_count=3, recommendation_limit=3), 0.6667)

    def test_score_citations_accepts_profile_and_flag_evidence_ids(self) -> None:
        response = {
            "recommended_profiles": [
                {
                    "profile_id": "aqua-1",
                    "evidence_ids": ["profile:aqua-1", "chunk:k1"],
                    "risk_flags": [
                        {"label": "Hybrid system check", "evidence_ids": ["chunk:k1"]},
                    ],
                }
            ],
            "evidence": [
                {"id": "profile:aqua-1"},
                {"id": "chunk:k1"},
            ],
        }

        score, failures = score_citations(response)

        self.assertEqual(score, 1.0)
        self.assertEqual(failures, [])


class ProviderValidationTests(unittest.TestCase):
    def test_provider_validation_skips_missing_api_key(self) -> None:
        settings = self._settings()

        result = validate_provider(
            "openai",
            RecommendRequest(query="Recommend a city-friendly hybrid.", selected_profile_ids=["aqua-1", "fit-1"]),
            self._retrieval_response(),
            settings,
            include_missing=False,
        )

        self.assertEqual(result["provider"], "openai")
        self.assertEqual(result["status"], "skipped")
        self.assertEqual(result["reason"], "missing api key")

    def test_provider_api_key_supports_alias_environment_mapping(self) -> None:
        settings = self._settings(deepseek_api_key="shared-key", qwen_api_key="qwen-key", kimi_api_key="kimi-key")

        self.assertEqual(provider_api_key("deepseek", settings), "shared-key")
        self.assertEqual(provider_api_key("qwen", settings), "qwen-key")
        self.assertEqual(provider_api_key("kimi", settings), "kimi-key")

    @staticmethod
    def _settings(**overrides: object) -> Settings:
        values = {
            "database_url": "postgresql+psycopg://used_car:used_car@127.0.0.1:5432/used_car_copilot",
            "seed_data_dir": Path("data/seed"),
            "api_host": "0.0.0.0",
            "api_port": 8000,
            "embedding_provider": "local_hash",
            "embedding_model": "local-hash-embedding-v1",
            "recommendation_provider": "deterministic",
            "recommendation_model": "deterministic_variant_recommender_v1",
            "openai_api_key": None,
            "openai_base_url": "https://api.openai.com/v1",
            "openai_timeout_seconds": 30.0,
            "deepseek_api_key": None,
            "deepseek_base_url": "https://api.deepseek.com",
            "qwen_api_key": None,
            "qwen_base_url": "https://dashscope-intl.aliyuncs.com/compatible-mode/v1",
            "kimi_api_key": None,
            "kimi_base_url": "https://api.moonshot.ai/v1",
        }
        values.update(overrides)
        return Settings(**values)

    @staticmethod
    def _retrieval_response() -> dict[str, object]:
        return {
            "applied_filters": {"budget_max": 20000, "limit": 4, "selected_profile_ids": ["aqua-1", "fit-1"]},
            "vehicle_profiles": [],
            "chunks": [],
            "debug": {},
        }


class RecommendationRegressionTests(unittest.TestCase):
    def test_validate_recommend_request_requires_between_two_and_four_unique_ids(self) -> None:
        with self.assertRaisesRegex(recommendation_service.RecommendationRequestError, "at least 2"):
            recommendation_service.validate_recommend_request(
                RecommendRequest(query="Find me a city profile", selected_profile_ids=["car-1"])
            )

        with self.assertRaisesRegex(recommendation_service.RecommendationRequestError, "no more than 4"):
            recommendation_service.validate_recommend_request(
                RecommendRequest(query="Find me a city profile", selected_profile_ids=["1", "2", "3", "4", "5"])
            )

        with self.assertRaisesRegex(recommendation_service.RecommendationRequestError, "must be unique"):
            recommendation_service.validate_recommend_request(
                RecommendRequest(query="Find me a city profile", selected_profile_ids=["car-1", "car-1"])
            )

    def test_recommend_route_returns_400_for_invalid_selection_payload(self) -> None:
        with self.assertRaises(HTTPException) as caught:
            recommend_cars(RecommendRequest(query="Find me a city profile", selected_profile_ids=["car-1"]))

        self.assertEqual(caught.exception.status_code, 400)
        self.assertIn("select at least 2 profile ids", str(caught.exception.detail))

    def test_recommendation_generator_selects_deterministic_provider(self) -> None:
        generator = recommendation_service.get_recommendation_generator(
            "deterministic",
            "deterministic_variant_recommender_v1",
        )

        self.assertEqual(generator.name, "deterministic")
        self.assertEqual(generator.model, "deterministic_variant_recommender_v1")

    def test_recommendation_generator_rejects_unknown_provider(self) -> None:
        with self.assertRaises(ValueError):
            recommendation_service.get_recommendation_generator("unsupported")

    def test_openai_generator_falls_back_without_api_key(self) -> None:
        generator = recommendation_service.OpenAIRecommendationGenerator(api_key=None, model="gpt-5-mini")

        response = generator.generate(
            RecommendRequest(query="Recommend a city-friendly hybrid.", selected_profile_ids=["aqua-1", "fit-1"]),
            self._retrieval_response(),
        )

        self.assertEqual(response["_generation_metadata"]["source"], "deterministic_fallback")
        self.assertEqual(response["_generation_metadata"]["fallback_reason"], "missing_openai_api_key")
        self.assertEqual(response["recommended_profiles"][0]["profile_id"], "aqua-1")

    @staticmethod
    def _retrieval_response() -> dict[str, object]:
        return {
            "applied_filters": {"budget_max": 20000, "limit": 2, "selected_profile_ids": ["aqua-1", "fit-1"]},
            "vehicle_profiles": [
                DummyProfile("aqua-1", "2015-2017 Toyota Aqua 1.5 Hybrid S", "Toyota", "Aqua"),
                DummyProfile("fit-1", "2014-2016 Honda Fit 1.5 Petrol L", "Honda", "Fit"),
            ],
            "chunks": [
                {
                    "chunk_id": "k1",
                    "source_title": "Toyota Aqua notes",
                    "source_type": "maintenance",
                    "brand": "Toyota",
                    "model": "Aqua",
                    "profile_id": "aqua-1",
                    "text": "Hybrid battery condition and service history matter.",
                },
                {
                    "chunk_id": "k2",
                    "source_title": "Honda Fit notes",
                    "source_type": "buying_guide",
                    "brand": "Honda",
                    "model": "Fit",
                    "profile_id": "fit-1",
                    "text": "Fit is practical and easy to park.",
                },
            ],
            "debug": {},
        }


class DummyProfile:
    def __init__(self, profile_id: str, title: str, brand: str, model: str) -> None:
        self.profile_id = profile_id
        self.title = title
        self.brand = brand
        self.model = model
        self.engine_description = "1.5L profile"
        self.displacement_l = 1.5
        self.transmission = "cvt"
        self.fuel_type = "petrol hybrid" if brand == "Toyota" else "petrol"
        self.body_type = "hatchback"
        self.power_kw = 90
        self.suitability_summary = "Good for city commuting and easy parking."
        self.comfort_summary = "Comfortable enough for daily use."
        self.space_summary = "Compact rear seat and boot."
        self.nvh_summary = "Quiet enough in town."
        self.reliability_summary = "Strong reliability reputation."
        self.maintenance_cost_band = "low"
        self.fuel_consumption_l_per_100km = 4.3 if brand == "Toyota" else 5.6
        self.estimated_price_min_nzd = 13000 if brand == "Toyota" else 14000
        self.estimated_price_mid_nzd = 14500 if brand == "Toyota" else 15000
        self.estimated_price_max_nzd = 16000 if brand == "Toyota" else 16500
        self.year_start = 2015
        self.year_end = 2017
        self.common_issues = ["service history", "wear items"]


if __name__ == "__main__":
    unittest.main()
