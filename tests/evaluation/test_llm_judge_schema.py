"""llm_judge.py: the skip path needs no key; the parsing/gating logic is
tested with a mocked LLM response so it runs offline in CI without a
real credential."""

import json

import pytest

from context_layer.evaluation import llm_judge
from context_layer.evaluation.config import EvalLLMConfig
from context_layer.evaluation.custom_llm import PluggableLLM
from context_layer.evaluation.schemas import EvaluationCase, PolicyEvalResult


def _case() -> EvaluationCase:
    return EvaluationCase(id="c", category="commercial_engagement", entity_id="HCP-001", question="q?")


def _package() -> dict:
    return {
        "entity": {"id": "HCP-001", "type": "Person", "display": "Dr. Test"},
        "purpose": "commercial_engagement",
        "scope_applied": {"subgraphs": ["commercial"], "bridges": []},
        "facts": [],
        "community_summary": None,
    }


def test_skips_cleanly_with_no_api_key(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    result = llm_judge.judge(_case(), _package(), "answer", PolicyEvalResult(True, [], [], [], []), "TestAgent")
    assert result.skipped
    assert "no EVAL_LLM_PROVIDER" in result.skip_reason


def test_parses_a_well_formed_response_and_respects_the_models_pass_flag(monkeypatch):
    canned = json.dumps(
        {
            "correctness": {"score": 5, "reason": "accurate"},
            "relevance": {"score": 5, "reason": "on topic"},
            "faithfulness": {"score": 5, "reason": "grounded"},
            "policy_compliance": {"score": 5, "reason": "fine"},
            "hallucination_risk": {"level": "LOW", "reason": "none found"},
            "overall_score": 95,
            "pass": True,
            "critical_violation": False,
        }
    )
    monkeypatch.setattr(PluggableLLM, "generate", lambda self, prompt, *a, **k: canned)
    cfg = EvalLLMConfig(provider="anthropic", model="claude-sonnet-5", api_key="fake")
    monkeypatch.setattr(llm_judge, "get_eval_llm_config", lambda: cfg)

    result = llm_judge.judge(_case(), _package(), "answer", PolicyEvalResult(True, [], [], [], []), "TestAgent")
    assert not result.skipped
    assert result.correctness.score == 5
    assert result.hallucination_risk.level == "LOW"
    assert result.passed is True
    assert result.critical_violation is False


def test_a_deterministic_policy_violation_forces_critical_failure_even_if_the_model_disagrees(monkeypatch):
    """The CRITICAL RULE: governance is a hard gate, never left solely to
    the model's own self-report."""
    canned = json.dumps(
        {
            "correctness": {"score": 5, "reason": "x"},
            "relevance": {"score": 5, "reason": "x"},
            "faithfulness": {"score": 5, "reason": "x"},
            "policy_compliance": {"score": 5, "reason": "the model thinks this is fine"},
            "hallucination_risk": {"level": "LOW", "reason": "x"},
            "overall_score": 95,
            "pass": True,
            "critical_violation": False,  # the model is wrong here
        }
    )
    monkeypatch.setattr(PluggableLLM, "generate", lambda self, prompt, *a, **k: canned)
    cfg = EvalLLMConfig(provider="anthropic", model="claude-sonnet-5", api_key="fake")
    monkeypatch.setattr(llm_judge, "get_eval_llm_config", lambda: cfg)

    violated_policy = PolicyEvalResult(False, ["commercial"], ["commercial", "clinical"], ["clinical"], ["forbidden domain leaked"])
    result = llm_judge.judge(_case(), _package(), "answer", violated_policy, "TestAgent")

    assert result.critical_violation is True
    assert result.passed is False


def test_malformed_llm_output_degrades_to_skipped_not_a_crash(monkeypatch):
    monkeypatch.setattr(PluggableLLM, "generate", lambda self, prompt, *a, **k: "not json at all")
    cfg = EvalLLMConfig(provider="anthropic", model="claude-sonnet-5", api_key="fake")
    monkeypatch.setattr(llm_judge, "get_eval_llm_config", lambda: cfg)

    result = llm_judge.judge(_case(), _package(), "answer", PolicyEvalResult(True, [], [], [], []), "TestAgent")
    assert result.skipped
    assert "judge call failed" in result.skip_reason
