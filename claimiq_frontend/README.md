# ClaimIQ — Knowledge Graph Claims Triage Copilot (prototype)

A click-through UI prototype for a Guidewire ClaimCenter-style claims
triage copilot built around a knowledge graph. All data — the claim
queue, the graph, documents, guidelines, and performance metrics — is
simulated; nothing here connects to a real ClaimCenter instance.

It demonstrates the pitch: a knowledge graph sits as the shared context
layer that rules, ML, an LLM, and retrieval-augmented Q&A all read from,
so every AI triage recommendation stays explainable back to graph
entities and source documents, and every adjuster decision (approve or
override) is captured as labelled feedback.

## Screens

- **Overview** — KPIs, the featured claim, and the end-to-end demo flow.
- **Claims** — the triage queue and a per-claim workspace (AI summary,
  extracted facts, graph context, "why this recommendation", an
  Ask-ClaimIQ RAG + graph Q&A panel, and the adjuster approve/override
  decision).
- **Knowledge Graph** — an interactive, filterable, force-style graph
  explorer centered on a claim/policy/customer/exposure.
- **AI Performance** — acceptance rate, override rate, calibration, and
  segment-level automation eligibility, updated live from decisions made
  in the session.
- **Architecture** / **Autonomy roadmap** — the conceptual architecture
  and the staged path from "recommend" to "scaled automation."

## Quickstart

```bash
npm install
npm run dev       # http://localhost:5173
npm run build     # production build to dist/
npm run preview   # serve the production build
```
