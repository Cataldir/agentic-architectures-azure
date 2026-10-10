"""Repair these deliberately wrong policies; do not deploy them."""
from azure_course.policy import Evidence, ReleaseState
from azure_course.saga import Saga, SagaState


def release_decision(e: Evidence, *, tolerance: float = 0.02) -> ReleaseState:
    # Exercise32: require live, calibrated, complete evidence and bounded regression.
    return ReleaseState.ELIGIBLE


def begin_compensation(s: Saga, *, outcome_known: bool) -> Saga:
    # Exercise27: reverse completed steps; unknown outcome requires reconciliation.
    return Saga(s.saga_id, s.tenant, s.revision + 1, s.completed,
                s.completed, SagaState.COMPENSATING)
