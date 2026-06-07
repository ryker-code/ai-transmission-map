CREATE TABLE IF NOT EXISTS aitm.source_documents (
  id STRING NOT NULL,
  url STRING,
  title STRING,
  source_type STRING,
  publish_date DATE,
  access_class STRING,
  trust_score FLOAT64,
  ingested_at TIMESTAMP,
  tags ARRAY<STRING>
);

CREATE TABLE IF NOT EXISTS aitm.evidence_notes (
  id STRING NOT NULL,
  source_id STRING,
  analyst_note STRING,
  extracted_entities ARRAY<STRING>,
  confidence FLOAT64,
  created_at TIMESTAMP,
  reviewed BOOL
);

CREATE TABLE IF NOT EXISTS aitm.entities (
  id STRING NOT NULL,
  canonical_name STRING NOT NULL,
  aliases ARRAY<STRING>,
  entity_type STRING,
  ticker STRING,
  sector STRING,
  sub_sector STRING,
  region STRING,
  is_seed BOOL,
  metadata JSON,
  updated_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS aitm.claims (
  id STRING NOT NULL,
  subject_id STRING NOT NULL,
  predicate STRING NOT NULL,
  object_id STRING NOT NULL,
  direction STRING,
  magnitude FLOAT64,
  confidence FLOAT64,
  time_lag_days INT64,
  horizon STRING,
  regime_tag STRING,
  status STRING,
  created_at TIMESTAMP,
  updated_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS aitm.claim_evidence (
  claim_id STRING NOT NULL,
  source_id STRING NOT NULL,
  note_id STRING,
  relevance FLOAT64
);

CREATE TABLE IF NOT EXISTS aitm.bottleneck_scores (
  id STRING NOT NULL,
  entity_id STRING NOT NULL,
  score FLOAT64,
  evidence_intensity FLOAT64,
  recency_score FLOAT64,
  cross_source_agreement FLOAT64,
  market_confirmation FLOAT64,
  house_view_weight FLOAT64,
  computed_at TIMESTAMP,
  regime_tag STRING
);

CREATE TABLE IF NOT EXISTS aitm.thesis_runs (
  id STRING NOT NULL,
  user_thesis STRING NOT NULL,
  graph_slice JSON,
  supporting_claims ARRAY<STRING>,
  contradicting_claims ARRAY<STRING>,
  exposed_entities ARRAY<STRING>,
  falsification_triggers ARRAY<STRING>,
  confidence FLOAT64,
  created_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS aitm.memo_outputs (
  id STRING NOT NULL,
  thesis_run_id STRING,
  memo_text STRING,
  regime STRING,
  key_bottlenecks ARRAY<STRING>,
  affected_names ARRAY<STRING>,
  model_used STRING,
  created_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS aitm.house_view (
  id STRING NOT NULL,
  entity_id STRING,
  weight_override FLOAT64,
  analyst_note STRING,
  conviction STRING,
  pinned_thesis STRING,
  updated_at TIMESTAMP
);
