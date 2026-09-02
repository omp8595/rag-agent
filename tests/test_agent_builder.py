import pytest

from context_layer.agent_builder.agent import ThinAgent
from context_layer.agent_builder.builder import AgentValidationError, load_agent_config, publish_agent
from context_layer.agent_builder.schema import AgentConfig


def test_hcp_engagement_agent_config_is_valid():
    config = publish_agent(load_agent_config("agents/hcp_engagement.yaml"))
    assert config.purpose == "commercial_engagement"


def test_site_selection_agent_config_is_valid():
    config = publish_agent(load_agent_config("agents/site_selection.yaml"))
    assert config.purpose == "site_selection"


def test_role_purpose_mismatch_is_rejected():
    bad = AgentConfig(
        name="Bad Agent",
        purpose="site_selection",
        audience_roles=["brand_manager"],
        context_tools=["get_context_package"],
    )
    with pytest.raises(AgentValidationError):
        publish_agent(bad)


def test_unregistered_purpose_is_rejected():
    bad = AgentConfig(
        name="Bad Agent",
        purpose="not_a_real_purpose",
        audience_roles=["brand_manager"],
        context_tools=["get_context_package"],
    )
    with pytest.raises(AgentValidationError):
        publish_agent(bad)


def test_thin_agent_purpose_is_not_a_call_argument(assembler):
    """ThinAgent.get_context has no `purpose` parameter at all — this test
    exists to catch a future refactor that accidentally reintroduces one,
    which would reopen the "rephrase to escalate" hole."""
    config = publish_agent(load_agent_config("agents/hcp_engagement.yaml"))
    agent = ThinAgent(config, assembler)
    import inspect

    assert "purpose" not in inspect.signature(agent.get_context).parameters
    pkg = agent.get_context("HCP-001")
    assert pkg["purpose"] == "commercial_engagement"
