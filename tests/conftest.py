from __future__ import annotations

import pytest

from context_layer.agent_builder.agent import ThinAgent
from context_layer.agent_builder.approvals import ApprovalQueue
from context_layer.agent_builder.builder import load_agent_config, publish_agent
from context_layer.api.app import build_assembler
from context_layer.data.loader import load_source_data


@pytest.fixture(scope="module")
def assembler():
    return build_assembler()


@pytest.fixture(scope="module")
def approval_queue():
    return ApprovalQueue()


@pytest.fixture(scope="module")
def hcp_agent(assembler, approval_queue):
    config = publish_agent(load_agent_config("agents/hcp_engagement.yaml"))
    return ThinAgent(config, assembler, approval_queue)


@pytest.fixture(scope="module")
def site_agent(assembler, approval_queue):
    config = publish_agent(load_agent_config("agents/site_selection.yaml"))
    return ThinAgent(config, assembler, approval_queue)


@pytest.fixture(scope="module")
def source_data():
    return load_source_data()


@pytest.fixture(scope="module")
def active_investigator_hcp(source_data):
    return next(r for r in source_data["investigator_sites"] if r["active"])["hcp_id"]
