import copy

from context_layer.evaluation.policy_evaluator import evaluate_policy
from context_layer.evaluation.schemas import EvaluationCase


def _case(**overrides) -> EvaluationCase:
    defaults = dict(id="c", category="commercial_engagement", entity_id="HCP-001", question="q", forbidden_domains=["clinical"])
    defaults.update(overrides)
    return EvaluationCase(**defaults)


def test_real_commercial_package_is_compliant(assembler):
    package = assembler.get_context_package("HCP-001", "commercial_engagement", principal="u", principal_roles=["brand_manager"])
    result = evaluate_policy(_case(), package)
    assert result.policy_compliant
    assert result.violations == []


def test_flags_a_forbidden_domain_that_leaked_in(assembler):
    """Proves the check discriminates: a hand-broken package with a
    forbidden-domain fact injected must fail, not silently pass."""
    package = copy.deepcopy(assembler.get_context_package("HCP-001", "commercial_engagement", principal="u", principal_roles=["brand_manager"]))
    package["facts"].append({"claim": "leaked clinical detail", "source": "CTMS", "domain": "clinical", "confidence": 1.0, "bridge": None})

    result = evaluate_policy(_case(forbidden_domains=["clinical"]), package)
    assert not result.policy_compliant
    assert "clinical" in result.forbidden_domains_found


def test_flags_an_unbridged_foreign_domain_fact():
    """A fact whose domain isn't in scope and has no bridge id is a
    violation even if that domain isn't in the case's forbidden list —
    the mechanism itself (bridge tagging), not just the domain name, is
    what's being checked."""
    package = {
        "scope_applied": {"subgraphs": ["commercial"], "bridges": []},
        "facts": [{"claim": "x", "source": "s", "domain": "medical", "confidence": 1.0, "bridge": None}],
    }
    result = evaluate_policy(_case(forbidden_domains=[]), package)
    assert not result.policy_compliant


def test_a_bridged_foreign_domain_fact_is_not_a_violation():
    package = {
        "scope_applied": {"subgraphs": ["commercial"], "bridges": ["medical.publications->commercial"]},
        "facts": [{"claim": "x", "source": "PubMed", "domain": "medical", "confidence": 0.9, "bridge": "medical.publications->commercial"}],
    }
    result = evaluate_policy(_case(forbidden_domains=["clinical"]), package)
    assert result.policy_compliant
