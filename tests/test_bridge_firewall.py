"""Proves the firewall table in design doc section 3 holds at the graph
layer, independent of policy: even asking for every bridge that exists,
a denied crossing (Commercial<->Medical, Commercial->Clinical) is never
reachable, and MSL interactions never cross any bridge at all.
"""

from context_layer.graph.bridges import BRIDGE_WHITELIST
from context_layer.graph.build import build_graph_store


def test_msl_interactions_never_bridge_anywhere(source_data):
    store = build_graph_store()
    hcp_with_msl = source_data["msl_interactions"][0]["hcp_id"]

    facts = store.bounded_traversal(
        hcp_with_msl,
        allowed_subgraphs={"commercial"},
        allowed_bridges=set(BRIDGE_WHITELIST.keys()),  # grant every bridge that exists
        max_hops=3,
    )
    assert not any(f.edge_type == "MSL_INTERACTION" for f in facts)


def test_commercial_to_medical_is_never_reachable(active_investigator_hcp):
    store = build_graph_store()
    facts = store.bounded_traversal(
        active_investigator_hcp,
        allowed_subgraphs={"medical"},
        allowed_bridges=set(BRIDGE_WHITELIST.keys()),
        max_hops=3,
    )
    assert not any(f.domain == "commercial" for f in facts)


def test_commercial_to_clinical_is_never_reachable(active_investigator_hcp):
    store = build_graph_store()
    facts = store.bounded_traversal(
        active_investigator_hcp,
        allowed_subgraphs={"clinical"},
        allowed_bridges=set(BRIDGE_WHITELIST.keys()),
        max_hops=3,
    )
    assert not any(f.domain == "commercial" for f in facts)


def test_only_two_bridges_are_whitelisted():
    # Guards against a future edit silently widening the whitelist without
    # updating this test (and, in a real deployment, without Compliance
    # sign-off — see graph/bridges.py).
    assert set(BRIDGE_WHITELIST.keys()) == {
        "medical.publications->commercial",
        "clinical.investigator_status->commercial",
    }
