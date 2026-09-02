"""The demo HTTP API (context_layer/api/http_server.py) — Phase 3/4.
Exercises the same security properties the rest of the suite validates,
now through the HTTP boundary: purpose cannot be overridden by a
request, unknown agents/entities fail safely with no stack trace, and
/demo/compare is computed live, not fabricated.
"""

import json

import pytest
from fastapi.testclient import TestClient

from context_layer.api.http_server import app


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_ready(client):
    response = client.get("/ready")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ready"
    assert set(body["agents_loaded"]) == {"hcp_engagement_agent", "site_selection_agent"}
    assert body["entities_loaded"] == 50


def test_context_returns_the_bound_purpose_not_a_client_supplied_one(client):
    response = client.post("/context", json={"agent_id": "hcp_engagement_agent", "entity_id": "HCP-001", "question": "What should I know?"})
    assert response.status_code == 200
    assert response.json()["context_package"]["purpose"] == "commercial_engagement"


def test_a_purpose_field_in_the_request_body_is_rejected_not_silently_dropped(client):
    """The critical security requirement: purpose cannot override the
    published agent config. A 422 naming the field is the correct,
    auditable failure mode — silently ignoring it would look identical
    to a caller as "it worked," which is worse."""
    response = client.post(
        "/context", json={"agent_id": "hcp_engagement_agent", "entity_id": "HCP-001", "question": "x", "purpose": "site_selection"}
    )
    assert response.status_code == 422
    assert any(err["loc"] == ["body", "purpose"] for err in response.json()["detail"])


def test_unknown_agent_fails_safely_with_no_stack_trace(client):
    response = client.post("/context", json={"agent_id": "not_a_real_agent", "entity_id": "HCP-001", "question": "x"})
    assert response.status_code == 404
    assert response.json()["detail"]["error"] == "agent_not_found"
    assert "Traceback" not in response.text


def test_unknown_entity_fails_predictably_with_no_stack_trace(client):
    response = client.post("/context", json={"agent_id": "hcp_engagement_agent", "entity_id": "HCP-does-not-exist", "question": "x"})
    assert response.status_code == 404
    assert response.json()["detail"]["error"] == "entity_not_found"
    assert "Traceback" not in response.text


def test_every_response_carries_a_request_id_header(client):
    response = client.get("/health")
    assert response.headers.get("x-request-id", "").startswith("req-")


def test_demo_commercial_and_demo_clinical_use_their_bound_purposes(client):
    commercial = client.get("/demo/commercial")
    clinical = client.get("/demo/clinical")
    assert commercial.json()["context_package"]["purpose"] == "commercial_engagement"
    assert clinical.json()["context_package"]["purpose"] == "site_selection"


def test_request_log_captures_governance_fields(client, caplog):
    """Phase 10 observability: agent_id, entity_id, bound purpose,
    allowed domains, and context package id must actually appear in the
    structured log — not just be declared fields nothing populates.

    Uses caplog (pytest's logging-record capture), not capsys: the
    service's StreamHandler binds sys.stdout at logging-setup time
    (during the module-scoped client fixture's app startup), which runs
    before any individual test's capsys starts monkeypatching stdout —
    caplog captures at the logging-record level instead, unaffected by
    that ordering."""
    with caplog.at_level("INFO", logger="context_layer.api"):
        client.post("/context", json={"agent_id": "hcp_engagement_agent", "entity_id": "HCP-001", "question": "x"})

    log_lines = [json.loads(record.message) for record in caplog.records if record.message.strip().startswith("{")]
    request_log = next(entry for entry in log_lines if entry.get("path") == "/context")

    assert request_log["agent_id"] == "hcp_engagement_agent"
    assert request_log["entity_id"] == "HCP-001"
    assert request_log["purpose"] == "commercial_engagement"
    assert request_log["allowed_domains"] == ["commercial"]
    assert request_log["context_package_id"].startswith("ctx-")
    assert "latency_ms" in request_log
    # never a secret or a raw exception payload
    assert "api_key" not in caplog.text.lower()
    assert "traceback" not in caplog.text.lower()


def test_demo_compare_is_computed_live_and_shows_the_primary_thesis(client):
    response = client.get("/demo/compare/HCP-021")
    assert response.status_code == 200
    body = response.json()

    comparison = body["comparison"]
    assert comparison["same_entity"] is True
    assert comparison["different_purpose"] is True
    assert comparison["different_allowed_domains"] is True
    assert comparison["different_context_package_ids"] is True
    assert comparison["forbidden_domain_leak"] == []
    assert comparison["unauthorized_bridge_traversal"] == []
    assert comparison["status"] == "PASS"

    # not fabricated: the two packages actually carry different real facts
    commercial_facts = {f["claim"] for f in body["commercial"]["context_package"]["facts"]}
    clinical_facts = {f["claim"] for f in body["clinical"]["context_package"]["facts"]}
    assert commercial_facts and clinical_facts
    assert commercial_facts.isdisjoint(clinical_facts)
