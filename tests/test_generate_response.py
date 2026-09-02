"""ThinAgent.generate_response: the full agent -> context -> LLM ->
grounded-response flow, and answer_question's continued backward
compatibility as a thin wrapper over it."""

from context_layer.llm.provider import MockLLMProvider


def test_generate_response_returns_a_grounded_answer(hcp_agent, active_investigator_hcp):
    result = hcp_agent.generate_response(active_investigator_hcp, "What is the appropriate next engagement context?")
    assert result["llm_provider"] == "mock"
    assert result["context_package_id"] == result["package"]["request_id"]
    assert result["supporting_fact_ids"]  # the mock provider's template always cites real facts
    assert result["warnings"] == []


def test_generate_response_accepts_an_explicit_provider(hcp_agent):
    result = hcp_agent.generate_response("HCP-001", "What should I know?", provider=MockLLMProvider())
    assert result["llm_provider"] == "mock"


def test_answer_question_is_a_stable_wrapper_over_generate_response(hcp_agent):
    result = hcp_agent.answer_question("HCP-001", "What should I know?")
    assert set(result.keys()) == {"package", "answer"}
    full = hcp_agent.generate_response("HCP-001", "What should I know?")
    assert result["answer"] == full["answer"]


def test_generate_response_respects_context_tool_authorization(site_agent):
    """generate_response calls get_context internally - an agent without
    get_context_package in its context_tools must still be refused."""
    import pytest

    from context_layer.agent_builder.agent import ThinAgent
    from context_layer.agent_builder.schema import AgentConfig

    no_context_tools = ThinAgent(
        AgentConfig(name="No Context Agent", purpose="commercial_engagement", audience_roles=["brand_manager"], context_tools=[]),
        site_agent.assembler,
    )
    with pytest.raises(PermissionError):
        no_context_tools.generate_response("HCP-001", "anything")
