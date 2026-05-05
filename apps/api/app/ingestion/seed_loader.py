from __future__ import annotations

import json
from datetime import date, datetime
from pathlib import Path
from typing import Any

from sqlalchemy import func, select

from app.db.connection import get_session
from app.db.orm import (
    CanonicalModelRecord,
    DocumentChunkRecord,
    EvalCaseRecord,
    IngestionRunRecord,
    KnowledgeSourceRecord,
    ModelMarketVariantRecord,
    ModelPopularityRankingRecord,
    VehicleProfileRecord,
)
from app.valuation.service import compute_profile_valuation


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


def make_json_compatible(value: Any) -> Any:
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if isinstance(value, dict):
        return {key: make_json_compatible(item) for key, item in value.items()}
    if isinstance(value, list):
        return [make_json_compatible(item) for item in value]
    return value


def chunk_text(text: str, max_words: int = 180) -> list[str]:
    words = text.split()
    if len(words) <= max_words:
        return [text]
    chunks: list[str] = []
    for index in range(0, len(words), max_words):
        chunks.append(" ".join(words[index : index + max_words]))
    return chunks


def ingest_seed_data(seed_dir: Path) -> dict[str, int]:
    canonical_models = read_jsonl(seed_dir / "canonical_models.jsonl")
    market_variants = read_jsonl(seed_dir / "model_market_variants.jsonl")
    popularity_rankings = read_jsonl(seed_dir / "model_popularity_rankings.jsonl")
    vehicle_profiles = read_jsonl(seed_dir / "vehicle_profiles.jsonl")
    knowledge_sources = read_jsonl(seed_dir / "knowledge_sources.jsonl")
    eval_cases = read_json(seed_dir / "eval_cases.json")

    if not isinstance(eval_cases, list):
        raise ValueError("eval_cases.json must contain a JSON array")

    with get_session() as session:
        run = IngestionRunRecord(status="running", message="seed ingestion started")
        session.add(run)
        session.flush()

        try:
            for row in canonical_models:
                session.merge(
                    CanonicalModelRecord(
                        canonical_model_id=row["canonical_model_id"],
                        brand=row["brand"],
                        model=row["model"],
                        canonical_model_slug=row["canonical_model_slug"],
                        aliases=row.get("aliases", []),
                        raw_payload=make_json_compatible(row),
                        updated_at=func.now(),
                    )
                )

            for row in market_variants:
                session.merge(
                    ModelMarketVariantRecord(
                        market_variant_id=row["market_variant_id"],
                        canonical_model_id=row["canonical_model_id"],
                        market=row["market"],
                        brand=row["brand"],
                        model=row["model"],
                        display_name=row["display_name"],
                        local_aliases=row.get("local_aliases", []),
                        year_start=row["year_start"],
                        year_end=row["year_end"],
                        body_types=row.get("body_types", []),
                        fuel_types=row.get("fuel_types", []),
                        raw_payload=make_json_compatible(row),
                        updated_at=func.now(),
                    )
                )

            for row in popularity_rankings:
                session.merge(
                    ModelPopularityRankingRecord(
                        market=row["market"],
                        market_variant_id=row["market_variant_id"],
                        popularity_rank=row["popularity_rank"],
                        brand_popularity_rank=row["brand_popularity_rank"],
                        source_label=row["source_label"],
                        snapshot_date=date.fromisoformat(row["snapshot_date"]),
                        match_tags=row.get("match_tags", []),
                        raw_payload=make_json_compatible(row),
                        updated_at=func.now(),
                    )
                )

            for row in vehicle_profiles:
                valuation = compute_profile_valuation(row)
                session.merge(
                    VehicleProfileRecord(
                        profile_id=row["profile_id"],
                        title=row["title"],
                        brand=row["brand"],
                        model=row["model"],
                        market=row.get("market") or valuation["valuation_market"],
                        market_variant_id=row.get("market_variant_id"),
                        generation_label=row.get("generation_label"),
                        facelift_label=row.get("facelift_label"),
                        year_start=row["year_start"],
                        year_end=row["year_end"],
                        trim=row["trim"],
                        engine_code=row.get("engine_code"),
                        engine_description=row["engine_description"],
                        displacement_l=row.get("displacement_l"),
                        transmission=row.get("transmission"),
                        drivetrain=row.get("drivetrain"),
                        fuel_type=row.get("fuel_type"),
                        body_type=row.get("body_type"),
                        seat_count=row.get("seat_count"),
                        fuel_consumption_l_per_100km=row.get("fuel_consumption_l_per_100km"),
                        power_kw=row.get("power_kw"),
                        power_hp=row.get("power_hp"),
                        nvh_summary=row.get("nvh_summary"),
                        ride_handling_summary=row.get("ride_handling_summary"),
                        comfort_summary=row.get("comfort_summary"),
                        space_summary=row.get("space_summary"),
                        reliability_summary=row.get("reliability_summary"),
                        common_issues=row.get("common_issues", []),
                        maintenance_cost_band=row.get("maintenance_cost_band"),
                        suitability_summary=row.get("suitability_summary"),
                        base_msrp_nzd=row.get("base_msrp_nzd"),
                        estimated_price_min_nzd=valuation["estimated_price_min_nzd"],
                        estimated_price_mid_nzd=valuation["estimated_price_mid_nzd"],
                        estimated_price_max_nzd=valuation["estimated_price_max_nzd"],
                        valuation_confidence=valuation["valuation_confidence"],
                        valuation_market=valuation["valuation_market"],
                        valuation_as_of_date=valuation["valuation_as_of_date"],
                        assumed_condition=valuation["assumed_condition"],
                        assumed_mileage_km=valuation["assumed_mileage_km"],
                        valuation_method=valuation["valuation_method"],
                        valuation_notes=valuation["valuation_notes"],
                        raw_payload=make_json_compatible({**row, **valuation}),
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
                        market_variant_id=row.get("market_variant_id"),
                        profile_id=row.get("profile_id"),
                        generation_label=row.get("generation_label"),
                        trim=row.get("trim"),
                        powertrain_tags=row.get("powertrain_tags", []),
                        tags=row.get("tags", []),
                        summary=row.get("summary"),
                        text=row["text"],
                        evidence_level=row.get("evidence_level"),
                        ownership_stage=row.get("ownership_stage"),
                        raw_payload=make_json_compatible(row),
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
                            metadata_={
                                "brand": row["brand"],
                                "model": row["model"],
                                "market": row.get("market"),
                                "profile_id": row.get("profile_id"),
                                "market_variant_id": row.get("market_variant_id"),
                                "generation_label": row.get("generation_label"),
                                "trim": row.get("trim"),
                                "powertrain_tags": row.get("powertrain_tags", []),
                                "tags": row.get("tags", []),
                            },
                        )
                    )

            for row in eval_cases:
                session.merge(
                    EvalCaseRecord(
                        id=row["id"],
                        query=row["query"],
                        expected_filters=make_json_compatible(row.get("expected_filters", {})),
                        expected_candidate_models=row.get("expected_candidate_models", []),
                        expected_risk_themes=row.get("expected_risk_themes", []),
                        raw_payload=make_json_compatible(row),
                        updated_at=func.now(),
                    )
                )

            run.status = "completed"
            run.completed_at = session.scalar(select(func.now()))
            run.listings_count = 0
            run.profile_count = len(vehicle_profiles)
            run.knowledge_count = len(knowledge_sources)
            run.eval_count = len(eval_cases)
            run.message = "seed ingestion completed"
        except Exception as exc:
            run.status = "failed"
            run.completed_at = session.scalar(select(func.now()))
            run.message = str(exc)
            raise

    return {
        "canonical_models": len(canonical_models),
        "market_variants": len(market_variants),
        "popularity_rankings": len(popularity_rankings),
        "vehicle_profiles": len(vehicle_profiles),
        "knowledge_sources": len(knowledge_sources),
        "eval_cases": len(eval_cases),
    }
