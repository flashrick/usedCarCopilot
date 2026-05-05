from __future__ import annotations

import json
from time import perf_counter
from typing import Any, Protocol
import urllib.error
import urllib.request

from sqlalchemy import and_, or_, select

from app.core.config import get_settings
from app.db.connection import get_session
from app.db.orm import KnowledgeSourceRecord, RequestLogRecord, VehicleProfileRecord
from app.models.schemas import RecommendRequest, RetrieveRequest
from app.retrieval.service import infer_filters, load_relevant_knowledge, retrieve_semantic_chunks, score_profile


OPENAI_DEFAULT_MODEL = "gpt-5-mini"
COMPATIBLE_PROVIDER_DEFAULT_MODELS = {
    "deepseek": "deepseek-chat",
    "qwen": "qwen-plus",
    "kimi": "kimi-k2.6",
}


RECOMMENDATION_OUTPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": ["query_summary", "recommended_profiles"],
    "properties": {
        "query_summary": {
            "type": "object",
            "additionalProperties": False,
            "required": ["budget", "usage", "preferences"],
            "properties": {
                "budget": {"type": "string"},
                "usage": {"type": "string"},
                "preferences": {"type": "array", "items": {"type": "string"}},
            },
        },
        "recommended_profiles": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": [
                    "profile_id",
                    "title",
                    "match_score",
                    "powertrain_summary",
                    "why_it_matches",
                    "trade_offs",
                    "risk_flags",
                    "valuation_summary",
                    "evidence_ids",
                    "next_steps",
                ],
                "properties": {
                    "profile_id": {"type": "string"},
                    "title": {"type": "string"},
                    "match_score": {"type": "integer", "minimum": 0, "maximum": 100},
                    "powertrain_summary": {"type": "string"},
                    "why_it_matches": {"type": "array", "items": {"type": "string"}},
                    "trade_offs": {"type": "array", "items": {"type": "string"}},
                    "risk_flags": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "additionalProperties": False,
                            "required": ["label", "severity", "reason", "evidence_ids"],
                            "properties": {
                                "label": {"type": "string"},
                                "severity": {"type": "string", "enum": ["low", "medium", "high"]},
                                "reason": {"type": "string"},
                                "evidence_ids": {"type": "array", "items": {"type": "string"}},
                            },
                        },
                    },
                    "valuation_summary": {"type": "string"},
                    "evidence_ids": {"type": "array", "items": {"type": "string"}},
                    "next_steps": {"type": "array", "items": {"type": "string"}},
                },
            },
        },
    },
}


class RecommendationGenerator(Protocol):
    name: str
    model: str

    def generate(self, request: RecommendRequest, retrieval_response: dict[str, Any]) -> dict[str, Any]:
        """Return the stable recommendation payload fields after retrieval."""


class RecommendationRequestError(ValueError):
    """Raised when the selected-profile recommendation request is invalid."""


class DeterministicRecommendationGenerator:
    name = "deterministic"

    def __init__(self, model: str = "deterministic_variant_recommender_v1") -> None:
        self.model = model

    def generate(self, request: RecommendRequest, retrieval_response: dict[str, Any]) -> dict[str, Any]:
        filters = retrieval_response["applied_filters"]
        profiles = retrieval_response["vehicle_profiles"]
        chunks = retrieval_response["chunks"]
        evidence: dict[str, dict[str, str]] = {}
        scored_profiles: list[dict[str, Any]] = []

        for profile in profiles:
            profile_score = max(35, min(99, score_profile(profile, filters)))
            profile_chunks = find_relevant_chunks(profile, chunks)
            profile_evidence_id = add_profile_evidence(profile, evidence)
            chunk_evidence_ids = [add_chunk_evidence(chunk, evidence) for chunk in profile_chunks[:2]]
            risk_flags = build_risk_flags(profile, profile_chunks, chunk_evidence_ids)
            evidence_ids = [profile_evidence_id, *chunk_evidence_ids]

            scored_profiles.append(
                {
                    "profile_id": profile.profile_id,
                    "title": profile.title,
                    "match_score": profile_score,
                    "powertrain_summary": build_powertrain_summary(profile),
                    "why_it_matches": build_reasons(profile, filters),
                    "trade_offs": build_trade_offs(profile),
                    "risk_flags": risk_flags,
                    "valuation_summary": build_valuation_summary(profile),
                    "evidence_ids": evidence_ids,
                    "next_steps": build_next_steps(profile, risk_flags),
                    "_rank_key": (-profile_score, profile.estimated_price_mid_nzd or 10**9, profile.profile_id),
                }
            )

        ranked_profiles = sorted(scored_profiles, key=lambda item: item["_rank_key"])
        for item in ranked_profiles:
            item.pop("_rank_key", None)

        return {
            "query_summary": build_query_summary(request.query, filters),
            "recommended_profiles": ranked_profiles,
            "evidence": list(evidence.values()),
        }


class OpenAIRecommendationGenerator:
    name = "openai"

    def __init__(
        self,
        api_key: str | None,
        model: str = OPENAI_DEFAULT_MODEL,
        base_url: str = "https://api.openai.com/v1",
        timeout_seconds: float = 30,
    ) -> None:
        self.api_key = api_key
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds
        self.fallback_generator = DeterministicRecommendationGenerator()

    def generate(self, request: RecommendRequest, retrieval_response: dict[str, Any]) -> dict[str, Any]:
        draft = self.fallback_generator.generate(request, retrieval_response)
        if not self.api_key:
            return with_generation_metadata(draft, {"source": "deterministic_fallback", "fallback_reason": "missing_openai_api_key"})

        try:
            generated = self._generate_with_openai(request, retrieval_response, draft)
            validated = validate_llm_recommendation_payload(generated, draft)
        except Exception as exc:
            return with_generation_metadata(
                draft,
                {"source": "deterministic_fallback", "fallback_reason": f"{type(exc).__name__}: {exc}"},
            )

        return with_generation_metadata(validated, {"source": "openai"})

    def _generate_with_openai(
        self,
        request: RecommendRequest,
        retrieval_response: dict[str, Any],
        draft: dict[str, Any],
    ) -> dict[str, Any]:
        payload = {
            "model": self.model,
            "input": [
                {
                    "role": "system",
                    "content": [
                        {
                            "type": "input_text",
                            "text": (
                                "You are a used-car variant decision support generator. "
                                "Return grounded JSON only. Keep the same profile_id order, titles, match_score values, "
                                "and evidence_ids from the draft. Do not invent profiles or citations. "
                                "Rewrite reasons, trade-offs, risks, valuation wording, and next steps only when the supplied evidence supports it."
                            ),
                        }
                    ],
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "input_text",
                            "text": json.dumps(
                                {
                                    "query": request.query,
                                    "filters": retrieval_response.get("applied_filters", {}),
                                    "draft_recommendation": draft,
                                    "available_evidence": draft.get("evidence", []),
                                },
                                ensure_ascii=True,
                            ),
                        }
                    ],
                },
            ],
            "text": {
                "format": {
                    "type": "json_schema",
                    "name": "vehicle_profile_recommendation",
                    "schema": RECOMMENDATION_OUTPUT_SCHEMA,
                    "strict": True,
                }
            },
        }
        response = self._post_response(payload)
        response_text = extract_response_text(response)
        if not response_text:
            raise ValueError("OpenAI response did not contain output text")
        return json.loads(response_text)

    def _post_response(self, payload: dict[str, Any]) -> dict[str, Any]:
        request = urllib.request.Request(
            f"{self.base_url}/responses",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"OpenAI request failed with HTTP {exc.code}: {trim(body, 240)}") from exc
        except urllib.error.URLError as exc:
            raise RuntimeError(f"OpenAI request failed: {exc}") from exc


class OpenAICompatibleChatRecommendationGenerator:
    def __init__(
        self,
        name: str,
        api_key: str | None,
        model: str,
        base_url: str,
        timeout_seconds: float = 30,
    ) -> None:
        self.name = name
        self.api_key = api_key
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds
        self.fallback_generator = DeterministicRecommendationGenerator()

    def generate(self, request: RecommendRequest, retrieval_response: dict[str, Any]) -> dict[str, Any]:
        draft = self.fallback_generator.generate(request, retrieval_response)
        if not self.api_key:
            return with_generation_metadata(
                draft,
                {"source": "deterministic_fallback", "fallback_reason": f"missing_{self.name}_api_key"},
            )

        try:
            generated = self._generate_with_chat_completions(request, retrieval_response, draft)
            validated = validate_llm_recommendation_payload(generated, draft)
        except Exception as exc:
            return with_generation_metadata(
                draft,
                {"source": "deterministic_fallback", "fallback_reason": f"{type(exc).__name__}: {exc}"},
            )

        return with_generation_metadata(validated, {"source": self.name})

    def _generate_with_chat_completions(
        self,
        request: RecommendRequest,
        retrieval_response: dict[str, Any],
        draft: dict[str, Any],
    ) -> dict[str, Any]:
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are a used-car variant decision support generator. Return valid JSON only. "
                        "The JSON object must contain query_summary and recommended_profiles. "
                        "Keep the same profile_id order, titles, match_score values, and evidence_ids from the draft. "
                        "Do not invent profiles, citations, or evidence ids. "
                        "Rewrite reasons, trade-offs, valuation commentary, and next steps only when supplied evidence supports it."
                    ),
                },
                {
                    "role": "user",
                    "content": json.dumps(
                        {
                            "query": request.query,
                            "filters": retrieval_response.get("applied_filters", {}),
                            "draft_recommendation": draft,
                            "available_evidence": draft.get("evidence", []),
                        },
                        ensure_ascii=True,
                    ),
                },
            ],
            "response_format": {"type": "json_object"},
        }
        response = self._post_chat_completion(payload)
        response_text = extract_chat_completion_text(response)
        if not response_text:
            raise ValueError(f"{self.name} response did not contain message content")
        return json.loads(response_text)

    def _post_chat_completion(self, payload: dict[str, Any]) -> dict[str, Any]:
        request = urllib.request.Request(
            f"{self.base_url}/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"{self.name} request failed with HTTP {exc.code}: {trim(body, 240)}") from exc
        except urllib.error.URLError as exc:
            raise RuntimeError(f"{self.name} request failed: {exc}") from exc


def recommend(request: RecommendRequest) -> dict[str, Any]:
    started_at = perf_counter()
    settings = get_settings()
    generator = get_recommendation_generator(
        settings.recommendation_provider,
        settings.recommendation_model,
        openai_api_key=settings.openai_api_key,
        openai_base_url=settings.openai_base_url,
        openai_timeout_seconds=settings.openai_timeout_seconds,
        deepseek_api_key=settings.deepseek_api_key,
        deepseek_base_url=settings.deepseek_base_url,
        qwen_api_key=settings.qwen_api_key,
        qwen_base_url=settings.qwen_base_url,
        kimi_api_key=settings.kimi_api_key,
        kimi_base_url=settings.kimi_base_url,
    )

    with get_session() as session:
        retrieval_response = build_selected_retrieval_response(session, request)
        generated = generator.generate(request, retrieval_response)
        generation_metadata = generated.pop("_generation_metadata", {})
        latency_ms = int((perf_counter() - started_at) * 1000)
        session.add(
            RequestLogRecord(
                endpoint="/recommend",
                query=request.query,
                filters=retrieval_response["applied_filters"],
                listing_count=0,
                profile_count=len(generated["recommended_profiles"]),
                knowledge_count=len(generated["evidence"]),
                latency_ms=latency_ms,
            )
        )

    return {
        "query_summary": generated["query_summary"],
        "recommended_profiles": generated["recommended_profiles"],
        "evidence": generated["evidence"],
        "debug": {
            "retrieval_mode": retrieval_response["debug"].get("retrieval_mode"),
            "embedding_search_enabled": retrieval_response["debug"].get("embedding_search_enabled"),
            "embedding_model": retrieval_response["debug"].get("embedding_model"),
            "candidate_models": retrieval_response["debug"].get("candidate_models", []),
            "selected_profile_ids": retrieval_response["debug"].get("selected_profile_ids", []),
            "selected_profile_count": retrieval_response["debug"].get("selected_profile_count", 0),
            "retrieved_profile_count": len(retrieval_response["vehicle_profiles"]),
            "retrieved_chunk_count": len(retrieval_response["chunks"]),
            "recommendation_provider": generator.name,
            "recommendation_mode": generator.model,
            "generation_source": generation_metadata.get("source", generator.name),
            "generation_fallback_reason": generation_metadata.get("fallback_reason"),
            "latency_ms": latency_ms,
        },
    }


def build_selected_retrieval_response(session: Any, request: RecommendRequest) -> dict[str, Any]:
    query, selected_profile_ids = validate_recommend_request(request)
    profiles = load_selected_profiles(session, selected_profile_ids)
    selected_markets = {profile.market for profile in profiles}
    if len(selected_markets) != 1:
        raise RecommendationRequestError("selected profile ids must belong to the same market")
    market = selected_markets.pop()
    filters = infer_filters(RetrieveRequest(query=query, market=market, limit=len(selected_profile_ids)))
    filters["selected_profile_ids"] = selected_profile_ids
    candidate_pairs = dedupe_model_pairs(profiles)
    knowledge = load_selected_knowledge(session, market, selected_profile_ids, candidate_pairs)
    semantic_chunks = retrieve_semantic_chunks(
        session=session,
        query=query,
        filters=filters,
        candidate_pairs=candidate_pairs,
        selected_profile_ids=selected_profile_ids,
        limit=max(len(selected_profile_ids), 4),
    )
    return {
        "query": query,
        "applied_filters": filters,
        "vehicle_profiles": profiles,
        "knowledge": knowledge,
        "chunks": semantic_chunks,
        "debug": {
            "candidate_models": [f"{brand} {model}" for brand, model in candidate_pairs],
            "selected_profile_ids": selected_profile_ids,
            "selected_profile_count": len(selected_profile_ids),
            "market": market,
            "retrieval_mode": "selected_profiles_plus_semantic_chunks",
            "embedding_search_enabled": bool(semantic_chunks),
            "embedding_model": get_settings().embedding_model,
        },
    }


def validate_recommend_request(request: RecommendRequest) -> tuple[str, list[str]]:
    query = (request.query or "").strip()
    if not query:
        raise RecommendationRequestError("query is required")
    selected_profile_ids = [profile_id.strip() for profile_id in request.selected_profile_ids if profile_id.strip()]
    if len(selected_profile_ids) < 2:
        raise RecommendationRequestError("select at least 2 profile ids")
    if len(selected_profile_ids) > 4:
        raise RecommendationRequestError("select no more than 4 profile ids")
    if len(set(selected_profile_ids)) != len(selected_profile_ids):
        raise RecommendationRequestError("selected profile ids must be unique")
    return query, selected_profile_ids


def load_selected_profiles(session: Any, selected_profile_ids: list[str]) -> list[VehicleProfileRecord]:
    rows = list(session.scalars(select(VehicleProfileRecord).where(VehicleProfileRecord.profile_id.in_(selected_profile_ids))))
    profiles_by_id = {row.profile_id: row for row in rows}
    missing_profile_ids = [profile_id for profile_id in selected_profile_ids if profile_id not in profiles_by_id]
    if missing_profile_ids:
        raise RecommendationRequestError("selected profile ids not found: " + ", ".join(missing_profile_ids))
    return [profiles_by_id[profile_id] for profile_id in selected_profile_ids]


def load_selected_knowledge(
    session: Any,
    market: str,
    selected_profile_ids: list[str],
    candidate_pairs: list[tuple[str, str]],
) -> list[KnowledgeSourceRecord]:
    return load_relevant_knowledge(session, market, selected_profile_ids, candidate_pairs, max(len(candidate_pairs), 4))


def get_recommendation_generator(
    provider_name: str | None = None,
    model: str | None = None,
    *,
    openai_api_key: str | None = None,
    openai_base_url: str = "https://api.openai.com/v1",
    openai_timeout_seconds: float = 30,
    deepseek_api_key: str | None = None,
    deepseek_base_url: str = "https://api.deepseek.com",
    qwen_api_key: str | None = None,
    qwen_base_url: str = "https://dashscope-intl.aliyuncs.com/compatible-mode/v1",
    kimi_api_key: str | None = None,
    kimi_base_url: str = "https://api.moonshot.ai/v1",
) -> RecommendationGenerator:
    provider = normalize(provider_name or "deterministic")
    if provider in {"deterministic", "local deterministic"}:
        return DeterministicRecommendationGenerator(model or "deterministic_variant_recommender_v1")
    if provider in {"openai", "openai responses"}:
        selected_model = model if model and model != "deterministic_variant_recommender_v1" else OPENAI_DEFAULT_MODEL
        return OpenAIRecommendationGenerator(
            api_key=openai_api_key,
            model=selected_model,
            base_url=openai_base_url,
            timeout_seconds=openai_timeout_seconds,
        )
    if provider in {"deepseek", "qwen", "kimi"}:
        defaults = {
            "deepseek": (deepseek_api_key, deepseek_base_url),
            "qwen": (qwen_api_key, qwen_base_url),
            "kimi": (kimi_api_key, kimi_base_url),
        }
        api_key, base_url = defaults[provider]
        return OpenAICompatibleChatRecommendationGenerator(
            name=provider,
            api_key=api_key,
            model=selected_external_model(model, COMPATIBLE_PROVIDER_DEFAULT_MODELS[provider]),
            base_url=base_url,
            timeout_seconds=openai_timeout_seconds,
        )
    raise ValueError(f"Unsupported recommendation provider: {provider_name}")


def find_relevant_chunks(profile: VehicleProfileRecord, chunks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    matched = [
        chunk
        for chunk in chunks
        if chunk.get("profile_id") == profile.profile_id or (chunk.get("brand") == profile.brand and chunk.get("model") == profile.model)
    ]
    return matched[:3]


def build_query_summary(query: str | None, filters: dict[str, Any]) -> dict[str, Any]:
    budget = filters.get("budget_max")
    usage = filters.get("usage") or "general used-car profile selection"
    preferences = [value for value in [filters.get("fuel_type"), filters.get("body_type"), filters.get("transmission"), filters.get("priority")] if value]
    market = str(filters.get("market") or "US")
    return {
        "budget": format_budget_summary(budget, market),
        "usage": usage.replace("_", " "),
        "preferences": [str(item).replace("_", " ") for item in preferences],
    }


def build_powertrain_summary(profile: VehicleProfileRecord) -> str:
    power = f"{profile.power_kw}kW" if profile.power_kw else (f"{profile.power_hp}hp" if profile.power_hp else "power output not stated")
    displacement = f"{profile.displacement_l:.1f}L" if profile.displacement_l else profile.engine_description
    return f"{displacement} · {profile.transmission.upper()} · {profile.fuel_type.title()} · {power}"


def build_reasons(profile: VehicleProfileRecord, filters: dict[str, Any]) -> list[str]:
    reasons = [profile.suitability_summary or "Strong fit for general used-car profile selection."]
    if filters.get("budget_max") and profile.estimated_price_mid_nzd and profile.estimated_price_mid_nzd <= filters["budget_max"]:
        reasons.append("Estimated market midpoint stays inside the current budget target.")
    if filters.get("priority") == "low_running_cost" and (profile.fuel_consumption_l_per_100km or 99) <= 6.0:
        reasons.append("Fuel economy is favorable for a running-cost-sensitive buyer.")
    if filters.get("priority") == "premium_feel":
        reasons.append(profile.nvh_summary or "This profile leans more refined than the cheaper mainstream alternatives.")
    else:
        reasons.append(profile.comfort_summary or "Comfort and usability align with the intended daily use.")
    return dedupe_non_empty(reasons)


def build_trade_offs(profile: VehicleProfileRecord) -> list[str]:
    trade_offs = []
    if profile.body_type == "suv":
        trade_offs.append("SUV practicality comes with higher tyre, brake, and fuel exposure than a small hatchback.")
    if "hybrid" in (profile.fuel_type or "").lower():
        trade_offs.append("Lower fuel spend is attractive, but hybrid-system condition matters more than the badge alone.")
    if (profile.fuel_consumption_l_per_100km or 0) >= 7.5:
        trade_offs.append("Running costs will be higher than the most efficient hatchback options in the shortlist.")
    if profile.maintenance_cost_band in {"medium_high", "high"}:
        trade_offs.append("This version needs stronger maintenance evidence to justify its premium or complexity.")
    trade_offs.append(profile.space_summary or "Always match cabin and cargo space to the real use case, not just the body style.")
    return dedupe_non_empty(trade_offs)


def build_risk_flags(
    profile: VehicleProfileRecord,
    chunks: list[dict[str, Any]],
    chunk_evidence_ids: list[str],
) -> list[dict[str, Any]]:
    flags: list[dict[str, Any]] = []
    maintenance_band = (profile.maintenance_cost_band or "").lower()
    if maintenance_band in {"medium_high", "high"}:
        flags.append(
            {
                "label": "Maintenance sensitivity",
                "severity": "medium",
                "reason": "This variant needs stronger service evidence because running-cost and complexity risk are higher than the simplest shortlist options.",
                "evidence_ids": chunk_evidence_ids or [f"profile:{profile.profile_id}"],
            }
        )
    if "hybrid" in (profile.fuel_type or "").lower():
        flags.append(
            {
                "label": "Hybrid system check",
                "severity": "medium",
                "reason": "Battery health, warning lights, and hybrid maintenance history should be verified before treating fuel savings as guaranteed value.",
                "evidence_ids": chunk_evidence_ids or [f"profile:{profile.profile_id}"],
            }
        )
    if profile.body_type == "suv":
        flags.append(
            {
                "label": "Higher wear-item cost",
                "severity": "low",
                "reason": "SUV profiles usually carry higher tyre, brake, and suspension spend than smaller commuter profiles.",
                "evidence_ids": [f"profile:{profile.profile_id}"],
            }
        )
    if not flags:
        flags.append(
            {
                "label": "Routine used-car checks",
                "severity": "low",
                "reason": "Service history, tyres, brakes, and body condition still matter even on stronger-looking variants.",
                "evidence_ids": chunk_evidence_ids or [f"profile:{profile.profile_id}"],
            }
        )
    return flags


def build_valuation_summary(profile: VehicleProfileRecord) -> str:
    if profile.estimated_price_mid_nzd is None:
        return "Deterministic valuation range unavailable."
    currency = market_currency_code(profile.market or profile.valuation_market)
    symbol = {"USD": "$", "CNY": "CNY ", "NZD": "NZ$"}.get(currency, f"{currency} ")
    return (
        f"Estimated {profile.market} fair range: {symbol}{profile.estimated_price_min_nzd:,}-{symbol}{profile.estimated_price_max_nzd:,} "
        f"(midpoint {symbol}{profile.estimated_price_mid_nzd:,}) for a good-condition used example."
    )


def build_next_steps(profile: VehicleProfileRecord, risk_flags: list[dict[str, Any]]) -> list[str]:
    steps = [
        "Confirm service history and version-specific equipment before shopping the market.",
        "Use the valuation band as a negotiation anchor, not as a guaranteed ask price.",
        "Shortlist real cars only after this profile's gearbox, fuel system, and space trade-offs still fit.",
    ]
    if any(flag["label"] == "Hybrid system check" for flag in risk_flags):
        steps.append("Prioritize hybrid battery health, warning-light scan, and cooling-system service evidence.")
    return dedupe_non_empty(steps)


def format_budget_summary(budget: Any, market: str) -> str:
    if not isinstance(budget, int):
        return "Flexible budget"
    currency = market_currency_code(market)
    if currency == "CNY":
        return f"Under CNY {budget:,}"
    if currency == "USD":
        return f"Under ${budget:,}"
    return f"Under NZ${budget:,}"


def market_currency_code(market: str | None) -> str:
    normalized = str(market or "").upper()
    if normalized == "CN":
        return "CNY"
    if normalized == "US":
        return "USD"
    return "NZD"


def add_profile_evidence(profile: VehicleProfileRecord, evidence: dict[str, dict[str, str]]) -> str:
    evidence_id = f"profile:{profile.profile_id}"
    evidence.setdefault(
        evidence_id,
        {
            "id": evidence_id,
            "source_type": "vehicle_profile",
            "title": profile.title,
            "snippet": f"{profile.engine_description}; {profile.suitability_summary or profile.comfort_summary or profile.space_summary or profile.reliability_summary or ''}",
        },
    )
    return evidence_id


def add_chunk_evidence(chunk: dict[str, Any], evidence: dict[str, dict[str, str]]) -> str:
    evidence_id = f"chunk:{chunk['chunk_id']}"
    evidence.setdefault(
        evidence_id,
        {
            "id": evidence_id,
            "source_type": str(chunk["source_type"]),
            "title": str(chunk["source_title"]),
            "snippet": trim(str(chunk["text"]), 180),
        },
    )
    return evidence_id


def dedupe_model_pairs(profiles: list[VehicleProfileRecord]) -> list[tuple[str, str]]:
    pairs: list[tuple[str, str]] = []
    for profile in profiles:
        pair = (profile.brand, profile.model)
        if pair not in pairs:
            pairs.append(pair)
    return pairs


def validate_llm_recommendation_payload(generated: dict[str, Any], draft: dict[str, Any]) -> dict[str, Any]:
    draft_profiles = draft.get("recommended_profiles", [])
    generated_profiles = generated.get("recommended_profiles", [])
    if len(generated_profiles) != len(draft_profiles):
        raise ValueError("generated recommendation count does not match draft")

    evidence = draft.get("evidence", [])
    evidence_ids = {item["id"] for item in evidence}
    validated_profiles: list[dict[str, Any]] = []
    for generated_profile, draft_profile in zip(generated_profiles, draft_profiles, strict=True):
        if generated_profile.get("profile_id") != draft_profile.get("profile_id"):
            raise ValueError("generated profile order or ids changed")
        if generated_profile.get("title") != draft_profile.get("title"):
            raise ValueError("generated profile title changed")
        if generated_profile.get("match_score") != draft_profile.get("match_score"):
            raise ValueError("generated match score changed")

        profile_evidence_ids = list(generated_profile.get("evidence_ids", []))
        if not profile_evidence_ids or not set(profile_evidence_ids).issubset(evidence_ids):
            raise ValueError(f"{generated_profile.get('profile_id')} has invalid evidence ids")

        risk_flags = list(generated_profile.get("risk_flags", []))
        for flag in risk_flags:
            flag_evidence_ids = list(flag.get("evidence_ids", []))
            if not flag_evidence_ids or not set(flag_evidence_ids).issubset(evidence_ids):
                raise ValueError(f"{generated_profile.get('profile_id')} risk flag has invalid evidence ids")

        validated_profiles.append(
            {
                "profile_id": generated_profile["profile_id"],
                "title": generated_profile["title"],
                "match_score": generated_profile["match_score"],
                "powertrain_summary": generated_profile.get("powertrain_summary") or draft_profile["powertrain_summary"],
                "why_it_matches": non_empty_strings(generated_profile.get("why_it_matches")) or draft_profile["why_it_matches"],
                "trade_offs": non_empty_strings(generated_profile.get("trade_offs")) or draft_profile["trade_offs"],
                "risk_flags": risk_flags or draft_profile["risk_flags"],
                "valuation_summary": generated_profile.get("valuation_summary") or draft_profile["valuation_summary"],
                "evidence_ids": profile_evidence_ids,
                "next_steps": non_empty_strings(generated_profile.get("next_steps")) or draft_profile["next_steps"],
            }
        )

    query_summary = generated.get("query_summary")
    if not isinstance(query_summary, dict):
        query_summary = draft["query_summary"]

    return {
        "query_summary": {
            "budget": str(query_summary.get("budget") or draft["query_summary"]["budget"]),
            "usage": str(query_summary.get("usage") or draft["query_summary"]["usage"]),
            "preferences": non_empty_strings(query_summary.get("preferences")) or draft["query_summary"]["preferences"],
        },
        "recommended_profiles": validated_profiles,
        "evidence": evidence,
    }


def with_generation_metadata(payload: dict[str, Any], metadata: dict[str, str]) -> dict[str, Any]:
    payload = dict(payload)
    payload["_generation_metadata"] = metadata
    return payload


def selected_external_model(model: str | None, default_model: str) -> str:
    if not model or model == "deterministic_variant_recommender_v1":
        return default_model
    return model


def non_empty_strings(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item).strip()]


def dedupe_non_empty(values: list[str]) -> list[str]:
    deduped: list[str] = []
    for value in values:
        normalized = value.strip()
        if normalized and normalized not in deduped:
            deduped.append(normalized)
    return deduped


def extract_response_text(response: dict[str, Any]) -> str | None:
    output_text = response.get("output_text")
    if isinstance(output_text, str):
        return output_text
    text_parts: list[str] = []
    for item in response.get("output", []):
        for content in item.get("content", []):
            if content.get("type") in {"output_text", "text"} and isinstance(content.get("text"), str):
                text_parts.append(content["text"])
    return "".join(text_parts) if text_parts else None


def extract_chat_completion_text(response: dict[str, Any]) -> str | None:
    choices = response.get("choices")
    if not isinstance(choices, list) or not choices:
        return None
    message = choices[0].get("message", {})
    content = message.get("content")
    return content if isinstance(content, str) else None


def normalize(value: str) -> str:
    return value.strip().lower()


def trim(value: str, length: int) -> str:
    return value if len(value) <= length else f"{value[: length - 3].rstrip()}..."
