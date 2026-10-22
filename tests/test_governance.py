import os, tempfile, unittest
from governance_harness import GovernanceHarness

class HarnessTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.h = GovernanceHarness(os.path.join(self.tmp.name, "test.db"))

    def tearDown(self):
        self.tmp.cleanup()

    def test_human_review_required_and_single_review(self):
        pid = self.h.propose_reservation("Reservar sala 2", "Propuesta jueves 16:00")
        self.assertEqual(self.h.get_proposals("pending")[0]["id"], pid)
        self.assertEqual(self.h.review_proposal(pid, True, "Responsable"), "approved")
        with self.assertRaises(ValueError):
            self.h.review_proposal(pid, False, "Otra persona")

    def test_prediction_error(self):
        pid = self.h.record_prediction(100, "v1")
        error = self.h.attach_actual(pid, 90)
        self.assertEqual(error, 10)
        self.assertAlmostEqual(self.h.performance_summary()["mae"], 10)

    def test_missing_prediction_rejected(self):
        with self.assertRaises(ValueError):
            self.h.attach_actual("no-existe", 4)

if __name__ == "__main__":
    unittest.main()
