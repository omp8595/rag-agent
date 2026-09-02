"""The killer demo: one HCP, two agents, two approved purposes, all the
way through to a grounded LLM response — proving the full chain the
architecture claims:

    User Question -> Published Agent -> Purpose-bound Config
        -> Enterprise Context API -> Policy Evaluation -> Context Package
        -> LLM Prompt Construction -> Generated Response

Uses the mock LLM provider by default (deterministic, no credentials).
Pass --real to use a configured ANTHROPIC_API_KEY/OPENAI_API_KEY instead —
see context_layer/llm/provider.py.

Run: python scripts/e2e_demo.py [--real]
"""

from __future__ import annotations

import argparse

from context_layer.agent_builder.agent import ThinAgent
from context_layer.agent_builder.builder import load_agent_config, publish_agent
from context_layer.api.app import build_assembler
from context_layer.data.loader import load_source_data
from context_layer.evaluation.isolation_evaluator import evaluate_isolation
from context_layer.evaluation.policy_evaluator import evaluate_policy
from context_layer.evaluation.schemas import EvaluationCase
from context_layer.llm.provider import MockLLMProvider, RealLLMProvider

SCENARIOS = [
    {
        "agent_config": "agents/hcp_engagement.yaml",
        "roles": ["brand_manager"],
        "label": "AGENT A — HCP Engagement Agent",
        "question": "What context should I consider for the next approved engagement with this HCP?",
        "forbidden_domains": ["clinical"],
    },
    {
        "agent_config": "agents/site_selection.yaml",
        "roles": ["clinical_ops"],
        "label": "AGENT B — Clinical Site Selection Agent",
        "question": "What context is available to assess this HCP and institution for clinical site selection?",
        "forbidden_domains": ["commercial", "medical"],
    },
]


def _entity_id() -> str:
    source = load_source_data()
    return next(r for r in source["investigator_sites"] if r["active"])["hcp_id"]


def _print_section(title: str) -> None:
    print(f"\n{'-' * 68}\n{title}\n{'-' * 68}")


def run(use_real_llm: bool) -> None:
    assembler = build_assembler()
    entity_id = _entity_id()

    print("=" * 68)
    print("ENTERPRISE CONTEXT LAYER — END-TO-END DEMO")
    print("=" * 68)
    print(f"\nENTITY\n{entity_id}")

    packages = []
    for scenario in SCENARIOS:
        config = publish_agent(load_agent_config(scenario["agent_config"]))
        agent = ThinAgent(config, assembler)
        provider = RealLLMProvider() if use_real_llm else MockLLMProvider()

        result = agent.generate_response(entity_id, scenario["question"], provider=provider)
        package = result["package"]
        packages.append((scenario, package))

        _print_section(scenario["label"])
        print(f"Purpose:\n  {package['purpose']}")
        print(f"\nAllowed Domains:\n  {', '.join(package['policy_decision']['allowed_domains'])}")
        print(f"\nForbidden Domains:\n  {', '.join(package['policy_decision']['forbidden_domains']) or '(none)'}")
        print(f"\nFacts Retrieved ({len(package['facts'])}):")
        for fact in package["facts"]:
            print(f"  [{fact['fact_id']}] {fact['claim']}")
        print(f"\nBridges Used:\n  {', '.join(package['governance']['bridges_used']) or '(none)'}")
        print(f"\nConstraints:\n  {'; '.join(package['constraints']) or '(none)'}")
        print(f"\nContext Package ID:\n  {package['request_id']}")
        print(f"\nGenerated Response (provider={result['llm_provider']}, model={result['llm_model']}):")
        print(f"  {result['answer']}")
        print(f"\nSupporting Fact IDs:\n  {result['supporting_fact_ids'] or '(none)'}")
        print(f"\nGrounding Warnings:\n  {result['warnings'] or '(none)'}")

    (scenario_a, package_a), (scenario_b, package_b) = packages
    case_a = EvaluationCase(id="e2e-a", category="demo", entity_id=entity_id, question=scenario_a["question"], forbidden_domains=scenario_a["forbidden_domains"])
    case_b = EvaluationCase(id="e2e-b", category="demo", entity_id=entity_id, question=scenario_b["question"], forbidden_domains=scenario_b["forbidden_domains"])
    policy_a = evaluate_policy(case_a, package_a)
    policy_b = evaluate_policy(case_b, package_b)
    isolation = evaluate_isolation(package_a, package_b)

    unauthorized = not policy_a.policy_compliant or not policy_b.policy_compliant or bool(isolation.forbidden_domain_leak)
    status = "FAIL" if unauthorized else "PASS"

    print(f"\n{'=' * 68}\nISOLATION RESULT\n{'=' * 68}")
    print(f"Same Entity: YES")
    print(f"Same Base Data: YES")
    print(f"Different Purpose: {'YES' if package_a['purpose'] != package_b['purpose'] else 'NO'}")
    print(f"Different Context Packages: {'YES' if isolation.packages_differ else 'NO'}")
    print(f"Unauthorized Data Exposed: {'YES' if unauthorized else 'NO'}")
    print(f"\nSTATUS: {status}")
    print("=" * 68)


def main() -> None:
    parser = argparse.ArgumentParser(description="Enterprise Context Layer end-to-end demo")
    parser.add_argument("--real", action="store_true", help="use a configured real LLM provider instead of the mock")
    args = parser.parse_args()
    try:
        run(use_real_llm=args.real)
    except RuntimeError as exc:
        raise SystemExit(f"{exc}\n(run without --real to use the deterministic mock provider)") from None


if __name__ == "__main__":
    main()
