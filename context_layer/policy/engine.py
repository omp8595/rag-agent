"""Policy engine — design doc section 5.

A stand-in for OPA/Cedar (open decision #1 doesn't name this one, but the
doc names OPA/Cedar as the intended engine — this is a small rule table
with the same input/output contract, so swapping in a real policy engine
later only means replacing `PolicyEngine.evaluate`, not any caller).

Two invariants this module exists to guarantee:

* **Fail closed.** An unregistered purpose, or a purpose/role combination
  that isn't permitted, is denied — never given an empty-but-present
  scope that some other layer might treat as "no restriction."
* **Purpose is not the requester's choice.** `evaluate()` takes the
  purpose from the request, but the request itself is only ever
  constructed by an Agent Builder config (see agent_builder/), which
  binds one fixed purpose per agent. A caller cannot rephrase `task` to
  get a wider scope — `task` never enters this function's decision.
"""

from __future__ import annotations

from dataclasses import dataclass

from context_layer.policy.models import PolicyDenied, PolicyRequest, RetrievalScope


@dataclass(frozen=True)
class PurposePolicy:
    purpose: str
    subgraphs: list[str]
    bridges: list[str]
    indexes: list[str]
    max_hops: int
    redactions: list[str]
    permitted_roles: set[str]


# The prototype's policy table (design doc section 9, week 3: two purposes
# plus a real bridge whitelist). medical_inquiry is included because the
# week-6 demo needs a third purpose to show the Medical firewall holding
# from more than one angle.
PURPOSE_POLICIES: dict[str, PurposePolicy] = {
    "commercial_engagement": PurposePolicy(
        purpose="commercial_engagement",
        subgraphs=["commercial"],
        bridges=[
            "medical.publications->commercial",
            "clinical.investigator_status->commercial",
        ],
        indexes=["commercial"],
        max_hops=2,
        redactions=["personal_email"],
        permitted_roles={"brand_manager", "field_rep"},
    ),
    "medical_inquiry": PurposePolicy(
        purpose="medical_inquiry",
        subgraphs=["medical"],
        bridges=[],
        indexes=["medical"],
        max_hops=2,
        redactions=[],
        permitted_roles={"msl", "medical_science_liaison"},
    ),
    "site_selection": PurposePolicy(
        purpose="site_selection",
        subgraphs=["clinical"],
        bridges=[],  # Commercial engagement -> Clinical site selection: No.
        indexes=["clinical"],
        max_hops=2,
        redactions=[],
        permitted_roles={"clinical_ops", "study_manager"},
    ),
}


def permitted_combination(purpose: str, role: str) -> bool:
    policy = PURPOSE_POLICIES.get(purpose)
    return policy is not None and role in policy.permitted_roles


class PolicyEngine:
    def evaluate(self, request: PolicyRequest) -> RetrievalScope:
        policy = PURPOSE_POLICIES.get(request.purpose)
        if policy is None:
            raise PolicyDenied(f"unrecognized purpose '{request.purpose}'")

        if not any(role in policy.permitted_roles for role in request.principal_roles):
            raise PolicyDenied(
                f"none of principal roles {request.principal_roles} are permitted "
                f"for purpose '{request.purpose}' (requires one of {sorted(policy.permitted_roles)})"
            )

        return RetrievalScope(
            purpose=policy.purpose,
            subgraphs=list(policy.subgraphs),
            bridges=list(policy.bridges),
            indexes=list(policy.indexes),
            max_hops=policy.max_hops,
            redactions=list(policy.redactions),
        )
