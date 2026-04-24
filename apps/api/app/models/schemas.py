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
    brands: list[str] = Field(default_factory=list)
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


class QuerySummary(BaseModel):
    budget: str
    usage: str
    preferences: list[str] = Field(default_factory=list)


class RecommendationRiskFlag(BaseModel):
    label: str
    severity: str
    reason: str
    evidence_ids: list[str] = Field(default_factory=list)


class RecommendationEvidence(BaseModel):
    id: str
    source_type: str
    title: str
    snippet: str


class RecommendedCar(BaseModel):
    listing_id: str
    title: str
    match_score: int = Field(ge=0, le=100)
    why_it_matches: list[str] = Field(default_factory=list)
    risk_flags: list[RecommendationRiskFlag] = Field(default_factory=list)
    price_commentary: str
    evidence_ids: list[str] = Field(default_factory=list)
    next_steps: list[str] = Field(default_factory=list)


class RecommendRequest(RetrieveRequest):
    limit: int = Field(default=3, ge=1, le=10)


class RecommendResponse(BaseModel):
    query_summary: QuerySummary
    recommended_cars: list[RecommendedCar]
    evidence: list[RecommendationEvidence]
    debug: dict[str, Any]
