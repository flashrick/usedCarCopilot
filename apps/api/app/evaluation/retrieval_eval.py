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
    "honda hrv": "Honda HR-V",
    "hr v": "Honda HR-V",
    "hrv": "Honda HR-V",
    "mazda mazda2": "Mazda2",
    "mazda2": "Mazda2",
    "mazda mazda3": "Mazda3",
    "mazda3": "Mazda3",
    "mazda cx 5": "Mazda CX-5",
    "cx 5": "Mazda CX-5",
}

STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "before",
    "by",
    "car",
    "cars",
    "check",
    "choice",
    "condition",
    "for",
    "from",
    "is",
    "it",
    "main",
    "most",
    "of",
    "or",
    "should",
    "the",
    "these",
    "to",
    "used",
    "use",
    "variation",
    "when",
    "which",
}

TERM_ALIASES: dict[str, tuple[str, ...]] = {
    "accident": ("repair", "body", "paint", "damage"),
    "battery": ("hybrid",),
    "brake": ("brakes", "braking"),
    "brakes": ("brake", "braking"),
    "cargo": ("boot", "space", "practicality"),
    "cheap": ("budget", "cost", "price"),
    "comfort": ("comfortable",),
    "cost": ("price", "budget", "fuel", "maintenance", "running"),
    "fuel": ("economy", "hybrid", "running"),
    "hybrid": ("battery", "fuel", "economy"),
    "inspection": ("check", "pre purchase", "warning"),
    "maintenance": ("service", "repair", "wear"),
    "parking": ("city", "compact"),
    "practicality": ("space", "boot", "seat", "cargo"),
    "reliable": ("reliability", "service"),
    "reliability": ("reliable", "service"),
    "repair": ("accident", "maintenance", "body"),
    "risk": ("warning", "check", "inspection"),
    "running": ("fuel", "cost", "economy"),
    "safety": ("safe", "equipment"),
    "service": ("maintenance", "history"),
    "space": ("boot", "seat", "cargo", "practicality"),
    "suspension": ("noise", "wear"),
    "transmission": ("cvt", "gearbox"),
    "tyre": ("tyres", "tire", "tires"),
    "tyres": ("tyre", "tire", "tires"),
    "wear": ("condition", "maintenance"),
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
        "listing_count": len(response.get("listings", [])),
        "knowledge_count": len(response.get("knowledge", [])),
        "chunk_count": len(response.get("chunks", [])),
        "embedding_search_enabled": bool(response.get("debug", {}).get("embedding_search_enabled")),
        "candidate_models": response.get("debug", {}).get("candidate_models", []),
        "embedding_model": response.get("debug", {}).get("embedding_model"),
    }


def post_retrieve(api_url: str, query: str, limit: int, timeout_seconds: float) -> dict[str, Any]:
    url = f"{api_url.rstrip('/')}/retrieve"
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


def build_summary(case_results: list[dict[str, Any]], config: RetrievalEvalConfig) -> dict[str, Any]:
    total = len(case_results)
    average_model_recall = average(result["model_recall"] for result in case_results)
    average_risk_theme_recall = average(result["risk_theme_recall"] for result in case_results)
    average_filter_recall = average(result["filter_recall"] for result in case_results)
    embedding_enabled_cases = sum(1 for result in case_results if result["embedding_search_enabled"])
    cases_with_chunks = sum(1 for result in case_results if result["chunk_count"] > 0)
    perfect_model_cases = sum(1 for result in case_results if result["model_recall"] == 1.0)
    perfect_risk_cases = sum(1 for result in case_results if result["risk_theme_recall"] == 1.0)
    weak_cases = sorted(
        case_results,
        key=lambda result: (result["model_recall"] + result["risk_theme_recall"] + result["filter_recall"]) / 3,
    )[:5]

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "api_url": config.api_url,
        "seed_dir": str(config.seed_dir),
        "limit": config.limit,
        "case_count": total,
        "average_model_recall": round(average_model_recall, 4),
        "average_risk_theme_recall": round(average_risk_theme_recall, 4),
        "average_filter_recall": round(average_filter_recall, 4),
        "embedding_enabled_cases": embedding_enabled_cases,
        "cases_with_chunks": cases_with_chunks,
        "perfect_model_cases": perfect_model_cases,
        "perfect_risk_theme_cases": perfect_risk_cases,
        "embedding_model": first_non_empty(result.get("embedding_model") for result in case_results),
        "weak_cases": [
            {
                "id": result["id"],
                "model_recall": result["model_recall"],
                "risk_theme_recall": result["risk_theme_recall"],
                "filter_recall": result["filter_recall"],
                "model_misses": [
                    model for model in result["expected_models"] if model not in result["model_hits"]
                ],
                "risk_theme_misses": [
                    theme for theme in result["expected_risk_themes"] if theme not in result["risk_theme_hits"]
                ],
            }
            for result in weak_cases
        ],
        "cases": case_results,
    }


def format_summary(summary: dict[str, Any]) -> str:
    lines = [
        "Retrieval eval completed",
        f"- cases: {summary['case_count']}",
        f"- average model recall: {summary['average_model_recall']:.2%}",
        f"- average risk theme recall: {summary['average_risk_theme_recall']:.2%}",
        f"- average filter recall: {summary['average_filter_recall']:.2%}",
        f"- embedding-enabled cases: {summary['embedding_enabled_cases']}/{summary['case_count']}",
        f"- cases with semantic chunks: {summary['cases_with_chunks']}/{summary['case_count']}",
        f"- perfect model coverage cases: {summary['perfect_model_cases']}/{summary['case_count']}",
        f"- perfect risk-theme coverage cases: {summary['perfect_risk_theme_cases']}/{summary['case_count']}",
    ]
    if summary["weak_cases"]:
        lines.append("- weakest cases:")
        for case in summary["weak_cases"]:
            lines.append(
                "  - "
                f"{case['id']}: model={case['model_recall']:.2%}, "
                f"risk={case['risk_theme_recall']:.2%}, filter={case['filter_recall']:.2%}"
            )
    return "\n".join(lines)


def format_markdown_report(summary: dict[str, Any]) -> str:
    lines = [
        "# Retrieval Eval Report",
        "",
        "## Run Metadata",
        "",
        f"- Generated at: `{summary['generated_at']}`",
        f"- API URL: `{summary['api_url']}`",
        f"- Seed data: `{summary['seed_dir']}`",
        f"- Retrieve limit: `{summary['limit']}`",
        f"- Embedding model: `{summary.get('embedding_model') or 'unknown'}`",
        "",
        "## Summary",
        "",
        f"- Cases: {summary['case_count']}",
        f"- Average model recall: {summary['average_model_recall']:.2%}",
        f"- Average risk theme recall: {summary['average_risk_theme_recall']:.2%}",
        f"- Average filter recall: {summary['average_filter_recall']:.2%}",
        f"- Embedding-enabled cases: {summary['embedding_enabled_cases']}/{summary['case_count']}",
        f"- Cases with semantic chunks: {summary['cases_with_chunks']}/{summary['case_count']}",
        f"- Perfect model coverage cases: {summary['perfect_model_cases']}/{summary['case_count']}",
        f"- Perfect risk-theme coverage cases: {summary['perfect_risk_theme_cases']}/{summary['case_count']}",
        "",
        "## Weakest Cases",
        "",
    ]
    for case in summary["weak_cases"]:
        model_misses = ", ".join(case["model_misses"]) or "none"
        risk_misses = ", ".join(case["risk_theme_misses"]) or "none"
        lines.extend(
            [
                f"### {case['id']}",
                "",
                f"- Model recall: {case['model_recall']:.2%}",
                f"- Risk theme recall: {case['risk_theme_recall']:.2%}",
                f"- Filter recall: {case['filter_recall']:.2%}",
                f"- Missed models: {model_misses}",
                f"- Missed risk themes: {risk_misses}",
                "",
            ]
        )

    lines.extend(["## Case Details", ""])
    for case in summary["cases"]:
        lines.extend(
            [
                f"### {case['id']}",
                "",
                f"- Query: {case['query']}",
                f"- Expected models: {', '.join(case['expected_models']) or 'none'}",
                f"- Retrieved models: {', '.join(case['retrieved_models']) or 'none'}",
                f"- Model hits: {', '.join(case['model_hits']) or 'none'}",
                f"- Risk theme hits: {', '.join(case['risk_theme_hits']) or 'none'}",
                f"- Filter hits: {', '.join(case['filter_hits']) or 'none'}",
                f"- Listings / knowledge / chunks: {case['listing_count']} / {case['knowledge_count']} / {case['chunk_count']}",
                "",
            ]
        )
    return "\n".join(lines).rstrip() + "\n"


def extract_models(response: dict[str, Any]) -> set[str]:
    models: set[str] = set()
    for section in ("listings", "knowledge", "chunks"):
        for item in response.get(section, []):
            brand = item.get("brand")
            model = item.get("model")
            if brand and model:
                models.add(canonical_model_name(f"{brand} {model}"))
    for model in response.get("debug", {}).get("candidate_models", []):
        models.add(canonical_model_name(model))
    return models


def collect_evidence_text(response: dict[str, Any]) -> str:
    parts: list[str] = []
    for listing in response.get("listings", []):
        parts.extend(
            str(value)
            for value in (
                listing.get("title"),
                listing.get("description"),
                listing.get("body_type"),
                listing.get("fuel_type"),
            )
            if value
        )
    for source in response.get("knowledge", []):
        parts.extend(str(value) for value in (source.get("title"), source.get("summary"), source.get("text")) if value)
    for chunk in response.get("chunks", []):
        parts.extend(str(value) for value in (chunk.get("source_title"), chunk.get("text")) if value)
    return normalize_text(" ".join(parts))


def score_filters(expected_filters: dict[str, Any], applied_filters: dict[str, Any]) -> list[str]:
    hits: list[str] = []
    for key, expected_value in expected_filters.items():
        if key == "max_price" and applied_filters.get("max_price") == expected_value:
            hits.append(key)
        elif key == "target_price" and applied_filters.get("max_price") == expected_value:
            hits.append(key)
        elif key == "location" and normalize_text(applied_filters.get("location")) == normalize_text(expected_value):
            hits.append(key)
        elif key == "body_type" and normalize_text(applied_filters.get("body_type")) == normalize_text(expected_value):
            hits.append(key)
        elif key == "brand" and normalize_text(applied_filters.get("brand")) == normalize_text(expected_value):
            hits.append(key)
        elif key == "brands":
            requested_brands = {normalize_text(brand) for brand in expected_value}
            applied_brands = {normalize_text(brand) for brand in applied_filters.get("brands", [])}
            applied_brand = normalize_text(applied_filters.get("brand"))
            if applied_brand:
                applied_brands.add(applied_brand)
            if requested_brands and requested_brands.issubset(applied_brands):
                hits.append(key)
        elif key == "model" and canonical_model_name(str(expected_value)) in [
            canonical_model_name(model) for model in applied_filters.get("models", [])
        ]:
            hits.append(key)
        elif key == "compare_models":
            requested = {canonical_model_name(model) for model in expected_value}
            applied = {canonical_model_name(model) for model in applied_filters.get("models", [])}
            if requested and requested.issubset(applied):
                hits.append(key)
    return hits


def risk_theme_matches(theme: str, normalized_text: str) -> bool:
    normalized_theme = normalize_text(theme)
    if normalized_theme in normalized_text:
        return True

    terms = [term for term in normalized_theme.split() if term not in STOPWORDS and len(term) > 2]
    if not terms:
        return False

    matched = sum(1 for term in terms if term_matches(term, normalized_text))
    required = 1 if len(terms) == 1 else max(2, round(len(terms) * 0.6))
    return matched >= required


def term_matches(term: str, normalized_text: str) -> bool:
    if re.search(rf"\b{re.escape(term)}s?\b", normalized_text):
        return True
    return any(alias in normalized_text for alias in TERM_ALIASES.get(term, ()))


def canonical_model_name(value: str) -> str:
    normalized = normalize_text(value)
    return MODEL_ALIASES.get(normalized, value)


def normalize_text(value: Any) -> str:
    text = "" if value is None else str(value).lower()
    text = text.replace("-", " ")
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def ratio(numerator: int, denominator: int) -> float:
    if denominator == 0:
        return 1.0
    return round(numerator / denominator, 4)


def average(values: Any) -> float:
    collected = list(values)
    if not collected:
        return 0.0
    return sum(collected) / len(collected)


def first_non_empty(values: Any) -> Any:
    for value in values:
        if value:
            return value
    return None
