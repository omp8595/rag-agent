"""The Context Package envelope (Phase 3): agent/policy_decision/retrieval/
context/lineage/governance/audit, additive on top of the original flat
fields every existing caller reads."""

from context_layer.api.schema import ContextPackage


def test_envelope_validates_against_the_pydantic_schema(assembler):
    package = assembler.get_context_package(
        "HCP-021", "commercial_engagement", task="biomarker testing", principal="HCP Engagement Agent", principal_roles=["brand_manager"]
    )
    validated = ContextPackage.model_validate(package)  # raises on mismatch
    assert validated.request_id == package["lineage_id"]


def test_policy_decision_matches_scope_applied(assembler):
    package = assembler.get_context_package("HCP-001", "commercial_engagement", principal="u", principal_roles=["brand_manager"])
    assert package["policy_decision"]["allowed_domains"] == package["scope_applied"]["subgraphs"]
    assert package["policy_decision"]["allowed_bridges"] == package["scope_applied"]["bridges"]
    assert package["policy_decision"]["allowed"] is True


def test_governance_domains_accessed_matches_observed_fact_domains(assembler):
    package = assembler.get_context_package("HCP-021", "commercial_engagement", principal="u", principal_roles=["brand_manager"])
    assert set(package["governance"]["domains_accessed"]) == {f["domain"] for f in package["facts"]}
    assert set(package["governance"]["bridges_used"]) == {f["bridge"] for f in package["facts"] if f["bridge"]}


def test_lineage_list_has_one_entry_per_fact_with_matching_ids(assembler):
    package = assembler.get_context_package("HCP-021", "commercial_engagement", principal="u", principal_roles=["brand_manager"])
    assert len(package["lineage"]) == len(package["facts"])
    assert [entry["fact_id"] for entry in package["lineage"]] == [f["fact_id"] for f in package["facts"]]
    assert all(entry["fact_id"] for entry in package["lineage"])


def test_fact_ids_are_sequential_and_unique(assembler):
    package = assembler.get_context_package("HCP-021", "commercial_engagement", principal="u", principal_roles=["brand_manager"])
    ids = [f["fact_id"] for f in package["facts"]]
    assert ids == sorted(ids)
    assert len(ids) == len(set(ids))


def test_agent_block_reflects_the_caller(assembler):
    package = assembler.get_context_package(
        "HCP-001", "commercial_engagement", principal="HCP Engagement Agent", principal_roles=["brand_manager"]
    )
    assert package["agent"] == {"agent_id": "HCP Engagement Agent", "role": "brand_manager", "purpose": "commercial_engagement"}
