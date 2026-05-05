from __future__ import annotations

from datetime import date
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class VehicleProfile(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    profile_id: str
    title: str
    brand: str
    model: str
    generation_label: str | None = None
    facelift_label: str | None = None
    year_start: int
    year_end: int
    trim: str
    engine_code: str | None = None
    engine_description: str
    displacement_l: float | None = None
    transmission: str
    drivetrain: str | None = None
    fuel_type: str
    body_type: str
    seat_count: int | None = None
    fuel_consumption_l_per_100km: float | None = None
    power_kw: int | None = None
    power_hp: int | None = None
    nvh_summary: str | None = None
    ride_handling_summary: str | None = None
    comfort_summary: str | None = None
    space_summary: str | None = None
    reliability_summary: str | None = None
    common_issues: list[str] = Field(default_factory=list)
    maintenance_cost_band: str | None = None
    suitability_summary: str | None = None
    estimated_price_min_nzd: int | None = None
    estimated_price_mid_nzd: int | None = None
    estimated_price_max_nzd: int | None = None
    valuation_confidence: str | None = None
    valuation_market: str | None = None
    valuation_as_of_date: date | None = None
    assumed_condition: str | None = None
    assumed_mileage_km: int | None = None
    valuation_method: str | None = None
    valuation_notes: str | None = None


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
    profile_id: str | None = None
    generation_label: str | None = None
    trim: str | None = None
    powertrain_tags: list[str] = Field(default_factory=list)
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
    profile_id: str | None = None
    evidence_level: str | None = None
    text: str
    similarity: float | None = None


class RetrieveRequest(BaseModel):
    query: str | None = None
    budget_max: int | None = None
    brands: list[str] = Field(default_factory=list)
    models: list[str] = Field(default_factory=list)
    body_type: str | None = None
    fuel_type: str | None = None
    transmission: str | None = None
    limit: int = Field(default=6, ge=1, le=20)


class RetrieveResponse(BaseModel):
    query: str | None
    applied_filters: dict[str, Any]
    vehicle_profiles: list[VehicleProfile]
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


class RecommendedProfile(BaseModel):
    profile_id: str
    title: str
    match_score: int = Field(ge=0, le=100)
    powertrain_summary: str
    why_it_matches: list[str] = Field(default_factory=list)
    trade_offs: list[str] = Field(default_factory=list)
    risk_flags: list[RecommendationRiskFlag] = Field(default_factory=list)
    valuation_summary: str
    evidence_ids: list[str] = Field(default_factory=list)
    next_steps: list[str] = Field(default_factory=list)


class RecommendRequest(BaseModel):
    query: str | None = None
    selected_profile_ids: list[str] = Field(default_factory=list)


class RecommendResponse(BaseModel):
    query_summary: QuerySummary
    recommended_profiles: list[RecommendedProfile]
    evidence: list[RecommendationEvidence]
    debug: dict[str, Any]
