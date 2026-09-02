"""End-to-end proof of the week-6 demo thesis: same entity, two purposes,
two different Context Packages, at the ContextAssembler level."""


def test_same_entity_two_purposes_different_facts(assembler, active_investigator_hcp):
    commercial_pkg = assembler.get_context_package(
        active_investigator_hcp, "commercial_engagement", principal="u1", principal_roles=["brand_manager"]
    )
    clinical_pkg = assembler.get_context_package(
        active_investigator_hcp, "site_selection", principal="u2", principal_roles=["clinical_ops"]
    )

    assert commercial_pkg["lineage_id"] != clinical_pkg["lineage_id"]
    assert commercial_pkg["scope_applied"] != clinical_pkg["scope_applied"]
    assert {f["domain"] for f in commercial_pkg["facts"]} <= {"commercial", "medical"}
    assert {f["domain"] for f in clinical_pkg["facts"]} == {"clinical"}


def test_commercial_purpose_never_sees_msl_or_study_detail(assembler, active_investigator_hcp):
    pkg = assembler.get_context_package(
        active_investigator_hcp, "commercial_engagement", principal="u1", principal_roles=["brand_manager"]
    )
    assert not any(f["domain"] == "medical" and "inquiry" in f["claim"].lower() for f in pkg["facts"])
    assert not any("STUDY" in f["claim"] or "PROTO" in f["claim"] for f in pkg["facts"])
    # the investigator status still reaches the agent, but only as a flag
    assert any("investigator" in c.lower() for c in pkg["constraints"])


def test_site_selection_purpose_never_sees_commercial_data(assembler, active_investigator_hcp):
    pkg = assembler.get_context_package(
        active_investigator_hcp, "site_selection", principal="u2", principal_roles=["clinical_ops"]
    )
    assert not any(f["domain"] == "commercial" for f in pkg["facts"])
    assert pkg["scope_applied"]["bridges"] == []
    assert any(e["domain"] == "commercial" for e in pkg["excluded"])


def test_redaction_removes_personal_email(assembler):
    pkg = assembler.get_context_package(
        "HCP-001", "commercial_engagement", principal="u1", principal_roles=["brand_manager"]
    )
    assert "personal_email" not in pkg["profile"]


def test_every_package_is_audited(assembler, active_investigator_hcp):
    before = len(assembler.audit_log.entries)
    assembler.get_context_package(
        active_investigator_hcp, "commercial_engagement", principal="u1", principal_roles=["brand_manager"]
    )
    assert len(assembler.audit_log.entries) == before + 1
    last = assembler.audit_log.entries[-1]
    assert last["request"]["purpose"] == "commercial_engagement"
    assert "lineage_id" in last


def test_find_content_only_returns_approved(assembler):
    results = assembler.find_content(topic="", audience="")
    assert results  # sanity: fixtures include approved content
    assert all(r["approval"] == "approved" for r in results)
