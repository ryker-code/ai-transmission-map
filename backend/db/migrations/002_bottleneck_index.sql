-- Migration 002: Add entity_id index view for bottleneck queries
-- BigQuery doesn't have traditional indexes, but this clustered view
-- speeds up the bottleneck ranking query pattern.

CREATE OR REPLACE VIEW `{project}.aitm.v_top_bottlenecks` AS
SELECT
  bs.entity_id,
  e.canonical_name AS entity_name,
  e.entity_type,
  e.sector,
  e.ticker,
  bs.score,
  bs.evidence_intensity,
  bs.recency_score,
  bs.cross_source_agreement,
  bs.market_confirmation,
  bs.house_view_weight,
  bs.computed_at,
  bs.regime_tag,
  ROW_NUMBER() OVER (
    PARTITION BY bs.entity_id
    ORDER BY bs.computed_at DESC
  ) AS rn
FROM `{project}.aitm.bottleneck_scores` bs
JOIN `{project}.aitm.entities` e ON e.id = bs.entity_id
WHERE bs.score IS NOT NULL
QUALIFY rn = 1
ORDER BY bs.score DESC;
