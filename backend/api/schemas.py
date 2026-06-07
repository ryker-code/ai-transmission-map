from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, List, Literal
from datetime import datetime

class EvidenceIngest(BaseModel):
    url: str
    title: str
    source_type: Literal["bloomberg","sec","utility_filing","public"]
    publish_date: Optional[str] = None
    analyst_note: str = Field(..., min_length=20)
    tags: List[str] = []
    trust_score: float = Field(0.7, ge=0.0, le=1.0)

class EvidenceResponse(BaseModel):
    source_id: str
    note_id: str
    extracted_entities: List[str]
    claims_created: int
    status: str
    transcript: Optional[str] = None

class EntityCreate(BaseModel):
    canonical_name: str
    aliases: List[str] = []
    entity_type: Literal["public_co","private_co","utility","asset","technology","geo","market"]
    ticker: Optional[str] = None
    sector: Optional[str] = None
    sub_sector: Optional[str] = None
    metadata: Optional[dict] = None

class EntityResponse(EntityCreate):
    id: str
    updated_at: datetime

class GraphNode(BaseModel):
    id: str
    label: str
    entity_type: str
    bottleneck_score: Optional[float] = None
    sector: Optional[str] = None

class GraphEdge(BaseModel):
    source: str
    target: str
    predicate: str
    direction: str
    confidence: float
    horizon: str
    claim_id: Optional[str] = None

class GraphResponse(BaseModel):
    nodes: List[GraphNode]
    edges: List[GraphEdge]
    regime_tag: Optional[str] = None
    computed_at: datetime

class BottleneckEntry(BaseModel):
    entity_id: str
    entity_name: str
    score: float
    rank: int
    regime_tag: str
    top_evidence: List[str]
    components: dict

class BottlenecksResponse(BaseModel):
    bottlenecks: List[BottleneckEntry]
    total: int
    computed_at: datetime

class ThesisRunRequest(BaseModel):
    thesis: str = Field(..., min_length=30)
    depth: int = Field(2, ge=1, le=4)
    include_private: bool = True
    regime_filter: Optional[str] = None

class ThesisRunResponse(BaseModel):
    run_id: str
    thesis: str
    support_score: float
    contradiction_score: float
    supporting_claims: List[dict]
    contradicting_claims: List[dict]
    exposed_entities: List[dict]
    falsification_triggers: List[str]
    graph_slice: GraphResponse
    created_at: datetime

class MemoRequest(BaseModel):
    thesis_run_id: str
    style: Literal["buyside_lp","sellside_note","internal_brief"] = "buyside_lp"
    max_words: int = 800

class MemoResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
    memo_id: str
    memo_text: str
    regime: str
    key_bottlenecks: List[str]
    affected_names: List[str]
    model_used: str
    created_at: datetime

class ClaimCreate(BaseModel):
    subject: str
    predicate: str
    object: str
    direction: str
    confidence: float
    horizon: str
    regime_tag: str
    extracted_by: Optional[str] = None
    rationale: Optional[str] = None

class ClaimSummary(BaseModel):
    claim_id: str
    subject: str
    predicate: str
    object: str
    direction: str
    confidence: float
    horizon: str
    regime_tag: str
    extracted_by: Optional[str] = None
    analyst_note: Optional[str] = None

class ModelStatusEntry(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
    name: str
    task_types: List[str]
    call_count: int
    avg_latency_ms: int
    success_rate: float

class ModelStatusResponse(BaseModel):
    models: List[ModelStatusEntry]
    is_live: bool = True
    last_updated: datetime

class EntityDetailResponse(BaseModel):
    id: str
    canonical_name: str
    entity_type: str
    ticker: Optional[str] = None
    sector: Optional[str] = None
    sub_sector: Optional[str] = None
    aliases: List[str] = []
    bottleneck_score: Optional[float] = None
    bottleneck_components: Optional[dict] = None
    outbound_claims: List[ClaimSummary] = []
    inbound_claims: List[ClaimSummary] = []
    house_view: Optional[dict] = None
    related_entities: List[dict] = []

class HouseViewUpdate(BaseModel):
    entity_id: str
    weight_override: float = Field(1.0, ge=0.1, le=3.0)
    analyst_note: Optional[str] = None
    conviction: Literal["high","medium","low"]
    pinned_thesis: Optional[str] = None

class EvidenceAuditEntry(BaseModel):
    source_id: str
    title: str
    source_type: str
    url: Optional[str] = None
    publish_date: Optional[str] = None
    trust_score: float
    analyst_note: Optional[str] = None

class ClaimAuditResponse(BaseModel):
    claim_id: str
    subject: str
    predicate: str
    object: str
    direction: str
    confidence: float
    horizon: str
    regime_tag: str
    evidence: List[EvidenceAuditEntry]
    supporting_sources: int
    analyst_summary: str

class MarketSignalEntry(BaseModel):
    ticker: str
    rel_perf_30d: float
    momentum: str
    vol_percentile: int
    market_confirmation_score: float

class MarketSignalsResponse(BaseModel):
    signals: List[MarketSignalEntry]
    last_updated: datetime
    is_live: bool = False

class ClaimOverride(BaseModel):
    claim_id: str
    confidence_override: float = Field(ge=0.0, le=1.0)
    direction_override: Optional[Literal["bullish", "bearish", "neutral"]] = None

class EntityWeightOverride(BaseModel):
    entity_id: str
    weight_override: float = Field(ge=0.1, le=3.0)

class ScenarioRequest(BaseModel):
    base_run_id: str
    scenario_name: str
    claim_overrides: List[ClaimOverride] = []
    entity_weight_overrides: List[EntityWeightOverride] = []

class ScenarioResponse(BaseModel):
    scenario_id: str
    scenario_name: str
    base_run_id: str
    support_score: float
    contradiction_score: float
    delta_support: float
    delta_contradiction: float
    changed_bottlenecks: List[dict]
    narrative: str

class RegimeTimelineEntry(BaseModel):
    timestamp: str
    regime_tag: str
    confidence: float
    dominant_claim_count: int
    note: Optional[str] = None

class RegimeTimelineResponse(BaseModel):
    entries: List[RegimeTimelineEntry]
    current_regime: str
    computed_at: datetime
