# Pilot Workflow

A structured session for running the pilot with a stakeholder or small
group. **Approximately 30–60 minutes** — the range depends heavily on how
many of `docs/pilot_feedback_questions.md`'s questions get real
discussion and how many stakeholder groups are combined into one session;
treat the range as planning guidance, not a claimed exact duration for
every session.

Run one session per stakeholder group where possible (AI/Platform,
Business, Governance — `docs/pilot_plan.md` §Pilot users), since each
group's step 6/7 below differs. A combined session works too, at the cost
of covering fewer feedback questions per group in the available time.

---

## 1. Set context (≈5 min)

State plainly, every session, so no participant mistakes this for a
finished product: **"This is a validated prototype, not production
software. We're here to find out if the approach is useful and the
governance model is right — not to sign off on shipping it."** Name the
use case(s) this session focuses on.

## 2. Architecture walkthrough (≈5 min)

One pass through `README.md` §3–4 (what an Enterprise Context Layer is,
the core architecture diagram) — enough that "purpose bound to the agent,
not the caller" and "policy scopes retrieval before it happens" land
before the demo, not during it.

## 3. Live primary demo (≈5–10 min)

```bash
curl http://<host>:8080/demo/compare/HCP-021
```

or open `http://<host>:8080/` in a browser and click through — the
landing page links directly to this. Walk through the `comparison` block
live: same entity, two agents, two purposes, different (non-overlapping)
facts, `status: PASS`. This is the single most important five minutes of
the session — everything else supports or tests this claim.

## 4. Hands-on: stakeholder drives their own use case (≈10–15 min)

Hand over `/docs` (the auto-generated Swagger UI) or a terminal with
`curl`. Have the stakeholder run their own use case's endpoint
(`/demo/commercial` or `/demo/clinical`, or a `POST /context` with a
question they'd actually ask) themselves, not watch it run. This is
where `docs/pilot_feedback_questions.md` §2 (business users) gets real
material — a stakeholder reacting to output they triggered themselves
produces sharper feedback than watching a canned demo.

## 5. Run the pilot scenario dataset together (≈10 min)

```bash
./.venv/bin/python scripts/run_pilot_scenarios.py --type adversarial
```

For a Governance session, this is the most important step — run it live,
not pre-recorded, and let the stakeholder pick which scenario to look at
next. For a Business session, focus on `--type normal` and `--type edge`
instead; adversarial scenarios are Governance's material. See
`evaluation/pilot_dataset/README.md` for what each scenario tests.

## 6. Review the Context Package structure (≈5 min)

Open one real returned `context_package` (from step 3, 4, or 5) and walk
through `policy_decision`, `lineage`, `governance`, and `audit` — the
parts of the response most stakeholders won't read on their own but that
matter most for trust and audit (`README.md` §7).

## 7. Governance-specific discussion (Governance sessions only, ≈5–10 min)

Work through `docs/pilot_feedback_questions.md` §3 directly against
`context_layer/graph/bridges.py` and `context_layer/policy/engine.py`
open on screen — this is deliberately code-level, not slide-level, since
the governance trust hypothesis (`docs/pilot_execution_plan.md` §4.3)
is specifically about whether the *actual rule table* maps to real
requirements.

## 8. Structured feedback (≈10 min)

Work through the relevant section of `docs/pilot_feedback_questions.md`
for this stakeholder group. Capture answers verbatim where possible —
see that document's "Capturing answers" section for why.

## 9. Wrap-up (≈5 min)

- Note anything that came up as a candidate GO/ITERATE/STOP-PIVOT signal
  per `docs/pilot_decision_framework.md` — flag it explicitly rather than
  letting it get lost in general notes.
- Confirm next steps and who owns following up on any open question
  (especially anything Governance flagged in step 7 — those are blocking
  by default, not optional polish).
- Log the session (date, stakeholder group, which use case(s) covered,
  which scenarios were run) so `docs/pilot_readiness_report.md`'s
  eventual pilot outcome summary (a document this repository does not yet
  contain, since the pilot hasn't run) has a real record to draw from.

---

## What this workflow deliberately does not do

It does not ask a stakeholder to approve a production deployment, sign
off on compliance, or commit to a rollout — those are downstream of a
GO decision (`docs/pilot_decision_framework.md`), not something a single
30–60 minute session can responsibly produce.
