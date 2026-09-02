"""Deterministic lineage evaluation — no LLM. Every fact in a Context
Package must carry a source system and a domain (design doc principle #4,
"every fact carries lineage"); an "orphan" fact is one missing either.
"""

from __future__ import annotations

from context_layer.evaluation.schemas import LineageEvalResult


def evaluate_lineage(package: dict) -> LineageEvalResult:
    facts = package["facts"]
    orphans = [
        fact["claim"] for fact in facts if not fact.get("source") or not fact.get("domain")
    ]
    total = len(facts)
    with_lineage = total - len(orphans)
    coverage = 1.0 if total == 0 else with_lineage / total

    return LineageEvalResult(
        total_facts=total,
        facts_with_lineage=with_lineage,
        orphan_facts=orphans,
        lineage_coverage=coverage,
    )
