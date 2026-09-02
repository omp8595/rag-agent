from __future__ import annotations

import pytest

from context_layer.api.app import build_assembler
from context_layer.data.loader import load_source_data


@pytest.fixture(scope="module")
def assembler():
    return build_assembler()


@pytest.fixture(scope="module")
def source_data():
    return load_source_data()


@pytest.fixture(scope="module")
def active_investigator_hcp(source_data):
    return next(r for r in source_data["investigator_sites"] if r["active"])["hcp_id"]
