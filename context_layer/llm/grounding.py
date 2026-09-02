"""Response grounding — Phase 6: every generated answer must be
traceable to the Context Package that produced it, so the system can
distinguish a supported answer from an unsupported claim rather than
trusting the model's fluency.

Two grounding signals, tried in order:

1. Explicit citation — a real LLM provider is prompted to end its answer
   with `CITED_FACTS: fact_001, fact_003`. Any cited id that isn't
   actually in this Context Package is an unsupported claim — the
   strongest signal available, and the one that matters most, since it
   catches the model naming a fact_id it fabricated.
2. Substring fallback — for the deterministic mock provider (and any
   real answer that cites nothing), a fact "supports" the answer if its
   claim text literally appears in it. Weaker, but appropriate for
   template-grounded text where citation isn't part of the format.

This is not an attempt to solve hallucination detection in general — it's
a clean, cheap architecture that makes grounding checkable and gives the
evaluation layer (llm_judge's faithfulness dimension, RAGAS/DeepEval
faithfulness metrics) something concrete to independently verify against.
"""

from __future__ import annotations

import re

_CITATION_RE = re.compile(r"fact_\d{3}")


def ground_answer(package: dict, answer: str) -> dict:
    fact_ids = {f["fact_id"] for f in package["facts"]}
    cited = set(_CITATION_RE.findall(answer))

    if cited:
        supporting_fact_ids = sorted(cited & fact_ids)
        unsupported_fact_ids = sorted(cited - fact_ids)
    else:
        supporting_fact_ids = sorted(f["fact_id"] for f in package["facts"] if f["claim"] and f["claim"] in answer)
        unsupported_fact_ids = []

    warnings = []
    if unsupported_fact_ids:
        warnings.append(f"answer cites fact id(s) not present in this Context Package: {unsupported_fact_ids}")
    if not supporting_fact_ids and package["facts"]:
        warnings.append("answer does not reference any retrieved fact")

    return {
        "answer": answer,
        "context_package_id": package["request_id"],
        "supporting_fact_ids": supporting_fact_ids,
        "unsupported_fact_ids": unsupported_fact_ids,
        "warnings": warnings,
    }
