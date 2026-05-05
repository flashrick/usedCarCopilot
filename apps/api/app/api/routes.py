from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request, Response
from pydantic import TypeAdapter
from sqlalchemy import select, text

from app.ai_request_logs import log_ai_recommendation_request
from app.auth import (
    AuthenticationError,
    clear_session_cookie,
    create_session_token,
    create_user,
    require_authenticated_user,
    revoke_session_token,
    set_session_cookie,
    verify_login,
)
from app.db.connection import get_session
from app.db.orm import KnowledgeSourceRecord, RecommendationHistoryRecord, VehicleProfileRecord
from app.models.schemas import (
    AdminReportsResponse,
    AuthSessionResponse,
    AuthUser,
    HistoryDetail,
    HistoryListItem,
    KnowledgeSource,
    LoginRequest,
    LogoutResponse,
    RecommendRequest,
    RecommendResponse,
    RegisterRequest,
    RetrieveRequest,
    RetrieveResponse,
    VehicleProfile,
)
from app.reporting.service import build_admin_reports
from app.recommendation.service import RecommendationRequestError, recommend, recommend_with_session
from app.retrieval.service import retrieve


router = APIRouter()
recommend_request_adapter = TypeAdapter(RecommendRequest)
recommend_response_adapter = TypeAdapter(RecommendResponse)


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


@router.post("/auth/register", response_model=AuthSessionResponse, status_code=201)
def register_user_route(request: RegisterRequest, response: Response) -> dict:
    try:
        with get_session() as session:
            user = create_user(session, email=request.email, password=request.password)
            token = create_session_token(session, user=user)
            set_session_cookie(response, token)
            return {"user": user}
    except AuthenticationError as exc:
        message = str(exc)
        status_code = 409 if "already exists" in message else 400
        raise HTTPException(status_code=status_code, detail=message) from exc


@router.post("/auth/login", response_model=AuthSessionResponse)
def login_user_route(request: LoginRequest, response: Response) -> dict:
    try:
        with get_session() as session:
            user = verify_login(session, email=request.email, password=request.password)
            token = create_session_token(session, user=user)
            set_session_cookie(response, token)
            return {"user": user}
    except AuthenticationError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc


@router.post("/auth/logout", response_model=LogoutResponse)
def logout_user_route(http_request: Request, response: Response) -> dict:
    with get_session() as session:
        revoke_session_token(session, http_request)
    clear_session_cookie(response)
    return {"ok": True}


@router.get("/auth/me", response_model=AuthUser)
def auth_me(http_request: Request) -> object:
    with get_session() as session:
        return require_authenticated_user(session, http_request)


@router.get("/me/history", response_model=list[HistoryListItem])
def list_recommendation_history(http_request: Request) -> list[dict]:
    with get_session() as session:
        user = require_authenticated_user(session, http_request)
        records = list(
            session.scalars(
                select(RecommendationHistoryRecord)
                .where(RecommendationHistoryRecord.user_id == user.id)
                .order_by(RecommendationHistoryRecord.created_at.desc(), RecommendationHistoryRecord.id.desc())
            )
        )

    items: list[dict] = []
    for record in records:
        response_payload = record.recommend_response or {}
        recommended_profiles = response_payload.get("recommended_profiles") or []
        overview = response_payload.get("recommendation_overview") or {}
        items.append(
            {
                "id": record.id,
                "query": record.query,
                "market": record.market,
                "selected_profile_ids": record.selected_profile_ids,
                "recommended_title": overview.get("recommended_title")
                or (recommended_profiles[0].get("title") if recommended_profiles else None),
                "recommended_profile_count": len(recommended_profiles),
                "created_at": record.created_at,
            }
        )
    return items


@router.get("/me/history/{history_id}", response_model=HistoryDetail)
def get_recommendation_history(history_id: int, http_request: Request) -> dict:
    with get_session() as session:
        user = require_authenticated_user(session, http_request)
        record = session.scalar(
            select(RecommendationHistoryRecord)
            .where(RecommendationHistoryRecord.id == history_id)
            .where(RecommendationHistoryRecord.user_id == user.id)
        )
        if record is None:
            raise HTTPException(status_code=404, detail="Recommendation history entry not found.")

        return {
            "id": record.id,
            "query": record.query,
            "market": record.market,
            "selected_profile_ids": record.selected_profile_ids,
            "recommend_request": recommend_request_adapter.validate_python(record.recommend_request),
            "recommend_response": recommend_response_adapter.validate_python(record.recommend_response),
            "created_at": record.created_at,
        }


@router.post("/me/recommendations", response_model=RecommendResponse)
def recommend_and_save(request: RecommendRequest, http_request: Request) -> dict:
    try:
        with get_session() as session:
            user = require_authenticated_user(session, http_request)
            response = recommend_with_session(session, request, endpoint="/me/recommendations")
            session.add(
                RecommendationHistoryRecord(
                    user_id=user.id,
                    query=(request.query or "").strip(),
                    market=str(response.get("debug", {}).get("market") or "US"),
                    selected_profile_ids=list(request.selected_profile_ids),
                    recommend_request=request.model_dump(mode="json"),
                    recommend_response=response,
                )
            )
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
