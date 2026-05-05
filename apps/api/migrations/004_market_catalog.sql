CREATE TABLE IF NOT EXISTS canonical_models (
  canonical_model_id TEXT PRIMARY KEY,
  brand TEXT NOT NULL,
  model TEXT NOT NULL,
  canonical_model_slug TEXT NOT NULL,
  aliases TEXT[] NOT NULL DEFAULT '{}',
  raw_payload JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_canonical_models_brand_slug
  ON canonical_models (brand, canonical_model_slug);

CREATE TABLE IF NOT EXISTS model_market_variants (
  market_variant_id TEXT PRIMARY KEY,
  canonical_model_id TEXT NOT NULL REFERENCES canonical_models(canonical_model_id) ON DELETE CASCADE,
  market TEXT NOT NULL,
  brand TEXT NOT NULL,
  model TEXT NOT NULL,
  display_name TEXT NOT NULL,
  local_aliases TEXT[] NOT NULL DEFAULT '{}',
  year_start INTEGER NOT NULL,
  year_end INTEGER NOT NULL,
  body_types TEXT[] NOT NULL DEFAULT '{}',
  fuel_types TEXT[] NOT NULL DEFAULT '{}',
  raw_payload JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_market_variants_canonical_market
  ON model_market_variants (canonical_model_id, market);

CREATE INDEX IF NOT EXISTS idx_market_variants_market_brand_display
  ON model_market_variants (market, brand, display_name);

CREATE TABLE IF NOT EXISTS model_popularity_rankings (
  market TEXT NOT NULL,
  market_variant_id TEXT NOT NULL REFERENCES model_market_variants(market_variant_id) ON DELETE CASCADE,
  popularity_rank INTEGER NOT NULL,
  brand_popularity_rank INTEGER NOT NULL,
  source_label TEXT NOT NULL,
  snapshot_date DATE NOT NULL,
  match_tags TEXT[] NOT NULL DEFAULT '{}',
  raw_payload JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  PRIMARY KEY (market, market_variant_id)
);

CREATE INDEX IF NOT EXISTS idx_popularity_market_rank
  ON model_popularity_rankings (market, popularity_rank, brand_popularity_rank);

ALTER TABLE vehicle_profiles
  ADD COLUMN IF NOT EXISTS market TEXT NOT NULL DEFAULT 'NZ',
  ADD COLUMN IF NOT EXISTS market_variant_id TEXT;

CREATE INDEX IF NOT EXISTS idx_vehicle_profiles_market_brand_model
  ON vehicle_profiles (market, brand, model);

CREATE INDEX IF NOT EXISTS idx_vehicle_profiles_market_variant
  ON vehicle_profiles (market, market_variant_id);

CREATE INDEX IF NOT EXISTS idx_vehicle_profiles_market_body_fuel_price
  ON vehicle_profiles (market, body_type, fuel_type, estimated_price_mid_nzd);

ALTER TABLE knowledge_sources
  ADD COLUMN IF NOT EXISTS market_variant_id TEXT;

CREATE INDEX IF NOT EXISTS idx_knowledge_market_brand_model
  ON knowledge_sources (market, brand, model);

CREATE INDEX IF NOT EXISTS idx_knowledge_market_variant
  ON knowledge_sources (market, market_variant_id);
