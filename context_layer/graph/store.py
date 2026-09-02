"""Partitioned knowledge graph — design doc section 3.

One networkx.MultiDiGraph holds everything, but every node and edge is
tagged with a `domain`: "spine" (Identity Spine — reference entities and
their standard-coded attributes only, no interactions) or one of
"commercial" / "medical" / "clinical" (behavioral, relational edges owned
by that domain). Partitioning is enforced by construction (loaders only
ever write into their own domain) and re-checked at traversal time, so a
bug in one loader can't silently leak another domain's edges.
"""

from __future__ import annotations

from dataclasses import dataclass

import networkx as nx

from context_layer.graph.bridges import Bridge

DOMAINS = {"spine", "commercial", "medical", "clinical"}


@dataclass
class Fact:
    """One traversed edge, with the lineage the Context Package requires."""

    src: str
    dst: str
    edge_type: str
    domain: str
    attrs: dict
    bridged_via: str | None = None  # bridge id, if this crossed a domain boundary


class GraphStore:
    def __init__(self) -> None:
        self.g = nx.MultiDiGraph()

    # -- construction -----------------------------------------------------

    def add_node(self, node_id: str, *, domain: str, node_type: str, **attrs) -> None:
        assert domain in DOMAINS, f"unknown domain {domain!r}"
        if self.g.has_node(node_id):
            self.g.nodes[node_id].update(attrs)
            return
        self.g.add_node(node_id, domain=domain, node_type=node_type, **attrs)

    def add_edge(self, src: str, dst: str, *, edge_type: str, domain: str, **attrs) -> None:
        assert domain in DOMAINS, f"unknown domain {domain!r}"
        self.g.add_edge(src, dst, key=edge_type, edge_type=edge_type, domain=domain, **attrs)

    # -- read ---------------------------------------------------------------

    def node(self, node_id: str) -> dict | None:
        if node_id not in self.g:
            return None
        return {"id": node_id, **self.g.nodes[node_id]}

    def find_nodes(self, node_type: str | None = None, domain: str | None = None) -> list[dict]:
        out = []
        for nid, data in self.g.nodes(data=True):
            if node_type and data.get("node_type") != node_type:
                continue
            if domain and data.get("domain") != domain:
                continue
            out.append({"id": nid, **data})
        return out

    def bounded_traversal(
        self,
        start: str,
        *,
        allowed_subgraphs: set[str],
        allowed_bridges: set[str],
        max_hops: int,
    ) -> list[Fact]:
        """BFS out from `start` up to `max_hops`, only ever crossing an edge
        that is either (a) in a domain the caller's retrieval scope permits,
        including "spine" identity edges which carry no policy risk, or
        (b) an explicitly whitelisted + scope-granted bridge edge.

        This is the single enforcement point for "policy scopes retrieval;
        it does not filter results" (design principle #2) — an edge that
        fails the check is never added to the graph the caller can see, it
        isn't fetched-then-hidden.
        """
        if start not in self.g:
            return []

        facts: list[Fact] = []
        seen_edges: set[tuple[str, str, str]] = set()
        frontier = [start]
        visited_nodes = {start}

        for _hop in range(max_hops):
            next_frontier: list[str] = []
            for node in frontier:
                for _, dst, key, data in self.g.out_edges(node, keys=True, data=True):
                    edge_domain = data["domain"]
                    edge_type = data["edge_type"]
                    bridge_id = None

                    if edge_domain == "spine" or edge_domain in allowed_subgraphs:
                        pass
                    else:
                        bridge = self._matching_bridge(edge_domain, edge_type, allowed_subgraphs)
                        if bridge is None or bridge.id not in allowed_bridges:
                            continue
                        bridge_id = bridge.id

                    edge_key = (node, dst, key)
                    if edge_key in seen_edges:
                        continue
                    seen_edges.add(edge_key)

                    facts.append(
                        Fact(
                            src=node,
                            dst=dst,
                            edge_type=edge_type,
                            domain=edge_domain,
                            attrs=dict(data),
                            bridged_via=bridge_id,
                        )
                    )
                    if dst not in visited_nodes:
                        visited_nodes.add(dst)
                        next_frontier.append(dst)
            frontier = next_frontier
            if not frontier:
                break

        return facts

    @staticmethod
    def _matching_bridge(edge_domain: str, edge_type: str, allowed_subgraphs: set[str]) -> Bridge | None:
        from context_layer.graph.bridges import BRIDGE_WHITELIST

        for bridge in BRIDGE_WHITELIST.values():
            if (
                bridge.from_domain == edge_domain
                and bridge.to_domain in allowed_subgraphs
                and edge_type in bridge.edge_types
            ):
                return bridge
        return None
