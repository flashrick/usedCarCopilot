from __future__ import annotations

from datetime import datetime
from typing import Any

from datetime import date

from sqlalchemy import ARRAY, BigInteger, Date, DateTime, Float, ForeignKey, Integer, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.types import UserDefinedType


class Base(DeclarativeBase):
    pass


class Vector(UserDefinedType):
    cache_ok = True

    def __init__(self, dimensions: int) -> None:
        self.dimensions = dimensions

    def get_col_spec(self, **kw: Any) -> str:
        return f"vector({self.dimensions})"

    def bind_processor(self, dialect: Any) -> Any:
        def process(value: Any) -> str | None:
            if value is None:
                return None
            if isinstance(value, str):
                return value
            return "[" + ",".join(f"{float(item):.8f}" for item in value) + "]"

        return process

    def result_processor(self, dialect: Any, coltype: Any) -> Any:
        def process(value: Any) -> list[float] | None:
            if value is None:
                return None
            if isinstance(value, list):
                return [float(item) for item in value]
            if isinstance(value, str):
                stripped = value.strip("[]")
                if not stripped:
                    return []
                return [float(item) for item in stripped.split(",")]
            return value

        return process


class IngestionRunRecord(Base):
    __tablename__ = "ingestion_runs"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(Text)
    listings_count: Mapped[int] = mapped_column(Integer, default=0)
    profile_count: Mapped[int] = mapped_column(Integer, default=0)
    knowledge_count: Mapped[int] = mapped_column(Integer, default=0)
    eval_count: Mapped[int] = mapped_column(Integer, default=0)
    message: Mapped[str | None] = mapped_column(Text)


class UserRecord(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    email: Mapped[str] = mapped_column(Text, unique=True)
    password_hash: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    sessions: Mapped[list[UserSessionRecord]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    recommendation_history: Mapped[list[RecommendationHistoryRecord]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )


class UserSessionRecord(Base):
    __tablename__ = "user_sessions"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    token_hash: Mapped[str] = mapped_column(Text, unique=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped[UserRecord] = relationship(back_populates="sessions")


class RecommendationHistoryRecord(Base):
    __tablename__ = "recommendation_history"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    query: Mapped[str] = mapped_column(Text)
    market: Mapped[str] = mapped_column(Text)
    selected_profile_ids: Mapped[list[str]] = mapped_column(ARRAY(Text), default=list)
    recommend_request: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    recommend_response: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped[UserRecord] = relationship(back_populates="recommendation_history")


class CanonicalModelRecord(Base):
    __tablename__ = "canonical_models"

    canonical_model_id: Mapped[str] = mapped_column(Text, primary_key=True)
    brand: Mapped[str] = mapped_column(Text)
    model: Mapped[str] = mapped_column(Text)
    canonical_model_slug: Mapped[str] = mapped_column(Text)
    aliases: Mapped[list[str]] = mapped_column(ARRAY(Text), default=list)
    raw_payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class ModelMarketVariantRecord(Base):
    __tablename__ = "model_market_variants"

    market_variant_id: Mapped[str] = mapped_column(Text, primary_key=True)
    canonical_model_id: Mapped[str] = mapped_column(ForeignKey("canonical_models.canonical_model_id", ondelete="CASCADE"))
    market: Mapped[str] = mapped_column(Text)
    brand: Mapped[str] = mapped_column(Text)
    model: Mapped[str] = mapped_column(Text)
    display_name: Mapped[str] = mapped_column(Text)
    local_aliases: Mapped[list[str]] = mapped_column(ARRAY(Text), default=list)
    year_start: Mapped[int] = mapped_column(Integer)
    year_end: Mapped[int] = mapped_column(Integer)
    body_types: Mapped[list[str]] = mapped_column(ARRAY(Text), default=list)
    fuel_types: Mapped[list[str]] = mapped_column(ARRAY(Text), default=list)
    raw_payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class ModelPopularityRankingRecord(Base):
    __tablename__ = "model_popularity_rankings"

    market: Mapped[str] = mapped_column(Text, primary_key=True)
    market_variant_id: Mapped[str] = mapped_column(
        ForeignKey("model_market_variants.market_variant_id", ondelete="CASCADE"),
        primary_key=True,
    )
    popularity_rank: Mapped[int] = mapped_column(Integer)
    brand_popularity_rank: Mapped[int] = mapped_column(Integer)
    source_label: Mapped[str] = mapped_column(Text)
    snapshot_date: Mapped[date] = mapped_column(Date)
    match_tags: Mapped[list[str]] = mapped_column(ARRAY(Text), default=list)
    raw_payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class VehicleProfileRecord(Base):
    __tablename__ = "vehicle_profiles"

    profile_id: Mapped[str] = mapped_column(Text, primary_key=True)
    title: Mapped[str] = mapped_column(Text)
    brand: Mapped[str] = mapped_column(Text)
    model: Mapped[str] = mapped_column(Text)
    market: Mapped[str] = mapped_column(Text, default="NZ")
    market_variant_id: Mapped[str | None] = mapped_column(Text)
    generation_label: Mapped[str | None] = mapped_column(Text)
    facelift_label: Mapped[str | None] = mapped_column(Text)
    year_start: Mapped[int] = mapped_column(Integer)
    year_end: Mapped[int] = mapped_column(Integer)
    trim: Mapped[str] = mapped_column(Text)
    engine_code: Mapped[str | None] = mapped_column(Text)
    engine_description: Mapped[str] = mapped_column(Text)
    displacement_l: Mapped[float | None] = mapped_column(Float)
    transmission: Mapped[str] = mapped_column(Text)
    drivetrain: Mapped[str | None] = mapped_column(Text)
    fuel_type: Mapped[str] = mapped_column(Text)
    body_type: Mapped[str] = mapped_column(Text)
    seat_count: Mapped[int | None] = mapped_column(Integer)
    fuel_consumption_l_per_100km: Mapped[float | None] = mapped_column(Float)
    power_kw: Mapped[int | None] = mapped_column(Integer)
    power_hp: Mapped[int | None] = mapped_column(Integer)
    nvh_summary: Mapped[str | None] = mapped_column(Text)
    ride_handling_summary: Mapped[str | None] = mapped_column(Text)
    comfort_summary: Mapped[str | None] = mapped_column(Text)
    space_summary: Mapped[str | None] = mapped_column(Text)
    reliability_summary: Mapped[str | None] = mapped_column(Text)
    common_issues: Mapped[list[str]] = mapped_column(ARRAY(Text), default=list)
    maintenance_cost_band: Mapped[str | None] = mapped_column(Text)
    suitability_summary: Mapped[str | None] = mapped_column(Text)
    base_msrp_nzd: Mapped[int | None] = mapped_column(Integer)
    estimated_price_min_nzd: Mapped[int | None] = mapped_column(Integer)
    estimated_price_mid_nzd: Mapped[int | None] = mapped_column(Integer)
    estimated_price_max_nzd: Mapped[int | None] = mapped_column(Integer)
    valuation_confidence: Mapped[str | None] = mapped_column(Text)
    valuation_market: Mapped[str | None] = mapped_column(Text)
    valuation_as_of_date: Mapped[date | None] = mapped_column(Date)
    assumed_condition: Mapped[str | None] = mapped_column(Text)
    assumed_mileage_km: Mapped[int | None] = mapped_column(Integer)
    valuation_method: Mapped[str | None] = mapped_column(Text)
    valuation_notes: Mapped[str | None] = mapped_column(Text)
    raw_payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class KnowledgeSourceRecord(Base):
    __tablename__ = "knowledge_sources"

    source_id: Mapped[str] = mapped_column(Text, primary_key=True)
    source_type: Mapped[str] = mapped_column(Text)
    source_channel: Mapped[str] = mapped_column(Text)
    title: Mapped[str] = mapped_column(Text)
    brand: Mapped[str] = mapped_column(Text)
    model: Mapped[str] = mapped_column(Text)
    year_range: Mapped[str | None] = mapped_column(Text)
    market: Mapped[str | None] = mapped_column(Text)
    market_variant_id: Mapped[str | None] = mapped_column(Text)
    profile_id: Mapped[str | None] = mapped_column(Text)
    generation_label: Mapped[str | None] = mapped_column(Text)
    trim: Mapped[str | None] = mapped_column(Text)
    powertrain_tags: Mapped[list[str]] = mapped_column(ARRAY(Text), default=list)
    tags: Mapped[list[str]] = mapped_column(ARRAY(Text), default=list)
    summary: Mapped[str | None] = mapped_column(Text)
    text: Mapped[str] = mapped_column(Text)
    evidence_level: Mapped[str | None] = mapped_column(Text)
    ownership_stage: Mapped[str | None] = mapped_column(Text)
    raw_payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    chunks: Mapped[list[DocumentChunkRecord]] = relationship(
        back_populates="source",
        cascade="all, delete-orphan",
    )


class DocumentChunkRecord(Base):
    __tablename__ = "document_chunks"

    chunk_id: Mapped[str] = mapped_column(Text, primary_key=True)
    source_id: Mapped[str] = mapped_column(ForeignKey("knowledge_sources.source_id", ondelete="CASCADE"))
    chunk_index: Mapped[int] = mapped_column(Integer)
    text: Mapped[str] = mapped_column(Text)
    token_count: Mapped[int] = mapped_column(Integer)
    metadata_: Mapped[dict[str, Any]] = mapped_column("metadata", JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    source: Mapped[KnowledgeSourceRecord] = relationship(back_populates="chunks")
    embedding: Mapped[ChunkEmbeddingRecord | None] = relationship(
        back_populates="chunk",
        cascade="all, delete-orphan",
        uselist=False,
    )


class ChunkEmbeddingRecord(Base):
    __tablename__ = "chunk_embeddings"

    chunk_id: Mapped[str] = mapped_column(
        ForeignKey("document_chunks.chunk_id", ondelete="CASCADE"),
        primary_key=True,
    )
    embedding_model: Mapped[str] = mapped_column(Text)
    content_hash: Mapped[str | None] = mapped_column(Text)
    embedding: Mapped[list[float]] = mapped_column(Vector(1536))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    chunk: Mapped[DocumentChunkRecord] = relationship(back_populates="embedding")


class EvalCaseRecord(Base):
    __tablename__ = "eval_cases"

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    query: Mapped[str] = mapped_column(Text)
    expected_filters: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    expected_candidate_models: Mapped[list[str]] = mapped_column(ARRAY(Text), default=list)
    expected_risk_themes: Mapped[list[str]] = mapped_column(ARRAY(Text), default=list)
    raw_payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class RequestLogRecord(Base):
    __tablename__ = "request_logs"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    endpoint: Mapped[str] = mapped_column(Text)
    query: Mapped[str | None] = mapped_column(Text)
    filters: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    listing_count: Mapped[int] = mapped_column(Integer, default=0)
    profile_count: Mapped[int] = mapped_column(Integer, default=0)
    knowledge_count: Mapped[int] = mapped_column(Integer, default=0)
    latency_ms: Mapped[int | None] = mapped_column(Integer)
    error: Mapped[str | None] = mapped_column(Text)
