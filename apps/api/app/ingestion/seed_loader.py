from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from psycopg.types.json import Jsonb

from app.db.connection import get_connection


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

    with get_connection() as connection:
        run_id = connection.execute(
            "INSERT INTO ingestion_runs (status, message) VALUES (%s, %s) RETURNING id",
            ("running", "seed ingestion started"),
        ).fetchone()["id"]

        try:
            for row in listings:
                connection.execute(
                    """
                    INSERT INTO listings (
                      listing_id, title, brand, model, year, price, mileage,
                      transmission, fuel_type, seller_type, location, body_type,
                      source, source_url, description, raw_payload, updated_at
                    )
                    VALUES (
                      %(listing_id)s, %(title)s, %(brand)s, %(model)s, %(year)s,
                      %(price)s, %(mileage)s, %(transmission)s, %(fuel_type)s,
                      %(seller_type)s, %(location)s, %(body_type)s, %(source)s,
                      %(source_url)s, %(description)s, %(raw_payload)s, now()
                    )
                    ON CONFLICT (listing_id) DO UPDATE SET
                      title = EXCLUDED.title,
                      brand = EXCLUDED.brand,
                      model = EXCLUDED.model,
                      year = EXCLUDED.year,
                      price = EXCLUDED.price,
                      mileage = EXCLUDED.mileage,
                      transmission = EXCLUDED.transmission,
                      fuel_type = EXCLUDED.fuel_type,
                      seller_type = EXCLUDED.seller_type,
                      location = EXCLUDED.location,
                      body_type = EXCLUDED.body_type,
                      source = EXCLUDED.source,
                      source_url = EXCLUDED.source_url,
                      description = EXCLUDED.description,
                      raw_payload = EXCLUDED.raw_payload,
                      updated_at = now()
                    """,
                    {**row, "raw_payload": Jsonb(row)},
                )

            for row in knowledge_sources:
                connection.execute(
                    """
                    INSERT INTO knowledge_sources (
                      source_id, source_type, source_channel, title, brand, model,
                      year_range, market, tags, summary, text, evidence_level,
                      ownership_stage, raw_payload, updated_at
                    )
                    VALUES (
                      %(source_id)s, %(source_type)s, %(source_channel)s, %(title)s,
                      %(brand)s, %(model)s, %(year_range)s, %(market)s, %(tags)s,
                      %(summary)s, %(text)s, %(evidence_level)s,
                      %(ownership_stage)s, %(raw_payload)s, now()
                    )
                    ON CONFLICT (source_id) DO UPDATE SET
                      source_type = EXCLUDED.source_type,
                      source_channel = EXCLUDED.source_channel,
                      title = EXCLUDED.title,
                      brand = EXCLUDED.brand,
                      model = EXCLUDED.model,
                      year_range = EXCLUDED.year_range,
                      market = EXCLUDED.market,
                      tags = EXCLUDED.tags,
                      summary = EXCLUDED.summary,
                      text = EXCLUDED.text,
                      evidence_level = EXCLUDED.evidence_level,
                      ownership_stage = EXCLUDED.ownership_stage,
                      raw_payload = EXCLUDED.raw_payload,
                      updated_at = now()
                    """,
                    {**row, "raw_payload": Jsonb(row)},
                )

                for index, chunk in enumerate(chunk_text(row["text"])):
                    chunk_id = f"{row['source_id']}-chunk-{index:03d}"
                    connection.execute(
                        """
                        INSERT INTO document_chunks (
                          chunk_id, source_id, chunk_index, text, token_count, metadata
                        )
                        VALUES (%s, %s, %s, %s, %s, %s)
                        ON CONFLICT (chunk_id) DO UPDATE SET
                          text = EXCLUDED.text,
                          token_count = EXCLUDED.token_count,
                          metadata = EXCLUDED.metadata
                        """,
                        (
                            chunk_id,
                            row["source_id"],
                            index,
                            chunk,
                            len(chunk.split()),
                            Jsonb({"brand": row["brand"], "model": row["model"], "tags": row["tags"]}),
                        ),
                    )

            for row in eval_cases:
                connection.execute(
                    """
                    INSERT INTO eval_cases (
                      id, query, expected_filters, expected_candidate_models,
                      expected_risk_themes, raw_payload, updated_at
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, now())
                    ON CONFLICT (id) DO UPDATE SET
                      query = EXCLUDED.query,
                      expected_filters = EXCLUDED.expected_filters,
                      expected_candidate_models = EXCLUDED.expected_candidate_models,
                      expected_risk_themes = EXCLUDED.expected_risk_themes,
                      raw_payload = EXCLUDED.raw_payload,
                      updated_at = now()
                    """,
                    (
                        row["id"],
                        row["query"],
                        Jsonb(row.get("expected_filters", {})),
                        row.get("expected_candidate_models", []),
                        row.get("expected_risk_themes", []),
                        Jsonb(row),
                    ),
                )

            connection.execute(
                """
                UPDATE ingestion_runs
                SET status = %s,
                    completed_at = now(),
                    listings_count = %s,
                    knowledge_count = %s,
                    eval_count = %s,
                    message = %s
                WHERE id = %s
                """,
                ("completed", len(listings), len(knowledge_sources), len(eval_cases), "seed ingestion completed", run_id),
            )
        except Exception as exc:
            connection.execute(
                """
                UPDATE ingestion_runs
                SET status = %s, completed_at = now(), message = %s
                WHERE id = %s
                """,
                ("failed", str(exc), run_id),
            )
            raise

    return {
        "listings": len(listings),
        "knowledge_sources": len(knowledge_sources),
        "eval_cases": len(eval_cases),
    }
