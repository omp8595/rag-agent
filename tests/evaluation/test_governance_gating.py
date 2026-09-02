"""Phase 11 — the governance gating test. Explicitly proves scoring.py's
central claim: a governance violation forces FAIL regardless of how
excellent every other signal is. This is not an averaging system with
governance as one more weighted input — it's a gate."""

from context_layer.evaluation.schemas import (
    CaseResult,
    EvaluationCase,
    FrameworkResult,
    GraphEvalResult,
    HallucinationRisk,
    JudgeDimension,
    LineageEvalResult,
    LLMJudgeResult,
    MetricResult,
    PolicyEvalResult,
)
from context_layer.evaluation.scoring import score_case


def _base_case() -> EvaluationCase:
    return EvaluationCase(id="gate-test", category="commercial_engagement", entity_id="HCP-001", question="q?")


def _excellent_ragas() -> FrameworkResult:
    return FrameworkResult(
        framework="ragas",
        metrics=[
            MetricResult(name="context_precision", value=1.0),
            MetricResult(name="context_recall", value=1.0),
            MetricResult(name="faithfulness", value=1.0),
            MetricResult(name="answer_relevancy", value=1.0),
        ],
    )


def _excellent_deepeval() -> FrameworkResult:
    return FrameworkResult(
        framework="deepeval",
        metrics=[
            MetricResult(name="AnswerRelevancyMetric", value=1.0),
            MetricResult(name="FaithfulnessMetric", value=1.0),
            MetricResult(name="ContextualRelevancyMetric", value=1.0),
        ],
    )


def _excellent_llm_judge(critical_violation: bool = False) -> LLMJudgeResult:
    """The model's own self-report says everything is perfect — used to
    prove the deterministic gate does not depend on the judge agreeing."""
    perfect = JudgeDimension(score=5, reason="flawless")
    return LLMJudgeResult(
        correctness=perfect,
        relevance=perfect,
        faithfulness=perfect,
        policy_compliance=perfect,
        hallucination_risk=HallucinationRisk("LOW", "none"),
        overall_score=100,
        passed=True,
        critical_violation=critical_violation,
    )


def test_excellent_scores_pass_when_governance_is_clean():
    """Sanity check the test harness itself: excellent scores + clean
    governance really does produce PASS, so the failing tests below are
    proving something (the gate), not just always failing."""
    result = CaseResult(
        case=_base_case(),
        question="q?",
        retrieved_context=["ctx"],
        generated_answer="a",
        policy=PolicyEvalResult(True, ["commercial"], ["commercial"], [], []),
        graph=GraphEvalResult(True, ["commercial"], [], []),
        lineage=LineageEvalResult(3, 3, [], 1.0),
        ragas=_excellent_ragas(),
        deepeval=_excellent_deepeval(),
        llm_judge=_excellent_llm_judge(),
    )
    score_case(result)
    assert result.status == "PASS"
    assert result.unified_score == 100.0


def test_unauthorized_domain_access_fails_despite_perfect_rag_and_judge_scores():
    """RAGAS = excellent, DeepEval = excellent, LLM Judge = excellent,
    BUT an unauthorized domain was accessed -> FINAL STATUS = FAIL."""
    result = CaseResult(
        case=_base_case(),
        question="q?",
        retrieved_context=["ctx"],
        generated_answer="a",
        policy=PolicyEvalResult(
            policy_compliant=False,
            allowed_domains=["commercial"],
            observed_domains=["commercial", "clinical"],
            forbidden_domains_found=["clinical"],
            violations=["forbidden domain(s) present in facts: ['clinical']"],
        ),
        graph=GraphEvalResult(True, ["commercial", "clinical"], [], []),
        lineage=LineageEvalResult(3, 3, [], 1.0),
        ragas=_excellent_ragas(),
        deepeval=_excellent_deepeval(),
        llm_judge=_excellent_llm_judge(critical_violation=False),  # the judge itself missed it
    )
    score_case(result)
    assert result.status == "FAIL"
    assert any("policy violation" in reason for reason in result.status_reasons)


def test_unauthorized_bridge_traversal_fails_despite_perfect_answer_quality():
    """Answer is factually perfect BUT an unauthorized bridge was
    traversed -> FINAL STATUS = FAIL."""
    result = CaseResult(
        case=_base_case(),
        question="q?",
        retrieved_context=["ctx"],
        generated_answer="a",
        policy=PolicyEvalResult(True, ["commercial"], ["commercial"], [], []),
        graph=GraphEvalResult(
            graph_compliant=False,
            domains_traversed=["commercial", "clinical"],
            bridges_used=["not.a.real.bridge"],
            unauthorized_bridges=["not.a.real.bridge is not in the bridge whitelist at all"],
        ),
        lineage=LineageEvalResult(3, 3, [], 1.0),
        ragas=_excellent_ragas(),
        deepeval=_excellent_deepeval(),
        llm_judge=_excellent_llm_judge(),
    )
    score_case(result)
    assert result.status == "FAIL"
    assert any("unauthorized bridge" in reason for reason in result.status_reasons)


def test_llm_judge_critical_violation_fails_even_with_perfect_ragas_and_deepeval():
    """Great RAGAS/DeepEval scores, but the LLM judge itself flags a
    critical policy violation -> FAIL. (The judge agreeing with itself
    isn't what makes this a gate — see the policy/bridge tests above,
    where the judge disagrees and the deterministic checks still win.
    This test proves the judge's own critical_violation flag is honored,
    not silently averaged away.)"""
    result = CaseResult(
        case=_base_case(),
        question="q?",
        retrieved_context=["ctx"],
        generated_answer="a",
        policy=PolicyEvalResult(True, ["commercial"], ["commercial"], [], []),
        graph=GraphEvalResult(True, ["commercial"], [], []),
        lineage=LineageEvalResult(3, 3, [], 1.0),
        ragas=_excellent_ragas(),
        deepeval=_excellent_deepeval(),
        llm_judge=_excellent_llm_judge(critical_violation=True),
    )
    score_case(result)
    assert result.status == "FAIL"
    assert any("critical" in reason.lower() for reason in result.status_reasons)
