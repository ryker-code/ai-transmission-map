export interface EvidenceIngest {
  url: string;
  title: string;
  source_type: "bloomberg" | "sec" | "utility_filing" | "public";
  publish_date?: string;
  analyst_note: string;
  tags: string[];
  trust_score: number;
}

export interface EvidenceResponse {
  source_id: string;
  note_id: string;
  extracted_entities: string[];
  claims_created: number;
  status: string;
}

export interface ClaimSummary {
  claim_id: string;
  subject: string;
  predicate: string;
  object: string;
  direction: string;
  confidence: number;
  horizon: string;
  regime_tag: string;
  extracted_by?: string;
  analyst_note?: string;
}

export interface MarketSignalEntry {
  ticker: string;
  rel_perf_30d: number;
  momentum: string;
  vol_percentile: number;
  market_confirmation_score: number;
}

export interface MarketSignalsResponse {
  signals: MarketSignalEntry[];
  last_updated: string;
  is_live: boolean;
}

export interface ModelStatusEntry {
  name: string;
  task_types: string[];
  call_count: number;
  avg_latency_ms: number;
  success_rate: number;
}

export interface ModelStatusResponse {
  models: ModelStatusEntry[];
  is_live: boolean;
  last_updated: string;
}

export interface EntityDetailResponse {
  id: string;
  canonical_name: string;
  entity_type: string;
  ticker?: string;
  sector?: string;
  sub_sector?: string;
  aliases: string[];
  bottleneck_score?: number;
  bottleneck_components?: Record<string, number>;
  outbound_claims: ClaimSummary[];
  inbound_claims: ClaimSummary[];
  house_view?: { conviction: string; weight_override: number; analyst_note?: string; pinned_thesis?: string };
  related_entities: { id: string; canonical_name: string; entity_type: string; claim_count: number }[];
}

export interface EntityCreate {
  canonical_name: string;
  aliases: string[];
  entity_type: "public_co" | "private_co" | "utility" | "asset" | "technology" | "geo" | "market";
  ticker?: string;
  sector?: string;
  sub_sector?: string;
  metadata?: Record<string, unknown>;
}

export interface EntityResponse extends EntityCreate {
  id: string;
  updated_at: string;
}

export interface GraphNode {
  id: string;
  label: string;
  entity_type: string;
  bottleneck_score?: number;
  sector?: string;
}

export interface GraphEdge {
  source: string;
  target: string;
  predicate: string;
  direction: string;
  confidence: number;
  horizon: string;
  claim_id?: string;
}

export interface EvidenceAuditEntry {
  source_id: string;
  title: string;
  source_type: string;
  url?: string;
  publish_date?: string;
  trust_score: number;
  analyst_note?: string;
}

export interface ClaimAuditResponse {
  claim_id: string;
  subject: string;
  predicate: string;
  object: string;
  direction: string;
  confidence: number;
  horizon: string;
  regime_tag: string;
  evidence: EvidenceAuditEntry[];
  supporting_sources: number;
  analyst_summary: string;
}

export interface GraphResponse {
  nodes: GraphNode[];
  edges: GraphEdge[];
  regime_tag?: string;
  computed_at: string;
}

export interface BottleneckEntry {
  entity_id: string;
  entity_name: string;
  score: number;
  rank: number;
  regime_tag: string;
  top_evidence: string[];
  components: Record<string, number>;
}

export interface BottlenecksResponse {
  bottlenecks: BottleneckEntry[];
  total: number;
  computed_at: string;
}

export interface ThesisRunRequest {
  thesis: string;
  depth: number;
  include_private: boolean;
  regime_filter?: string;
}

export interface ThesisRunResponse {
  run_id: string;
  thesis: string;
  support_score: number;
  contradiction_score: number;
  supporting_claims: Record<string, unknown>[];
  contradicting_claims: Record<string, unknown>[];
  exposed_entities: Record<string, unknown>[];
  falsification_triggers: string[];
  graph_slice: GraphResponse;
  created_at: string;
}

export interface MemoRequest {
  thesis_run_id: string;
  style: "buyside_lp" | "sellside_note" | "internal_brief";
  max_words: number;
}

export interface MemoResponse {
  memo_id: string;
  memo_text: string;
  regime: string;
  key_bottlenecks: string[];
  affected_names: string[];
  model_used: string;
  created_at: string;
}

export interface HouseViewUpdate {
  entity_id: string;
  weight_override: number;
  analyst_note?: string;
  conviction: "high" | "medium" | "low";
  pinned_thesis?: string;
}

export interface ClaimOverride {
  claim_id: string;
  confidence_override: number;
  direction_override?: "bullish" | "bearish" | "neutral";
}

export interface EntityWeightOverride {
  entity_id: string;
  weight_override: number;
}

export interface ScenarioRequest {
  base_run_id: string;
  scenario_name: string;
  claim_overrides: ClaimOverride[];
  entity_weight_overrides: EntityWeightOverride[];
}

export interface ScenarioResponse {
  scenario_id: string;
  scenario_name: string;
  base_run_id: string;
  support_score: number;
  contradiction_score: number;
  delta_support: number;
  delta_contradiction: number;
  changed_bottlenecks: { entity_id: string; entity_name: string; weight_override: number; direction: string }[];
  narrative: string;
}

export interface WatchlistEntry {
  entity_id: string;
  name: string;
  ticker?: string;
  bottleneck_score?: number;
  score_delta_24h: number;
  momentum: string;
  is_watched: boolean;
}

export interface WatchlistResponse {
  entries: WatchlistEntry[];
  total: number;
}

export interface RegimeTimelineEntry {
  timestamp: string;
  regime_tag: string;
  confidence: number;
  dominant_claim_count: number;
  note?: string;
}

export interface RegimeTimelineResponse {
  entries: RegimeTimelineEntry[];
  current_regime: string;
  computed_at: string;
}
