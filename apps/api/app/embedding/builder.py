from __future__ import annotations

from sqlalchemy import select

from app.db.connection import get_session
from app.db.orm import ChunkEmbeddingRecord, DocumentChunkRecord
from app.embedding.service import LocalHashEmbeddingProvider, chunk_content_hash


def build_chunk_embeddings(limit: int | None = None) -> dict[str, int | str]:
    provider = LocalHashEmbeddingProvider()
    embedded_count = 0
    skipped_count = 0
    scanned_count = 0

    with get_session() as session:
        statement = (
            select(DocumentChunkRecord, ChunkEmbeddingRecord)
            .outerjoin(ChunkEmbeddingRecord, ChunkEmbeddingRecord.chunk_id == DocumentChunkRecord.chunk_id)
            .order_by(DocumentChunkRecord.source_id, DocumentChunkRecord.chunk_index)
        )

        for chunk, existing_embedding in session.execute(statement):
            scanned_count += 1
            content_hash = chunk_content_hash(chunk.text)
            if (
                existing_embedding is not None
                and existing_embedding.embedding_model == provider.model
                and existing_embedding.content_hash == content_hash
            ):
                skipped_count += 1
                continue

            session.merge(
                ChunkEmbeddingRecord(
                    chunk_id=chunk.chunk_id,
                    embedding_model=provider.model,
                    content_hash=content_hash,
                    embedding=provider.embed(chunk.text),
                )
            )
            embedded_count += 1

            if limit is not None and embedded_count >= limit:
                break

    return {
        "embedding_model": provider.model,
        "scanned_chunks": scanned_count,
        "embedded_chunks": embedded_count,
        "skipped_chunks": skipped_count,
    }
