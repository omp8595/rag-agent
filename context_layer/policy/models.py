"""Request / RetrievalScope schema — design doc section 5."""

from __future__ import annotations

from pydantic import BaseModel, Field


class PolicyRequest(BaseModel):
    principal: str
    principal_roles: list[str]
    purpose: str
    entity_id: str
    task: str = ""  # free text, for relevance ranking only — never for access decisions


class RetrievalScope(BaseModel):
    purpose: str
    subgraphs: list[str]
    bridges: list[str]
    indexes: list[str]
    max_hops: int
    redactions: list[str] = Field(default_factory=list)


class PolicyDenied(Exception):
    def __init__(self, reason: str):
        self.reason = reason
        super().__init__(reason)
