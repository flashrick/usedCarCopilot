from __future__ import annotations

import re
from time import perf_counter
from typing import Any

from app.db.connection import get_session
from app.db.orm import RequestLogRecord
from app.models.schemas import RecommendRequest
from app.retrieval.service import retrieve


SOURCE_TYPE_MAP = {
    "buying_guide": "buying_guide",
    "driving_review": "review",
    "inspection": "buying_guide",
    "maintenance": "maintenance",
    "owner_experience": "review",
}

RISK_PATTERNS = (
    (
        "Service history",
        "medium",
        ("service history", "service records", "service intervals", "service record"),
        "Verify service records before shortlisting this car.",
    ),
    (
        "Accident repair",
        "medium",
        ("accident repair", "body repair", "paint", "damage"),
        "Check for prior repair quality and signs of accident damage.",
    ),
    (
        "Used condition",
        "medium",
        ("used condition", "condition evidence", "clean service record", "neglected", "documentation"),
        "Treat used condition and documentation as deciding factors, especially for buyers who want a low-risk choice.",
    ),
    (
        "Trim and feature variation",
        "low",
        ("trim", "feature", "features", "equipment", "year"),
        "Compare trim differences, feature variation by year, and safety equipment before paying a premium.",
    ),
    (
        "Comfort or space trade-off",
        "low",
        ("comfort", "seat", "rear space", "boot space", "road noise"),
        "Confirm seat comfort, small car comfort, road noise, and usable space against the intended driving pattern.",
    ),
    (
        "Parking or body damage",
        "low",
        ("parking", "body repair", "paint", "panel gaps", "damage"),
        "Check parking damage and body repair signs during the walk-around inspection.",
    ),
    (
        "Hybrid system condition",
        "medium",
        ("hybrid battery", "hybrid system", "battery condition"),
        "Hybrid condition should be checked because the matched evidence raises it as a buying point.",
    ),
    (
        "Transmission behaviour",
        "medium",
        ("transmission behaviour", "transmission feel", "cvt", "gearbox"),
        "Road test the transmission and confirm smooth operation.",
    ),
    (
        "Tyres and brakes",
        "low",
        ("tyre", "tyres", "brake", "brakes"),
        "Inspect tyres and brakes because wear items affect the true purchase cost.",
    ),
    (
        "Suspension or warning lights",
        "medium",
        ("suspension", "warning lights", "warning light"),
        "Include suspension noise and dashboard warnings in the inspection.",
    ),
)


def recommend(request: RecommendRequest) -> dict[str, Any]:
    started_at = perf_counter()
    retrieval_limit = 20
    retrieval_request = request.model_copy(update={"limit": retrieval_limit})
    retrieval_response = retrieve(retrieval_request)

    filters = retrieval_response["applied_filters"]
    listings = retrieval_response["listings"]
    chunks = retrieval_response["chunks"]
    evidence: dict[str, dict[str, str]] = {}

    scored_cars = []
    for listing in listings:
        relevant_chunks = find_relevant_chunks(listing, chunks)
        risk_flags = build_risk_flags(listing, relevant_chunks)
        match_score = score_listing(listing, filters, relevant_chunks, risk_flags)

        scored_cars.append(
            {
                "listing_id": value_of(listing, "listing_id"),
                "title": value_of(listing, "title"),
                "match_score": match_score,
                "why_it_matches": build_reasons(listing, filters, relevant_chunks),
                "risk_flags": risk_flags,
                "price_commentary": build_price_commentary(listing, filters),
                "evidence_ids": [],
                "next_steps": build_next_steps(listing, risk_flags),
                "_listing": listing,
                "_chunks": relevant_chunks,
                "_model_key": model_key(listing),
                "_price": value_of(listing, "price"),
                "_mileage": value_of(listing, "mileage"),
            }
        )

    ranked_cars = sorted(
        scored_cars,
        key=lambda car: (-car["match_score"], car["_price"] is None, car["_price"] or 0, car["_mileage"] or 0),
    )
    recommended_cars = select_diverse_recommendations(ranked_cars, request.limit)
    for car in recommended_cars:
        car["evidence_ids"] = collect_evidence(car["_listing"], car["_chunks"], car["risk_flags"], evidence)
        car.pop("_listing", None)
        car.pop("_chunks", None)
        car.pop("_model_key", None)
        car.pop("_price", None)
        car.pop("_mileage", None)

    latency_ms = int((perf_counter() - started_at) * 1000)
    with get_session() as session:
        session.add(
            RequestLogRecord(
                endpoint="/recommend",
                query=request.query,
                filters=filters,
                listing_count=len(recommended_cars),
                knowledge_count=len(evidence),
                latency_ms=latency_ms,
            )
        )

    return {
        "query_summary": build_query_summary(request.query, filters),
        "recommended_cars": recommended_cars,
        "evidence": list(evidence.values()),
        "debug": {
            "retrieval_mode": retrieval_response["debug"].get("retrieval_mode"),
            "embedding_search_enabled": retrieval_response["debug"].get("embedding_search_enabled"),
            "embedding_model": retrieval_response["debug"].get("embedding_model"),
            "candidate_models": retrieval_response["debug"].get("candidate_models", []),
            "retrieved_listing_count": len(listings),
            "retrieved_chunk_count": len(chunks),
            "recommendation_mode": "deterministic_ranker_with_citations",
            "latency_ms": latency_ms,
        },
    }


def select_diverse_recommendations(ranked_cars: list[dict[str, Any]], limit: int) -> list[dict[str, Any]]:
    selected: list[dict[str, Any]] = []
    selected_ids: set[str] = set()
    seen_models: set[str] = set()

    for car in ranked_cars:
        model = car["_model_key"]
        if model in seen_models:
            continue
        selected.append(car)
        selected_ids.add(car["listing_id"])
        seen_models.add(model)
        if len(selected) >= limit:
            return selected

    for car in ranked_cars:
        if car["listing_id"] in selected_ids:
            continue
        selected.append(car)
        selected_ids.add(car["listing_id"])
        if len(selected) >= limit:
            break
    return selected


def collect_evidence(
    listing: Any,
    chunks: list[Any],
    risk_flags: list[dict[str, Any]],
    evidence: dict[str, dict[str, str]],
) -> list[str]:
    evidence_ids = [add_listing_evidence(listing, evidence)]
    chunks_by_evidence_id = {f"chunk:{value_of(chunk, 'chunk_id')}": chunk for chunk in chunks}
    cited_chunk_ids = [
        evidence_id
        for flag in risk_flags
        for evidence_id in flag.get("evidence_ids", [])
        if evidence_id.startswith("chunk:")
    ]
    selected_chunks = list(chunks[:3])
    selected_chunk_ids = {f"chunk:{value_of(chunk, 'chunk_id')}" for chunk in selected_chunks}
    for evidence_id in cited_chunk_ids:
        chunk = chunks_by_evidence_id.get(evidence_id)
        if chunk is not None and evidence_id not in selected_chunk_ids:
            selected_chunks.append(chunk)
            selected_chunk_ids.add(evidence_id)

    for chunk in selected_chunks:
        evidence_ids.append(add_chunk_evidence(chunk, evidence))
    return dedupe(evidence_ids)


def add_listing_evidence(listing: Any, evidence: dict[str, dict[str, str]]) -> str:
    listing_id = value_of(listing, "listing_id")
    evidence_id = f"listing:{listing_id}"
    if evidence_id not in evidence:
        facts = [
            value_of(listing, "title"),
            format_money(value_of(listing, "price")),
            format_km(value_of(listing, "mileage")),
            value_of(listing, "fuel_type"),
            value_of(listing, "body_type"),
            value_of(listing, "description"),
        ]
        evidence[evidence_id] = {
            "id": evidence_id,
            "source_type": "listing",
            "title": value_of(listing, "title"),
            "snippet": trim(" | ".join(str(fact) for fact in facts if fact), 320),
        }
    return evidence_id


def add_chunk_evidence(chunk: Any, evidence: dict[str, dict[str, str]]) -> str:
    chunk_id = value_of(chunk, "chunk_id")
    evidence_id = f"chunk:{chunk_id}"
    if evidence_id not in evidence:
        source_type = value_of(chunk, "source_type")
        evidence[evidence_id] = {
            "id": evidence_id,
            "source_type": SOURCE_TYPE_MAP.get(str(source_type), str(source_type or "buying_guide")),
            "title": value_of(chunk, "source_title"),
            "snippet": trim(value_of(chunk, "text") or "", 320),
        }
    return evidence_id


def find_relevant_chunks(listing: Any, chunks: list[Any]) -> list[Any]:
    brand = normalize(value_of(listing, "brand"))
    model = normalize(value_of(listing, "model"))
    matching = [
        chunk
        for chunk in chunks
        if normalize(value_of(chunk, "brand")) == brand and normalize(value_of(chunk, "model")) == model
    ]
    if matching:
        return matching
    return chunks[:2]


def score_listing(listing: Any, filters: dict[str, Any], chunks: list[Any], risk_flags: list[dict[str, Any]]) -> int:
    score = 52
    price = value_of(listing, "price")
    max_price = filters.get("max_price")
    if price is None:
        score -= 10
    elif max_price is not None and price <= max_price:
        score += 18
        if price <= max_price * 0.85:
            score += 5
    elif max_price is None:
        score += 4
    else:
        score -= 18

    mileage = value_of(listing, "mileage")
    if mileage is not None:
        if mileage <= 90_000:
            score += 11
        elif mileage <= 130_000:
            score += 7
        elif mileage <= 170_000:
            score += 1
        else:
            score -= 8

    year = value_of(listing, "year")
    if year is not None:
        if year >= 2017:
            score += 9
        elif year >= 2013:
            score += 5
        elif year <= 2010:
            score -= 4

    if filters.get("body_type") and normalize(value_of(listing, "body_type")) == normalize(filters["body_type"]):
        score += 5
    if filters.get("brand") and normalize(value_of(listing, "brand")) == normalize(filters["brand"]):
        score += 4
    if filters.get("prefer_hybrid") and "hybrid" in normalize(value_of(listing, "fuel_type")):
        score += 8
    if filters.get("prefer_premium") and year and year >= 2015:
        score += 5
    if filters.get("priority") == "low_risk":
        preferred_low_risk_models = {
            ("toyota", "aqua"): 14,
            ("honda", "fit"): 18,
            ("mazda", "mazda3"): 12,
        }
        listing_model = (normalize(value_of(listing, "brand")), normalize(value_of(listing, "model")))
        if listing_model in preferred_low_risk_models:
            score += preferred_low_risk_models[listing_model]
        if normalize(value_of(listing, "body_type")) == "suv":
            score -= 8
        if price is not None and price > 20_000:
            score -= 5
    if filters.get("priority") == "safer_choice" and year is not None and year <= 2011:
        score -= 3
    if chunks:
        score += min(10, 3 * len(chunks))

    risk_penalty = sum({"low": 1, "medium": 3, "high": 7}.get(flag["severity"], 2) for flag in risk_flags)
    return max(0, min(100, score - risk_penalty))


def build_reasons(listing: Any, filters: dict[str, Any], chunks: list[Any]) -> list[str]:
    reasons: list[str] = []
    price = value_of(listing, "price")
    max_price = filters.get("max_price")
    if price is not None and max_price is not None and price <= max_price:
        reasons.append(f"Fits the budget at {format_money(price)} against a {format_money(max_price)} ceiling.")
    elif price is not None:
        reasons.append(f"Has a visible listing price of {format_money(price)} for comparison.")

    location = value_of(listing, "location")
    body_type = value_of(listing, "body_type")
    if location:
        reasons.append(f"Available in {location}, matching the local search area.")
    if body_type:
        reasons.append(f"Matches a {body_type} body style.")

    mileage = value_of(listing, "mileage")
    year = value_of(listing, "year")
    if mileage is not None and mileage <= 130_000:
        reasons.append(f"Mileage is relatively usable for the seed set at {format_km(mileage)}.")
    if year is not None and year >= 2015:
        reasons.append(f"The {year} model year is newer than many budget candidates in the current data.")
    if filters.get("prefer_hybrid") and "hybrid" in normalize(value_of(listing, "fuel_type")):
        reasons.append("Hybrid fuel type supports the low-running-cost intent.")

    evidence_reason = strongest_evidence_reason(chunks)
    if evidence_reason:
        reasons.append(evidence_reason)

    return reasons[:5] or ["Ranked from the available structured listing data and retrieved model evidence."]


def strongest_evidence_reason(chunks: list[Any]) -> str | None:
    for chunk in chunks:
        text = value_of(chunk, "text") or ""
        normalized = normalize(text)
        if "city" in normalized or "parking" in normalized:
            return "Retrieved model evidence supports city use or easy parking."
        if "family" in normalized or "space" in normalized or "boot" in normalized:
            return "Retrieved model evidence discusses practical space or family fit."
        if "fuel" in normalized or "running cost" in normalized or "hybrid" in normalized:
            return "Retrieved model evidence supports running-cost evaluation."
        if "comfort" in normalized or "highway" in normalized:
            return "Retrieved model evidence discusses comfort or highway use."
    return None


def build_risk_flags(listing: Any, chunks: list[Any]) -> list[dict[str, Any]]:
    flags: list[dict[str, Any]] = []
    listing_evidence_id = f"listing:{value_of(listing, 'listing_id')}"
    mileage = value_of(listing, "mileage")
    if mileage is not None and mileage >= 180_000:
        flags.append(
            {
                "label": "High mileage",
                "severity": "high",
                "reason": f"The listing shows {format_km(mileage)}, so condition evidence matters more than model reputation.",
                "evidence_ids": [listing_evidence_id],
            }
        )
    elif mileage is not None and mileage >= 140_000:
        flags.append(
            {
                "label": "Higher mileage",
                "severity": "medium",
                "reason": f"The listing shows {format_km(mileage)}, which should trigger closer service and wear checks.",
                "evidence_ids": [listing_evidence_id],
            }
        )

    year = value_of(listing, "year")
    if year is not None and year <= 2010:
        flags.append(
            {
                "label": "Older vehicle age",
                "severity": "medium",
                "reason": f"The listing is a {year} vehicle, so age-related wear and safety equipment variation should be checked.",
                "evidence_ids": [listing_evidence_id],
            }
        )

    owner_count = extract_owner_count(value_of(listing, "description"))
    if owner_count and owner_count >= 3:
        flags.append(
            {
                "label": "Multiple previous owners",
                "severity": "medium",
                "reason": f"The listing text mentions {owner_count} owners, so documentation and condition checks matter.",
                "evidence_ids": [listing_evidence_id],
            }
        )

    if value_of(listing, "price") is None:
        flags.append(
            {
                "label": "Missing listing price",
                "severity": "medium",
                "reason": "The listing has no visible price, so it cannot be compared cleanly on value.",
                "evidence_ids": [listing_evidence_id],
            }
        )

    seen_labels = {flag["label"] for flag in flags}
    for label, severity, terms, reason in RISK_PATTERNS:
        chunk_ids = [
            f"chunk:{value_of(chunk, 'chunk_id')}"
            for chunk in chunks
            if any(term in normalize(value_of(chunk, "text")) for term in terms)
        ]
        if chunk_ids and label not in seen_labels:
            flags.append(
                {
                    "label": label,
                    "severity": severity,
                    "reason": reason,
                    "evidence_ids": dedupe(chunk_ids)[:2],
                }
            )
            seen_labels.add(label)
        if len(flags) >= 5:
            break
    return flags


def build_price_commentary(listing: Any, filters: dict[str, Any]) -> str:
    price = value_of(listing, "price")
    max_price = filters.get("max_price")
    if price is None:
        return "No price is visible in the seed listing, so value cannot be judged until the seller confirms it."
    if max_price is None:
        return f"Listed at {format_money(price)}. Compare against similar year, mileage, and condition examples."
    if price <= max_price:
        headroom = max_price - price
        return f"Listed at {format_money(price)}, which is {format_money(headroom)} under the stated budget."
    return f"Listed at {format_money(price)}, which is above the stated {format_money(max_price)} budget."


def build_next_steps(listing: Any, risk_flags: list[dict[str, Any]]) -> list[str]:
    steps = [
        "Ask for service history and ownership documentation.",
        "Book a pre-purchase inspection before committing.",
    ]
    risk_labels = {normalize(flag["label"]) for flag in risk_flags}
    if "hybrid system condition" in risk_labels:
        steps.append("Ask for hybrid battery or hybrid-system health evidence.")
    if "transmission behaviour" in risk_labels:
        steps.append("Road test from cold and check for hesitation, shudder, or warning lights.")
    if "tyres and brakes" in risk_labels or "high mileage" in risk_labels or "higher mileage" in risk_labels:
        steps.append("Use tyre, brake, and wear-item findings when negotiating price.")
    return steps[:4]


def build_query_summary(query: str | None, filters: dict[str, Any]) -> dict[str, Any]:
    preferences: list[str] = []
    if filters.get("location"):
        preferences.append(f"Location: {filters['location']}")
    if filters.get("brand"):
        preferences.append(f"Brand: {filters['brand']}")
    elif filters.get("brands"):
        preferences.append("Brands: " + ", ".join(filters["brands"]))
    if filters.get("body_type"):
        preferences.append(f"Body type: {filters['body_type']}")
    if filters.get("models"):
        preferences.append("Models: " + ", ".join(filters["models"]))
    if filters.get("prefer_hybrid"):
        preferences.append("Low running costs or hybrid preference")
    if filters.get("prefer_premium"):
        preferences.append("More premium or comfortable feel")

    return {
        "budget": f"Up to {format_money(filters['max_price'])}" if filters.get("max_price") else "Not specified",
        "usage": infer_usage(query or ""),
        "preferences": preferences,
    }


def infer_usage(query: str) -> str:
    normalized = normalize(query)
    if "uber" in normalized or "rideshare" in normalized:
        return "rideshare or high-use driving"
    if "family" in normalized or "child" in normalized or "children" in normalized:
        return "family and everyday use"
    if "highway" in normalized or "hamilton" in normalized:
        return "highway or intercity driving"
    if "city" in normalized or "park" in normalized or "commut" in normalized:
        return "city commuting"
    if "first car" in normalized or "new driver" in normalized:
        return "first car"
    return "general used-car shortlisting"


def extract_owner_count(description: str | None) -> int | None:
    if not description:
        return None
    match = re.search(r"had\s+([0-9]+)\s+owners?", description, flags=re.IGNORECASE)
    if not match:
        return None
    return int(match.group(1))


def value_of(item: Any, key: str, default: Any = None) -> Any:
    if isinstance(item, dict):
        return item.get(key, default)
    return getattr(item, key, default)


def model_key(listing: Any) -> str:
    return f"{normalize(value_of(listing, 'brand'))}:{normalize(value_of(listing, 'model'))}"


def normalize(value: Any) -> str:
    text = "" if value is None else str(value).lower()
    text = text.replace("-", " ")
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def format_money(value: int | None) -> str | None:
    if value is None:
        return None
    return f"${value:,.0f}"


def format_km(value: int | None) -> str | None:
    if value is None:
        return None
    return f"{value:,.0f} km"


def trim(text: str, limit: int) -> str:
    normalized = re.sub(r"\s+", " ", text).strip()
    if len(normalized) <= limit:
        return normalized
    return normalized[: limit - 3].rstrip() + "..."


def dedupe(values: list[str]) -> list[str]:
    output: list[str] = []
    for value in values:
        if value and value not in output:
            output.append(value)
    return output
