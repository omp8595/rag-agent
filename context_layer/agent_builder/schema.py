"""Agent Builder config schema — design doc section 7."""

from __future__ import annotations

from pydantic import BaseModel, Field


class Guardrails(BaseModel):
    approved_content_only: bool = True
    human_approval_required: list[str] = Field(default_factory=list)
    max_context_hops: int = 2


class AgentConfig(BaseModel):
    name: str
    purpose: str  # binds policy scope — fixed at publish time, never a runtime parameter
    audience_roles: list[str]
    context_tools: list[str]
    action_tools: list[str] = Field(default_factory=list)
    guardrails: Guardrails = Field(default_factory=Guardrails)
