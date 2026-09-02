"""THE PRIMARY ACCEPTANCE TEST for the entire product.

Same HCP. Same underlying enterprise data. Two agents, two approved
purposes, using the exact questions from the acceptance scenario. Proves
the core product promise end to end — not by trusting any evaluator's
own self-report, but by recomputing every check directly against the raw
Context Package dicts and the real bridge whitelist.
"""

from context_layer.agent_builder.agent import ThinAgent
from context_layer.agent_builder.builder import load_agent_config, publish_agent
from context_layer.graph.bridges import BRIDGE_WHITELIST


def _unauthorized_bridge_uses(package: dict) -> list[tuple[str, str]]:
    """A fact from outside this package's own allowed domains is only
    legitimate if it names a real, granted bridge whose whitelist entry
    actually covers it — recomputed here independently of whatever
    graph_evaluator.py / policy_evaluator.py already assert."""
    allowed = set(package["policy_decision"]["allowed_domains"])
    granted_bridges = set(package["policy_decision"]["allowed_bridges"])
    violations = []
    for fact in package["facts"]:
        if fact["domain"] in allowed:
            continue
        bridge_id = fact["bridge"]
        if not bridge_id:
            violations.append((fact["fact_id"], "out-of-scope fact with no bridge tag"))
            continue
        bridge = BRIDGE_WHITELIST.get(bridge_id)
        if bridge is None:
            violations.append((fact["fact_id"], f"bridge {bridge_id!r} is not in the whitelist"))
        elif bridge.from_domain != fact["domain"]:
            violations.append((fact["fact_id"], f"bridge {bridge_id!r} from_domain mismatch"))
        elif bridge_id not in granted_bridges:
            violations.append((fact["fact_id"], f"bridge {bridge_id!r} used but not granted to this purpose"))
    return violations


def test_same_hcp_different_agent_purpose_yields_different_policy_compliant_packages(assembler, active_investigator_hcp):
    entity_id = active_investigator_hcp

    hcp_agent = ThinAgent(publish_agent(load_agent_config("agents/hcp_engagement.yaml")), assembler)
    site_agent = ThinAgent(publish_agent(load_agent_config("agents/site_selection.yaml")), assembler)

    package_a = hcp_agent.get_context(entity_id, "What context should I consider for the next approved engagement with this HCP?")
    package_b = site_agent.get_context(entity_id, "What context is available to assess this HCP and institution for clinical site selection?")

    # SAME ENTITY / SAME BASE DATA
    assert package_a["entity"]["id"] == package_b["entity"]["id"] == entity_id
    assert assembler.store.node(entity_id) is not None  # both drew from the one shared GraphStore

    # DIFFERENT AGENT / PURPOSE / POLICY DECISION / ALLOWED DOMAINS
    assert package_a["agent"]["agent_id"] != package_b["agent"]["agent_id"]
    assert package_a["purpose"] != package_b["purpose"]
    assert package_a["policy_decision"] != package_b["policy_decision"]
    assert set(package_a["policy_decision"]["allowed_domains"]) != set(package_b["policy_decision"]["allowed_domains"])

    # DIFFERENT RETRIEVED FACTS / DIFFERENT CONTEXT PACKAGE
    facts_a = {f["claim"] for f in package_a["facts"]}
    facts_b = {f["claim"] for f in package_b["facts"]}
    assert facts_a != facts_b
    assert facts_a.isdisjoint(facts_b)
    assert package_a["request_id"] != package_b["request_id"]

    # ZERO commercial facts in the clinical package, ZERO clinical facts in the commercial package
    commercial_facts_in_clinical = [f for f in package_b["facts"] if f["domain"] == "commercial"]
    clinical_facts_in_commercial = [f for f in package_a["facts"] if f["domain"] == "clinical"]
    assert commercial_facts_in_clinical == []
    assert clinical_facts_in_commercial == []

    # ZERO unauthorized bridge traversal in either direction
    assert _unauthorized_bridge_uses(package_a) == []
    assert _unauthorized_bridge_uses(package_b) == []

    # sanity: this scenario actually has data on both sides (a vacuous
    # pass — zero facts everywhere — would satisfy every assertion above
    # without proving anything)
    assert package_a["facts"]
    assert package_b["facts"]
