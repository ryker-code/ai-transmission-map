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

class HouseViewUpdate(BaseModel):
    entity_id: str
    weight_override: float = Field(1.0, ge=0.1, le=3.0)
    analyst_note: Optional[str] = None
    conviction: Literal["high","medium","low"]
    pinned_thesis: Optional[str] = None
