"""Pure deployment, tool and evaluation decisions; no cloud effects."""
from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from math import isfinite


class ReleaseState(StrEnum):
    HOLD = "hold"
    REJECT = "reject"
    ELIGIBLE = "eligible-for-owner-review"


@dataclass(frozen=True)
class Evidence:
    candidate: str
    source: str
    calibrated: bool
    live: bool
    complete: bool
    baseline_success: float
    candidate_success: float
    unauthorized_effects: int
    n: int


def release_decision(e: Evidence, *, tolerance: float = 0.02) -> ReleaseState:
    """Return eligibility only; a caller still needs release authority."""
    if not 0 <= tolerance <= 1:
        raise ValueError("tolerance must be a probability")
    scores = (e.baseline_success, e.candidate_success)
    if any(not isfinite(x) or not 0 <= x <= 1 for x in scores):
        raise ValueError("invalid score")
    if e.unauthorized_effects < 0 or e.n < 0:
        raise ValueError("invalid count")
    if e.unauthorized_effects:
        return ReleaseState.REJECT
    if not (e.candidate and e.source and e.live and e.calibrated and e.complete):
        return ReleaseState.HOLD
    # Classroom minimum; sample size is chosen by power/risk analysis in real use.
    if e.n < 30:
        return ReleaseState.HOLD
    if e.candidate_success < e.baseline_success - tolerance:
        return ReleaseState.REJECT
    return ReleaseState.ELIGIBLE


@dataclass(frozen=True)
class ToolContext:
    actor: str
    tenant: str
    domain: str
    allowed_tools: frozenset[str]


def authorize_tool(context: ToolContext, tool: str, tenant: str) -> None:
    """Authenticated context must be supplied by the trusted gateway."""
    if not context.actor or not context.domain or not context.tenant:
        raise PermissionError("missing authenticated context")
    if context.tenant != tenant or tool not in context.allowed_tools:
        raise PermissionError("cross-context or tool denied")


@dataclass(frozen=True)
class Deployment:
    name: str
    provider: str
    data_class: str
    tool_schema: str
    region: str


def compatible_failover(primary: Deployment, alternate: Deployment) -> bool:
    """An explicit policy comparison, never a catch-all SDK retry."""
    return (
        bool(primary.name and alternate.name)
        and primary.data_class == alternate.data_class
        and primary.tool_schema == alternate.tool_schema
        and primary.region == alternate.region
        and primary.name != alternate.name
    )
