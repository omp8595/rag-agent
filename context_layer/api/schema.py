"""Context Package schema — design doc section 6."""

from __future__ import annotations

from pydantic import BaseModel


class EntityRef(BaseModel):
    id: str
    type: str
    display: str


class ScopeApplied(BaseModel):
    subgraphs: list[str]
    bridges: list[str]


class FactEntry(BaseModel):
    claim: str
    source: str
    domain: str
    confidence: float
    bridge: str | None = None
    fact_id: str
    source_id: str
    retrieval_method: str


class RelationshipEntry(BaseModel):
    type: str
    target: str
    display: str


class ContentRec(BaseModel):
    id: str
    title: str
    approval: str
    audience: str


class ExclusionEntry(BaseModel):
    domain: str
    reason: str


class AgentRef(BaseModel):
    agent_id: str
    role: str | None
    purpose: str


class PolicyDecision(BaseModel):
    allowed: bool
    allowed_domains: list[str]
    forbidden_domains: list[str]
    allowed_bridges: list[str]
    redactions: list[str]


class RetrievalBundle(BaseModel):
    entity_facts: list[str]
    graph_facts: list[FactEntry]
    vector_results: list[ContentRec]
    community_context: list[str]


class ContextBundle(BaseModel):
    facts: list[FactEntry]
    documents: list[ContentRec]
    summary: str | None


class LineageEntry(BaseModel):
    fact_id: str
    source_type: str
    source_id: str
    domain: str
    retrieval_method: str


class GovernanceInfo(BaseModel):
    domains_accessed: list[str]
    bridges_used: list[str]
    redactions_applied: list[str]


class AuditInfo(BaseModel):
    timestamp: str
    policy_version: str


class ContextPackage(BaseModel):
    """The central artifact of the Enterprise Context Layer. Two layers of
    fields, both always present:

    * The original, flat fields (`facts`, `constraints`, `excluded`, ...) —
      every existing caller and test reads these directly.
    * The envelope (`agent`, `policy_decision`, `retrieval`, `context`,
      `lineage`, `governance`, `audit`) — the same data reshaped into a
      self-describing artifact, so the package explains its own
      provenance and policy basis without a reader needing to know this
      module's internals.
    """

    entity: EntityRef
    purpose: str
    scope_applied: ScopeApplied
    profile: dict
    facts: list[FactEntry]
    relationships: list[RelationshipEntry]
    recommended_content: list[ContentRec]
    community_summary: str | None = None
    constraints: list[str]
    excluded: list[ExclusionEntry]
    lineage_id: str

    request_id: str
    agent: AgentRef
    policy_decision: PolicyDecision
    retrieval: RetrievalBundle
    context: ContextBundle
    lineage: list[LineageEntry]
    governance: GovernanceInfo
    audit: AuditInfo
