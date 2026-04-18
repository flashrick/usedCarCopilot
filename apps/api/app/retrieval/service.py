from __future__ import annotations

from typing import Any

from sqlalchemy import and_, bindparam, or_, select
from sqlalchemy.orm import Session

from app.db.connection import get_session
from app.db.orm import (
    ChunkEmbeddingRecord,
    DocumentChunkRecord,
    KnowledgeSourceRecord,
    ListingRecord,
    RequestLogRecord,
    Vector,
)
from app.embedding.service import LocalHashEmbeddingProvider
from app.models.schemas import RetrieveRequest


MODEL_ALIASES = {
    "Aqua": ("Toyota", "Aqua"),
    "Toyota Aqua": ("Toyota", "Aqua"),
    "Prius": ("Toyota", "Prius"),
    "Toyota Prius": ("Toyota", "Prius"),
    "RAV4": ("Toyota", "RAV4"),
    "Rav4": ("Toyota", "RAV4"),
    "Toyota RAV4": ("Toyota", "RAV4"),
    "Fit": ("Honda", "Fit"),
    "Honda Fit": ("Honda", "Fit"),
    "Civic": ("Honda", "Civic"),
    "Honda Civic": ("Honda", "Civic"),
    "HR-V": ("Honda", "HR-V"),
    "Honda HR-V": ("Honda", "HR-V"),
    "Mazda2": ("Mazda", "Mazda2"),
    "Mazda Mazda2": ("Mazda", "Mazda2"),
    "Mazda3": ("Mazda", "Mazda3"),
    "Mazda Mazda3": ("Mazda", "Mazda3"),
    "CX-5": ("Mazda", "CX-5"),
    "Mazda CX-5": ("Mazda", "CX-5"),
}


def infer_filters(request: RetrieveRequest) -> dict[str, Any]:
    query = (request.query or "").lower()
    models = list(request.models)
    for label in MODEL_ALIASES:
        if label.lower() in query and label not in models:
            models.append(label)

    body_type = request.body_type
    if body_type is None:
        if "suv" in query:
            body_type = "suv"
        elif "hatchback" in query:
            body_type = "hatchback"
        elif "sedan" in query:
            body_type = "sedan"

    max_price = request.max_price
    if max_price is None:
        # Keep parsing intentionally conservative until a proper parser is added.
        import re

        price_match = re.search(r"under\s+\$?([0-9][0-9,]*)", query)
        if price_match:
            max_price = int(price_match.group(1).replace(",", ""))

    return {
        "query": request.query,
        "max_price": max_price,
        "brand": request.brand,
        "models": models,
        "body_type": body_type,
        "location": request.location,
        "limit": request.limit,
    }


def model_pairs(models: list[str]) -> list[tuple[str, str]]:
    pairs: list[tuple[str, str]] = []
    for model in models:
        pair = MODEL_ALIASES.get(model)
        if pair and pair not in pairs:
            pairs.append(pair)
    return pairs


def retrieve_semantic_chunks(
    session: Session,
    query: str | None,
    filters: dict[str, Any],
    candidate_pairs: list[tuple[str, str]],
    limit: int,
) -> list[dict[str, Any]]:
    if not query or not query.strip():
        return []

    provider = LocalHashEmbeddingProvider()
    query_embedding = provider.embed(query)
    distance = ChunkEmbeddingRecord.embedding.op("<=>")(
        bindparam("query_embedding", query_embedding, type_=Vector(provider.dimensions))
    ).label("distance")

    conditions = []
    scoped_pairs = model_pairs(filters["models"]) or candidate_pairs
    if scoped_pairs:
        conditions.append(
            or_(
                *[
                    and_(KnowledgeSourceRecord.brand == brand, KnowledgeSourceRecord.model == model)
                    for brand, model in scoped_pairs
                ]
            )
        )
    elif filters["brand"]:
        conditions.append(KnowledgeSourceRecord.brand == filters["brand"])

    statement = (
        select(DocumentChunkRecord, KnowledgeSourceRecord, distance)
        .join(ChunkEmbeddingRecord, ChunkEmbeddingRecord.chunk_id == DocumentChunkRecord.chunk_id)
        .join(KnowledgeSourceRecord, KnowledgeSourceRecord.source_id == DocumentChunkRecord.source_id)
        .order_by(distance.asc(), DocumentChunkRecord.chunk_id.asc())
        .limit(max(limit * 3, 8))
    )
    if conditions:
        statement = statement.where(and_(*conditions))

    rows = session.execute(statement).all()

    chunks: list[dict[str, Any]] = []
    for chunk, source, distance_value in rows:
        similarity = None
        if distance_value is not None:
            similarity = round(max(0.0, 1.0 - float(distance_value)), 4)
        chunks.append(
            {
                "chunk_id": chunk.chunk_id,
                "source_id": source.source_id,
                "source_title": source.title,
                "source_type": source.source_type,
                "brand": source.brand,
                "model": source.model,
                "evidence_level": source.evidence_level,
                "text": chunk.text,
                "similarity": similarity,
            }
        )
    return chunks


def retrieve(request: RetrieveRequest) -> dict[str, Any]:
    filters = infer_filters(request)
    conditions = []

    if filters["location"]:
        conditions.append(ListingRecord.location == filters["location"])
    if filters["max_price"] is not None:
        conditions.append(and_(ListingRecord.price.is_not(None), ListingRecord.price <= filters["max_price"]))
    if filters["brand"]:
        conditions.append(ListingRecord.brand == filters["brand"])
    if filters["body_type"]:
        conditions.append(ListingRecord.body_type == filters["body_type"])

    pairs = model_pairs(filters["models"])
    if pairs:
        conditions.append(
            or_(
                *[
                    and_(ListingRecord.brand == brand, ListingRecord.model == model)
                    for brand, model in pairs
                ]
            )
        )

    limit = filters["limit"]

    with get_session() as session:
        statement = (
            select(ListingRecord)
            .order_by(
                ListingRecord.price.is_(None),
                ListingRecord.price.asc(),
                ListingRecord.mileage.is_(None),
                ListingRecord.mileage.asc(),
                ListingRecord.year.desc().nulls_last(),
            )
            .limit(limit)
        )
        if conditions:
            statement = statement.where(and_(*conditions))

        listings = list(session.scalars(statement))

        candidate_pairs = sorted({(row.brand, row.model) for row in listings})
        knowledge: list[KnowledgeSourceRecord] = []
        if candidate_pairs:
            knowledge = list(
                session.scalars(
                    select(KnowledgeSourceRecord)
                    .where(
                        or_(
                            *[
                                and_(KnowledgeSourceRecord.brand == brand, KnowledgeSourceRecord.model == model)
                                for brand, model in candidate_pairs
                            ]
                        )
                    )
                    .order_by(KnowledgeSourceRecord.evidence_level.desc(), KnowledgeSourceRecord.source_id.asc())
                    .limit(max(limit * 3, 10))
                )
            )

        semantic_chunks = retrieve_semantic_chunks(
            session=session,
            query=request.query,
            filters=filters,
            candidate_pairs=candidate_pairs,
            limit=limit,
        )

        session.add(
            RequestLogRecord(
                endpoint="/retrieve",
                query=request.query,
                filters=filters,
                listing_count=len(listings),
                knowledge_count=len(semantic_chunks) or len(knowledge),
            )
        )

    return {
        "query": request.query,
        "applied_filters": filters,
        "listings": listings,
        "knowledge": knowledge,
        "chunks": semantic_chunks,
        "debug": {
            "candidate_models": [f"{brand} {model}" for brand, model in candidate_pairs],
            "retrieval_mode": "structured_filters_plus_semantic_chunks",
            "embedding_search_enabled": bool(semantic_chunks),
            "embedding_model": LocalHashEmbeddingProvider.model,
            "semantic_chunk_count": len(semantic_chunks),
        },
    }
