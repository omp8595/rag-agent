"""RAGAS adapter — context_precision, context_recall, faithfulness,
answer_relevancy.

`ragas` is an OPTIONAL extra, not a hard dependency (`pip install ragas`),
for two reasons: it pulls a heavy langchain stack, and — verified in this
repo's own dev environment — ragas 0.4.3's `ragas.llms.base` unconditionally
imports `langchain_community.chat_models.vertexai`, which does not exist in
any `langchain-community` release compatible with the rest of the current
langchain 1.x line pip resolves (confirmed with two different
langchain-community pins; both cascade into worse conflicts rather than
fixing it). That's an upstream packaging bug, not something to patch
around here. The guarded import below means: ragas missing, broken, or
unconfigured all degrade to the same `skipped` result — never a crash.
"""

from __future__ import annotations

from context_layer.evaluation.config import get_eval_llm_config
from context_layer.evaluation.schemas import EvaluationCase, FrameworkResult, MetricResult


def evaluate_with_ragas(case: EvaluationCase, retrieved_context: list[str], answer: str) -> FrameworkResult:
    cfg = get_eval_llm_config()
    if cfg is None:
        return FrameworkResult(framework="ragas", metrics=[], skipped=True, skip_reason="no EVAL_LLM_PROVIDER/API key configured")

    try:
        from ragas import EvaluationDataset, SingleTurnSample
        from ragas import evaluate as ragas_evaluate
        from ragas.embeddings import LangchainEmbeddingsWrapper
        from ragas.llms import LangchainLLMWrapper
        from ragas.metrics import Faithfulness, LLMContextPrecisionWithoutReference, LLMContextRecall, ResponseRelevancy
    except Exception as exc:  # noqa: BLE001 - any import failure (missing pkg or the known packaging bug) is a skip
        return FrameworkResult(framework="ragas", metrics=[], skipped=True, skip_reason=f"ragas unavailable in this environment: {exc}")

    try:
        chat_model = _build_langchain_chat_model(cfg)
        embeddings = _build_langchain_embeddings(cfg)
        judge_llm = LangchainLLMWrapper(chat_model)
        judge_embeddings = LangchainEmbeddingsWrapper(embeddings) if embeddings else None

        sample = SingleTurnSample(
            user_input=case.question,
            response=answer,
            retrieved_contexts=retrieved_context,
            reference=case.ground_truth_answer,
        )
        dataset = EvaluationDataset(samples=[sample])

        metrics = [Faithfulness(llm=judge_llm), ResponseRelevancy(llm=judge_llm, embeddings=judge_embeddings)]
        if case.ground_truth_answer:
            metrics += [LLMContextPrecisionWithoutReference(llm=judge_llm), LLMContextRecall(llm=judge_llm)]

        result = ragas_evaluate(dataset=dataset, metrics=metrics)
        scores = result.to_pandas().iloc[0].to_dict()
        return FrameworkResult(
            framework="ragas",
            metrics=[MetricResult(name=m.name, value=scores.get(m.name)) for m in metrics],
        )
    except Exception as exc:  # noqa: BLE001 - never let an evaluator crash the whole run
        return FrameworkResult(framework="ragas", metrics=[], skipped=True, skip_reason=f"ragas evaluation failed: {exc}")


def _build_langchain_chat_model(cfg):
    if cfg.provider == "openai":
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(model=cfg.model, api_key=cfg.api_key)
    from langchain_anthropic import ChatAnthropic  # optional extra: pip install langchain-anthropic

    return ChatAnthropic(model=cfg.model, api_key=cfg.api_key)


def _build_langchain_embeddings(cfg):
    if cfg.provider != "openai":
        return None  # Anthropic has no embeddings API; context_precision/recall are skipped for that provider
    from langchain_openai import OpenAIEmbeddings

    return OpenAIEmbeddings(api_key=cfg.api_key)
