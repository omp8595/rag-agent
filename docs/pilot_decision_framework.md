# Pilot Decision Framework

How pilot evidence (`docs/pilot_metrics.md` [PILOT] rows,
`docs/pilot_feedback_questions.md` answers, scenario runs from
`evaluation/pilot_dataset/`) becomes one of three calls: **GO**,
**ITERATE**, or **STOP-PIVOT**. This framework did not exist before the
pilot ran — it exists now so the criteria are fixed *before* results
come in, not chosen afterward to fit whatever happened.

This framework is evaluated against the four hypotheses in
`docs/pilot_execution_plan.md` §4. It does not by itself declare the
pilot a success or claim product-market fit — see
`docs/pilot_readiness_report.md`'s explicit constraint on that.

---

## GO — proceed to a larger pilot / begin targeted production hardening

All of the following:

1. **Reuse (§4.1):** no pilot use case required a code change to
   `context_layer/graph/`, `policy/`, or `retrieval/` — config only. If a
   3rd agent (`medical_inquiry`) was onboarded during the pilot, it also
   held.
2. **Governance trust (§4.3):** zero policy/bridge violations during
   organic (non-adversarial) pilot usage, **and** the governance
   stakeholder affirms the bridge whitelist and purpose table reflect
   real rules (or names specific, addressable gaps rather than a
   fundamental mismatch).
3. **Context relevance (§4.2):** business users rate retrieved context as
   useful for their actual workflow (not just policy-compliant), even if
   they also name specific gaps.
4. **Platform value (§4.4):** the platform owner judges onboarding effort
   as lower than their counterfactual.
5. No critical defect is found during the pilot (a critical defect found
   during a prior validation pass, per `docs/test_report.md`, does not
   count against this — it was found and fixed before the pilot; a *new*
   one found during the pilot does count, and must be fixed and
   regression-tested before GO is declared).

**Then:** proceed per `docs/roadmap.md`'s NEXT section — targeted
production hardening informed by exactly what the pilot found gaps in,
not a blanket "build everything in
`docs/production_reference_architecture.md`" push.

---

## ITERATE — the direction is right, specific things need to change first

Any of the following, with nothing in STOP-PIVOT's list also true:

- Governance stakeholder identifies specific, addressable gaps in the
  purpose/bridge model (e.g., a missing purpose, a bridge that should be
  narrower or wider) rather than rejecting the model's shape.
- Business users find the *architecture's* governance behavior correct
  but the *retrieved content* insufficiently rich for their real workflow
  — a retrieval/data-source gap, not a governance-model gap.
- Onboarding worked (config-only, per §4.1) but adoption was low because
  of API/DX friction (e.g., stakeholders found `/context` awkward to
  integrate) rather than the underlying value being absent.
- RAGAS/DeepEval/LLM-judge scores (first real run, with a provider key)
  surface answer-quality issues unrelated to governance (e.g.,
  `answer_synthesis.py`'s templated generation is too rigid for real
  questions) — a generation-layer fix, not an architecture rejection.

**Then:** fix the specific, named gaps; re-run the affected pilot
scenarios and feedback questions; do not re-run the entire pilot from
scratch unless the fix touches the core architecture.

---

## STOP-PIVOT — the current approach needs to change, not just extend

Any of the following:

- A governance stakeholder identifies that the purpose-bound,
  bridge-whitelisted model **cannot express** a real compliance
  requirement they have — not a missing entry, but a shape the model
  itself doesn't support (e.g., a rule that genuinely needs runtime
  negotiation of purpose, which the architecture's central invariant
  explicitly forbids).
- A non-zero policy or bridge violation occurs during **organic** (not
  adversarial-test) pilot usage — per `docs/pilot_plan.md`, this is
  always a stop-and-investigate event, not a metric to average away.
- Business stakeholders across both use cases find the retrieved context
  not useful for real workflows even after addressing retrieval-quality
  gaps (i.e., the *governance-scoped* context itself is the wrong shape
  for real decisions, not just under-populated).
- The reuse hypothesis is refuted — a real pilot use case needed core
  code changes beyond configuration, indicating the architecture's
  "reuse via config" claim doesn't hold outside the two use cases it was
  built and tested against.

**Then:** do not proceed to production hardening on the current
architecture. Take the specific finding back to redesign — this is a
successful pilot outcome in the sense that it answered the open question
before expensive infrastructure work was spent on the wrong foundation,
not a failure of the pilot process.

---

## What this framework is not

It is not a scoring rubric that averages metrics into one number —
consistent with this whole project's governance-gating philosophy
(`context_layer/evaluation/scoring.py`: a governance violation is a hard
gate, not one weighted term), a single STOP-PIVOT-level signal from
Governance overrides any number of positive signals elsewhere. The
categories above are read in listed order for exactly that reason.
