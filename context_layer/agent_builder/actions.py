"""Action payload builders — design doc §7, `action_tools`.

Pure functions: given an already policy-scoped Context Package (and, for
campaign tasks, an already-validated content record), build the payload
an action would submit. No graph or policy access here — that separation
is deliberate, so an action can never reach past what the Context Package
already decided to show it.

`build_email_draft` is the one with a real decision in it: it reads the
package's `constraints` block and refuses to draft outreach when one
names a promotional exclusion, rather than drafting anyway and hoping a
human notices. That's the payoff of design doc §6's "the agent is told
what it must respect... so it can be honest with the user rather than
guessing" — here, "honest" means declining to act.
"""

from __future__ import annotations

_PROMOTIONAL_EXCLUSION_MARKER = "promotional exclusion"


def build_email_draft(package: dict, task: str = "") -> dict:
    constraints = package.get("constraints", [])
    blocking = next((c for c in constraints if _PROMOTIONAL_EXCLUSION_MARKER in c.lower()), None)
    if blocking:
        return {"action": "draft_email", "blocked": True, "reason": blocking}

    display = package["entity"]["display"]
    content = package.get("recommended_content", [])
    content_lines = [f"- {c['title']}" for c in content] or ["(no matching approved content — general check-in)"]
    subject = f"Re: {task}" if task else f"Following up — {display}"
    body = (
        f"Hi {display},\n\n"
        + (f"Following up on {task}. " if task else "")
        + "Thought you'd find this useful:\n"
        + "\n".join(content_lines)
        + "\n\nBest,\n{{sender}}"
    )
    return {
        "action": "draft_email",
        "blocked": False,
        "subject": subject,
        "body": body,
        "references": [c["id"] for c in content],
    }


def build_campaign_task(package: dict, content: dict) -> dict:
    return {
        "action": "create_campaign_task",
        "entity_id": package["entity"]["id"],
        "content_id": content["id"],
        "note": f"Add {package['entity']['display']} to outreach for '{content['title']}'.",
    }


def build_feasibility_note(package: dict, note_text: str) -> dict:
    facts = package.get("facts", [])
    pi_fact = next((f for f in facts if "Principal investigator" in f["claim"]), None)
    return {
        "action": "create_feasibility_note",
        "entity_id": package["entity"]["id"],
        "note": note_text,
        "supporting_fact": pi_fact["claim"] if pi_fact else None,
    }
