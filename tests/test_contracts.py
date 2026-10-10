"""Meaningful offline negative cases; authored, never executed in this session."""
import os
import unittest
from azure_course.policy import Evidence, ReleaseState, ToolContext, authorize_tool
from azure_course.saga import Saga, SagaState, record_step, acknowledge_compensation

if os.environ.get("COURSE_IMPLEMENTATION") == "starter":
    from starter.exercises import release_decision, begin_compensation
else:
    from azure_course.policy import release_decision
    from azure_course.saga import begin_compensation


class ContractTests(unittest.TestCase):
    def test_mock_never_promotes(self) -> None:
        e = Evidence("c", "fixture", False, False, True, .9, 1.0, 0, 100)
        self.assertEqual(release_decision(e), ReleaseState.HOLD)

    def test_regression_rejects(self) -> None:
        e = Evidence("c", "frozen-live-run", True, True, True, .9, .7, 0, 100)
        self.assertEqual(release_decision(e), ReleaseState.REJECT)

    def test_unauthorized_effect_vetoes(self) -> None:
        e = Evidence("c", "fixture", False, False, False, .9, 1, 1, 100)
        self.assertEqual(release_decision(e), ReleaseState.REJECT)

    def test_insufficient_sample_holds(self) -> None:
        e = Evidence("c", "run", True, True, True, .9, .9, 0, 2)
        self.assertEqual(release_decision(e), ReleaseState.HOLD)

    def test_cross_tenant_denied(self) -> None:
        c = ToolContext("principal-a", "a", "orders", frozenset({"lookup"}))
        with self.assertRaises(PermissionError):
            authorize_tool(c, "lookup", "b")

    def test_compensation_reverses_and_holds_unknown(self) -> None:
        s = record_step(Saga("s", "a"), "reserve", 0)
        s = record_step(s, "charge", 1)
        self.assertEqual(begin_compensation(s, outcome_known=True).remaining,
                         ("charge", "reserve"))
        self.assertEqual(begin_compensation(s, outcome_known=False).state,
                         SagaState.RECONCILE)

    def test_failure_does_not_skip_compensation(self) -> None:
        s = record_step(Saga("s", "a"), "reserve", 0)
        c = begin_compensation(s, outcome_known=True)
        failed = acknowledge_compensation(c, "reserve", succeeded=False)
        self.assertEqual(failed.remaining, ("reserve",))
        self.assertEqual(failed.state, SagaState.RECONCILE)

    def test_stale_step_refused(self) -> None:
        s = record_step(Saga("s", "a"), "reserve", 0)
        with self.assertRaises(ValueError):
            record_step(s, "charge", 0)

    def test_no_completed_effect_needs_no_compensation(self) -> None:
        s = begin_compensation(Saga("empty", "a"), outcome_known=True)
        self.assertEqual(s.state, SagaState.COMPENSATED)
        self.assertEqual(s.remaining, ())


if __name__ == "__main__":
    unittest.main()
