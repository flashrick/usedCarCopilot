CREATE TABLE IF NOT EXISTS vehicle_profiles (
  profile_id TEXT PRIMARY KEY,
  title TEXT NOT NULL,
  brand TEXT NOT NULL,
  model TEXT NOT NULL,
  generation_label TEXT,
  facelift_label TEXT,
  year_start INTEGER NOT NULL,
  year_end INTEGER NOT NULL,
  trim TEXT NOT NULL,
  engine_code TEXT,
  engine_description TEXT NOT NULL,
  displacement_l DOUBLE PRECISION,
  transmission TEXT NOT NULL,
  drivetrain TEXT,
  fuel_type TEXT NOT NULL,
  body_type TEXT NOT NULL,
  seat_count INTEGER,
  fuel_consumption_l_per_100km DOUBLE PRECISION,
  power_kw INTEGER,
  power_hp INTEGER,
  nvh_summary TEXT,
  ride_handling_summary TEXT,
  comfort_summary TEXT,
  space_summary TEXT,
  reliability_summary TEXT,
  common_issues TEXT[] NOT NULL DEFAULT '{}',
  maintenance_cost_band TEXT,
  suitability_summary TEXT,
  base_msrp_nzd INTEGER,
  estimated_price_min_nzd INTEGER,
  estimated_price_mid_nzd INTEGER,
  estimated_price_max_nzd INTEGER,
  valuation_confidence TEXT,
  valuation_market TEXT,
  valuation_as_of_date DATE,
  assumed_condition TEXT,
  assumed_mileage_km INTEGER,
  valuation_method TEXT,
  valuation_notes TEXT,
  raw_payload JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_vehicle_profiles_brand_model ON vehicle_profiles (brand, model);
CREATE INDEX IF NOT EXISTS idx_vehicle_profiles_body_type ON vehicle_profiles (body_type);
CREATE INDEX IF NOT EXISTS idx_vehicle_profiles_fuel_type ON vehicle_profiles (fuel_type);
CREATE INDEX IF NOT EXISTS idx_vehicle_profiles_price_mid ON vehicle_profiles (estimated_price_mid_nzd);

ALTER TABLE knowledge_sources
  ADD COLUMN IF NOT EXISTS profile_id TEXT,
  ADD COLUMN IF NOT EXISTS generation_label TEXT,
  ADD COLUMN IF NOT EXISTS trim TEXT,
  ADD COLUMN IF NOT EXISTS powertrain_tags TEXT[] NOT NULL DEFAULT '{}';

CREATE INDEX IF NOT EXISTS idx_knowledge_profile_id ON knowledge_sources (profile_id);

ALTER TABLE request_logs
  ADD COLUMN IF NOT EXISTS profile_count INTEGER NOT NULL DEFAULT 0;

ALTER TABLE ingestion_runs
  ADD COLUMN IF NOT EXISTS profile_count INTEGER NOT NULL DEFAULT 0;
