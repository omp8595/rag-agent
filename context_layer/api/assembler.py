"""Context Assembler — design doc section 4 (intro) and section 6.

Ties the pieces together for the primary entry point,
`get_context_package`: evaluate policy -> get a RetrievalScope -> pull
entity lookup + bounded traversal + vector search, all scoped -> shape
the result into the Context Package schema, with lineage on every fact
and an audit record for the whole request.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from context_layer.graph.bridges import VERSION as BRIDGE_WHITELIST_VERSION
from context_layer.graph.bridges import get_bridge
from context_layer.graph.store import Fact, GraphStore
from context_layer.policy.audit import AuditLog
from context_layer.policy.engine import PolicyEngine
from context_layer.policy.models import PolicyRequest, RetrievalScope
from context_layer.retrieval.entity_lookup import get_entity_profile
from context_layer.retrieval.graphrag import community_summary
from context_layer.retrieval.vector_index import DomainVectorIndex

# Human-readable reasons shown in `excluded` for a domain the requesting
# purpose's scope does not include. Kept as data so Compliance can review
# the wording alongside the bridge whitelist it mirrors.
_EXCLUSION_REASONS = {
    "commercial": "Commercial engagement and interaction data not permitted for '{purpose}' purpose.",
    "medical": "MSL interactions not permitted for '{purpose}' purpose; only whitelisted publication bridges apply.",
    "clinical": "Clinical subgraph not permitted for '{purpose}' purpose.",
}

_FACT_SOURCE_BY_EDGE_TYPE = {
    "ENGAGED_WITH": "CRM",
    "AUTHORED": "PubMed",
    "MSL_INTERACTION": "Medical Information System",
    "PRINCIPAL_INVESTIGATOR_OF": "CTMS",
}


class ContextAssembler:
    def __init__(
        self,
        store: GraphStore,
        engine: PolicyEngine,
        indexes: dict[str, DomainVectorIndex],
        audit_log: AuditLog,
    ):
        self.store = store
        self.engine = engine
        self.indexes = indexes
        self.audit_log = audit_log

    # -- tools ---------------------------------------------------------

    def get_context_package(
        self,
        entity_id: str,
        purpose: str,
        task: str = "",
        *,
        principal: str = "agent",
        principal_roles: list[str] | None = None,
    ) -> dict:
        request = PolicyRequest(
            principal=principal,
            principal_roles=principal_roles or [],
            purpose=purpose,
            entity_id=entity_id,
            task=task,
        )
        scope = self.engine.evaluate(request)

        node = self.store.node(entity_id)
        if node is None:
            raise ValueError(f"unknown entity {entity_id!r}")

        profile = get_entity_profile(self.store, entity_id, scope)

        raw_facts = self.store.bounded_traversal(
            entity_id,
            allowed_subgraphs=set(scope.subgraphs),
            allowed_bridges=set(scope.bridges),
            max_hops=scope.max_hops,
        )

        facts, relationships, constraints = self._classify_facts(raw_facts, purpose)
        recommended_content = self._recommend_content(scope, task)
        excluded = self._excluded_domains(scope, purpose)
        summary = self._community_summary(entity_id, scope)

        request_id = f"ctx-{uuid.uuid4().hex[:12]}"
        forbidden_domains = sorted(e["domain"] for e in excluded)

        package = {
            # -- original fields (every existing caller/test reads these) --
            "entity": {"id": entity_id, "type": node.get("node_type", "Entity"), "display": node.get("display", entity_id)},
            "purpose": purpose,
            "scope_applied": {"subgraphs": scope.subgraphs, "bridges": scope.bridges},
            "profile": profile,
            "facts": facts,
            "relationships": relationships,
            "recommended_content": recommended_content,
            "community_summary": summary,
            "constraints": constraints,
            "excluded": excluded,
            "lineage_id": request_id,
            # -- envelope: the same data, reshaped as a self-describing artifact --
            "request_id": request_id,
            "agent": {"agent_id": principal, "role": (principal_roles or [None])[0], "purpose": purpose},
            "policy_decision": {
                "allowed": True,  # reaching this point means PolicyEngine.evaluate() did not raise PolicyDenied
                "allowed_domains": scope.subgraphs,
                "forbidden_domains": forbidden_domains,
                "allowed_bridges": scope.bridges,
                "redactions": scope.redactions,
            },
            "retrieval": {
                "entity_facts": list(profile.keys()),
                "graph_facts": facts,
                "vector_results": recommended_content,
                "community_context": [summary] if summary else [],
            },
            "context": {"facts": facts, "documents": recommended_content, "summary": summary},
            "lineage": [
                {
                    "fact_id": f["fact_id"],
                    "source_type": f["source"],
                    "source_id": f["source_id"],
                    "domain": f["domain"],
                    "retrieval_method": f["retrieval_method"],
                }
                for f in facts
            ],
            "governance": {
                "domains_accessed": sorted({f["domain"] for f in facts}),
                "bridges_used": sorted({f["bridge"] for f in facts if f["bridge"]}),
                "redactions_applied": scope.redactions,
            },
            "audit": {"timestamp": datetime.now(timezone.utc).isoformat(), "policy_version": BRIDGE_WHITELIST_VERSION},
        }

        self.audit_log.record(
            request=request.model_dump(),
            scope=scope.model_dump(),
            context_package=package,
        )
        return package

    def find_entities(self, query: str, entity_type: str, purpose: str) -> list[dict]:
        query_lower = query.lower()
        results = []
        for node in self.store.find_nodes(node_type=entity_type):
            display = node.get("display") or node.get("name") or node.get("title", "")
            if query_lower in str(display).lower():
                results.append({"id": node["id"], "type": entity_type, "display": display})
        return results

    def explain_relationship(self, entity_a: str, entity_b: str, purpose: str) -> dict:
        import networkx as nx

        request = PolicyRequest(principal="agent", principal_roles=[], purpose=purpose, entity_id=entity_a)
        # Role check bypassed here deliberately isn't possible — evaluate()
        # requires at least one permitted role, so callers of this tool
        # pass roles the same way get_context_package's caller does. For a
        # role-agnostic explain, use the purpose's own permitted roles.
        from context_layer.policy.engine import PURPOSE_POLICIES

        policy = PURPOSE_POLICIES.get(purpose)
        if policy is None:
            return {"path": None, "reason": f"unrecognized purpose '{purpose}'"}
        request.principal_roles = list(policy.permitted_roles)[:1]
        scope = self.engine.evaluate(request)

        allowed_domains = set(scope.subgraphs) | {"spine"}
        allowed_bridges = set(scope.bridges)

        view = nx.MultiDiGraph()
        for u, v, data in self.store.g.edges(data=True):
            domain = data["domain"]
            if domain in allowed_domains:
                view.add_edge(u, v, **data)
            else:
                bridge = get_bridge(
                    self._bridge_id_for(domain, data["edge_type"], allowed_domains, allowed_bridges)
                )
                if bridge:
                    view.add_edge(u, v, **data)

        try:
            path = nx.shortest_path(view, entity_a, entity_b)
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            return {"path": None, "reason": "no path within permitted subgraph(s)"}
        return {"path": path, "scope_applied": {"subgraphs": scope.subgraphs, "bridges": scope.bridges}}

    def find_content(self, topic: str = "", audience: str = "HCP", approval_status: str = "approved") -> list[dict]:
        results = []
        for node in self.store.find_nodes(node_type="Content", domain="commercial"):
            if node["approval_status"] != approval_status:
                continue
            if audience and node["audience"] != audience:
                continue
            if topic and topic.lower() not in node["topic"].lower() and topic.lower() not in node["title"].lower():
                continue
            results.append(
                {"id": node["id"], "title": node["title"], "approval": node["approval_status"], "audience": node["audience"]}
            )
        return results

    # -- helpers ---------------------------------------------------------

    @staticmethod
    def _bridge_id_for(domain: str, edge_type: str, allowed_domains: set[str], allowed_bridges: set[str]) -> str | None:
        from context_layer.graph.bridges import BRIDGE_WHITELIST

        for bridge in BRIDGE_WHITELIST.values():
            if (
                bridge.id in allowed_bridges
                and bridge.from_domain == domain
                and bridge.to_domain in allowed_domains
                and edge_type in bridge.edge_types
            ):
                return bridge.id
        return None

    def _classify_facts(self, raw_facts: list[Fact], purpose: str) -> tuple[list[dict], list[dict], list[str]]:
        facts: list[dict] = []
        relationships: list[dict] = []
        constraints: list[str] = []
        seen_constraints: set[str] = set()

        for fact in raw_facts:
            dst_node = self.store.node(fact.dst)
            if fact.edge_type == "WORKS_AT":
                relationships.append(
                    {"type": "WORKS_AT", "target": fact.dst, "display": dst_node.get("name", fact.dst) if dst_node else fact.dst}
                )
                continue

            if fact.edge_type in ("IN_THERAPEUTIC_AREA", "IN_TERRITORY", "SITE_OF"):
                continue  # surfaced via profile, not as a standalone fact

            if fact.edge_type == "PRINCIPAL_INVESTIGATOR_OF":
                bridge = get_bridge(fact.bridged_via) if fact.bridged_via else None
                if bridge and bridge.mode == "flag_only":
                    if fact.attrs.get("active"):
                        note = "Active clinical investigator on sponsor study — apply promotional exclusion rules"
                        if note not in seen_constraints:
                            constraints.append(note)
                            seen_constraints.add(note)
                    continue
                study = dst_node or {}
                facts.append(
                    {
                        "claim": (
                            f"Principal investigator on {study.get('protocol_id', fact.dst)} "
                            f"(enrollment_rate={fact.attrs.get('enrollment_rate')}, "
                            f"feasibility_score={fact.attrs.get('feasibility_score')})"
                        ),
                        "source": "CTMS",
                        "domain": fact.domain,
                        "confidence": 1.0,
                        "bridge": fact.bridged_via,
                        "source_id": fact.dst,
                        "retrieval_method": "bridge_traversal" if fact.bridged_via else "graph_traversal",
                    }
                )
                continue

            claim = self._claim_text(fact, dst_node)
            if claim is None:
                continue
            facts.append(
                {
                    "claim": claim,
                    "source": _FACT_SOURCE_BY_EDGE_TYPE.get(fact.edge_type, fact.domain),
                    "domain": fact.domain,
                    "confidence": 1.0 if fact.bridged_via is None else 0.9,
                    "bridge": fact.bridged_via,
                    "source_id": fact.dst,
                    "retrieval_method": "bridge_traversal" if fact.bridged_via else "graph_traversal",
                }
            )

        for i, fact_dict in enumerate(facts, start=1):
            fact_dict["fact_id"] = f"fact_{i:03d}"

        return facts, relationships, constraints

    @staticmethod
    def _claim_text(fact: Fact, dst_node: dict | None) -> str | None:
        if fact.edge_type == "ENGAGED_WITH" and dst_node:
            return f"Engaged with content '{dst_node['title']}' via {fact.attrs.get('channel')} on {fact.attrs.get('date')}"
        if fact.edge_type == "AUTHORED" and dst_node:
            return f"Co-authored publication '{dst_node['title']}' ({dst_node.get('date')})"
        if fact.edge_type == "MSL_INTERACTION" and dst_node:
            return f"Medical inquiry interaction regarding {dst_node.get('topic')} on {dst_node.get('date')}"
        return None

    def _recommend_content(self, scope: RetrievalScope, task: str) -> list[dict]:
        if "commercial" not in scope.indexes or not task:
            return []
        index = self.indexes.get("commercial")
        if index is None:
            return []
        recs = []
        for doc, _score in index.search(task, top_k=3):
            node = self.store.node(doc.id)
            if node and node["approval_status"] == "approved":
                recs.append(
                    {"id": node["id"], "title": node["title"], "approval": node["approval_status"], "audience": node["audience"]}
                )
        return recs

    def _community_summary(self, entity_id: str, scope: RetrievalScope) -> str | None:
        """GraphRAG capability (design doc §4.3) — "what does this entity
        care about," computed strictly per granted domain. Never passed a
        domain outside `scope.subgraphs`, so it can't become a side
        channel around the bridge whitelist the way a careless "summarize
        everything reachable" implementation could."""
        parts = [
            text
            for domain in scope.subgraphs
            if (text := community_summary(self.store, entity_id, domain=domain, max_hops=scope.max_hops))
        ]
        return " ".join(parts) if parts else None

    @staticmethod
    def _excluded_domains(scope: RetrievalScope, purpose: str) -> list[dict]:
        excluded = []
        for domain, reason_template in _EXCLUSION_REASONS.items():
            if domain in scope.subgraphs:
                continue
            excluded.append({"domain": domain, "reason": reason_template.format(purpose=purpose)})
        return excluded
