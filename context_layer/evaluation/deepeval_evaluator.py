"""DeepEval adapter — the RAG Triad (answer relevancy, faithfulness,
contextual relevancy) plus contextual precision/recall when a case
carries a reference answer. Uses the shared `PluggableLLM` as the judge
model for every metric, so it goes through the same provider/key config
as `llm_judge.py`.
"""

from __future__ import annotations

from context_layer.evaluation.config import get_eval_llm_config
from context_layer.evaluation.custom_llm import PluggableLLM
from context_layer.evaluation.schemas import EvaluationCase, FrameworkResult, MetricResult


def evaluate_with_deepeval(case: EvaluationCase, retrieved_context: list[str], answer: str) -> FrameworkResult:
    cfg = get_eval_llm_config()
    if cfg is None:
        return FrameworkResult(framework="deepeval", metrics=[], skipped=True, skip_reason="no EVAL_LLM_PROVIDER/API key configured")

    from deepeval.metrics import (
        AnswerRelevancyMetric,
        ContextualPrecisionMetric,
        ContextualRecallMetric,
        ContextualRelevancyMetric,
        FaithfulnessMetric,
    )
    from deepeval.test_case import LLMTestCase

    llm = PluggableLLM(cfg)
    test_case = LLMTestCase(
        input=case.question,
        actual_output=answer,
        retrieval_context=retrieved_context,
        context=retrieved_context,
        expected_output=case.ground_truth_answer,
    )

    metrics = [
        AnswerRelevancyMetric(model=llm),
        FaithfulnessMetric(model=llm),
        ContextualRelevancyMetric(model=llm),
    ]
    if case.ground_truth_answer:
        metrics += [ContextualPrecisionMetric(model=llm), ContextualRecallMetric(model=llm)]

    results: list[MetricResult] = []
    for metric in metrics:
        name = type(metric).__name__
        try:
            metric.measure(test_case)
            results.append(MetricResult(name=name, value=metric.score))
        except Exception as exc:  # noqa: BLE001 - one metric failing must not sink the others or the suite
            results.append(MetricResult(name=name, value=None, skipped=True, skip_reason=str(exc)))

    return FrameworkResult(framework="deepeval", metrics=results)
