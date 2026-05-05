from __future__ import annotations

import re
from typing import Any

from sqlalchemy import and_, bindparam, func, or_, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.connection import get_session
from app.db.orm import (
    ChunkEmbeddingRecord,
    DocumentChunkRecord,
    KnowledgeSourceRecord,
    ModelMarketVariantRecord,
    ModelPopularityRankingRecord,
    RequestLogRecord,
    Vector,
    VehicleProfileRecord,
)
from app.embedding.service import get_embedding_provider
from app.models.schemas import RetrieveRequest


MODEL_ALIASES = {
    "Toyota RAV4": ("Toyota", "RAV4"),
    "RAV4": ("Toyota", "RAV4"),
    "Honda CR-V": ("Honda", "CR-V"),
    "CR-V": ("Honda", "CR-V"),
    "Toyota Camry": ("Toyota", "Camry"),
    "Camry": ("Toyota", "Camry"),
    "Honda Civic": ("Honda", "Civic"),
    "Civic": ("Honda", "Civic"),
    "Tesla Model Y": ("Tesla", "Model Y"),
    "Model Y": ("Tesla", "Model Y"),
    "BYD Song Plus": ("BYD", "Song Plus"),
    "Song Plus": ("BYD", "Song Plus"),
    "BYD Qin Plus": ("BYD", "Qin Plus"),
    "Qin Plus": ("BYD", "Qin Plus"),
}
NORMALIZED_MODEL_ALIASES = {
    re.sub(r"\s+", " ", re.sub(r"[^a-z0-9]+", " ", label.lower())).strip(): pair
    for label, pair in MODEL_ALIASES.items()
}
SUPPORTED_BRANDS = ("Toyota", "Honda", "Tesla", "BYD")
SUPPORTED_BODY_TYPES = ("hatchback", "sedan", "suv")
SUPPORTED_FUELS = ("petrol", "hybrid", "diesel", "electric")
SUPPORTED_TRANSMISSIONS = ("automatic", "cvt", "dct", "manual")
SUPPORTED_MARKETS = ("US", "CN")
DEFAULT_POPULAR_MODEL_LIMIT = 8
POPULAR_RELEVANCE_TIE_DELTA = 0.5


def retrieve(request: RetrieveRequest) -> dict[str, Any]:
    filters = infer_filters(request)
    limit = filters["limit"]

    with get_session() as session:
        popular_models = load_popular_models(session, filters, DEFAULT_POPULAR_MODEL_LIMIT)
        profiles = load_candidate_profiles(session, filters)
        scored_profiles = sorted(
            profiles,
            key=lambda profile: (-score_profile(profile, filters), profile.estimated_price_mid_nzd or 10**9, profile.profile_id),
        )
        shortlisted_profiles = select_diverse_profiles(scored_profiles, limit)
        candidate_pairs = dedupe_brand_models(shortlisted_profiles or scored_profiles[:limit])
        if not candidate_pairs:
            candidate_pairs = [(item["brand"], item["model"]) for item in popular_models[:limit]]
        selected_profile_ids = [profile.profile_id for profile in shortlisted_profiles]

        knowledge = load_relevant_knowledge(session, filters["market"], selected_profile_ids, candidate_pairs, limit)
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
        "popular_models": popular_models,
        "vehicle_profiles": shortlisted_profiles,
        "knowledge": knowledge,
        "chunks": semantic_chunks,
        "debug": {
            "retrieval_mode": "market_aware_popular_models_plus_vehicle_profile_ranker",
            "embedding_search_enabled": bool(semantic_chunks),
            "embedding_model": get_settings().embedding_model,
            "candidate_models": [f"{brand} {model}" for brand, model in candidate_pairs],
            "candidate_profile_ids": selected_profile_ids,
            "market": filters["market"],
            "valuation_assumption": "good used condition with market-aware retained-value estimation",
        },
    }


def infer_filters(request: RetrieveRequest) -> dict[str, Any]:
    market = normalize_market(request.market)
    query = (request.query or "").strip()
    normalized_query = normalize_text(query)
    lowered_query = query.lower()

    models = list(request.models)
    for label in MODEL_ALIASES:
        if normalize_text(label) in normalized_query and label not in models:
            models.append(label)

    detected_brands = [brand for brand in SUPPORTED_BRANDS if brand.lower() in lowered_query]
    brands = dedupe_preserving_order([*request.brands, *detected_brands])

    budget_max = request.budget_max
    if budget_max is None:
        budget_match = re.search(r"(?:under|below|budget(?: is)?|around|up to)\s+\$?([0-9][0-9,]*)", lowered_query)
        if budget_match:
            budget_max = int(budget_match.group(1).replace(",", ""))

    body_type = normalize_choice(request.body_type, SUPPORTED_BODY_TYPES)
    if body_type is None:
        body_type = infer_body_type(query, normalized_query)

    fuel_type = normalize_fuel(request.fuel_type)
    if fuel_type is None:
        fuel_type = infer_fuel(query)

    transmission = normalize_choice(request.transmission, SUPPORTED_TRANSMISSIONS)
    if transmission is None:
        for candidate in SUPPORTED_TRANSMISSIONS:
            if candidate in normalized_query:
                transmission = candidate
                break

    usage = infer_usage(query, normalized_query)
    priority = infer_priority(query, normalized_query)
    compare_models = [f"{brand} {model}" for brand, model in model_pairs(models)]

    return {
        "market": market,
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


def load_popular_models(session: Session, filters: dict[str, Any], limit: int) -> list[dict[str, Any]]:
    statement = (
        select(ModelMarketVariantRecord, ModelPopularityRankingRecord)
        .join(
            ModelPopularityRankingRecord,
            and_(
                ModelPopularityRankingRecord.market_variant_id == ModelMarketVariantRecord.market_variant_id,
                ModelPopularityRankingRecord.market == ModelMarketVariantRecord.market,
            ),
        )
        .where(ModelMarketVariantRecord.market == filters["market"])
    )
    brands = filters.get("brands") or []
    if brands:
        statement = statement.where(ModelMarketVariantRecord.brand.in_(brands))

    matching_variant_ids = load_matching_market_variant_ids(session, filters)
    rows = session.execute(statement).all()
    scored: list[dict[str, Any]] = []
    for variant, ranking in rows:
        if not popular_model_matches_filters(variant, filters, matching_variant_ids):
            continue
        relevance_score = score_popular_model(variant, ranking, filters)
        scored.append(
            {
                "market_variant_id": variant.market_variant_id,
                "canonical_model_id": variant.canonical_model_id,
                "market": variant.market,
                "brand": variant.brand,
                "model": variant.model,
                "display_name": variant.display_name,
                "year_start": variant.year_start,
                "year_end": variant.year_end,
                "body_types": list(variant.body_types or []),
                "fuel_types": list(variant.fuel_types or []),
                "popularity_rank": ranking.popularity_rank,
                "brand_popularity_rank": ranking.brand_popularity_rank,
                "relevance_score": round(relevance_score, 2),
                "match_reasons": build_popular_model_reasons(variant, ranking, filters),
                "_sort_key": popularity_sort_key(relevance_score, ranking.brand_popularity_rank, ranking.popularity_rank, variant.display_name),
            }
        )
    scored.sort(key=lambda item: item["_sort_key"])
    for item in scored:
        item.pop("_sort_key", None)
    return scored[:limit]


def load_matching_market_variant_ids(session: Session, filters: dict[str, Any]) -> set[str]:
    statement = select(VehicleProfileRecord.market_variant_id).where(
        *build_profile_filter_conditions(filters),
        VehicleProfileRecord.market_variant_id.is_not(None),
    )
    return {market_variant_id for market_variant_id in session.scalars(statement.distinct()) if market_variant_id}


def popular_model_matches_filters(
    variant: ModelMarketVariantRecord,
    filters: dict[str, Any],
    matching_variant_ids: set[str] | None = None,
) -> bool:
    if matching_variant_ids is not None and variant.market_variant_id not in matching_variant_ids:
        return False

    body_type = filters.get("body_type")
    if body_type and body_type not in list(variant.body_types or []):
        return False

    fuel_type = filters.get("fuel_type")
    if fuel_type and not fuel_group_matches(list(variant.fuel_types or []), fuel_type):
        return False

    requested_pairs = model_pairs(filters.get("models") or [])
    if requested_pairs and (variant.brand, variant.model) not in requested_pairs:
        return False

    return True


def build_profile_filter_conditions(filters: dict[str, Any]) -> list[Any]:
    conditions: list[Any] = [VehicleProfileRecord.market == filters["market"]]

    brands = filters.get("brands") or []
    if brands:
        conditions.append(VehicleProfileRecord.brand.in_(brands))

    requested_pairs = model_pairs(filters.get("models") or [])
    if requested_pairs:
        conditions.append(
            or_(
                *[
                    and_(VehicleProfileRecord.brand == brand, VehicleProfileRecord.model == model)
                    for brand, model in requested_pairs
                ]
            )
        )

    body_type = filters.get("body_type")
    if body_type:
        conditions.append(func.lower(VehicleProfileRecord.body_type) == body_type)

    fuel_type = filters.get("fuel_type")
    if fuel_type == "hybrid":
        conditions.append(func.lower(VehicleProfileRecord.fuel_type).like("%hybrid%"))
    elif fuel_type == "electric":
        conditions.append(func.lower(VehicleProfileRecord.fuel_type).like("%electric%"))
    elif fuel_type == "diesel":
        conditions.append(func.lower(VehicleProfileRecord.fuel_type).like("%diesel%"))
    elif fuel_type == "petrol":
        conditions.append(
            and_(
                func.lower(VehicleProfileRecord.fuel_type).like("%petrol%"),
                ~func.lower(VehicleProfileRecord.fuel_type).like("%hybrid%"),
            )
        )

    transmission = filters.get("transmission")
    if transmission:
        conditions.append(func.lower(VehicleProfileRecord.transmission) == transmission)

    return conditions


def popularity_sort_key(relevance_score: float, brand_rank: int, popularity_rank: int, display_name: str) -> tuple[float, int, int, str]:
    rounded_bucket = int(relevance_score / POPULAR_RELEVANCE_TIE_DELTA)
    return (-rounded_bucket, brand_rank, popularity_rank, display_name)


def score_popular_model(
    variant: ModelMarketVariantRecord,
    ranking: ModelPopularityRankingRecord,
    filters: dict[str, Any],
) -> float:
    score = 20.0
    query = str(filters.get("query") or "")
    normalized_query = normalize_text(query)
    lowered_query = query.lower()

    if normalize_text(variant.display_name) in normalized_query or normalize_text(variant.model) in normalized_query:
        score += 24.0
    if variant.brand.lower() in lowered_query:
        score += 12.0

    body_type = filters.get("body_type")
    if body_type:
        score += 15.0 if body_type in list(variant.body_types or []) else -5.0
    fuel_type = filters.get("fuel_type")
    if fuel_type:
        score += 14.0 if fuel_group_matches(list(variant.fuel_types or []), fuel_type) else -4.0

    requested_pairs = model_pairs(filters.get("models") or [])
    if requested_pairs:
        score += 20.0 if (variant.brand, variant.model) in requested_pairs else -3.0

    usage = filters.get("usage")
    if usage and tag_matches_usage(list(ranking.match_tags or []), usage):
        score += 12.0

    priority = filters.get("priority")
    if priority and tag_matches_priority(list(ranking.match_tags or []), priority):
        score += 10.0

    if filters.get("budget_max") is not None and any(token in normalized_query for token in ("family", "space", "commut", "reliable")):
        score += 2.0

    return score


def build_popular_model_reasons(
    variant: ModelMarketVariantRecord,
    ranking: ModelPopularityRankingRecord,
    filters: dict[str, Any],
) -> list[str]:
    reasons: list[str] = []
    body_type = filters.get("body_type")
    if body_type and body_type in list(variant.body_types or []):
        reasons.append(f"Matches requested {body_type} body style.")
    fuel_type = filters.get("fuel_type")
    if fuel_type and fuel_group_matches(list(variant.fuel_types or []), fuel_type):
        reasons.append(f"Offers the requested {fuel_type} powertrain direction.")
    usage = filters.get("usage")
    if usage and tag_matches_usage(list(ranking.match_tags or []), usage):
        reasons.append(f"Popular with {usage.replace('_', ' ')} use cases in this market.")
    priority = filters.get("priority")
    if priority and tag_matches_priority(list(ranking.match_tags or []), priority):
        reasons.append(f"Aligns with {priority.replace('_', ' ')} preferences.")
    if not reasons:
        reasons.append("Ranks highly in this market and remains broadly relevant to the query.")
    return reasons[:3]


def load_candidate_profiles(session: Session, filters: dict[str, Any]) -> list[VehicleProfileRecord]:
    statement = select(VehicleProfileRecord).where(*build_profile_filter_conditions(filters))

    return list(session.scalars(statement.order_by(VehicleProfileRecord.brand.asc(), VehicleProfileRecord.model.asc(), VehicleProfileRecord.profile_id.asc())))


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
        .where(KnowledgeSourceRecord.market == filters["market"])
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
                "market": source.market,
                "profile_id": source.profile_id,
                "evidence_level": source.evidence_level,
                "text": chunk.text,
                "similarity": similarity,
            }
        )
    return chunks


def load_relevant_knowledge(
    session: Session,
    market: str,
    selected_profile_ids: list[str],
    candidate_pairs: list[tuple[str, str]],
    limit: int,
) -> list[KnowledgeSourceRecord]:
    statement = select(KnowledgeSourceRecord).where(KnowledgeSourceRecord.market == market)
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

    safety_weight = 2 if query_mentions_safety(filters.get("query")) else 1
    transmission_risk_weight = 2 if query_mentions_maintenance_risk(filters.get("query")) else 1
    score += safety_score_delta(profile) * safety_weight
    score += transmission_risk_delta(profile) * transmission_risk_weight

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
        consumption = profile.fuel_consumption_l_per_100km if profile.fuel_consumption_l_per_100km is not None else 99.0
        if consumption == 0:
            return 8
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


def safety_score_delta(profile: VehicleProfileRecord) -> int:
    if (profile.safety_rating_status or "").lower() == "unrated":
        return 0
    if profile.safety_rating_stars is None:
        return 0
    if profile.safety_rating_stars >= 5:
        return 8
    if profile.safety_rating_stars == 4:
        return 4
    return -6


def transmission_risk_delta(profile: VehicleProfileRecord) -> int:
    risk = normalize_text(profile.transmission_maintenance_risk)
    if risk == "low":
        return 5
    if risk == "high":
        return -8
    return 0


def query_mentions_safety(query: Any) -> bool:
    text = str(query or "")
    normalized = normalize_text(text)
    return any(token in normalized for token in ("safety", "safe", "safer")) or "安全" in text


def query_mentions_maintenance_risk(query: Any) -> bool:
    text = str(query or "")
    normalized = normalize_text(text)
    return any(token in normalized for token in ("reliable", "reliability", "maintenance", "repair", "gearbox", "transmission")) or any(
        token in text for token in ("省心", "维修", "变速箱")
    )


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
    if "hybrid" in normalized or "混动" in query or "dmi" in normalized:
        return "hybrid"
    if "petrol" in normalized or "gasoline" in normalized or "燃油" in query:
        return "petrol"
    if "diesel" in normalized:
        return "diesel"
    if "electric" in normalized or "ev" in normalized or "电动" in query or "新能源" in query:
        return "electric"
    return None


def infer_body_type(query: str, normalized_query: str) -> str | None:
    if "轿车" in query:
        return "sedan"
    if "suv" in normalized_query or "SUV" in query or "越野" in query:
        return "suv"
    if "hatchback" in normalized_query or "两厢" in query:
        return "hatchback"
    if "sedan" in normalized_query:
        return "sedan"
    return None


def infer_usage(query: str, normalized_query: str) -> str | None:
    if any(token in normalized_query for token in ("family", "child", "children")) or "家用" in query or "家庭" in query:
        return "family"
    if any(token in normalized_query for token in ("first car", "new driver")) or "新手" in query:
        return "first_car"
    if any(token in normalized_query for token in ("uber", "rideshare")):
        return "rideshare"
    if any(token in normalized_query for token in ("city", "easy to park", "urban")) or "城市" in query:
        return "city"
    if "commut" in normalized_query or "通勤" in query:
        return "commute"
    return None


def infer_priority(query: str, normalized_query: str) -> str | None:
    if any(token in normalized_query for token in ("cheap to run", "low running", "fuel economy")) or "省油" in query or "省钱" in query:
        return "low_running_cost"
    if any(token in normalized_query for token in ("premium", "refined", "comfortable")) or "舒适" in query:
        return "premium_feel"
    if any(token in normalized_query for token in ("reliable", "reliability", "low risk", "safer")) or "省心" in query or "可靠" in query:
        return "reliability"
    if any(token in normalized_query for token in ("space", "practical", "boot")) or "空间" in query:
        return "space_practicality"
    return None


def normalize_market(value: str | None) -> str:
    market = str(value or "").strip().upper()
    if market not in SUPPORTED_MARKETS:
        raise ValueError(f"Unsupported market: {value}")
    return market


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


def fuel_group_matches(fuels: list[str], requested_fuel: str) -> bool:
    return any(fuel_matches(fuel, requested_fuel) for fuel in fuels)


def tag_matches_usage(tags: list[str], usage: str) -> bool:
    if usage == "family":
        return any(tag in tags for tag in ("family", "space"))
    if usage == "commute":
        return any(tag in tags for tag in ("commute", "value", "hybrid"))
    if usage == "city":
        return any(tag in tags for tag in ("commute", "value", "hatchback"))
    if usage == "first_car":
        return any(tag in tags for tag in ("first_car", "value", "commute"))
    return False


def tag_matches_priority(tags: list[str], priority: str) -> bool:
    if priority == "low_running_cost":
        return any(tag in tags for tag in ("hybrid", "electric", "value", "commute"))
    if priority == "premium_feel":
        return any(tag in tags for tag in ("comfort", "tech"))
    if priority == "reliability":
        return any(tag in tags for tag in ("reliability", "family"))
    if priority == "space_practicality":
        return any(tag in tags for tag in ("space", "family", "suv"))
    return False


def normalize_text(value: str | None) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9]+", " ", (value or "").lower())).strip()
