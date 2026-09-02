# Pilot Feedback Questions

Three question sets, one per stakeholder group from `docs/pilot_plan.md`.
Used during the feedback step of `docs/pilot_workflow.md`. Each question
maps back to a hypothesis in `docs/pilot_execution_plan.md` §4 so answers
translate directly into a GO/ITERATE/STOP-PIVOT input
(`docs/pilot_decision_framework.md`) rather than staying anecdotal.

Ask open-ended, capture verbatim where possible — these are qualitative
inputs, not a survey to be numerically averaged. A 1–5 rating is included
per question only where a quick anchor is useful; the reasoning behind
the number matters more than the number.

---

## 1. AI / Platform teams (AI Platform Owner, Enterprise Architect)

*Maps primarily to the reuse hypothesis (§4.1) and platform value
hypothesis (§4.4).*

1. Compare onboarding a new use case here (a new `agents/*.yaml` config)
   to how your team would normally give an AI agent access to enterprise
   data. Is this less effort, more, or about the same? Why?
2. Did you need to touch anything under `context_layer/graph/`,
   `context_layer/policy/`, or `context_layer/retrieval/` to get your use
   case working, or was a config file enough? (1–5: 1 = needed real code
   changes, 5 = config only, as designed)
3. Is the `Request → RetrievalScope` policy contract
   (`context_layer/policy/engine.py`) something your real policy engine
   (OPA, Cedar, or otherwise) could actually implement, or does it assume
   something your stack doesn't have?
4. Is the bridge-whitelist pattern (`context_layer/graph/bridges.py` — a
   single table of allowed cross-domain edges) something you'd want as
   the enforcement point in your own systems, or does your real
   architecture need something this model doesn't capture?
5. Would you trust this Context Package contract (facts + lineage +
   governance + audit,
   `context_layer/api/schema.py`) as something a real production
   pipeline could be built against, or does it need to change shape
   first?
6. What's the single biggest blocker, if any, to extending this beyond
   synthetic data to a real (even limited) source system?
7. If this became the standard way your org's AI agents get enterprise
   context, what's the first thing that would break at real scale?

---

## 2. Business users (Commercial Product Owner, Clinical Product Owner,
   and anyone acting as a rep/brand-manager/clinical-ops end user during
   the session)

*Maps primarily to the context relevance hypothesis (§4.2).*

1. Looking at the context returned for your use case — is this actually
   what you'd want to know before doing [the next approved engagement /
   assessing this site]? What's missing? (1–5: 1 = not useful, 5 =
   exactly what I need)
2. Did anything in the returned context feel wrong, out of date, or
   irrelevant to your real workflow?
3. The system explicitly tells you what's *excluded* and why (e.g. "MSL
   interactions not permitted for this purpose"). Is that useful, or
   just noise?
4. For the compliance-flagged scenario (an HCP who's an active
   investigator) — is a flag ("promotional exclusion rules apply")
   enough, or would you actually need more detail here to trust the
   system's judgment?
5. Would you use this instead of however you currently pull this
   information together? What would have to be true for you to actually
   rely on it?
6. Was the generated answer (not just the raw data) something you could
   act on directly, or would you always need to go verify it yourself
   first?

---

## 3. Governance stakeholders (Data/AI Governance, Compliance)

*Maps primarily to the governance trust hypothesis (§4.3).*

1. Look at `context_layer/graph/bridges.py`'s whitelist table (2
   entries: publications→commercial, investigator-status→commercial
   flag-only) — does this reflect a real rule your organization actually
   has, or is it a plausible-sounding simplification?
2. Look at `context_layer/policy/engine.py`'s purpose table — are these
   the right purposes, the right roles per purpose, and the right
   subgraph/bridge/redaction scoping for each? What's missing or wrong?
3. Walk through the compliance-flagged scenario
   (`evaluation/pilot_dataset/scenarios.json`, `N3`) live — does the
   system's behavior (surface a flag, withhold clinical detail) match
   what your actual compliance process requires here?
4. Is "purpose bound to the agent at publish time, never a runtime
   parameter" (see `README.md` §5, `tests/test_privilege_escalation.py`)
   the right enforcement model, or does your real governance process need
   purpose to be negotiable at request time in some case this doesn't
   handle?
5. Is per-fact lineage (source system, domain, retrieval method — see any
   returned Context Package's `lineage` field) sufficient for an audit,
   or is something missing?
6. If this went to production, what compliance/regulatory review would
   this architecture need to pass that hasn't been checked yet?
7. Run the adversarial scenarios (`evaluation/pilot_dataset/scenarios.json`,
   type `adversarial`) live — does anything here surprise you, in either
   direction (something you expected to be blocked that wasn't, or
   something blocked that shouldn't have been)?

---

## Capturing answers

Record verbatim quotes where possible, tagged with the scenario or
question number, in whatever the pilot's own notes format is —
`docs/pilot_workflow.md` step 9 covers this. Do not summarize a
stakeholder's answer into a number without keeping the reasoning; the
decision framework (`docs/pilot_decision_framework.md`) treats a single
clear "no, this doesn't map to our real rules" from Governance as more
decisive than five positive ratings elsewhere.
