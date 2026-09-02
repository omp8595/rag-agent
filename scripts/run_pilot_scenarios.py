"""Runs every scenario in evaluation/pilot_dataset/scenarios.json against
the live Context Layer and prints actual vs. expected for a human
facilitator to review during a pilot session (docs/pilot_workflow.md).

This does NOT feed `expected_context_characteristics` or
`expected_policy_outcome` into generation anywhere — those fields exist
only in this script's own output, for a person to compare against what
the system actually returned. The dataset stays evaluation-only, per the
pilot mega-prompt's explicit instruction not to place expected answers
into the runtime system.

Usage:
    ./.venv/bin/python scripts/run_pilot_scenarios.py [--type normal|edge|adversarial]
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from pydantic import ValidationError

from context_layer.agent_builder.agent import ThinAgent
from context_layer.agent_builder.builder import load_agent_config, publish_agent
from context_layer.api.app import build_assembler
from context_layer.api.http_server import ContextRequest
from context_layer.llm.provider import MockLLMProvider
from context_layer.policy.engine import PolicyEngine
from context_layer.policy.models import PolicyDenied, PolicyRequest

DATASET_PATH = Path(__file__).resolve().parent.parent / "evaluation" / "pilot_dataset" / "scenarios.json"

AGENT_YAML = {
    "hcp_engagement_agent": "agents/hcp_engagement.yaml",
    "site_selection_agent": "agents/site_selection.yaml",
}


def _run_normal_or_edge_or_a3_a4_a5(scenario: dict, agents: dict[str, ThinAgent]) -> dict:
    agent = agents[scenario["agent"]]
    try:
        result = agent.generate_response(scenario["entity_id"], scenario["question"], provider=MockLLMProvider())
    except ValueError as exc:
        return {"outcome": "error_not_found", "detail": str(exc)}
    except PermissionError as exc:
        return {"outcome": "error_forbidden", "detail": str(exc)}
    package = result["package"]
    return {
        "outcome": "allow",
        "allowed_domains": package["policy_decision"]["allowed_domains"],
        "facts_count": len(package["facts"]),
        "constraints": package.get("constraints", []),
        "answer": result["answer"],
        "supporting_fact_ids": result["supporting_fact_ids"],
    }


def _run_unregistered_purpose(scenario: dict) -> dict:
    try:
        PolicyEngine().evaluate(
            PolicyRequest(
                principal="pilot-scenario-runner",
                principal_roles=["brand_manager"],
                purpose=scenario["bound_purpose"],
                entity_id=scenario["entity_id"],
            )
        )
        return {"outcome": "allow", "detail": "UNEXPECTED — an unregistered purpose was not denied"}
    except PolicyDenied as exc:
        return {"outcome": "deny_fail_closed", "detail": exc.reason}


def _run_http_purpose_override(scenario: dict) -> dict:
    try:
        ContextRequest(agent_id=scenario["agent"], entity_id=scenario["entity_id"], question=scenario["question"], purpose=scenario["bound_purpose"])
        return {"outcome": "allow", "detail": "UNEXPECTED — a 'purpose' field in the request body was accepted"}
    except ValidationError as exc:
        return {"outcome": "reject_422_extra_field", "detail": str(exc.errors()[0]["type"])}


def run_scenario(scenario: dict, agents: dict[str, ThinAgent]) -> dict:
    if scenario["scenario_id"] == "A1-unregistered-purpose-fails-closed":
        return _run_unregistered_purpose(scenario)
    if scenario["scenario_id"] == "A2-http-purpose-override-attempt":
        return _run_http_purpose_override(scenario)
    return _run_normal_or_edge_or_a3_a4_a5(scenario, agents)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--type", choices=["normal", "edge", "adversarial"], default=None)
    args = parser.parse_args()

    scenarios = json.loads(DATASET_PATH.read_text())
    if args.type:
        scenarios = [s for s in scenarios if s["type"] == args.type]

    assembler = build_assembler()
    agents = {agent_id: ThinAgent(publish_agent(load_agent_config(path)), assembler) for agent_id, path in AGENT_YAML.items()}

    for scenario in scenarios:
        print("=" * 70)
        print(f"{scenario['scenario_id']}  [{scenario['type']}]")
        print(f"  question: {scenario['question']}")
        print(f"  expected_allowed_domains:  {scenario['expected_allowed_domains']}")
        print(f"  expected_policy_outcome:   {scenario['expected_policy_outcome']}")
        print(f"  expected_characteristics:  {scenario['expected_context_characteristics']}")
        actual = run_scenario(scenario, agents)
        print("  --- actual ---")
        for key, value in actual.items():
            print(f"  {key}: {value}")
        print("  facilitator: compare 'actual' above against 'expected_*' by hand — this script does not auto-grade.")
    print("=" * 70)


if __name__ == "__main__":
    main()
