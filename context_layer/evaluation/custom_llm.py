"""A pluggable `DeepEvalBaseLLM` — the one custom-LLM adapter every
LLM-backed evaluator (`deepeval_evaluator`, `llm_judge`) shares, wired to
whichever provider `config.get_eval_llm_config()` resolves. Kept to raw
provider SDK calls (no langchain) to sidestep the dependency churn that
broke the `ragas` integration in this environment.
"""

from __future__ import annotations

from deepeval.models.base_model import DeepEvalBaseLLM

from context_layer.evaluation.config import EvalLLMConfig


class PluggableLLM(DeepEvalBaseLLM):
    def __init__(self, cfg: EvalLLMConfig):
        self.cfg = cfg
        self._client = self._build_client()
        super().__init__()

    def _build_client(self):
        if self.cfg.provider == "anthropic":
            import anthropic

            return anthropic.Anthropic(api_key=self.cfg.api_key)
        if self.cfg.provider == "openai":
            import openai

            return openai.OpenAI(api_key=self.cfg.api_key)
        raise ValueError(f"unsupported EVAL_LLM_PROVIDER '{self.cfg.provider}'")

    def load_model(self):
        return self._client

    def generate(self, prompt: str, *args, **kwargs) -> str:
        if self.cfg.provider == "anthropic":
            response = self._client.messages.create(
                model=self.cfg.model,
                max_tokens=1024,
                messages=[{"role": "user", "content": prompt}],
            )
            return "".join(block.text for block in response.content if hasattr(block, "text"))
        response = self._client.chat.completions.create(
            model=self.cfg.model,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.choices[0].message.content or ""

    async def a_generate(self, prompt: str, *args, **kwargs) -> str:
        return self.generate(prompt, *args, **kwargs)

    def get_model_name(self) -> str:
        return f"{self.cfg.provider}:{self.cfg.model}"
