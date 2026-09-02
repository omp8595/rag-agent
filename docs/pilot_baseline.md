# Pilot Baseline

Current-state measurements only. **Every number below was actually
measured** (test run, live script, or committed evaluation report) —
none is estimated or assumed. Where real pilot data doesn't exist yet,
this document says so explicitly rather than filling the gap with a
plausible-sounding figure.

Do not read this as "the system's performance" in any general sense — it
is single-developer, synthetic-data, prototype-scale evidence, gathered
during the validation and deployment passes documented in
[`docs/test_report.md`](test_report.md) and
[`docs/deployment_validation_report.md`](deployment_validation_report.md).
It exists so the pilot has something to compare *against*, not to claim
those numbers will hold at real scale.

---

## Product — measured now

| Metric | Value | Source |
|---|---|---|
| Purposes defined in the policy engine | 3 (`commercial_engagement`, `medical_inquiry`, `site_selection`) | `context_layer/policy/engine.py::PURPOSE_POLICIES` |
| Agents actually published | 2 (`hcp_engagement_agent`, `site_selection_agent`) | `agents/*.yaml` |
| Purposes policy-defined but with no published agent yet | 1 (`medical_inquiry`) | same |
| Lines of core-layer code changed to add the 2nd agent after the 1st existed | 0 (a new `agents/*.yaml` file only) | repo history — no `graph/`, `policy/`, or `retrieval/` commit was required between the two agents' publication |

**TO BE MEASURED DURING PILOT:** time for someone who did not build this
codebase to go from "we have a purpose" to a working, published agent
config; real Context API adoption (calls through `/context` or the MCP
server vs. stakeholders falling back to ad hoc retrieval); whether a 3rd
agent (`medical_inquiry`) gets onboarded live during the pilot.

---

## Quality — measured now

| Metric | Value | Source |
|---|---|---|
| Fact lineage coverage | 100% (54/54 facts, 15-HCP sample, `commercial_engagement`) | `docs/test_report.md` §5, `context_layer/evaluation/lineage_evaluator.py` |
| Primary acceptance test (same HCP, two purposes, two non-overlapping Context Packages) | PASS | `tests/test_primary_acceptance.py`, `docs/test_report.md` §3 |
| Response grounding mechanism exists and is exercised | Yes — `context_layer/llm/grounding.py`, tested against the mock provider | `tests/` (grounding tests) |
| RAGAS / DeepEval / LLM-as-judge run against a real model | **Not yet run automatically** — no LLM API key has been available in any build/test environment used so far | `docs/test_report.md` §6 |
| One real LLM-judge pass performed manually (by the assistant, against the identical rubric, since no automated key was available) | 1 pass, on 6 cases, all judged compliant | `evaluation_reports/manual_llm_judge_pass.json` |

**TO BE MEASURED DURING PILOT:** RAGAS/DeepEval/LLM-judge scores from an
actual configured provider key, on real stakeholder questions (not just
the 6 built-in evaluation cases); human-perceived relevance/usefulness
ratings (`docs/pilot_feedback_questions.md`).

---

## Governance — measured now

| Metric | Value | Source |
|---|---|---|
| Policy violations across the full test suite (118 tests, including deliberate adversarial attempts: graph path attack, vector leakage, prompt injection, purpose escalation) | 0 | `docs/test_report.md` §4 |
| Unauthorized bridge traversals (every whitelisted bridge granted, still checked) | 0 | `docs/test_report.md` §4, `tests/test_bridge_firewall.py` |
| Runtime purpose-escalation attempts blocked | Yes — after one real defect found and fixed during this validation program (see `docs/test_report.md` §4 Critical Defect #1) | `tests/test_privilege_escalation.py` (5/5 passing) |
| Governance treated as a hard gate over answer-quality scoring, not one weighted term | Confirmed in both directions (judge agrees with a violation, judge misses it) | `tests/evaluation/test_governance_gating.py`, `docs/test_report.md` §6 |

**This is adversarial and unit-test evidence, not organic-usage
evidence** — these numbers prove the mechanism holds under deliberate
attack, written by the people who built it. They are not a substitute for
§4.3 of `docs/pilot_execution_plan.md` (the governance trust hypothesis),
which specifically requires an independent governance stakeholder's
judgment and organic pilot usage.

**TO BE MEASURED DURING PILOT:** policy/bridge violation count under
organic (non-adversarial) pilot usage (target: zero, and any non-zero
count is a stop-and-investigate event per `docs/pilot_plan.md`);
governance stakeholder's direct assessment of whether the bridge
whitelist and purpose table reflect real compliance rules.

---

## Operational — measured now

| Metric | Value | Source |
|---|---|---|
| Full context assembly, mean (single warm process, n=200, 50-HCP synthetic graph) | 2.158 ms | `docs/test_report.md` §7 |
| End-to-end incl. mock LLM, mean (n=50) | 2.030 ms | `docs/test_report.md` §7 |
| Cold graph build (50 HCPs, 10 institutions, etc.) | 2.70 ms | `docs/test_report.md` §7 |
| Docker container build+run+health-check | PASS, validated via CI on a GitHub-hosted runner (real Docker daemon) | `.github/workflows/ci.yml` `docker` job, `docs/deployment_validation_report.md` §4 |
| Live cloud deployment | **Not performed** — no usable cloud credentials found in the build environment (a read-only AWS `sts:GetCallerIdentity` check returned `InvalidClientTokenId`) | `docs/deployment_validation_report.md` §5 |

These performance numbers are in-memory, single-process, prototype-scale
(networkx graph, TF-IDF retrieval) — explicitly **not** predictive of
production latency behind a real graph database, real embeddings, or
concurrent multi-user load. Treat them only as "this is not the
bottleneck at prototype scale," nothing more.

**TO BE MEASURED DURING PILOT:** real latency under whatever
infrastructure the pilot actually runs on; error rate; availability over
the pilot window; latency under concurrent stakeholder sessions (this
baseline is single-request, sequential).

---

## Summary

Everything measurable without real users has been measured, honestly,
and is either a real number or an explicit "TO BE MEASURED DURING PILOT."
No product, quality, governance, or operational metric below the
"measured now" tables in this document was fabricated or estimated.
