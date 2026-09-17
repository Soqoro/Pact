import contextlib
import dataclasses
import io
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

from pact.artifacts import sync_run, validate_bundle
from pact.colab import execute
from pact.config import Config, ProbeConfig
from pact.runner import RunFailed, run
from pact.storage import persist_bundle
from pact.util import file_hash, read_json, write_json


class StorageRecoveryTests(unittest.TestCase):
    def config(self):
        return Config(probe=ProbeConfig(tasks=0), bootstrap_samples=20, sync_every=1000)

    def test_blocked_storage_worker_has_deadline(self):
        with tempfile.TemporaryDirectory() as temp, contextlib.redirect_stdout(io.StringIO()):
            source, target = Path(temp) / "run", Path(temp) / "remote"
            write_json(source / "manifest.json", {"status": "pending"})
            real_popen = subprocess.Popen
            children = []
            def blocked_worker(command, **kwargs):
                process = real_popen([sys.executable, "-c", "import time; time.sleep(60)"], **kwargs)
                children.append(process)
                return process
            started = time.monotonic()
            with patch("pact.storage.subprocess.Popen", side_effect=blocked_worker):
                with self.assertRaisesRegex(TimeoutError, "local results retained"):
                    sync_run(source, target, timeout_seconds=0.2)
            self.assertLess(time.monotonic() - started, 5)
            self.assertIsNotNone(children[0].poll())
            self.assertFalse(list(target.glob("snapshots/*/COMPLETE")))
            self.assertTrue((source / "manifest.json").is_file())

    def test_final_sync_failure_has_local_bundle_and_honest_status(self):
        with tempfile.TemporaryDirectory() as temp, contextlib.redirect_stdout(io.StringIO()):
            scratch, persistent = Path(temp) / "scratch", Path(temp) / "remote"
            def blocked_sync(root, remote):
                bundles = list((scratch / "bundles").glob("*-local-*.zip"))
                self.assertEqual(len(bundles), 1)
                payload = validate_bundle(bundles[0])
                self.assertIn(b'"persistence":"pending"', payload["manifest.json"])
                self.assertEqual(read_json(root / "manifest.json")["stage_status"]["persistence"], "pending")
                raise TimeoutError("simulated blocked Drive")
            with patch("pact.runner.sync_run", side_effect=blocked_sync) as sync:
                with self.assertRaisesRegex(RunFailed, "Persistence failed"):
                    run(self.config(), run_id="complete", scratch=scratch, persistent=persistent)
            sync.assert_called_once()
            root = scratch / "runs" / "complete"
            manifest = read_json(root / "manifest.json")
            self.assertEqual(manifest["completed_records"], 12)
            self.assertEqual(manifest["stage_status"]["collection"], "complete")
            self.assertEqual(manifest["stage_status"]["persistence"], "failed")
            self.assertNotIn("verified_snapshot", manifest)
            self.assertIn("simulated blocked Drive", (root / "failures.jsonl").read_text())
            self.assertEqual(read_json(root / "metrics.json")["missing_records"], 0)

    def test_success_claim_follows_verified_marker(self):
        with tempfile.TemporaryDirectory() as temp, contextlib.redirect_stdout(io.StringIO()):
            with patch("pact.runner.sync_run", wraps=sync_run) as sync:
                root = run(dataclasses.replace(self.config(), sync_every=6), run_id="complete",
                           scratch=Path(temp) / "scratch", persistent=Path(temp) / "remote")
            # One intermediate checkpoint plus one final snapshot, not a redundant
            # periodic sync at 12/12 before making the local recovery ZIP.
            self.assertEqual(sync.call_count, 2)
            manifest = read_json(root / "manifest.json")
            self.assertEqual(manifest["stage_status"]["persistence"], "complete")
            snapshot = Path(manifest["verified_snapshot"])
            self.assertEqual((snapshot / "COMPLETE").read_text(), file_hash(snapshot / "index.json"))
            index = read_json(snapshot / "index.json")
            # The snapshot describes the pending intent; its verified marker is the receipt.
            saved = read_json(snapshot.parent.parent / "objects" / index["files"]["manifest.json"])
            self.assertEqual(saved["stage_status"]["persistence"], "pending")

    def test_bundle_copy_checks_source_and_destination(self):
        with tempfile.TemporaryDirectory() as temp, contextlib.redirect_stdout(io.StringIO()):
            source = Path(temp) / "bundle.zip"
            source.write_bytes(b"a small local artifact")
            target = Path(temp) / "remote" / source.name
            sha = file_hash(source)
            persist_bundle(source, target, sha)
            self.assertEqual(file_hash(target), sha)
            self.assertEqual(target.with_suffix(".zip.sha256").read_text().strip(), sha)
            other = Path(temp) / "remote" / "bad.zip"
            with self.assertRaisesRegex(ValueError, "checksum changed"):
                persist_bundle(source, other, "0" * 64)
            self.assertFalse(other.exists())

    def test_notebook_returns_local_handoff_when_bundle_copy_stalls(self):
        with tempfile.TemporaryDirectory() as temp, contextlib.redirect_stdout(io.StringIO()):
            scratch, remote = Path(temp) / "scratch", Path(temp) / "remote"
            root = run(self.config(), run_id="ready", scratch=scratch)
            # The wrapper gets an already collected run; no generation in this test.
            def blocked_copy(source, destination, sha):
                self.assertEqual(file_hash(source), sha)
                validate_bundle(source)
                raise TimeoutError("simulated stalled bundle copy")
            with patch("pact.colab.main", return_value=0), patch("pact.colab.persist_bundle", side_effect=blocked_copy):
                result = execute(checkout=Path.cwd(), preset="smoke", run_id="ready", scratch=scratch, persistent=remote)
            self.assertEqual(result["exit_code"], 2)
            self.assertIsNone(result["persistent_bundle"])
            self.assertTrue(Path(result["path"]).is_file())
            self.assertIn("stalled", result["persistence_error"])
            self.assertEqual(read_json(root / "manifest.json")["completed_records"], 12)
            with patch("pact.colab.main", return_value=2), patch("pact.colab.persist_bundle") as copy:
                retry = execute(checkout=Path.cwd(), preset="smoke", run_id="ready", scratch=scratch, persistent=remote)
            copy.assert_not_called()
            self.assertTrue(Path(retry["path"]).is_file())
