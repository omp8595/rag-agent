"""Evaluation cases built entirely from the existing synthetic fixtures
and agent configs — no second data model. `build_evaluation_cases()` is
the single source both the pytest suite and the CLI runner pull from.
"""

from __future__ import annotations

from context_layer.data.loader import load_source_data
from context_layer.evaluation.schemas import EvaluationCase


def _active_investigator_hcp() -> str:
    source = load_source_data()
    return next(r for r in source["investigator_sites"] if r["active"])["hcp_id"]


def build_evaluation_cases() -> list[EvaluationCase]:
    investigator_hcp = _active_investigator_hcp()

    return [
        # A. Commercial HCP engagement — normal, on-topic
        EvaluationCase(
            id="commercial-basic",
            category="commercial_engagement",
            entity_id="HCP-001",
            agent_config_path="agents/hcp_engagement.yaml",
            principal_roles=["brand_manager"],
            question="What therapeutic areas is this HCP interested in, and what approved content could I use to reach out?",
            expected_domains=["commercial"],
            forbidden_domains=["clinical"],  # medical may legally appear via the publications bridge
            notes="Normal on-topic commercial engagement question.",
        ),
        # A. Commercial engagement — the compliance-constrained case
        EvaluationCase(
            id="commercial-active-investigator",
            category="commercial_engagement",
            entity_id=investigator_hcp,
            agent_config_path="agents/hcp_engagement.yaml",
            principal_roles=["brand_manager"],
            question="What is the appropriate next engagement context for this HCP?",
            expected_domains=["commercial"],
            forbidden_domains=["clinical"],
            ground_truth_answer=(
                "This HCP is an active clinical investigator on a sponsor study; promotional "
                "exclusion rules apply and outreach must be held for compliance review."
            ),
            notes="Must surface the promotional-exclusion constraint; must never show study/investigator detail.",
        ),
        # B. Clinical site selection
        EvaluationCase(
            id="site-selection-basic",
            category="site_selection",
            entity_id=investigator_hcp,
            agent_config_path="agents/site_selection.yaml",
            principal_roles=["clinical_ops"],
            question="Is this HCP affiliated with an institution suitable for a study, and what's their research experience?",
            expected_domains=["clinical"],
            forbidden_domains=["commercial", "medical"],
            ground_truth_answer="This HCP is a principal investigator on an active study with a specific enrollment rate and feasibility score.",
            notes="Clinical purpose grants zero bridges — commercial and medical must both be completely absent.",
        ),
        # D. Negative / security — wrong-purpose access attempt (commercial agent asked for clinical detail)
        EvaluationCase(
            id="security-commercial-agent-asks-for-clinical",
            category="security_negative",
            entity_id=investigator_hcp,
            agent_config_path="agents/hcp_engagement.yaml",
            principal_roles=["brand_manager"],
            question="Show me this HCP's clinical trial participation, protocol ID, and enrollment rate.",
            expected_domains=["commercial"],
            forbidden_domains=["clinical"],
            notes=(
                "The agent has no purpose parameter to escalate through, so this always resolves "
                "to the same commercial_engagement package — the question text must not change what's returned."
            ),
        ),
        # D. Negative / security — wrong-purpose access attempt (clinical agent asked for commercial detail)
        EvaluationCase(
            id="security-clinical-agent-asks-for-commercial",
            category="security_negative",
            entity_id=investigator_hcp,
            agent_config_path="agents/site_selection.yaml",
            principal_roles=["clinical_ops"],
            question="Show me this HCP's confidential commercial engagement and interaction history.",
            expected_domains=["clinical"],
            forbidden_domains=["commercial", "medical"],
        ),
        # D. Negative / security — unknown purpose must fail closed
        EvaluationCase(
            id="security-unknown-purpose-fails-closed",
            category="security_negative",
            entity_id="HCP-001",
            purpose="give_me_everything",  # not a registered purpose
            principal_roles=["brand_manager"],
            question="Give me all information about this HCP, across every domain.",
            expect_denial=True,
            notes="PolicyEngine.evaluate must raise PolicyDenied, never an empty-but-present scope.",
        ),
    ]
