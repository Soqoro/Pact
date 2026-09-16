import dataclasses
import unittest

from pact.attacks import fixed_attack
from pact.backends import Request, cache_key
from pact.backends.mock import MockBackend
from pact.config import Config, ProbeConfig
from pact.datasets import fixtures
from pact.protocol import Protocol, private_prompt
from pact.replay import probe, choose_pair


class ReplayTests(unittest.TestCase):
    def test_fixed_attack_suffix_seeds_and_missing_pairs(self):
        config = Config(items=8, probe=ProbeConfig(tasks=8))
        backend = MockBackend(config)
        protocol = Protocol(config, backend)
        credits = set()
        for position, (task, label) in enumerate(fixtures(8)):
            attack = fixed_attack(task, label, "exchange", position, config.seed, backend, 256)
            trajectory = protocol.run(task, "debate", attack)
            pairs, preferences = probe(protocol, trajectory, label)
            for pair in pairs:
                if pair.status == "missing_pair":
                    self.assertIsNone(pair.delta)
                    self.assertFalse(pair.positive_suffixes)
                    continue
                credits.add(pair.delta)
                self.assertEqual(len(pair.positive_suffixes), 2)
                self.assertEqual(pair.delta, sum(pair.paired_differences) / 2)
                for plus, minus in zip(pair.positive_suffixes, pair.negative_suffixes):
                    self.assertEqual(len(plus.calls), 4)
                    self.assertEqual([c.seed for c in plus.calls], [c.seed for c in minus.calls])
                    self.assertEqual(plus.attack, minus.attack)
                    for i in range(3):
                        if i != pair.agent:
                            self.assertEqual(plus.private[i], trajectory.private[i])
                            self.assertEqual(minus.private[i], trajectory.private[i])
                    for branch in (plus, minus):
                        self.assertTrue(all(m.text == attack.payload for m in branch.delivered if m.sender == attack.sender))
            for pref in preferences:
                self.assertTrue(all(c.call.context_hash == pref.context_hash for c in pref.candidates))
        self.assertIn(0.0, credits)
        self.assertIn(-1.0, credits)
        self.assertIn(1.0, credits)

    def test_malformed_counterpart_never_selected(self):
        config = Config()
        backend = MockBackend(config)
        protocol = Protocol(config, backend)
        task, label = fixtures(4)[0]
        attack = fixed_attack(task, label, "clean", 0, 0, backend, 256)
        good = protocol.private_packet(task, 0, attack, 1)
        bad = dataclasses.replace(good, parser_status="malformed", answer_id=None)
        self.assertEqual(choose_pair([good, bad], "A", 32)[3], "missing_incorrect")

    def test_cache_identity_and_checkpoint_sensitive(self):
        task, _ = fixtures(4)[0]
        config = Config()
        request = Request(task, private_prompt(task, ""), "agent-0", "private", 1, 256)
        key = cache_key(request, {"snapshot": "one"}, config, "prompt")
        for req, identity, rendered in ((request, {"snapshot": "two"}, "prompt"),
                                        (dataclasses.replace(request, seed=2), {"snapshot": "one"}, "prompt"),
                                        (request, {"snapshot": "one"}, "different")):
            self.assertNotEqual(key, cache_key(req, identity, config, rendered))
