"""GraphRAG-lite (design doc §4.3) wired into the Context Package —
`community_summary` must reflect only the domain(s) the purpose was
actually granted, never anything reachable only via a bridge."""

from context_layer.retrieval.graphrag import community_summary as raw_summary


def test_community_summary_matches_the_domain_scoped_computation_exactly(assembler):
    """The assembler's summary for a commercial-purpose request must equal
    calling the same domain-scoped function directly with domain='commercial'
    — proving nothing else got folded in, even though this purpose is
    granted bridges into medical and clinical for *facts*."""
    pkg = assembler.get_context_package("HCP-001", "commercial_engagement", principal="u", principal_roles=["brand_manager"])
    expected = raw_summary(assembler.store, "HCP-001", domain="commercial", max_hops=2)
    assert pkg["community_summary"] == expected


def test_community_summary_differs_by_purpose_for_the_same_entity(assembler):
    commercial_pkg = assembler.get_context_package("HCP-001", "commercial_engagement", principal="u", principal_roles=["brand_manager"])
    medical_pkg = assembler.get_context_package("HCP-001", "medical_inquiry", principal="u", principal_roles=["msl"])
    assert commercial_pkg["community_summary"] != medical_pkg["community_summary"]
    assert commercial_pkg["community_summary"].startswith("Within commercial,")
    assert medical_pkg["community_summary"].startswith("Within medical,")


def test_community_summary_is_none_when_the_entity_has_no_activity_in_scope(assembler, source_data):
    """An HCP with zero clinical involvement gets no summary rather than a
    fabricated or empty-string one — this purpose has no publications or
    MSL text corpus to summarize, since site_selection grants no bridges."""
    investigator_ids = {r["hcp_id"] for r in source_data["investigator_sites"]}
    non_investigator = next(h["id"] for h in source_data["hcps"] if h["id"] not in investigator_ids)
    pkg = assembler.get_context_package(non_investigator, "site_selection", principal="u", principal_roles=["clinical_ops"])
    assert pkg["community_summary"] is None
