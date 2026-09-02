"""Runtime half of "purpose is bound to the agent, not chosen by the
user": ThinAgent closes over a published AgentConfig and never exposes
purpose (or roles) as something a caller can pass in — every context
request an agent makes goes out under its own fixed identity.
"""

from __future__ import annotations

from context_layer.agent_builder.schema import AgentConfig
from context_layer.api.assembler import ContextAssembler


class ThinAgent:
    def __init__(self, config: AgentConfig, assembler: ContextAssembler):
        self.config = config
        self.assembler = assembler

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
