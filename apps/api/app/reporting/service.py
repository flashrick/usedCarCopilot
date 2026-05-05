from __future__ import annotations

import json
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

from app.ai_request_logs import repo_root
from app.db.connection import get_session
from app.db.orm import (
    ChunkEmbeddingRecord,
    DocumentChunkRecord,
    EvalCaseRecord,
    IngestionRunRecord,
    KnowledgeSourceRecord,
    RequestLogRecord,
    VehicleProfileRecord,
)


PRICE_BANDS = [
    (0, 15000, "Under 15k"),
    (15000, 25000, "15k-25k"),
    (25000, 40000, "25k-40k"),
    (40000, None, "40k+"),
]


def build_admin_reports() -> dict[str, Any]:
    generated_at = datetime.now().astimezone()
    with get_session() as session:
        profile_count = count_rows(session, select(func.count()).select_from(VehicleProfileRecord))
        knowledge_count = count_rows(session, select(func.count()).select_from(KnowledgeSourceRecord))
        chunk_count = count_rows(session, select(func.count()).select_from(DocumentChunkRecord))
        embedding_count = count_rows(session, select(func.count()).select_from(ChunkEmbeddingRecord))
        eval_count = count_rows(session, select(func.count()).select_from(EvalCaseRecord))

        retrieval_total = count_rows(session, select(func.count()).select_from(RequestLogRecord))
        retrieval_errors = count_rows(session, select(func.count()).select_from(RequestLogRecord).where(RequestLogRecord.error.is_not(None)))
        average_latency = session.scalar(select(func.avg(RequestLogRecord.latency_ms)).where(RequestLogRecord.latency_ms.is_not(None)))
        last_retrieval_at = session.scalar(select(func.max(RequestLogRecord.created_at)))

        ingestion_total = count_rows(session, select(func.count()).select_from(IngestionRunRecord))
        last_ingestion_at = session.scalar(select(func.max(IngestionRunRecord.completed_at)))

        profiles_by_market = bucket_column(session, VehicleProfileRecord.market, profile_count)
        profiles_by_body_type = bucket_column(session, VehicleProfileRecord.body_type, profile_count)
        profiles_by_fuel_type = bucket_column(session, VehicleProfileRecord.fuel_type, profile_count)
        knowledge_by_source_type = bucket_column(session, KnowledgeSourceRecord.source_type, knowledge_count)
        knowledge_by_evidence_level = bucket_column(session, KnowledgeSourceRecord.evidence_level, knowledge_count)
        retrieval_by_endpoint = bucket_column(session, RequestLogRecord.endpoint, retrieval_total)
        profiles_by_price_band = profile_price_buckets(session, profile_count)

        recent_retrieval_requests = [
            {
                "title": row.endpoint,
                "subtitle": row.query or "No query text",
                "value": f"{row.profile_count} profiles / {row.knowledge_count} evidence",
                "status": "error" if row.error else "ok",
                "timestamp": row.created_at,
            }
            for row in session.scalars(select(RequestLogRecord).order_by(RequestLogRecord.created_at.desc()).limit(8))
        ]

        recent_ingestion_runs = [
            {
                "title": row.status,
                "subtitle": row.message or "Seed ingestion run",
                "value": f"{row.profile_count} profiles / {row.knowledge_count} knowledge",
                "status": row.status,
                "timestamp": row.completed_at or row.started_at,
            }
            for row in session.scalars(select(IngestionRunRecord).order_by(IngestionRunRecord.started_at.desc()).limit(5))
        ]

    ai_summary = summarize_ai_request_logs()
    embedding_coverage = percent(embedding_count, chunk_count)
    retrieval_success = percent(retrieval_total - retrieval_errors, retrieval_total)

    return {
        "generated_at": generated_at,
        "summary": [
            metric("Vehicle profiles", profile_count, "Searchable structured vehicle records"),
            metric("Knowledge sources", knowledge_count, "Citation sources available to retrieval"),
            metric("Semantic chunks", chunk_count, f"{embedding_coverage:.1f}% have embeddings"),
            metric("Eval cases", eval_count, "Regression coverage for retrieval and recommendations"),
        ],
        "retrieval_activity": [
            metric("Retrieval requests", retrieval_total, "Logged `/retrieve` requests"),
            metric("Success rate", f"{retrieval_success:.1f}%", "Requests without recorded errors", status_for_rate(retrieval_success)),
            metric("Avg latency", format_milliseconds(average_latency), "Only populated when latency logging is enabled"),
            metric("Last retrieval", format_datetime(last_retrieval_at), "Most recent logged retrieval request"),
        ],
        "ai_activity": [
            metric("AI advice calls", ai_summary["total"], "Logged `/recommend` calls"),
            metric("Success rate", f"{ai_summary['success_rate']:.1f}%", "Calls with status code below 400", status_for_rate(ai_summary["success_rate"])),
            metric("Provider errors", ai_summary["errors"], "Failed AI recommendation calls"),
            metric("Last AI call", format_datetime(ai_summary["last_timestamp"]), "Most recent logged recommendation call"),
        ],
        "ingestion_activity": [
            metric("Ingestion runs", ingestion_total, "Seed load attempts recorded by the backend"),
            metric("Last ingestion", format_datetime(last_ingestion_at), "Most recent completed ingestion run"),
            metric("Embedding coverage", f"{embedding_coverage:.1f}%", f"{embedding_count} of {chunk_count} chunks embedded", status_for_rate(embedding_coverage)),
        ],
        "profiles_by_market": profiles_by_market,
        "profiles_by_body_type": profiles_by_body_type,
        "profiles_by_fuel_type": profiles_by_fuel_type,
        "profiles_by_price_band": profiles_by_price_band,
        "knowledge_by_source_type": knowledge_by_source_type,
        "knowledge_by_evidence_level": knowledge_by_evidence_level,
        "retrieval_by_endpoint": retrieval_by_endpoint,
        "ai_by_provider": ai_summary["providers"],
        "recent_retrieval_requests": recent_retrieval_requests,
        "recent_ai_requests": ai_summary["recent"],
        "recent_ingestion_runs": recent_ingestion_runs,
    }


def count_rows(session: Session, statement: Select[tuple[Any]]) -> int:
    return int(session.scalar(statement) or 0)


def bucket_column(session: Session, column: Any, total: int, limit: int = 8) -> list[dict[str, Any]]:
    if total <= 0:
        return []

    rows = session.execute(
        select(column, func.count())
        .where(column.is_not(None), column != "")
        .group_by(column)
        .order_by(func.count().desc(), column.asc())
        .limit(limit)
    ).all()
    return [{"label": str(label), "count": int(count), "percentage": percent(int(count), total)} for label, count in rows]


def profile_price_buckets(session: Session, total_profiles: int) -> list[dict[str, Any]]:
    if total_profiles <= 0:
        return []

    counts = Counter(
        price_band_label(price)
        for price in session.scalars(select(VehicleProfileRecord.estimated_price_mid_nzd).where(VehicleProfileRecord.estimated_price_mid_nzd.is_not(None)))
    )
    return [
        {"label": label, "count": counts[label], "percentage": percent(counts[label], total_profiles)}
        for _, _, label in PRICE_BANDS
        if counts[label] > 0
    ]


def price_band_label(price: int | None) -> str:
    if price is None:
        return "Unpriced"

    for minimum, maximum, label in PRICE_BANDS:
        if price >= minimum and (maximum is None or price < maximum):
            return label
    return "Unpriced"


def summarize_ai_request_logs(log_dir: Path | None = None) -> dict[str, Any]:
    entries = load_ai_request_log_entries(log_dir or repo_root() / "logs")
    total = len(entries)
    errors = sum(1 for entry in entries if int(entry.get("status_code") or 0) >= 400 or entry.get("error"))
    providers = Counter(provider_from_ai_entry(entry) for entry in entries)
    last_timestamp = max((parse_timestamp(entry.get("timestamp")) for entry in entries), default=None)
    recent = sorted(entries, key=lambda item: item.get("timestamp") or "", reverse=True)[:8]

    return {
        "total": total,
        "errors": errors,
        "success_rate": percent(total - errors, total),
        "last_timestamp": last_timestamp,
        "providers": [
            {"label": label, "count": count, "percentage": percent(count, total)}
            for label, count in providers.most_common(8)
        ],
        "recent": [format_ai_recent_item(entry) for entry in recent],
    }


def load_ai_request_log_entries(log_dir: Path) -> list[dict[str, Any]]:
    if not log_dir.exists():
        return []

    entries: list[dict[str, Any]] = []
    for path in sorted(log_dir.glob("ai-requests-*.log"), reverse=True):
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except OSError:
            continue
        for line in lines:
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue
            if entry.get("event") == "ai_recommendation_request":
                entries.append(entry)
    return entries


def provider_from_ai_entry(entry: dict[str, Any]) -> str:
    debug = ((entry.get("response") or {}).get("debug") or {}) if isinstance(entry.get("response"), dict) else {}
    return str(debug.get("recommendation_provider") or debug.get("provider_name") or "unknown")


def format_ai_recent_item(entry: dict[str, Any]) -> dict[str, Any]:
    request = entry.get("request") if isinstance(entry.get("request"), dict) else {}
    selected = request.get("selected_profile_ids") if isinstance(request.get("selected_profile_ids"), list) else []
    status_code = int(entry.get("status_code") or 0)
    return {
        "title": provider_from_ai_entry(entry),
        "subtitle": request.get("query") or "No query text",
        "value": f"{len(selected)} selected profiles",
        "status": "error" if status_code >= 400 or entry.get("error") else "ok",
        "timestamp": parse_timestamp(entry.get("timestamp")),
    }


def metric(label: str, value: str | int | float, helper: str | None = None, status: str | None = None) -> dict[str, str | None]:
    return {"label": label, "value": str(value), "helper": helper, "status": status}


def percent(part: int, total: int) -> float:
    if total <= 0:
        return 0.0
    return round((part / total) * 100, 1)


def status_for_rate(rate: float) -> str:
    if rate >= 90:
        return "ok"
    if rate >= 70:
        return "warning"
    return "error"


def format_milliseconds(value: Any) -> str:
    if value is None:
        return "N/A"
    return f"{float(value):.0f} ms"


def parse_timestamp(value: Any) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value))
    except ValueError:
        return None


def format_datetime(value: datetime | None) -> str:
    if value is None:
        return "N/A"
    return value.astimezone().strftime("%Y-%m-%d %H:%M")
