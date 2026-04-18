CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS ingestion_runs (
  id BIGSERIAL PRIMARY KEY,
  started_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  completed_at TIMESTAMPTZ,
  status TEXT NOT NULL,
  listings_count INTEGER NOT NULL DEFAULT 0,
  knowledge_count INTEGER NOT NULL DEFAULT 0,
  eval_count INTEGER NOT NULL DEFAULT 0,
  message TEXT
);

CREATE TABLE IF NOT EXISTS listings (
  listing_id TEXT PRIMARY KEY,
  title TEXT NOT NULL,
  brand TEXT NOT NULL,
  model TEXT NOT NULL,
  year INTEGER,
  price INTEGER,
  mileage INTEGER,
  transmission TEXT,
  fuel_type TEXT,
  seller_type TEXT,
  location TEXT,
  body_type TEXT,
  source TEXT NOT NULL,
  source_url TEXT,
  description TEXT,
  raw_payload JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_listings_brand_model ON listings (brand, model);
CREATE INDEX IF NOT EXISTS idx_listings_price ON listings (price);
CREATE INDEX IF NOT EXISTS idx_listings_body_type ON listings (body_type);
CREATE INDEX IF NOT EXISTS idx_listings_location ON listings (location);

CREATE TABLE IF NOT EXISTS knowledge_sources (
  source_id TEXT PRIMARY KEY,
  source_type TEXT NOT NULL,
  source_channel TEXT NOT NULL,
  title TEXT NOT NULL,
  brand TEXT NOT NULL,
  model TEXT NOT NULL,
  year_range TEXT,
  market TEXT,
  tags TEXT[] NOT NULL DEFAULT '{}',
  summary TEXT,
  text TEXT NOT NULL,
  evidence_level TEXT,
  ownership_stage TEXT,
  raw_payload JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_knowledge_brand_model ON knowledge_sources (brand, model);
CREATE INDEX IF NOT EXISTS idx_knowledge_source_type ON knowledge_sources (source_type);
CREATE INDEX IF NOT EXISTS idx_knowledge_tags ON knowledge_sources USING GIN (tags);

CREATE TABLE IF NOT EXISTS document_chunks (
  chunk_id TEXT PRIMARY KEY,
  source_id TEXT NOT NULL REFERENCES knowledge_sources(source_id) ON DELETE CASCADE,
  chunk_index INTEGER NOT NULL,
  text TEXT NOT NULL,
  token_count INTEGER NOT NULL,
  metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_document_chunks_source_id ON document_chunks (source_id);

CREATE TABLE IF NOT EXISTS chunk_embeddings (
  chunk_id TEXT PRIMARY KEY REFERENCES document_chunks(chunk_id) ON DELETE CASCADE,
  embedding_model TEXT NOT NULL,
  content_hash TEXT,
  embedding vector(1536) NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_chunk_embeddings_vector
  ON chunk_embeddings USING ivfflat (embedding vector_cosine_ops)
  WITH (lists = 100);

CREATE TABLE IF NOT EXISTS eval_cases (
  id TEXT PRIMARY KEY,
  query TEXT NOT NULL,
  expected_filters JSONB NOT NULL DEFAULT '{}'::jsonb,
  expected_candidate_models TEXT[] NOT NULL DEFAULT '{}',
  expected_risk_themes TEXT[] NOT NULL DEFAULT '{}',
  raw_payload JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS request_logs (
  id BIGSERIAL PRIMARY KEY,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  endpoint TEXT NOT NULL,
  query TEXT,
  filters JSONB NOT NULL DEFAULT '{}'::jsonb,
  listing_count INTEGER NOT NULL DEFAULT 0,
  knowledge_count INTEGER NOT NULL DEFAULT 0,
  latency_ms INTEGER,
  error TEXT
);
