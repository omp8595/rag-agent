"""Loads source records (context_layer.data.loader) into the partitioned
GraphStore: Identity Spine first, then each domain's behavioral edges.
Mirrors design doc section 8 — each domain "registers" its sources and
owns writing into its own subgraph only.
"""

from __future__ import annotations

from context_layer.data.loader import load_source_data
from context_layer.graph.store import GraphStore
from context_layer.semantic.mapping import crosswalk_institution_account


def _load_identity_spine(store: GraphStore, source: dict) -> None:
    ta_nodes: set[str] = set()
    for hcp in source["hcps"]:
        store.add_node(
            hcp["id"],
            domain="spine",
            node_type="Person",
            display=hcp["display"],
            npi=hcp["npi"],
            orcid=hcp["orcid"],
            specialty=hcp["specialty"],
            personal_email=hcp["personal_email"],
        )
        ta_id = f"TA-{hcp['therapeutic_area'].replace(' ', '_')}"
        if ta_id not in ta_nodes:
            store.add_node(ta_id, domain="spine", node_type="TherapeuticArea", name=hcp["therapeutic_area"])
            ta_nodes.add(ta_id)
        store.add_edge(hcp["id"], ta_id, edge_type="IN_THERAPEUTIC_AREA", domain="spine")

    for inst in source["institutions"]:
        crosswalk = crosswalk_institution_account(inst)
        store.add_node(
            inst["id"],
            domain="spine",
            node_type="Institution",
            name=inst["name"],
            institution_type=inst["type"],
            country=inst["country"],
            mdm_account_id=crosswalk.matched_id,
            mdm_crosswalk_confidence=crosswalk.confidence,
        )

    for hcp in source["hcps"]:
        store.add_edge(hcp["id"], hcp["institution_id"], edge_type="WORKS_AT", domain="spine")


def _load_commercial(store: GraphStore, source: dict) -> None:
    for content in source["content"]:
        store.add_node(
            content["id"],
            domain="commercial",
            node_type="Content",
            title=content["title"],
            topic=content["topic"],
            mesh_code=content["mesh_code"],
            therapeutic_area=content["therapeutic_area"],
            approval_status=content["approval_status"],
            audience=content["audience"],
            body_text=content["body_text"],
        )

    territories: set[str] = set()
    for hcp in source["hcps"]:
        terr_id = f"TERR-{hcp['territory']}"
        if terr_id not in territories:
            store.add_node(terr_id, domain="commercial", node_type="Territory", name=hcp["territory"])
            territories.add(terr_id)
        store.add_edge(hcp["id"], terr_id, edge_type="IN_TERRITORY", domain="commercial")

    for interaction in source["interactions"]:
        store.add_edge(
            interaction["hcp_id"],
            interaction["content_id"],
            edge_type="ENGAGED_WITH",
            domain="commercial",
            interaction_id=interaction["id"],
            channel=interaction["channel"],
            date=interaction["date"],
        )


def _load_medical(store: GraphStore, source: dict) -> None:
    for pub in source["publications"]:
        store.add_node(
            pub["id"],
            domain="medical",
            node_type="Publication",
            title=pub["title"],
            topic=pub["topic"],
            mesh_code=pub["mesh_code"],
            journal=pub["journal"],
            date=pub["date"],
            abstract=pub["abstract"],
        )
        for author_id in pub["author_hcp_ids"]:
            store.add_edge(author_id, pub["id"], edge_type="AUTHORED", domain="medical")

    for msl in source["msl_interactions"]:
        node_id = msl["id"]
        store.add_node(
            node_id,
            domain="medical",
            node_type="MedicalInquiry",
            msl_id=msl["msl_id"],
            topic=msl["topic"],
            date=msl["date"],
        )
        store.add_edge(msl["hcp_id"], node_id, edge_type="MSL_INTERACTION", domain="medical")


def _load_clinical(store: GraphStore, source: dict) -> None:
    for study in source["studies"]:
        store.add_node(
            study["id"],
            domain="clinical",
            node_type="Study",
            protocol_id=study["protocol_id"],
            phase=study["phase"],
            status=study["status"],
            therapeutic_area=study["therapeutic_area"],
        )

    for record in source["investigator_sites"]:
        store.add_edge(
            record["hcp_id"],
            record["study_id"],
            edge_type="PRINCIPAL_INVESTIGATOR_OF",
            domain="clinical",
            enrollment_rate=record["enrollment_rate"],
            feasibility_score=record["feasibility_score"],
            active=record["active"],
        )
        store.add_edge(
            record["site_institution_id"],
            record["study_id"],
            edge_type="SITE_OF",
            domain="clinical",
        )


def build_graph_store() -> GraphStore:
    source = load_source_data()
    store = GraphStore()
    _load_identity_spine(store, source)
    _load_commercial(store, source)
    _load_medical(store, source)
    _load_clinical(store, source)
    return store
