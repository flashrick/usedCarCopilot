from __future__ import annotations

import json
import re
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


MODEL_ALIASES: dict[str, str] = {
    "toyota aqua": "Toyota Aqua",
    "aqua": "Toyota Aqua",
    "toyota prius": "Toyota Prius",
    "prius": "Toyota Prius",
    "toyota rav4": "Toyota RAV4",
    "rav4": "Toyota RAV4",
    "honda fit": "Honda Fit",
    "fit": "Honda Fit",
    "honda civic": "Honda Civic",
    "civic": "Honda Civic",
    "honda hr v": "Honda HR-V",
    "hrv": "Honda HR-V",
    "mazda2": "Mazda Mazda2",
    "mazda3": "Mazda Mazda3",
    "mazda cx 5": "Mazda CX-5",
    "cx 5": "Mazda CX-5",
}

THEME_ALIASES: dict[str, tuple[str, ...]] = {
    "maintenance cost": ("running cost", "maintenance", "service"),
    "running cost": ("fuel", "tyre", "brake", "suspension", "running cost"),
    "hybrid system condition": ("hybrid", "battery", "warning lights"),
    "service history": ("service", "maintenance history", "records"),
    "accident repair": ("body repair", "paint", "panel", "accident"),
    "space practicality": ("space", "boot", "rear seat", "cargo"),
    "premium feel": ("premium", "refined", "calm", "comfortable"),
}


@dataclass(frozen=True)
class RetrievalEvalConfig:
    api_url: str
    seed_dir: Path
    limit: int
    timeout_seconds: float


def load_eval_cases(seed_dir: Path) -> list[dict[str, Any]]:
    path = seed_dir / "eval_cases.json"
    cases = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(cases, list):
        raise ValueError(f"{path} must contain a JSON array")
    return cases


def run_retrieval_eval(config: RetrievalEvalConfig) -> dict[str, Any]:
    cases = load_eval_cases(config.seed_dir)
    case_results = [evaluate_case(case, config) for case in cases]
    return build_summary(case_results, config)


def evaluate_case(case: dict[str, Any], config: RetrievalEvalConfig) -> dict[str, Any]:
    response = post_retrieve(config.api_url, case["query"], config.limit, config.timeout_seconds)
    expected_models = [canonical_model_name(model) for model in case.get("expected_candidate_models", [])]
    retrieved_models = sorted(extract_models(response))
    model_hits = [model for model in expected_models if model in retrieved_models]

    expected_risks = case.get("expected_risk_themes", [])
    evidence_text = collect_evidence_text(response)
    risk_hits = [theme for theme in expected_risks if risk_theme_matches(theme, evidence_text)]

    expected_filters = case.get("expected_filters", {})
    applied_filters = response.get("applied_filters", {})
    filter_hits = score_filters(expected_filters, applied_filters)

    return {
        "id": case["id"],
        "query": case["query"],
        "expected_models": expected_models,
        "retrieved_models": retrieved_models,
        "model_hits": model_hits,
        "model_recall": ratio(len(model_hits), len(expected_models)),
        "expected_risk_themes": expected_risks,
        "risk_theme_hits": risk_hits,
        "risk_theme_recall": ratio(len(risk_hits), len(expected_risks)),
        "expected_filter_keys": sorted(expected_filters),
        "filter_hits": filter_hits,
        "filter_recall": ratio(len(filter_hits), len(expected_filters)),
        "profile_count": len(response.get("vehicle_profiles", [])),
        "knowledge_count": len(response.get("knowledge", [])),
        "chunk_count": len(response.get("chunks", [])),
        "embedding_search_enabled": bool(response.get("debug", {}).get("embedding_search_enabled")),
        "candidate_models": response.get("debug", {}).get("candidate_models", []),
        "embedding_model": response.get("debug", {}).get("embedding_model"),
    }


def post_retrieve(api_url: str, query: str, limit: int, timeout_seconds: float) -> dict[str, Any]:
    url = f"{api_url.rstrip('/')}/retrieve"
    payload = json.dumps({"query": query, "limit": limit}).encode("utf-8")
    request = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Could not call {url}: {exc}") from exc


def build_summary(case_results: list[dict[str, Any]], config: RetrievalEvalConfig) -> dict[str, Any]:
    weak_cases = sorted(
        case_results,
        key=lambda result: (result["model_recall"] + result["risk_theme_recall"] + result["filter_recall"]) / 3,
    )[:5]
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "api_url": config.api_url,
        "seed_dir": str(config.seed_dir),
        "limit": config.limit,
        "case_count": len(case_results),
        "average_model_recall": round(average(result["model_recall"] for result in case_results), 4),
        "average_risk_theme_recall": round(average(result["risk_theme_recall"] for result in case_results), 4),
        "average_filter_recall": round(average(result["filter_recall"] for result in case_results), 4),
        "embedding_model": first_non_empty(result.get("embedding_model") for result in case_results),
        "weak_cases": weak_cases,
        "cases": case_results,
    }


def format_summary(summary: dict[str, Any]) -> str:
    lines = [
        "Retrieval eval completed",
        f"- cases: {summary['case_count']}",
        f"- average model recall: {summary['average_model_recall']:.2%}",
        f"- average risk theme recall: {summary['average_risk_theme_recall']:.2%}",
        f"- average filter recall: {summary['average_filter_recall']:.2%}",
    ]
    if summary["weak_cases"]:
        lines.append("- weakest cases:")
        for case in summary["weak_cases"]:
            lines.append(
                f"  - {case['id']}: model={case['model_recall']:.2%}, risk={case['risk_theme_recall']:.2%}, filter={case['filter_recall']:.2%}"
            )
    return "\n".join(lines)


def format_markdown_report(summary: dict[str, Any]) -> str:
    lines = [
        "# Retrieval Eval Report",
        "",
        f"- Generated at: `{summary['generated_at']}`",
        f"- API URL: `{summary['api_url']}`",
        f"- Seed data: `{summary['seed_dir']}`",
        f"- Embedding model: `{summary.get('embedding_model') or 'unknown'}`",
        "",
        f"- Cases: {summary['case_count']}",
        f"- Average model recall: {summary['average_model_recall']:.2%}",
        f"- Average risk theme recall: {summary['average_risk_theme_recall']:.2%}",
        f"- Average filter recall: {summary['average_filter_recall']:.2%}",
        "",
    ]
    for case in summary["cases"]:
        lines.extend(
            [
                f"## {case['id']}",
                "",
                f"- Query: {case['query']}",
                f"- Expected models: {', '.join(case['expected_models']) or 'none'}",
                f"- Retrieved models: {', '.join(case['retrieved_models']) or 'none'}",
                f"- Profile count: {case['profile_count']}",
                f"- Risk theme hits: {', '.join(case['risk_theme_hits']) or 'none'}",
                "",
            ]
        )
    return "\n".join(lines).rstrip() + "\n"


def normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9]+", " ", value.lower())).strip()


def canonical_model_name(value: str) -> str:
    return MODEL_ALIASES.get(normalize_text(value), value)


def extract_models(response: dict[str, Any]) -> set[str]:
    models = set()
    for profile in response.get("vehicle_profiles", []):
        brand = profile.get("brand")
        model = profile.get("model")
        if brand and model:
            display = f"{brand} {model}"
            if display == "Mazda Mazda2" or display == "Mazda Mazda3" or display == "Mazda CX-5":
                models.add(display)
            else:
                models.add(display)
    return models


def collect_evidence_text(response: dict[str, Any]) -> str:
    parts: list[str] = []
    for profile in response.get("vehicle_profiles", []):
        parts.extend(
            str(profile.get(field, ""))
            for field in (
                "title",
                "suitability_summary",
                "comfort_summary",
                "space_summary",
                "reliability_summary",
                "valuation_notes",
            )
        )
    for knowledge in response.get("knowledge", []):
        parts.extend([str(knowledge.get("summary", "")), str(knowledge.get("text", ""))])
    for chunk in response.get("chunks", []):
        parts.append(str(chunk.get("text", "")))
    return normalize_text(" ".join(parts))


def risk_theme_matches(theme: str, evidence_text: str) -> bool:
    normalized_theme = normalize_text(theme)
    if normalized_theme in evidence_text:
        return True
    for alias in THEME_ALIASES.get(normalized_theme, ()):
        if normalize_text(alias) in evidence_text:
            return True
    return False


def score_filters(expected_filters: dict[str, Any], applied_filters: dict[str, Any]) -> list[str]:
    hits: list[str] = []
    for key, expected_value in expected_filters.items():
        actual_value = applied_filters.get(key)
        if actual_value == expected_value:
            hits.append(key)
    return hits


def ratio(hit_count: int, expected_count: int) -> float:
    if expected_count <= 0:
        return 1.0
    return round(hit_count / expected_count, 4)


def average(values: Any) -> float:
    values = list(values)
    if not values:
        return 0.0
    return sum(values) / len(values)


def first_non_empty(values: Any) -> Any:
    for value in values:
        if value:
            return value
    return None
