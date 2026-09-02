"""Deterministic policy evaluation — no LLM. Re-checks, from the outside,
the one invariant the whole architecture rests on: a fact from a domain
outside the granted scope is only legitimate if it crossed a whitelisted
bridge (`fact["bridge"]` is set). A domain listed in a case's
`forbidden_domains` must never appear as a fact domain at all, bridged or
not — that's how "clinical never reaches a commercial purpose" is
actually verified, as opposed to merely asserted in a docstring.
"""

from __future__ import annotations

from context_layer.evaluation.schemas import EvaluationCase, PolicyEvalResult


def evaluate_policy(case: EvaluationCase, package: dict) -> PolicyEvalResult:
    scope_domains = set(package["scope_applied"]["subgraphs"])
    observed_domains = {fact["domain"] for fact in package["facts"]}
    forbidden = set(case.forbidden_domains)

    violations: list[str] = []

    unbridged_foreign = [
        fact for fact in package["facts"] if fact["domain"] not in scope_domains and not fact["bridge"]
    ]
    if unbridged_foreign:
        violations.append(
            f"{len(unbridged_foreign)} fact(s) from a domain outside scope_applied.subgraphs "
            f"with no bridge id: {[f['domain'] for f in unbridged_foreign]}"
        )

    forbidden_found = sorted(observed_domains & forbidden)
    if forbidden_found:
        violations.append(f"forbidden domain(s) present in facts: {forbidden_found}")

    return PolicyEvalResult(
        policy_compliant=not violations,
        allowed_domains=sorted(scope_domains),
        observed_domains=sorted(observed_domains),
        forbidden_domains_found=forbidden_found,
        violations=violations,
    )
