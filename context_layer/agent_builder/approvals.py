"""Approval queue for guardrailed actions — design doc §7,
`guardrails.human_approval_required`.

An action named in that list is never executed by the agent itself: it is
submitted here and sits `pending` until a human calls `approve()`. This
prototype stops at that boundary deliberately — it proves the gate holds,
it does not wire up a real send-email or CTMS-write integration behind it.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass
class ApprovalRecord:
    id: str
    action: str
    agent: str
    payload: dict
    status: str  # "pending" | "approved"
    created_at: str
    approved_at: str | None = None


class ApprovalQueue:
    def __init__(self) -> None:
        self._records: dict[str, ApprovalRecord] = {}

    def submit(self, *, action: str, agent: str, payload: dict) -> ApprovalRecord:
        record = ApprovalRecord(
            id=f"appr-{uuid.uuid4().hex[:10]}",
            action=action,
            agent=agent,
            payload=payload,
            status="pending",
            created_at=datetime.now(timezone.utc).isoformat(),
        )
        self._records[record.id] = record
        return record

    def approve(self, approval_id: str) -> ApprovalRecord:
        record = self._records.get(approval_id)
        if record is None:
            raise KeyError(f"no such approval {approval_id!r}")
        record.status = "approved"
        record.approved_at = datetime.now(timezone.utc).isoformat()
        return record

    def pending(self) -> list[ApprovalRecord]:
        return [r for r in self._records.values() if r.status == "pending"]
