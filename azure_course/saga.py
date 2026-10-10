"""Finite compensation planner; external execution belongs to step owners."""
from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class SagaState(StrEnum):
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    COMPENSATING = "compensating"
    COMPENSATED = "compensated"
    RECONCILE = "reconcile"


@dataclass(frozen=True)
class Saga:
    saga_id: str
    tenant: str
    revision: int = 0
    completed: tuple[str, ...] = ()
    remaining: tuple[str, ...] = ()
    state: SagaState = SagaState.RUNNING


def record_step(s: Saga, step: str, expected_revision: int) -> Saga:
    if expected_revision != s.revision:
        raise ValueError("stale revision")
    if not step or s.state != SagaState.RUNNING:
        raise ValueError("invalid step/state")
    if step in s.completed:
        return s  # Exact duplicate only; payload equality is journal owner's duty.
    return Saga(s.saga_id, s.tenant, s.revision + 1, s.completed + (step,))


def begin_compensation(s: Saga, *, outcome_known: bool) -> Saga:
    if s.state != SagaState.RUNNING:
        raise ValueError("cannot begin compensation")
    state = (SagaState.COMPENSATING if s.completed else SagaState.COMPENSATED) if outcome_known else SagaState.RECONCILE
    return Saga(s.saga_id, s.tenant, s.revision + 1, s.completed,
                tuple(reversed(s.completed)), state)


def acknowledge_compensation(s: Saga, step: str, *, succeeded: bool) -> Saga:
    if s.state != SagaState.COMPENSATING or not s.remaining:
        raise ValueError("no active compensation")
    if step != s.remaining[0]:
        raise ValueError("compensation out of order")
    if not succeeded:
        return Saga(s.saga_id, s.tenant, s.revision + 1, s.completed,
                    s.remaining, SagaState.RECONCILE)
    remaining = s.remaining[1:]
    state = SagaState.COMPENSATING if remaining else SagaState.COMPENSATED
    return Saga(s.saga_id, s.tenant, s.revision + 1, s.completed, remaining, state)
