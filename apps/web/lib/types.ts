export type Severity = "low" | "medium" | "high";

export type Listing = {
  listing_id: string;
  title: string;
  brand: string;
  model: string;
  year?: number | null;
  price?: number | null;
  mileage?: number | null;
  transmission?: string | null;
  fuel_type?: string | null;
  seller_type?: string | null;
  location?: string | null;
  body_type?: string | null;
  source: string;
  source_url?: string | null;
  description?: string | null;
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
  evidence_level?: string | null;
  text: string;
  similarity?: number | null;
};

export type RetrieveRequest = {
  query?: string;
  max_price?: number;
  brand?: string;
  brands?: string[];
  models?: string[];
  body_type?: string;
  location?: string;
  limit?: number;
};

export type RetrieveResponse = {
  query?: string | null;
  applied_filters: Record<string, unknown>;
  listings: Listing[];
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

export type RecommendedCar = {
  listing_id: string;
  title: string;
  match_score: number;
  why_it_matches: string[];
  risk_flags: RecommendationRiskFlag[];
  price_commentary: string;
  evidence_ids: string[];
  next_steps: string[];
};

export type RecommendRequest = RetrieveRequest;

export type RecommendResponse = {
  query_summary: QuerySummary;
  recommended_cars: RecommendedCar[];
  evidence: RecommendationEvidence[];
  debug: Record<string, unknown>;
};

export type EvalSummary = {
  title: string;
  metrics: Array<{ label: string; value: string }>;
  weakestCases: string[];
};
