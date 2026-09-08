import { useState, useMemo, useEffect } from "react";
import {
  LayoutDashboard, FileText, Share2, BarChart3, Layers, Route, Search,
  ChevronRight, CheckCircle2, AlertTriangle, XCircle, Info, Database,
  FileSearch, Users, Car, ShieldCheck, Bell, ZoomIn, ZoomOut, Maximize2,
  ArrowDown, Sparkles, MessageSquare, Send, ExternalLink, Plus, Minus
} from "lucide-react";
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, LineChart, Line,
  CartesianGrid, ScatterChart, Scatter, ReferenceLine, Legend
} from "recharts";

/* ------------------------------------------------------------------ */
/* SIMULATED KNOWLEDGE GRAPH (ClaimCenter-style simulated claim data)  */
/* ------------------------------------------------------------------ */

const TYPE_STYLE = {
  Customer:      { color: "#1D4ED8", ring: "#BFDBFE", label: "Customer" },
  Policy:        { color: "#4338CA", ring: "#C7D2FE", label: "Policy" },
  Coverage:      { color: "#6D28D9", ring: "#DDD6FE", label: "Coverage" },
  Claim:         { color: "#0F172A", ring: "#CBD5E1", label: "Claim" },
  Incident:      { color: "#B45309", ring: "#FDE68A", label: "Incident" },
  Exposure:      { color: "#BE123C", ring: "#FECDD3", label: "Exposure" },
  Vehicle:       { color: "#0369A1", ring: "#BAE6FD", label: "Vehicle" },
  Party:         { color: "#047857", ring: "#A7F3D0", label: "Party" },
  Document:      { color: "#525252", ring: "#E5E5E5", label: "Document" },
  Adjuster:      { color: "#0F766E", ring: "#99F6E4", label: "Adjuster" },
  Activity:      { color: "#7C2D12", ring: "#FED7AA", label: "Activity" },
  Reserve:       { color: "#9F1239", ring: "#FBCFE8", label: "Reserve" },
  Payment:       { color: "#3F6212", ring: "#D9F99D", label: "Payment" },
  "Previous Claim": { color: "#475569", ring: "#E2E8F0", label: "Previous Claim" },
};

const NODES = {
  "CUST-55021": { type: "Customer", label: "Daniel Whitaker", source: "Policy Admin System", attrs: { "Customer since": "2020-03-11", Segment: "Preferred", State: "OH", "Contact preference": "Mobile" } },
  "POL-78321": { type: "Policy", label: "POL-78321", source: "Policy Admin System", attrs: { Product: "Personal Auto", "Effective": "2026-01-15", "Expires": "2027-01-15", Status: "In force", "Named insured": "Daniel Whitaker" } },
  "COV-COLL": { type: "Coverage", label: "Collision", source: "Policy Admin System", attrs: { Deductible: "$500", Limit: "Actual cash value", "Applies to": "2024 Honda Accord" } },
  "COV-BI": { type: "Coverage", label: "Bodily Injury Liability", source: "Policy Admin System", attrs: { Limit: "$100,000 / $300,000", "Per person / per accident": "Yes" } },
  "COV-PD": { type: "Coverage", label: "Property Damage Liability", source: "Policy Admin System", attrs: { Limit: "$50,000", Deductible: "None" } },
  "VEH-4471": { type: "Vehicle", label: "2024 Honda Accord", source: "Policy Admin System", attrs: { VIN: "1HGCY2F5XRA044716", Plate: "OH · KTX 4471", Use: "Personal commute", "Estimated damage": "$8,400" } },
  "VEH-9082": { type: "Vehicle", label: "2019 Ford F-150", source: "Police Report DOC-001", confidence: 0.94, attrs: { Plate: "OH · GHP 9082", Owner: "Marcus Bell", "Insurer": "Third-party carrier (unverified)" } },
  "CC-10245": { type: "Claim", label: "CC-10245", source: "Claim Intake (FNOL)", attrs: { "Loss date": "2026-08-28", Reported: "2026-08-29", Type: "Auto · Collision", Status: "Open — Triage", "Loss location": "Main St & 5th Ave, Columbus, OH" } },
  "INC-10245-1": { type: "Incident", label: "Rear-end collision", source: "FNOL Narrative DOC-002", confidence: 0.96, attrs: { "Incident type": "Rear-end collision", Location: "Signalised intersection", "Police called": "Yes", "Liability status": "Disputed by other driver", Weather: "Clear, dry" } },
  "EXP-001": { type: "Exposure", label: "Vehicle Damage", source: "AI extraction + Coverage match", confidence: 0.97, attrs: { "Exposure type": "Collision — Insured vehicle", Claimant: "Daniel Whitaker", Coverage: "Collision", "Reserve": "$8,500" } },
  "EXP-002": { type: "Exposure", label: "Bodily Injury — Passenger 1", source: "AI extraction + Coverage match", confidence: 0.89, attrs: { "Exposure type": "Bodily injury", Claimant: "Elena Whitaker", "Reported injury": "Neck pain, ER visit", Coverage: "Bodily Injury Liability", "Reserve": "$25,000" } },
  "EXP-003": { type: "Exposure", label: "Bodily Injury — Passenger 2", source: "AI extraction + Coverage match", confidence: 0.86, attrs: { "Exposure type": "Bodily injury", Claimant: "Rohan Whitaker", "Reported injury": "Neck pain, no treatment yet", Coverage: "Bodily Injury Liability", "Reserve": "$25,000" } },
  "PTY-001": { type: "Party", label: "Daniel Whitaker (Insured driver)", source: "FNOL Narrative DOC-002", attrs: { Role: "Insured driver", Injured: "No", Statement: "Stopped at red light, struck from behind" } },
  "PTY-002": { type: "Party", label: "Marcus Bell (Other driver)", source: "Police Report DOC-001", confidence: 0.94, attrs: { Role: "Other driver", Injured: "Not reported", Statement: "Claims insured reversed into him" , Represented: "Unknown" } },
  "PTY-003": { type: "Party", label: "Elena Whitaker (Passenger)", source: "FNOL Narrative DOC-002", confidence: 0.93, attrs: { Role: "Passenger — front seat", Injured: "Yes — neck pain", Treatment: "Urgent care, 2026-08-28" } },
  "PTY-004": { type: "Party", label: "Rohan Whitaker (Passenger)", source: "FNOL Narrative DOC-002", confidence: 0.91, attrs: { Role: "Passenger — rear seat", Injured: "Yes — neck pain", Treatment: "None yet", Age: "Minor" } },
  "DOC-001": { type: "Document", label: "Police Report", source: "Columbus PD · Uploaded 2026-08-30", confidence: 0.98, attrs: { "Report #": "CPD-26-118834", Pages: 4, "Fault indicated": "No determination — conflicting statements", "Citations issued": "None" } },
  "DOC-002": { type: "Document", label: "FNOL Narrative", source: "Claim Intake · 2026-08-29", confidence: 0.99, attrs: { Channel: "Mobile app", Length: "312 words", Reporter: "Daniel Whitaker" } },
  "DOC-003": { type: "Document", label: "Medical Document", source: "Urgent care intake · Uploaded 2026-08-31", confidence: 0.92, attrs: { Provider: "Riverside Urgent Care", Patient: "Elena Whitaker", Diagnosis: "Cervical strain (suspected)", "Follow-up": "Referred for imaging" } },
  "DOC-004": { type: "Document", label: "Repair Estimate", source: "Partner body shop · 2026-09-02", confidence: 0.95, attrs: { Shop: "Northgate Collision", Estimate: "$8,412", "Total loss": "No" } },
  "ADJ-207": { type: "Adjuster", label: "Chris Alvarez", source: "Workforce System", attrs: { Team: "Auto intake", Role: "Intake adjuster", Caseload: 42, Region: "Midwest" } },
  "ADJ-114": { type: "Adjuster", label: "Sarah Kim", source: "Workforce System", attrs: { Team: "Bodily Injury", Role: "BI Specialist", Caseload: 18, "Licensed states": "OH, IN, MI" } },
  "ACT-001": { type: "Activity", label: "FNOL received", source: "Claim Intake", attrs: { When: "2026-08-29 09:14", By: "Mobile app", Status: "Complete" } },
  "ACT-002": { type: "Activity", label: "Police report retrieved", source: "Document Ingestion", attrs: { When: "2026-08-30 15:02", By: "System", Status: "Complete" } },
  "ACT-003": { type: "Activity", label: "AI triage generated", source: "ClaimIQ", attrs: { When: "2026-09-02 08:41", By: "ClaimIQ", Status: "Awaiting review" } },
  "RES-001": { type: "Reserve", label: "$8,500", source: "Claim System", attrs: { Exposure: "Vehicle Damage", Set: "2026-09-02", Basis: "Repair estimate + rental" } },
  "RES-002": { type: "Reserve", label: "$25,000", source: "Claim System", attrs: { Exposure: "BI — Passenger 1", Set: "2026-09-02", Basis: "Initial BI reserve guideline" } },
  "RES-003": { type: "Reserve", label: "$25,000", source: "Claim System", attrs: { Exposure: "BI — Passenger 2", Set: "2026-09-02", Basis: "Initial BI reserve guideline" } },
  "PAY-001": { type: "Payment", label: "$420 — Rental", source: "Claim System", attrs: { Exposure: "Vehicle Damage", Paid: "2026-09-03", Payee: "Enterprise Rent-A-Car" } },
  "PC-88102": { type: "Previous Claim", label: "PC-88102 · Hail damage", source: "Claim History", attrs: { "Loss date": "2023-06-14", Type: "Comprehensive", Paid: "$3,120", Status: "Closed" } },
  "PC-91230": { type: "Previous Claim", label: "PC-91230 · Rear-end (minor)", source: "Claim History", attrs: { "Loss date": "2025-02-02", Type: "Collision", Paid: "$2,760", "BI exposure": "None", Status: "Closed" } },
};

const EDGES = [
  ["CUST-55021", "OWNS", "POL-78321"],
  ["POL-78321", "HAS", "COV-COLL"],
  ["POL-78321", "HAS", "COV-BI"],
  ["POL-78321", "HAS", "COV-PD"],
  ["POL-78321", "COVERS", "VEH-4471"],
  ["POL-78321", "HAS", "CC-10245"],
  ["CC-10245", "HAS", "INC-10245-1"],
  ["CC-10245", "HAS", "EXP-001"],
  ["CC-10245", "HAS", "EXP-002"],
  ["CC-10245", "HAS", "EXP-003"],
  ["CC-10245", "INVOLVES", "PTY-001"],
  ["CC-10245", "INVOLVES", "PTY-002"],
  ["CC-10245", "INVOLVES", "PTY-003"],
  ["CC-10245", "INVOLVES", "PTY-004"],
  ["CC-10245", "INVOLVES", "VEH-4471"],
  ["CC-10245", "INVOLVES", "VEH-9082"],
  ["CC-10245", "HAS", "DOC-001"],
  ["CC-10245", "HAS", "DOC-002"],
  ["CC-10245", "HAS", "DOC-003"],
  ["CC-10245", "HAS", "DOC-004"],
  ["CC-10245", "ASSIGNED TO", "ADJ-207"],
  ["CC-10245", "HAS", "ACT-001"],
  ["CC-10245", "HAS", "ACT-002"],
  ["CC-10245", "HAS", "ACT-003"],
  ["EXP-001", "HAS", "RES-001"],
  ["EXP-002", "HAS", "RES-002"],
  ["EXP-003", "HAS", "RES-003"],
  ["EXP-001", "HAS", "PAY-001"],
  ["EXP-001", "RELATES TO", "COV-COLL"],
  ["EXP-002", "RELATES TO", "COV-BI"],
  ["EXP-003", "RELATES TO", "COV-BI"],
  ["CUST-55021", "HAS", "PC-88102"],
  ["CUST-55021", "HAS", "PC-91230"],
  ["DOC-001", "SUPPORTS", "CC-10245"],
  ["DOC-001", "REFERENCES", "PTY-002"],
  ["DOC-001", "REFERENCES", "PTY-001"],
  ["DOC-003", "REFERENCES", "PTY-003"],
  ["DOC-002", "REFERENCES", "PTY-003"],
  ["DOC-002", "REFERENCES", "PTY-004"],
  ["INC-10245-1", "INVOLVES", "VEH-4471"],
  ["INC-10245-1", "INVOLVES", "VEH-9082"],
  ["INC-10245-1", "INVOLVES", "PTY-002"],
  ["EXP-002", "RELATES TO", "PTY-003"],
  ["EXP-003", "RELATES TO", "PTY-004"],
];

const REL_TYPES = [...new Set(EDGES.map(e => e[1]))];

function pathBetween(from, to) {
  const prev = { [from]: null };
  const q = [from];
  while (q.length) {
    const cur = q.shift();
    if (cur === to) break;
    neighborsOf(cur).forEach(({ id }) => { if (prev[id] === undefined) { prev[id] = cur; q.push(id); } });
  }
  if (prev[to] === undefined) return [to];
  const path = [];
  for (let n = to; n !== null; n = prev[n]) path.push(n);
  return path;
}

function neighborsOf(id) {
  const out = [];
  EDGES.forEach(([a, r, b]) => {
    if (a === id) out.push({ id: b, rel: r, dir: "out" });
    else if (b === id) out.push({ id: a, rel: r, dir: "in" });
  });
  return out;
}

/* ------------------------------------------------------------------ */
/* CLAIM QUEUE (simulated)                                             */
/* ------------------------------------------------------------------ */

const CLAIMS = [
  { id: "CC-10245", insured: "Daniel Whitaker", policy: "POL-78321", type: "Auto · Collision", loss: "2026-08-28", state: "OH", severity: "HIGH", complexity: "HIGH", priority: "P1", handler: "Bodily Injury Specialist", confidence: 91, status: "Awaiting review", reserve: 58500 },
  { id: "CC-10251", insured: "Marta Okafor", policy: "POL-80114", type: "Auto · Glass", loss: "2026-09-04", state: "IN", severity: "LOW", complexity: "LOW", priority: "P4", handler: "Fast-track glass", confidence: 97, status: "Auto-routed (eligible)", reserve: 620 },
  { id: "CC-10248", insured: "Kevin Trask", policy: "POL-79950", type: "Auto · Theft", loss: "2026-09-01", state: "MI", severity: "MEDIUM", complexity: "MEDIUM", priority: "P2", handler: "SIU referral review", confidence: 74, status: "Awaiting review", reserve: 21000 },
  { id: "CC-10239", insured: "Lena Fischer", policy: "POL-77602", type: "Auto · Collision", loss: "2026-08-25", state: "OH", severity: "MEDIUM", complexity: "LOW", priority: "P3", handler: "General auto adjuster", confidence: 88, status: "Approved by adjuster", reserve: 6200 },
  { id: "CC-10233", insured: "Ravi Menon", policy: "POL-76118", type: "Auto · Comprehensive", loss: "2026-08-22", state: "IL", severity: "LOW", complexity: "LOW", priority: "P4", handler: "Fast-track auto", confidence: 95, status: "Approved by adjuster", reserve: 1850 },
  { id: "CC-10229", insured: "Grace Lindqvist", policy: "POL-75407", type: "Auto · Collision", loss: "2026-08-20", state: "IN", severity: "HIGH", complexity: "MEDIUM", priority: "P1", handler: "Bodily Injury Specialist", confidence: 83, status: "Overridden by adjuster", reserve: 41000 },
];

const CLAIM_CONTEXT = {
  facts: [
    { fact: "Accident type", value: "Rear-end collision", source: "FNOL Narrative", doc: "DOC-002", conf: 0.96 },
    { fact: "Potential bodily injury", value: "Yes", source: "FNOL + Medical Document", doc: "DOC-003", conf: 0.93 },
    { fact: "Injured parties", value: "2", source: "FNOL Narrative", doc: "DOC-002", conf: 0.91 },
    { fact: "Liability", value: "Disputed", source: "Police Report", doc: "DOC-001", conf: 0.94 },
    { fact: "Police involvement", value: "Yes", source: "Police Report", doc: "DOC-001", conf: 0.98 },
    { fact: "Vehicles involved", value: "2", source: "Police Report", doc: "DOC-001", conf: 0.97 },
  ],
  reasons: [
    { title: "Multiple potential bodily injury exposures", weight: 0.31, entities: ["EXP-002", "EXP-003", "DOC-003"], note: "Two BI exposures opened against the Bodily Injury Liability coverage. One has medical documentation with imaging referral." },
    { title: "Liability is disputed", weight: 0.24, entities: ["INC-10245-1", "PTY-002", "DOC-001"], note: "Police report records conflicting statements with no fault determination. The other driver disputes the insured's account." },
    { title: "Multiple claimants", weight: 0.18, entities: ["CC-10245", "PTY-002", "PTY-003", "PTY-004"], note: "Three non-insured parties are connected to the claim, one of whom is a minor." },
    { title: "Police involvement", weight: 0.13, entities: ["DOC-001", "INC-10245-1"], note: "A police report exists and was retrieved. Its presence correlates with higher-severity outcomes in the historical claims segment." },
    { title: "Prior related claims", weight: 0.14, entities: ["CUST-55021", "PC-91230", "PC-88102"], note: "The customer has two prior claims, including a 2025 rear-end collision on the same policy." },
  ],
  questions: {
    "Why does this claim require specialist review?": {
      answer: "Specialist review is recommended because the claim carries two open bodily injury exposures with a disputed liability position and three third-party claimants, one of whom is a minor. The claims-handling guideline directs any claim with more than one BI claimant and a contested liability position to the Bodily Injury team. Medical documentation already shows a suspected cervical strain with an imaging referral, which the guideline treats as a soft-tissue injury with escalation potential.",
      graph: ["EXP-002", "EXP-003", "INC-10245-1", "PTY-002", "PTY-003", "PTY-004", "PC-91230"],
      rag: [
        { title: "Claims-handling guideline CH-4.2 · BI assignment thresholds", excerpt: "Claims with two or more bodily injury claimants, or any BI claimant where liability is contested, are assigned to the Bodily Injury team on intake.", kind: "Guideline" },
        { title: "Police Report CPD-26-118834 · p.2", excerpt: "Driver 2 states Driver 1 reversed into his vehicle at the light. No independent witnesses. No fault determination made at scene.", kind: "Document" },
        { title: "FNOL Narrative · reporter statement", excerpt: "…my daughter and son in the back both said their necks hurt. We were stopped at the red light when the truck hit us.", kind: "Document" },
        { title: "Urgent care intake · Elena Whitaker", excerpt: "Assessment: cervical strain, suspected. Plan: NSAIDs, referred for cervical imaging within 7 days.", kind: "Document" },
      ],
    },
    "Which coverage responds to the passenger injuries?": {
      answer: "The passenger injury exposures are mapped to the Bodily Injury Liability coverage on POL-78321 (limit $100,000 per person / $300,000 per accident). Because liability is disputed, whether this coverage ultimately responds — versus the other driver's carrier — depends on the fault determination. Medical Payments coverage is not present on this policy, which the guideline flags as a coverage gap to communicate to the insured.",
      graph: ["COV-BI", "EXP-002", "EXP-003", "POL-78321", "INC-10245-1"],
      rag: [
        { title: "Policy POL-78321 · Declarations page", excerpt: "Bodily Injury Liability 100/300. Property Damage 50. Collision ACV, $500 deductible. Medical Payments: not selected.", kind: "Document" },
        { title: "Claims-handling guideline CH-2.7 · Passenger injuries", excerpt: "Where passengers of the insured vehicle are injured and fault is undetermined, open BI exposures under the insured's policy and pursue subrogation review in parallel.", kind: "Guideline" },
      ],
    },
    "Is there a fraud or SIU signal?": {
      answer: "No SIU referral is recommended at this time. The graph shows a prior rear-end claim in 2025, but it had no bodily injury exposure and was closed with a modest payment, which the SIU guideline does not treat as a pattern on its own. The medical documentation is from a licensed urgent care provider and predates any attorney involvement. The claim is flagged for a routine subrogation review rather than an SIU referral.",
      graph: ["PC-91230", "PC-88102", "DOC-003", "PTY-002"],
      rag: [
        { title: "SIU referral guideline SIU-1.3", excerpt: "A single prior collision claim without injury exposure is not a referral trigger. Refer when two or more injury claims occur within 24 months or when treatment is obtained only after attorney contact.", kind: "Guideline" },
        { title: "Claim history · PC-91230", excerpt: "Minor rear-end, bumper replacement, no injuries reported, closed in 19 days.", kind: "Document" },
      ],
    },
  },
};

/* ------------------------------------------------------------------ */
/* DASHBOARD DATA (simulated demo data)                                */
/* ------------------------------------------------------------------ */

const SEGMENTS = {
  "Claim type": [
    { seg: "Collision", accept: 84, override: 16, recall: 0.94, auto: 22 },
    { seg: "Glass", accept: 97, override: 3, recall: 0.99, auto: 71 },
    { seg: "Comprehensive", accept: 92, override: 8, recall: 0.96, auto: 48 },
    { seg: "Theft", accept: 78, override: 22, recall: 0.9, auto: 6 },
    { seg: "Liability only", accept: 81, override: 19, recall: 0.93, auto: 9 },
  ],
  Severity: [
    { seg: "Low", accept: 95, override: 5, recall: 0.98, auto: 54 },
    { seg: "Medium", accept: 87, override: 13, recall: 0.95, auto: 18 },
    { seg: "High", accept: 79, override: 21, recall: 0.93, auto: 0 },
  ],
  Complexity: [
    { seg: "Low", accept: 94, override: 6, recall: 0.97, auto: 49 },
    { seg: "Medium", accept: 86, override: 14, recall: 0.94, auto: 12 },
    { seg: "High", accept: 76, override: 24, recall: 0.92, auto: 0 },
  ],
  Geography: [
    { seg: "OH", accept: 88, override: 12, recall: 0.95, auto: 27 },
    { seg: "IN", accept: 90, override: 10, recall: 0.96, auto: 31 },
    { seg: "MI", accept: 85, override: 15, recall: 0.93, auto: 22 },
    { seg: "IL", accept: 87, override: 13, recall: 0.94, auto: 25 },
  ],
  "Claim volume": [
    { seg: "< 500 / mo", accept: 83, override: 17, recall: 0.92, auto: 15 },
    { seg: "500–2k / mo", accept: 88, override: 12, recall: 0.95, auto: 26 },
    { seg: "> 2k / mo", accept: 91, override: 9, recall: 0.96, auto: 33 },
  ],
};

const CALIBRATION = [
  { bucket: "50–60", predicted: 55, observed: 52, n: 41 },
  { bucket: "60–70", predicted: 65, observed: 63, n: 118 },
  { bucket: "70–80", predicted: 75, observed: 77, n: 302 },
  { bucket: "80–90", predicted: 85, observed: 86, n: 611 },
  { bucket: "90–100", predicted: 95, observed: 93, n: 728 },
];

const TREND = [
  { wk: "W27", accept: 79, time: 41 }, { wk: "W28", accept: 81, time: 38 }, { wk: "W29", accept: 83, time: 36 },
  { wk: "W30", accept: 84, time: 33 }, { wk: "W31", accept: 86, time: 31 }, { wk: "W32", accept: 87, time: 29 },
  { wk: "W33", accept: 87, time: 28 }, { wk: "W34", accept: 88, time: 27 }, { wk: "W35", accept: 88, time: 26 },
];

/* ------------------------------------------------------------------ */
/* SHARED UI                                                            */
/* ------------------------------------------------------------------ */

const SEV = {
  HIGH: "bg-red-50 text-red-700 border-red-200",
  MEDIUM: "bg-amber-50 text-amber-700 border-amber-200",
  LOW: "bg-emerald-50 text-emerald-700 border-emerald-200",
};

function Tag({ level, children }) {
  return <span className={`inline-flex items-center px-2 py-0.5 rounded border text-xs font-semibold ${SEV[level] || "bg-slate-100 text-slate-700 border-slate-200"}`}>{children || level}</span>;
}

function Card({ title, right, children, className = "", tone }) {
  return (
    <section className={`bg-white border rounded-md ${tone === "graph" ? "border-teal-300" : "border-slate-200"} ${className}`}>
      {(title || right) && (
        <header className={`flex items-center justify-between px-4 py-2.5 border-b ${tone === "graph" ? "border-teal-200 bg-teal-50" : "border-slate-100"}`}>
          <h3 className="text-sm font-semibold text-slate-800 flex items-center gap-2">{title}</h3>
          {right}
        </header>
      )}
      <div className="p-4">{children}</div>
    </section>
  );
}

function TypeDot({ type, size = 10 }) {
  const s = TYPE_STYLE[type] || { color: "#999" };
  return <span className="inline-block rounded-full flex-shrink-0" style={{ width: size, height: size, background: s.color }} />;
}

function EntityChip({ id, onOpen }) {
  const n = NODES[id];
  if (!n) return null;
  return (
    <button onClick={() => onOpen && onOpen(id)} className="inline-flex items-center gap-1.5 px-2 py-1 rounded border border-slate-200 bg-white hover:border-teal-400 hover:bg-teal-50 text-xs text-slate-700 focus:outline-none focus:ring-2 focus:ring-teal-400">
      <TypeDot type={n.type} size={8} />
      <span className="text-slate-500">{n.type}</span>
      <span className="font-medium">{n.label}</span>
    </button>
  );
}

function Btn({ children, variant = "secondary", onClick, disabled, className = "", small }) {
  const base = small ? "px-2.5 py-1 text-xs" : "px-3.5 py-2 text-sm";
  const v = {
    primary: "bg-teal-700 text-white hover:bg-teal-800 border-teal-700",
    secondary: "bg-white text-slate-700 hover:bg-slate-50 border-slate-300",
    danger: "bg-white text-red-700 hover:bg-red-50 border-red-300",
    dark: "bg-slate-900 text-white hover:bg-slate-800 border-slate-900",
  }[variant];
  return (
    <button disabled={disabled} onClick={onClick} className={`${base} rounded border font-medium inline-flex items-center gap-1.5 disabled:opacity-40 disabled:cursor-not-allowed focus:outline-none focus:ring-2 focus:ring-teal-400 ${v} ${className}`}>
      {children}
    </button>
  );
}

/* ------------------------------------------------------------------ */
/* GRAPH LAYOUT                                                         */
/* ------------------------------------------------------------------ */

function layoutGraph(center, visible, hiddenTypes, hiddenRels) {
  const vis = new Set(visible);
  const allowed = (id) => vis.has(id) && !hiddenTypes.has(NODES[id].type);
  // BFS from center over visible edges
  const depth = { [center]: 0 };
  const parent = {};
  const queue = [center];
  const edgesUsed = [];
  while (queue.length) {
    const cur = queue.shift();
    neighborsOf(cur).forEach(({ id, rel }) => {
      if (hiddenRels.has(rel)) return;
      if (!allowed(id)) return;
      if (depth[id] === undefined) {
        depth[id] = depth[cur] + 1;
        parent[id] = cur;
        queue.push(id);
      }
    });
  }
  const nodes = Object.keys(depth);
  const R = [0, 165, 285, 385, 470];
  const pos = { [center]: { x: 0, y: 0, angle: 0 } };
  const maxD = Math.max(...nodes.map(n => depth[n]));
  for (let d = 1; d <= maxD; d++) {
    const layer = nodes.filter(n => depth[n] === d);
    if (d === 1) {
      layer.forEach((n, i) => {
        const a = -Math.PI / 2 + (i * 2 * Math.PI) / layer.length;
        pos[n] = { x: Math.cos(a) * R[d], y: Math.sin(a) * R[d], angle: a };
      });
    } else {
      const byParent = {};
      layer.forEach(n => { (byParent[parent[n]] = byParent[parent[n]] || []).push(n); });
      const parents = Object.keys(byParent);
      // sector per parent, sized by number of children
      const total = layer.length;
      let cursor = 0;
      const sorted = parents.sort((a, b) => pos[a].angle - pos[b].angle);
      // distribute all layer nodes evenly, ordered by parent angle, then rotate to align first parent
      const ordered = sorted.flatMap(p => byParent[p]);
      const step = (2 * Math.PI) / Math.max(total, 4);
      const firstParentAngle = pos[sorted[0]].angle;
      const firstParentCount = byParent[sorted[0]].length;
      const start = firstParentAngle - ((firstParentCount - 1) * step) / 2;
      ordered.forEach((n, i) => {
        const a = start + i * step;
        pos[n] = { x: Math.cos(a) * R[Math.min(d, 4)], y: Math.sin(a) * R[Math.min(d, 4)], angle: a };
        cursor++;
      });
    }
  }
  EDGES.forEach(([a, r, b]) => {
    if (pos[a] && pos[b] && !hiddenRels.has(r)) edgesUsed.push([a, r, b]);
  });
  return { pos, edges: edgesUsed, depth };
}

/* ------------------------------------------------------------------ */
/* KNOWLEDGE GRAPH VIEW                                                 */
/* ------------------------------------------------------------------ */

function GraphView({ focus, setFocus, initialSelected, compact = false, onOpenClaim }) {
  const [visible, setVisible] = useState(() => new Set([focus, ...neighborsOf(focus).map(n => n.id)]));
  const [selected, setSelected] = useState(initialSelected || focus);
  const [hiddenTypes, setHiddenTypes] = useState(new Set());
  const [hiddenRels, setHiddenRels] = useState(new Set());
  const [zoom, setZoom] = useState(compact ? 0.85 : 1);
  const [showLabels, setShowLabels] = useState(true);

  useEffect(() => {
    setVisible(new Set([focus, ...neighborsOf(focus).map(n => n.id)]));
    setSelected(initialSelected || focus);
  }, [focus, initialSelected]);

  useEffect(() => {
    if (initialSelected) {
      setVisible(v => new Set([...v, ...pathBetween(focus, initialSelected)]));
    }
  }, [initialSelected, focus]);

  const { pos, edges, depth } = useMemo(() => layoutGraph(focus, [...visible], hiddenTypes, hiddenRels), [focus, visible, hiddenTypes, hiddenRels]);

  const sel = NODES[selected];
  const selNeighbors = neighborsOf(selected);
  const toggleType = (t) => setHiddenTypes(s => { const n = new Set(s); n.has(t) ? n.delete(t) : n.add(t); return n; });
  const toggleRel = (r) => setHiddenRels(s => { const n = new Set(s); n.has(r) ? n.delete(r) : n.add(r); return n; });
  const addNode = (id) => setVisible(v => new Set([...v, id]));
  const removeNode = (id) => setVisible(v => { const n = new Set(v); if (id !== focus) n.delete(id); return n; });
  const expandAll = (id) => setVisible(v => new Set([...v, ...neighborsOf(id).map(n => n.id)]));
  const isVisible = (id) => pos[id] !== undefined;

  const W = 1000, H = compact ? 520 : 640;
  const cx = W / 2, cy = H / 2;

  const focusOptions = Object.keys(NODES).filter(id => ["Claim", "Policy", "Customer", "Exposure"].includes(NODES[id].type));

  return (
    <div className={`grid ${compact ? "grid-cols-1" : "grid-cols-12"} gap-4`}>
      {/* Filters */}
      {!compact && (
        <aside className="col-span-2 space-y-4">
          <Card title="Focus on">
            <select value={focus} onChange={e => setFocus(e.target.value)} className="w-full text-sm border border-slate-300 rounded px-2 py-1.5 bg-white focus:outline-none focus:ring-2 focus:ring-teal-400">
              {["Claim", "Policy", "Customer", "Exposure"].map(t => (
                <optgroup key={t} label={t}>
                  {focusOptions.filter(id => NODES[id].type === t).map(id => <option key={id} value={id}>{id} — {NODES[id].label}</option>)}
                </optgroup>
              ))}
            </select>
          </Card>
          <Card title="Entity types">
            <ul className="space-y-1">
              {Object.keys(TYPE_STYLE).map(t => (
                <li key={t}>
                  <label className="flex items-center gap-2 text-xs text-slate-700 cursor-pointer">
                    <input type="checkbox" checked={!hiddenTypes.has(t)} onChange={() => toggleType(t)} className="accent-teal-700" />
                    <TypeDot type={t} size={9} /> {t}
                  </label>
                </li>
              ))}
            </ul>
          </Card>
          <Card title="Relationship types">
            <ul className="space-y-1">
              {REL_TYPES.map(r => (
                <li key={r}>
                  <label className="flex items-center gap-2 text-xs text-slate-700 cursor-pointer">
                    <input type="checkbox" checked={!hiddenRels.has(r)} onChange={() => toggleRel(r)} className="accent-teal-700" />
                    <span className="font-mono text-xs">{r}</span>
                  </label>
                </li>
              ))}
            </ul>
          </Card>
        </aside>
      )}

      {/* Canvas */}
      <div className={compact ? "" : "col-span-7"}>
        <div className="bg-white border border-slate-200 rounded-md overflow-hidden">
          <div className="flex items-center justify-between px-3 py-2 border-b border-slate-100 bg-slate-50">
            <div className="text-xs text-slate-600 flex items-center gap-2">
              <Share2 size={14} className="text-teal-700" />
              <span>Centered on <span className="font-semibold text-slate-800">{focus}</span> · {Object.keys(pos).length} entities · {edges.length} relationships shown</span>
            </div>
            <div className="flex items-center gap-1">
              <label className="text-xs text-slate-600 mr-2 flex items-center gap-1"><input type="checkbox" checked={showLabels} onChange={e => setShowLabels(e.target.checked)} className="accent-teal-700" /> Labels</label>
              <Btn small onClick={() => setZoom(z => Math.max(0.5, z - 0.15))}><ZoomOut size={13} /></Btn>
              <Btn small onClick={() => setZoom(z => Math.min(1.8, z + 0.15))}><ZoomIn size={13} /></Btn>
              <Btn small onClick={() => { setZoom(1); setVisible(new Set([focus, ...neighborsOf(focus).map(n => n.id)])); }}><Maximize2 size={13} /> Reset</Btn>
            </div>
          </div>
          <svg viewBox={`0 0 ${W} ${H}`} className="w-full" style={{ height: compact ? 420 : 560, background: "#FAFBFC" }}>
            <defs>
              <marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
                <path d="M 0 0 L 10 5 L 0 10 z" fill="#94A3B8" />
              </marker>
            </defs>
            <g transform={`translate(${cx} ${cy}) scale(${zoom})`}>
              {edges.map(([a, r, b], i) => {
                const pa = pos[a], pb = pos[b];
                const dx = pb.x - pa.x, dy = pb.y - pa.y;
                const len = Math.hypot(dx, dy) || 1;
                const ra = a === focus ? 30 : 20, rb = b === focus ? 30 : 20;
                const x1 = pa.x + (dx / len) * ra, y1 = pa.y + (dy / len) * ra;
                const x2 = pb.x - (dx / len) * (rb + 4), y2 = pb.y - (dy / len) * (rb + 4);
                const hi = a === selected || b === selected;
                return (
                  <g key={i}>
                    <line x1={x1} y1={y1} x2={x2} y2={y2} stroke={hi ? "#0F766E" : "#CBD5E1"} strokeWidth={hi ? 2 : 1.2} markerEnd="url(#arrow)" />
                    {showLabels && (
                      <text x={(x1 + x2) / 2} y={(y1 + y2) / 2 - 4} textAnchor="middle" fontSize="8.5" fill={hi ? "#0F766E" : "#94A3B8"} fontFamily="ui-monospace, SFMono-Regular, Menlo, monospace">{r}</text>
                    )}
                  </g>
                );
              })}
              {Object.keys(pos).map(id => {
                const n = NODES[id]; const p = pos[id]; const s = TYPE_STYLE[n.type];
                const isFocus = id === focus; const isSel = id === selected;
                const r = isFocus ? 30 : 20;
                const unexpanded = neighborsOf(id).some(nb => !isVisible(nb.id) && !hiddenTypes.has(NODES[nb.id].type));
                return (
                  <g key={id} transform={`translate(${p.x} ${p.y})`} onClick={() => setSelected(id)} onDoubleClick={() => expandAll(id)} style={{ cursor: "pointer" }}>
                    {isSel && <circle r={r + 7} fill="none" stroke="#0F766E" strokeWidth="2" strokeDasharray="4 3" />}
                    <circle r={r} fill={s.ring} stroke={s.color} strokeWidth={isFocus ? 3 : 2} />
                    <text textAnchor="middle" dy="4" fontSize={isFocus ? 11 : 9} fontWeight="700" fill={s.color}>{n.type === "Previous Claim" ? "Prev" : n.type.slice(0, isFocus ? 6 : 5)}</text>
                    {showLabels && (
                      <>
                        <text textAnchor="middle" y={r + 13} fontSize="10" fontWeight="600" fill="#1E293B">{n.label.length > 26 ? n.label.slice(0, 24) + "…" : n.label}</text>
                        <text textAnchor="middle" y={r + 24} fontSize="8.5" fill="#64748B">{id}</text>
                      </>
                    )}
                    {unexpanded && <g transform={`translate(${r - 4} ${-r + 4})`}><circle r="7" fill="#0F766E" /><text textAnchor="middle" dy="3" fontSize="10" fontWeight="700" fill="white">+</text></g>}
                  </g>
                );
              })}
            </g>
          </svg>
          <div className="px-3 py-2 border-t border-slate-100 text-xs text-slate-500 flex items-center gap-4">
            <span>Click a node to inspect it. Double-click to expand all its relationships.</span>
            <span className="inline-flex items-center gap-1"><span className="inline-block w-3 h-3 rounded-full bg-teal-700 text-white text-xs leading-3 text-center">+</span> has unexpanded relationships</span>
          </div>
        </div>
      </div>

      {/* Details */}
      <aside className={compact ? "" : "col-span-3"}>
        {sel && (
          <div className="bg-white border border-slate-200 rounded-md">
            <div className="px-4 py-3 border-b border-slate-100">
              <div className="flex items-center gap-2 text-xs text-slate-500"><TypeDot type={sel.type} /> {sel.type}</div>
              <div className="text-base font-semibold text-slate-900 mt-0.5">{sel.label}</div>
              <div className="font-mono text-xs text-slate-500">{selected}</div>
            </div>
            <div className="px-4 py-3 border-b border-slate-100">
              <div className="text-xs font-semibold text-slate-700 mb-2">Attributes</div>
              <dl className="grid grid-cols-2 gap-x-3 gap-y-1.5 text-xs">
                {Object.entries(sel.attrs).map(([k, v]) => (
                  <div key={k} className="contents"><dt className="text-slate-500">{k}</dt><dd className="text-slate-800 font-medium text-right">{String(v)}</dd></div>
                ))}
              </dl>
            </div>
            <div className="px-4 py-3 border-b border-slate-100 grid grid-cols-2 gap-3 text-xs">
              <div><div className="text-slate-500">Source</div><div className="text-slate-800 font-medium">{sel.source}</div></div>
              <div><div className="text-slate-500">Confidence</div>
                <div className="text-slate-800 font-medium">{sel.confidence ? `${Math.round(sel.confidence * 100)}% (extracted)` : "System of record"}</div></div>
            </div>
            <div className="px-4 py-3">
              <div className="flex items-center justify-between mb-2">
                <div className="text-xs font-semibold text-slate-700">Relationships ({selNeighbors.length})</div>
                <Btn small onClick={() => expandAll(selected)}>Expand all</Btn>
              </div>
              <ul className="space-y-1 max-h-72 overflow-auto pr-1">
                {selNeighbors.map(({ id, rel, dir }) => {
                  const shown = isVisible(id);
                  return (
                    <li key={id + rel} className="flex items-center justify-between gap-2 text-xs py-1 border-b border-slate-50">
                      <button onClick={() => { if (shown) setSelected(id); }} className={`flex items-center gap-1.5 text-left ${shown ? "hover:text-teal-700" : "text-slate-400"}`}>
                        <span className="font-mono text-xs text-slate-500 w-20 flex-shrink-0">{dir === "out" ? rel : `◀ ${rel}`}</span>
                        <TypeDot type={NODES[id].type} size={8} />
                        <span className="truncate">{NODES[id].label}</span>
                      </button>
                      {shown ? (
                        id !== focus && <button title="Hide" onClick={() => removeNode(id)} className="text-slate-400 hover:text-red-600"><Minus size={13} /></button>
                      ) : (
                        <button title="Show" onClick={() => addNode(id)} className="text-teal-700 hover:text-teal-900"><Plus size={13} /></button>
                      )}
                    </li>
                  );
                })}
              </ul>
              {sel.type === "Claim" && onOpenClaim && selected !== "PC-88102" && (
                <Btn small className="mt-3 w-full justify-center" onClick={() => onOpenClaim(selected)}><FileText size={13} /> Open claim workspace</Btn>
              )}
              {selected !== focus && ["Claim", "Policy", "Customer", "Exposure"].includes(sel.type) && (
                <Btn small className="mt-2 w-full justify-center" onClick={() => setFocus(selected)}><Share2 size={13} /> Re-center graph here</Btn>
              )}
            </div>
          </div>
        )}
      </aside>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/* CLAIM WORKSPACE                                                      */
/* ------------------------------------------------------------------ */

function ConfidenceBar({ value }) {
  return (
    <div className="flex items-center gap-2">
      <div className="h-1.5 flex-1 bg-slate-100 rounded overflow-hidden"><div className="h-full bg-teal-600" style={{ width: `${value}%` }} /></div>
      <span className="text-xs font-semibold text-slate-700 w-9 text-right">{value}%</span>
    </div>
  );
}

function ClaimWorkspace({ claim, decision, onDecide, openGraph, openEntity }) {
  const [openReason, setOpenReason] = useState(0);
  const [mode, setMode] = useState(null); // null | 'override'
  const [ov, setOv] = useState({ severity: "MEDIUM", complexity: "HIGH", handler: "General auto adjuster", reason: "" });
  const [question, setQuestion] = useState("Why does this claim require specialist review?");
  const [asked, setAsked] = useState(null);
  const [typed, setTyped] = useState("");

  const isMain = claim.id === "CC-10245";
  const qa = asked ? CLAIM_CONTEXT.questions[asked] : null;

  const ask = (q) => {
    const key = Object.keys(CLAIM_CONTEXT.questions).find(k => k.toLowerCase() === q.toLowerCase()) || "Why does this claim require specialist review?";
    setAsked(key); setQuestion(key);
  };

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="bg-white border border-slate-200 rounded-md px-5 py-4">
        <div className="flex items-start justify-between gap-6">
          <div>
            <div className="flex items-center gap-3">
              <h2 className="text-xl font-semibold text-slate-900">Claim {claim.id}</h2>
              <span className="text-xs px-2 py-0.5 rounded bg-slate-100 border border-slate-200 text-slate-700">{decision ? (decision.type === "approve" ? "Approved" : "Overridden") : claim.status}</span>
            </div>
            <p className="text-sm text-slate-600 mt-1 max-w-3xl">
              {isMain ? "Rear-end collision at an intersection. Two passengers report neck pain. The other driver disputes liability. Police were called to the scene." : `${claim.type} loss reported for ${claim.insured}.`}
            </p>
          </div>
          <Btn variant="primary" onClick={() => openGraph(claim.id)}><Share2 size={15} /> Explore in Knowledge Graph</Btn>
        </div>
        <dl className="grid grid-cols-6 gap-4 mt-4 pt-4 border-t border-slate-100 text-sm">
          {[["Claim ID", claim.id], ["Loss date", claim.loss], ["Policy number", claim.policy], ["Claim type", claim.type], ["Location", isMain ? "Main St & 5th Ave, Columbus, OH" : `${claim.state}, US`], ["Claim status", decision ? "Open — Assigned" : "Open — Triage"]].map(([k, v]) => (
            <div key={k}><dt className="text-xs text-slate-500">{k}</dt><dd className="font-medium text-slate-800 mt-0.5">{v}</dd></div>
          ))}
        </dl>
      </div>

      <div className="grid grid-cols-12 gap-4">
        {/* Left column */}
        <div className="col-span-8 space-y-4">
          <Card title={<><Sparkles size={15} className="text-teal-700" /> AI summary</>} right={<span className="text-xs text-slate-500">Generated from FNOL, police report, medical intake and graph context</span>}>
            <p className="text-sm text-slate-700 leading-relaxed">
              {isMain
                ? "On 28 Aug 2026 the insured's 2024 Honda Accord was struck from behind by a 2019 Ford F-150 while stopped at a signalised intersection in Columbus, OH. Two passengers — the insured's daughter (front seat) and son (rear seat, a minor) — reported neck pain; the daughter was seen at urgent care the same day with a suspected cervical strain and an imaging referral. The other driver disputes fault and told police the insured reversed into him; no fault determination was made at the scene. The policy carries Collision and 100/300 Bodily Injury Liability. Three exposures are open (vehicle damage and two BI). The customer has two prior claims, including a minor rear-end collision in 2025 with no injury exposure."
                : "Simulated summary. Select claim CC-10245 for the full demo scenario."}
            </p>
          </Card>

          <Card title="Extracted facts" right={<span className="text-xs text-slate-500">Each fact links to its source document</span>}>
            <table className="w-full text-sm">
              <thead><tr className="text-xs text-slate-500 text-left border-b border-slate-100"><th className="py-1.5 font-medium">Fact</th><th className="font-medium">Value</th><th className="font-medium">Source</th><th className="font-medium w-36">Extraction confidence</th></tr></thead>
              <tbody>
                {CLAIM_CONTEXT.facts.map(f => (
                  <tr key={f.fact} className="border-b border-slate-50">
                    <td className="py-2 text-slate-600">{f.fact}</td>
                    <td className="font-semibold text-slate-900">{f.value}</td>
                    <td><button onClick={() => openEntity(f.doc)} className="inline-flex items-center gap-1 text-xs text-teal-700 hover:underline"><FileSearch size={12} /> {f.source}</button></td>
                    <td><ConfidenceBar value={Math.round(f.conf * 100)} /></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </Card>

          {/* KNOWLEDGE GRAPH CONTEXT */}
          <Card tone="graph" title={<><Share2 size={15} className="text-teal-700" /> Knowledge Graph context</>} right={<Btn small variant="primary" onClick={() => openGraph(claim.id)}>Explore in Knowledge Graph <ChevronRight size={13} /></Btn>}>
            <p className="text-xs text-slate-600 mb-3">Entities retrieved from the graph that influenced the AI assessment. Click any entity to inspect it in the graph.</p>
            <div className="grid grid-cols-3 gap-x-6 gap-y-4 text-sm">
              {[
                ["Policy", ["POL-78321"]],
                ["Coverage", ["COV-COLL", "COV-BI", "COV-PD"]],
                ["Vehicle", ["VEH-4471", "VEH-9082"]],
                ["Previous claims (2)", ["PC-91230", "PC-88102"]],
                ["Current exposures", ["EXP-001", "EXP-002", "EXP-003"]],
                ["Documents", ["DOC-001", "DOC-002", "DOC-003", "DOC-004"]],
                ["Parties", ["PTY-001", "PTY-002", "PTY-003", "PTY-004"]],
                ["Reserves", ["RES-001", "RES-002", "RES-003"]],
                ["Adjuster (current)", ["ADJ-207"]],
              ].map(([grp, ids]) => (
                <div key={grp}>
                  <div className="text-xs font-semibold text-slate-700 mb-1.5">{grp}</div>
                  <div className="flex flex-wrap gap-1.5">{ids.map(id => <EntityChip key={id} id={id} onOpen={openEntity} />)}</div>
                </div>
              ))}
            </div>
          </Card>

          {/* EXPLAINABILITY */}
          <Card title={<><Info size={15} className="text-teal-700" /> Why this recommendation?</>}>
            <div className="grid grid-cols-12 gap-4">
              <ul className="col-span-5 space-y-1">
                {CLAIM_CONTEXT.reasons.map((r, i) => (
                  <li key={r.title}>
                    <button onClick={() => setOpenReason(i)} className={`w-full text-left px-3 py-2 rounded border text-sm flex items-center justify-between gap-2 ${openReason === i ? "border-teal-400 bg-teal-50 text-slate-900" : "border-slate-200 hover:bg-slate-50 text-slate-700"}`}>
                      <span>{r.title}</span>
                      <span className="text-xs text-slate-500 flex-shrink-0">{Math.round(r.weight * 100)}%</span>
                    </button>
                  </li>
                ))}
                <li className="text-xs text-slate-500 px-1 pt-1">Percentages are relative contribution to the severity score, not probabilities.</li>
              </ul>
              <div className="col-span-7 border-l border-slate-100 pl-4">
                <div className="text-sm font-semibold text-slate-900">{CLAIM_CONTEXT.reasons[openReason].title}</div>
                <p className="text-sm text-slate-600 mt-1">{CLAIM_CONTEXT.reasons[openReason].note}</p>
                <div className="text-xs font-semibold text-slate-700 mt-3 mb-1.5">Grounded in these graph entities and sources</div>
                <div className="flex flex-col gap-1.5">
                  {CLAIM_CONTEXT.reasons[openReason].entities.map((id, i) => (
                    <div key={id} className="flex items-center gap-2"><span className="text-slate-400 text-xs">→</span><EntityChip id={id} onOpen={openEntity} /></div>
                  ))}
                </div>
              </div>
            </div>
          </Card>

          {/* RAG + KG */}
          <Card title={<><MessageSquare size={15} className="text-teal-700" /> Ask ClaimIQ</>} right={<span className="text-xs text-slate-500">Graph answers who / what / how connected. Retrieval answers what documents and guidelines say.</span>}>
            <div className="flex gap-2">
              <input value={typed || question} onChange={e => { setTyped(e.target.value); }} onKeyDown={e => { if (e.key === "Enter") { ask(typed || question); setTyped(""); } }}
                className="flex-1 border border-slate-300 rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-teal-400" />
              <Btn variant="primary" onClick={() => { ask(typed || question); setTyped(""); }}><Send size={14} /> Ask</Btn>
            </div>
            <div className="flex flex-wrap gap-1.5 mt-2">
              {Object.keys(CLAIM_CONTEXT.questions).map(q => <button key={q} onClick={() => ask(q)} className="text-xs px-2 py-1 rounded-full border border-slate-200 text-slate-600 hover:border-teal-400 hover:text-teal-800">{q}</button>)}
            </div>
            {qa && (
              <div className="mt-4 grid grid-cols-12 gap-4">
                <div className="col-span-12">
                  <div className="text-xs font-semibold text-slate-500 mb-1">Grounded answer</div>
                  <p className="text-sm text-slate-800 leading-relaxed bg-slate-50 border border-slate-200 rounded p-3">{qa.answer}</p>
                </div>
                <div className="col-span-5">
                  <div className="text-xs font-semibold text-teal-800 mb-1.5 flex items-center gap-1"><Share2 size={12} /> Knowledge graph evidence</div>
                  <div className="flex flex-col gap-1.5">{qa.graph.map(id => <EntityChip key={id} id={id} onOpen={openEntity} />)}</div>
                </div>
                <div className="col-span-7">
                  <div className="text-xs font-semibold text-indigo-800 mb-1.5 flex items-center gap-1"><FileSearch size={12} /> Retrieved documents and guidelines</div>
                  <ul className="space-y-1.5">
                    {qa.rag.map(r => (
                      <li key={r.title} className="border border-slate-200 rounded p-2.5 bg-white">
                        <div className="flex items-center justify-between"><span className="text-xs font-semibold text-slate-800">{r.title}</span><span className={`text-xs px-1.5 py-0.5 rounded ${r.kind === "Guideline" ? "bg-indigo-50 text-indigo-700" : "bg-slate-100 text-slate-600"}`}>{r.kind}</span></div>
                        <p className="text-xs text-slate-600 mt-1 italic">“{r.excerpt}”</p>
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            )}
          </Card>
        </div>

        {/* Right column */}
        <div className="col-span-4 space-y-4">
          <Card title={<><Sparkles size={15} className="text-teal-700" /> AI triage recommendation</>}>
            <dl className="space-y-3 text-sm">
              <div className="flex items-center justify-between"><dt className="text-slate-500">Severity</dt><dd><Tag level={claim.severity} /></dd></div>
              <div className="flex items-center justify-between"><dt className="text-slate-500">Complexity</dt><dd><Tag level={claim.complexity} /></dd></div>
              <div className="flex items-center justify-between"><dt className="text-slate-500">Priority</dt><dd className="font-semibold text-slate-900">{claim.priority}</dd></div>
              <div className="flex items-center justify-between"><dt className="text-slate-500">Recommended handler</dt><dd className="font-semibold text-slate-900 text-right">{claim.handler}</dd></div>
              <div><dt className="text-slate-500 mb-1">AI confidence</dt><dd><ConfidenceBar value={claim.confidence} /></dd></div>
            </dl>
            <p className="text-xs text-slate-500 mt-3 border-t border-slate-100 pt-2">Confidence reflects how consistent this claim is with validated historical triage outcomes in its segment. It is not a guarantee of correctness — the adjuster remains the decision-maker.</p>
          </Card>

          <Card title="Inputs consumed by the triage engine">
            <ul className="text-xs text-slate-700 space-y-1.5">
              <li className="flex gap-2"><Share2 size={13} className="text-teal-700 mt-0.5" /> Graph context: 27 entities, 44 relationships within 2 hops of the claim</li>
              <li className="flex gap-2"><FileSearch size={13} className="text-indigo-700 mt-0.5" /> Document evidence: 4 documents, 6 extracted facts</li>
              <li className="flex gap-2"><ShieldCheck size={13} className="text-slate-600 mt-0.5" /> Rules: 3 guideline thresholds evaluated (CH-4.2, CH-2.7, SIU-1.3)</li>
              <li className="flex gap-2"><BarChart3 size={13} className="text-slate-600 mt-0.5" /> ML: severity model v2.3, complexity model v1.8 (segment: Collision · Midwest)</li>
            </ul>
          </Card>

          {/* HUMAN IN THE LOOP */}
          <Card title={<><Users size={15} className="text-teal-700" /> Adjuster decision</>}>
            {decision ? (
              <div className="text-sm">
                <div className={`flex items-center gap-2 font-semibold ${decision.type === "approve" ? "text-emerald-700" : "text-amber-700"}`}>
                  {decision.type === "approve" ? <CheckCircle2 size={16} /> : <AlertTriangle size={16} />}
                  {decision.type === "approve" ? "Recommendation approved" : "Recommendation overridden"}
                </div>
                <div className="mt-3 text-xs space-y-2">
                  <div className="grid grid-cols-3 gap-2">
                    <div className="border border-slate-200 rounded p-2"><div className="text-slate-500">AI recommendation</div><div className="font-medium mt-1">{claim.severity} / {claim.complexity}</div><div className="text-slate-600">{claim.handler}</div></div>
                    <div className="border border-slate-200 rounded p-2"><div className="text-slate-500">Human decision</div><div className="font-medium mt-1">{decision.severity} / {decision.complexity}</div><div className="text-slate-600">{decision.handler}</div></div>
                    <div className="border border-slate-200 rounded p-2"><div className="text-slate-500">Outcome</div><div className="font-medium mt-1">Routed</div><div className="text-slate-600">Feedback logged</div></div>
                  </div>
                  {decision.reason && <div className="text-slate-600">Reason: {decision.reason}</div>}
                  <div className="text-slate-500">Recorded {decision.at} by Chris Alvarez (ADJ-207). This decision feeds the evaluation loop and the performance dashboard.</div>
                </div>
              </div>
            ) : mode === "override" ? (
              <div className="space-y-3 text-sm">
                <div className="grid grid-cols-2 gap-3">
                  <label className="text-xs text-slate-600">New severity
                    <select value={ov.severity} onChange={e => setOv({ ...ov, severity: e.target.value })} className="mt-1 w-full border border-slate-300 rounded px-2 py-1.5 text-sm bg-white">{["LOW", "MEDIUM", "HIGH"].map(s => <option key={s}>{s}</option>)}</select></label>
                  <label className="text-xs text-slate-600">New complexity
                    <select value={ov.complexity} onChange={e => setOv({ ...ov, complexity: e.target.value })} className="mt-1 w-full border border-slate-300 rounded px-2 py-1.5 text-sm bg-white">{["LOW", "MEDIUM", "HIGH"].map(s => <option key={s}>{s}</option>)}</select></label>
                </div>
                <label className="text-xs text-slate-600 block">New assignment
                  <select value={ov.handler} onChange={e => setOv({ ...ov, handler: e.target.value })} className="mt-1 w-full border border-slate-300 rounded px-2 py-1.5 text-sm bg-white">{["Bodily Injury Specialist", "General auto adjuster", "Litigation specialist", "SIU referral review", "Fast-track auto"].map(s => <option key={s}>{s}</option>)}</select></label>
                <label className="text-xs text-slate-600 block">Reason for override
                  <textarea value={ov.reason} onChange={e => setOv({ ...ov, reason: e.target.value })} rows={3} placeholder="e.g. Passenger 2 has no treatment on file; downgrade until medical records arrive." className="mt-1 w-full border border-slate-300 rounded px-2 py-1.5 text-sm" /></label>
                <div className="flex gap-2">
                  <Btn variant="dark" disabled={!ov.reason.trim()} onClick={() => { onDecide({ type: "override", ...ov }); setMode(null); }}>Record override</Btn>
                  <Btn onClick={() => setMode(null)}>Cancel</Btn>
                </div>
              </div>
            ) : (
              <div className="space-y-2">
                <Btn variant="primary" className="w-full justify-center" onClick={() => onDecide({ type: "approve", severity: claim.severity, complexity: claim.complexity, handler: claim.handler, reason: "" })}><CheckCircle2 size={15} /> Approve recommendation</Btn>
                <Btn className="w-full justify-center" onClick={() => setMode("override")}><XCircle size={15} /> Override recommendation</Btn>
                <p className="text-xs text-slate-500 pt-1">Every approval or override is stored as labelled feedback: AI recommendation → human decision → outcome.</p>
              </div>
            )}
          </Card>

          <Card title="Activity">
            <ol className="text-xs space-y-2">
              {["ACT-001", "ACT-002", "ACT-003"].map(id => (
                <li key={id} className="flex gap-2"><span className="text-slate-400 font-mono w-24 flex-shrink-0">{NODES[id].attrs.When}</span><span className="text-slate-700">{NODES[id].label} <span className="text-slate-400">· {NODES[id].attrs.By}</span></span></li>
              ))}
              {decision && <li className="flex gap-2"><span className="text-slate-400 font-mono w-24 flex-shrink-0">{decision.at}</span><span className="text-slate-700">Adjuster {decision.type === "approve" ? "approved" : "overrode"} triage <span className="text-slate-400">· Chris Alvarez</span></span></li>}
            </ol>
          </Card>
        </div>
      </div>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/* CLAIMS LIST                                                          */
/* ------------------------------------------------------------------ */

function ClaimsList({ onOpen, decisions }) {
  const [q, setQ] = useState("");
  const rows = CLAIMS.filter(c => !q || c.id.toLowerCase().includes(q.toLowerCase()) || c.insured.toLowerCase().includes(q.toLowerCase()));
  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-semibold text-slate-900">Triage queue</h2>
          <p className="text-sm text-slate-600">Claims awaiting adjuster review, ranked by AI priority. ClaimCenter-style simulated data.</p>
        </div>
        <div className="relative"><Search size={14} className="absolute left-2.5 top-2.5 text-slate-400" /><input value={q} onChange={e => setQ(e.target.value)} placeholder="Search claim or insured" className="pl-8 pr-3 py-2 text-sm border border-slate-300 rounded w-64 focus:outline-none focus:ring-2 focus:ring-teal-400" /></div>
      </div>
      <div className="bg-white border border-slate-200 rounded-md overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-slate-50 text-xs text-slate-500 text-left"><tr>
            {["Claim", "Insured", "Type", "Loss date", "State", "Severity", "Complexity", "Priority", "Recommended handler", "AI confidence", "Status", ""].map(h => <th key={h} className="px-3 py-2 font-medium">{h}</th>)}
          </tr></thead>
          <tbody>
            {rows.map(c => {
              const d = decisions[c.id];
              return (
                <tr key={c.id} className="border-t border-slate-100 hover:bg-slate-50 cursor-pointer" onClick={() => onOpen(c.id)}>
                  <td className="px-3 py-2.5 font-mono font-medium text-slate-900">{c.id}</td>
                  <td className="px-3 py-2.5">{c.insured}</td>
                  <td className="px-3 py-2.5 text-slate-600">{c.type}</td>
                  <td className="px-3 py-2.5 text-slate-600">{c.loss}</td>
                  <td className="px-3 py-2.5 text-slate-600">{c.state}</td>
                  <td className="px-3 py-2.5"><Tag level={c.severity} /></td>
                  <td className="px-3 py-2.5"><Tag level={c.complexity} /></td>
                  <td className="px-3 py-2.5 font-semibold">{c.priority}</td>
                  <td className="px-3 py-2.5 text-slate-700">{c.handler}</td>
                  <td className="px-3 py-2.5 w-32"><ConfidenceBar value={c.confidence} /></td>
                  <td className="px-3 py-2.5 text-xs text-slate-600">{d ? (d.type === "approve" ? "Approved by adjuster" : "Overridden by adjuster") : c.status}</td>
                  <td className="px-3 py-2.5 text-slate-400"><ChevronRight size={15} /></td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/* OVERVIEW                                                             */
/* ------------------------------------------------------------------ */

const DEMO_STEPS = [
  ["Claim arrives", "FNOL submitted via mobile app", "Claim Intake"],
  ["AI ingests FNOL and documents", "Police report, medical intake, repair estimate", "Data Ingestion"],
  ["Entities and relationships created", "27 entities, 44 relationships resolved into the graph", "Entity Resolution → Knowledge Graph"],
  ["AI retrieves graph context", "2-hop neighbourhood of CC-10245", "Knowledge Graph"],
  ["AI combines graph context with document evidence", "Rules + ML + LLM + RAG", "AI Orchestration"],
  ["AI produces summary, severity, complexity, assignment, confidence", "HIGH / HIGH / P1 / BI Specialist / 91%", "Confidence Engine"],
  ["AI explains the recommendation", "5 reasons, each linked to graph entities and sources", "Decision Layer"],
  ["Adjuster explores the graph and reviews evidence", "Interactive graph + evidence panels", "Human Adjuster"],
  ["Adjuster approves or overrides", "Decision recorded as labelled feedback", "Feedback Loop"],
  ["Dashboard reflects the decision", "Segment eligibility for automation updated", "AI Performance"],
];

function Overview({ go, decisions }) {
  const total = CLAIMS.length;
  const decided = Object.keys(decisions).length;
  return (
    <div className="space-y-5">
      <div className="flex items-end justify-between">
        <div>
          <h2 className="text-xl font-semibold text-slate-900">Claims triage overview</h2>
          <p className="text-sm text-slate-600">Knowledge graph → context → AI analysis → confidence → human review → feedback → progressive automation</p>
        </div>
        <span className="text-xs px-2 py-1 rounded bg-amber-50 border border-amber-200 text-amber-800">Demo data · Guidewire-compatible conceptual architecture</span>
      </div>

      <div className="grid grid-cols-5 gap-3">
        {[
          ["Claims in triage queue", total - decided, "awaiting adjuster review"],
          ["P1 claims", CLAIMS.filter(c => c.priority === "P1").length, "high severity, needs specialist"],
          ["Recommendation acceptance", "88%", "trailing 30 days"],
          ["Median triage time", "26 min", "down from 41 min in W27"],
          ["Automation-eligible", "24%", "validated low-risk segments"],
        ].map(([k, v, s]) => (
          <div key={k} className="bg-white border border-slate-200 rounded-md px-4 py-3">
            <div className="text-xs text-slate-500">{k}</div>
            <div className="text-2xl font-semibold text-slate-900 mt-1">{v}</div>
            <div className="text-xs text-slate-500">{s}</div>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-12 gap-4">
        <div className="col-span-7">
          <Card title="Featured claim · CC-10245" right={<Btn small variant="primary" onClick={() => go("claims", "CC-10245")}>Open workspace <ChevronRight size={13} /></Btn>}>
            <p className="text-sm text-slate-700">Rear-end collision at an intersection. Two passengers report neck pain. The other driver disputes liability. Police were called to the scene.</p>
            <div className="grid grid-cols-4 gap-3 mt-3 text-sm">
              <div><div className="text-xs text-slate-500">Severity</div><Tag level="HIGH" /></div>
              <div><div className="text-xs text-slate-500">Complexity</div><Tag level="HIGH" /></div>
              <div><div className="text-xs text-slate-500">Priority</div><div className="font-semibold">P1</div></div>
              <div><div className="text-xs text-slate-500">Recommended handler</div><div className="font-semibold">BI Specialist</div></div>
            </div>
            <div className="mt-3 pt-3 border-t border-slate-100 flex items-center justify-between">
              <span className="text-xs text-slate-600">Graph context: 27 entities · 3 exposures · 4 parties · 4 documents · 2 prior claims</span>
              <Btn small onClick={() => go("graph", "CC-10245")}><Share2 size={13} /> View in graph</Btn>
            </div>
          </Card>
        </div>
        <div className="col-span-5">
          <Card title="Where the knowledge graph sits" tone="graph">
            <p className="text-xs text-slate-600 mb-3">The graph is the contextual layer every AI component reads from. It answers who and what are connected; retrieval answers what documents and guidelines say.</p>
            <div className="flex flex-col items-center gap-1 text-xs">
              {["Claim intake & documents", "Entity resolution"].map(s => <div key={s} className="w-full text-center border border-slate-200 rounded py-1.5 bg-slate-50 text-slate-700">{s}</div>)}
              <ArrowDown size={14} className="text-slate-400" />
              <div className="w-full text-center border-2 border-teal-500 rounded py-2 bg-teal-50 text-teal-900 font-semibold">Knowledge Graph — shared context</div>
              <ArrowDown size={14} className="text-slate-400" />
              <div className="w-full grid grid-cols-4 gap-1">{["Rules", "ML", "LLM", "RAG"].map(s => <div key={s} className="text-center border border-slate-200 rounded py-1.5 bg-white text-slate-700">{s}</div>)}</div>
              <ArrowDown size={14} className="text-slate-400" />
              <div className="w-full text-center border border-slate-200 rounded py-1.5 bg-slate-50 text-slate-700">Confidence → Decision → Adjuster → Feedback</div>
            </div>
            <Btn small className="mt-3 w-full justify-center" onClick={() => go("architecture")}><Layers size={13} /> Full architecture view</Btn>
          </Card>
        </div>
      </div>

      <Card title="End-to-end demo flow" right={<span className="text-xs text-slate-500">Each step maps to a screen in this prototype</span>}>
        <ol className="grid grid-cols-5 gap-2">
          {DEMO_STEPS.map(([t, d, layer], i) => (
            <li key={t} className="border border-slate-200 rounded p-2.5 bg-slate-50">
              <div className="text-xs text-teal-800 font-semibold">{i + 1}. {layer}</div>
              <div className="text-xs font-medium text-slate-900 mt-1">{t}</div>
              <div className="text-xs text-slate-500 mt-0.5">{d}</div>
            </li>
          ))}
        </ol>
      </Card>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/* ARCHITECTURE                                                         */
/* ------------------------------------------------------------------ */

function Box({ children, sub, strong, wide }) {
  return (
    <div className={`rounded border text-center px-4 py-3 ${strong ? "border-2 border-teal-500 bg-teal-50" : "border-slate-300 bg-white"} ${wide ? "w-full" : "w-80"}`}>
      <div className={`text-sm font-semibold ${strong ? "text-teal-900" : "text-slate-900"}`}>{children}</div>
      {sub && <div className={`text-xs mt-0.5 ${strong ? "text-teal-800" : "text-slate-500"}`}>{sub}</div>}
    </div>
  );
}

function Architecture() {
  const Arrow = () => <ArrowDown size={18} className="text-slate-400 my-1" />;
  return (
    <div className="space-y-4">
      <div className="flex items-end justify-between">
        <div>
          <h2 className="text-xl font-semibold text-slate-900">AI architecture</h2>
          <p className="text-sm text-slate-600">Guidewire-compatible conceptual architecture. No production ClaimCenter integration is implemented in this prototype.</p>
        </div>
      </div>
      <div className="grid grid-cols-12 gap-4">
        <div className="col-span-7 bg-white border border-slate-200 rounded-md p-6 flex flex-col items-center">
          <Box sub="ClaimCenter-style FNOL, documents, policy and party data">ClaimCenter / Claim Intake</Box>
          <Arrow />
          <Box sub="Document OCR, fact extraction, schema mapping">Data Ingestion</Box>
          <Arrow />
          <Box sub="Match parties, vehicles, policies and prior claims to canonical entities">Entity Resolution</Box>
          <Arrow />
          <Box strong sub="Central contextual layer — every AI component reads from and writes to it">Knowledge Graph</Box>
          <Arrow />
          <Box sub="Assembles graph context + evidence, routes to the right capability">AI Orchestration Layer</Box>
          <Arrow />
          <div className="w-full grid grid-cols-4 gap-3">
            {[["Rules", "Guideline thresholds, coverage checks"], ["ML", "Severity & complexity models"], ["LLM", "Summary, explanation, Q&A"], ["RAG", "Guidelines & document retrieval"]].map(([t, s]) => (
              <div key={t} className="rounded border border-slate-300 bg-white text-center px-2 py-3"><div className="text-sm font-semibold text-slate-900">{t}</div><div className="text-xs text-slate-500 mt-0.5">{s}</div></div>
            ))}
          </div>
          <Arrow />
          <Box sub="Calibrated confidence per recommendation and per segment">Confidence Engine</Box>
          <Arrow />
          <Box sub="Recommend, or auto-route only where the segment is validated">Decision Layer</Box>
          <Arrow />
          <Box sub="Approves or overrides; explores graph and evidence">Human Adjuster</Box>
          <Arrow />
          <Box sub="Decisions and outcomes flow back into evaluation, models and graph">Feedback Loop</Box>
        </div>
        <div className="col-span-5 space-y-4">
          <Card title="Why the graph is the centre" tone="graph">
            <ul className="text-sm text-slate-700 space-y-2">
              <li><span className="font-medium">One context for all components.</span> Rules, ML, the LLM and retrieval all consume the same resolved entities and relationships, so recommendations are consistent and explainable.</li>
              <li><span className="font-medium">Explainability by construction.</span> Every reason in a recommendation points back to graph entities and source documents rather than a free-text rationale.</li>
              <li><span className="font-medium">History is a first-class relationship.</span> Prior claims, parties and vehicles connect across claims, which is where fraud, severity and litigation signals usually live.</li>
              <li><span className="font-medium">Feedback lands on the graph.</span> Adjuster decisions attach to the claim node and become training and evaluation labels.</li>
            </ul>
          </Card>
          <Card title="Graph vs. retrieval">
            <table className="w-full text-xs">
              <thead><tr className="text-left text-slate-500 border-b border-slate-100"><th className="py-1 font-medium">Question</th><th className="font-medium">Answered by</th></tr></thead>
              <tbody className="text-slate-700">
                {[["Who is involved and how are they connected?", "Knowledge graph"], ["Which coverage responds to this exposure?", "Knowledge graph + rules"], ["What does the police report say?", "RAG over documents"], ["What does the guideline require?", "RAG over guidelines"], ["Why is this claim severe?", "Graph context + LLM explanation"]].map(([q, a]) => (
                  <tr key={q} className="border-b border-slate-50"><td className="py-1.5 pr-3">{q}</td><td className="font-medium">{a}</td></tr>
                ))}
              </tbody>
            </table>
          </Card>
          <Card title="Integration note">
            <p className="text-xs text-slate-600">Intake, policy and party data are simulated in the ClaimCenter data shape. A production deployment would connect through the claim system's APIs and event streams; that integration is outside the scope of this prototype and is not claimed here.</p>
          </Card>
        </div>
      </div>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/* AUTONOMY ROADMAP                                                     */
/* ------------------------------------------------------------------ */

function Roadmap() {
  const levels = [
    { n: 1, name: "Assist", ai: "AI extracts facts and summarises claims.", human: "Human makes every decision.", status: "Live", tone: "emerald" },
    { n: 2, name: "Recommend", ai: "AI recommends severity, complexity and assignment with confidence and explanation.", human: "Human approves or overrides.", status: "Live — this prototype", tone: "emerald" },
    { n: 3, name: "Conditional automation", ai: "Only validated low-risk, high-confidence segments are routed automatically.", human: "Humans review exceptions and sampled cases.", status: "Pilot — Glass, Comprehensive < $2k", tone: "amber" },
    { n: 4, name: "Scaled automation", ai: "The automation envelope expands as segment performance is validated.", human: "Humans govern the envelope and handle complex claims.", status: "Planned", tone: "slate" },
  ];
  return (
    <div className="space-y-4">
      <div>
        <h2 className="text-xl font-semibold text-slate-900">AI autonomy roadmap</h2>
        <p className="text-sm text-slate-600">Autonomy increases by segment, not globally. Automation eligibility is determined by validated performance, risk, claim segment and business policy.</p>
      </div>
      <div className="flex flex-col items-center">
        {levels.map((l, i) => (
          <div key={l.n} className="w-full max-w-4xl flex flex-col items-center">
            <div className="w-full bg-white border border-slate-200 rounded-md grid grid-cols-12">
              <div className={`col-span-3 p-4 border-r border-slate-100 ${l.tone === "emerald" ? "bg-emerald-50" : l.tone === "amber" ? "bg-amber-50" : "bg-slate-50"}`}>
                <div className="text-xs text-slate-500">Level {l.n}</div>
                <div className="text-lg font-semibold text-slate-900">{l.name}</div>
                <span className={`inline-block mt-2 text-xs px-2 py-0.5 rounded border ${l.tone === "emerald" ? "bg-emerald-50 text-emerald-800 border-emerald-200" : l.tone === "amber" ? "bg-amber-50 text-amber-800 border-amber-200" : "bg-slate-100 text-slate-700 border-slate-200"}`}>{l.status}</span>
              </div>
              <div className="col-span-9 p-4 grid grid-cols-2 gap-4 text-sm">
                <div><div className="text-xs font-semibold text-teal-800 mb-1">AI does</div><div className="text-slate-700">{l.ai}</div></div>
                <div><div className="text-xs font-semibold text-slate-700 mb-1">Human does</div><div className="text-slate-700">{l.human}</div></div>
              </div>
            </div>
            {i < levels.length - 1 && <ArrowDown size={18} className="text-slate-400 my-1" />}
          </div>
        ))}
      </div>
      <Card title="What moves a segment to the next level">
        <div className="grid grid-cols-4 gap-4 text-sm">
          {[["Validated performance", "Acceptance rate, high-severity recall and false-negative rate stable across two evaluation windows."], ["Risk", "Low financial exposure and no litigation, fraud or injury indicators in the segment."], ["Claim segment", "Homogeneous claim types with mature guidelines, e.g. glass, low-value comprehensive."], ["Business policy", "Sign-off from claims leadership, compliance and the model risk function."]].map(([t, d]) => (
            <div key={t} className="border border-slate-200 rounded p-3"><div className="font-semibold text-slate-900">{t}</div><div className="text-xs text-slate-600 mt-1">{d}</div></div>
          ))}
        </div>
      </Card>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/* PERFORMANCE DASHBOARD                                                */
/* ------------------------------------------------------------------ */

function Performance({ decisions }) {
  const [seg, setSeg] = useState("Claim type");
  const n = Object.values(decisions).length;
  const approvals = Object.values(decisions).filter(d => d.type === "approve").length;
  const base = { n: 1800, accept: 1584 };
  const acceptRate = Math.round(((base.accept + approvals) / (base.n + n)) * 1000) / 10;
  const overrideRate = Math.round((100 - acceptRate) * 10) / 10;
  const metrics = [
    ["Recommendation acceptance rate", `${acceptRate}%`, "trailing 30 days"],
    ["Human override rate", `${overrideRate}%`, "trailing 30 days"],
    ["Average triage time", "26 min", "from FNOL to assignment"],
    ["High-severity recall", "94.6%", "of adjuster-confirmed HIGH"],
    ["False-negative rate", "2.1%", "HIGH triaged as LOW/MEDIUM"],
    ["Extraction accuracy", "96.3%", "facts vs. adjuster-verified"],
    ["Confidence calibration", "ECE 0.024", "expected calibration error"],
    ["Claims eligible for automation", "24%", "validated segments only"],
    ["Automation rate", "11%", "actually auto-routed"],
  ];
  const data = SEGMENTS[seg];
  return (
    <div className="space-y-4">
      <div className="flex items-end justify-between">
        <div>
          <h2 className="text-xl font-semibold text-slate-900">AI performance</h2>
          <p className="text-sm text-slate-600">Evaluation loop: AI recommendation → human decision → outcome. {n > 0 && <span className="text-teal-800 font-medium">{n} decision{n > 1 ? "s" : ""} from this session included.</span>}</p>
        </div>
        <span className="text-xs px-2 py-1 rounded bg-amber-50 border border-amber-200 text-amber-800">Simulated demo data</span>
      </div>
      <div className="grid grid-cols-9 gap-2">
        {metrics.map(([k, v, s]) => (
          <div key={k} className="bg-white border border-slate-200 rounded-md px-3 py-2.5">
            <div className="text-xs text-slate-500 leading-tight h-7">{k}</div>
            <div className="text-xl font-semibold text-slate-900 mt-1">{v}</div>
            <div className="text-xs text-slate-500">{s}</div>
          </div>
        ))}
      </div>
      <div className="grid grid-cols-12 gap-4">
        <div className="col-span-7">
          <Card title="Performance by segment" right={
            <div className="flex gap-1">{Object.keys(SEGMENTS).map(s => <button key={s} onClick={() => setSeg(s)} className={`text-xs px-2 py-1 rounded border ${seg === s ? "bg-slate-900 text-white border-slate-900" : "bg-white text-slate-600 border-slate-200 hover:bg-slate-50"}`}>{s}</button>)}</div>
          }>
            <div className="h-56">
              <ResponsiveContainer>
                <BarChart data={data} margin={{ top: 5, right: 10, left: -15, bottom: 0 }}>
                  <CartesianGrid vertical={false} stroke="#F1F5F9" />
                  <XAxis dataKey="seg" tick={{ fontSize: 11 }} />
                  <YAxis tick={{ fontSize: 11 }} domain={[0, 100]} />
                  <Tooltip />
                  <Legend wrapperStyle={{ fontSize: 11 }} />
                  <Bar dataKey="accept" name="Acceptance %" fill="#0F766E" radius={[2, 2, 0, 0]} />
                  <Bar dataKey="override" name="Override %" fill="#F59E0B" radius={[2, 2, 0, 0]} />
                  <Bar dataKey="auto" name="Automation %" fill="#94A3B8" radius={[2, 2, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
            <table className="w-full text-xs mt-2">
              <thead><tr className="text-left text-slate-500 border-b border-slate-100"><th className="py-1 font-medium">{seg}</th><th className="font-medium">Acceptance</th><th className="font-medium">Override</th><th className="font-medium">High-sev recall</th><th className="font-medium">Automation</th><th className="font-medium">Eligibility</th></tr></thead>
              <tbody>
                {data.map(r => (
                  <tr key={r.seg} className="border-b border-slate-50">
                    <td className="py-1.5 font-medium text-slate-800">{r.seg}</td><td>{r.accept}%</td><td>{r.override}%</td><td>{Math.round(r.recall * 100)}%</td><td>{r.auto}%</td>
                    <td>{r.auto >= 40 ? <span className="text-emerald-700 font-medium">Level 3 eligible</span> : r.auto >= 15 ? <span className="text-amber-700 font-medium">Under validation</span> : <span className="text-slate-500">Recommend only</span>}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </Card>
        </div>
        <div className="col-span-5 space-y-4">
          <Card title="Confidence calibration" right={<span className="text-xs text-slate-500">predicted vs. observed acceptance</span>}>
            <div className="h-44">
              <ResponsiveContainer>
                <ScatterChart margin={{ top: 5, right: 10, left: -15, bottom: 0 }}>
                  <CartesianGrid stroke="#F1F5F9" />
                  <XAxis type="number" dataKey="predicted" domain={[50, 100]} tick={{ fontSize: 11 }} name="Predicted" />
                  <YAxis type="number" dataKey="observed" domain={[50, 100]} tick={{ fontSize: 11 }} name="Observed" />
                  <Tooltip cursor={{ strokeDasharray: "3 3" }} />
                  <ReferenceLine segment={[{ x: 50, y: 50 }, { x: 100, y: 100 }]} stroke="#CBD5E1" strokeDasharray="4 4" />
                  <Scatter data={CALIBRATION} fill="#0F766E" />
                </ScatterChart>
              </ResponsiveContainer>
            </div>
            <p className="text-xs text-slate-500 mt-1">Points near the dashed line mean the confidence score tracks real acceptance. A 91% score means claims scored similarly were accepted about 91% of the time — not that this recommendation is 91% likely to be right.</p>
          </Card>
          <Card title="Trend · acceptance and triage time">
            <div className="h-40">
              <ResponsiveContainer>
                <LineChart data={TREND} margin={{ top: 5, right: 10, left: -15, bottom: 0 }}>
                  <CartesianGrid vertical={false} stroke="#F1F5F9" />
                  <XAxis dataKey="wk" tick={{ fontSize: 11 }} />
                  <YAxis tick={{ fontSize: 11 }} />
                  <Tooltip />
                  <Legend wrapperStyle={{ fontSize: 11 }} />
                  <Line type="monotone" dataKey="accept" name="Acceptance %" stroke="#0F766E" strokeWidth={2} dot={false} />
                  <Line type="monotone" dataKey="time" name="Triage time (min)" stroke="#F59E0B" strokeWidth={2} dot={false} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </Card>
        </div>
      </div>
      <Card title="Feedback log · AI recommendation → human decision → outcome">
        <table className="w-full text-xs">
          <thead><tr className="text-left text-slate-500 border-b border-slate-100"><th className="py-1 font-medium">Claim</th><th className="font-medium">AI recommendation</th><th className="font-medium">Human decision</th><th className="font-medium">Reason</th><th className="font-medium">Outcome</th><th className="font-medium">Recorded</th></tr></thead>
          <tbody>
            {Object.entries(decisions).map(([id, d]) => {
              const c = CLAIMS.find(x => x.id === id);
              return <tr key={id} className="border-b border-slate-50 bg-teal-50"><td className="py-1.5 font-mono font-medium">{id}</td><td>{c.severity} / {c.complexity} · {c.handler}</td><td className={d.type === "approve" ? "text-emerald-700" : "text-amber-700"}>{d.type === "approve" ? "Approved" : `Overrode → ${d.severity} / ${d.complexity} · ${d.handler}`}</td><td className="text-slate-600">{d.reason || "—"}</td><td>Routed · label stored</td><td className="text-slate-500">{d.at} (this session)</td></tr>;
            })}
            {[["CC-10229", "HIGH / MEDIUM · BI Specialist", "Overrode → HIGH / HIGH · Litigation specialist", "Attorney letter received before triage", "Routed · label stored", "2026-08-21"], ["CC-10239", "MEDIUM / LOW · General auto", "Approved", "—", "Closed in 9 days", "2026-08-26"], ["CC-10233", "LOW / LOW · Fast-track", "Approved", "—", "Closed in 4 days", "2026-08-23"]].map(r => (
              <tr key={r[0]} className="border-b border-slate-50">{r.map((c, i) => <td key={i} className={`py-1.5 ${i === 0 ? "font-mono font-medium" : i === 5 ? "text-slate-500" : ""}`}>{c}</td>)}</tr>
            ))}
          </tbody>
        </table>
      </Card>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/* APP SHELL                                                            */
/* ------------------------------------------------------------------ */

export default function ClaimIQ() {
  const [page, setPage] = useState("overview");
  const [claimId, setClaimId] = useState(null);
  const [graphFocus, setGraphFocus] = useState("CC-10245");
  const [graphSelected, setGraphSelected] = useState(null);
  const [decisions, setDecisions] = useState({});

  const go = (p, id) => {
    setPage(p);
    if (p === "claims") setClaimId(id || null);
    if (p === "graph" && id) { setGraphFocus(id); setGraphSelected(null); }
  };
  const openGraph = (id) => { setGraphFocus(id); setGraphSelected(null); setPage("graph"); };
  const openEntity = (id) => { setGraphFocus("CC-10245"); setGraphSelected(id); setPage("graph"); };
  const decide = (d) => {
    const at = new Date().toISOString().slice(0, 16).replace("T", " ");
    setDecisions(s => ({ ...s, [claimId]: { ...d, at } }));
  };

  const NAV = [
    ["overview", "Overview", LayoutDashboard],
    ["claims", "Claims", FileText],
    ["graph", "Knowledge Graph", Share2],
    ["performance", "AI Performance", BarChart3],
  ];
  const NAV2 = [
    ["architecture", "Architecture", Layers],
    ["roadmap", "Autonomy roadmap", Route],
  ];

  const claim = claimId ? CLAIMS.find(c => c.id === claimId) : null;

  return (
    <div className="min-h-screen bg-slate-100 text-slate-800" style={{ fontFamily: "'Segoe UI', system-ui, -apple-system, Roboto, sans-serif" }}>
      <div className="flex min-h-screen">
        {/* Sidebar */}
        <aside className="w-56 bg-slate-900 text-slate-300 flex flex-col flex-shrink-0">
          <div className="px-4 py-4 border-b border-slate-800">
            <div className="text-white font-semibold text-lg tracking-tight">ClaimIQ</div>
            <div className="text-xs text-slate-400">Knowledge Graph Claims Triage Copilot</div>
          </div>
          <nav className="px-2 py-3 space-y-0.5">
            {NAV.map(([k, l, I]) => (
              <button key={k} onClick={() => go(k)} className={`w-full flex items-center gap-2.5 px-3 py-2 rounded text-sm focus:outline-none focus:ring-2 focus:ring-teal-400 ${page === k ? "bg-teal-700 text-white" : "hover:bg-slate-800 hover:text-white"}`}><I size={16} /> {l}</button>
            ))}
            <div className="pt-3 pb-1 px-3 text-xs text-slate-500">Product concept</div>
            {NAV2.map(([k, l, I]) => (
              <button key={k} onClick={() => go(k)} className={`w-full flex items-center gap-2.5 px-3 py-2 rounded text-sm focus:outline-none focus:ring-2 focus:ring-teal-400 ${page === k ? "bg-teal-700 text-white" : "hover:bg-slate-800 hover:text-white"}`}><I size={16} /> {l}</button>
            ))}
          </nav>
          <div className="mt-auto px-4 py-3 border-t border-slate-800 text-xs text-slate-500">
            <div>Line of business: Personal Auto</div>
            <div>Region: Midwest</div>
            <div className="mt-2">Prototype · simulated data only</div>
          </div>
        </aside>

        {/* Main */}
        <div className="flex-1 min-w-0">
          <header className="h-12 bg-white border-b border-slate-200 flex items-center justify-between px-6">
            <div className="text-sm text-slate-500 flex items-center gap-1.5">
              <span>ClaimIQ</span><ChevronRight size={14} />
              <span className="text-slate-800 font-medium">{[...NAV, ...NAV2].find(n => n[0] === page)?.[1]}</span>
              {page === "claims" && claim && <><ChevronRight size={14} /><span className="text-slate-800 font-mono">{claim.id}</span></>}
            </div>
            <div className="flex items-center gap-4 text-sm text-slate-600">
              <span className="text-xs px-2 py-0.5 rounded bg-slate-100 border border-slate-200">Level 2 · Recommend</span>
              <Bell size={16} />
              <div className="flex items-center gap-2"><div className="w-7 h-7 rounded-full bg-teal-700 text-white text-xs flex items-center justify-center font-semibold">CA</div><span>Chris Alvarez · Intake adjuster</span></div>
            </div>
          </header>

          <main className="p-6">
            {page === "overview" && <Overview go={go} decisions={decisions} />}
            {page === "claims" && !claim && <ClaimsList onOpen={id => setClaimId(id)} decisions={decisions} />}
            {page === "claims" && claim && (
              <div>
                <button onClick={() => setClaimId(null)} className="text-xs text-teal-700 hover:underline mb-3 inline-flex items-center gap-1">← Back to triage queue</button>
                <ClaimWorkspace claim={claim} decision={decisions[claim.id]} onDecide={decide} openGraph={openGraph} openEntity={openEntity} />
              </div>
            )}
            {page === "graph" && (
              <div className="space-y-4">
                <div className="flex items-end justify-between">
                  <div>
                    <h2 className="text-xl font-semibold text-slate-900">Knowledge graph</h2>
                    <p className="text-sm text-slate-600">Explore how the customer, policy, coverages, parties, vehicles, documents, exposures and money connect around the claim.</p>
                  </div>
                  <div className="flex items-center gap-2">
                    {graphFocus !== "CC-10245" && <Btn small onClick={() => openGraph("CC-10245")}>Center on CC-10245</Btn>}
                    <Btn small variant="primary" onClick={() => go("claims", "CC-10245")}><FileText size={13} /> Back to claim workspace</Btn>
                  </div>
                </div>
                <GraphView focus={graphFocus} setFocus={id => { setGraphFocus(id); setGraphSelected(null); }} initialSelected={graphSelected} onOpenClaim={id => go("claims", id)} />
              </div>
            )}
            {page === "performance" && <Performance decisions={decisions} />}
            {page === "architecture" && <Architecture />}
            {page === "roadmap" && <Roadmap />}
          </main>
        </div>
      </div>
    </div>
  );
}
