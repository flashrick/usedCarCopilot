from __future__ import annotations

import json
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.evaluation.retrieval_eval import (
    average,
    canonical_model_name,
    load_eval_cases,
    MODEL_ALIASES,
    normalize_text,
    post_retrieve,
    ratio,
    risk_theme_matches,
)


@dataclass(frozen=True)
class RecommendationEvalConfig:
    api_url: str
    seed_dir: Path
    limit: int
    retrieve_limit: int
    timeout_seconds: float


def run_recommendation_eval(config: RecommendationEvalConfig) -> dict[str, Any]:
    cases = load_eval_cases(config.seed_dir)
    case_results = [evaluate_case(case, config) for case in cases]
    return build_summary(case_results, config)


def evaluate_case(case: dict[str, Any], config: RecommendationEvalConfig) -> dict[str, Any]:
    retrieval_response = post_retrieve(config.api_url, case["query"], case.get("market", "US"), config.retrieve_limit, config.timeout_seconds)
    selected_profile_ids = shortlist_profile_ids(retrieval_response, config.limit)
    expected_models = [canonical_model_name(model) for model in case.get("expected_candidate_models", [])]
    expected_risks = case.get("expected_risk_themes", [])

    if len(selected_profile_ids) < 2:
        return {
            "id": case["id"],
            "query": case["query"],
            "expected_models": expected_models,
            "recommended_models": [],
            "model_hits": [],
            "model_recall": 0.0,
            "expected_risk_themes": expected_risks,
            "risk_theme_hits": [],
            "risk_theme_recall": 0.0,
            "citation_score": 0.0,
            "citation_failures": ["recommendation skipped because retrieval returned fewer than 2 selectable profiles"],
            "recommendation_count": 0,
            "evidence_count": 0,
            "recommendation_mode": None,
            "embedding_model": retrieval_response.get("debug", {}).get("embedding_model"),
            "selected_profile_ids": selected_profile_ids,
            "error": "insufficient_shortlist",
        }

    response = post_recommend(config.api_url, case["query"], selected_profile_ids, config.timeout_seconds)
    recommended_models = sorted(extract_recommended_models(response))
    model_hits = [model for model in expected_models if model in recommended_models]
    recommendation_text = collect_recommendation_text(response)
    risk_hits = [theme for theme in expected_risks if risk_theme_matches(theme, recommendation_text)]
    citation_score, citation_failures = score_citations(response)

    return {
        "id": case["id"],
        "query": case["query"],
        "expected_models": expected_models,
        "recommended_models": recommended_models,
        "model_hits": model_hits,
        "model_recall": capped_model_recall(len(model_hits), len(expected_models), config.limit),
        "expected_risk_themes": expected_risks,
        "risk_theme_hits": risk_hits,
        "risk_theme_recall": ratio(len(risk_hits), len(expected_risks)),
        "citation_score": citation_score,
        "citation_failures": citation_failures,
        "recommendation_count": len(response.get("recommended_profiles", [])),
        "evidence_count": len(response.get("evidence", [])),
        "recommendation_mode": response.get("debug", {}).get("recommendation_mode"),
        "embedding_model": response.get("debug", {}).get("embedding_model"),
        "selected_profile_ids": selected_profile_ids,
        "error": None,
    }


def capped_model_recall(hit_count: int, expected_count: int, recommendation_limit: int) -> float:
    return ratio(hit_count, min(expected_count, recommendation_limit))


def post_recommend(api_url: str, query: str, selected_profile_ids: list[str], timeout_seconds: float) -> dict[str, Any]:
    url = f"{api_url.rstrip('/')}/recommend"
    payload = json.dumps({"query": query, "selected_profile_ids": selected_profile_ids}).encode("utf-8")
    request = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Could not call {url}: {exc}") from exc


def build_summary(case_results: list[dict[str, Any]], config: RecommendationEvalConfig) -> dict[str, Any]:
    weak_cases = sorted(
        case_results,
        key=lambda result: (result["model_recall"] + result["risk_theme_recall"] + result["citation_score"]) / 3,
    )[:5]
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "api_url": config.api_url,
        "seed_dir": str(config.seed_dir),
        "limit": config.limit,
        "retrieve_limit": config.retrieve_limit,
        "case_count": len(case_results),
        "average_model_recall": round(average(result["model_recall"] for result in case_results), 4),
        "average_risk_theme_recall": round(average(result["risk_theme_recall"] for result in case_results), 4),
        "average_citation_score": round(average(result["citation_score"] for result in case_results), 4),
        "cases_with_full_citations": sum(1 for result in case_results if result["citation_score"] == 1.0),
        "insufficient_shortlist_cases": sum(1 for result in case_results if result.get("error") == "insufficient_shortlist"),
        "weak_cases": weak_cases,
        "cases": case_results,
    }


def format_summary(summary: dict[str, Any]) -> str:
    return "\n".join(
        [
            "Recommendation eval completed",
            f"- cases: {summary['case_count']}",
            f"- average model recall: {summary['average_model_recall']:.2%}",
            f"- average risk theme recall: {summary['average_risk_theme_recall']:.2%}",
            f"- average citation score: {summary['average_citation_score']:.2%}",
        ]
    )


def format_markdown_report(summary: dict[str, Any]) -> str:
    lines = [
        "# Recommendation Eval Report",
        "",
        f"- Generated at: `{summary['generated_at']}`",
        f"- API URL: `{summary['api_url']}`",
        f"- Seed data: `{summary['seed_dir']}`",
        "",
    ]
    for case in summary["cases"]:
        lines.extend(
            [
                f"## {case['id']}",
                "",
                f"- Query: {case['query']}",
                f"- Recommended models: {', '.join(case['recommended_models']) or 'none'}",
                f"- Citation score: {case['citation_score']:.2%}",
                "",
            ]
        )
    return "\n".join(lines).rstrip() + "\n"


def shortlist_profile_ids(retrieval_response: dict[str, Any], limit: int) -> list[str]:
    profile_ids = [
        str(profile.get("profile_id")).strip()
        for profile in retrieval_response.get("vehicle_profiles", [])
        if str(profile.get("profile_id", "")).strip()
    ]
    return profile_ids[: max(2, min(limit, 4))]


def score_citations(response: dict[str, Any]) -> tuple[float, list[str]]:
    evidence_ids = {item.get("id") for item in response.get("evidence", [])}
    failures: list[str] = []
    total_checks = 0
    passed_checks = 0

    for profile in response.get("recommended_profiles", []):
        total_checks += 1
        profile_evidence_ids = set(profile.get("evidence_ids", []))
        if profile_evidence_ids and profile_evidence_ids.issubset(evidence_ids):
            passed_checks += 1
        else:
            failures.append(f"{profile.get('profile_id')} has invalid evidence ids")

        for flag in profile.get("risk_flags", []):
            total_checks += 1
            flag_ids = set(flag.get("evidence_ids", []))
            if flag_ids and flag_ids.issubset(evidence_ids):
                passed_checks += 1
            else:
                failures.append(f"{profile.get('profile_id')} risk flag has invalid evidence ids")

    return ratio(passed_checks, total_checks), failures


def extract_recommended_models(response: dict[str, Any]) -> set[str]:
    models: set[str] = set()
    for profile in response.get("recommended_profiles", []):
        title = normalize_text(str(profile.get("title", "")))
        for alias, canonical in MODEL_ALIASES.items():
            if alias in title:
                models.add(canonical)
    return models


def collect_recommendation_text(response: dict[str, Any]) -> str:
    parts: list[str] = []
    for profile in response.get("recommended_profiles", []):
        parts.extend(
            [*profile.get("why_it_matches", []), *profile.get("trade_offs", []), profile.get("valuation_summary", "")]
        )
        for flag in profile.get("risk_flags", []):
            parts.append(flag.get("reason", ""))
    for item in response.get("evidence", []):
        parts.append(item.get("snippet", ""))
    return normalize_text(" ".join(str(part) for part in parts))
