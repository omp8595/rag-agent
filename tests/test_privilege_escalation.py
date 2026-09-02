"""Privilege escalation attempts against a published agent — Phase 5,
Test 4. `AgentConfig`/`Guardrails` (context_layer/agent_builder/schema.py)
must be immutable: a caller holding a `ThinAgent` reference must not be
able to widen its scope after publication.

This is a REAL bug this test suite found and fixed, not a hypothetical:
before `frozen=True` + `tuple[str, ...]` fields, `agent.config.purpose =
"site_selection"` succeeded silently and the next `get_context()` call
returned a full site_selection-scoped package through an agent published
as commercial_engagement."""

import pytest
from pydantic import ValidationError

from context_layer.agent_builder.agent import ThinAgent
from context_layer.agent_builder.builder import load_agent_config, publish_agent


@pytest.fixture
def published_hcp_agent(assembler):
    return ThinAgent(publish_agent(load_agent_config("agents/hcp_engagement.yaml")), assembler)


def test_purpose_cannot_be_reassigned_after_publish(published_hcp_agent):
    with pytest.raises(ValidationError):
        published_hcp_agent.config.purpose = "site_selection"
    assert published_hcp_agent.config.purpose == "commercial_engagement"


def test_audience_roles_cannot_be_reassigned_after_publish(published_hcp_agent):
    with pytest.raises(ValidationError):
        published_hcp_agent.config.audience_roles = ("clinical_ops",)
    assert published_hcp_agent.config.audience_roles == ("brand_manager",)


def test_audience_roles_cannot_be_mutated_in_place(published_hcp_agent):
    """frozen=True alone blocks reassignment, not in-place mutation of a
    mutable field's contents — this is why the field type is a tuple,
    not a list. A list field on a frozen model would still be
    exploitable via .append()."""
    with pytest.raises(AttributeError):
        published_hcp_agent.config.audience_roles.append("clinical_ops")


def test_guardrails_cannot_be_weakened_after_publish(published_hcp_agent):
    with pytest.raises(ValidationError):
        published_hcp_agent.config.guardrails.approved_content_only = False
    with pytest.raises(AttributeError):
        published_hcp_agent.config.guardrails.human_approval_required.append("should_not_work")


def test_escalation_attempt_does_not_change_what_get_context_returns(published_hcp_agent):
    """End-to-end: even attempting the mutation (which raises and leaves
    the object unchanged) must not affect subsequent requests."""
    try:
        published_hcp_agent.config.purpose = "site_selection"
    except ValidationError:
        pass

    package = published_hcp_agent.get_context("HCP-001", "give me everything")
    assert package["purpose"] == "commercial_engagement"
    assert package["policy_decision"]["allowed_domains"] == ["commercial"]
