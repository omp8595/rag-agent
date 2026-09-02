"""Brand Manager promotional campaign workflow.

A GraphRAG-driven targeting pipeline built entirely on the existing HCP
Engagement Agent (`agents/hcp_engagement.yaml`, purpose=commercial_engagement)
— this script adds no new access path, it just calls the agent's own
tools in sequence:

  1. SCREEN   — for every HCP, pull a Context Package for the campaign
                topic. Targeting itself is GraphRAG-driven: an HCP is
                on-topic only if `community_summary` (§4.3 — "what does
                this HCP care about," derived from their own commercial
                engagement history, nothing else) actually names the
                topic. `recommended_content` (per-domain vector search,
                §4.4) is a *global* corpus search independent of the
                entity — useful for picking which approved piece to
                reference once someone is in, useless for deciding who's
                in: it matches the whole content library for any query
                that appears in it, entity or no entity.
  2. DRAFT    — call the agent's own `draft_email` action tool for each
                on-topic HCP. The promotional-exclusion constraint and
                the human-approval gate are enforced by the agent itself
                (agent_builder/agent.py) — this script never re-derives
                or special-cases either check.
  3. LOG      — `create_campaign_task` records the outreach against the
                top-ranked recommended content.
  4. REPORT   — who's in, who's off-topic, who's excluded on compliance
                grounds and why, what's still waiting on a human.

Run: python scripts/campaign_workflow.py ["campaign topic"]
"""

from __future__ import annotations

import sys

from context_layer.agent_builder.agent import ThinAgent
from context_layer.agent_builder.approvals import ApprovalQueue
from context_layer.agent_builder.builder import load_agent_config, publish_agent
from context_layer.api.app import build_assembler
from context_layer.data.loader import load_source_data

DEFAULT_TOPIC = "Biomarker testing"


def build_campaign(topic: str) -> tuple[dict, ApprovalQueue]:
    assembler = build_assembler()
    approvals = ApprovalQueue()
    agent = ThinAgent(publish_agent(load_agent_config("agents/hcp_engagement.yaml")), assembler, approvals)

    hcp_ids = [h["id"] for h in load_source_data()["hcps"]]

    report = {
        "topic": topic,
        "candidates": len(hcp_ids),
        "on_topic": [],
        "off_topic": 0,
        "excluded_compliance": [],
        "drafted": [],
        "campaign_tasks": [],
    }

    for hcp_id in hcp_ids:
        package = agent.get_context(hcp_id, task=topic)
        summary = package["community_summary"] or ""
        on_topic = topic.lower() in summary.lower()
        if not on_topic:
            report["off_topic"] += 1
            continue
        report["on_topic"].append({"hcp_id": hcp_id, "display": package["entity"]["display"], "community_summary": summary})

        draft = agent.draft_email(hcp_id, task=topic)
        if draft["status"] == "blocked":
            report["excluded_compliance"].append(
                {"hcp_id": hcp_id, "display": package["entity"]["display"], "reason": draft["reason"]}
            )
            continue

        report["drafted"].append(
            {"hcp_id": hcp_id, "display": package["entity"]["display"], "approval_id": draft["approval_id"], "subject": draft["subject"]}
        )

        if not package["recommended_content"]:
            continue  # nothing approved to reference — draft stands, no campaign task to log
        content_id = package["recommended_content"][0]["id"]
        task_result = agent.create_campaign_task(hcp_id, content_id, task=topic)
        report["campaign_tasks"].append({"hcp_id": hcp_id, "content_id": content_id, "status": task_result["status"]})

    return report, approvals


def main() -> None:
    topic = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_TOPIC
    report, approvals = build_campaign(topic)

    print(f"{'=' * 72}\nPromotional campaign: '{topic}'\n{'=' * 72}")
    print(f"candidates screened:     {report['candidates']}")
    print(f"on-topic (GraphRAG community summary): {len(report['on_topic'])}")
    print(f"off-topic (skipped):     {report['off_topic']}")
    print(f"excluded on compliance:  {len(report['excluded_compliance'])}")
    print(f"drafted, pending review: {len(report['drafted'])}")

    if report["on_topic"]:
        print(f"\n{'-' * 72}\nWhat GraphRAG saw (first 3 on-topic HCPs)\n{'-' * 72}")
        for entry in report["on_topic"][:3]:
            print(f"  {entry['hcp_id']} {entry['display']}: {entry['community_summary'] or '(no commercial-domain activity yet)'}")

    if report["excluded_compliance"]:
        print(f"\n{'-' * 72}\nExcluded on compliance grounds — never drafted\n{'-' * 72}")
        for entry in report["excluded_compliance"]:
            print(f"  {entry['hcp_id']} {entry['display']}: {entry['reason']}")

    if report["drafted"]:
        print(f"\n{'-' * 72}\nDrafted and held for approval\n{'-' * 72}")
        for entry in report["drafted"]:
            print(f"  {entry['hcp_id']} {entry['display']}: \"{entry['subject']}\" [{entry['approval_id']}]")

        print(f"\n{'-' * 72}\nA campaign reviewer approves the batch\n{'-' * 72}")
        for entry in report["drafted"]:
            record = approvals.approve(entry["approval_id"])
            print(f"  {record.id} -> {record.status} at {record.approved_at}")

    print(
        f"\n{report['candidates']} HCPs screened -> {len(report['on_topic'])} on-topic -> "
        f"{len(report['excluded_compliance'])} held back by policy, not by this script -> "
        f"{len(report['drafted'])} drafts approved -> {len(report['campaign_tasks'])} campaign tasks logged."
    )


if __name__ == "__main__":
    main()
