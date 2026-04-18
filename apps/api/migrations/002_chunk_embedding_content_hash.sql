ALTER TABLE chunk_embeddings
  ADD COLUMN IF NOT EXISTS content_hash TEXT;

CREATE INDEX IF NOT EXISTS idx_chunk_embeddings_model_hash
  ON chunk_embeddings (embedding_model, content_hash);
