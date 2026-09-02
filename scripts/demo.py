"""Week-6 demo (design doc section 9): one HCP entity, two published
agents bound to different purposes, two provably different Context
Packages — plus the audit log entries showing why.

Run: python scripts/demo.py
"""

from __future__ import annotations

import json

from context_layer.agent_builder.agent import ThinAgent
from context_layer.agent_builder.builder import load_agent_config, publish_agent
from context_layer.api.app import build_assembler
from context_layer.data.loader import load_source_data


def _pick_demo_entity() -> str:
    """An HCP who is simultaneously commercially engaged, a publishing
    author, and an active clinical investigator — so all three domains
    (and both bridges) have something to show or withhold."""
    source = load_source_data()
    active = next(r for r in source["investigator_sites"] if r["active"])
    return active["hcp_id"]


def _print_package(agent_name: str, package: dict) -> None:
    print(f"\n{'=' * 70}\n{agent_name} -> {package['entity']['display']} ({package['entity']['id']})\n{'=' * 70}")
    print("purpose:       ", package["purpose"])
    print("scope_applied: ", package["scope_applied"])
    print(f"facts ({len(package['facts'])}):")
    for fact in package["facts"]:
        bridge = f"  [bridged via {fact['bridge']}]" if fact["bridge"] else ""
        print(f"  - [{fact['domain']}] {fact['claim']}{bridge}")
    print(f"constraints ({len(package['constraints'])}):")
    for c in package["constraints"]:
        print(f"  - {c}")
    print(f"excluded ({len(package['excluded'])}):")
    for e in package["excluded"]:
        print(f"  - [{e['domain']}] {e['reason']}")
    print("lineage_id:    ", package["lineage_id"])


def main() -> None:
    assembler = build_assembler()
    entity_id = _pick_demo_entity()

    hcp_agent = ThinAgent(publish_agent(load_agent_config("agents/hcp_engagement.yaml")), assembler)
    site_agent = ThinAgent(publish_agent(load_agent_config("agents/site_selection.yaml")), assembler)

    commercial_pkg = hcp_agent.get_context(entity_id, task="biomarker testing outreach")
    clinical_pkg = site_agent.get_context(entity_id)

    _print_package("HCP Engagement Agent (commercial_engagement)", commercial_pkg)
    _print_package("Site Selection Agent (site_selection)", clinical_pkg)

    print(f"\n{'=' * 70}\nAudit log (last 2 entries)\n{'=' * 70}")
    for entry in assembler.audit_log.entries[-2:]:
        print(json.dumps(entry, indent=2))

    print(
        "\nSame entity, one platform, two agents, provably different context: "
        f"commercial_engagement saw {len(commercial_pkg['facts'])} facts and withheld "
        f"{len(commercial_pkg['excluded'])} domains; site_selection saw "
        f"{len(clinical_pkg['facts'])} facts and never received a single commercial-domain fact."
    )


if __name__ == "__main__":
    main()
