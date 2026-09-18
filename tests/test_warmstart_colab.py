import contextlib
import hashlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import zipfile

from pact.artifacts import _sync_run
from pact.training.checkpoints import commit_checkpoint, latest_checkpoint
from pact.training.colab import handoff, restore_snapshot, _restore_snapshot
from pact.util import file_hash, read_json, write_json


class WarmstartColabTests(unittest.TestCase):
    def fixture(self, root):
        identity = {"fixture": "storage only, not neural training"}
        write_json(root / "run.json", {"identity": identity})
        write_json(root / "examples.json", [{"fixture": True}])
        write_json(root / "status.json", {"completed_steps": 1})
        for step in range(2):
            commit_checkpoint(root / "checkpoints", step=step, identity=identity, tree={},
                              write_tensors=lambda p: p.write_bytes(b"fixture checkpoint bytes"))
        return identity

    def test_handoff_and_deadline_worker_restore_full_checkpoints(self):
        with tempfile.TemporaryDirectory() as tmp, contextlib.redirect_stdout(io.StringIO()):
            base = Path(tmp)
            root = base / "run"
            identity = self.fixture(root)
            result = handoff(root=root, bundles=base / "bundles", persistent=base / "drive", run_id="fixture",
                             outcome={"exit_code": 0}, timeout_seconds=10)
            self.assertTrue(result["persistent_copy_verified"])
            self.assertEqual(result["exit_code"], 0)
            self.assertEqual(file_hash(Path(result["persistent_bundle"])), result["sha256"])
            with zipfile.ZipFile(result["path"]) as archive:
                self.assertFalse(any(n.endswith(".safetensors") for n in archive.namelist()))
                receipt = json.loads(archive.read("HANDOFF.json"))
                self.assertFalse(receipt["resume_archive"])
                self.assertTrue(receipt["outcome"]["persistent_copy_verified"])
                self.assertIn("checkpoints/step-000001/tensors.safetensors", receipt["inventory"])
                checksums = json.loads(archive.read("review_checksums.json"))
                self.assertEqual(set(checksums), set(archive.namelist()) - {"review_checksums.json"})
                for name, sha in checksums.items():
                    self.assertEqual(hashlib.sha256(archive.read(name)).hexdigest(), sha)
            restored = base / "restored"
            restore_snapshot(result["persistent_snapshot"], restored, timeout_seconds=10)
            self.assertEqual(latest_checkpoint(restored / "checkpoints", identity)[1]["step"], 1)
            for p in root.rglob("*"):
                if p.is_file():
                    self.assertEqual(p.read_bytes(), (restored / p.relative_to(root)).read_bytes())
            with self.assertRaises(ValueError):
                restore_snapshot(result["persistent_snapshot"], restored, timeout_seconds=10)

    def test_corruption_and_traversal_reject_without_publishing_partial_restore(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            root = base / "run"
            self.fixture(root)
            snapshot = _sync_run(root, base / "drive")
            index = read_json(snapshot / "index.json")
            obj = base / "drive" / "objects" / index["files"]["examples.json"]
            obj.write_bytes(b"corrupt")
            with self.assertRaisesRegex(ValueError, "Corrupt"):
                _restore_snapshot(snapshot, base / "restore")
            self.assertFalse((base / "restore").exists())
            snapshot = _sync_run(root, base / "drive")
            index = read_json(snapshot / "index.json")
            index["files"]["../escape"] = index["files"]["examples.json"]
            write_json(snapshot / "index.json", index)
            (snapshot / "COMPLETE").write_text(file_hash(snapshot / "index.json"))
            with self.assertRaises(ValueError):
                _restore_snapshot(snapshot, base / "restore")
            self.assertFalse((base / "escape").exists())
            self.assertFalse((base / "restore").exists())

    def test_timeout_keeps_local_review_and_retry_does_not_train(self):
        with tempfile.TemporaryDirectory() as tmp, contextlib.redirect_stdout(io.StringIO()):
            base = Path(tmp)
            root = base / "run"
            self.fixture(root)
            kwargs = dict(root=root, bundles=base / "bundles", persistent=base / "drive", run_id="fixture",
                          outcome={"exit_code": 130}, timeout_seconds=10)
            with patch("pact.training.colab.sync_run", side_effect=TimeoutError("fixture mount stall")), \
                    patch("pact.training.warmstart.run_warmstart") as train:
                failed = handoff(**kwargs)
                self.assertFalse(failed["persistent_copy_verified"])
                self.assertTrue(Path(failed["path"]).is_file())
                self.assertEqual(failed["exit_code"], 2)
                with zipfile.ZipFile(failed["path"]) as archive:
                    self.assertEqual(json.loads(archive.read("HANDOFF.json"))["outcome"]["exit_code"], 130)
                train.assert_not_called()
            with patch("pact.training.warmstart.run_warmstart") as train:
                retried = handoff(**kwargs)
                self.assertTrue(retried["persistent_copy_verified"])
                self.assertEqual(retried["exit_code"], 130)  # Persistence cannot erase a training failure.
                self.assertNotEqual(retried["path"], failed["path"])
                train.assert_not_called()

    def test_missing_checkpoints_cannot_claim_recovery(self):
        with tempfile.TemporaryDirectory() as tmp, contextlib.redirect_stdout(io.StringIO()):
            base = Path(tmp)
            result = handoff(root=base / "absent", bundles=base / "bundles", persistent=base / "drive",
                             run_id="failed-preflight", outcome={"exit_code": 2})
            self.assertFalse(result["persistent_copy_verified"])
            self.assertIsNone(result["persistent_snapshot"])
            self.assertTrue(Path(result["path"]).exists())

    def test_notebook_cells_compile_and_execution_is_explicit(self):
        notebook = json.loads(Path("notebooks/02_warmstart_colab.ipynb").read_text())
        cells = [c for c in notebook["cells"] if c["cell_type"] == "code"]
        for c in cells:
            self.assertEqual(c["outputs"], [])
            self.assertIsNone(c["execution_count"])
            compile("".join(c["source"]), "02_warmstart_colab.ipynb", "exec")
        params = {}
        exec("".join(cells[0]["source"]), params)
        self.assertFalse(params["EXECUTE"])
        self.assertFalse(params["RESUME"])
        self.assertEqual(params["STOP_AFTER"], 1)
        # Exercise the actual notebook execution gate: Run All cannot train by default.
        for c in cells:
            source = "".join(c["source"])
            if "HANDOFF = execute(" in source:
                with patch("pact.training.colab.execute") as execute, contextlib.redirect_stdout(io.StringIO()):
                    exec(source, params)
                    execute.assert_not_called()
