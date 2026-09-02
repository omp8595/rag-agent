"""The brand-manager promotional campaign workflow (scripts/campaign_workflow.py)
— a GraphRAG-driven targeting pipeline built entirely on the HCP Engagement
Agent's own tools. These tests check the workflow's own logic (targeting,
compliance exclusion, approval state), not the agent internals already
covered by test_actions.py and test_graphrag.py."""

from scripts.campaign_workflow import build_campaign


def test_targeting_is_differentiated_not_blanket():
    """GraphRAG-driven targeting must actually discriminate: some HCPs'
    commercial engagement history names the topic, most won't."""
    report, _approvals = build_campaign("Biomarker testing")
    assert report["candidates"] == 50
    assert 0 < len(report["on_topic"]) < report["candidates"]
    for entry in report["on_topic"]:
        assert "biomarker testing" in entry["community_summary"].lower()


def test_compliance_excluded_hcps_are_never_drafted():
    report, _approvals = build_campaign("Biomarker testing")
    excluded_ids = {e["hcp_id"] for e in report["excluded_compliance"]}
    drafted_ids = {e["hcp_id"] for e in report["drafted"]}
    assert excluded_ids.isdisjoint(drafted_ids)
    assert len(report["on_topic"]) == len(report["excluded_compliance"]) + len(report["drafted"])


def test_drafts_start_pending_until_a_human_approves():
    report, approvals = build_campaign("Biomarker testing")
    assert len(approvals.pending()) == len(report["drafted"])


def test_a_topic_with_no_matching_engagement_yields_an_empty_campaign():
    report, _approvals = build_campaign("this topic does not exist in the synthetic corpus")
    assert report["on_topic"] == []
    assert report["drafted"] == []
