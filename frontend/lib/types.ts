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
