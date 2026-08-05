import unittest

from benchmark import break_relations, invariant_signature, run


class BenchmarkTests(unittest.TestCase):
    def test_signature_is_rigid_transform_invariant(self):
        source = [[0.0, 0.0], [1.0, 0.0], [0.0, 2.0]]
        transformed = [[10.0, -4.0], [10.0, -6.0], [14.0, -4.0]]
        self.assertEqual(invariant_signature(source), invariant_signature(transformed))

    def test_negative_control_changes_signature(self):
        source = [[float(i), float(i % 3)] for i in range(9)]
        self.assertNotEqual(invariant_signature(source), invariant_signature(break_relations(source)))

    def test_reference_configuration_passes(self):
        result = run()
        self.assertTrue(result["pass"], result)
        self.assertGreater(result["scores"]["integrity_gap"], 0.10)

    def test_run_is_deterministic(self):
        self.assertEqual(run(trials=4), run(trials=4))


if __name__ == "__main__":
    unittest.main()
