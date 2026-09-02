"""Entity lookup — design doc section 4, capability 1: Identity Spine +
domain profile, with redactions applied per the retrieval scope.
"""

from __future__ import annotations

from context_layer.graph.store import GraphStore
from context_layer.policy.models import RetrievalScope


def get_entity_profile(store: GraphStore, entity_id: str, scope: RetrievalScope) -> dict:
    node = store.node(entity_id)
    if node is None:
        return {}

    profile: dict[str, dict] = {}

    if node.get("node_type") == "Person":
        if "specialty" in node:
            spec = node["specialty"]
            profile["specialty"] = {"value": spec["value"], "code": spec["code"], "source": "MDM"}
        if "personal_email" in node and "personal_email" not in scope.redactions:
            profile["personal_email"] = {"value": node["personal_email"], "source": "MDM"}

        for _, dst, data in store.g.out_edges(entity_id, data=True):
            if data["edge_type"] == "IN_THERAPEUTIC_AREA":
                ta = store.node(dst)
                if ta:
                    profile["therapeutic_area"] = {"value": ta["name"], "source": "Enterprise TA hierarchy"}
            if data["edge_type"] == "IN_TERRITORY" and "commercial" in scope.subgraphs:
                terr = store.node(dst)
                if terr:
                    profile["territory"] = {"value": terr["name"], "source": "CRM"}

    return profile
