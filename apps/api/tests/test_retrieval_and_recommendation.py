from __future__ import annotations

import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
API_ROOT = Path(__file__).resolve().parents[1]

import sys

sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(API_ROOT))

from app.api.routes import recommend_cars
from app.core.config import Settings
from app.evaluation.provider_validation import provider_api_key, validate_provider
from app.evaluation.recommendation_eval import capped_model_recall, score_citations
from app.models.schemas import RecommendRequest, RetrieveRequest
from app.recommendation import service as recommendation_service
from app.retrieval.service import (
    infer_filters,
    popularity_sort_key,
    popular_model_matches_filters,
    score_profile,
    select_diverse_profiles,
)
from app.valuation.service import compute_profile_valuation
from scripts.sync_market_catalog import build_diff, build_outputs, read_json


class ValuationTests(unittest.TestCase):
    def test_compute_profile_valuation_preserves_requested_market(self) -> None:
        valuation = compute_profile_valuation(
            {
                "brand": "BYD",
                "market": "CN",
                "body_type": "sedan",
                "fuel_type": "petrol hybrid",
                "year_end": 2025,
                "maintenance_cost_band": "medium",
                "fuel_consumption_l_per_100km": 4.2,
                "reliability_summary": "Strong value story",
                "suitability_summary": "Strong fit for commuting.",
                "title": "2022-2025 BYD Qin Plus DM-i 120KM",
                "trim": "DM-i 120KM",
                "base_msrp_nzd": 139800,
            }
        )

        self.assertLessEqual(valuation["estimated_price_min_nzd"], valuation["estimated_price_mid_nzd"])
        self.assertLessEqual(valuation["estimated_price_mid_nzd"], valuation["estimated_price_max_nzd"])
        self.assertEqual(valuation["valuation_market"], "CN")


class RetrievalParsingTests(unittest.TestCase):
    def test_infers_market_body_fuel_and_usage_from_english_query(self) -> None:
        filters = infer_filters(
            RetrieveRequest(query="I need a family SUV under $30,000 with hybrid efficiency.", market="US", limit=6)
        )

        self.assertEqual(filters["market"], "US")
        self.assertEqual(filters["budget_max"], 30000)
        self.assertEqual(filters["body_type"], "suv")
        self.assertEqual(filters["fuel_type"], "hybrid")
        self.assertEqual(filters["usage"], "family")

    def test_infers_market_body_priority_and_usage_from_chinese_query(self) -> None:
        filters = infer_filters(
            RetrieveRequest(query="我每天通勤，想要一台省钱、省心的轿车，最好油耗低。", market="CN", limit=6)
        )

        self.assertEqual(filters["market"], "CN")
        self.assertEqual(filters["body_type"], "sedan")
        self.assertEqual(filters["priority"], "low_running_cost")
        self.assertEqual(filters["usage"], "commute")

    def test_select_diverse_profiles_prefers_model_coverage_before_duplicates(self) -> None:
        class Profile:
            def __init__(self, profile_id: str, brand: str, model: str) -> None:
                self.profile_id = profile_id
                self.brand = brand
                self.model = model

        profiles = [
            Profile("camry-1", "Toyota", "Camry"),
            Profile("camry-2", "Toyota", "Camry"),
            Profile("crv-1", "Honda", "CR-V"),
            Profile("rav4-1", "Toyota", "RAV4"),
        ]

        selected = select_diverse_profiles(profiles, 3)

        self.assertEqual([profile.profile_id for profile in selected], ["camry-1", "crv-1", "rav4-1"])

    def test_popularity_sort_prefers_brand_rank_when_relevance_bucket_matches(self) -> None:
        self.assertLess(
            popularity_sort_key(41.0, 1, 3, "Toyota Camry"),
            popularity_sort_key(41.4, 2, 1, "BYD Song Plus"),
        )

    def test_popular_models_respect_suv_body_type_filter(self) -> None:
        class Variant:
            market_variant_id = "us-toyota-camry"
            brand = "Toyota"
            model = "Camry"
            body_types = ["sedan"]
            fuel_types = ["petrol", "petrol hybrid"]

        filters = infer_filters(
            RetrieveRequest(
                query="Find me a family SUV with a big boot, good safety reputation, and low maintenance risk.",
                market="US",
                limit=6,
            )
        )

        self.assertEqual(filters["body_type"], "suv")
        self.assertFalse(popular_model_matches_filters(Variant(), filters, {"us-toyota-camry"}))

    def test_popular_models_require_matching_profile_availability(self) -> None:
        class Variant:
            market_variant_id = "us-toyota-camry"
            brand = "Toyota"
            model = "Camry"
            body_types = ["sedan"]
            fuel_types = ["petrol", "petrol hybrid"]

        filters = {"market": "US", "brands": [], "models": [], "body_type": None, "fuel_type": None, "transmission": "manual"}

        self.assertFalse(popular_model_matches_filters(Variant(), filters, {"us-honda-civic"}))

    def test_score_profile_rewards_budget_and_family_fit(self) -> None:
        class Profile:
            brand = "Toyota"
            model = "RAV4"
            estimated_price_mid_nzd = 28000
            estimated_price_min_nzd = 26000
            body_type = "suv"
            fuel_type = "petrol hybrid"
            transmission = "cvt"
            suitability_summary = "Excellent match for family SUV buyers who want efficiency and resale confidence."
            comfort_summary = "Family-friendly seating and easy daily usability."
            space_summary = "Strong rear-seat and cargo space for strollers and weekend trips."
            nvh_summary = "Quiet enough for family commuting."
            maintenance_cost_band = "low"
            fuel_consumption_l_per_100km = 6.0
            reliability_summary = "Strong reliability reputation."

        score = score_profile(
            Profile(),
            {
                "market": "US",
                "budget_max": 30000,
                "brands": ["Toyota"],
                "models": ["Toyota RAV4"],
                "body_type": "suv",
                "fuel_type": "hybrid",
                "transmission": "cvt",
                "usage": "family",
                "priority": "reliability",
                "limit": 6,
            },
        )

        self.assertGreaterEqual(score, 70)


class CatalogScriptTests(unittest.TestCase):
    def test_build_outputs_generates_market_scoped_catalog(self) -> None:
        source = read_json(REPO_ROOT / "data" / "seed" / "market_catalog_seed.json")
        result = build_outputs(source, "US")

        self.assertGreaterEqual(len(result.canonical_models), 5)
        self.assertTrue(all(row["market"] == "US" for row in result.market_variants))
        self.assertTrue(all(row["market"] == "US" for row in result.vehicle_profiles))

    def test_diff_detects_new_market_variant_and_profile(self) -> None:
        previous = {
            "canonical_models": [{"canonical_model_id": "toyota-rav4"}],
            "market_variants": [{"market_variant_id": "us-toyota-rav4"}],
            "vehicle_profiles": [{"profile_id": "us-toyota-rav4-2020-2022-2.5-hybrid-xle"}],
            "knowledge_sources": [],
        }
        current = {
            "canonical_models": [{"canonical_model_id": "toyota-rav4"}, {"canonical_model_id": "honda-cr-v"}],
            "market_variants": [{"market_variant_id": "us-toyota-rav4"}, {"market_variant_id": "us-honda-crv"}],
            "vehicle_profiles": [
                {"profile_id": "us-toyota-rav4-2020-2022-2.5-hybrid-xle"},
                {"profile_id": "us-honda-crv-2020-2022-1.5-petrol-ex"},
            ],
            "knowledge_sources": [{"source_id": "us-honda-crv-space-001"}],
        }

        diff = build_diff(previous, current)

        self.assertEqual(diff["market_variants_added"][0]["market_variant_id"], "us-honda-crv")
        self.assertEqual(diff["vehicle_profiles_added"][0]["profile_id"], "us-honda-crv-2020-2022-1.5-petrol-ex")


class RecommendationEvalTests(unittest.TestCase):
    def test_capped_model_recall_is_limited_by_recommendation_cap(self) -> None:
        self.assertEqual(capped_model_recall(hit_count=3, expected_count=6, recommendation_limit=3), 1.0)
        self.assertEqual(capped_model_recall(hit_count=2, expected_count=3, recommendation_limit=3), 0.6667)

    def test_score_citations_accepts_profile_and_flag_evidence_ids(self) -> None:
        response = {
            "recommended_profiles": [
                {
                    "profile_id": "rav4-1",
                    "evidence_ids": ["profile:rav4-1", "chunk:k1"],
                    "risk_flags": [
                        {"label": "Hybrid system check", "evidence_ids": ["chunk:k1"]},
                    ],
                }
            ],
            "evidence": [
                {"id": "profile:rav4-1"},
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
            RecommendRequest(query="Recommend a family SUV.", selected_profile_ids=["rav4-1", "crv-1"]),
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
            "applied_filters": {"market": "US", "budget_max": 30000, "limit": 4, "selected_profile_ids": ["rav4-1", "crv-1"]},
            "vehicle_profiles": [],
            "chunks": [],
            "debug": {},
        }


class RecommendationRegressionTests(unittest.TestCase):
    def test_validate_recommend_request_requires_between_two_and_four_unique_ids(self) -> None:
        with self.assertRaisesRegex(recommendation_service.RecommendationRequestError, "at least 2"):
            recommendation_service.validate_recommend_request(
                RecommendRequest(query="Find me a family SUV", selected_profile_ids=["car-1"])
            )

        with self.assertRaisesRegex(recommendation_service.RecommendationRequestError, "no more than 4"):
            recommendation_service.validate_recommend_request(
                RecommendRequest(query="Find me a family SUV", selected_profile_ids=["1", "2", "3", "4", "5"])
            )

        with self.assertRaisesRegex(recommendation_service.RecommendationRequestError, "must be unique"):
            recommendation_service.validate_recommend_request(
                RecommendRequest(query="Find me a family SUV", selected_profile_ids=["car-1", "car-1"])
            )

    def test_recommend_route_returns_400_for_invalid_selection_payload(self) -> None:
        with self.assertRaises(Exception) as caught:
            recommend_cars(RecommendRequest(query="Find me a family SUV", selected_profile_ids=["car-1"]))

        self.assertIn("select at least 2 profile ids", str(caught.exception))

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
