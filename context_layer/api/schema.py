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


class ContextPackage(BaseModel):
    entity: EntityRef
    purpose: str
    scope_applied: ScopeApplied
    profile: dict
    facts: list[FactEntry]
    relationships: list[RelationshipEntry]
    recommended_content: list[ContentRec]
    constraints: list[str]
    excluded: list[ExclusionEntry]
    lineage_id: str
