# Pilot Metrics

Four categories, matching `docs/pilot_plan.md`'s success-metric
categories. Each metric is tagged **[NOW]** — already measurable, and
measured, without real pilot users (see `docs/pilot_baseline.md` for the
actual current values) — or **[PILOT]** — genuinely requires real pilot
usage to produce a number. **No [PILOT] metric has a value in this
document.** Filling one in before the pilot happens would be fabrication;
this document exists specifically to make that distinction impossible to
blur later.

---

## Product

| Metric | Tag | Definition | Target |
|---|---|---|---|
| Agents onboarded | NOW + PILOT | Count of published `agents/*.yaml` configs actively used | ≥2 now (measured); stretch 3 during pilot (`medical_inquiry`) |
| Core-layer code changes required per new agent | NOW | Commits to `graph/`, `policy/`, `retrieval/` needed to add an agent beyond the first | 0 (measured — see `docs/pilot_baseline.md`) |
| Time to onboard a new agent, by someone who did not build the codebase | PILOT | Wall-clock time from "we have a purpose" to a published, working agent config, timed live during a pilot session | Directional only — no target set in advance; this is discovery, not a pass/fail gate |
| Context API adoption | PILOT | Real `/context` or MCP-server calls made by pilot stakeholders vs. reported ad hoc workarounds | Directional — evidence for or against the platform-value hypothesis (§4.4, `pilot_execution_plan.md`) |

---

## Quality

| Metric | Tag | Definition | Target |
|---|---|---|---|
| Fact lineage coverage | NOW | % of returned facts with a resolvable `fact_id`/`source_type`/`source_id`/`domain`/`retrieval_method` | 100% (measured — `docs/pilot_baseline.md`) |
| Primary acceptance scenario | NOW | Same entity, two purposes, non-overlapping, policy-compliant Context Packages | PASS (measured) |
| RAGAS (context precision/recall, faithfulness, answer relevancy) | PILOT | Run against real pilot questions with a configured provider key | No target set in advance — first real data point for this framework |
| DeepEval (RAG Triad + contextual precision/recall) | PILOT | Same, DeepEval framework | No target set in advance |
| LLM-as-judge (correctness/relevance/faithfulness/policy_compliance/hallucination_risk) | PILOT | Structured rubric run against real pilot Q&A | No target set in advance — one manual pass exists (`evaluation_reports/manual_llm_judge_pass.json`), not a corpus |
| Human-perceived relevance | PILOT | Stakeholder rating from `docs/pilot_feedback_questions.md` | Evidence for/against the context-relevance hypothesis (§4.2) |

---

## Governance

| Metric | Tag | Definition | Target |
|---|---|---|---|
| Policy violations (adversarial + unit tests) | NOW | Deliberate attack attempts against the policy/bridge model, in the existing test suite | 0 (measured — `docs/pilot_baseline.md`) |
| Unauthorized bridge traversals (adversarial + unit tests) | NOW | Same, bridge-specific | 0 (measured) |
| Policy violations under organic pilot usage | PILOT | Any policy or bridge violation during real, non-adversarial pilot sessions | 0 — **any non-zero count is a stop-and-investigate event, not a metric to trend down over time** (per `docs/pilot_plan.md`) |
| Governance stakeholder trust assessment | PILOT | Direct qualitative judgment: does the purpose/bridge model reflect real compliance rules? | Evidence for/against the governance-trust hypothesis (§4.3) |
| Audit completeness | NOW | Every Context Package logged with request, applied scope, and fact lineage | Confirmed structurally (`policy/audit.py`, `tests/test_context_package_envelope.py`) — measured |

---

## Operational

| Metric | Tag | Definition | Target |
|---|---|---|---|
| Context assembly latency, prototype scale | NOW | Mean full context-assembly time, single warm process, 50-HCP synthetic graph, n=200 | 2.158 ms measured — see caveats in `docs/pilot_baseline.md`; not a production prediction |
| Container build/run/health-check | NOW | Docker build + run + endpoint validation, on a real daemon (CI) | PASS (measured) |
| Real latency under pilot infrastructure | PILOT | Wherever the pilot actually runs (local, a shared server, a deployed container) | No baseline exists at real-infra scale — first measurement |
| Error rate during the pilot window | PILOT | Non-2xx/5xx responses, unhandled exceptions surfaced to a client | Target: 0 unhandled exceptions reaching a client (matches the existing "no stack traces to clients" design property, `tests/test_http_api.py`) — new during pilot is whether *real* traffic patterns trigger any |
| Availability during the pilot window | PILOT | Uptime of whatever instance the pilot uses | No target set in advance — this is a single-container prototype with no redundancy story (`docs/production_reference_architecture.md`), so availability data here is informative, not a production SLA measurement |

---

## How this feeds the decision

Every **[PILOT]** row in this document is exactly what
`docs/pilot_workflow.md` sessions are designed to produce, and exactly
what `docs/pilot_decision_framework.md` weighs against the four
hypotheses in `docs/pilot_execution_plan.md` §4 to reach a GO / ITERATE /
STOP-PIVOT call. **No [PILOT] metric is treated as passing or failing
until it has a real measured value.**
