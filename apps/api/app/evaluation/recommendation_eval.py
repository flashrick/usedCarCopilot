from __future__ import annotations

import json
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.evaluation.retrieval_eval import (
    MODEL_ALIASES,
    average,
    load_eval_cases,
    normalize_text,
    ratio,
    risk_theme_matches,
)


@dataclass(frozen=True)
class RecommendationEvalConfig:
    api_url: str
    seed_dir: Path
    limit: int
    timeout_seconds: float


def run_recommendation_eval(config: RecommendationEvalConfig) -> dict[str, Any]:
    cases = load_eval_cases(config.seed_dir)
    case_results = [evaluate_case(case, config) for case in cases]
    return build_summary(case_results, config)


def evaluate_case(case: dict[str, Any], config: RecommendationEvalConfig) -> dict[str, Any]:
    response = post_recommend(config.api_url, case["query"], config.limit, config.timeout_seconds)
    expected_models = [canonical_model_name(model) for model in case.get("expected_candidate_models", [])]
    recommended_models = sorted(extract_recommended_models(response))
    model_hits = [model for model in expected_models if model in recommended_models]

    expected_risks = case.get("expected_risk_themes", [])
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
        "recommendation_count": len(response.get("recommended_cars", [])),
        "evidence_count": len(response.get("evidence", [])),
        "recommendation_mode": response.get("debug", {}).get("recommendation_mode"),
        "embedding_model": response.get("debug", {}).get("embedding_model"),
    }


def capped_model_recall(hit_count: int, expected_count: int, recommendation_limit: int) -> float:
    return ratio(hit_count, min(expected_count, recommendation_limit))


def post_recommend(api_url: str, query: str, limit: int, timeout_seconds: float) -> dict[str, Any]:
    url = f"{api_url.rstrip('/')}/recommend"
    payload = json.dumps({"query": query, "limit": limit}).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Could not call {url}: {exc}") from exc


def build_summary(case_results: list[dict[str, Any]], config: RecommendationEvalConfig) -> dict[str, Any]:
    total = len(case_results)
    weak_cases = sorted(
        case_results,
        key=lambda result: (result["model_recall"] + result["risk_theme_recall"] + result["citation_score"]) / 3,
    )[:5]

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "api_url": config.api_url,
        "seed_dir": str(config.seed_dir),
        "limit": config.limit,
        "case_count": total,
        "average_model_recall": round(average(result["model_recall"] for result in case_results), 4),
        "average_risk_theme_recall": round(average(result["risk_theme_recall"] for result in case_results), 4),
        "average_citation_score": round(average(result["citation_score"] for result in case_results), 4),
        "cases_with_full_citations": sum(1 for result in case_results if result["citation_score"] == 1.0),
        "average_recommendation_count": round(
            average(result["recommendation_count"] for result in case_results),
            2,
        ),
        "recommendation_mode": first_non_empty(result.get("recommendation_mode") for result in case_results),
        "embedding_model": first_non_empty(result.get("embedding_model") for result in case_results),
        "weak_cases": [
            {
                "id": result["id"],
                "model_recall": result["model_recall"],
                "risk_theme_recall": result["risk_theme_recall"],
                "citation_score": result["citation_score"],
                "model_misses": [
                    model for model in result["expected_models"] if model not in result["model_hits"]
                ],
                "risk_theme_misses": [
                    theme for theme in result["expected_risk_themes"] if theme not in result["risk_theme_hits"]
                ],
                "citation_failures": result["citation_failures"],
            }
            for result in weak_cases
        ],
        "cases": case_results,
    }


def format_summary(summary: dict[str, Any]) -> str:
    lines = [
        "Recommendation eval completed",
        f"- cases: {summary['case_count']}",
        f"- average model recall: {summary['average_model_recall']:.2%}",
        f"- average risk theme recall: {summary['average_risk_theme_recall']:.2%}",
        f"- average citation score: {summary['average_citation_score']:.2%}",
        f"- cases with full citations: {summary['cases_with_full_citations']}/{summary['case_count']}",
        f"- average recommendations per case: {summary['average_recommendation_count']:.2f}",
    ]
    if summary["weak_cases"]:
        lines.append("- weakest cases:")
        for case in summary["weak_cases"]:
            lines.append(
                "  - "
                f"{case['id']}: model={case['model_recall']:.2%}, "
                f"risk={case['risk_theme_recall']:.2%}, citation={case['citation_score']:.2%}"
            )
    return "\n".join(lines)


def format_markdown_report(summary: dict[str, Any]) -> str:
    lines = [
        "# Recommendation Eval Report",
        "",
        "## Run Metadata",
        "",
        f"- Generated at: `{summary['generated_at']}`",
        f"- API URL: `{summary['api_url']}`",
        f"- Seed data: `{summary['seed_dir']}`",
        f"- Recommend limit: `{summary['limit']}`",
        f"- Recommendation mode: `{summary.get('recommendation_mode') or 'unknown'}`",
        f"- Embedding model: `{summary.get('embedding_model') or 'unknown'}`",
        "",
        "## Summary",
        "",
        f"- Cases: {summary['case_count']}",
        f"- Average model recall: {summary['average_model_recall']:.2%}",
        f"- Average risk theme recall: {summary['average_risk_theme_recall']:.2%}",
        f"- Average citation score: {summary['average_citation_score']:.2%}",
        f"- Cases with full citations: {summary['cases_with_full_citations']}/{summary['case_count']}",
        f"- Average recommendations per case: {summary['average_recommendation_count']:.2f}",
        "",
        "## Weakest Cases",
        "",
    ]
    for case in summary["weak_cases"]:
        model_misses = ", ".join(case["model_misses"]) or "none"
        risk_misses = ", ".join(case["risk_theme_misses"]) or "none"
        citation_failures = "; ".join(case["citation_failures"]) or "none"
        lines.extend(
            [
                f"### {case['id']}",
                "",
                f"- Model recall: {case['model_recall']:.2%}",
                f"- Risk theme recall: {case['risk_theme_recall']:.2%}",
                f"- Citation score: {case['citation_score']:.2%}",
                f"- Missed models: {model_misses}",
                f"- Missed risk themes: {risk_misses}",
                f"- Citation failures: {citation_failures}",
                "",
            ]
        )

    lines.extend(["## Case Details", ""])
    for case in summary["cases"]:
        failures = "; ".join(case["citation_failures"]) or "none"
        lines.extend(
            [
                f"### {case['id']}",
                "",
                f"- Query: {case['query']}",
                f"- Expected models: {', '.join(case['expected_models']) or 'none'}",
                f"- Recommended models: {', '.join(case['recommended_models']) or 'none'}",
                f"- Model hits: {', '.join(case['model_hits']) or 'none'}",
                f"- Risk theme hits: {', '.join(case['risk_theme_hits']) or 'none'}",
                f"- Citation score: {case['citation_score']:.2%}",
                f"- Citation failures: {failures}",
                f"- Recommendations / evidence: {case['recommendation_count']} / {case['evidence_count']}",
                "",
            ]
        )
    return "\n".join(lines).rstrip() + "\n"


def score_citations(response: dict[str, Any]) -> tuple[float, list[str]]:
    evidence_ids = {item.get("id") for item in response.get("evidence", [])}
    obligations = 0
    hits = 0
    failures: list[str] = []

    for car in response.get("recommended_cars", []):
        title = car.get("title") or car.get("listing_id") or "unknown car"
        obligations += 1
        car_evidence_ids = set(car.get("evidence_ids", []))
        if car_evidence_ids and car_evidence_ids.issubset(evidence_ids):
            hits += 1
        else:
            failures.append(f"{title} has missing or invalid car evidence ids")

        for flag in car.get("risk_flags", []):
            obligations += 1
            flag_evidence_ids = set(flag.get("evidence_ids", []))
            if flag_evidence_ids and flag_evidence_ids.issubset(evidence_ids):
                hits += 1
            else:
                failures.append(f"{title} risk '{flag.get('label', 'unknown')}' has missing or invalid evidence ids")

    return ratio(hits, obligations), failures


def extract_recommended_models(response: dict[str, Any]) -> set[str]:
    text = normalize_text(
        " ".join(
            str(value)
            for car in response.get("recommended_cars", [])
            for value in (car.get("title"), car.get("listing_id"))
            if value
        )
    )
    padded_text = f" {text} "
    models = set()
    for alias, model in MODEL_ALIASES.items():
        if f" {alias} " in padded_text:
            models.add(model)
    return models


def collect_recommendation_text(response: dict[str, Any]) -> str:
    parts: list[str] = []
    for car in response.get("recommended_cars", []):
        parts.extend(str(value) for value in car.get("why_it_matches", []) if value)
        parts.append(str(car.get("price_commentary", "")))
        parts.extend(str(value) for value in car.get("next_steps", []) if value)
        for flag in car.get("risk_flags", []):
            parts.extend(str(value) for value in (flag.get("label"), flag.get("reason")) if value)
    for evidence in response.get("evidence", []):
        parts.extend(str(value) for value in (evidence.get("title"), evidence.get("snippet")) if value)
    return normalize_text(" ".join(parts))


def canonical_model_name(value: str) -> str:
    normalized = normalize_text(value)
    return MODEL_ALIASES.get(normalized, value)


def first_non_empty(values: Any) -> Any:
    for value in values:
        if value:
            return value
    return None
