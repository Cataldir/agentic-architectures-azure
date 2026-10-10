import unittest
from azure_course.session_saga import initial, apply

class SessionSagaTests(unittest.TestCase):
    def advance(self, row):
        payload = row["outbox"][-1]["payload"]
        return apply(row, payload)
    def test_known_failure_compensates_reverse_order(self):
        row = initial("saga1", "learnera")
        for _ in range(5):
            row = self.advance(row)
        self.assertEqual("compensated", row["state"])
        self.assertEqual([], row["effects"])
        self.assertEqual(["reserve", "charge", "ship", "undo-charge", "undo-reserve"],
                         [x["payload"]["operation"] for x in row["outbox"]])
    def test_unknown_failure_refuses_compensation(self):
        row = initial("saga2", "learnera", failure="unknown-ship")
        for _ in range(3):
            row = self.advance(row)
        self.assertEqual("reconcile", row["state"])
        self.assertEqual(3, len(row["outbox"]))
    def test_duplicate_is_idempotent_changed_payload_is_refused(self):
        row = initial("saga3", "learnera")
        payload = row["outbox"][0]["payload"]
        updated = apply(row, payload)
        self.assertEqual(updated, apply(updated, payload))
        changed = {**payload, "owner": "payment"}
        with self.assertRaises(PermissionError):
            apply(updated, changed)
    def test_compensation_failure_requires_reconciliation(self):
        row = initial("saga4", "learnera", failure="undo-charge")
        for _ in range(4):
            row = self.advance(row)
        self.assertEqual("reconcile", row["state"])

if __name__ == "__main__":
    unittest.main()

