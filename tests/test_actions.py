"""Action tools (design doc §7 `action_tools`) and the approval gate on
`guardrails.human_approval_required`."""

import pytest

from context_layer.agent_builder.agent import ThinAgent
from context_layer.agent_builder.builder import AgentValidationError, publish_agent
from context_layer.agent_builder.schema import AgentConfig, Guardrails


def test_draft_email_blocks_for_an_active_investigator(hcp_agent, active_investigator_hcp):
    """The Context Package's own `constraints` block — not a separate
    check re-derived here — is what stops this draft."""
    result = hcp_agent.draft_email(active_investigator_hcp, task="biomarker testing outreach")
    assert result["status"] == "blocked"
    assert "promotional exclusion" in result["reason"].lower()


def test_draft_email_requires_approval_when_not_blocked(hcp_agent):
    """draft_email is itself in this agent's human_approval_required list
    (it produces real outbound content) — even an unconstrained draft is
    held, never auto-sent."""
    result = hcp_agent.draft_email("HCP-001", task="biomarker testing outreach")
    assert result["status"] == "pending_approval"
    assert result["body"]


def test_create_campaign_task_executes_for_approved_content(hcp_agent, assembler):
    """Unlike draft_email, this action isn't gated — a lower-risk,
    internal-only side effect runs immediately."""
    content = assembler.find_content(approval_status="approved")[0]
    result = hcp_agent.create_campaign_task("HCP-001", content["id"])
    assert result["status"] == "executed"
    assert result["content_id"] == content["id"]


def test_create_campaign_task_blocks_for_unknown_content(hcp_agent):
    result = hcp_agent.create_campaign_task("HCP-001", "CNT-does-not-exist")
    assert result["status"] == "blocked"


def test_create_campaign_task_respects_approved_content_only_guardrail(assembler, approval_queue):
    non_approved = next(n for n in assembler.store.find_nodes(node_type="Content") if n["approval_status"] != "approved")

    strict_config = AgentConfig(
        name="Strict Agent",
        purpose="commercial_engagement",
        audience_roles=["brand_manager"],
        context_tools=["get_context_package"],
        action_tools=["create_campaign_task"],
        guardrails=Guardrails(approved_content_only=True),
    )
    lenient_config = AgentConfig(
        name="Lenient Agent",
        purpose="commercial_engagement",
        audience_roles=["brand_manager"],
        context_tools=["get_context_package"],
        action_tools=["create_campaign_task"],
        guardrails=Guardrails(approved_content_only=False),
    )
    strict_agent = ThinAgent(strict_config, assembler, approval_queue)
    lenient_agent = ThinAgent(lenient_config, assembler, approval_queue)

    assert strict_agent.create_campaign_task("HCP-001", non_approved["id"])["status"] == "blocked"
    assert lenient_agent.create_campaign_task("HCP-001", non_approved["id"])["status"] == "executed"


def test_create_feasibility_note_always_requires_approval(site_agent, active_investigator_hcp, approval_queue):
    before = len(approval_queue.pending())
    result = site_agent.create_feasibility_note(active_investigator_hcp, "Recommend for Phase 3 expansion.")
    assert result["status"] == "pending_approval"
    assert len(approval_queue.pending()) == before + 1

    approved = approval_queue.approve(result["approval_id"])
    assert approved.status == "approved"
    assert approved.approved_at is not None


def test_feasibility_note_carries_the_supporting_fact(site_agent, active_investigator_hcp):
    result = site_agent.create_feasibility_note(active_investigator_hcp, "note")
    assert result["supporting_fact"] is not None
    assert "Principal investigator" in result["supporting_fact"]


def test_agent_cannot_call_an_action_it_was_not_configured_with(site_agent, active_investigator_hcp):
    with pytest.raises(PermissionError):
        site_agent.draft_email(active_investigator_hcp)


def test_authorization_is_checked_before_any_business_logic(assembler, approval_queue, active_investigator_hcp):
    """An agent with no action_tools at all must be refused outright —
    never a 'blocked' result that would mean the draft/lookup logic ran
    for an action it was never authorized to use."""
    unauthorized_config = AgentConfig(
        name="Unauthorized Agent",
        purpose="commercial_engagement",
        audience_roles=["brand_manager"],
        context_tools=["get_context_package"],
        action_tools=[],
    )
    agent = ThinAgent(unauthorized_config, assembler, approval_queue)

    with pytest.raises(PermissionError):
        agent.draft_email(active_investigator_hcp)  # would otherwise be "blocked" by the constraint
    with pytest.raises(PermissionError):
        agent.create_campaign_task("HCP-001", "CNT-does-not-exist")  # would otherwise be "blocked" as unknown content


def test_approving_an_unknown_id_raises(approval_queue):
    with pytest.raises(KeyError):
        approval_queue.approve("appr-does-not-exist")


def test_builder_rejects_a_guardrail_naming_an_action_not_declared():
    bad = AgentConfig(
        name="Bad Agent",
        purpose="commercial_engagement",
        audience_roles=["brand_manager"],
        context_tools=["get_context_package"],
        action_tools=["draft_email", "create_campaign_task"],
        guardrails=Guardrails(human_approval_required=["send_email"]),  # not an action_tool
    )
    with pytest.raises(AgentValidationError):
        publish_agent(bad)
