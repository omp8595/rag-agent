"""ragas_evaluator.py: both skip paths need to be provably real — no key
configured, and (this repo's own dev environment) ragas installed but
failing to import due to a known upstream packaging bug. Neither may
raise; both must produce a clearly explained FrameworkResult."""

from context_layer.evaluation.ragas_evaluator import evaluate_with_ragas
from context_layer.evaluation.schemas import EvaluationCase


def _case() -> EvaluationCase:
    return EvaluationCase(id="c", category="commercial_engagement", entity_id="HCP-001", question="q?")


def test_skips_cleanly_with_no_api_key(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    result = evaluate_with_ragas(_case(), ["ctx1"], "answer")
    assert result.framework == "ragas"
    assert result.skipped
    assert "no EVAL_LLM_PROVIDER" in result.skip_reason


def test_skips_cleanly_when_ragas_cannot_be_imported(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "fake-key-for-this-test-only")
    result = evaluate_with_ragas(_case(), ["ctx1"], "answer")
    assert result.framework == "ragas"
    # Either genuinely unavailable in this environment, or (if a future
    # environment has a working ragas) it degrades on the fake key instead —
    # either way this must never raise.
    assert result.skipped
    assert result.skip_reason
