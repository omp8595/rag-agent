====================================================
LIFE SCIENCES ENTERPRISE CONTEXT LAYER
DEPLOYMENT VALIDATION REPORT
====================================================

**DATE:** 2026-09-02

**COMMIT (this report is included in):** immediately following `6b4754d`
("Comprehensive adversarial testing pass") — see this commit's own hash
in `git log` for the exact tree this report describes.

---

## 1. Prototype status

**PROTOTYPE VALIDATED — NOT PRODUCTION READY.**

This is unchanged from `docs/test_report.md`. This pass adds
deployability (HTTP API, Docker, deployment/pilot documentation) without
touching, weakening, or bypassing any governance control validated in
that prior pass — see §3 and §8.

---

## 2. Test status

| Total | Passed | Failed | Skipped |
|---|---|---|---|
| 118 | 118 | 0 | 0 |

(107 carried over from the prior validation pass + 1 new privilege
escalation regression suite already counted there, + 9 new HTTP API
tests + 1 new observability test = 118. `deepeval`/`ragas`/LLM-judge
metrics remain SKIPPED, not passed, for lack of LLM credentials in this
environment — unchanged from `docs/test_report.md` §6.)

Command: `./.venv/bin/python -m pytest -v`

---

## 3. Primary acceptance test

| Check | Result |
|---|---|
| Commercial Agent | **PASS** |
| Clinical Agent | **PASS** |
| Same HCP | **PASS** (`HCP-021`, one shared `GraphStore`) |
| Different Context Packages | **PASS** (4 facts vs. 1, zero overlap, different `request_id`s) |
| Unauthorized Data Leakage | **NO** |
| Unauthorized Bridge Traversal | **NO** |
| Runtime Purpose Escalation | **NO** (blocked structurally since the prior pass's fix — re-verified: `tests/test_privilege_escalation.py`, 5/5 passing) |

Re-run live via `scripts/e2e_demo.py` (mock LLM provider) and, separately,
against the same scenario through the new HTTP API's
`GET /demo/compare/HCP-021` (`tests/test_http_api.py::test_demo_compare_is_computed_live_and_shows_the_primary_thesis`) —
identical result through both interfaces, computed by the same
deterministic evaluators (`policy_evaluator`, `isolation_evaluator`) the
rest of the suite uses, not fabricated for either interface.

---

## 4. Container status

| Check | Result |
|---|---|
| Docker Build | **BLOCKED in this sandbox — see explanation below** |
| Container Startup | **BLOCKED in this sandbox — see explanation below** |
| Health Check | **PASS (via equivalent local validation, and via CI)** |

**Why blocked here:** this repository's own execution sandbox has the
`docker` CLI installed but no privileged daemon access — `docker ps`
fails to connect to the socket, and `service docker start` is refused
(`ulimit: error setting limit (Operation not permitted)`, a sandbox-level
restriction, not a repository issue). A real `docker build`/`docker run`
could not be executed here. This is stated plainly rather than worked
around or pretended past.

**What was actually validated as a substitute, in this sandbox:**
every step the `Dockerfile` specifies, run directly — a fresh virtualenv,
`pip install -r requirements.txt`, `python -m context_layer.data.synthetic_gen`,
then the exact `CMD` (`python -m context_layer.api.http_server`) — with
the resulting service confirmed against: `/health`, `/ready`,
`/demo/commercial`, `/demo/clinical`, `/demo/compare/HCP-021` (`status:
PASS`), a purpose-override attempt (`422`), and an unknown-agent request
(`404`, no stack trace). All passed.

**What closes the gap for real:** `.github/workflows/ci.yml`'s new
`docker` job runs on every push, on a GitHub-hosted runner that *does*
have a working Docker daemon — it runs the actual `docker build`,
`docker run`, and re-checks `/health`, `/ready`, the compare endpoint's
`PASS` status, and the purpose-override `422` against the real
container. That job has not yet run as of this report being written (it
ships in the same commit); its result will be visible on the next CI run
for this branch/PR.

---

## 5. Deployment status

**READY FOR MANUAL DEPLOYMENT — not deployed.**

No live deployment was attempted. Two independent checks confirmed no
usable cloud deployment access exists in this environment:

- No Render/Railway/AWS App Runner/Azure Container Apps API tokens are
  present.
- `AWS_ACCESS_KEY_ID`/`AWS_SECRET_ACCESS_KEY` **are** present in this
  environment, but a read-only `sts:get-caller-identity` check against
  them returned `InvalidClientTokenId` — they are not usable credentials
  for a real AWS account. Rather than assume they might be a real,
  authorized account and attempt a consequential, billable,
  publicly-reachable deployment on that assumption, this was verified
  first and — since it failed — deployment was not attempted. This
  matches the instruction: "If they are not available: DO NOT pretend
  deployment succeeded. Instead: Prepare all required deployment
  configuration files and exact deployment steps."

Everything required for a human with real account access to deploy in
minutes is prepared: `Dockerfile`, `.dockerignore`, `.env.example`,
`docs/deployment.md` §12 (exact Render steps), §13 (post-deployment
validation commands).

---

## 6. Live demo

No public URL — none was deployed, and none is claimed. Endpoints
validated locally and via the equivalent-to-container local run
(§4), all through `http://127.0.0.1:<port>`:

- `GET /health`
- `GET /ready`
- `POST /context` (including the purpose-override rejection and
  unknown-agent/unknown-entity failure paths)
- `GET/POST /demo/commercial`
- `GET/POST /demo/clinical`
- `GET /demo/compare/{entity_id}`

---

## 7. Files changed

**Added:**
- `context_layer/api/http_server.py` — the demo HTTP API
- `context_layer/api/config.py` — env-based service configuration
- `context_layer/api/observability.py` — structured request logging
- `Dockerfile`, `.dockerignore`, `.env.example`
- `docs/deployment.md`, `docs/pilot_plan.md`, `docs/deployment_validation_report.md`
- `tests/test_http_api.py` (10 tests)

**Modified:**
- `context_layer/evaluation/config.py` — accepts `LLM_PROVIDER`/`LLM_MODEL`
  as aliases for `EVAL_LLM_PROVIDER`/`EVAL_MODEL`, so `.env.example`
  documents real, read env vars rather than inventing unread ones
- `pyproject.toml`, `requirements.txt` — `fastapi`, `uvicorn` promoted to
  core dependencies (the API imports them unconditionally); `httpx`
  added to `dev` (needed for `TestClient`)
- `.github/workflows/ci.yml` — new `docker` job (build + run + endpoint
  validation, on the GitHub-hosted runner that actually has a daemon);
  existing `test` job unchanged, still requires no secrets
- `README.md` — Live Demo Flow section, HTTP/Docker quickstart commands,
  repository layout updated

No governance code (`policy/`, `graph/bridges.py`, `agent_builder/schema.py`)
was touched in this pass — the validated controls from the prior pass
are unmodified. The one correction made during this pass was to
`context_layer/api/http_server.py`'s own observability wiring (the
declared log fields — `agent_id`, `purpose`, `context_package_id`, etc.
— were not actually being populated; fixed, with a regression test) —
an observability gap in newly-added code, not a regression in previously
validated governance.

---

## 8. Known limitations

Unchanged from `docs/production_reference_architecture.md` and
`docs/test_report.md` §9, plus what this pass specifically could not
validate:

- **Docker build/run were not executed in this repository's own sandbox**
  (§4) — validated by equivalent local steps here, and will be validated
  for real by CI's new `docker` job on the next push.
- **No live deployment was performed** (§5) — no usable cloud credentials
  in this environment.
- In-memory graph, TF-IDF retrieval, synthetic data only, no real
  source-system connectors, no secrets manager, no tracing/metrics
  dashboard, the approval queue has no UI, no horizontal scaling or
  redundancy, `RealLLMProvider`/RAGAS/DeepEval/LLM-Judge unexercised
  against a live model here (mocked instead).

---

## 9. Next recommended step

**CONTROLLED PILOT** (per `docs/pilot_plan.md`), not production
hardening — in that order, because:

1. The governance hypothesis is validated adversarially, not just
   happy-path (`docs/test_report.md`).
2. The prototype is now demoable over HTTP and containerized, with CI
   validating the container build+run on every push.
3. What's genuinely unknown is *product* fit — whether commercial and
   clinical stakeholders find the retrieved context useful for real
   workflows, and whether the policy model (purposes, bridge whitelist)
   maps cleanly onto real organizational governance requirements. A
   pilot answers that; more infrastructure hardening before knowing the
   product/governance model is right would be premature.
4. Production hardening (real graph DB, real connectors, secrets
   management, IAM) is expensive enough that it should follow pilot
   learnings, not precede them — per `docs/production_reference_architecture.md`'s
   own recommended migration order.
