====================================================
LIFE SCIENCES ENTERPRISE CONTEXT LAYER
PILOT READINESS REPORT
====================================================

**DATE:** 2026-09-02

**COMMIT (this report is included in):** immediately following `1830eb9`
("Make the validated prototype demoable, containerized, and pilot-ready")
— see this commit's own hash in `git log` for the exact tree this report
describes.

**This report answers one question: is the prototype ready to *run* a
controlled pilot?** It does **not** claim the pilot has happened, does
**not** claim product-market fit, and does **not** claim pilot success —
the pilot has not happened yet. Those claims can only be made after
`docs/pilot_workflow.md` sessions actually run and
`docs/pilot_decision_framework.md` is applied to real results.

---

## 1. Executive summary

**CONTROLLED PILOT READY.**

Every prerequisite this report checks for is in place: the core
governance claim is validated (§3), the demo surface works end-to-end
(§4), the pilot's own plan/hypotheses/metrics/dataset/workflow/decision
framework exist and are internally consistent (§5–§9), and a final
regression pass is green (§10). One real gap was found while writing
this report (§11) — not a blocker, but a correction to an earlier
report's implicit assumption, stated plainly rather than left uncorrected.

---

## 2. What this prototype is (recap)

A policy-scoped Context API over a partitioned knowledge graph, proving
that the same HCP entity produces provably different, governed context
depending on which agent — and therefore which published purpose — is
asking. Full detail: `README.md`, `docs/design.md`.

---

## 3. What was validated before this pilot-readiness pass

Unchanged, re-confirmed in §10 rather than re-litigated here:

| Source | Finding |
|---|---|
| `docs/test_report.md` | Primary acceptance test PASS; bridge firewall holds under direct, indirect, and vector-search attack; purpose cannot be escalated at runtime (after one critical defect found and fixed); 100% lineage coverage; governance is a hard gate over answer-quality scoring in both directions tested |
| `docs/deployment_validation_report.md` | Demo HTTP API works; Docker build/run validated by sandbox-equivalent simulation and (per §11 below, with one correction) by CI configuration, not yet by an actual CI execution; no live cloud deployment (no usable credentials found) |

Neither document's findings were weakened or reopened by this pass — see
§10.

---

## 4. Demo / access readiness (Phase 7)

- `GET /` now serves a minimal landing page (plain HTML, no build step)
  linking to the primary demo, `/docs` (FastAPI's auto-generated Swagger
  UI — the "smallest possible interface," not a built frontend), and the
  two use-case demo endpoints. New regression test:
  `tests/test_http_api.py::test_landing_page_links_to_the_primary_demo_and_docs`.
- `scripts/run_pilot_scenarios.py` runs the pilot dataset (§7) live
  against the real Context Layer and prints actual-vs-expected for a
  human facilitator — exercised directly while building this report (all
  12 scenarios; adversarial and edge subsets shown below).

No new frontend was built — this matches the instruction to use the
smallest solution that makes the existing API usable in a pilot session.

---

## 5. Pilot execution plan (Phases 1, 2, 4)

`docs/pilot_execution_plan.md` reviews `docs/pilot_plan.md` against
everything built since, names five concrete gaps it and its sibling
documents close, restates scope (two use cases against one shared Context
Layer) and users unchanged from `pilot_plan.md`, and defines **4 falsifiable
hypotheses** (reuse, context relevance, governance trust, platform value),
each with an explicit "what would make this true" / "what would refute
it" pair — not just a restated goal.

---

## 6. Baseline (Phase 3)

`docs/pilot_baseline.md` — every number in it is a real, previously
measured value (test counts, lineage coverage, latency, CI/Docker status)
traced to its source document, or explicitly marked **TO BE MEASURED
DURING PILOT** where no real data exists yet. No estimated or fabricated
figures appear.

---

## 7. Metrics framework (Phase 5)

`docs/pilot_metrics.md` — product/quality/governance/operational, every
row tagged **[NOW]** (already measured — see §6) or **[PILOT]**
(genuinely requires real pilot usage). **No [PILOT] row carries a value**
— confirmed by direct inspection while writing this report.

---

## 8. Pilot evaluation dataset (Phase 6)

`evaluation/pilot_dataset/scenarios.json` — 12 scenarios (4 normal, 3
edge, 5 adversarial), each with `scenario_id`, `agent`, `bound_purpose`,
`entity_id`, `question`, `expected_allowed_domains`/`expected_forbidden_domains`,
`expected_context_characteristics` (descriptive, not a literal expected
answer), and `expected_policy_outcome`.

**Deliberately kept outside `context_layer/evaluation/`** (the runtime
evaluation package the automated runner and CI use) — nothing under
`context_layer/` imports it, and `scripts/run_pilot_scenarios.py` never
feeds the expected fields into the system under test, only prints them
next to real output for a human to judge. See
`evaluation/pilot_dataset/README.md` for the full rationale.

**Actually run against the live system while writing this report** (not
just written and assumed correct):

| Type | Result |
|---|---|
| 4 normal scenarios | All produced the expected allowed domains and characteristics |
| 3 edge scenarios | Unknown entity → clean `error_not_found`; irrelevant question text → valid package, empty content match, no error; no-investigator-record → valid package, zero clinical facts, correctly distinguishable from the unknown-entity case |
| 5 adversarial scenarios | Unregistered purpose → `deny_fail_closed` (direct policy-engine check); HTTP purpose-override → `reject_422_extra_field`; both cross-purpose question-phrasing attempts → scope unchanged, no leak; prompt-injection attempt → no MSL/medical fact leak (attacker's own text is echoed, per the known template behavior documented in `docs/test_report.md` §4, which is not a leak) |

All 12 matched their `expected_policy_outcome`.

---

## 9. Feedback, workflow, decision framework, roadmap (Phases 8–11)

- `docs/pilot_feedback_questions.md` — three stakeholder question sets
  (AI/platform, business, governance), each question mapped to one of
  the four hypotheses in §5.
- `docs/pilot_workflow.md` — a 9-step, ~30–60 minute session structure,
  explicitly stated as a range rather than a claimed exact duration.
- `docs/pilot_decision_framework.md` — GO / ITERATE / STOP-PIVOT criteria
  fixed *before* pilot results exist, read in listed order so a single
  governance STOP-PIVOT signal overrides any number of positive signals
  elsewhere (the same governance-gating philosophy already used in
  `context_layer/evaluation/scoring.py`).
- `docs/roadmap.md` — NOW (done) / NEXT (contingent on the pilot's
  GO/ITERATE/STOP-PIVOT outcome, not predetermined) / LATER (the full
  production migration, deferred). Explicitly does not commit to building
  `docs/production_reference_architecture.md`'s full list regardless of
  outcome.

---

## 10. Final regression check (Phase 12)

Re-run in full immediately before writing this report, from a clean
audit log and regenerated fixtures:

```
$ rm -f context_layer_audit.log
$ ./.venv/bin/python -m context_layer.data.synthetic_gen
$ ./.venv/bin/python -m pytest -v
```

| Total | Passed | Failed | Skipped |
|---|---|---|---|
| **119** | **119** | 0 | 0 |

(118 carried over from `docs/deployment_validation_report.md` + 1 new:
`test_landing_page_links_to_the_primary_demo_and_docs`.)

Governance-specific subset re-run in isolation (bridge firewall, primary
acceptance, privilege escalation, adversarial, governance gating):

```
$ ./.venv/bin/python -m pytest -v tests/test_bridge_firewall.py tests/test_primary_acceptance.py \
    tests/test_privilege_escalation.py tests/test_adversarial.py tests/evaluation/test_governance_gating.py
```

**18/18 passed.**

Deterministic evaluation runner:

```
$ ./.venv/bin/python -m context_layer.evaluation.runner --mode fast
```

**6/6 cases passed.**

**Checklist:**

- [x] Deterministic test suite green (119/119)
- [x] Governance regression subset green in isolation (18/18)
- [x] Deterministic evaluation runner green (6/6)
- [x] All pilot documents exist: `pilot_execution_plan.md`,
      `pilot_baseline.md`, `pilot_metrics.md`,
      `evaluation/pilot_dataset/{scenarios.json,README.md}`,
      `pilot_feedback_questions.md`, `pilot_workflow.md`,
      `pilot_decision_framework.md`, `roadmap.md`
- [x] No fake pilot results generated — `pilot_baseline.md` and
      `pilot_metrics.md` contain only real measured values or explicit
      "TO BE MEASURED DURING PILOT" placeholders; no [PILOT]-tagged
      metric carries a value
- [x] `README.md` updated to link every new document

---

## 11. Known gaps and risks

Unchanged from `docs/production_reference_architecture.md` and
`docs/deployment_validation_report.md` §8 (in-memory graph, TF-IDF, no
real connectors, no secrets manager, no observability stack, no approval
UI, single-container/no-redundancy), plus:

- **Correction to `docs/deployment_validation_report.md` §4:** that
  report said the new `docker` CI job's "result will be visible on the
  next CI run for this branch/PR." Checked directly against GitHub while
  writing this report: **PR #1 (the only PR ever opened for this branch)
  merged before the `docker` job was added, and no push or PR event has
  triggered CI since** — `ci.yml` only runs on `push` to `main` or a
  `pull_request` event, and this branch currently has neither. So the
  `docker` job exists in configuration and was written to run on a real
  daemon, but **has not yet actually executed anywhere**. Docker
  build/run remains validated only by the sandbox-equivalent venv
  simulation described in `docs/deployment_validation_report.md` §4, not
  by a real `docker build`/`docker run`. This does not block pilot
  readiness (the venv-equivalent validation covers the same steps the
  Dockerfile specifies, endpoint-by-endpoint), but a real CI run — via
  opening a fresh PR for this branch, or a manual `workflow_dispatch` —
  should happen before anyone relies on the containerized path for the
  pilot itself.
- **The pilot dataset's expected characteristics are prose, not an
  automated oracle.** `scripts/run_pilot_scenarios.py` deliberately
  requires a human to compare actual vs. expected — by design (§8), but
  it means dataset quality depends on the facilitator actually reading
  both sides carefully during a live session.
- **No pilot has run yet.** Every hypothesis in §5, and every [PILOT]
  metric in `docs/pilot_metrics.md`, is untested until
  `docs/pilot_workflow.md` sessions actually happen.

---

## 12. Recommendation

**CONTROLLED PILOT READY.**

The prototype's core governance claim is validated (§3), the demo and
scenario-runner surface actually work when exercised live (§4, §8), and
the pilot's own supporting documents (§5–§9) are complete, internally
consistent, and free of fabricated results (§10 checklist). The one gap
found while preparing this report (§11 — the CI `docker` job's real
first run is still pending) does not block running the pilot, since the
equivalent validation already covers the same ground; it should be
closed by opening a fresh PR (or a manual workflow dispatch) before or
during the pilot, not treated as a blocker to starting it.

**This is not a claim of product-market fit, and not a claim that the
pilot will succeed.** It is a claim that the prototype, its governance
model, and its supporting pilot materials are ready for real stakeholders
to actually test those two things — which is exactly what
`docs/pilot_decision_framework.md` exists to judge once they do.

**Recommended first pilot session:** a Governance session (§`docs/pilot_workflow.md`,
step 7 variant) — of the four hypotheses in §5, the governance trust
hypothesis is both the one this prototype's own test suite is least able
to substitute for (a self-written adversarial test is not independent
governance judgment) and the one whose refutation would most change
what NEXT looks like (`docs/roadmap.md`). Running it first means the
highest-leverage piece of pilot evidence comes back earliest.

**What this pilot will decide, concretely:** whether to proceed toward
targeted production hardening (GO), fix specific named gaps and
re-validate narrowly (ITERATE), or take the architecture back to
redesign on a specific, named point before any further hardening
(STOP-PIVOT) — per `docs/pilot_decision_framework.md`. No infrastructure
investment beyond what's already built should happen until one of those
three calls is actually made.
