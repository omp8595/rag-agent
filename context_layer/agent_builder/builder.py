"""Agent Builder — design doc section 7.

"Configuration, not code": loads a YAML agent definition and validates
that `purpose` + `audience_roles` is a permitted combination in the
policy engine *before* the agent can be published. This is the
publish-time half of "a Brand Manager cannot escalate by rephrasing" —
the runtime half is that ThinAgent (agent.py) never accepts purpose as a
call argument.
"""

from __future__ import annotations

from pathlib import Path

import yaml

from context_layer.agent_builder.schema import AgentConfig
from context_layer.policy.engine import PURPOSE_POLICIES, permitted_combination


class AgentValidationError(Exception):
    pass


def load_agent_config(path: str | Path) -> AgentConfig:
    raw = yaml.safe_load(Path(path).read_text())
    return AgentConfig(**raw["agent"])


def validate_agent_config(config: AgentConfig) -> None:
    if config.purpose not in PURPOSE_POLICIES:
        raise AgentValidationError(f"'{config.purpose}' is not a registered purpose")

    if not config.audience_roles:
        raise AgentValidationError("audience_roles must be non-empty")

    for role in config.audience_roles:
        if not permitted_combination(config.purpose, role):
            raise AgentValidationError(
                f"role '{role}' is not permitted for purpose '{config.purpose}'"
            )

    policy = PURPOSE_POLICIES[config.purpose]
    if config.guardrails.max_context_hops > policy.max_hops:
        raise AgentValidationError(
            f"guardrails.max_context_hops={config.guardrails.max_context_hops} exceeds "
            f"the policy-permitted max_hops={policy.max_hops} for '{config.purpose}'"
        )

    unknown_gated = set(config.guardrails.human_approval_required) - set(config.action_tools)
    if unknown_gated:
        raise AgentValidationError(
            f"guardrails.human_approval_required names {sorted(unknown_gated)}, which "
            f"{'is' if len(unknown_gated) == 1 else 'are'} not in action_tools={config.action_tools} "
            "— the guardrail would never actually gate anything"
        )


def publish_agent(config: AgentConfig) -> AgentConfig:
    """Validates and returns the config unchanged — the return value is
    what a real Agent Builder would hand to the agent runtime to
    instantiate. Raises AgentValidationError instead of publishing."""
    validate_agent_config(config)
    return config
