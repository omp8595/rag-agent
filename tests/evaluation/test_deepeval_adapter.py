"""deepeval_evaluator.py: the skip path needs no key. With a key configured
but the judge LLM mocked (no real network call), every metric either
scores or degrades to `skipped` — the adapter itself must never raise,
regardless of what the mocked model returns."""

from context_layer.evaluation.custom_llm import PluggableLLM
from context_layer.evaluation.deepeval_evaluator import evaluate_with_deepeval
from context_layer.evaluation.schemas import EvaluationCase


def _case() -> EvaluationCase:
    return EvaluationCase(id="c", category="commercial_engagement", entity_id="HCP-001", question="What should I know about this HCP?")


def test_skips_cleanly_with_no_api_key(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    result = evaluate_with_deepeval(_case(), ["ctx1"], "answer")
    assert result.framework == "deepeval"
    assert result.skipped


def test_never_raises_even_when_the_judge_model_returns_garbage(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "fake-key-for-this-test-only")
    monkeypatch.setattr(PluggableLLM, "generate", lambda self, prompt, *a, **k: "not a useful response")
    monkeypatch.setattr(PluggableLLM, "a_generate", lambda self, prompt, *a, **k: "not a useful response")

    result = evaluate_with_deepeval(_case(), ["This HCP engages with biomarker testing content."], "This HCP is interested in biomarker testing.")

    assert result.framework == "deepeval"
    assert not result.skipped  # the adapter itself ran — key was configured
    assert result.metrics  # every configured metric produced either a value or a per-metric skip
    for metric in result.metrics:
        assert metric.value is not None or metric.skipped
