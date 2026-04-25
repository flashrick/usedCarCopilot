from __future__ import annotations

import re
from typing import Any

from sqlalchemy import and_, bindparam, case, or_, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.connection import get_session
from app.db.orm import (
    ChunkEmbeddingRecord,
    DocumentChunkRecord,
    KnowledgeSourceRecord,
    ListingRecord,
    RequestLogRecord,
    Vector,
)
from app.embedding.service import get_embedding_provider
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
NORMALIZED_MODEL_ALIASES = {
    re.sub(r"\s+", " ", re.sub(r"[^a-z0-9]+", " ", label.lower())).strip(): pair
    for label, pair in MODEL_ALIASES.items()
}

SUPPORTED_BRANDS = ("Toyota", "Honda", "Mazda")

BODY_TYPE_BY_MODEL = {
    ("Honda", "Civic"): "sedan",
    ("Honda", "Fit"): "hatchback",
    ("Honda", "HR-V"): "suv",
    ("Mazda", "CX-5"): "suv",
    ("Mazda", "Mazda2"): "hatchback",
    ("Mazda", "Mazda3"): "hatchback",
    ("Toyota", "Aqua"): "hatchback",
    ("Toyota", "Prius"): "hatchback",
    ("Toyota", "RAV4"): "suv",
}

NEGATED_BODY_TYPE_PATTERNS = {
    "suv": ("do not want an suv", "don't want an suv", "not an suv", "no suv", "avoid suv"),
    "hatchback": (
        "do not want a hatchback",
        "don't want a hatchback",
        "not a hatchback",
        "no hatchback",
        "avoid hatchback",
    ),
    "sedan": ("do not want a sedan", "don't want a sedan", "not a sedan", "no sedan", "avoid sedan"),
}

RUNNING_COST_TERMS = (
    "cheap to run",
    "low running",
    "running cost",
    "fuel economy",
    "fuel efficient",
    "efficient",
    "hybrid",
)

PREMIUM_TERMS = ("premium", "nicer", "upmarket", "comfortable")
FUEL_PREFERENCE_TERMS = {
    "hybrid": ("hybrid", "petrol hybrid", "gas hybrid"),
    "petrol": ("petrol", "gasoline", "gas "),
    "diesel": ("diesel",),
    "electric": ("electric", "ev"),
}


def infer_filters(request: RetrieveRequest) -> dict[str, Any]:
    query = (request.query or "").lower()
    normalized_query = normalize_text(query)
    models = list(request.models)
    for label in MODEL_ALIASES:
        if normalize_text(label) in normalized_query and label not in models:
            models.append(label)

    detected_brands = detect_brands(query)
    if not detected_brands and "these brands" in normalized_query:
        detected_brands = list(SUPPORTED_BRANDS)
    requested_brands = dedupe_preserving_order([*request.brands, *detected_brands])
    brand = request.brand
    if brand is None and len(requested_brands) == 1:
        brand = requested_brands[0]

    exclude_body_type = detect_excluded_body_type(normalized_query)
    body_type = request.body_type.lower() if request.body_type else None
    if body_type is None:
        if "suv" in query and not is_negated_body_type(query, "suv"):
            body_type = "suv"
        elif "hatchback" in query and not is_negated_body_type(query, "hatchback"):
            body_type = "hatchback"
        elif "sedan" in query and not is_negated_body_type(query, "sedan"):
            body_type = "sedan"
        else:
            inferred_body_type = infer_body_type_from_models(model_pairs(models))
            if inferred_body_type:
                body_type = inferred_body_type

    max_price = request.max_price
    if max_price is None:
        price_match = re.search(r"(?:under|budget(?:\s+is)?(?:\s+around)?|around)\s+\$?([0-9][0-9,]*)", query)
        if price_match:
            max_price = int(price_match.group(1).replace(",", ""))

    max_mileage = request.max_mileage
    if max_mileage is None:
        mileage_match = re.search(
            r"(?:under|below|less than|max(?:imum)?(?: mileage)?(?: around)?|up to)\s+([0-9][0-9,]*)\s*(?:km|kms|kilomet(?:er|re)s?)",
            query,
        )
        if mileage_match:
            max_mileage = int(mileage_match.group(1).replace(",", ""))

    fuel_type = normalize_fuel_preference(request.fuel_type)
    if fuel_type is None:
        fuel_type = infer_fuel_preference(query)

    context_filters = infer_context_filters(normalized_query)

    return {
        "query": request.query,
        "max_price": max_price,
        "max_mileage": max_mileage,
        "brand": brand,
        "brands": requested_brands,
        "models": models,
        "body_type": body_type,
        "exclude_body_type": exclude_body_type,
        "fuel_type": fuel_type,
        "location": request.location,
        "limit": request.limit,
        "prefer_hybrid": any(term in query for term in RUNNING_COST_TERMS),
        "prefer_premium": any(term in query for term in PREMIUM_TERMS),
        **context_filters,
    }


def model_pairs(models: list[str]) -> list[tuple[str, str]]:
    pairs: list[tuple[str, str]] = []
    for model in models:
        pair = MODEL_ALIASES.get(model) or NORMALIZED_MODEL_ALIASES.get(normalize_text(model))
        if pair and pair not in pairs:
            pairs.append(pair)
    return pairs


def infer_body_type_from_models(pairs: list[tuple[str, str]]) -> str | None:
    mapped_body_types = [BODY_TYPE_BY_MODEL[pair] for pair in pairs if pair in BODY_TYPE_BY_MODEL]
    body_types = set(mapped_body_types)
    if pairs and len(mapped_body_types) == len(pairs) and len(body_types) == 1:
        return next(iter(body_types))
    return None


def detect_brands(query: str) -> list[str]:
    return [brand for brand in SUPPORTED_BRANDS if brand.lower() in query]


def dedupe_preserving_order(values: list[str]) -> list[str]:
    deduped: list[str] = []
    for value in values:
        normalized = value.strip()
        if not normalized:
            continue
        canonical = next((brand for brand in SUPPORTED_BRANDS if brand.lower() == normalized.lower()), normalized)
        if canonical not in deduped:
            deduped.append(canonical)
    return deduped


def is_negated_body_type(query: str, body_type: str) -> bool:
    return any(pattern in query for pattern in NEGATED_BODY_TYPE_PATTERNS[body_type])


def detect_excluded_body_type(normalized_query: str) -> str | None:
    for body_type in NEGATED_BODY_TYPE_PATTERNS:
        if is_negated_body_type(normalized_query, body_type):
            return body_type
    return None


def infer_context_filters(normalized_query: str) -> dict[str, Any]:
    filters: dict[str, Any] = {}
    if "commut" in normalized_query:
        filters["usage"] = "daily_commute" if "grocery" in normalized_query else "commute"
    if "city" in normalized_query or "easy to park" in normalized_query:
        filters["usage"] = "city" if "which of these" in normalized_query else filters.get("usage", "short_city_trips")
    if "family" in normalized_query or "child" in normalized_query or "children" in normalized_query:
        filters["usage"] = "small_family_errands" if "shopping" in normalized_query else "family"
        filters["household_size"] = 3
        if "shopping" in normalized_query or "too small" in normalized_query or "carry" in normalized_query:
            filters["priority"] = "practicality"
    if "uber" in normalized_query or "rideshare" in normalized_query:
        filters["usage"] = "rideshare"
        filters["priority"] = "fuel_economy"
    if "first car" in normalized_query or "new driver" in normalized_query:
        filters["usage"] = "first_car"
        filters["driver_profile"] = "new_driver"
    if "highway" in normalized_query or "hamilton" in normalized_query:
        filters["usage"] = "highway"
        filters["route_profile"] = "intercity"
    if "daily use" in normalized_query:
        filters["usage"] = "daily_use"
    if "short distance" in normalized_query or "short distances" in normalized_query:
        filters["usage"] = "short_city_trips"
        filters["priority"] = "efficiency"

    if "check before" in normalized_query or "inspection" in normalized_query or "before purchase" in normalized_query:
        filters["ownership_stage"] = "pre_purchase"
        filters["intent"] = "inspection"
    if "cheaper to own" in normalized_query:
        filters["intent"] = "ownership_cost"
    if "main risks" in normalized_query or "risk" in normalized_query:
        filters["intent"] = "risk_assessment"
    if "high mileage" in normalized_query:
        filters["mileage_band"] = "high"

    if "reliable" in normalized_query or "reliability" in normalized_query:
        filters["priority"] = "reliability"
    if "city driving" in normalized_query:
        filters["priority"] = "city_driving"
    if "fuel economy" in normalized_query:
        filters["priority"] = "fuel_economy"
    if "practical" in normalized_query or "practicality" in normalized_query:
        filters["priority"] = "practicality"
    if "low running" in normalized_query:
        filters["priority"] = "low_running_cost"
    if "cheap to run" in normalized_query:
        filters["priority"] = "cheap_to_run"
        filters["secondary_priority"] = "easy_parking"
    if "premium feel" in normalized_query or "premium" in normalized_query:
        filters["priority"] = "premium_feel"
    if "low risk" in normalized_query:
        filters["priority"] = "low_risk"
    if "safer choice" in normalized_query or "safer choices" in normalized_query:
        filters["priority"] = "safer_choice"
    if "space" in normalized_query or "big enough" in normalized_query:
        filters["priority"] = "space_practicality"
    if "efficiency" in normalized_query or "short distances" in normalized_query:
        filters["priority"] = "efficiency"

    if "grocery" in normalized_query or "shopping" in normalized_query or "errand" in normalized_query:
        filters["secondary_usage"] = "errands"
    if "do not know much" in normalized_query or "simple" in normalized_query:
        filters["user_profile"] = "novice_buyer"
        filters["priority"] = "low_risk"
    if "hybrid" in normalized_query:
        filters["fuel_type"] = "hybrid"
    return filters


def normalize_fuel_preference(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = normalize_text(value)
    if not normalized:
        return None
    for canonical, aliases in FUEL_PREFERENCE_TERMS.items():
        if normalized == canonical or normalized in aliases:
            return canonical
    return normalized


def infer_fuel_preference(query: str) -> str | None:
    normalized_query = f" {normalize_text(query)} "
    for canonical, aliases in FUEL_PREFERENCE_TERMS.items():
        if any(f" {normalize_text(alias)} " in normalized_query for alias in aliases):
            return canonical
    return None


def listing_order(filters: dict[str, Any]) -> list[Any]:
    order: list[Any] = []
    if filters["prefer_hybrid"]:
        order.append(case((ListingRecord.fuel_type.ilike("%hybrid%"), 0), else_=1))
    if filters["prefer_premium"]:
        order.extend(
            [
                ListingRecord.price.is_(None),
                ListingRecord.price.desc(),
                ListingRecord.year.desc().nulls_last(),
            ]
        )
    if filters.get("priority") in {"low_risk", "safer_choice"}:
        order.extend(
            [
                ListingRecord.price.is_(None),
                ListingRecord.mileage.is_(None),
                ListingRecord.mileage.asc(),
                ListingRecord.year.desc().nulls_last(),
            ]
        )
    order.extend(
        [
            ListingRecord.price.is_(None),
            ListingRecord.price.asc(),
            ListingRecord.mileage.is_(None),
            ListingRecord.mileage.asc(),
            ListingRecord.year.desc().nulls_last(),
        ]
    )
    return order


def retrieve_semantic_chunks(
    session: Session,
    query: str | None,
    filters: dict[str, Any],
    candidate_pairs: list[tuple[str, str]],
    limit: int,
) -> list[dict[str, Any]]:
    if not query or not query.strip():
        return []

    settings = get_settings()
    provider = get_embedding_provider(settings.embedding_provider, settings.embedding_model)
    query_embedding = provider.embed(query)
    distance = ChunkEmbeddingRecord.embedding.op("<=>")(
        bindparam("query_embedding", query_embedding, type_=Vector(provider.dimensions))
    ).label("distance")

    conditions = []
    scoped_pairs = model_pairs(filters["models"]) or candidate_pairs
    if scoped_pairs:
        conditions.append(
            or_(
                *[
                    and_(KnowledgeSourceRecord.brand == brand, KnowledgeSourceRecord.model == model)
                    for brand, model in scoped_pairs
                ]
            )
        )
    elif filters["brand"]:
        conditions.append(KnowledgeSourceRecord.brand == filters["brand"])
    elif filters["brands"]:
        conditions.append(KnowledgeSourceRecord.brand.in_(filters["brands"]))

    statement = (
        select(DocumentChunkRecord, KnowledgeSourceRecord, distance)
        .join(ChunkEmbeddingRecord, ChunkEmbeddingRecord.chunk_id == DocumentChunkRecord.chunk_id)
        .join(KnowledgeSourceRecord, KnowledgeSourceRecord.source_id == DocumentChunkRecord.source_id)
        .order_by(distance.asc(), DocumentChunkRecord.chunk_id.asc())
        .limit(max(limit * 3, 8))
    )
    if conditions:
        statement = statement.where(and_(*conditions))

    rows = session.execute(statement).all()

    chunks: list[dict[str, Any]] = []
    for chunk, source, distance_value in rows:
        similarity = None
        if distance_value is not None:
            similarity = round(max(0.0, 1.0 - float(distance_value)), 4)
        chunks.append(
            {
                "chunk_id": chunk.chunk_id,
                "source_id": source.source_id,
                "source_title": source.title,
                "source_type": source.source_type,
                "brand": source.brand,
                "model": source.model,
                "evidence_level": source.evidence_level,
                "text": chunk.text,
                "similarity": similarity,
            }
        )
    return chunks


def listing_conditions(filters: dict[str, Any], include_price: bool = True) -> list[Any]:
    conditions = []

    if filters["location"]:
        conditions.append(ListingRecord.location == filters["location"])
    if include_price and filters["max_price"] is not None:
        conditions.append(and_(ListingRecord.price.is_not(None), ListingRecord.price <= filters["max_price"]))
    if filters.get("max_mileage") is not None:
        conditions.append(and_(ListingRecord.mileage.is_not(None), ListingRecord.mileage <= filters["max_mileage"]))
    if filters["brand"]:
        conditions.append(ListingRecord.brand == filters["brand"])
    elif filters["brands"]:
        conditions.append(ListingRecord.brand.in_(filters["brands"]))
    if filters["body_type"]:
        conditions.append(ListingRecord.body_type == filters["body_type"])
    if filters.get("exclude_body_type"):
        conditions.append(ListingRecord.body_type != filters["exclude_body_type"])
    if filters.get("fuel_type") == "hybrid":
        conditions.append(ListingRecord.fuel_type.ilike("%hybrid%"))
    elif filters.get("fuel_type"):
        conditions.append(ListingRecord.fuel_type.ilike(f"%{filters['fuel_type']}%"))

    pairs = model_pairs(filters["models"])
    if pairs:
        conditions.append(
            or_(
                *[
                    and_(ListingRecord.brand == brand, ListingRecord.model == model)
                    for brand, model in pairs
                ]
            )
        )
    return conditions


def select_diverse_listings(listings: list[ListingRecord], limit: int) -> list[ListingRecord]:
    if limit >= len(listings):
        return listings

    selected: list[ListingRecord] = []
    selected_ids: set[str] = set()
    seen_models: set[tuple[str, str]] = set()
    for listing in listings:
        model = (listing.brand, listing.model)
        if model in seen_models:
            continue
        selected.append(listing)
        selected_ids.add(listing.listing_id)
        seen_models.add(model)
        if len(selected) >= limit:
            return selected

    for listing in listings:
        if listing.listing_id in selected_ids:
            continue
        selected.append(listing)
        if len(selected) >= limit:
            break
    return selected


def retrieve(request: RetrieveRequest) -> dict[str, Any]:
    filters = infer_filters(request)
    conditions = listing_conditions(filters)
    limit = filters["limit"]

    with get_session() as session:
        statement = (
            select(ListingRecord)
            .order_by(*listing_order(filters))
            .limit(max(limit * 6, 30))
        )
        if conditions:
            statement = statement.where(and_(*conditions))

        candidate_listing_rows = list(session.scalars(statement))
        listings = select_diverse_listings(candidate_listing_rows, limit)

        candidate_statement = select(ListingRecord.brand, ListingRecord.model).distinct()
        candidate_conditions = listing_conditions(filters, include_price=False)
        if candidate_conditions:
            candidate_statement = candidate_statement.where(and_(*candidate_conditions))
        candidate_pair_rows = session.execute(candidate_statement).all()
        candidate_pairs = sorted((brand, model) for brand, model in candidate_pair_rows) or sorted(
            {(row.brand, row.model) for row in candidate_listing_rows}
        )
        knowledge: list[KnowledgeSourceRecord] = []
        if candidate_pairs:
            knowledge = list(
                session.scalars(
                    select(KnowledgeSourceRecord)
                    .where(
                        or_(
                            *[
                                and_(KnowledgeSourceRecord.brand == brand, KnowledgeSourceRecord.model == model)
                                for brand, model in candidate_pairs
                            ]
                        )
                    )
                    .order_by(KnowledgeSourceRecord.evidence_level.desc(), KnowledgeSourceRecord.source_id.asc())
                    .limit(max(limit * 3, 10))
                )
            )

        semantic_chunks = retrieve_semantic_chunks(
            session=session,
            query=request.query,
            filters=filters,
            candidate_pairs=candidate_pairs,
            limit=limit,
        )

        session.add(
            RequestLogRecord(
                endpoint="/retrieve",
                query=request.query,
                filters=filters,
                listing_count=len(listings),
                knowledge_count=len(semantic_chunks) or len(knowledge),
            )
        )

    return {
        "query": request.query,
        "applied_filters": filters,
        "listings": listings,
        "knowledge": knowledge,
        "chunks": semantic_chunks,
        "debug": {
            "candidate_models": [f"{brand} {model}" for brand, model in candidate_pairs],
            "retrieval_mode": "structured_filters_plus_semantic_chunks",
            "embedding_search_enabled": bool(semantic_chunks),
            "embedding_model": get_settings().embedding_model,
            "semantic_chunk_count": len(semantic_chunks),
        },
    }


def normalize_text(value: Any) -> str:
    text = "" if value is None else str(value).lower()
    text = text.replace("-", " ")
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()
