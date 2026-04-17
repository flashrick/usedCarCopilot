from __future__ import annotations

from typing import Any

from psycopg.types.json import Jsonb

from app.db.connection import get_connection
from app.models.schemas import RetrieveRequest


MODEL_ALIASES = {
    "Aqua": ("Toyota", "Aqua"),
    "Toyota Aqua": ("Toyota", "Aqua"),
    "Prius": ("Toyota", "Prius"),
    "Toyota Prius": ("Toyota", "Prius"),
    "RAV4": ("Toyota", "RAV4"),
    "Rav4": ("Toyota", "RAV4"),
    "Toyota RAV4": ("Toyota", "RAV4"),
    "Fit": ("Honda", "Fit"),
    "Honda Fit": ("Honda", "Fit"),
    "Civic": ("Honda", "Civic"),
    "Honda Civic": ("Honda", "Civic"),
    "HR-V": ("Honda", "HR-V"),
    "Honda HR-V": ("Honda", "HR-V"),
    "Mazda2": ("Mazda", "Mazda2"),
    "Mazda Mazda2": ("Mazda", "Mazda2"),
    "Mazda3": ("Mazda", "Mazda3"),
    "Mazda Mazda3": ("Mazda", "Mazda3"),
    "CX-5": ("Mazda", "CX-5"),
    "Mazda CX-5": ("Mazda", "CX-5"),
}


def infer_filters(request: RetrieveRequest) -> dict[str, Any]:
    query = (request.query or "").lower()
    models = list(request.models)
    for label in MODEL_ALIASES:
        if label.lower() in query and label not in models:
            models.append(label)

    body_type = request.body_type
    if body_type is None:
        if "suv" in query:
            body_type = "suv"
        elif "hatchback" in query:
            body_type = "hatchback"
        elif "sedan" in query:
            body_type = "sedan"

    max_price = request.max_price
    if max_price is None:
        # Keep parsing intentionally conservative until a proper parser is added.
        import re

        price_match = re.search(r"under\s+\$?([0-9][0-9,]*)", query)
        if price_match:
            max_price = int(price_match.group(1).replace(",", ""))

    return {
        "query": request.query,
        "max_price": max_price,
        "brand": request.brand,
        "models": models,
        "body_type": body_type,
        "location": request.location,
        "limit": request.limit,
    }


def model_pairs(models: list[str]) -> list[tuple[str, str]]:
    pairs: list[tuple[str, str]] = []
    for model in models:
        pair = MODEL_ALIASES.get(model)
        if pair and pair not in pairs:
            pairs.append(pair)
    return pairs


def retrieve(request: RetrieveRequest) -> dict[str, Any]:
    filters = infer_filters(request)
    conditions = []
    params: list[Any] = []

    if filters["location"]:
        conditions.append("location = %s")
        params.append(filters["location"])
    if filters["max_price"] is not None:
        conditions.append("(price IS NOT NULL AND price <= %s)")
        params.append(filters["max_price"])
    if filters["brand"]:
        conditions.append("brand = %s")
        params.append(filters["brand"])
    if filters["body_type"]:
        conditions.append("body_type = %s")
        params.append(filters["body_type"])

    pairs = model_pairs(filters["models"])
    if pairs:
        model_conditions = []
        for brand, model in pairs:
            model_conditions.append("(brand = %s AND model = %s)")
            params.extend([brand, model])
        conditions.append("(" + " OR ".join(model_conditions) + ")")

    where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""
    limit = filters["limit"]

    with get_connection() as connection:
        listings = connection.execute(
            f"""
            SELECT listing_id, title, brand, model, year, price, mileage,
                   transmission, fuel_type, seller_type, location, body_type,
                   source, source_url, description
            FROM listings
            {where_clause}
            ORDER BY
              price IS NULL,
              price ASC,
              mileage IS NULL,
              mileage ASC,
              year DESC NULLS LAST
            LIMIT %s
            """,
            [*params, limit],
        ).fetchall()

        candidate_pairs = sorted({(row["brand"], row["model"]) for row in listings})
        knowledge = []
        if candidate_pairs:
            knowledge_conditions = []
            knowledge_params: list[Any] = []
            for brand, model in candidate_pairs:
                knowledge_conditions.append("(brand = %s AND model = %s)")
                knowledge_params.extend([brand, model])
            knowledge = connection.execute(
                f"""
                SELECT source_id, source_type, source_channel, title, brand, model,
                       year_range, market, tags, summary, text, evidence_level,
                       ownership_stage
                FROM knowledge_sources
                WHERE {" OR ".join(knowledge_conditions)}
                ORDER BY evidence_level DESC, source_id ASC
                LIMIT %s
                """,
                [*knowledge_params, max(limit * 3, 10)],
            ).fetchall()

        connection.execute(
            """
            INSERT INTO request_logs (endpoint, query, filters, listing_count, knowledge_count)
            VALUES (%s, %s, %s, %s, %s)
            """,
            ("/retrieve", request.query, Jsonb(filters), len(listings), len(knowledge)),
        )

    return {
        "query": request.query,
        "applied_filters": filters,
        "listings": listings,
        "knowledge": knowledge,
        "debug": {
            "candidate_models": [f"{brand} {model}" for brand, model in candidate_pairs],
            "retrieval_mode": "structured_filters_plus_model_linked_knowledge",
            "embedding_search_enabled": False,
        },
    }
