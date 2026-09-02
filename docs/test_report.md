====================================================
LIFE SCIENCES ENTERPRISE CONTEXT LAYER
COMPREHENSIVE TEST REPORT
====================================================

**DATE:** 2026-09-02

**COMMIT (baseline tested against):** `c21dd6d` — this report, and the
fixes it describes, are included in the commit that follows it.

---

## 1. Baseline

```
$ ./.venv/bin/python -m context_layer.data.synthetic_gen
$ ./.venv/bin/python -m pytest -v
```

| Tests Run | Passed | Failed | Skipped | Errors |
|---|---|---|---|---|
| 87 | 87 | 0 | 0 | 0 |

`scripts/demo.py`, `scripts/campaign_workflow.py`, `scripts/e2e_demo.py`,
and `python -m context_layer.evaluation.runner --mode fast` all exited 0.

Baseline was already green — this pass did not start from a broken state.
Testing continued into adversarial and edge-case territory beyond what
the existing 87 tests covered, per the assignment's Phase 5 explicitly
telling me to "attempt to break the architecture."

---

## 2. Core component testing

| Component | Result | Evidence |
|---|---|---|
| Policy Engine | **PASS** | `tests/test_policy_engine.py`, `tests/evaluation/test_policy_evaluator.py` — fail-closed on unknown purpose and wrong role, `task` text proven not to affect scope |
| Agent Builder | **PASS after fix** | `tests/test_agent_builder.py` + new `tests/test_privilege_escalation.py` — see Critical Defect #1 below |
| Graph Partitioning | **PASS** | `tests/test_bridge_firewall.py`, `tests/evaluation/test_graph_evaluator.py`, new `tests/test_adversarial.py::test_graph_path_attack_via_shared_institution_node` |
| Bridge Firewall | **PASS** | Every forbidden crossing (Commercial→Medical, Commercial→Clinical) independently re-verified unreachable — see §4 |
| Entity Retrieval | **PASS** | `tests/test_edge_cases.py::test_unknown_entity_raises_a_clear_error` and redaction tests in `tests/test_context_package_isolation.py` |
| Vector Retrieval | **PASS** | New `tests/test_adversarial.py::test_vector_retrieval_never_searches_a_forbidden_domain_index`, `tests/test_edge_cases.py` (empty index, no-match query) |
| Context Assembly | **PASS** | New `tests/test_context_package_envelope.py` — the full envelope (`agent`, `policy_decision`, `lineage`, `governance`, `audit`) validates against its own pydantic schema on real packages |

---

## 3. Primary product acceptance test

Executed live, independently re-verified from raw Context Package dicts
(not by trusting any script's own printed "PASS"), and formalized as
`tests/test_primary_acceptance.py`.

**Scenario:** `HCP-021` (an active clinical investigator — the entity
where all three domains and both bridges actually have something to show
or withhold), same underlying `GraphStore`, two agents:

- **Test A** — HCP Engagement Agent, `commercial_engagement`: *"What
  context should I consider for the next approved engagement with this
  HCP?"*
- **Test B** — Clinical Site Selection Agent, `site_selection`: *"What
  context is available to assess this HCP and institution for clinical
  site selection?"*

| Check | Result |
|---|---|
| Same Entity | ✅ YES |
| Same Base Data | ✅ YES (one shared `GraphStore` instance) |
| Different Agent | ✅ YES |
| Different Purpose | ✅ YES |
| Different Policy Decision | ✅ YES |
| Different Allowed Domains | ✅ YES (`[commercial]` vs `[clinical]`) |
| Different Retrieved Facts | ✅ YES (4 facts vs 1, zero overlap) |
| Different Context Package | ✅ YES |
| Commercial facts in Clinical package | **0 / 1** |
| Clinical facts in Commercial package | **0 / 4** |
| Unauthorized bridge traversal | **0 / 4** and **0 / 1** (independently re-validated against the live `BRIDGE_WHITELIST`, not just trusted from a prior evaluator) |

**RESULT: PASS.**

Commercial Agent facts (4): 2 commercial `ENGAGED_WITH` facts, 2 medical
`AUTHORED` facts legitimately bridged via `medical.publications->commercial`.
The investigator's clinical status appears only as a compliance
`constraint` string, never as a domain fact. Clinical Agent facts (1):
the PI/enrollment/feasibility detail, zero bridges applied, zero
commercial facts.

---

## 4. Security testing

| Test | Result |
|---|---|
| Unknown Purpose (fail-closed) | **PASS** — `PolicyDenied` raised, never an empty-but-present scope |
| Purpose Escalation | **PASS — after a real fix** (see Critical Defect #1) |
| Forbidden Domain Access (both directions, via adversarial question phrasing) | **PASS** — `tests/evaluation/datasets.py`'s two security cases + `tests/test_adversarial.py` |
| Graph Path Attack (HCP →[spine, allowed]→ Institution →[clinical]→ Study) | **PASS** — the shared, always-visible institution node does not open a side door; the `SITE_OF` edge is rejected on its own domain check regardless of the path that reached it |
| Vector Retrieval Leakage (medical-vocabulary query under a commercial purpose) | **PASS** — `recommended_content` only ever contains `Content` nodes from the commercial index, never `Publication` nodes |
| Prompt Injection Resistance | **PASS — after a test correction** (see Non-Critical Finding below) |

### Critical Defect #1 (found and fixed): `AgentConfig` was mutable

**Severity: Critical.** `context_layer/agent_builder/schema.py`'s
`AgentConfig` was a plain, unfrozen pydantic `BaseModel` with `list[str]`
fields. The code's own comment said `purpose` was "bound at publish time,
never a runtime parameter" — but nothing enforced that. Proof of exploit,
run against the pre-fix code:

```python
hcp_agent.config.purpose = "site_selection"
hcp_agent.config.audience_roles = ["clinical_ops"]
pkg = hcp_agent.get_context("HCP-001", "give me clinical data")
# pkg["purpose"] == "site_selection"
# pkg["policy_decision"]["allowed_domains"] == ["clinical"]
```

Any caller holding a `ThinAgent` reference — which is every caller, since
nothing wraps or hides it — could silently re-scope the agent to any
purpose and role it wanted, with no exception, no log entry, no trace.
This directly broke the architecture's central claim.

**Fix:** `AgentConfig` and `Guardrails` are now `model_config =
ConfigDict(frozen=True)`, and every security-relevant field changed from
`list[str]` to `tuple[str, ...]`. `frozen=True` alone blocks attribute
*reassignment*; it does **not** block in-place mutation of a still-mutable
list field (`.append()` still works on a frozen model's list attribute) —
which is why the type change was necessary too, not just the freeze.
Verified both vectors are closed:

```python
hcp_agent.config.purpose = "site_selection"          # -> pydantic.ValidationError
hcp_agent.config.audience_roles.append("clinical_ops") # -> AttributeError (tuple has no append)
```

Regression coverage: `tests/test_privilege_escalation.py` (5 tests).

### Non-critical finding: an adversarial test's own assertion was wrong

`tests/test_adversarial.py`'s prompt-injection test initially asserted
`"MSL" not in answer`. It failed — investigated, and the failure was in
the test, not the product: `synthesize_answer`'s template echoes the raw
question at the top of every response (`Regarding "{question}" — ...`),
so injecting text containing the word "MSL" makes it appear in the
answer purely as a quotation of the attacker's own input, plus a second,
legitimate appearance in the honest `excluded` notice ("medical (MSL
interactions not permitted...)"). Neither is a data leak. Fixed the
assertion to check for the actual leak signal (a real MSL claim template,
`"Medical inquiry interaction ..."`, or a real study protocol id) instead
of a substring that trivially matches attacker-supplied text. No product
code changed for this one.

---

## 5. Lineage

Computed by `context_layer/evaluation/lineage_evaluator.py` over a
15-HCP sample under `commercial_engagement`:

| | |
|---|---|
| Total Facts | 54 |
| Facts With Lineage | 54 |
| Orphan Facts | 0 |
| Lineage Coverage | **100%** |

Every fact in every sampled package resolves to a `fact_id`, a
`source_type` (CRM/PubMed/CTMS/Medical Information System), a
`source_id` (the actual graph node id it came from), a `domain`, and a
`retrieval_method` (`graph_traversal` or `bridge_traversal`) — validated
structurally against `ContextPackage`'s pydantic schema
(`tests/test_context_package_envelope.py`), not just spot-checked.

---

## 6. AI evaluation framework

Ran `python -m context_layer.evaluation.runner --mode full` in this
sandbox, which has no `ANTHROPIC_API_KEY`/`OPENAI_API_KEY` configured.

| Framework | Result |
|---|---|
| RAGAS | **SKIPPED** — `ragas` fails to import in this environment (upstream packaging bug: `ragas==0.4.3`'s `ragas.llms.base` unconditionally imports `langchain_community.chat_models.vertexai`, which doesn't exist in any `langchain-community` compatible with the rest of the resolvable `langchain` 1.x line — documented in `docs/evaluation.md`, reproduced by `tests/evaluation/test_ragas_adapter.py`) |
| DeepEval | **SKIPPED** — no LLM credentials configured (adapter itself verified working: `tests/evaluation/test_deepeval_adapter.py` constructs real metric objects and confirms no-key skip + malformed-response resilience) |
| LLM-as-Judge | **SKIPPED** — no LLM credentials; parsing/gating logic verified with a mocked model response (`tests/evaluation/test_llm_judge_schema.py`) |
| Deterministic Governance | **PASS** — 6/6 evaluation cases, all deterministic checks green (`policy_evaluator`, `graph_evaluator`, `lineage_evaluator`) |

No skipped metric is reported or counted as passed anywhere in the
report JSON or the unified score — `evaluation_reports/latest.json`
records each as `"skipped": true` with an explicit `"skip_reason"`.
`evaluation_reports/manual_llm_judge_pass.json` remains the one real
judged pass performed (by Claude, directly, using the identical rubric)
since no automated LLM credentials exist here.

### Governance gating — explicitly tested (Phase 11)

New `tests/evaluation/test_governance_gating.py`, four scenarios, all
passing:

1. Excellent RAGAS + DeepEval + LLM Judge scores, clean governance →
   `PASS`, `unified_score = 100.0` (sanity check that the harness can
   pass at all).
2. Excellent RAGAS + DeepEval + LLM Judge scores, **unauthorized domain
   accessed** (the LLM judge itself missed it) → **`FAIL`**.
3. Perfect answer quality, **unauthorized bridge traversed** → **`FAIL`**.
4. Excellent RAGAS + DeepEval, LLM judge sets its own
   `critical_violation = true` → **`FAIL`** (the judge's flag is honored,
   not averaged away).

Governance is confirmed to be a gate, not one term in a weighted
average, in both the "judge agrees" and "judge disagrees" cases.

---

## 7. Performance (baseline, single warm process, n=200 unless noted)

| Stage | Mean | Median | Max |
|---|---|---|---|
| Policy evaluation | 0.005 ms | 0.003 ms | 0.04 ms |
| Entity lookup (raw node) | 0.001 ms | 0.001 ms | 0.08 ms |
| Entity profile lookup | 0.011 ms | 0.008 ms | 0.11 ms |
| Graph traversal (bounded) | 0.053 ms | 0.041 ms | 0.14 ms |
| Vector retrieval (TF-IDF) | 1.635 ms | 1.622 ms | 2.75 ms |
| **Full context assembly** | **2.158 ms** | 2.124 ms | 3.61 ms |
| End-to-end (mock LLM, n=50) | 2.030 ms | 1.980 ms | 3.36 ms |
| Cold graph build (50 HCPs, 10 institutions, etc.) | 2.70 ms | — | — |

TF-IDF vector search dominates the cost and is still sub-2ms at this
scale. No performance concerns at prototype scale; these numbers do not
extrapolate to a production graph database or a real embedding index —
see `docs/production_reference_architecture.md`.

**Edge cases** (`tests/test_edge_cases.py`, 7 tests, all PASS): unknown
entity → clear `ValueError`; empty/non-matching task → empty
`recommended_content`, no error; empty (clinical) vector index → `[]`,
no error; invalid agent config → `AgentValidationError` at publish time;
a malformed evaluation case (nonexistent entity) → isolated to that one
case's `.error` field, the rest of the run completes normally;
`PolicyDenied` is a distinct exception type, not a bare `ValueError`.

---

## 8. Critical defects

| # | Defect | Severity | Status |
|---|---|---|---|
| 1 | `AgentConfig`/`Guardrails` were mutable pydantic models — a `ThinAgent`'s bound purpose, roles, and guardrails could be reassigned after publication with no exception, fully escalating privilege | **Critical** | **Fixed** (`frozen=True` + `tuple[str, ...]` fields) |

No other critical defects found. One non-critical test-assertion error
was found and corrected (§4).

---

## 9. Final verdict

**PRODUCTION STATUS: PROTOTYPE VALIDATED — NOT PRODUCTION READY.**

### Functionally validated as a prototype

- The core product promise — same entity, different purpose, different
  policy-compliant, non-leaking Context Package — is proven true by a
  live, independently-verified run, not just by unit tests passing in
  isolation (§3).
- The bridge firewall holds under direct traversal, indirect
  multi-hop path attempts, and vector-search attempts to route around it
  (§4).
- Purpose cannot be escalated at runtime — this was **not** true before
  this testing pass found and fixed it (§4, Critical Defect #1).
- Fact lineage is 100% for every sampled package, structurally validated
  against a schema, not spot-checked (§5).
- Governance is a genuine hard gate over answer-quality scoring in both
  directions tested (§6).
- 108 tests passing (87 baseline + 21 added by this validation pass), 0
  failing, 0 skipped in the deterministic suite; CI runs all of it with
  no API keys.

### NOT production-ready

Per `docs/production_reference_architecture.md`, unchanged by this
pass: in-memory graph (no real graph database), TF-IDF (no real
embeddings), synthetic data only, no real connectors, no secrets
management, no observability/tracing, no human-governance UI for the
approval queue, no horizontal scaling story, `RealLLMProvider` and the
full RAGAS/DeepEval/LLM-Judge pipeline are unexercised against a live
model in this environment (no credentials here — code paths are tested
via mocking, not a real call). None of this was in scope to build during
a testing pass, and none of it should be inferred as done from the fact
that the prototype's own claims about itself now hold up under adversarial
testing.
