# rag-agent — Life Sciences Enterprise Context Layer (prototype)

A working prototype of the design in [`docs/design.md`](docs/design.md): a
policy-scoped Context API, sitting over a partitioned knowledge graph, that
proves the same HCP produces provably different context depending on which
agent — and therefore which purpose — is asking.

Everything here runs locally with no external services: an in-memory graph
(networkx) stands in for Neo4j, and per-domain TF-IDF indexes stand in for
an embedding store, so the demo and tests run offline. All data is
synthetic — 50 HCPs, 10 institutions, 30 content items, 100 interactions,
40 publications, 5 studies, generated deterministically.

## Quickstart

```bash
python3 -m venv .venv
./.venv/bin/pip install -e ".[dev]"

# Week 1: generate the synthetic fixtures (data/synthetic/*.json)
./.venv/bin/python -m context_layer.data.synthetic_gen

# Week 6: the demo — same HCP, two agents, two Context Packages
./.venv/bin/python scripts/demo.py

# A GraphRAG-driven brand-manager promotional campaign across all 50 HCPs
./.venv/bin/python scripts/campaign_workflow.py "Biomarker testing"

# Tests — prove the firewall, policy engine, and scope isolation hold
./.venv/bin/python -m pytest

# Run the Context API as an MCP server (stdio transport)
./.venv/bin/python -m context_layer.api.mcp_server
```

## Architecture → code map

| Design doc section | Code |
|---|---|
| §1 Data Layer | `context_layer/data/synthetic_gen.py` (generator), `context_layer/data/loader.py` (source-system seam) |
| §2 Semantic (mapping) Layer | `context_layer/semantic/mapping.py` |
| §3 Knowledge Graph (partitioned) | `context_layer/graph/store.py` (Identity Spine + domain subgraphs, bounded traversal), `context_layer/graph/build.py` (loaders), `context_layer/graph/bridges.py` (the whitelist table) |
| §4 Retrieval capabilities | `context_layer/retrieval/entity_lookup.py`, `context_layer/retrieval/vector_index.py`, `context_layer/retrieval/graphrag.py` |
| §5 Governance & Policy Layer | `context_layer/policy/engine.py` (Request → RetrievalScope), `context_layer/policy/models.py`, `context_layer/policy/audit.py` |
| §6 Context API (MCP server) | `context_layer/api/assembler.py` (Context Assembler), `context_layer/api/schema.py`, `context_layer/api/mcp_server.py` |
| §7 Agent Builder | `context_layer/agent_builder/schema.py`, `context_layer/agent_builder/builder.py`, `context_layer/agent_builder/agent.py`, `context_layer/agent_builder/actions.py`, `context_layer/agent_builder/approvals.py`, `agents/*.yaml` |
| §9 Prototype scope / week-6 demo | `scripts/demo.py`, `scripts/campaign_workflow.py`, `tests/` |

## What the prototype actually enforces

- **The bridge whitelist is data, not scattered conditionals** (`graph/bridges.py`), and it's the single choke point `GraphStore.bounded_traversal` consults before crossing a domain boundary — so `tests/test_bridge_firewall.py` can grant *every* bridge that exists and still prove MSL interactions and Commercial↔Clinical/Medical crossings never appear.
- **Purpose is bound to the agent, not the caller.** `ThinAgent.get_context()` (`agent_builder/agent.py`) has no `purpose` parameter at all — it's fixed at publish time by `agent_builder/builder.py`, which also rejects any `purpose`/`audience_roles` combination the policy engine doesn't recognize. `task` (free text) only ever affects vector-search ranking, never the retrieval scope — see `tests/test_policy_engine.py::test_task_text_never_affects_scope`.
- **Policy fails closed.** An unregistered purpose or a role not permitted for that purpose raises `PolicyDenied` rather than returning an empty-but-present scope.
- **Every Context Package is audited** with its request, the scope that was applied, and its `lineage_id` (`policy/audit.py`, appended to `context_layer_audit.log`).
- **Action tools are authorized before anything else runs, then optionally gated.** `ThinAgent._require_action` (`agent_builder/agent.py`) checks `action_tools` membership as the *first* line of every action method — before any context lookup or business-rule evaluation — so an unauthorized caller gets a `PermissionError`, never a `blocked` result that would reveal the action ran at all. Only past that gate does `_dispatch` check `guardrails.human_approval_required`: an action named there is never executed directly, it's submitted to a shared `ApprovalQueue` (`agent_builder/approvals.py`) and returns `pending_approval` until an explicit `approvals.approve(id)`. `agent_builder/builder.py` rejects, at publish time, any config whose `human_approval_required` names an action that isn't actually in `action_tools` — the class of bug where a guardrail silently gates nothing. `draft_email` adds one more refusal on top: it reads the Context Package's own `constraints` block and returns `blocked` for a promotional draft when one names a promotional exclusion (`agent_builder/actions.py`) — see `tests/test_actions.py`.
- **GraphRAG never sees more than its own domain, even for a purpose with bridges.** `ContextAssembler._community_summary` calls `retrieval/graphrag.py` once per subgraph in the *granted* scope only — a commercial-purpose request gets a commercial-only summary even though that purpose is bridged into medical and clinical for individual *facts* (`tests/test_graphrag.py`).

Run `scripts/demo.py` to see the thesis directly: `HCP-021` (an active
clinical investigator) produces one Context Package under the HCP
Engagement Agent (`commercial_engagement`) — publications bridged in,
investigator status collapsed to a compliance flag, MSL/study detail
excluded — and a different one under the Site Selection Agent
(`site_selection`) — full study/enrollment detail, zero commercial facts,
no bridges applied at all.

## GraphRAG-driven promotional campaign

`scripts/campaign_workflow.py` is a brand-manager workflow built entirely
on the HCP Engagement Agent's own tools — it opens no new access path.
For a campaign topic (default `"Biomarker testing"`), it:

1. **Screens** all 50 HCPs using `community_summary` — GraphRAG-lite's
   "what does this HCP care about," derived only from their own
   commercial-domain engagement history. This is the actual targeting
   signal; `recommended_content` (a global corpus search) is deliberately
   *not* used for targeting — it matches the whole content library for
   any query regardless of entity, which made an early version of this
   script "target" all 50 HCPs. See `tests/test_campaign_workflow.py`.
2. **Drafts** outreach via `draft_email` for every on-topic HCP — the
   promotional-exclusion constraint and the human-approval gate are
   enforced by the agent itself, not re-derived here.
3. **Logs** a `create_campaign_task` against the top vector-recommended
   piece of approved content.
4. **Reports** who's in, who's off-topic, who's excluded on compliance
   grounds and why, and what a reviewer still has to approve.

A real run against the synthetic fixtures: 50 screened → 10 on-topic
(GraphRAG actually discriminates) → 1 held back as an active investigator
→ 9 drafts approved → 9 campaign tasks logged.

## Deliberate simplifications (and why)

These are prototype-scoped stand-ins, not the production design — see
`docs/design.md` §10 for the open decisions they trade off against:

- **networkx instead of Neo4j/RDF** — same partition + bridge-whitelist
  enforcement model, no server to stand up for a 4–6 week prototype.
  Swapping in Neo4j means reimplementing `GraphStore`; nothing above it
  (policy, retrieval, API, agents) would need to change.
- **A rule table instead of OPA/Cedar** (`policy/engine.py`) — same
  Request → RetrievalScope contract; a real deployment plugs in the actual
  policy engine there.
- **TF-IDF instead of an embedding index** (`retrieval/vector_index.py`) —
  keeps the demo runnable offline; the per-domain isolation property is
  identical either way.
- **GraphRAG is a minimal extractive stub** (`retrieval/graphrag.py`,
  wired into every Context Package as `community_summary`) — frequency-
  ranked topics among same-domain neighbors, not LLM-summarized
  communities. It exists to make design-doc open decision #2 concrete
  rather than to resolve it.
- **Three purposes implemented** (`commercial_engagement`, `medical_inquiry`,
  `site_selection`) against the doc's four-purpose enum — `sales_prep` is
  named but not defined; adding it is a `PurposePolicy` entry in
  `policy/engine.py`, nothing structural.

## Repository layout

```
context_layer/
  data/            synthetic data generator + source-record loader
  semantic/        MDM/standards crosswalk
  graph/           GraphStore, domain loaders, bridge whitelist
  policy/          policy engine, request/scope models, audit log
  retrieval/       entity lookup, vector index, GraphRAG-lite
  api/             Context Assembler, Context Package schema, MCP server
  agent_builder/   agent config schema, publish-time validation, ThinAgent, action tools + approval queue
agents/            HCP Engagement Agent, Site Selection Agent configs
data/synthetic/    generated fixtures, committed for convenience — regenerate anytime via synthetic_gen.py
docs/design.md     the source design document
scripts/demo.py               the week-6 demo
scripts/campaign_workflow.py  GraphRAG-driven brand-manager campaign workflow
tests/             firewall, policy, scope-isolation, action-tool, GraphRAG, and campaign tests
```
