from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from sqlalchemy import func, select

from app.db.connection import get_session
from app.db.orm import (
    DocumentChunkRecord,
    EvalCaseRecord,
    IngestionRunRecord,
    KnowledgeSourceRecord,
    ListingRecord,
)


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"{path}:{line_number}: invalid JSONL: {exc}") from exc
        if not isinstance(value, dict):
            raise ValueError(f"{path}:{line_number}: expected a JSON object")
        rows.append(value)
    return rows


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def chunk_text(text: str, max_words: int = 180) -> list[str]:
    words = text.split()
    if len(words) <= max_words:
        return [text]
    chunks: list[str] = []
    for index in range(0, len(words), max_words):
        chunks.append(" ".join(words[index : index + max_words]))
    return chunks


def ingest_seed_data(seed_dir: Path) -> dict[str, int]:
    listings = read_jsonl(seed_dir / "listings.jsonl")
    knowledge_sources = read_jsonl(seed_dir / "knowledge_sources.jsonl")
    eval_cases = read_json(seed_dir / "eval_cases.json")

    if not isinstance(eval_cases, list):
        raise ValueError("eval_cases.json must contain a JSON array")

    with get_session() as session:
        run = IngestionRunRecord(status="running", message="seed ingestion started")
        session.add(run)
        session.flush()

        try:
            for row in listings:
                session.merge(
                    ListingRecord(
                        listing_id=row["listing_id"],
                        title=row["title"],
                        brand=row["brand"],
                        model=row["model"],
                        year=row.get("year"),
                        price=row.get("price"),
                        mileage=row.get("mileage"),
                        transmission=row.get("transmission"),
                        fuel_type=row.get("fuel_type"),
                        seller_type=row.get("seller_type"),
                        location=row.get("location"),
                        body_type=row.get("body_type"),
                        source=row["source"],
                        source_url=row.get("source_url"),
                        description=row.get("description"),
                        raw_payload=row,
                        updated_at=func.now(),
                    )
                )

            for row in knowledge_sources:
                session.merge(
                    KnowledgeSourceRecord(
                        source_id=row["source_id"],
                        source_type=row["source_type"],
                        source_channel=row["source_channel"],
                        title=row["title"],
                        brand=row["brand"],
                        model=row["model"],
                        year_range=row.get("year_range"),
                        market=row.get("market"),
                        tags=row.get("tags", []),
                        summary=row.get("summary"),
                        text=row["text"],
                        evidence_level=row.get("evidence_level"),
                        ownership_stage=row.get("ownership_stage"),
                        raw_payload=row,
                        updated_at=func.now(),
                    )
                )

                for index, chunk in enumerate(chunk_text(row["text"])):
                    chunk_id = f"{row['source_id']}-chunk-{index:03d}"
                    session.merge(
                        DocumentChunkRecord(
                            chunk_id=chunk_id,
                            source_id=row["source_id"],
                            chunk_index=index,
                            text=chunk,
                            token_count=len(chunk.split()),
                            metadata_={"brand": row["brand"], "model": row["model"], "tags": row["tags"]},
                        )
                    )

            for row in eval_cases:
                session.merge(
                    EvalCaseRecord(
                        id=row["id"],
                        query=row["query"],
                        expected_filters=row.get("expected_filters", {}),
                        expected_candidate_models=row.get("expected_candidate_models", []),
                        expected_risk_themes=row.get("expected_risk_themes", []),
                        raw_payload=row,
                        updated_at=func.now(),
                    )
                )

            run.status = "completed"
            run.completed_at = session.scalar(select(func.now()))
            run.listings_count = len(listings)
            run.knowledge_count = len(knowledge_sources)
            run.eval_count = len(eval_cases)
            run.message = "seed ingestion completed"
        except Exception as exc:
            run.status = "failed"
            run.completed_at = session.scalar(select(func.now()))
            run.message = str(exc)
            raise

    return {
        "listings": len(listings),
        "knowledge_sources": len(knowledge_sources),
        "eval_cases": len(eval_cases),
    }
