from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class Listing(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    listing_id: str
    title: str
    brand: str
    model: str
    year: int | None = None
    price: int | None = None
    mileage: int | None = None
    transmission: str | None = None
    fuel_type: str | None = None
    seller_type: str | None = None
    location: str | None = None
    body_type: str | None = None
    source: str
    source_url: str | None = None
    description: str | None = None


class KnowledgeSource(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    source_id: str
    source_type: str
    source_channel: str
    title: str
    brand: str
    model: str
    year_range: str | None = None
    market: str | None = None
    tags: list[str] = Field(default_factory=list)
    summary: str | None = None
    text: str
    evidence_level: str | None = None
    ownership_stage: str | None = None


class RetrievedChunk(BaseModel):
    chunk_id: str
    source_id: str
    source_title: str
    source_type: str
    brand: str
    model: str
    evidence_level: str | None = None
    text: str
    similarity: float | None = None


class RetrieveRequest(BaseModel):
    query: str | None = None
    max_price: int | None = None
    brand: str | None = None
    models: list[str] = Field(default_factory=list)
    body_type: str | None = None
    location: str | None = "Auckland"
    limit: int = Field(default=5, ge=1, le=20)


class RetrieveResponse(BaseModel):
    query: str | None
    applied_filters: dict[str, Any]
    listings: list[Listing]
    knowledge: list[KnowledgeSource]
    chunks: list[RetrievedChunk]
    debug: dict[str, Any]
