"""Vector retrieval — design doc section 4, capability 4.

Per-domain indexes built at ingest, "which is what makes retrieval-time
scoping enforceable rather than aspirational": a commercial-purpose
request is handed the `commercial` index object and has no reference to
the `medical` one at all, so there's no query string that can reach it.

TF-IDF (scikit-learn) stands in for an embedding index here — same
per-domain isolation property, no external embedding API required to run
the prototype offline.
"""

from __future__ import annotations

from dataclasses import dataclass

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from context_layer.graph.store import GraphStore


@dataclass
class IndexedDoc:
    id: str
    node_type: str
    text: str


class DomainVectorIndex:
    def __init__(self, domain: str, docs: list[IndexedDoc]):
        self.domain = domain
        self.docs = docs
        self._vectorizer = TfidfVectorizer(stop_words="english")
        self._matrix = (
            self._vectorizer.fit_transform([d.text for d in docs]) if docs else None
        )

    def search(self, query: str, top_k: int = 5) -> list[tuple[IndexedDoc, float]]:
        if not self.docs or not query.strip():
            return []
        query_vec = self._vectorizer.transform([query])
        scores = cosine_similarity(query_vec, self._matrix)[0]
        ranked = sorted(zip(self.docs, scores), key=lambda pair: pair[1], reverse=True)
        return [(doc, float(score)) for doc, score in ranked[:top_k] if score > 0]


def build_domain_indexes(store: GraphStore) -> dict[str, DomainVectorIndex]:
    commercial_docs = [
        IndexedDoc(id=n["id"], node_type="Content", text=f"{n['title']} {n['topic']} {n['body_text']}")
        for n in store.find_nodes(node_type="Content", domain="commercial")
    ]
    medical_docs = [
        IndexedDoc(id=n["id"], node_type="Publication", text=f"{n['title']} {n['topic']} {n['abstract']}")
        for n in store.find_nodes(node_type="Publication", domain="medical")
    ]
    # Clinical has no free-text corpus in this prototype (studies carry only
    # structured/coded fields) — the index exists so lookups by domain name
    # stay uniform, but it will always return no results.
    clinical_docs: list[IndexedDoc] = []

    return {
        "commercial": DomainVectorIndex("commercial", commercial_docs),
        "medical": DomainVectorIndex("medical", medical_docs),
        "clinical": DomainVectorIndex("clinical", clinical_docs),
    }
