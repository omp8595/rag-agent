# Life Sciences Enterprise Context Layer — Detailed Design

## 0. Design principles

1. **Domains keep their data.** Clinical, Medical, and Commercial IT remain system owners. The Context Layer holds identity, semantics, relationships, and indexes — not a copy of every record.
2. **Policy scopes retrieval; it does not filter results.** The request's purpose determines which subgraphs and indexes are queried at all.
3. **Consume MDM, don't rebuild it.** Golden IDs come from the existing MDM. The Context Layer maps, it does not master.
4. **Every fact carries lineage.** Each element of a Context Package states its source system, domain, and policy basis.
5. **The Context API is an MCP server.** Standard tools/resources, so any agent runtime can consume it.

---

## 1. Data Layer (federated)

| Domain | Systems | What the Context Layer ingests |
|---|---|---|
| Commercial | CRM (Veeva/SFDC), campaign platform, MDM, engagement analytics | HCP golden ID, interaction events, content engagement, approved content metadata, territory |
| Medical | Publications feed, congress data, medical information system, MSL CRM | Publications, congress attendance, scientific topics; **MSL interactions and medical inquiries are ingested into the Medical subgraph only** |
| Clinical | CTMS, EDC, eTMF, site feasibility | Investigator–site–study relationships, site performance metrics (aggregate, no patient data) |

Ingestion is metadata- and relationship-first. Bulk documents stay in source; only chunks needed for retrieval are embedded, tagged with domain and classification at ingest time.

**Explicitly out of scope:** patient-level data, PHI, safety case narratives.

---

## 2. Semantic (mapping) Layer

Not a new ontology. A mapping layer over existing standards and enterprise hierarchies.

```
Enterprise concept       Mapped from
─────────────────────    ─────────────────────────────────
Person / HCP             MDM golden ID, NPI, ORCID
Specialty                MDM specialty → SNOMED CT
Condition / Indication   MedDRA, SNOMED CT
Therapeutic Area         Enterprise TA hierarchy
Product / Brand          Enterprise product master, RxNorm
Study                    CDISC (protocol ID, phase, status)
Site / Institution       CTMS site ID → MDM account ID
Content                  DAM ID + approval status + intended audience
Topic                    MeSH (for publications), enterprise topic taxonomy
```

The layer answers: "when Commercial says *account* and Clinical says *site*, are they the same institution?" — via MDM crosswalk, with confidence scores where the match is inferred.

---

## 3. Knowledge Graph (partitioned)

Three domain subgraphs plus one shared **Identity Spine**.

```
                 ┌───────────────────────────┐
                 │      IDENTITY SPINE       │
                 │ Person · Institution ·    │
                 │ Product · TA · Topic      │
                 └────┬──────────┬──────────┬┘
                      │          │          │
          ┌───────────▼──┐  ┌───▼──────┐  ┌▼────────────┐
          │ COMMERCIAL   │  │ MEDICAL  │  │ CLINICAL    │
          │ subgraph     │  │ subgraph │  │ subgraph    │
          └──────────────┘  └──────────┘  └─────────────┘
```

**Identity Spine** holds only reference entities and their standard-coded attributes. No interactions, no engagement, no study assignments.

**Domain subgraphs** hold behavioral and relational edges:

- Commercial: `ENGAGED_WITH`, `ATTENDED`, `IN_TERRITORY`, `TARGETED_BY_CAMPAIGN`
- Medical: `AUTHORED`, `PRESENTED_AT`, `KOL_IN`, `MSL_INTERACTION` (restricted)
- Clinical: `PRINCIPAL_INVESTIGATOR_OF`, `SITE_OF`, `ENROLLMENT_RATE`, `FEASIBILITY_SCORE`

**Bridges are whitelisted edges, not open traversal.** Examples of approved bridges:

| From → To | Allowed direction | Condition |
|---|---|---|
| Medical publications → Commercial | Yes | Public-domain publications only; MSL interactions never |
| Clinical investigator status → Commercial | Yes, flag only | Boolean "is active investigator" for compliance exclusion; no study details |
| Commercial engagement → Clinical site selection | No | Regulatory: commercial data must not influence site selection |
| Commercial → Medical | No | Firewall |

This table is owned by Compliance and versioned. It is the single most important artifact for approval.

---

## 4. Retrieval capabilities

Four capabilities behind one interface, selected by the Context Assembler per request:

1. **Entity lookup** — Identity Spine + domain profile.
2. **Graph traversal** — bounded k-hop within the permitted subgraph(s); bridge edges only if whitelisted for the purpose.
3. **GraphRAG** — community summaries pre-computed per domain (never across the firewall), used for "what does this HCP care about" style questions.
4. **Vector retrieval** — per-domain indexes. A Commercial-purpose request never touches the Medical index.

Indexes and community summaries are built per domain at ingest, which is what makes retrieval-time scoping enforceable rather than aspirational.

---

## 5. Governance & Policy Layer

Policy is evaluated **before** retrieval and produces a *retrieval scope*.

```
Request
  ├── principal   (user/agent identity, roles)
  ├── purpose     (enum: commercial_engagement, medical_inquiry,
  │                site_selection, sales_prep, ...)
  ├── entity      (golden ID)
  └── task        (free text, for relevance only, never for access)
        │
        ▼
Policy Engine (OPA / Cedar)
        │
        ▼
Retrieval Scope
  ├── subgraphs: [commercial]
  ├── bridges:   [medical.publications → commercial]
  ├── indexes:   [commercial_content, commercial_interactions]
  ├── max_hops:  2
  └── redactions: [hcp.personal_email]
```

Purpose is declared by the agent definition, not chosen at query time by the user, so a Brand Manager cannot escalate by rephrasing.

Audit: every Context Package is logged with request, scope, and the lineage of every returned fact.

---

## 6. Context API (MCP server)

**Resources**
- `context://hcp/{id}` — profile within permitted scope
- `context://institution/{id}`
- `context://content/{id}`

**Tools**
- `get_context_package(entity_id, purpose, task)` — primary entry point
- `find_entities(query, entity_type, purpose)` — search within scope
- `explain_relationship(entity_a, entity_b, purpose)` — path in permitted subgraph
- `find_content(topic, audience, approval_status)` — approved content only

**Context Package schema**

```json
{
  "entity": { "id": "HCP-123", "type": "HCP", "display": "Dr. A. Smith" },
  "purpose": "commercial_engagement",
  "scope_applied": { "subgraphs": ["commercial"], "bridges": ["medical.publications"] },
  "profile": {
    "specialty": { "value": "Oncology", "code": "SNOMED:394592004", "source": "MDM" }
  },
  "facts": [
    { "claim": "Attended brand webinar on biomarker testing, 2026-06-14",
      "source": "CRM", "domain": "commercial", "confidence": 1.0 },
    { "claim": "Co-authored 3 publications on HER2-low breast cancer (2024–26)",
      "source": "PubMed", "domain": "medical", "bridge": "medical.publications",
      "confidence": 0.92 }
  ],
  "relationships": [
    { "type": "WORKS_AT", "target": "INST-45", "display": "Tata Memorial Hospital" }
  ],
  "recommended_content": [
    { "id": "CNT-881", "title": "...", "approval": "approved", "audience": "HCP" }
  ],
  "constraints": [
    "Active clinical investigator on sponsor study — apply promotional exclusion rules"
  ],
  "excluded": [
    { "domain": "medical", "reason": "MSL interactions not permitted for commercial purpose" }
  ],
  "lineage_id": "ctx-9f2a..."
}
```

The `constraints` and `excluded` blocks matter: the agent is told what it must respect and what it was not shown, so it can be honest with the user rather than guessing.

---

## 7. Agent Builder

Configuration, not code:

```yaml
agent:
  name: HCP Engagement Agent
  purpose: commercial_engagement      # binds policy scope
  audience_roles: [brand_manager]
  context_tools: [get_context_package, find_content, explain_relationship]
  action_tools: [draft_email, create_campaign_task]
  guardrails:
    approved_content_only: true
    human_approval_required: [send_email]
    max_context_hops: 2
```

The builder validates that `purpose` and `audience_roles` are a permitted combination in the policy engine before the agent can be published.

---

## 8. How the domains connect — one line each

- **Commercial IT** registers CRM, campaign, and content systems as sources; owns the Commercial subgraph and indexes; consumes Medical publications via the whitelisted bridge.
- **Medical IT** registers publication and congress feeds; owns the Medical subgraph; MSL interactions are ingested but never bridged outward.
- **Clinical IT** registers CTMS/site data at aggregate level; owns the Clinical subgraph; exposes only an "active investigator" flag to Commercial for compliance exclusion.
- **MDM / Data Governance** owns the Identity Spine and the bridge whitelist.

---

## 9. Prototype scope (4–6 weeks)

| Week | Deliverable |
|---|---|
| 1 | Synthetic data: 50 HCPs, 10 institutions, 30 content items, 100 interactions, 40 publications, 5 studies |
| 2 | Identity Spine + Commercial subgraph + Medical publications subgraph (Neo4j or similar); one bridge |
| 3 | Policy engine with two purposes (`commercial_engagement`, `site_selection`) and a real bridge whitelist |
| 4 | Context API as MCP server; `get_context_package` returning the schema above with lineage |
| 5 | HCP Engagement Agent consuming the API; second thin agent (`site_selection`) to prove scope isolation |
| 6 | Demo: same HCP, two purposes, two different Context Packages, audit log showing why |

The week-6 demo is the thesis: one entity, one platform, two agents, provably different context.

---

## 10. Open decisions

1. Graph store: property graph (Neo4j) vs. RDF/SPARQL — RDF fits the standards mapping better; property graphs are faster to prototype.
2. Whether GraphRAG community summaries are worth the maintenance cost at enterprise scale, or whether bounded traversal + vector is sufficient for v1.
3. Who arbitrates bridge whitelist changes — Compliance alone, or a cross-domain council.
4. Agent memory: does conversation state live in the Context Layer (shared) or in the agent runtime (isolated)? Recommend isolated for v1.
