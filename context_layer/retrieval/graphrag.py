"""GraphRAG-lite — design doc section 4, capability 3.

"Community summaries pre-computed per domain (never across the firewall),
used for 'what does this HCP care about' style questions."

This is a deliberately minimal, extractive version — a real deployment
would run community detection + an LLM summarizer per domain at ingest.
The prototype instead ranks topics by frequency among the entity's
same-domain neighbors, which is enough to prove the property that
matters for the week-6 demo: the summary for one domain never draws on
another domain's community, purpose-bridged facts included. Open
decision #2 in the design doc asks whether the maintenance cost of full
GraphRAG is worth it over this bound-traversal-plus-vector combination;
this stub makes that tradeoff concrete rather than deciding it.
"""

from __future__ import annotations

from collections import Counter

from context_layer.graph.store import GraphStore

_TOPIC_FIELDS = {
    "Content": "topic",
    "Publication": "topic",
}


def community_summary(store: GraphStore, entity_id: str, *, domain: str, max_hops: int = 2) -> str | None:
    """A same-domain-only summary of what `entity_id` engages with, never
    crossing a bridge — bridged facts belong in the Context Package's
    `facts` list with their own lineage, not folded into a summary that
    would obscure where they came from.
    """
    facts = store.bounded_traversal(
        entity_id, allowed_subgraphs={domain}, allowed_bridges=set(), max_hops=max_hops
    )
    topics: Counter[str] = Counter()
    for fact in facts:
        node = store.node(fact.dst)
        if not node:
            continue
        topic_field = _TOPIC_FIELDS.get(node.get("node_type", ""))
        if topic_field and node.get(topic_field):
            topics[node[topic_field]] += 1

    if not topics:
        return None

    top = [topic for topic, _ in topics.most_common(3)]
    return f"Within {domain}, this entity's activity clusters around: {', '.join(top)}."
