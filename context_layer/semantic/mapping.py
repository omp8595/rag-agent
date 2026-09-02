"""Semantic (mapping) layer — design doc section 2.

Not a new ontology: a thin mapping table over existing standards and
enterprise hierarchies, plus the MDM crosswalk that answers "when
Commercial says *account* and Clinical says *site*, are they the same
institution?"
"""

from __future__ import annotations

from dataclasses import dataclass

# Enterprise concept -> standard(s) it is mapped from. Metadata only (used
# for lineage/display); the actual coded values live on the source records
# and are carried through onto graph nodes at ingest.
ENTERPRISE_CONCEPT_MAP: dict[str, str] = {
    "Person / HCP": "MDM golden ID, NPI, ORCID",
    "Specialty": "MDM specialty -> SNOMED CT",
    "Condition / Indication": "MedDRA, SNOMED CT",
    "Therapeutic Area": "Enterprise TA hierarchy",
    "Product / Brand": "Enterprise product master, RxNorm",
    "Study": "CDISC (protocol ID, phase, status)",
    "Site / Institution": "CTMS site ID -> MDM account ID",
    "Content": "DAM ID + approval status + intended audience",
    "Topic": "MeSH (for publications), enterprise topic taxonomy",
}


@dataclass(frozen=True)
class CrosswalkResult:
    entity_id: str
    matched_id: str
    confidence: float
    source: str


def crosswalk_institution_account(institution: dict) -> CrosswalkResult:
    """Resolves a Clinical/CTMS site (Institution record) to its MDM account.

    In this prototype the synthetic institution records already carry the
    MDM account ID (an exact match from MDM), so confidence is 1.0. A real
    integration would fall back to fuzzy name/address matching for
    unmatched sites and report a lower confidence score there.
    """
    return CrosswalkResult(
        entity_id=institution["id"],
        matched_id=institution["mdm_account_id"],
        confidence=1.0,
        source="MDM",
    )
