export type Severity = "low" | "medium" | "high";

export type VehicleProfile = {
  profile_id: string;
  title: string;
  brand: string;
  model: string;
  generation_label?: string | null;
  facelift_label?: string | null;
  year_start: number;
  year_end: number;
  trim: string;
  engine_code?: string | null;
  engine_description: string;
  displacement_l?: number | null;
  transmission: string;
  drivetrain?: string | null;
  fuel_type: string;
  body_type: string;
  seat_count?: number | null;
  fuel_consumption_l_per_100km?: number | null;
  power_kw?: number | null;
  power_hp?: number | null;
  nvh_summary?: string | null;
  ride_handling_summary?: string | null;
  comfort_summary?: string | null;
  space_summary?: string | null;
  reliability_summary?: string | null;
  common_issues: string[];
  maintenance_cost_band?: string | null;
  suitability_summary?: string | null;
  estimated_price_min_nzd?: number | null;
  estimated_price_mid_nzd?: number | null;
  estimated_price_max_nzd?: number | null;
  valuation_confidence?: string | null;
  valuation_market?: string | null;
  valuation_as_of_date?: string | null;
  assumed_condition?: string | null;
  assumed_mileage_km?: number | null;
  valuation_method?: string | null;
  valuation_notes?: string | null;
};

export type KnowledgeSource = {
  source_id: string;
  source_type: string;
  source_channel: string;
  title: string;
  brand: string;
  model: string;
  year_range?: string | null;
  market?: string | null;
  profile_id?: string | null;
  generation_label?: string | null;
  trim?: string | null;
  powertrain_tags: string[];
  tags: string[];
  summary?: string | null;
  text: string;
  evidence_level?: string | null;
  ownership_stage?: string | null;
};

export type RetrievedChunk = {
  chunk_id: string;
  source_id: string;
  source_title: string;
  source_type: string;
  brand: string;
  model: string;
  profile_id?: string | null;
  evidence_level?: string | null;
  text: string;
  similarity?: number | null;
};

export type RetrieveRequest = {
  query?: string;
  budget_max?: number;
  brands?: string[];
  models?: string[];
  body_type?: string;
  fuel_type?: string;
  transmission?: string;
  limit?: number;
};

export type RetrieveResponse = {
  query?: string | null;
  applied_filters: Record<string, unknown>;
  vehicle_profiles: VehicleProfile[];
  knowledge: KnowledgeSource[];
  chunks: RetrievedChunk[];
  debug: Record<string, unknown>;
};

export type QuerySummary = {
  budget: string;
  usage: string;
  preferences: string[];
};

export type RecommendationRiskFlag = {
  label: string;
  severity: Severity;
  reason: string;
  evidence_ids: string[];
};

export type RecommendationEvidence = {
  id: string;
  source_type: string;
  title: string;
  snippet: string;
};

export type RecommendedProfile = {
  profile_id: string;
  title: string;
  match_score: number;
  powertrain_summary: string;
  why_it_matches: string[];
  trade_offs: string[];
  risk_flags: RecommendationRiskFlag[];
  valuation_summary: string;
  evidence_ids: string[];
  next_steps: string[];
};

export type RecommendRequest = {
  query?: string;
  selected_profile_ids: string[];
};

export type RecommendResponse = {
  query_summary: QuerySummary;
  recommended_profiles: RecommendedProfile[];
  evidence: RecommendationEvidence[];
  debug: Record<string, unknown>;
};

export type EvalSummary = {
  title: string;
  metrics: Array<{ label: string; value: string }>;
  weakestCases: string[];
};

export type AIProviderId = "deterministic" | "openai" | "deepseek" | "qwen" | "kimi";

export type ProviderConnectionSettings = {
  apiKeyConfigured: boolean;
  baseUrl: string;
  timeoutSeconds?: string;
};

export type AdminSettingsResponse = {
  envFilePath: string;
  recommendationProvider: AIProviderId;
  recommendationModel: string;
  providers: {
    openai: ProviderConnectionSettings;
    deepseek: ProviderConnectionSettings;
    qwen: ProviderConnectionSettings;
    kimi: ProviderConnectionSettings;
  };
};

export type ProviderConnectionUpdate = {
  apiKey?: string;
  baseUrl: string;
  timeoutSeconds?: string;
};

export type AdminSettingsUpdate = {
  recommendationProvider: AIProviderId;
  recommendationModel: string;
  providers: {
    openai: ProviderConnectionUpdate;
    deepseek: ProviderConnectionUpdate;
    qwen: ProviderConnectionUpdate;
    kimi: ProviderConnectionUpdate;
  };
};
