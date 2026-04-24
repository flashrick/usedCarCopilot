from __future__ import annotations

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
        retrieval_response = {
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
