"""Adapter interfaces — Phase 2: the extension points a production
deployment would implement to replace this prototype's in-memory
components, without changing anything above them (policy, retrieval,
Context Assembler, agents).

These are `Protocol`s, not base classes the current code inherits from —
introducing them here documents the seam and typechecks against it
without forcing a risky refactor of working code purely for architectural
elegance (see design principle "do not over-engineer" / "do not replace
working components simply for architectural elegance"). Each one names
the module that plays that role today and what a production
implementation would swap in instead.

| Interface                 | Prototype implementation                          | Production swap-in |
|----------------------------|---------------------------------------------------|---------------------|
| `DataSourceAdapter`        | `data/loader.py` + `data/synthetic_gen.py`         | CRM/CTMS/pub-feed connectors, API/event/batch ingestion |
| `KnowledgeGraphRepository`| `graph/store.py` (`GraphStore`, in-memory networkx)| Neo4j/RDF store, same partition + bridge-whitelist contract |
| `VectorStoreAdapter`      | `retrieval/vector_index.py` (`DomainVectorIndex`, TF-IDF) | A real embedding index (per-domain, same isolation property) |
| `IdentityProvider`        | `semantic/mapping.py` (`crosswalk_institution_account`) | Enterprise MDM |
| `SemanticMappingProvider` | `semantic/mapping.py` (`ENTERPRISE_CONCEPT_MAP`)   | Live SNOMED CT/MeSH/RxNorm/MedDRA terminology services |

See `docs/production_reference_architecture.md` for the full picture.
"""

from __future__ import annotations

from typing import Protocol


class DataSourceAdapter(Protocol):
    """A federated enterprise source system (design doc §1: CRM, CTMS,
    publications feed, MDM, ...). Ingestion is metadata- and
    relationship-first — bulk documents stay in source."""

    def fetch_records(self, record_type: str) -> list[dict]:
        """Returns raw records of one type, ready for a domain loader
        (see `graph/build.py`) to shape into graph nodes/edges."""
        ...


class KnowledgeGraphRepository(Protocol):
    """The partitioned graph (Identity Spine + domain subgraphs +
    whitelisted bridges). `graph/store.py`'s `GraphStore` is the
    in-memory prototype implementation; the contract itself —
    domain-tagged nodes/edges, bounded traversal that only crosses a
    domain boundary via a whitelisted bridge id — is what a real graph
    database implementation must preserve."""

    def add_node(self, node_id: str, *, domain: str, node_type: str, **attrs) -> None: ...

    def add_edge(self, src: str, dst: str, *, edge_type: str, domain: str, **attrs) -> None: ...

    def bounded_traversal(
        self, start: str, *, allowed_subgraphs: set[str], allowed_bridges: set[str], max_hops: int
    ) -> list:
        ...


class VectorStoreAdapter(Protocol):
    """A per-domain retrieval index (design doc §4.4). The isolation
    property — a commercial-purpose request never touches the medical
    index — is what a production embedding store must preserve; TF-IDF
    vs. a real embedding model is an implementation detail behind it."""

    def search(self, query: str, top_k: int = 5) -> list[tuple[object, float]]: ...


class IdentityProvider(Protocol):
    """Resolves a domain-local identifier (a CTMS site ID, a CRM account
    ID) to the enterprise MDM golden ID, with a confidence score where the
    match is inferred rather than exact (design doc §2)."""

    def resolve(self, local_id: str, local_system: str) -> tuple[str, float]:
        """Returns (golden_id, confidence)."""
        ...


class SemanticMappingProvider(Protocol):
    """Maps an enterprise concept to its standard coding system (SNOMED
    CT, MeSH, RxNorm, MedDRA, CDISC — design doc §2). The prototype's
    `semantic/mapping.py` is a static table; production is a live
    terminology service, potentially versioned per release."""

    def map_concept(self, enterprise_concept: str, value: str) -> dict:
        """Returns {"value": ..., "code": ..., "system": ...}."""
        ...
