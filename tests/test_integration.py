import contextlib
import dataclasses
import io
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path

from pact.artifacts import ShardStore, export_bundle, import_bundle
from pact.backends.mock import MockBackend
from pact.config import Config, ProbeConfig
from pact.reporting import report
from pact.runner import RunFailed, inspect_run, run
from pact.util import read_json, file_hash


class IntegrationTests(unittest.TestCase):
    def config(self):
        return Config(methods=("debate", "single", "synthesis"), probe=ProbeConfig(tasks=1), bootstrap_samples=30, sync_every=6)

    def test_interruption_resume_export_import_offline(self):
        with tempfile.TemporaryDirectory() as temp, contextlib.redirect_stdout(io.StringIO()):
            scratch = Path(temp) / "scratch"
            persistent = Path(temp) / "persistent"
            config = self.config()
            with self.assertRaises(RunFailed):
                run(config, run_id="roundtrip", scratch=scratch, persistent=persistent, stop_after=3)
            root = scratch / "runs" / "roundtrip"
            first_hashes = {p.name: file_hash(p) for p in (root / "shards").glob("*.json")}
            self.assertEqual(inspect_run(root)["completed"], 3)
            self.assertEqual(read_json(root / "metrics.json")["status"], "partial_collection")
            self.assertTrue(list((scratch / "bundles").glob("*.zip")))
            run(config, run_id="roundtrip", scratch=scratch, persistent=persistent, resume=True)
            self.assertEqual(inspect_run(root)["missing"], 0)
            self.assertEqual(len(ShardStore(root).records()), 36)
            for name, sha in first_hashes.items():
                self.assertEqual(file_hash(root / "shards" / name), sha)
            before = read_json(root / "metrics.json")
            run(config, run_id="roundtrip", scratch=scratch, persistent=persistent, resume=True)
            self.assertEqual(read_json(root / "metrics.json"), before)
            bundle = Path(temp) / "bundle.zip"
            export_bundle(root, bundle)
            imported = Path(temp) / "imported"
            import_bundle(bundle, imported)
            again = report(imported)
            self.assertEqual(again, before)
            for name, sha in read_json(imported / "checksums.json").items():
                self.assertEqual(file_hash(imported / name), sha)
            self.assertTrue((imported / "analysis" / "metrics.json").exists())
            self.assertEqual(read_json(root / "resource_usage.json")["compute_units"], None)
            # A new ephemeral runtime resumes from verified persistent objects.
            other = Path(temp) / "fresh-runtime"
            restored = run(config, run_id="roundtrip", scratch=other, persistent=persistent, resume=True)
            self.assertEqual(inspect_run(restored)["completed"], 36)

    def test_mismatch_and_overwrite_rejected(self):
        with tempfile.TemporaryDirectory() as temp, contextlib.redirect_stdout(io.StringIO()):
            config = self.config()
            scratch = Path(temp)
            run(config, run_id="test", scratch=scratch)
            with self.assertRaises(FileExistsError):
                run(config, run_id="test", scratch=scratch)
            with self.assertRaisesRegex(ValueError, "Configuration/code mismatch"):
                run(dataclasses.replace(config, seed=7), run_id="test", scratch=scratch, resume=True)
            def changed_backend(config, path):
                backend = MockBackend(config)
                backend.identity["snapshot"] = "changed-checkpoint"
                return backend
            with self.assertRaisesRegex(RunFailed, "snapshot mismatch"):
                run(config, run_id="test", scratch=scratch, resume=True, backend_factory=changed_backend)

    def test_oom_diagnostic_bundle_preserves_settings(self):
        with tempfile.TemporaryDirectory() as temp, contextlib.redirect_stdout(io.StringIO()):
            config = self.config()
            def unavailable(config, path):
                raise RuntimeError("CUDA out of memory (simulated)")
            with self.assertRaisesRegex(RunFailed, "Diagnostic bundle"):
                run(config, run_id="oom", scratch=Path(temp), backend_factory=unavailable)
            root = Path(temp) / "runs" / "oom"
            self.assertEqual(read_json(root / "resolved_config.yaml")["limits"], dataclasses.asdict(config.limits))
            self.assertEqual(read_json(root / "metrics.json")["missing_records"], 36)
            self.assertTrue(list((Path(temp) / "bundles").glob("*.zip")))

    def test_failed_sync_retains_diagnostic_and_recovers(self):
        with tempfile.TemporaryDirectory() as temp, contextlib.redirect_stdout(io.StringIO()):
            config = self.config()
            scratch, persistent = Path(temp) / "scratch", Path(temp) / "persistent"
            with patch("pact.runner.sync_run", side_effect=OSError("simulated storage interruption")):
                with self.assertRaisesRegex(RunFailed, "Persistence failed"):
                    run(config, run_id="storage", scratch=scratch, persistent=persistent)
            self.assertTrue(list((scratch / "bundles").glob("*.zip")))
            restored = run(config, run_id="storage", scratch=scratch, persistent=persistent, resume=True)
            self.assertEqual(inspect_run(restored)["missing"], 0)

    def test_marked_corrupt_shard_is_rejected_with_diagnostics(self):
        with tempfile.TemporaryDirectory() as temp, contextlib.redirect_stdout(io.StringIO()):
            root = run(self.config(), run_id="corrupt", scratch=Path(temp))
            path = next((root / "shards").glob("*.json"))
            path.write_text("incomplete", encoding="utf-8")
            with self.assertRaisesRegex(RunFailed, "Completed shard corrupted"):
                run(self.config(), run_id="corrupt", scratch=Path(temp), resume=True)
            self.assertTrue(list((Path(temp) / "bundles").glob("*.zip")))
