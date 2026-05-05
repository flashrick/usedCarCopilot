from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request
from sqlalchemy import select, text

from app.ai_request_logs import log_ai_recommendation_request
from app.db.connection import get_session
from app.db.orm import KnowledgeSourceRecord, VehicleProfileRecord
from app.models.schemas import AdminReportsResponse, KnowledgeSource, RecommendRequest, RecommendResponse, RetrieveRequest, RetrieveResponse, VehicleProfile
from app.reporting.service import build_admin_reports
from app.recommendation.service import RecommendationRequestError, recommend
from app.retrieval.service import retrieve


router = APIRouter()


def try_log_ai_recommendation_request(*args: object, **kwargs: object) -> None:
    try:
        log_ai_recommendation_request(*args, **kwargs)
    except Exception:
        # Logging must never break the request path.
        pass


@router.get("/health")
def health() -> dict[str, str]:
    with get_session() as session:
        session.execute(text("SELECT 1")).one()
    return {"status": "ok"}


@router.get("/vehicle-profiles", response_model=list[VehicleProfile])
def list_vehicle_profiles(limit: int = 20) -> list[VehicleProfileRecord]:
    limit = max(1, min(limit, 100))
    with get_session() as session:
        return list(
            session.scalars(
                select(VehicleProfileRecord)
                .order_by(
                    VehicleProfileRecord.brand,
                    VehicleProfileRecord.model,
                    VehicleProfileRecord.estimated_price_mid_nzd.is_(None),
                    VehicleProfileRecord.estimated_price_mid_nzd.asc(),
                    VehicleProfileRecord.profile_id,
                )
                .limit(limit)
            )
        )


@router.get("/knowledge", response_model=list[KnowledgeSource])
def list_knowledge(limit: int = 20) -> list[KnowledgeSourceRecord]:
    limit = max(1, min(limit, 100))
    with get_session() as session:
        return list(
            session.scalars(
                select(KnowledgeSourceRecord)
                .order_by(KnowledgeSourceRecord.brand, KnowledgeSourceRecord.model, KnowledgeSourceRecord.source_id)
                .limit(limit)
            )
        )


@router.get("/admin/reports", response_model=AdminReportsResponse)
def admin_reports() -> dict:
    return build_admin_reports()


@router.post("/retrieve", response_model=RetrieveResponse)
def retrieve_context(request: RetrieveRequest) -> dict:
    return retrieve(request)


@router.post("/recommend", response_model=RecommendResponse)
def recommend_cars(request: RecommendRequest, http_request: Request) -> dict:
    try:
        response = recommend(request)
        try_log_ai_recommendation_request(
            http_request,
            request,
            response=response,
            status_code=200,
        )
        return response
    except RecommendationRequestError as exc:
        try_log_ai_recommendation_request(
            http_request,
            request,
            status_code=400,
            error=exc,
        )
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        try_log_ai_recommendation_request(
            http_request,
            request,
            status_code=500,
            error=exc,
        )
        raise
