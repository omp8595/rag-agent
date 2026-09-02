"""The regression gate: `python -m context_layer.evaluation.runner --mode fast`
must pass on every case, every time, with no LLM required. This is what
CI actually runs — see Step 15's "default CI should run existing tests +
fast deterministic evaluation tests."
"""

from context_layer.evaluation.runner import run


def test_fast_mode_passes_every_case_with_no_llm_credentials(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    results = run(mode="fast")

    failures = [(r.case.id, r.status_reasons) for r in results if r.status != "PASS"]
    assert not failures, failures
    assert all(r.error is None for r in results)
