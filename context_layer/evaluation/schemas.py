"""Shared types for the evaluation layer. Deterministic evaluators and LLM
adapters both produce these; runner.py assembles them into a CaseResult,
scoring.py turns a CaseResult into a status, reporting.py renders it.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class EvaluationCase:
    id: str
    category: str  # "commercial_engagement" | "site_selection" | "medical_inquiry" | "security_negative"
    entity_id: str
    question: str
    agent_config_path: str | None = None  # None for cases that hit the policy engine directly
    purpose: str | None = None  # only used when agent_config_path is None
    principal_roles: list[str] = field(default_factory=list)
    expected_domains: list[str] = field(default_factory=list)
    forbidden_domains: list[str] = field(default_factory=list)
    expect_denial: bool = False
    ground_truth_answer: str | None = None
    notes: str = ""


# -- deterministic evaluators --------------------------------------------


@dataclass
class PolicyEvalResult:
    policy_compliant: bool
    allowed_domains: list[str]
    observed_domains: list[str]
    forbidden_domains_found: list[str]
    violations: list[str]


@dataclass
class GraphEvalResult:
    graph_compliant: bool
    domains_traversed: list[str]
    bridges_used: list[str]
    unauthorized_bridges: list[str]


@dataclass
class LineageEvalResult:
    total_facts: int
    facts_with_lineage: int
    orphan_facts: list[str]
    lineage_coverage: float


@dataclass
class IsolationEvalResult:
    entity_id: str
    purpose_a: str
    purpose_b: str
    packages_differ: bool
    forbidden_domain_leak: list[str]
    isolation_score: float


# -- LLM-backed evaluators -------------------------------------------------


@dataclass
class MetricResult:
    """One named float metric, or a skip reason instead of a value."""

    name: str
    value: float | None
    skipped: bool = False
    skip_reason: str | None = None


@dataclass
class FrameworkResult:
    framework: str  # "ragas" | "deepeval"
    metrics: list[MetricResult]
    skipped: bool = False
    skip_reason: str | None = None


@dataclass
class JudgeDimension:
    score: float
    reason: str


@dataclass
class HallucinationRisk:
    level: str  # "LOW" | "MEDIUM" | "HIGH"
    reason: str


@dataclass
class LLMJudgeResult:
    skipped: bool = False
    skip_reason: str | None = None
    correctness: JudgeDimension | None = None
    relevance: JudgeDimension | None = None
    faithfulness: JudgeDimension | None = None
    policy_compliance: JudgeDimension | None = None
    hallucination_risk: HallucinationRisk | None = None
    overall_score: float | None = None
    passed: bool | None = None
    critical_violation: bool = False


# -- unified case result ---------------------------------------------------


@dataclass
class CaseResult:
    case: EvaluationCase
    question: str
    retrieved_context: list[str]
    generated_answer: str | None
    policy: PolicyEvalResult | None = None
    graph: GraphEvalResult | None = None
    lineage: LineageEvalResult | None = None
    ragas: FrameworkResult | None = None
    deepeval: FrameworkResult | None = None
    llm_judge: LLMJudgeResult | None = None
    unified_score: float | None = None
    status: str | None = None  # "PASS" | "FAIL"
    status_reasons: list[str] = field(default_factory=list)
    error: str | None = None
