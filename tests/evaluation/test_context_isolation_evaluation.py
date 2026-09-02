import copy

from context_layer.evaluation.isolation_evaluator import evaluate_isolation


def test_same_hcp_two_purposes_is_isolated_and_differs(assembler, active_investigator_hcp):
    package_a = assembler.get_context_package(active_investigator_hcp, "commercial_engagement", principal="u", principal_roles=["brand_manager"])
    package_b = assembler.get_context_package(active_investigator_hcp, "site_selection", principal="u", principal_roles=["clinical_ops"])

    result = evaluate_isolation(package_a, package_b)
    assert result.packages_differ is True
    assert result.forbidden_domain_leak == []
    assert result.isolation_score == 1.0


def test_detects_a_leak_of_a_domain_exclusive_to_the_other_purpose(assembler, active_investigator_hcp):
    """Proves the check discriminates: injecting an unbridged clinical
    fact into the commercial package must be caught as a leak, since
    clinical is exclusive to site_selection's scope here."""
    package_a = copy.deepcopy(
        assembler.get_context_package(active_investigator_hcp, "commercial_engagement", principal="u", principal_roles=["brand_manager"])
    )
    package_b = assembler.get_context_package(active_investigator_hcp, "site_selection", principal="u", principal_roles=["clinical_ops"])
    package_a["facts"].append({"claim": "leaked", "source": "CTMS", "domain": "clinical", "confidence": 1.0, "bridge": None})

    result = evaluate_isolation(package_a, package_b)
    assert "clinical" in result.forbidden_domain_leak
    assert result.isolation_score == 0.0


def test_identical_packages_are_not_isolated():
    package = {"entity": {"id": "HCP-001"}, "purpose": "commercial_engagement", "facts": [], "scope_applied": {"subgraphs": ["commercial"]}}
    result = evaluate_isolation(package, package)
    assert result.packages_differ is False
    assert result.isolation_score == 0.0
