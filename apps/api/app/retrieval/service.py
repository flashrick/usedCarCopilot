from __future__ import annotations

import re
from typing import Any

from sqlalchemy import and_, bindparam, or_, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.connection import get_session
from app.db.orm import (
    ChunkEmbeddingRecord,
    DocumentChunkRecord,
    KnowledgeSourceRecord,
    RequestLogRecord,
    Vector,
    VehicleProfileRecord,
)
from app.embedding.service import get_embedding_provider
from app.models.schemas import RetrieveRequest


MODEL_ALIASES = {
    "Toyota Aqua": ("Toyota", "Aqua"),
    "Aqua": ("Toyota", "Aqua"),
    "Toyota Prius": ("Toyota", "Prius"),
    "Prius": ("Toyota", "Prius"),
    "Toyota RAV4": ("Toyota", "RAV4"),
    "RAV4": ("Toyota", "RAV4"),
    "Honda Fit": ("Honda", "Fit"),
    "Fit": ("Honda", "Fit"),
    "Honda Civic": ("Honda", "Civic"),
    "Civic": ("Honda", "Civic"),
    "Honda HR-V": ("Honda", "HR-V"),
    "HR-V": ("Honda", "HR-V"),
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
SUPPORTED_BODY_TYPES = ("hatchback", "sedan", "suv")
SUPPORTED_FUELS = ("petrol", "hybrid", "diesel", "electric")
SUPPORTED_TRANSMISSIONS = ("automatic", "cvt", "dct", "manual")


def retrieve(request: RetrieveRequest) -> dict[str, Any]:
    filters = infer_filters(request)
    limit = filters["limit"]

    with get_session() as session:
        profiles = list(session.scalars(select(VehicleProfileRecord)))
        scored_profiles = sorted(
            profiles,
            key=lambda profile: (-score_profile(profile, filters), profile.estimated_price_mid_nzd or 10**9, profile.profile_id),
        )
        shortlisted_profiles = select_diverse_profiles(scored_profiles, limit)
        candidate_pairs = dedupe_brand_models(shortlisted_profiles or scored_profiles[:limit])
        selected_profile_ids = [profile.profile_id for profile in shortlisted_profiles]

        knowledge = load_relevant_knowledge(session, selected_profile_ids, candidate_pairs, limit)
        semantic_chunks = retrieve_semantic_chunks(
            session=session,
            query=request.query,
            filters=filters,
            candidate_pairs=candidate_pairs,
            selected_profile_ids=selected_profile_ids,
            limit=limit,
        )

        session.add(
            RequestLogRecord(
                endpoint="/retrieve",
                query=request.query,
                filters=filters,
                listing_count=0,
                profile_count=len(shortlisted_profiles),
                knowledge_count=len(semantic_chunks) or len(knowledge),
            )
        )

    return {
        "query": request.query,
        "applied_filters": filters,
        "vehicle_profiles": shortlisted_profiles,
        "knowledge": knowledge,
        "chunks": semantic_chunks,
        "debug": {
            "retrieval_mode": "vehicle_profile_ranker_with_semantic_chunks",
            "embedding_search_enabled": bool(semantic_chunks),
            "embedding_model": get_settings().embedding_model,
            "candidate_models": [f"{brand} {model}" for brand, model in candidate_pairs],
            "candidate_profile_ids": selected_profile_ids,
            "valuation_assumption": "good used condition with age-normalized NZ mileage",
        },
    }


def infer_filters(request: RetrieveRequest) -> dict[str, Any]:
    query = (request.query or "").strip()
    normalized_query = normalize_text(query)

    models = list(request.models)
    for label in MODEL_ALIASES:
        if normalize_text(label) in normalized_query and label not in models:
            models.append(label)

    detected_brands = [brand for brand in SUPPORTED_BRANDS if brand.lower() in query.lower()]
    brands = dedupe_preserving_order([*request.brands, *detected_brands])

    budget_max = request.budget_max
    if budget_max is None:
        budget_match = re.search(r"(?:under|below|budget(?: is)?|around|up to)\s+\$?([0-9][0-9,]*)", query.lower())
        if budget_match:
            budget_max = int(budget_match.group(1).replace(",", ""))

    body_type = normalize_choice(request.body_type, SUPPORTED_BODY_TYPES)
    if body_type is None:
        for candidate in SUPPORTED_BODY_TYPES:
            if candidate in normalized_query:
                body_type = candidate
                break

    fuel_type = normalize_fuel(request.fuel_type)
    if fuel_type is None:
        fuel_type = infer_fuel(query)

    transmission = normalize_choice(request.transmission, SUPPORTED_TRANSMISSIONS)
    if transmission is None:
        for candidate in SUPPORTED_TRANSMISSIONS:
            if candidate in normalized_query:
                transmission = candidate
                break

    usage = infer_usage(normalized_query)
    priority = infer_priority(normalized_query)
    compare_models = [f"{brand} {model}" for brand, model in model_pairs(models)]

    return {
        "query": request.query,
        "budget_max": budget_max,
        "brands": brands,
        "models": models,
        "body_type": body_type,
        "fuel_type": fuel_type,
        "transmission": transmission,
        "usage": usage,
        "priority": priority,
        "compare_models": compare_models,
        "limit": request.limit,
    }


def retrieve_semantic_chunks(
    session: Session,
    query: str | None,
    filters: dict[str, Any],
    candidate_pairs: list[tuple[str, str]],
    selected_profile_ids: list[str],
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

    statement = (
        select(DocumentChunkRecord, KnowledgeSourceRecord, distance)
        .join(ChunkEmbeddingRecord, ChunkEmbeddingRecord.chunk_id == DocumentChunkRecord.chunk_id)
        .join(KnowledgeSourceRecord, KnowledgeSourceRecord.source_id == DocumentChunkRecord.source_id)
        .order_by(distance.asc(), DocumentChunkRecord.chunk_id.asc())
        .limit(max(limit * 4, 10))
    )

    conditions = []
    if selected_profile_ids:
        conditions.append(
            or_(
                KnowledgeSourceRecord.profile_id.in_(selected_profile_ids),
                or_(
                    *[
                        and_(KnowledgeSourceRecord.brand == brand, KnowledgeSourceRecord.model == model)
                        for brand, model in candidate_pairs
                    ]
                ),
            )
        )
    elif candidate_pairs:
        conditions.append(
            or_(
                *[
                    and_(KnowledgeSourceRecord.brand == brand, KnowledgeSourceRecord.model == model)
                    for brand, model in candidate_pairs
                ]
            )
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
                "profile_id": source.profile_id,
                "evidence_level": source.evidence_level,
                "text": chunk.text,
                "similarity": similarity,
            }
        )
    return chunks


def load_relevant_knowledge(
    session: Session,
    selected_profile_ids: list[str],
    candidate_pairs: list[tuple[str, str]],
    limit: int,
) -> list[KnowledgeSourceRecord]:
    statement = select(KnowledgeSourceRecord)
    if selected_profile_ids:
        statement = statement.where(
            or_(
                KnowledgeSourceRecord.profile_id.in_(selected_profile_ids),
                or_(
                    *[
                        and_(KnowledgeSourceRecord.brand == brand, KnowledgeSourceRecord.model == model)
                        for brand, model in candidate_pairs
                    ]
                ),
            )
        )
    elif candidate_pairs:
        statement = statement.where(
            or_(
                *[
                    and_(KnowledgeSourceRecord.brand == brand, KnowledgeSourceRecord.model == model)
                    for brand, model in candidate_pairs
                ]
            )
        )
    return list(
        session.scalars(
            statement.order_by(KnowledgeSourceRecord.profile_id.is_(None), KnowledgeSourceRecord.source_id.asc()).limit(max(limit * 3, 12))
        )
    )


def score_profile(profile: VehicleProfileRecord, filters: dict[str, Any]) -> int:
    score = 25

    budget_max = filters.get("budget_max")
    if budget_max is not None:
        budget = budget_max
        midpoint = profile.estimated_price_mid_nzd or 0
        minimum = profile.estimated_price_min_nzd or midpoint
        if midpoint <= budget:
            score += 18
        elif minimum <= budget:
            score += 10
        else:
            score -= 20

    brands = filters.get("brands") or []
    if brands:
        score += 10 if profile.brand in brands else -6

    requested_pairs = model_pairs(filters.get("models") or [])
    if requested_pairs:
        score += 18 if (profile.brand, profile.model) in requested_pairs else -8

    body_type = filters.get("body_type")
    if body_type:
        score += 9 if normalize_text(profile.body_type) == body_type else -5
    fuel_type = filters.get("fuel_type")
    if fuel_type:
        score += 9 if fuel_matches(profile.fuel_type, fuel_type) else -5
    transmission = filters.get("transmission")
    if transmission:
        score += 7 if normalize_text(profile.transmission) == transmission else -4

    score += usage_fit_score(profile, filters.get("usage"))
    score += priority_fit_score(profile, filters.get("priority"))

    if normalize_text(profile.maintenance_cost_band) == "low":
        score += 3
    elif normalize_text(profile.maintenance_cost_band) == "medium_high":
        score -= 2
    elif normalize_text(profile.maintenance_cost_band) == "high":
        score -= 4

    return score


def usage_fit_score(profile: VehicleProfileRecord, usage: str | None) -> int:
    if not usage:
        return 0
    text = " ".join(
        filter(
            None,
            [
                profile.suitability_summary,
                profile.comfort_summary,
                profile.space_summary,
                profile.nvh_summary,
            ],
        )
    ).lower()
    if usage in {"commute", "city"} and any(token in text for token in ("commut", "city", "easy to park", "urban")):
        return 8
    if usage == "family" and any(token in text for token in ("family", "rear seat", "boot", "space")):
        return 8
    if usage == "first_car" and any(token in text for token in ("easy", "balanced", "compact", "confidence")):
        return 7
    if usage == "rideshare" and any(token in text for token in ("fuel economy", "practical", "commut")):
        return 7
    return 0


def priority_fit_score(profile: VehicleProfileRecord, priority: str | None) -> int:
    if not priority:
        return 0
    if priority == "low_running_cost":
        consumption = profile.fuel_consumption_l_per_100km or 99.0
        if consumption <= 4.5:
            return 10
        if consumption <= 6.0:
            return 6
        return -5
    if priority == "premium_feel":
        text = f"{profile.nvh_summary or ''} {profile.comfort_summary or ''}".lower()
        return 8 if any(token in text for token in ("refined", "premium", "calm", "comfortable")) else 0
    if priority == "reliability":
        text = (profile.reliability_summary or "").lower()
        return 8 if any(token in text for token in ("strong", "dependable", "proven", "low-drama")) else 0
    if priority == "space_practicality":
        text = (profile.space_summary or "").lower()
        return 7 if any(token in text for token in ("space", "boot", "rear seat", "practical")) else 0
    return 0


def select_diverse_profiles(profiles: list[VehicleProfileRecord], limit: int) -> list[VehicleProfileRecord]:
    if limit >= len(profiles):
        return profiles

    selected: list[VehicleProfileRecord] = []
    selected_ids: set[str] = set()
    seen_models: set[tuple[str, str]] = set()
    for profile in profiles:
        model_key = (profile.brand, profile.model)
        if model_key in seen_models:
            continue
        selected.append(profile)
        selected_ids.add(profile.profile_id)
        seen_models.add(model_key)
        if len(selected) >= limit:
            return selected

    for profile in profiles:
        if profile.profile_id in selected_ids:
            continue
        selected.append(profile)
        if len(selected) >= limit:
            break
    return selected


def model_pairs(models: list[str]) -> list[tuple[str, str]]:
    pairs: list[tuple[str, str]] = []
    for model in models:
        pair = MODEL_ALIASES.get(model) or NORMALIZED_MODEL_ALIASES.get(normalize_text(model))
        if pair and pair not in pairs:
            pairs.append(pair)
    return pairs


def dedupe_brand_models(profiles: list[VehicleProfileRecord]) -> list[tuple[str, str]]:
    pairs: list[tuple[str, str]] = []
    for profile in profiles:
        pair = (profile.brand, profile.model)
        if pair not in pairs:
            pairs.append(pair)
    return pairs


def normalize_choice(value: str | None, supported: tuple[str, ...]) -> str | None:
    normalized = normalize_text(value)
    if not normalized:
        return None
    return normalized if normalized in supported else None


def normalize_fuel(value: str | None) -> str | None:
    normalized = normalize_text(value)
    if not normalized:
        return None
    if "hybrid" in normalized:
        return "hybrid"
    if "petrol" in normalized or normalized == "gasoline":
        return "petrol"
    return normalized if normalized in SUPPORTED_FUELS else None


def infer_fuel(query: str) -> str | None:
    normalized = normalize_text(query)
    if "hybrid" in normalized:
        return "hybrid"
    if "petrol" in normalized:
        return "petrol"
    if "diesel" in normalized:
        return "diesel"
    if "electric" in normalized or "ev" in normalized:
        return "electric"
    return None


def infer_usage(normalized_query: str) -> str | None:
    if any(token in normalized_query for token in ("family", "child", "children")):
        return "family"
    if any(token in normalized_query for token in ("first car", "new driver")):
        return "first_car"
    if any(token in normalized_query for token in ("uber", "rideshare")):
        return "rideshare"
    if any(token in normalized_query for token in ("city", "easy to park", "urban")):
        return "city"
    if "commut" in normalized_query:
        return "commute"
    return None


def infer_priority(normalized_query: str) -> str | None:
    if any(token in normalized_query for token in ("cheap to run", "low running", "fuel economy")):
        return "low_running_cost"
    if any(token in normalized_query for token in ("premium", "refined", "comfortable")):
        return "premium_feel"
    if any(token in normalized_query for token in ("reliable", "reliability", "low risk", "safer")):
        return "reliability"
    if any(token in normalized_query for token in ("space", "practical", "boot")):
        return "space_practicality"
    return None


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


def fuel_matches(profile_fuel: str | None, requested_fuel: str) -> bool:
    normalized = normalize_text(profile_fuel)
    if requested_fuel == "hybrid":
        return "hybrid" in normalized
    return requested_fuel in normalized


def normalize_text(value: str | None) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9]+", " ", (value or "").lower())).strip()
