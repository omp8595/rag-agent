"""Renders a list of CaseResult into JSON and Markdown reports."""

from __future__ import annotations

import dataclasses
import json
from pathlib import Path

from context_layer.evaluation.schemas import CaseResult

REPORTS_DIR = Path(__file__).resolve().parent.parent.parent / "evaluation_reports"


def _to_jsonable(obj):
    if dataclasses.is_dataclass(obj) and not isinstance(obj, type):
        return {k: _to_jsonable(v) for k, v in dataclasses.asdict(obj).items()}
    if isinstance(obj, list):
        return [_to_jsonable(v) for v in obj]
    if isinstance(obj, dict):
        return {k: _to_jsonable(v) for k, v in obj.items()}
    return obj


def write_json_report(results: list[CaseResult], path: Path = REPORTS_DIR / "latest.json") -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "summary": _summary(results),
        "cases": [_to_jsonable(r) for r in results],
    }
    path.write_text(json.dumps(payload, indent=2))
    return path


def write_markdown_report(results: list[CaseResult], path: Path = REPORTS_DIR / "latest.md") -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    summary = _summary(results)

    lines = [
        "# Life Sciences Enterprise Context Layer",
        "## Evaluation Report",
        "",
        f"**Cases:** {summary['total']}  **Passed:** {summary['passed']}  **Failed:** {summary['failed']}",
        "",
    ]

    for r in results:
        lines += [
            "---",
            "",
            f"### {r.case.id}  ({r.case.category})",
            "",
            f"**Agent / Purpose:** {r.case.agent_config_path or '(direct policy request)'} / {r.case.purpose or '(agent-bound)'}",
            "",
        ]
        if r.error:
            lines += [f"**ERROR:** {r.error}", ""]
            continue

        if r.policy:
            lines += [
                "**Governance**",
                "",
                f"- Policy compliance: {'PASS' if r.policy.policy_compliant else 'FAIL'}",
                f"- Observed domains: {r.policy.observed_domains}",
                f"- Forbidden domains found: {r.policy.forbidden_domains_found or 'none'}",
                "",
            ]
        if r.graph:
            lines += [
                f"- Unauthorized bridges: {r.graph.unauthorized_bridges or 'none'}",
                f"- Bridges used: {r.graph.bridges_used or 'none'}",
                "",
            ]
        if r.lineage:
            lines += [f"**Lineage coverage:** {r.lineage.lineage_coverage:.0%} ({r.lineage.facts_with_lineage}/{r.lineage.total_facts} facts)", ""]

        for framework_result in (r.ragas, r.deepeval):
            if framework_result is None:
                continue
            if framework_result.skipped:
                lines += [f"**{framework_result.framework}:** skipped — {framework_result.skip_reason}", ""]
            else:
                lines += [f"**{framework_result.framework}:**"] + [
                    f"- {m.name}: {m.value:.2f}" if not m.skipped else f"- {m.name}: skipped ({m.skip_reason})"
                    for m in framework_result.metrics
                ] + [""]

        if r.llm_judge:
            if r.llm_judge.skipped:
                lines += [f"**LLM Judge:** skipped — {r.llm_judge.skip_reason}", ""]
            else:
                j = r.llm_judge
                lines += [
                    "**LLM Judge:**",
                    f"- correctness: {j.correctness.score if j.correctness else '-'}/5",
                    f"- relevance: {j.relevance.score if j.relevance else '-'}/5",
                    f"- faithfulness: {j.faithfulness.score if j.faithfulness else '-'}/5",
                    f"- policy_compliance: {j.policy_compliance.score if j.policy_compliance else '-'}/5",
                    f"- hallucination_risk: {j.hallucination_risk.level if j.hallucination_risk else '-'}",
                    f"- critical_violation: {j.critical_violation}",
                    "",
                ]

        lines += [
            f"**Unified score:** {r.unified_score:.1f}/100" if r.unified_score is not None else "**Unified score:** n/a (no scorable dimensions)",
            f"**STATUS: {r.status}** — {'; '.join(r.status_reasons)}",
            "",
        ]

    path.write_text("\n".join(lines))
    return path


def _summary(results: list[CaseResult]) -> dict:
    return {
        "total": len(results),
        "passed": sum(1 for r in results if r.status == "PASS"),
        "failed": sum(1 for r in results if r.status == "FAIL"),
    }
