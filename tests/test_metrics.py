import itertools
import unittest

from pact.attacks import fixed_attack
from pact.backends.mock import MockBackend
from pact.config import Config, ProbeConfig
from pact.datasets import fixtures
from pact.evaluation import aggregate, paired_bootstrap, score, summarize
from pact.protocol import Protocol


def row(initial, revised, success, task_id="t"):
    return {"task_id": task_id, "family": "fixture", "method": "debate", "condition": "clean", "status": "complete",
            "initial": list(initial), "revised": list(revised), "success": success,
            "helpful": [True] * len(initial), "misleading": [True] * len(initial),
            "parsing_failures": 0, "final_parser_status": "ok", "abstentions": 0,
            "input_tokens": 1, "output_tokens": 1, "readout_low_trust_tokens": 1}


class MetricTests(unittest.TestCase):
    def test_all_joint_outcomes_decompose(self):
        rows = [row(before, after, final) for before in itertools.product((False, True), repeat=3)
                for after in itertools.product((False, True), repeat=3) for final in (False, True)]
        values = aggregate(rows)
        c, u, k, d, r = (values[key]["value"] for key in ("c", "u", "k", "d", "r"))
        self.assertAlmostEqual(values["terminal_success"]["value"], c * u + (1 - c) * k)
        self.assertAlmostEqual(values["decomposition"]["availability_lhs"], (1 - c) * (1 - r) + c * d)
        self.assertAlmostEqual(values["readout_loss"]["value"], 7 / 16)

    def test_zero_denominators_and_na(self):
        yes = aggregate([row([True] * 3, [True] * 3, True)])
        self.assertIsNone(yes["k"]["value"])
        self.assertEqual(yes["k"]["denominator"], 0)
        no = aggregate([row([False] * 3, [False] * 3, False)])
        self.assertIsNone(no["u"]["value"])
        self.assertIsNone(no["d"]["value"])
        no_revision = aggregate([row([True] * 3, [], True)])
        self.assertEqual(no_revision["d"]["reason"], "not_applicable")
        self.assertIsNone(aggregate([])["terminal_success"]["value"])

    def test_known_mock_mechanisms(self):
        config = Config(probe=ProbeConfig(tasks=0))
        backend = MockBackend(config)
        protocol = Protocol(config, backend)
        rows = []
        for position, (task, label) in enumerate(fixtures(4)):
            attack = fixed_attack(task, label, "clean", position, config.seed, backend, 256)
            rows.append(score(protocol.run(task, "debate", attack), label))
        self.assertEqual([r["success"] for r in rows], [False, True, True, False])
        values = aggregate(rows)
        self.assertEqual(values["c"]["value"], 3 / 4)
        self.assertEqual(values["u"]["value"], 1 / 3)
        self.assertEqual(values["k"]["value"], 1.0)
        self.assertEqual(values["d"]["value"], 1 / 3)
        self.assertEqual(values["readout_loss"]["value"], 1 / 4)

    def test_cluster_pairing_and_partial_counts(self):
        pairs = {"t1": [(1, 0)] * 10, "t2": [(0, 1)]}
        values = paired_bootstrap(pairs, samples=100)
        self.assertEqual(values["effect"], 0)  # Equal tasks, not repeated records.
        self.assertEqual(values, paired_bootstrap(pairs, samples=100))
        self.assertIsNone(paired_bootstrap({"one": [(1, 0)]})["ci95"])
        summary = summarize([row([True] * 3, [True] * 3, True)], 10, 1, 100)
        self.assertEqual(summary["missing_records"], 9)
        self.assertEqual(summary["status"], "partial_collection")
