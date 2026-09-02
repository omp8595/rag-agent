"""LLM consumption layer — Phase 5's core claim in code: the LLM does not
decide what enterprise data it is allowed to see. Both providers below
take exactly two arguments — an already policy-scoped Context Package
(a plain dict) and a question — and nothing else. Neither has a reference
to the graph store, the assembler, or any credential beyond what its own
generation call needs. There is structurally no path from "LLM" back to
"raw enterprise data": the Context Package is the only thing it can see.

Reuses `context_layer.evaluation`'s provider config and pluggable LLM
adapter rather than inventing a second one — "which model answers on
behalf of this system" is one knob, whether it's judging an evaluation
case or generating a live response.
"""

from __future__ import annotations

from typing import Protocol

from context_layer.evaluation.config import get_eval_llm_config
from context_layer.evaluation.custom_llm import PluggableLLM
from context_layer.retrieval.answer_synthesis import synthesize_answer

_GROUNDED_PROMPT = """You are answering a question about an enterprise entity using ONLY the \
context below, which has already been scoped by policy before reaching you. Do not use any \
knowledge beyond what is written here, and do not speculate about information in domains marked \
as excluded.

For every factual claim you make that comes from a numbered fact below, cite its fact_id. End \
your answer with a line in exactly this format (empty if none apply):
CITED_FACTS: fact_001, fact_003

ENTITY: {display}
PURPOSE: {purpose}
ALLOWED DOMAINS: {allowed_domains}

FACTS:
{facts}

RELATIONSHIPS: {relationships}
COMMUNITY CONTEXT: {community_summary}
APPROVED CONTENT: {content}
CONSTRAINTS YOU MUST RESPECT: {constraints}
EXCLUDED (do not discuss, do not imply you know this): {excluded}

QUESTION: {question}
"""


class LLMProvider(Protocol):
    def generate(self, context_package: dict, question: str) -> dict:
        """Returns {"answer": str, "provider": str, "model": str}."""
        ...


class MockLLMProvider:
    """Default, deterministic, no credentials required. Delegates to
    `answer_synthesis.synthesize_answer` — the same template-grounded
    generation the rest of the prototype already uses, so "mock mode" and
    the existing `ThinAgent.answer_question` behavior are identical."""

    def generate(self, context_package: dict, question: str) -> dict:
        return {"answer": synthesize_answer(context_package, question), "provider": "mock", "model": "template-v1"}


class RealLLMProvider:
    """Optional. Uses whichever provider `EVAL_LLM_PROVIDER`/`ANTHROPIC_API_KEY`/
    `OPENAI_API_KEY` resolves to (context_layer.evaluation.config) — no
    credentials are read or hardcoded here. Raises at construction if none
    is configured, so a caller finds out immediately rather than on first use."""

    def __init__(self) -> None:
        cfg = get_eval_llm_config()
        if cfg is None:
            raise RuntimeError(
                "no LLM provider configured (set ANTHROPIC_API_KEY or OPENAI_API_KEY) — use MockLLMProvider instead"
            )
        self._llm = PluggableLLM(cfg)
        self._provider, self._model = cfg.provider, cfg.model

    def generate(self, context_package: dict, question: str) -> dict:
        prompt = _GROUNDED_PROMPT.format(
            display=context_package["entity"]["display"],
            purpose=context_package["purpose"],
            allowed_domains=context_package["policy_decision"]["allowed_domains"],
            facts="\n".join(f"[{f['fact_id']}] {f['claim']}" for f in context_package["facts"]) or "(none)",
            relationships=", ".join(f"{r['type']} {r['display']}" for r in context_package["relationships"]) or "(none)",
            community_summary=context_package.get("community_summary") or "(none)",
            content=", ".join(c["title"] for c in context_package["recommended_content"]) or "(none)",
            constraints="; ".join(context_package["constraints"]) or "(none)",
            excluded=context_package["policy_decision"]["forbidden_domains"] or "(none)",
            question=question,
        )
        answer = self._llm.generate(prompt)
        return {"answer": answer, "provider": self._provider, "model": self._model}
