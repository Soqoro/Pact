import contextlib
import dataclasses
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from pact.artifacts import ShardStore, export_bundle, import_bundle
from pact.attacks import fixed_attack
from pact.backends.mock import MockBackend
from pact.config import Config, ProbeConfig, SelectedConfig, SelectedTask, SelectionConfig, budget, config_from_dict, load_config
from pact.datasets import prepare
from pact.protocol import Protocol
from pact.reporting import report
from pact.runner import RunFailed, run
from pact.util import digest, file_hash, read_json


class SelectionTests(unittest.TestCase):
    def fixture(self, cache):
        source = Config(stage="pilot", items=8, methods=("debate",), conditions=("clean", "exchange"),
                        probe=ProbeConfig(tasks=3), bootstrap_samples=20, sync_every=1000)
        tasks, labels, manifest = prepare(source, cache)
        # Purposefully not selected positions 0/1/2: source senders must survive filtering.
        chosen_ids = ["mock_arc:004-positive", "mock_logiqa:005-negative", "mock_arc:006-zero"]
        chosen = []
        backend = MockBackend(source)
        for tid in chosen_ids:
            position = next(i for i, t in enumerate(tasks) if t.task_id == tid)
            attacks = [fixed_attack(tasks[position], labels[tid], c, position, source.seed, backend, 256).attack_id
                       for c in ("clean", "exchange")]
            chosen.append(SelectedTask(tid, position, digest(tasks[position]), digest(labels[tid]), *attacks))
        selection = SelectionConfig("original-fixture", source.identity, digest(manifest),
                                    MockBackend(source).identity["snapshot"], source.generation_identity, 8, tuple(chosen))
        config = SelectedConfig(**{**dataclasses.asdict(source), "model": source.model, "limits": source.limits,
                                   "sampling": source.sampling, "probe": source.probe, "items": 3,
                                   "purpose": "selected_replay_feasibility"}, selection=selection).validate()
        return source, config, tasks, labels, manifest

    def test_real_preset_bounds_and_legacy_identity(self):
        original = load_config("configs/pilot/validation_80.yaml")
        self.assertEqual(original.identity, "92d66df5ede5d68cefed7f347290872aa36cbfe0ce0414e0b0295888d531db5a")
        config = load_config("configs/pilot/replay_check_3.yaml")
        self.assertEqual(config_from_dict(dataclasses.asdict(config)), config)
        self.assertEqual(config.generation_identity, original.generation_identity)
        self.assertEqual(config.selection.source_config_hash, original.identity)
        self.assertEqual([t.source_position for t in config.selection.tasks], [41, 61, 70])
        self.assertEqual(budget(config)["total_calls_upper_bound"], 474)
        self.assertEqual(budget(config)["total_output_tokens_upper_bound"], 106368)
        self.assertEqual(budget(config)["trajectory_calls_upper_bound"], 42)
        for change in ({"items": 3}, {"purpose": "selected_replay_feasibility"}):
            with self.assertRaises(ValueError):
                config_from_dict(change)
        for change in ({"seed": 1}, {"items": 4}, {"methods": ("archive",)},
                       {"conditions": ("early",)}, {"probe": ProbeConfig(tasks=3, candidates=3)},
                       {"limits": dataclasses.replace(config.limits, packet=128)},
                       {"sampling": dataclasses.replace(config.sampling, temperature=1.)}):
            with self.subTest(change=change), self.assertRaises(ValueError):
                dataclasses.replace(config, **change).validate()

    def test_selected_hashes_positions_and_rejection(self):
        with tempfile.TemporaryDirectory() as temp:
            cache = Path(temp)
            source, config, original, labels, old_manifest = self.fixture(cache)
            tasks, selected_labels, manifest = prepare(config, cache)
            self.assertEqual(len(tasks), 3)
            self.assertEqual(manifest["family_counts"], {"mock_arc": 2, "mock_logiqa": 1})
            self.assertIn("not representative", manifest["selection"])
            for task, chosen, entry in zip(tasks, config.selection.tasks, manifest["selected"]):
                self.assertEqual(task, original[chosen.source_position])
                self.assertEqual(selected_labels[task.task_id], labels[task.task_id])
                self.assertEqual(entry["source_position"], chosen.source_position)
            first = config.selection.tasks[0]
            for field in ("source_manifest_hash",):
                bad = dataclasses.replace(config, selection=dataclasses.replace(config.selection, **{field: "0" * 64}))
                with self.assertRaisesRegex(ValueError, "Source data manifest mismatch"):
                    prepare(bad, cache)
            for change in ({"input_hash": "0" * 64}, {"label_hash": "0" * 64},
                           {"task_id": "mock_arc:absent"}, {"source_position": 0}):
                changed = (dataclasses.replace(first, **change), *config.selection.tasks[1:])
                bad = dataclasses.replace(config, selection=dataclasses.replace(config.selection, tasks=changed))
                with self.subTest(change=change), self.assertRaises(ValueError):
                    prepare(bad, cache)
            duplicate = dataclasses.replace(config.selection, tasks=(first, first, config.selection.tasks[2]))
            with self.assertRaisesRegex(ValueError, "unique"):
                dataclasses.replace(config, selection=duplicate).validate()

    def test_runner_preserves_attacks_seeds_pairs_resume_and_handoff(self):
        with tempfile.TemporaryDirectory() as temp, contextlib.redirect_stdout(io.StringIO()):
            scratch = Path(temp) / "scratch"
            source, config, originals, labels, _ = self.fixture(scratch / "cache")
            with self.assertRaises(RunFailed):
                run(config, run_id="selected", scratch=scratch, stop_after=2)
            root = scratch / "runs" / "selected"
            hashes = {p.name: file_hash(p) for p in (root / "shards").glob("*.json")}
            run(config, run_id="selected", scratch=scratch, resume=True)
            records = ShardStore(root).records()
            self.assertEqual(len(records), 6)
            for name, sha in hashes.items():
                self.assertEqual(file_hash(root / "shards" / name), sha)
            backend = MockBackend(source)
            protocol = Protocol(source, backend)
            chosen = {t.task_id: t for t in config.selection.tasks}
            eligible = []
            for rec in records:
                t = rec["trajectory"]
                entry = chosen[t["task"]["task_id"]]
                task = originals[entry.source_position]
                attack = fixed_attack(task, labels[task.task_id], t["condition"], entry.source_position,
                                      source.seed, backend, source.limits.payload)
                prior = protocol.run(task, "debate", attack)
                self.assertEqual(t["attack"], dataclasses.asdict(attack))
                self.assertEqual(t["seed"], prior.seed)
                # Check actual messages, samples and seeds, not merely a position field.
                self.assertEqual(json.dumps(t["private"], sort_keys=True),
                                 json.dumps([dataclasses.asdict(p) for p in prior.private], sort_keys=True))
                self.assertEqual(len(rec["replays"]), 3)
                for pair in rec["replays"]:
                    if pair["status"] != "eligible":
                        self.assertIsNone(pair["delta"])
                        continue
                    eligible.append(pair)
                    for positive, negative in zip(pair["positive_suffixes"], pair["negative_suffixes"]):
                        self.assertEqual([c["seed"] for c in positive["calls"]], [c["seed"] for c in negative["calls"]])
                        self.assertEqual(positive["attack"], negative["attack"])
                        for branch in (positive, negative):
                            for i, packet in enumerate(branch["private"]):
                                if i != pair["agent"]:
                                    self.assertEqual(packet, t["private"][i])
                            if t["condition"] == "exchange":
                                self.assertTrue(all(d["text"] == attack.payload for d in branch["delivered"] if d["sender"] == attack.sender))
                for pref in rec["preferences"]:
                    self.assertTrue(all(p["call"]["context_hash"] == pref["context_hash"] for p in pref["candidates"]))
            self.assertTrue(eligible, "This CPU check must actually execute both suffix branches")
            resources = read_json(root / "resource_usage.json")
            self.assertLessEqual(resources["calls"], 474)
            bundle = Path(temp) / "selected.zip"
            export_bundle(root, bundle)
            imported = Path(temp) / "imported"
            import_bundle(bundle, imported)
            self.assertEqual(report(imported), read_json(root / "metrics.json"))
            self.assertIn("no representative performance", report(imported)["inference_scope"])
            samples = [json.loads(line) for line in (imported / "sample_traces.jsonl").read_text().splitlines()]
            self.assertEqual({r["work_id"] for r in samples}, {r["work_id"] for r in records})
            self.assertTrue(all(len(r["replays"]) == 3 for r in samples))
            with self.assertRaisesRegex(ValueError, "Configuration/code mismatch"):
                run(dataclasses.replace(config, bootstrap_samples=21), run_id="selected", scratch=scratch, resume=True)

    def test_incompatible_source_stops_before_generation(self):
        with tempfile.TemporaryDirectory() as temp, contextlib.redirect_stdout(io.StringIO()):
            scratch = Path(temp)
            _, config, _, _, _ = self.fixture(scratch / "cache")
            with self.assertRaisesRegex(ValueError, "new run ID"):
                run(config, run_id=config.selection.source_run_id, scratch=scratch)
            backend = MockBackend(config)
            backend.identity["snapshot"] = "wrong-model"
            with patch.object(backend, "generate") as generate:
                with self.assertRaisesRegex(RunFailed, "source model snapshot mismatch"):
                    run(config, run_id="wrong-model", scratch=scratch, backend_factory=lambda c, p: backend)
                generate.assert_not_called()
            bad = dataclasses.replace(config, selection=dataclasses.replace(config.selection, source_manifest_hash="0" * 64))
            with patch("pact.runner.create_backend") as factory:
                with self.assertRaisesRegex(RunFailed, "Source data manifest mismatch"):
                    run(bad, run_id="wrong-data", scratch=scratch, backend_factory=factory)
                factory.assert_not_called()
            changed = (*config.selection.tasks[:2],
                       dataclasses.replace(config.selection.tasks[2], exchange_attack_id="0" * 64))
            bad = dataclasses.replace(config, selection=dataclasses.replace(config.selection, tasks=changed))
            backend = MockBackend(config)
            with patch.object(backend, "generate") as generate:
                with self.assertRaisesRegex(RunFailed, "source attack mismatch"):
                    run(bad, run_id="wrong-attack", scratch=scratch, backend_factory=lambda c, p: backend)
                generate.assert_not_called()
