"""LLM consumption layer (Phase 5/6): MockLLMProvider is deterministic
and needs no credentials; RealLLMProvider fails clearly without one;
grounding distinguishes a supported answer from an unsupported claim."""

import pytest

from context_layer.llm.grounding import ground_answer
from context_layer.llm.provider import MockLLMProvider, RealLLMProvider


def test_mock_provider_never_touches_the_graph_store_or_assembler(assembler):
    """Structural proof: MockLLMProvider.generate's signature takes only
    a package dict and a question — there is no way to hand it a
    reference to the store even if you wanted to."""
    package = assembler.get_context_package("HCP-001", "commercial_engagement", principal="u", principal_roles=["brand_manager"])
    import inspect

    params = list(inspect.signature(MockLLMProvider.generate).parameters)
    assert params == ["self", "context_package", "question"]

    result = MockLLMProvider().generate(package, "What should I know?")
    assert result["provider"] == "mock"
    assert result["answer"]


def test_real_provider_raises_clearly_with_no_credentials(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    with pytest.raises(RuntimeError, match="no LLM provider configured"):
        RealLLMProvider()


def test_grounding_finds_facts_that_appear_verbatim():
    package = {
        "request_id": "ctx-1",
        "facts": [
            {"fact_id": "fact_001", "claim": "Engaged with content X"},
            {"fact_id": "fact_002", "claim": "Co-authored publication Y"},
        ],
    }
    result = ground_answer(package, "This HCP: Engaged with content X. Nothing else notable.")
    assert result["supporting_fact_ids"] == ["fact_001"]
    assert result["unsupported_fact_ids"] == []
    assert result["context_package_id"] == "ctx-1"


def test_grounding_prefers_explicit_citations_when_present():
    package = {"request_id": "ctx-1", "facts": [{"fact_id": "fact_001", "claim": "Engaged with content X"}]}
    result = ground_answer(package, "Some paraphrased answer. CITED_FACTS: fact_001")
    assert result["supporting_fact_ids"] == ["fact_001"]
    assert result["warnings"] == []


def test_grounding_flags_a_citation_to_a_fact_id_that_does_not_exist():
    """The core hallucination-detection signal: a cited fact_id that
    isn't actually in this Context Package."""
    package = {"request_id": "ctx-1", "facts": [{"fact_id": "fact_001", "claim": "Engaged with content X"}]}
    result = ground_answer(package, "An answer. CITED_FACTS: fact_001, fact_099")
    assert result["unsupported_fact_ids"] == ["fact_099"]
    assert any("fact_099" in w for w in result["warnings"])


def test_grounding_warns_when_facts_exist_but_none_are_referenced():
    package = {"request_id": "ctx-1", "facts": [{"fact_id": "fact_001", "claim": "Engaged with content X"}]}
    result = ground_answer(package, "A generic answer that mentions nothing specific.")
    assert result["supporting_fact_ids"] == []
    assert any("does not reference any retrieved fact" in w for w in result["warnings"])


def test_grounding_is_silent_when_the_package_has_no_facts_to_cite():
    package = {"request_id": "ctx-1", "facts": []}
    result = ground_answer(package, "There is nothing on record for this entity in this scope.")
    assert result["warnings"] == []
