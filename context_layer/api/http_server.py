"""Demo HTTP API — Phase 3. A thin, security-conscious wrapper around the
same ThinAgent/ContextAssembler the MCP server and CLI scripts already
use. This does not replace the MCP server; it exists so the governance
story can be demonstrated over plain HTTP (curl, a browser, a load
balancer health check) without an MCP client.

Run: uvicorn context_layer.api.http_server:app --host 0.0.0.0 --port 8080
(or: python -m context_layer.api.http_server)

CRITICAL SECURITY PROPERTY: no request body accepted by this API has a
`purpose` field. `ContextRequest` uses `model_config = ConfigDict(extra="forbid")`,
so a client that sends one gets a 422 naming the rejected field, not a
silently-ignored one — purpose is bound to the published agent config
(context_layer/agent_builder/schema.py, frozen) and there is structurally
no parameter on this API through which a caller could influence it.
"""

from __future__ import annotations

import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel, ConfigDict

from context_layer.agent_builder.agent import ThinAgent
from context_layer.agent_builder.builder import load_agent_config, publish_agent
from context_layer.api.app import build_assembler
from context_layer.api.config import get_service_config
from context_layer.api.observability import configure_logging, new_request_id, timed_request
from context_layer.evaluation.isolation_evaluator import evaluate_isolation
from context_layer.evaluation.policy_evaluator import evaluate_policy
from context_layer.evaluation.schemas import EvaluationCase
from context_layer.llm.provider import MockLLMProvider

AGENT_CONFIG_PATHS = {
    "hcp_engagement_agent": "agents/hcp_engagement.yaml",
    "site_selection_agent": "agents/site_selection.yaml",
}

DEMO_QUESTIONS = {
    "hcp_engagement_agent": "What context should I consider for the next approved engagement with this HCP?",
    "site_selection_agent": "What context is available to assess this HCP and institution for clinical site selection?",
}

_state: dict = {}


@asynccontextmanager
async def lifespan(_app: FastAPI):
    config = get_service_config()
    configure_logging(config.log_level)
    assembler = build_assembler()
    agents = {agent_id: ThinAgent(publish_agent(load_agent_config(path)), assembler) for agent_id, path in AGENT_CONFIG_PATHS.items()}
    _state.update(config=config, assembler=assembler, agents=agents, started_at=time.time())
    yield
    _state.clear()


app = FastAPI(title="Life Sciences Enterprise Context Layer — Demo API", lifespan=lifespan)


# -- request/response models -------------------------------------------------


class ContextRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")  # a "purpose" field here is a 422, not a silent no-op

    agent_id: str
    entity_id: str
    question: str = ""


# -- error handling: no stack traces to the client, every failure logged with its request_id ---


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    request_id = getattr(request.state, "request_id", new_request_id())
    return JSONResponse(status_code=500, content={"error": "internal_error", "request_id": request_id})


class _KnownError(HTTPException):
    def __init__(self, status_code: int, error: str, detail: str):
        super().__init__(status_code=status_code, detail={"error": error, "message": detail})


@app.middleware("http")
async def request_id_and_logging(request: Request, call_next):
    request_id = new_request_id()
    request.state.request_id = request_id
    with timed_request(request.method, request.url.path, request_id) as entry:
        request.state.log_entry = entry  # handlers enrich this with agent_id/entity_id/purpose/... below
        response = await call_next(request)
        entry.status_code = response.status_code
    response.headers["X-Request-ID"] = request_id
    return response


def _enrich_log(request: Request, *, agent_id: str | None = None, package: dict | None = None) -> None:
    """Populates the observability fields Phase 10 asks for — agent_id,
    entity_id, bound purpose, allowed domains, context package id — onto
    the request's log entry, from data the handler already computed.
    Never called with anything from the request body itself beyond
    agent_id/entity_id, which are not secrets."""
    entry = getattr(request.state, "log_entry", None)
    if entry is None:
        return
    if agent_id:
        entry.agent_id = agent_id
    if package:
        entry.entity_id = package["entity"]["id"]
        entry.purpose = package["purpose"]
        entry.allowed_domains = package["policy_decision"]["allowed_domains"]
        entry.context_package_id = package["request_id"]


# -- endpoints ----------------------------------------------------------------


_LANDING_PAGE_HTML = """<!doctype html>
<html><head><title>Life Sciences Enterprise Context Layer — Demo</title>
<style>body{font-family:system-ui,sans-serif;max-width:40rem;margin:3rem auto;line-height:1.5;color:#222}
code{background:#f0f0f0;padding:0.1rem 0.3rem;border-radius:3px}
li{margin-bottom:0.4rem}a{color:#0a5}</style></head>
<body>
<h1>Life Sciences Enterprise Context Layer</h1>
<p><strong>PROTOTYPE VALIDATED — NOT PRODUCTION READY.</strong>
See <a href="https://github.com/omp8595/rag-agent/blob/main/docs/pilot_readiness_report.md">docs/pilot_readiness_report.md</a>.</p>
<p>This is the demo HTTP API — a thin wrapper over the same governed
Context Layer the MCP server uses. The primary thing to look at:</p>
<ul>
<li><a href="/demo/compare/HCP-021">/demo/compare/HCP-021</a> — the killer demo: same HCP, two agents, two purposes, two different governed Context Packages, computed live</li>
<li><a href="/docs">/docs</a> — interactive API documentation (Swagger UI, auto-generated) — try any endpoint from the browser</li>
<li><a href="/demo/commercial">/demo/commercial</a> — HCP Engagement Agent (commercial_engagement)</li>
<li><a href="/demo/clinical">/demo/clinical</a> — Site Selection Agent (site_selection)</li>
<li><a href="/health">/health</a> / <a href="/ready">/ready</a> — liveness / readiness</li>
</ul>
<p><code>POST /context</code> accepts <code>{"agent_id", "entity_id", "question"}</code> —
a <code>"purpose"</code> field is rejected with <code>422</code>, on purpose: purpose is
bound to the published agent, never a request parameter.</p>
<p>See <code>docs/deployment.md</code> for local/Docker instructions, and
<code>evaluation/pilot_dataset/</code> for the scenario set a pilot session runs.</p>
</body></html>"""


@app.get("/", response_class=HTMLResponse)
def landing_page() -> str:
    return _LANDING_PAGE_HTML


@app.get("/health")
def health() -> dict:
    return {"status": "healthy"}


@app.get("/ready")
def ready() -> dict:
    if "assembler" not in _state:
        raise _KnownError(503, "not_ready", "service is still starting up")
    return {
        "status": "ready",
        "app_env": _state["config"].app_env,
        "data_mode": _state["config"].data_mode,
        "agents_loaded": sorted(_state["agents"].keys()),
        "entities_loaded": len(_state["assembler"].store.find_nodes(node_type="Person")),
    }


def _get_agent(agent_id: str) -> ThinAgent:
    agent = _state["agents"].get(agent_id)
    if agent is None:
        raise _KnownError(404, "agent_not_found", f"unknown agent_id '{agent_id}'. Known agents: {sorted(_state['agents'].keys())}")
    return agent


def _run_agent(agent: ThinAgent, entity_id: str, question: str) -> dict:
    try:
        result = agent.generate_response(entity_id, question, provider=MockLLMProvider())
    except ValueError as exc:
        raise _KnownError(404, "entity_not_found", str(exc)) from None
    except PermissionError as exc:
        raise _KnownError(403, "forbidden", str(exc)) from None
    return {
        "context_package": result["package"],
        "answer": result["answer"],
        "supporting_fact_ids": result["supporting_fact_ids"],
        "unsupported_fact_ids": result["unsupported_fact_ids"],
        "warnings": result["warnings"],
        "llm_provider": result["llm_provider"],
        "llm_model": result["llm_model"],
    }


@app.post("/context")
def get_context(body: ContextRequest, request: Request) -> dict:
    agent = _get_agent(body.agent_id)
    result = _run_agent(agent, body.entity_id, body.question)
    _enrich_log(request, agent_id=body.agent_id, package=result["context_package"])
    return result


@app.api_route("/demo/commercial", methods=["GET", "POST"])
def demo_commercial(request: Request, entity_id: str = "HCP-021") -> dict:
    agent = _get_agent("hcp_engagement_agent")
    result = _run_agent(agent, entity_id, DEMO_QUESTIONS["hcp_engagement_agent"])
    _enrich_log(request, agent_id="hcp_engagement_agent", package=result["context_package"])
    return result


@app.api_route("/demo/clinical", methods=["GET", "POST"])
def demo_clinical(request: Request, entity_id: str = "HCP-021") -> dict:
    agent = _get_agent("site_selection_agent")
    result = _run_agent(agent, entity_id, DEMO_QUESTIONS["site_selection_agent"])
    _enrich_log(request, agent_id="site_selection_agent", package=result["context_package"])
    return result


@app.get("/demo/compare/{entity_id}")
def demo_compare(entity_id: str, request: Request) -> dict:
    """The primary live demo: same entity, two agents, two purposes —
    computed live against the real Context Layer, not fabricated. The
    `comparison` block is derived from the same deterministic evaluators
    (policy_evaluator, isolation_evaluator) the test suite uses."""
    commercial_agent = _get_agent("hcp_engagement_agent")
    clinical_agent = _get_agent("site_selection_agent")

    commercial = _run_agent(commercial_agent, entity_id, DEMO_QUESTIONS["hcp_engagement_agent"])
    clinical = _run_agent(clinical_agent, entity_id, DEMO_QUESTIONS["site_selection_agent"])
    _enrich_log(request, agent_id="hcp_engagement_agent+site_selection_agent", package=commercial["context_package"])

    package_a, package_b = commercial["context_package"], clinical["context_package"]
    case_a = EvaluationCase(id="compare-a", category="demo", entity_id=entity_id, question=DEMO_QUESTIONS["hcp_engagement_agent"], forbidden_domains=["clinical"])
    case_b = EvaluationCase(id="compare-b", category="demo", entity_id=entity_id, question=DEMO_QUESTIONS["site_selection_agent"], forbidden_domains=["commercial", "medical"])
    policy_a = evaluate_policy(case_a, package_a)
    policy_b = evaluate_policy(case_b, package_b)
    isolation = evaluate_isolation(package_a, package_b)

    unauthorized = not policy_a.policy_compliant or not policy_b.policy_compliant or bool(isolation.forbidden_domain_leak)

    return {
        "entity_id": entity_id,
        "commercial": commercial,
        "clinical": clinical,
        "comparison": {
            "same_entity": True,
            "different_purpose": package_a["purpose"] != package_b["purpose"],
            "different_allowed_domains": set(package_a["policy_decision"]["allowed_domains"]) != set(package_b["policy_decision"]["allowed_domains"]),
            "different_context_package_ids": package_a["request_id"] != package_b["request_id"],
            "different_retrieved_facts": {f["claim"] for f in package_a["facts"]} != {f["claim"] for f in package_b["facts"]},
            "forbidden_domain_leak": isolation.forbidden_domain_leak,
            "unauthorized_bridge_traversal": policy_a.violations + policy_b.violations,
            "status": "FAIL" if unauthorized else "PASS",
        },
    }


if __name__ == "__main__":
    import uvicorn

    cfg = get_service_config()
    uvicorn.run("context_layer.api.http_server:app", host=cfg.host, port=cfg.port)
