"""Action tools (design doc §7 `action_tools`) and the approval gate on
`guardrails.human_approval_required`."""

import pytest


def test_draft_email_blocks_for_an_active_investigator(hcp_agent, active_investigator_hcp):
    """The Context Package's own `constraints` block — not a separate
    check re-derived here — is what stops this draft."""
    result = hcp_agent.draft_email(active_investigator_hcp, task="biomarker testing outreach")
    assert result["status"] == "blocked"
    assert "promotional exclusion" in result["reason"].lower()


def test_draft_email_executes_for_an_hcp_without_that_constraint(hcp_agent):
    result = hcp_agent.draft_email("HCP-001", task="biomarker testing outreach")
    assert result["status"] == "executed"
    assert "biomarker testing outreach" in result["subject"] or result["subject"].startswith("Following up")
    assert result["body"]


def test_create_campaign_task_executes_for_approved_content(hcp_agent, assembler):
    content = assembler.find_content(approval_status="approved")[0]
    result = hcp_agent.create_campaign_task("HCP-001", content["id"])
    assert result["status"] == "executed"
    assert result["content_id"] == content["id"]


def test_create_campaign_task_blocks_for_unknown_content(hcp_agent):
    result = hcp_agent.create_campaign_task("HCP-001", "CNT-does-not-exist")
    assert result["status"] == "blocked"


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


def test_approving_an_unknown_id_raises(approval_queue):
    with pytest.raises(KeyError):
        approval_queue.approve("appr-does-not-exist")
