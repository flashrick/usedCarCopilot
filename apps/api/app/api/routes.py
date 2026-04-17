from __future__ import annotations

from fastapi import APIRouter

from app.db.connection import get_connection
from app.models.schemas import KnowledgeSource, Listing, RetrieveRequest, RetrieveResponse
from app.retrieval.service import retrieve


router = APIRouter()


@router.get("/health")
def health() -> dict[str, str]:
    with get_connection() as connection:
        connection.execute("SELECT 1").fetchone()
    return {"status": "ok"}


@router.get("/listings", response_model=list[Listing])
def list_listings(limit: int = 20) -> list[dict]:
    limit = max(1, min(limit, 100))
    with get_connection() as connection:
        return connection.execute(
            """
            SELECT listing_id, title, brand, model, year, price, mileage,
                   transmission, fuel_type, seller_type, location, body_type,
                   source, source_url, description
            FROM listings
            ORDER BY brand, model, price IS NULL, price ASC, listing_id
            LIMIT %s
            """,
            (limit,),
        ).fetchall()


@router.get("/knowledge", response_model=list[KnowledgeSource])
def list_knowledge(limit: int = 20) -> list[dict]:
    limit = max(1, min(limit, 100))
    with get_connection() as connection:
        return connection.execute(
            """
            SELECT source_id, source_type, source_channel, title, brand, model,
                   year_range, market, tags, summary, text, evidence_level,
                   ownership_stage
            FROM knowledge_sources
            ORDER BY brand, model, source_id
            LIMIT %s
            """,
            (limit,),
        ).fetchall()


@router.post("/retrieve", response_model=RetrieveResponse)
def retrieve_context(request: RetrieveRequest) -> dict:
    return retrieve(request)

