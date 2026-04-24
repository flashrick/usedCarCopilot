from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.core.config import Settings, get_settings
from app.evaluation.recommendation_eval import score_citations
from app.models.schemas import RecommendRequest
from app.recommendation.service import get_recommendation_generator
from app.retrieval.service import retrieve


SUPPORTED_LIVE_PROVIDERS = ("openai", "deepseek", "qwen", "kimi")


@dataclass(frozen=True)
class ProviderValidationConfig:
    providers: tuple[str, ...]
    query: str
    limit: int
    include_missing: bool = False


def run_provider_validation(
    config: ProviderValidationConfig,
    settings: Settings | None = None,
) -> dict[str, Any]:
    resolved_settings = settings or get_settings()
    request = RecommendRequest(query=config.query, limit=max(1, min(config.limit, 10)))
    retrieval_response = retrieve(request.model_copy(update={"limit": 20}))
    results = [
        validate_provider(provider, request, retrieval_response, resolved_settings, config.include_missing)
        for provider in config.providers
    ]
    return {
        "query": config.query,
        "limit": request.limit,
        "providers": results,
        "passed": sum(1 for result in results if result["status"] == "passed"),
        "failed": sum(1 for result in results if result["status"] == "failed"),
        "skipped": sum(1 for result in results if result["status"] == "skipped"),
    }


def validate_provider(
    provider: str,
    request: RecommendRequest,
    retrieval_response: dict[str, Any],
    settings: Settings,
    include_missing: bool,
) -> dict[str, Any]:
    normalized_provider = provider.strip().lower()
    if normalized_provider not in SUPPORTED_LIVE_PROVIDERS:
        return {"provider": provider, "status": "failed", "error": "unsupported provider"}

    api_key = provider_api_key(normalized_provider, settings)
    if not api_key and not include_missing:
        return {"provider": normalized_provider, "status": "skipped", "reason": "missing api key"}

    generator = get_recommendation_generator(
        normalized_provider,
        None,
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

    try:
        generated = generator.generate(request, retrieval_response)
    except Exception as exc:
        return {
            "provider": normalized_provider,
            "model": generator.model,
            "status": "failed",
            "error": f"{type(exc).__name__}: {exc}",
        }

    generation_metadata = generated.pop("_generation_metadata", {})
    citation_score, citation_failures = score_citations(generated)
    generation_source = generation_metadata.get("source", generator.name)
    fallback_reason = generation_metadata.get("fallback_reason")
    status = "passed"
    errors: list[str] = []
    if generation_source != normalized_provider:
        status = "failed"
        errors.append(f"generation source was {generation_source}")
    if citation_score < 1.0:
        status = "failed"
        errors.extend(citation_failures)

    result: dict[str, Any] = {
        "provider": normalized_provider,
        "model": generator.model,
        "status": status,
        "generation_source": generation_source,
        "citation_score": citation_score,
        "recommendation_count": len(generated.get("recommended_cars", [])),
        "evidence_count": len(generated.get("evidence", [])),
    }
    if fallback_reason:
        result["fallback_reason"] = fallback_reason
    if errors:
        result["errors"] = errors
    return result


def provider_api_key(provider: str, settings: Settings) -> str | None:
    if provider == "openai":
        return settings.openai_api_key
    if provider == "deepseek":
        return settings.deepseek_api_key
    if provider == "qwen":
        return settings.qwen_api_key
    if provider == "kimi":
        return settings.kimi_api_key
    return None


def format_provider_validation_summary(summary: dict[str, Any]) -> str:
    lines = [
        "AI provider validation completed",
        f"- query: {summary['query']}",
        f"- limit: {summary['limit']}",
        f"- passed: {summary['passed']}",
        f"- failed: {summary['failed']}",
        f"- skipped: {summary['skipped']}",
        "- providers:",
    ]
    for result in summary["providers"]:
        detail = result.get("reason") or result.get("fallback_reason") or result.get("error")
        suffix = f" ({detail})" if detail else ""
        model = f" model={result['model']}" if result.get("model") else ""
        lines.append(f"  - {result['provider']}: {result['status']}{model}{suffix}")
    return "\n".join(lines)
