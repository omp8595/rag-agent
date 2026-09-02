"""Deterministic Context Package isolation evaluation — no LLM. Step 9:
"same HCP + same enterprise data + different purpose = different, and
mutually non-leaking, Context Package." Compares two packages for the
*same* entity retrieved under two different purposes.
"""

from __future__ import annotations

from context_layer.evaluation.schemas import IsolationEvalResult


def evaluate_isolation(package_a: dict, package_b: dict) -> IsolationEvalResult:
    facts_a = {f["claim"] for f in package_a["facts"]}
    facts_b = {f["claim"] for f in package_b["facts"]}
    domains_a = {f["domain"] for f in package_a["facts"]}
    domains_b = {f["domain"] for f in package_b["facts"]}
    scope_a = set(package_a["scope_applied"]["subgraphs"])
    scope_b = set(package_b["scope_applied"]["subgraphs"])

    def _leaked_into(domains_observed: set[str], own_scope: set[str], other_scope: set[str], package: dict) -> list[str]:
        exclusive_to_other = other_scope - own_scope
        leaked = []
        for domain in exclusive_to_other:
            if domain in domains_observed and not any(
                f["domain"] == domain and f["bridge"] for f in package["facts"]
            ):
                leaked.append(domain)
        return leaked

    leak = sorted(
        set(_leaked_into(domains_a, scope_a, scope_b, package_a))
        | set(_leaked_into(domains_b, scope_b, scope_a, package_b))
    )

    packages_differ = facts_a != facts_b or scope_a != scope_b

    isolation_score = 1.0 if (packages_differ and not leak) else 0.0

    return IsolationEvalResult(
        entity_id=package_a["entity"]["id"],
        purpose_a=package_a["purpose"],
        purpose_b=package_b["purpose"],
        packages_differ=packages_differ,
        forbidden_domain_leak=leak,
        isolation_score=isolation_score,
    )
