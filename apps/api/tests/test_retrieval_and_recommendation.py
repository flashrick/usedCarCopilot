from __future__ import annotations

import json
import unittest
from contextlib import contextmanager

from app.embedding.service import get_embedding_provider
from app.models.schemas import RecommendRequest, RetrieveRequest
from app.recommendation import service as recommendation_service
from app.retrieval.service import infer_filters, select_diverse_listings


class RetrievalParsingTests(unittest.TestCase):
    def test_embedding_provider_selects_local_hash_provider(self) -> None:
        provider = get_embedding_provider("local_hash", "local-hash-embedding-v1")

        self.assertEqual(provider.model, "local-hash-embedding-v1")
        self.assertEqual(len(provider.embed("Toyota Aqua city hybrid")), provider.dimensions)

    def test_embedding_provider_rejects_unknown_provider(self) -> None:
        with self.assertRaises(ValueError):
            get_embedding_provider("unsupported")

    def test_infers_excluded_body_type_and_supported_brands(self) -> None:
        filters = infer_filters(
            RetrieveRequest(
                query=(
                    "I want a used car under $10,000 and I do not want an SUV. "
                    "What are the safer choices from Toyota, Honda, and Mazda?"
                )
            )
        )

        self.assertEqual(filters["max_price"], 10000)
        self.assertEqual(filters["exclude_body_type"], "suv")
        self.assertEqual(filters["brands"], ["Toyota", "Honda", "Mazda"])
        self.assertEqual(filters["priority"], "safer_choice")

    def test_infers_scope_for_these_brands_novice_query(self) -> None:
        filters = infer_filters(
            RetrieveRequest(
                query=(
                    "I do not know much about cars. Give me the simplest "
                    "low-risk used car choice for Auckland from these brands."
                )
            )
        )

        self.assertEqual(filters["brands"], ["Toyota", "Honda", "Mazda"])
        self.assertEqual(filters["priority"], "low_risk")
        self.assertEqual(filters["user_profile"], "novice_buyer")

    def test_select_diverse_listings_prefers_model_coverage_before_duplicates(self) -> None:
        class Listing:
            def __init__(self, listing_id: str, brand: str, model: str) -> None:
                self.listing_id = listing_id
                self.brand = brand
                self.model = model

        listings = [
            Listing("fit-1", "Honda", "Fit"),
            Listing("fit-2", "Honda", "Fit"),
            Listing("civic-1", "Honda", "Civic"),
            Listing("aqua-1", "Toyota", "Aqua"),
        ]

        selected = select_diverse_listings(listings, 3)

        self.assertEqual([listing.listing_id for listing in selected], ["fit-1", "civic-1", "aqua-1"])


class RecommendationRegressionTests(unittest.TestCase):
    def test_recommendation_generator_selects_deterministic_provider(self) -> None:
        generator = recommendation_service.get_recommendation_generator(
            "deterministic",
            "deterministic_ranker_with_citations",
        )

        self.assertEqual(generator.name, "deterministic")
        self.assertEqual(generator.model, "deterministic_ranker_with_citations")

    def test_recommendation_generator_rejects_unknown_provider(self) -> None:
        with self.assertRaises(ValueError):
            recommendation_service.get_recommendation_generator("unsupported")

    def test_recommendation_generator_selects_openai_provider(self) -> None:
        generator = recommendation_service.get_recommendation_generator(
            "openai",
            "gpt-5-mini",
            openai_api_key="test-key",
        )

        self.assertEqual(generator.name, "openai")
        self.assertEqual(generator.model, "gpt-5-mini")

    def test_recommendation_generator_selects_openai_compatible_providers(self) -> None:
        cases = [
            ("deepseek", "deepseek-chat"),
            ("qwen", "qwen-plus"),
            ("kimi", "kimi-k2.6"),
        ]
        for provider, expected_model in cases:
            with self.subTest(provider=provider):
                generator = recommendation_service.get_recommendation_generator(
                    provider,
                    "deterministic_ranker_with_citations",
                    deepseek_api_key="test-key",
                    qwen_api_key="test-key",
                    kimi_api_key="test-key",
                )

                self.assertEqual(generator.name, provider)
                self.assertEqual(generator.model, expected_model)

    def test_openai_generator_falls_back_without_api_key(self) -> None:
        generator = recommendation_service.OpenAIRecommendationGenerator(api_key=None, model="gpt-5-mini")

        response = generator.generate(
            RecommendRequest(query="I need a reliable car under $12,000 for commuting in Auckland."),
            self._retrieval_response(),
        )

        self.assertEqual(response["_generation_metadata"]["source"], "deterministic_fallback")
        self.assertEqual(response["_generation_metadata"]["fallback_reason"], "missing_openai_api_key")
        self.assertEqual(response["recommended_cars"][0]["listing_id"], "akl-toyota-aqua-test")

    def test_openai_generator_accepts_valid_structured_response(self) -> None:
        class StubOpenAIGenerator(recommendation_service.OpenAIRecommendationGenerator):
            def _post_response(self, payload: dict[str, object]) -> dict[str, object]:
                prompt_payload = json.loads(payload["input"][1]["content"][0]["text"])
                draft = prompt_payload["draft_recommendation"]
                car = draft["recommended_cars"][0]
                generated = {
                    "query_summary": draft["query_summary"],
                    "recommended_cars": [
                        {
                            **car,
                            "why_it_matches": ["LLM-grounded reason that keeps the same listing and citations."],
                        }
                    ],
                }
                return {"output": [{"content": [{"type": "output_text", "text": json.dumps(generated)}]}]}

        generator = StubOpenAIGenerator(api_key="test-key", model="gpt-5-mini")

        response = generator.generate(
            RecommendRequest(query="I need a reliable car under $12,000 for commuting in Auckland."),
            self._retrieval_response(),
        )

        self.assertEqual(response["_generation_metadata"]["source"], "openai")
        self.assertEqual(
            response["recommended_cars"][0]["why_it_matches"],
            ["LLM-grounded reason that keeps the same listing and citations."],
        )

    def test_openai_generator_falls_back_on_invalid_citation(self) -> None:
        class BadCitationGenerator(recommendation_service.OpenAIRecommendationGenerator):
            def _post_response(self, payload: dict[str, object]) -> dict[str, object]:
                prompt_payload = json.loads(payload["input"][1]["content"][0]["text"])
                draft = prompt_payload["draft_recommendation"]
                car = dict(draft["recommended_cars"][0])
                car["evidence_ids"] = ["chunk:missing"]
                generated = {"query_summary": draft["query_summary"], "recommended_cars": [car]}
                return {"output": [{"content": [{"type": "output_text", "text": json.dumps(generated)}]}]}

        generator = BadCitationGenerator(api_key="test-key", model="gpt-5-mini")

        response = generator.generate(
            RecommendRequest(query="I need a reliable car under $12,000 for commuting in Auckland."),
            self._retrieval_response(),
        )

        self.assertEqual(response["_generation_metadata"]["source"], "deterministic_fallback")
        self.assertIn("invalid evidence ids", response["_generation_metadata"]["fallback_reason"])

    def test_compatible_chat_generator_falls_back_without_api_key(self) -> None:
        generator = recommendation_service.OpenAICompatibleChatRecommendationGenerator(
            name="deepseek",
            api_key=None,
            model="deepseek-chat",
            base_url="https://api.deepseek.com",
        )

        response = generator.generate(
            RecommendRequest(query="I need a reliable car under $12,000 for commuting in Auckland."),
            self._retrieval_response(),
        )

        self.assertEqual(response["_generation_metadata"]["source"], "deterministic_fallback")
        self.assertEqual(response["_generation_metadata"]["fallback_reason"], "missing_deepseek_api_key")

    def test_compatible_chat_generator_accepts_valid_json_response(self) -> None:
        class StubChatGenerator(recommendation_service.OpenAICompatibleChatRecommendationGenerator):
            def _post_chat_completion(self, payload: dict[str, object]) -> dict[str, object]:
                prompt_payload = json.loads(payload["messages"][1]["content"])
                draft = prompt_payload["draft_recommendation"]
                car = draft["recommended_cars"][0]
                generated = {
                    "query_summary": draft["query_summary"],
                    "recommended_cars": [
                        {
                            **car,
                            "next_steps": ["Ask for service records, then book an inspection."],
                        }
                    ],
                }
                return {"choices": [{"message": {"content": json.dumps(generated)}}]}

        generator = StubChatGenerator(
            name="qwen",
            api_key="test-key",
            model="qwen-plus",
            base_url="https://dashscope-intl.aliyuncs.com/compatible-mode/v1",
        )

        response = generator.generate(
            RecommendRequest(query="I need a reliable car under $12,000 for commuting in Auckland."),
            self._retrieval_response(),
        )

        self.assertEqual(response["_generation_metadata"]["source"], "qwen")
        self.assertEqual(response["recommended_cars"][0]["next_steps"], ["Ask for service records, then book an inspection."])

    def test_compatible_chat_generator_falls_back_on_invalid_json(self) -> None:
        class BadJsonChatGenerator(recommendation_service.OpenAICompatibleChatRecommendationGenerator):
            def _post_chat_completion(self, payload: dict[str, object]) -> dict[str, object]:
                return {"choices": [{"message": {"content": "not json"}}]}

        generator = BadJsonChatGenerator(
            name="kimi",
            api_key="test-key",
            model="kimi-k2.6",
            base_url="https://api.moonshot.ai/v1",
        )

        response = generator.generate(
            RecommendRequest(query="I need a reliable car under $12,000 for commuting in Auckland."),
            self._retrieval_response(),
        )

        self.assertEqual(response["_generation_metadata"]["source"], "deterministic_fallback")
        self.assertIn("JSONDecodeError", response["_generation_metadata"]["fallback_reason"])

    def test_select_diverse_recommendations_prefers_distinct_models(self) -> None:
        ranked = [
            {"listing_id": "fit-1", "_model_key": "honda:fit"},
            {"listing_id": "fit-2", "_model_key": "honda:fit"},
            {"listing_id": "civic-1", "_model_key": "honda:civic"},
            {"listing_id": "aqua-1", "_model_key": "toyota:aqua"},
        ]

        selected = recommendation_service.select_diverse_recommendations(ranked, 3)

        self.assertEqual([car["listing_id"] for car in selected], ["fit-1", "civic-1", "aqua-1"])

    def test_recommendation_evidence_includes_risk_flag_chunk_citations(self) -> None:
        retrieval_response = self._retrieval_response()

        @contextmanager
        def dummy_session():
            class Session:
                def add(self, item: object) -> None:
                    return None

            yield Session()

        original_retrieve = recommendation_service.retrieve
        original_get_session = recommendation_service.get_session
        recommendation_service.retrieve = lambda request: retrieval_response
        recommendation_service.get_session = dummy_session
        try:
            response = recommendation_service.recommend(
                RecommendRequest(query="I need a reliable car under $12,000 for commuting in Auckland.")
            )
        finally:
            recommendation_service.retrieve = original_retrieve
            recommendation_service.get_session = original_get_session

        evidence_ids = {item["id"] for item in response["evidence"]}
        self.assertEqual(response["debug"]["recommendation_provider"], "deterministic")
        self.assertEqual(response["debug"]["generation_model"], "deterministic_ranker_with_citations")
        self.assertIn("chunk:chunk-4", evidence_ids)
        for car in response["recommended_cars"]:
            self.assertTrue(set(car["evidence_ids"]).issubset(evidence_ids))
            for flag in car["risk_flags"]:
                self.assertTrue(set(flag["evidence_ids"]).issubset(evidence_ids))

    def _retrieval_response(self) -> dict[str, object]:
        return {
            "applied_filters": {"max_price": 12000, "location": "Auckland", "limit": 20},
            "listings": [
                {
                    "listing_id": "akl-toyota-aqua-test",
                    "title": "2015 Toyota Aqua",
                    "brand": "Toyota",
                    "model": "Aqua",
                    "year": 2015,
                    "price": 9990,
                    "mileage": 90000,
                    "fuel_type": "petrol hybrid",
                    "body_type": "hatchback",
                    "location": "Auckland",
                    "description": "Clean compact hybrid listing.",
                }
            ],
            "chunks": [
                self._chunk("chunk-1", "Toyota", "Aqua", "City use and parking are easy."),
                self._chunk("chunk-2", "Toyota", "Aqua", "Low fuel cost suits commuting."),
                self._chunk("chunk-3", "Toyota", "Aqua", "Compact size is useful in Auckland."),
                self._chunk("chunk-4", "Toyota", "Aqua", "Buyers should verify service history carefully."),
            ],
            "debug": {
                "retrieval_mode": "structured_filters_plus_semantic_chunks",
                "embedding_search_enabled": True,
                "embedding_model": "local-hash-embedding-v1",
                "candidate_models": ["Toyota Aqua"],
            },
        }

    @staticmethod
    def _chunk(chunk_id: str, brand: str, model: str, text: str) -> dict[str, object]:
        return {
            "chunk_id": chunk_id,
            "source_id": f"source-{chunk_id}",
            "source_title": f"{brand} {model} notes",
            "source_type": "maintenance",
            "brand": brand,
            "model": model,
            "evidence_level": "medium",
            "text": text,
            "similarity": 0.9,
        }


if __name__ == "__main__":
    unittest.main()
