"""Wires the graph store, policy engine, vector indexes, and audit log
into one ContextAssembler — the object both the MCP server and the demo
script build on.
"""

from __future__ import annotations

from context_layer.api.assembler import ContextAssembler
from context_layer.graph.build import build_graph_store
from context_layer.policy.audit import AuditLog
from context_layer.policy.engine import PolicyEngine
from context_layer.retrieval.vector_index import build_domain_indexes


def build_assembler() -> ContextAssembler:
    store = build_graph_store()
    engine = PolicyEngine()
    indexes = build_domain_indexes(store)
    audit_log = AuditLog()
    return ContextAssembler(store, engine, indexes, audit_log)
