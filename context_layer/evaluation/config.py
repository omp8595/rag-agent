"""One place LLM provider/credential config is read from — every LLM-backed
evaluator (ragas_evaluator, deepeval_evaluator, llm_judge) goes through
this, so there is exactly one skip/error path to test, not three.

Env vars:
  EVAL_LLM_PROVIDER   "anthropic" | "openai"  (default: whichever key is set;
                       anthropic wins if both are)
  EVAL_MODEL           model id (defaults per provider below)
  ANTHROPIC_API_KEY / OPENAI_API_KEY
"""

from __future__ import annotations

import os
from dataclasses import dataclass

_DEFAULT_MODELS = {
    "anthropic": "claude-sonnet-5",
    "openai": "gpt-4o-mini",
}


@dataclass(frozen=True)
class EvalLLMConfig:
    provider: str
    model: str
    api_key: str


def get_eval_llm_config() -> EvalLLMConfig | None:
    """Returns None (not an error) when no provider is configured — every
    caller is expected to treat that as "skip this metric", per the
    "never crash the suite for a missing key" requirement."""
    anthropic_key = os.environ.get("ANTHROPIC_API_KEY")
    openai_key = os.environ.get("OPENAI_API_KEY")
    provider = os.environ.get("EVAL_LLM_PROVIDER", "").lower() or None

    if provider is None:
        if anthropic_key:
            provider = "anthropic"
        elif openai_key:
            provider = "openai"
        else:
            return None

    api_key = anthropic_key if provider == "anthropic" else openai_key
    if not api_key:
        return None

    model = os.environ.get("EVAL_MODEL") or _DEFAULT_MODELS.get(provider)
    if model is None:
        return None
    return EvalLLMConfig(provider=provider, model=model, api_key=api_key)
