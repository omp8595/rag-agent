"""The bridge whitelist — design doc section 3.

"Bridges are whitelisted edges, not open traversal." This table is owned
by Compliance and versioned; it is the single most important artifact for
approval, so it lives as data (not scattered conditionals) and every
traversal consults it before crossing a domain subgraph boundary.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Bridge:
    id: str
    from_domain: str
    to_domain: str
    edge_types: frozenset[str]
    mode: str  # "full" | "flag_only"
    condition: str


# Approved bridges. Adding, removing, or narrowing an entry here requires
# Compliance sign-off (open decision #3 in the design doc: who arbitrates
# changes — recorded here as owner/version so the artifact is auditable).
OWNER = "Compliance"
VERSION = "1.0"

BRIDGE_WHITELIST: dict[str, Bridge] = {
    b.id: b
    for b in [
        Bridge(
            id="medical.publications->commercial",
            from_domain="medical",
            to_domain="commercial",
            edge_types=frozenset({"AUTHORED"}),
            mode="full",
            condition="Public-domain publications only; MSL interactions never bridge.",
        ),
        Bridge(
            id="clinical.investigator_status->commercial",
            from_domain="clinical",
            to_domain="commercial",
            edge_types=frozenset({"PRINCIPAL_INVESTIGATOR_OF"}),
            mode="flag_only",
            condition=(
                "Boolean 'is active investigator' for promotional-compliance "
                "exclusion only; no study details are exposed."
            ),
        ),
    ]
}

# Explicitly denied crossings, kept here for documentation and for the
# "why was this excluded" audit trail — these never appear in a granted
# retrieval scope, whatever purpose is requested.
DENIED_BRIDGES: list[dict] = [
    {
        "from_domain": "commercial",
        "to_domain": "clinical",
        "reason": "Regulatory: commercial data must not influence site selection.",
    },
    {
        "from_domain": "commercial",
        "to_domain": "medical",
        "reason": "Firewall.",
    },
]


def get_bridge(bridge_id: str) -> Bridge | None:
    return BRIDGE_WHITELIST.get(bridge_id)


def bridges_into(to_domain: str) -> list[Bridge]:
    return [b for b in BRIDGE_WHITELIST.values() if b.to_domain == to_domain]
