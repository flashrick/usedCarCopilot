from __future__ import annotations

from fastapi import APIRouter
from sqlalchemy import select, text

from app.db.connection import get_session
from app.db.orm import KnowledgeSourceRecord, ListingRecord
from app.models.schemas import KnowledgeSource, Listing, RetrieveRequest, RetrieveResponse
from app.retrieval.service import retrieve


router = APIRouter()


@router.get("/health")
def health() -> dict[str, str]:
    with get_session() as session:
        session.execute(text("SELECT 1")).one()
    return {"status": "ok"}


@router.get("/listings", response_model=list[Listing])
def list_listings(limit: int = 20) -> list[ListingRecord]:
    limit = max(1, min(limit, 100))
    with get_session() as session:
        return list(
            session.scalars(
                select(ListingRecord)
                .order_by(
                    ListingRecord.brand,
                    ListingRecord.model,
                    ListingRecord.price.is_(None),
                    ListingRecord.price.asc(),
                    ListingRecord.listing_id,
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


@router.post("/retrieve", response_model=RetrieveResponse)
def retrieve_context(request: RetrieveRequest) -> dict:
    return retrieve(request)
