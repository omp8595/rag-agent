"""Runtime half of "purpose is bound to the agent, not chosen by the
user": ThinAgent closes over a published AgentConfig and never exposes
purpose (or roles) as something a caller can pass in — every context
request an agent makes goes out under its own fixed identity.

Action tools (`action_tools` in the config) work the same way as context
tools — declared at publish time, checked before every call — plus one
more gate: an action named in `guardrails.human_approval_required` is
never executed here. It's submitted to the shared ApprovalQueue and comes
back `pending_approval`; only a human calling `approvals.approve()` moves
it further. `draft_email` adds a second kind of refusal on top of that:
it reads the Context Package's own `constraints` and declines to draft
promotional outreach when one names a promotional exclusion, instead of
drafting it and trusting a human to catch the conflict later.
"""

from __future__ import annotations

from context_layer.agent_builder import actions
from context_layer.agent_builder.approvals import ApprovalQueue
from context_layer.agent_builder.schema import AgentConfig
from context_layer.api.assembler import ContextAssembler
from context_layer.llm.grounding import ground_answer
from context_layer.llm.provider import LLMProvider, MockLLMProvider


class ThinAgent:
    def __init__(self, config: AgentConfig, assembler: ContextAssembler, approvals: ApprovalQueue | None = None):
        self.config = config
        self.assembler = assembler
        self.approvals = approvals if approvals is not None else ApprovalQueue()

    def get_context(self, entity_id: str, task: str = "") -> dict:
        if "get_context_package" not in self.config.context_tools:
            raise PermissionError(f"{self.config.name} is not configured with get_context_package")
        return self.assembler.get_context_package(
            entity_id,
            self.config.purpose,
            task,
            principal=self.config.name,
            principal_roles=self.config.audience_roles,
        )

    def find_content(self, topic: str = "", audience: str = "HCP") -> list[dict]:
        if "find_content" not in self.config.context_tools:
            raise PermissionError(f"{self.config.name} is not configured with find_content")
        return self.assembler.find_content(topic, audience)

    def explain_relationship(self, entity_a: str, entity_b: str) -> dict:
        if "explain_relationship" not in self.config.context_tools:
            raise PermissionError(f"{self.config.name} is not configured with explain_relationship")
        return self.assembler.explain_relationship(entity_a, entity_b, self.config.purpose)

    def answer_question(self, entity_id: str, question: str) -> dict:
        """Generation step, mock provider: a grounded natural-language
        answer, built only from an already policy-scoped Context Package.
        Kept as a thin, stable wrapper around `generate_response` for
        existing callers (campaign_workflow.py, the evaluation runner)
        that only need `{"package", "answer"}`."""
        result = self.generate_response(entity_id, question)
        return {"package": result["package"], "answer": result["answer"]}

    def generate_response(self, entity_id: str, question: str, provider: LLMProvider | None = None) -> dict:
        """The full agent -> context -> LLM -> grounded response flow.
        `provider` defaults to `MockLLMProvider` (deterministic, no
        credentials). The provider receives only `package` and `question`
        — it has no reference to `self.assembler` or the graph store, so
        there is no path from "LLM" back to raw enterprise data; the
        Context Package is the only thing it can see. The response is
        then checked against that same package (`ground_answer`) so a
        claim the model invented is distinguishable from one the package
        actually supports."""
        package = self.get_context(entity_id, question)
        provider = provider or MockLLMProvider()
        generated = provider.generate(package, question)
        grounded = ground_answer(package, generated["answer"])
        return {
            "package": package,
            "answer": grounded["answer"],
            "context_package_id": grounded["context_package_id"],
            "supporting_fact_ids": grounded["supporting_fact_ids"],
            "unsupported_fact_ids": grounded["unsupported_fact_ids"],
            "warnings": grounded["warnings"],
            "llm_provider": generated["provider"],
            "llm_model": generated["model"],
        }

    # -- action tools ----------------------------------------------------
    #
    # Authorization (`_require_action`) always runs first, before any
    # context lookup or business-rule evaluation — an unauthorized caller
    # gets a PermissionError, never a "blocked" or "executed" result that
    # would reveal the action ran at all.

    def draft_email(self, entity_id: str, task: str = "") -> dict:
        self._require_action("draft_email")
        package = self.get_context(entity_id, task)
        draft = actions.build_email_draft(package, task)
        if draft["blocked"]:
            return {"status": "blocked", **draft}
        return self._dispatch("draft_email", draft)

    def create_campaign_task(self, entity_id: str, content_id: str, task: str = "") -> dict:
        self._require_action("create_campaign_task")
        package = self.get_context(entity_id, task)
        content = self.assembler.store.node(content_id)
        if content is None or content.get("node_type") != "Content":
            return {"status": "blocked", "action": "create_campaign_task", "reason": f"{content_id} is not known content"}
        if self.config.guardrails.approved_content_only and content["approval_status"] != "approved":
            return {"status": "blocked", "action": "create_campaign_task", "reason": f"{content_id} is not approved content"}
        payload = actions.build_campaign_task(package, {"id": content_id, "title": content["title"]})
        return self._dispatch("create_campaign_task", payload)

    def create_feasibility_note(self, entity_id: str, note_text: str) -> dict:
        self._require_action("create_feasibility_note")
        package = self.get_context(entity_id)
        payload = actions.build_feasibility_note(package, note_text)
        return self._dispatch("create_feasibility_note", payload)

    def _require_action(self, action_name: str) -> None:
        if action_name not in self.config.action_tools:
            raise PermissionError(f"{self.config.name} is not configured with {action_name}")

    def _dispatch(self, action_name: str, payload: dict) -> dict:
        if action_name in self.config.guardrails.human_approval_required:
            record = self.approvals.submit(action=action_name, agent=self.config.name, payload=payload)
            return {"status": "pending_approval", "approval_id": record.id, **payload}
        return {"status": "executed", **payload}
