"""Deterministic graph/bridge evaluation — no LLM. Re-runs the same
bounded traversal the assembler uses, but independently re-validates every
bridge id it reports against the bridge whitelist itself (`graph/bridges.py`)
rather than trusting that `GraphStore.bounded_traversal` tagged it
correctly — this catches a bridge-tagging bug in the traversal layer that
`policy_evaluator` (which only looks at the shaped Context Package) would
not.
"""

from __future__ import annotations

from context_layer.graph.bridges import get_bridge
from context_layer.graph.store import GraphStore
from context_layer.policy.models import RetrievalScope
from context_layer.evaluation.schemas import GraphEvalResult


def evaluate_graph(store: GraphStore, entity_id: str, scope: RetrievalScope) -> GraphEvalResult:
    facts = store.bounded_traversal(
        entity_id,
        allowed_subgraphs=set(scope.subgraphs),
        allowed_bridges=set(scope.bridges),
        max_hops=scope.max_hops,
    )

    domains_traversed = sorted({f.domain for f in facts})
    bridges_used = sorted({f.bridged_via for f in facts if f.bridged_via})

    unauthorized: list[str] = []
    for fact in facts:
        if not fact.bridged_via:
            continue
        bridge = get_bridge(fact.bridged_via)
        if bridge is None:
            unauthorized.append(f"{fact.bridged_via} is not in the bridge whitelist at all")
        elif bridge.from_domain != fact.domain:
            unauthorized.append(f"{fact.bridged_via} claims from_domain={bridge.from_domain} but fact.domain={fact.domain}")
        elif fact.edge_type not in bridge.edge_types:
            unauthorized.append(f"{fact.bridged_via} does not cover edge_type={fact.edge_type}")
        elif fact.bridged_via not in scope.bridges:
            unauthorized.append(f"{fact.bridged_via} was used but not in this scope's granted bridges {scope.bridges}")

    return GraphEvalResult(
        graph_compliant=not unauthorized,
        domains_traversed=domains_traversed,
        bridges_used=bridges_used,
        unauthorized_bridges=unauthorized,
    )
