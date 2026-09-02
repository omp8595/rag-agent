"""Unified evaluation runner.

  python -m context_layer.evaluation.runner --mode fast   # deterministic only, no LLM, no key needed
  python -m context_layer.evaluation.runner --mode llm    # + LLM Judge only
  python -m context_layer.evaluation.runner --mode full   # + RAGAS + DeepEval + LLM Judge

Always builds every deterministic evaluator (policy/graph/lineage/isolation)
regardless of mode — those are free and give real signal with no API key.
`llm`/`full` additionally run the LLM-backed evaluators, each of which
independently degrades to `skipped` if no provider is configured, so
`--mode full` is always safe to run without credentials; it just won't
produce LLM scores.
"""

from __future__ import annotations

import argparse

from context_layer.agent_builder.agent import ThinAgent
from context_layer.agent_builder.builder import load_agent_config, publish_agent
from context_layer.api.app import build_assembler
from context_layer.evaluation import reporting
from context_layer.evaluation.datasets import build_evaluation_cases
from context_layer.evaluation.deepeval_evaluator import evaluate_with_deepeval
from context_layer.evaluation.graph_evaluator import evaluate_graph
from context_layer.evaluation.isolation_evaluator import evaluate_isolation
from context_layer.evaluation.lineage_evaluator import evaluate_lineage
from context_layer.evaluation.llm_judge import judge as llm_judge
from context_layer.evaluation.policy_evaluator import evaluate_policy
from context_layer.evaluation.ragas_evaluator import evaluate_with_ragas
from context_layer.evaluation.schemas import CaseResult, EvaluationCase
from context_layer.evaluation.scoring import score_case
from context_layer.policy.engine import PolicyEngine
from context_layer.policy.models import PolicyDenied, PolicyRequest


def run(mode: str = "fast") -> list[CaseResult]:
    assembler = build_assembler()
    engine = PolicyEngine()
    cases = build_evaluation_cases()

    results: list[CaseResult] = []
    packages: dict[str, dict] = {}  # case.id -> Context Package, for cases that produced one
    packages_by_entity_purpose: dict[tuple[str, str], dict] = {}

    for case in cases:
        try:
            result, package = _run_one_case(case, assembler, engine, mode)
        except Exception as exc:  # noqa: BLE001 - one broken case must not sink the run
            result, package = CaseResult(case=case, question=case.question, retrieved_context=[], generated_answer=None, error=str(exc)), None
        results.append(result)
        if package is not None:
            packages[case.id] = package
            packages_by_entity_purpose[(case.entity_id, _purpose_of(case))] = package

    entity_isolation_score = _compute_isolation_scores(packages_by_entity_purpose)
    for result in results:
        if result.error is None:
            score_case(result, isolation_score=entity_isolation_score.get(result.case.entity_id))

    return results


def _purpose_of(case: EvaluationCase) -> str:
    if case.agent_config_path:
        config = publish_agent(load_agent_config(case.agent_config_path))
        return config.purpose
    return case.purpose or ""


def _run_one_case(case: EvaluationCase, assembler, engine: PolicyEngine, mode: str) -> tuple[CaseResult, dict | None]:
    if case.expect_denial:
        try:
            engine.evaluate(PolicyRequest(principal="eval", principal_roles=case.principal_roles, purpose=case.purpose or "", entity_id=case.entity_id))
            status, reasons = "FAIL", ["expected PolicyDenied but the request was allowed — fail-closed is broken"]
        except PolicyDenied as exc:
            status, reasons = "PASS", [f"correctly denied: {exc.reason}"]
        result = CaseResult(case=case, question=case.question, retrieved_context=[], generated_answer=None)
        result.status, result.status_reasons = status, reasons
        return result, None

    if case.agent_config_path:
        config = publish_agent(load_agent_config(case.agent_config_path))
        agent = ThinAgent(config, assembler)
        outcome = agent.answer_question(case.entity_id, case.question)
        package, answer = outcome["package"], outcome["answer"]
        agent_id = config.name
        purpose = config.purpose
    else:
        package = assembler.get_context_package(
            case.entity_id, case.purpose or "", case.question, principal="eval", principal_roles=case.principal_roles
        )
        from context_layer.retrieval.answer_synthesis import synthesize_answer

        answer = synthesize_answer(package, case.question)
        agent_id = "(direct policy request)"
        purpose = case.purpose or ""

    retrieved_context = [c for c in [package.get("community_summary")] + [f["claim"] for f in package["facts"]] if c]

    policy_result = evaluate_policy(case, package)
    scope = engine.evaluate(PolicyRequest(principal="eval", principal_roles=case.principal_roles, purpose=purpose, entity_id=case.entity_id))
    graph_result = evaluate_graph(assembler.store, case.entity_id, scope)
    lineage_result = evaluate_lineage(package)

    result = CaseResult(
        case=case,
        question=case.question,
        retrieved_context=retrieved_context,
        generated_answer=answer,
        policy=policy_result,
        graph=graph_result,
        lineage=lineage_result,
    )
    if mode in ("llm", "full"):
        result.llm_judge = llm_judge(case, package, answer, policy_result, agent_id)
    if mode == "full":
        result.ragas = evaluate_with_ragas(case, retrieved_context, answer)
        result.deepeval = evaluate_with_deepeval(case, retrieved_context, answer)

    return result, package


def _compute_isolation_scores(packages_by_entity_purpose: dict[tuple[str, str], dict]) -> dict[str, float]:
    by_entity: dict[str, list[tuple[str, dict]]] = {}
    for (entity_id, purpose), package in packages_by_entity_purpose.items():
        by_entity.setdefault(entity_id, []).append((purpose, package))

    entity_isolation_score: dict[str, float] = {}
    for entity_id, purpose_packages in by_entity.items():
        scores = []
        for i in range(len(purpose_packages)):
            for j in range(i + 1, len(purpose_packages)):
                purpose_a, pkg_a = purpose_packages[i]
                purpose_b, pkg_b = purpose_packages[j]
                if purpose_a == purpose_b:
                    continue
                scores.append(evaluate_isolation(pkg_a, pkg_b).isolation_score)
        if scores:
            entity_isolation_score[entity_id] = min(scores)
    return entity_isolation_score


def main() -> None:
    parser = argparse.ArgumentParser(description="Life Sciences Enterprise Context Layer — evaluation runner")
    parser.add_argument("--mode", choices=["fast", "llm", "full"], default="fast")
    args = parser.parse_args()

    results = run(args.mode)
    json_path = reporting.write_json_report(results)
    md_path = reporting.write_markdown_report(results)

    passed = sum(1 for r in results if r.status == "PASS")
    print(f"{passed}/{len(results)} cases passed. Reports written to {json_path} and {md_path}")
    for r in results:
        print(f"  [{r.status:4}] {r.case.id}: {'; '.join(r.status_reasons)}")


if __name__ == "__main__":
    main()
