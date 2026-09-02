# Deployment Guide

**PROTOTYPE VALIDATED — NOT PRODUCTION READY.** This document covers
running the validated prototype locally, in a container, and preparing
it for a controlled pilot. It does not describe a production deployment
— see [`docs/production_reference_architecture.md`](production_reference_architecture.md)
for what that would require.

## 1. Prototype status

The core governance hypothesis — same entity, different agent purpose,
different policy-compliant, non-leaking Context Package — has passed a
comprehensive adversarial validation pass, including one real
privilege-escalation vulnerability found and fixed. See
[`docs/test_report.md`](test_report.md) and
[`docs/deployment_validation_report.md`](deployment_validation_report.md)
for the full evidence.

## 2. Architecture overview

```
Enterprise Source Systems (synthetic in this prototype)
        │
Knowledge Graph (Identity Spine + Commercial/Medical/Clinical subgraphs)
        │
Policy Engine (purpose → retrieval scope, fail-closed)
        │
Context Assembler (entity lookup + graph traversal + vector search + GraphRAG)
        │
Context Package (facts + lineage + governance + audit)
        │
   ┌────┴────┐
LLM (mock    HTTP API / MCP server / CLI scripts
 or real)
```

Full detail: [`README.md`](../README.md), [`docs/design.md`](design.md).

## 3. Local setup

```bash
git clone <this-repo>
cd rag-agent
python3 -m venv .venv
./.venv/bin/pip install -e ".[dev,eval]"
```

## 4. Generate synthetic data

```bash
./.venv/bin/python -m context_layer.data.synthetic_gen
```

Deterministic (fixed seed) — 50 HCPs, 10 institutions, 30 content items,
100 interactions, 40 publications, 5 studies. The output is also
committed under `data/synthetic/` for convenience; this command
regenerates it identically.

## 5. Running tests

```bash
./.venv/bin/python -m pytest -v
```

118 tests, all deterministic — no LLM API key required. This is exactly
what CI runs on every push (`.github/workflows/ci.yml`).

## 6. Running the demo

```bash
./.venv/bin/python scripts/e2e_demo.py      # the killer demo: agent -> policy -> context -> LLM -> grounded response
./.venv/bin/python scripts/demo.py          # narrower week-6 demo
./.venv/bin/python scripts/campaign_workflow.py "Biomarker testing"
```

## 7. Starting the API

```bash
./.venv/bin/python -m context_layer.api.http_server
# or: ./.venv/bin/uvicorn context_layer.api.http_server:app --host 0.0.0.0 --port 8080
```

Then:

```bash
curl http://localhost:8080/health
curl http://localhost:8080/ready
curl http://localhost:8080/demo/compare/HCP-021
```

This does not replace the MCP server (`python -m context_layer.api.mcp_server`)
— it's a demonstration interface over plain HTTP for contexts (curl,
browsers, a load balancer) where an MCP client isn't practical.

## 8. Docker build

```bash
docker build -t rag-agent:local .
```

**Validation note:** this repository's own development sandbox has no
privileged Docker daemon access (`docker ps` fails; `service docker
start` is blocked by the sandbox's own `ulimit` restrictions), so the
actual `docker build`/`docker run` could not be executed there. What was
validated instead, in that environment: every step the `Dockerfile`
specifies — `pip install -r requirements.txt` into a clean virtualenv,
`python -m context_layer.data.synthetic_gen`, then `python -m
context_layer.api.http_server` as the exact CMD — run end-to-end, with
every endpoint in §9 curled and confirmed correct. The real `docker
build`/`docker run` steps are additionally validated by
`.github/workflows/ci.yml`'s `docker` job on every push, since GitHub's
hosted runners do have a working daemon — that job builds the image,
runs the container, and re-runs the primary acceptance test's compare
endpoint plus the purpose-override rejection against the actual running
container.

## 9. Docker run

```bash
docker run -d --name rag-agent -p 8080:8080 rag-agent:local
curl http://localhost:8080/health
curl http://localhost:8080/ready
curl http://localhost:8080/demo/commercial
curl http://localhost:8080/demo/clinical
curl http://localhost:8080/demo/compare/HCP-021
docker stop rag-agent
```

## 10. API endpoints

| Method | Path | Purpose |
|---|---|---|
| GET | `/health` | Liveness — always `{"status": "healthy"}` once the process is up |
| GET | `/ready` | Readiness — confirms the graph/agents actually loaded; 503 if not |
| POST | `/context` | `{"agent_id", "entity_id", "question"}` → a full Context Package + grounded answer. **A `"purpose"` field in the body is rejected with 422** — purpose is bound to the published agent, never a request parameter |
| GET/POST | `/demo/commercial` | HCP Engagement Agent against `entity_id` (default `HCP-021`) |
| GET/POST | `/demo/clinical` | Site Selection Agent against `entity_id` (default `HCP-021`) |
| GET | `/demo/compare/{entity_id}` | **The primary live demo** — both agents against the same entity, plus a live-computed isolation/leakage verdict |

Every response includes the full Context Package (`policy_decision`,
`lineage`, `governance`, `audit`) — see [`README.md`](../README.md#7-governance-model).
Errors are `{"error": "<code>", "message": "..."}` with an appropriate
HTTP status — never a stack trace (verified: `tests/test_http_api.py`).

## 11. Environment variables

All optional; the service starts and demos work with none of them set
(`APP_ENV=demo` is the effective default). See `.env.example`.

| Variable | Default | Purpose |
|---|---|---|
| `APP_ENV` | `demo` | reported by `/ready`, informational |
| `LOG_LEVEL` | `INFO` | structured request-log verbosity |
| `HOST` | `0.0.0.0` | bind address |
| `PORT` | `8080` | bind port |
| `DATA_MODE` | `synthetic` | the only mode this prototype supports — documented, not silently assumed |
| `EVAL_MODE` | `fast` | default evaluation mode if the evaluation runner is invoked |
| `LLM_PROVIDER` / `EVAL_LLM_PROVIDER` | unset (mock mode) | `anthropic` or `openai`, for `RealLLMProvider` and the evaluation layer |
| `LLM_MODEL` / `EVAL_MODEL` | unset (provider default) | model id |
| `ANTHROPIC_API_KEY` / `OPENAI_API_KEY` | unset | required only if a provider is set above |

Never commit a real `.env` — `.gitignore` already excludes it; only
`.env.example` (no real values) is tracked.

## 12. Deployment instructions

No live cloud deployment was performed — see
[`docs/deployment_validation_report.md`](deployment_validation_report.md) §5
for why (no usable cloud credentials in this execution environment; the
AWS keys present returned `InvalidClientTokenId` on a read-only
`sts:GetCallerIdentity` check). What follows is the prepared plan for
whoever has real account access.

**Recommended target: Render** (or Railway — equivalent fit), for a
single stateless container with no persistent storage need:

1. Push this repository (with `Dockerfile`) to GitHub.
2. Render → New → Web Service → connect the repo → Environment: Docker.
3. Set environment variables from §11 as needed (none are required for
   demo mode).
4. Deploy. Render builds the `Dockerfile` and exposes the container's
   `$PORT` — note `Dockerfile`/`context_layer/api/config.py` already
   read `PORT` from the environment, so Render's dynamic port
   assignment works without a code change.
5. No database, no volume, no external service — the graph is rebuilt
   from the synthetic fixtures at container start.

AWS App Runner and Azure Container Apps are also a reasonable fit (same
single-container, no-state shape); Render/Railway are recommended first
for a demo/pilot specifically because there's no infrastructure to
provision beyond "point it at the Dockerfile."

## 13. Post-deployment validation

Whoever deploys this should run, against the live URL:

```bash
BASE=https://<deployed-url>
curl -sf $BASE/health
curl -sf $BASE/ready
curl -sf $BASE/demo/compare/HCP-021 | python3 -c "import json,sys; d=json.load(sys.stdin); assert d['comparison']['status']=='PASS'; print('PASS')"
curl -s -o /dev/null -w "%{http_code}\n" -X POST $BASE/context -H "Content-Type: application/json" -d '{"agent_id":"hcp_engagement_agent","entity_id":"HCP-001","question":"x","purpose":"site_selection"}'
# ^ must print 422, not 200
```

This mirrors exactly what `.github/workflows/ci.yml`'s `docker` job
already runs against the containerized build on every push.

## Known limitations

Unchanged from [`docs/production_reference_architecture.md`](production_reference_architecture.md):
in-memory graph (no real graph database), TF-IDF (no real embeddings),
synthetic data only, no real source-system connectors, no secrets
manager (raw env vars), no tracing/metrics dashboard, the approval queue
(`agent_builder/approvals.py`) has no UI — a human calls `.approve()` in
code — no horizontal scaling story, and single-container/no-redundancy.
`RealLLMProvider` and the full RAGAS/DeepEval/LLM-Judge pipeline are
exercised only via mocking in this environment (no LLM credentials
available here to validate a live call).
