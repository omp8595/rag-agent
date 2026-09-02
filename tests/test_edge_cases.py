"""Phase 12 — edge cases. The system should fail predictably: a clear
exception or an empty, well-formed result — never a silent wrong answer
or an unhandled crash that takes down a batch of otherwise-good requests."""

import pytest

from context_layer.agent_builder.builder import AgentValidationError, load_agent_config, publish_agent
from context_layer.evaluation.datasets import EvaluationCase
from context_layer.evaluation.runner import run as run_evaluation
from context_layer.policy.models import PolicyDenied


def test_unknown_entity_raises_a_clear_error(assembler):
    with pytest.raises(ValueError, match="unknown entity"):
        assembler.get_context_package("HCP-does-not-exist", "commercial_engagement", principal="u", principal_roles=["brand_manager"])


def test_empty_task_yields_empty_recommended_content_not_an_error(assembler):
    package = assembler.get_context_package("HCP-001", "commercial_engagement", task="", principal="u", principal_roles=["brand_manager"])
    assert package["recommended_content"] == []
    assert package["facts"] is not None  # the rest of the package still assembles normally


def test_clinical_vector_index_is_empty_and_search_degrades_gracefully(assembler):
    """The clinical domain has no free-text corpus in this prototype
    (structured fields only) — searching it must return [], never raise."""
    clinical_index = assembler.indexes["clinical"]
    assert clinical_index.docs == []
    assert clinical_index.search("anything at all", top_k=3) == []


def test_a_task_matching_nothing_returns_no_recommendations(assembler):
    package = assembler.get_context_package(
        "HCP-001", "commercial_engagement", task="xyzzy nonexistent gibberish query", principal="u", principal_roles=["brand_manager"]
    )
    assert package["recommended_content"] == []


def test_invalid_agent_configuration_is_rejected_at_publish_not_at_first_use():
    with pytest.raises(AgentValidationError):
        publish_agent(load_agent_config("agents/hcp_engagement.yaml").model_copy(update={"purpose": "not_a_real_purpose"}))


def test_a_malformed_evaluation_case_is_isolated_not_fatal_to_the_whole_run(monkeypatch):
    """One bad case (an entity id that doesn't exist) must not crash the
    entire evaluation run — it's recorded as an error on that case only,
    and every other case still runs to completion."""
    from context_layer.evaluation import datasets

    def _broken_cases():
        cases = datasets.build_evaluation_cases()
        return cases + [
            EvaluationCase(
                id="malformed-unknown-entity",
                category="commercial_engagement",
                entity_id="HCP-this-does-not-exist",
                agent_config_path="agents/hcp_engagement.yaml",
                principal_roles=["brand_manager"],
                question="anything",
            )
        ]

    monkeypatch.setattr("context_layer.evaluation.runner.build_evaluation_cases", _broken_cases)
    results = run_evaluation(mode="fast")

    broken = next(r for r in results if r.case.id == "malformed-unknown-entity")
    assert broken.error is not None

    other_results = [r for r in results if r.case.id != "malformed-unknown-entity"]
    assert len(other_results) == len(datasets.build_evaluation_cases())
    assert all(r.error is None for r in other_results)


def test_policy_denial_is_a_specific_exception_type_not_a_generic_one(assembler):
    """PolicyDenied, not a bare Exception/ValueError - callers need to be
    able to distinguish "access denied" from "something broke"."""
    from context_layer.policy.engine import PolicyEngine
    from context_layer.policy.models import PolicyRequest

    with pytest.raises(PolicyDenied):
        PolicyEngine().evaluate(PolicyRequest(principal="u", principal_roles=["brand_manager"], purpose="nonexistent_purpose", entity_id="HCP-001"))
