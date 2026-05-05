from __future__ import annotations

import unittest
from pathlib import Path
from types import SimpleNamespace

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
from starlette.requests import Request


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
            transmission_maintenance_risk = "low"
            suitability_summary = "Excellent match for family SUV buyers who want efficiency and resale confidence."
            comfort_summary = "Family-friendly seating and easy daily usability."
            space_summary = "Strong rear-seat and cargo space for strollers and weekend trips."
            nvh_summary = "Quiet enough for family commuting."
            maintenance_cost_band = "low"
            safety_rating_stars = 5
            safety_rating_status = "rated"
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

    def test_score_profile_prefers_five_star_and_low_transmission_risk(self) -> None:
        class StrongProfile:
            brand = "Toyota"
            model = "Camry"
            estimated_price_mid_nzd = 26000
            estimated_price_min_nzd = 25000
            body_type = "sedan"
            fuel_type = "petrol hybrid"
            transmission = "cvt"
            transmission_maintenance_risk = "low"
            suitability_summary = "Strong commuter fit."
            comfort_summary = "Comfortable daily driver."
            space_summary = "Enough space for daily use."
            nvh_summary = "Quiet enough for commuting."
            maintenance_cost_band = "low"
            safety_rating_stars = 5
            safety_rating_status = "rated"
            fuel_consumption_l_per_100km = 5.0
            reliability_summary = "Strong reliability reputation."

        class RiskyProfile(StrongProfile):
            transmission_maintenance_risk = "high"
            safety_rating_stars = 3

        filters = {
            "market": "US",
            "budget_max": 30000,
            "brands": [],
            "models": [],
            "body_type": "sedan",
            "fuel_type": "hybrid",
            "transmission": "cvt",
            "usage": "commute",
            "priority": "reliability",
            "limit": 6,
            "query": "I want a safe and reliable commuter sedan with low maintenance risk.",
        }

        self.assertGreater(score_profile(StrongProfile(), filters), score_profile(RiskyProfile(), filters))

    def test_score_profile_does_not_penalize_unrated_cn_safety_data(self) -> None:
        class RatedProfile:
            brand = "Toyota"
            model = "Camry"
            estimated_price_mid_nzd = 200000
            estimated_price_min_nzd = 190000
            body_type = "sedan"
            fuel_type = "petrol hybrid"
            transmission = "cvt"
            transmission_maintenance_risk = "low"
            suitability_summary = "Strong fit for commuting."
            comfort_summary = "Comfort-oriented cabin."
            space_summary = "Good space."
            nvh_summary = "Quiet."
            maintenance_cost_band = "low"
            safety_rating_stars = 5
            safety_rating_status = "rated"
            fuel_consumption_l_per_100km = 4.8
            reliability_summary = "Strong reliability reputation."

        class UnratedProfile(RatedProfile):
            safety_rating_stars = None
            safety_rating_status = "unrated"

        filters = {
            "market": "CN",
            "brands": [],
            "models": [],
            "body_type": None,
            "fuel_type": None,
            "transmission": None,
            "usage": "commute",
            "priority": "low_running_cost",
            "limit": 6,
            "query": "我想找一台省心的通勤车。",
        }

        self.assertEqual(score_profile(RatedProfile(), filters) - score_profile(UnratedProfile(), filters), 8)


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
        http_request = Request(
            {
                "type": "http",
                "method": "POST",
                "path": "/recommend",
                "headers": [],
                "client": ("127.0.0.1", 50000),
                "scheme": "http",
                "server": ("testserver", 80),
                "query_string": b"",
            }
        )
        with self.assertRaises(Exception) as caught:
            recommend_cars(RecommendRequest(query="Find me a family SUV", selected_profile_ids=["car-1"]), http_request)

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

    def test_validate_llm_recommendation_payload_keeps_valid_overview(self) -> None:
        draft = self._recommendation_draft()
        generated = self._generated_payload(
            draft,
            {
                "recommended_profile_id": "rav4-1",
                "recommended_title": "2020-2022 Toyota RAV4 Hybrid XLE",
                "summary": (
                    "2020-2022 Toyota RAV4 Hybrid XLE is the best overall pick in this shortlist because it balances "
                    "daily running costs, family-friendly space, and a strong reliability story better than the alternatives."
                ),
                "evidence_ids": ["profile:rav4-1", "chunk:k1"],
            },
        )

        validated = recommendation_service.validate_llm_recommendation_payload(generated, draft)

        self.assertEqual(validated["recommendation_overview"]["recommended_profile_id"], "rav4-1")
        self.assertEqual(validated["recommendation_overview"]["evidence_ids"], ["profile:rav4-1", "chunk:k1"])
        self.assertEqual(validated["_overview_status"], "generated")
        self.assertIsNone(validated["_overview_drop_reason"])

    def test_validate_llm_recommendation_payload_falls_back_to_draft_overview(self) -> None:
        draft = self._recommendation_draft()
        invalid_overviews = [
            {
                "recommended_profile_id": "crv-1",
                "recommended_title": "2020-2022 Toyota RAV4 Hybrid XLE",
                "summary": "Still tries to recommend the wrong profile id.",
                "evidence_ids": ["profile:rav4-1"],
            },
            {
                "recommended_profile_id": "rav4-1",
                "recommended_title": "2020-2022 Honda CR-V EX",
                "summary": "Still tries to recommend the wrong title.",
                "evidence_ids": ["profile:rav4-1"],
            },
            {
                "recommended_profile_id": "rav4-1",
                "recommended_title": "2020-2022 Toyota RAV4 Hybrid XLE",
                "summary": "",
                "evidence_ids": ["profile:rav4-1"],
            },
            {
                "recommended_profile_id": "rav4-1",
                "recommended_title": "2020-2022 Toyota RAV4 Hybrid XLE",
                "summary": "This recommendation comes from web search and shortlist evidence.",
                "evidence_ids": ["profile:rav4-1"],
            },
            {
                "recommended_profile_id": "rav4-1",
                "recommended_title": "2020-2022 Toyota RAV4 Hybrid XLE",
                "summary": "The RAV4 stays ahead on efficiency, family space, and lower-drama ownership risk.",
                "evidence_ids": ["missing:evidence"],
            },
        ]

        for overview in invalid_overviews:
            with self.subTest(overview=overview):
                generated = self._generated_payload(draft, overview)
                validated = recommendation_service.validate_llm_recommendation_payload(generated, draft)
                self.assertEqual(
                    validated["recommendation_overview"]["recommended_profile_id"],
                    draft["_overview_draft"]["recommended_profile_id"],
                )
                self.assertEqual(validated["recommended_profiles"][0]["profile_id"], "rav4-1")
                self.assertEqual(validated["_overview_status"], "fallback_draft")
                self.assertIsNotNone(validated["_overview_drop_reason"])

    def test_validate_llm_recommendation_payload_falls_back_to_draft_when_overview_missing(self) -> None:
        draft = self._recommendation_draft()
        generated = self._generated_payload(draft, None)

        validated = recommendation_service.validate_llm_recommendation_payload(generated, draft)

        self.assertEqual(
            validated["recommendation_overview"]["recommended_profile_id"],
            draft["_overview_draft"]["recommended_profile_id"],
        )
        self.assertEqual(validated["_overview_status"], "fallback_draft")
        self.assertEqual(validated["_overview_drop_reason"], "missing_recommendation_overview")

    def test_deterministic_generator_returns_null_overview(self) -> None:
        generator = recommendation_service.DeterministicRecommendationGenerator()

        generated = generator.generate(
            RecommendRequest(query="Need a practical hybrid SUV.", selected_profile_ids=["rav4-1", "crv-1"]),
            self._sample_retrieval_response(),
        )

        self.assertIsNone(generated["recommendation_overview"])
        self.assertEqual(generated["_overview_draft"]["recommended_profile_id"], "rav4-1")
        self.assertEqual(generated["_overview_status"], "not_requested")
        self.assertIsNone(generated["_overview_drop_reason"])

    def test_deterministic_generator_surfaces_transmission_and_unrated_safety_risks(self) -> None:
        generator = recommendation_service.DeterministicRecommendationGenerator()
        retrieval = self._sample_retrieval_response()
        profile = SimpleNamespace(**vars(retrieval["vehicle_profiles"][0]))
        profile.profile_id = "dct-1"
        profile.title = "2019-2021 Demo Dry DCT Crossover"
        profile.transmission = "dct"
        profile.transmission_detail = "dry dct"
        profile.transmission_maintenance_risk = "high"
        profile.transmission_risk_note = "Dry dual-clutch gearboxes can become expensive if low-speed judder or missed servicing is ignored."
        profile.safety_rating_stars = None
        profile.safety_rating_status = "unrated"
        retrieval["vehicle_profiles"] = [profile]
        retrieval["chunks"] = []

        generated = generator.generate(
            RecommendRequest(query="Need a safe and low-risk used crossover.", selected_profile_ids=["dct-1", "crv-1"]),
            retrieval,
        )

        recommended = generated["recommended_profiles"][0]
        self.assertIn("Dry DCT", recommended["powertrain_summary"])
        self.assertTrue(any(flag["label"] == "Transmission repair risk" for flag in recommended["risk_flags"]))
        self.assertTrue(any(flag["label"] == "Safety data unavailable" for flag in recommended["risk_flags"]))
        self.assertTrue(any("cold-start road test" in step for step in recommended["next_steps"]))

    def test_openai_generator_missing_api_key_keeps_overview_null_and_marks_fallback(self) -> None:
        generator = recommendation_service.OpenAIRecommendationGenerator(api_key=None)

        generated = generator.generate(
            RecommendRequest(query="Need a practical hybrid SUV.", selected_profile_ids=["rav4-1", "crv-1"]),
            self._sample_retrieval_response(),
        )

        self.assertIsNone(generated["recommendation_overview"])
        self.assertEqual(generated["_generation_metadata"]["source"], "deterministic_fallback")
        self.assertEqual(generated["_generation_metadata"]["fallback_reason"], "missing_openai_api_key")
        self.assertEqual(generated["_generation_metadata"]["overview_status"], "provider_fallback")
        self.assertEqual(generated["_generation_metadata"]["overview_drop_reason"], "missing_openai_api_key")

    @staticmethod
    def _generated_payload(draft: dict[str, object], overview: dict[str, object] | None) -> dict[str, object]:
        generated_profiles = []
        for profile in draft["recommended_profiles"]:
            generated_profiles.append(
                {
                    "profile_id": profile["profile_id"],
                    "title": profile["title"],
                    "match_score": profile["match_score"],
                    "powertrain_summary": profile["powertrain_summary"],
                    "why_it_matches": list(profile["why_it_matches"]),
                    "trade_offs": list(profile["trade_offs"]),
                    "risk_flags": [dict(flag) for flag in profile["risk_flags"]],
                    "valuation_summary": profile["valuation_summary"],
                    "evidence_ids": list(profile["evidence_ids"]),
                    "next_steps": list(profile["next_steps"]),
                }
            )
        return {
            "query_summary": dict(draft["query_summary"]),
            "recommendation_overview": overview,
            "recommended_profiles": generated_profiles,
        }

    @staticmethod
    def _recommendation_draft() -> dict[str, object]:
        return {
            "query_summary": {"budget": "Under $30,000", "usage": "family", "preferences": ["hybrid", "low running cost"]},
            "recommendation_overview": None,
            "recommended_profiles": [
                {
                    "profile_id": "rav4-1",
                    "title": "2020-2022 Toyota RAV4 Hybrid XLE",
                    "match_score": 91,
                    "powertrain_summary": "2.5L · CVT · Petrol Hybrid · 160kW",
                    "why_it_matches": [
                        "Strong fit for a family buyer who wants fuel savings and easy resale confidence.",
                        "Estimated market midpoint stays inside the current budget target.",
                    ],
                    "trade_offs": [
                        "SUV practicality comes with higher tyre, brake, and fuel exposure than a small hatchback.",
                    ],
                    "risk_flags": [
                        {
                            "label": "Hybrid system check",
                            "severity": "medium",
                            "reason": "Battery health and hybrid maintenance history should be verified before purchase.",
                            "evidence_ids": ["chunk:k1"],
                        }
                    ],
                    "valuation_summary": "Estimated US fair range: $27,000-$31,000 (midpoint $29,000) for a good-condition used example.",
                    "evidence_ids": ["profile:rav4-1", "chunk:k1"],
                    "next_steps": ["Confirm service history before making an offer."],
                },
                {
                    "profile_id": "crv-1",
                    "title": "2020-2022 Honda CR-V EX",
                    "match_score": 84,
                    "powertrain_summary": "1.5L · CVT · Petrol · 140kW",
                    "why_it_matches": ["Comfort and daily usability still fit the intended family use."],
                    "trade_offs": ["Running costs will be higher than the most efficient shortlist options."],
                    "risk_flags": [
                        {
                            "label": "Routine used-car checks",
                            "severity": "low",
                            "reason": "Service history and body condition still matter.",
                            "evidence_ids": ["profile:crv-1"],
                        }
                    ],
                    "valuation_summary": "Estimated US fair range: $24,000-$28,000 (midpoint $26,000) for a good-condition used example.",
                    "evidence_ids": ["profile:crv-1"],
                    "next_steps": ["Use the valuation band as a negotiation anchor."],
                },
            ],
            "evidence": [
                {"id": "profile:rav4-1", "source_type": "vehicle_profile", "title": "2020-2022 Toyota RAV4 Hybrid XLE", "snippet": "Profile summary."},
                {"id": "chunk:k1", "source_type": "review", "title": "RAV4 ownership notes", "snippet": "Hybrid ownership note."},
                {"id": "profile:crv-1", "source_type": "vehicle_profile", "title": "2020-2022 Honda CR-V EX", "snippet": "Profile summary."},
            ],
            "_overview_draft": {
                "recommended_profile_id": "rav4-1",
                "recommended_title": "2020-2022 Toyota RAV4 Hybrid XLE",
                "summary": "2020-2022 Toyota RAV4 Hybrid XLE is the strongest overall match in this shortlist.",
                "evidence_ids": ["profile:rav4-1", "chunk:k1"],
            },
        }

    @staticmethod
    def _sample_retrieval_response() -> dict[str, object]:
        profile = SimpleNamespace(
            profile_id="rav4-1",
            title="2020-2022 Toyota RAV4 Hybrid XLE",
            brand="Toyota",
            model="RAV4",
            market="US",
            estimated_price_mid_nzd=29000,
            estimated_price_min_nzd=27000,
            estimated_price_max_nzd=31000,
            transmission="cvt",
            transmission_detail="e-cvt",
            transmission_maintenance_risk="low",
            transmission_risk_note="Toyota hybrid e-CVT hardware is usually low-drama when service history is present.",
            fuel_type="petrol hybrid",
            body_type="suv",
            power_kw=160,
            power_hp=None,
            displacement_l=2.5,
            engine_description="2.5L hybrid",
            fuel_consumption_l_per_100km=5.8,
            maintenance_cost_band="medium",
            suitability_summary="Strong fit for a family buyer who wants fuel savings and resale confidence.",
            comfort_summary="Comfort and usability align with family commuting.",
            space_summary="Rear-seat and cargo space work well for family use.",
            nvh_summary="Quiet enough for daily commuting.",
            reliability_summary="Strong reliability reputation.",
            safety_rating_stars=5,
            safety_rating_source="NHTSA 5-Star Safety Ratings",
            safety_rating_status="rated",
            valuation_market="US",
        )
        return {
            "applied_filters": {
                "market": "US",
                "budget_max": 30000,
                "usage": "family",
                "priority": "low_running_cost",
                "limit": 4,
                "selected_profile_ids": ["rav4-1", "crv-1"],
            },
            "vehicle_profiles": [profile],
            "chunks": [
                {
                    "chunk_id": "k1",
                    "profile_id": "rav4-1",
                    "brand": "Toyota",
                    "model": "RAV4",
                    "source_type": "review",
                    "source_title": "RAV4 ownership notes",
                    "text": "Owners praise the fuel economy but still recommend checking battery history.",
                }
            ],
            "debug": {},
        }
