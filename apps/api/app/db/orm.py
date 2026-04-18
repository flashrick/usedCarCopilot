from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import ARRAY, BigInteger, DateTime, ForeignKey, Integer, Text, func
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
    knowledge_count: Mapped[int] = mapped_column(Integer, default=0)
    eval_count: Mapped[int] = mapped_column(Integer, default=0)
    message: Mapped[str | None] = mapped_column(Text)


class ListingRecord(Base):
    __tablename__ = "listings"

    listing_id: Mapped[str] = mapped_column(Text, primary_key=True)
    title: Mapped[str] = mapped_column(Text)
    brand: Mapped[str] = mapped_column(Text)
    model: Mapped[str] = mapped_column(Text)
    year: Mapped[int | None] = mapped_column(Integer)
    price: Mapped[int | None] = mapped_column(Integer)
    mileage: Mapped[int | None] = mapped_column(Integer)
    transmission: Mapped[str | None] = mapped_column(Text)
    fuel_type: Mapped[str | None] = mapped_column(Text)
    seller_type: Mapped[str | None] = mapped_column(Text)
    location: Mapped[str | None] = mapped_column(Text)
    body_type: Mapped[str | None] = mapped_column(Text)
    source: Mapped[str] = mapped_column(Text)
    source_url: Mapped[str | None] = mapped_column(Text)
    description: Mapped[str | None] = mapped_column(Text)
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
    knowledge_count: Mapped[int] = mapped_column(Integer, default=0)
    latency_ms: Mapped[int | None] = mapped_column(Integer)
    error: Mapped[str | None] = mapped_column(Text)
