# Controlled Pilot Plan

**Status of the thing being piloted: PROTOTYPE VALIDATED — NOT PRODUCTION
READY** (see [`docs/test_report.md`](test_report.md) and
[`docs/deployment_validation_report.md`](deployment_validation_report.md)).
This plan is for a **controlled pilot using synthetic or representative
data** — it explicitly does not authorize connecting real enterprise
source systems or processing real HCP/patient data. That step requires
the production-hardening work in
[`docs/production_reference_architecture.md`](production_reference_architecture.md)
first.

---

## Pilot objective

Validate whether a shared Enterprise Context Layer can:

1. Reduce the effort required to onboard a new AI agent (a new
   `agents/*.yaml` + purpose, not new integration code per agent).
2. Provide relevant context for multiple use cases from one underlying
   knowledge graph, without each use case building its own retrieval
   stack.
3. Enforce purpose-based governance — the same entity never leaks
   forbidden-domain data to the wrong agent, verifiably, not just by
   policy document.
4. Improve traceability of AI-consumed context (every fact has lineage;
   every request is audited).

---

## Pilot users

| Role | Stake in the pilot |
|---|---|
| AI Platform Owner | Owns whether this becomes the standard way new AI agents get enterprise context, vs. each team building its own retrieval |
| Commercial Product Owner | Owns the HCP Engagement use case; judges whether the commercial context is actually useful for rep/brand workflows |
| Clinical Product Owner | Owns the Site Selection use case; judges whether clinical context is sufficient for feasibility/site-selection workflows |
| Data/AI Governance | Owns whether the policy model (purpose → scope, bridge whitelist, fail-closed) satisfies real compliance requirements, not just this prototype's synthetic test cases |
| Enterprise Architect | Owns whether the architecture (partitioned graph, policy engine, Context Package contract) is the right foundation to extend to real source systems |

---

## Pilot scope

Two representative use cases — the same two the prototype already
implements, so the pilot is extending validated behavior, not building
new behavior mid-pilot:

1. **Commercial HCP Intelligence** — the HCP Engagement Agent
   (`commercial_engagement` purpose): "what should I know before the
   next approved engagement with this HCP."
2. **Clinical Site Intelligence** — the Site Selection Agent
   (`site_selection` purpose): "is this HCP/institution a reasonable
   candidate for a trial site."

Data: representative/synthetic, generated the same way as the
prototype's own fixtures (`context_layer/data/synthetic_gen.py`), or a
de-identified representative extract if governance approves — **not**
live production HCP data during this pilot phase.

---

## Success metrics

### Product

- Number of agents onboarded (target: the 2 in scope, plus a stretch
  goal of a 3rd — e.g. `medical_inquiry`, already policy-defined but
  without a published agent config yet).
- Time to onboard an agent (from "we have a purpose" to "a working
  agent config" — the prototype's own agent YAML files are the
  reference for what this actually takes).
- Context API adoption — number of real calls made through `/context`
  or the MCP server vs. teams falling back to ad hoc retrieval.

### Quality

- Context relevance, precision, recall, faithfulness — via the
  evaluation framework (`context_layer/evaluation/`, `docs/evaluation.md`):
  RAGAS + DeepEval + LLM-as-judge, run with a real provider key during
  the pilot (unlike this validation pass, which had none).

### Governance

- Unauthorized access attempts blocked (count, from the audit log —
  `policy/audit.py` and any pilot-added dashboarding over it).
- Policy violations (target: **zero** — any non-zero count is a stop-
  and-investigate event, not a metric to trend down over time).
- Lineage coverage (target: 100%, matching the validation pass's
  measured baseline — see `docs/test_report.md` §5).
- Unauthorized bridge traversals (target: **zero**, same reasoning as
  policy violations).

### Operational

- API latency (baseline from this validation pass: ~2ms full context
  assembly in-process, at prototype scale — pilot should measure real
  latency under real infrastructure and real data volume, which will
  differ).
- Error rate.
- Availability during the pilot window.

---

## Out of scope

- Enterprise-wide rollout.
- Production certification (SOC2 / HIPAA / GxP sign-off, or whatever
  the org's actual bar is — not attempted or claimed by this prototype).
- Full multi-region deployment.
- Full real-time integration with live source systems (CRM, CTMS,
  MDM) — the pilot uses synthetic/representative data specifically to
  avoid this dependency while the governance model itself is validated.
- Production IAM/SSO integration — `principal_roles` in this prototype
  is a value the caller asserts; a pilot that touches anything beyond
  synthetic data needs this backed by a real identity provider first
  (see `docs/production_reference_architecture.md`'s "Multi-tenancy and
  access control integration" gap).
