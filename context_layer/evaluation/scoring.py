"""Unified scoring — a weighted composite EXCEPT that governance failures
are hard gates, not inputs to an average. A perfect retrieval/answer score
next to a policy or bridge violation is still FAIL: that is the entire
point of a system whose product is governed context, not raw answer
quality.

Weights (of the dimensions that actually have data — see
`_renormalized_score`):
  retrieval_quality     20%   (LLM-derived: ragas/deepeval contextual metrics)
  answer_quality        20%   (LLM-derived: answer relevancy)
  faithfulness          15%   (LLM-derived)
  policy_compliance     25%   (deterministic)
  domain_isolation      10%   (deterministic)
  lineage_completeness  10%   (deterministic)
"""

from __future__ import annotations

from context_layer.evaluation.schemas import CaseResult

_WEIGHTS = {
    "retrieval_quality": 0.20,
    "answer_quality": 0.20,
    "faithfulness": 0.15,
    "policy_compliance": 0.25,
    "domain_isolation": 0.10,
    "lineage_completeness": 0.10,
}

_PASS_THRESHOLD = 60.0


def _metric_values(*framework_results, names: tuple[str, ...]) -> list[float]:
    values = []
    for fr in framework_results:
        if fr is None or fr.skipped:
            continue
        for metric in fr.metrics:
            if metric.value is not None and any(n.lower() in metric.name.lower() for n in names):
                values.append(metric.value)
    return values


def score_case(result: CaseResult, isolation_score: float | None = None) -> None:
    """Mutates `result` in place: sets unified_score, status, status_reasons.
    `isolation_score` is supplied by the runner only for cases it paired
    with another purpose for `isolation_evaluator` — most cases have none,
    which correctly drops that dimension out of the weighted average
    rather than penalizing a case the isolation check was never run on."""
    dims: dict[str, float | None] = {
        "policy_compliance": 1.0 if result.policy and result.policy.policy_compliant else (0.0 if result.policy else None),
        "domain_isolation": isolation_score,
        "lineage_completeness": result.lineage.lineage_coverage if result.lineage else None,
        "retrieval_quality": _avg(_metric_values(result.ragas, result.deepeval, names=("precision", "recall", "contextualrelevancy"))),
        "answer_quality": _avg(_metric_values(result.ragas, result.deepeval, names=("relevancy", "relevance")) + _llm_judge_dim(result, "relevance")),
        "faithfulness": _avg(_metric_values(result.ragas, result.deepeval, names=("faithfulness",)) + _llm_judge_dim(result, "faithfulness")),
    }

    available = {name: value for name, value in dims.items() if value is not None}
    total_weight = sum(_WEIGHTS[name] for name in available)
    score = (
        sum(_WEIGHTS[name] * value for name, value in available.items()) / total_weight * 100
        if total_weight
        else None
    )

    reasons: list[str] = []
    status = "PASS"

    if result.policy and not result.policy.policy_compliant:
        status = "FAIL"
        reasons.append(f"policy violation: {'; '.join(result.policy.violations)}")
    if result.graph and not result.graph.graph_compliant:
        status = "FAIL"
        reasons.append(f"unauthorized bridge traversal: {'; '.join(result.graph.unauthorized_bridges)}")
    if result.llm_judge and not result.llm_judge.skipped and result.llm_judge.critical_violation:
        status = "FAIL"
        reasons.append("LLM judge flagged a critical policy violation")
    if status == "PASS" and score is not None and score < _PASS_THRESHOLD:
        status = "FAIL"
        reasons.append(f"unified score {score:.1f} is below the {_PASS_THRESHOLD:.0f} threshold")
    if not reasons:
        reasons.append("all deterministic checks, and any available LLM checks, passed")

    result.unified_score = score
    result.status = status
    result.status_reasons = reasons


def _avg(values: list[float]) -> float | None:
    return sum(values) / len(values) if values else None


def _llm_judge_dim(result: CaseResult, dim: str) -> list[float]:
    judge = result.llm_judge
    if judge is None or judge.skipped:
        return []
    d = getattr(judge, dim, None)
    return [d.score / 5.0] if d else []
