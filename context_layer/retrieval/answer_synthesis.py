"""The generation half of "RAG" — turns an already policy-scoped Context
Package into a natural-language answer to a free-text question.

Deterministic and template-based on purpose: every sentence is built
directly from a field already present in the Context Package (facts,
relationships, community_summary, recommended_content, constraints,
excluded), so the
answer is faithful to its retrieved context by construction — nothing
here can introduce a claim retrieval didn't already return. That's what
makes it a useful baseline for the evaluation harness in `evaluation/`:
a faithfulness/hallucination metric run against this should score high,
and a metric that doesn't catch a hand-broken variant (see
`evaluation/dataset.py`'s adversarial case) isn't measuring anything.
"""

from __future__ import annotations


def synthesize_answer(package: dict, question: str) -> str:
    display = package["entity"]["display"]
    lines = [f"Regarding \"{question}\" — here's what I have on {display} within my permitted scope:"]

    if package.get("community_summary"):
        lines.append(package["community_summary"])

    if package["relationships"]:
        rels = ", ".join(f"{r['type']} {r['display']}" for r in package["relationships"])
        lines.append(f"Relationships: {rels}.")

    if package["facts"]:
        lines.append("Relevant history:")
        lines.extend(f"- {fact['claim']}" for fact in package["facts"])
    else:
        lines.append("No on-topic history found within this scope.")

    if package["recommended_content"]:
        titles = ", ".join(f"\"{c['title']}\"" for c in package["recommended_content"])
        lines.append(f"Approved content you could reference: {titles}.")

    if package["constraints"]:
        lines.append("Before acting on this: " + " ".join(package["constraints"]))

    if package["excluded"]:
        reasons = "; ".join(f"{e['domain']} ({e['reason']})" for e in package["excluded"])
        lines.append(f"Out of scope for this purpose, so not reflected above: {reasons}.")

    return "\n".join(lines)
