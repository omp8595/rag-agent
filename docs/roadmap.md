# Roadmap

**NOW / NEXT / LATER**, prioritized by evidence, not by "everything in
`docs/production_reference_architecture.md` eventually needs building so
start now." The explicit instruction driving this ordering: *do not
assume all production architecture features must be built immediately —
prioritize based on evidence.* As of this document, the missing evidence
is product fit (`docs/pilot_execution_plan.md`), not infrastructure — so
NEXT is evidence-contingent, not a fixed backlog.

---

## NOW

What's needed *right now*, already done:

- A validated prototype (`docs/test_report.md`) — the core governance
  claim holds under adversarial testing, including one critical defect
  found and fixed.
- A demoable, containerized interface (`docs/deployment_validation_report.md`)
  — HTTP API, Docker, CI-validated container build.
- A pilot-ready plan (`docs/pilot_execution_plan.md` and its siblings) —
  hypotheses, baseline, metrics, a runnable scenario dataset, a session
  workflow, and a decision framework.

There is no further NOW-priority engineering work before running the
pilot — see `docs/pilot_readiness_report.md` for the actual go/no-go on
running it.

---

## NEXT — contingent on pilot evidence, not predetermined

This section intentionally does **not** commit to a fixed list. What
belongs here depends on the pilot's GO / ITERATE / STOP-PIVOT outcome
(`docs/pilot_decision_framework.md`):

- **If GO:** begin *targeted* production hardening on exactly the gaps
  the pilot surfaced, following
  `docs/production_reference_architecture.md`'s own recommended migration
  order (graph store first, then policy engine — the two things
  everything else is written against a stable contract for). Do not treat
  a GO as license to build every row of that document's table at once.
- **If ITERATE:** fix the specific, named gaps the pilot found (a
  retrieval-quality gap, an API ergonomics issue, a narrower/wider bridge
  needed) and re-validate just those, per
  `docs/pilot_decision_framework.md`'s ITERATE section — not a rebuild.
- **If STOP-PIVOT:** the next step is redesign of the specific thing the
  pilot refuted (e.g., the purpose-binding model, if a real compliance
  requirement needs runtime purpose negotiation), not production
  hardening of the current architecture at all.

## LATER — the full production migration, deferred until NEXT resolves

Everything in `docs/production_reference_architecture.md`'s eight-layer
table that a GO outcome doesn't immediately require:

- Real source-system connectors (CRM/CTMS/EDC/eTMF/publications feed) —
  explicitly not attempted without a real target system to integrate
  against.
- A real secrets manager and credential rotation (currently raw env
  vars).
- Observability: tracing, metrics dashboards, alerting on policy denials
  and bridge-whitelist changes (currently a JSON-lines audit log).
- A real human-governance UI for the approval queue (currently a human
  calling `.approve()` in code).
- Multi-tenancy / real IdP-backed roles (currently `principal_roles` is
  caller-asserted).
- Horizontal scaling, redundancy, a real graph database and vector store
  at production data volume.

None of this is scheduled. It becomes NEXT-priority only once pilot
evidence says the architecture is worth hardening, and even then, only
the specific pieces the pilot's own findings point at first.
