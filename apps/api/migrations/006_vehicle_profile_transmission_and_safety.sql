ALTER TABLE vehicle_profiles
  ADD COLUMN IF NOT EXISTS transmission_detail TEXT,
  ADD COLUMN IF NOT EXISTS transmission_maintenance_risk TEXT,
  ADD COLUMN IF NOT EXISTS transmission_risk_note TEXT,
  ADD COLUMN IF NOT EXISTS safety_rating_stars INTEGER,
  ADD COLUMN IF NOT EXISTS safety_rating_source TEXT,
  ADD COLUMN IF NOT EXISTS safety_rating_status TEXT;

CREATE INDEX IF NOT EXISTS idx_vehicle_profiles_market_safety_rating
  ON vehicle_profiles (market, safety_rating_stars);

CREATE INDEX IF NOT EXISTS idx_vehicle_profiles_market_transmission_risk
  ON vehicle_profiles (market, transmission_maintenance_risk);
