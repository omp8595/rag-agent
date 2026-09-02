"""Agent Builder config schema — design doc section 7.

Both models are frozen and use tuples, not lists, for every field a
security decision depends on. That's not stylistic: a plain mutable
`BaseModel` with `list[str]` fields means "purpose is fixed at publish
time, never a runtime parameter" is only a comment — `agent.config.purpose
= "site_selection"` (or `agent.config.audience_roles.append(...)` on an
unfrozen model with a mutable list, which `frozen=True` alone does not
stop) succeeds silently and re-scopes every subsequent request through
that agent. `frozen=True` blocks attribute reassignment; `tuple[str, ...]`
additionally removes in-place mutation (`.append`/`.remove`) of the
collection fields, since a frozen model's protection only covers the
attribute binding, not a mutable object already bound to it. See
tests/test_privilege_escalation.py for the exploit this closes.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class Guardrails(BaseModel):
    model_config = ConfigDict(frozen=True)

    approved_content_only: bool = True
    human_approval_required: tuple[str, ...] = Field(default_factory=tuple)
    max_context_hops: int = 2


class AgentConfig(BaseModel):
    model_config = ConfigDict(frozen=True)

    name: str
    purpose: str  # binds policy scope — fixed at publish time, never a runtime parameter
    audience_roles: tuple[str, ...]
    context_tools: tuple[str, ...]
    action_tools: tuple[str, ...] = Field(default_factory=tuple)
    guardrails: Guardrails = Field(default_factory=Guardrails)
