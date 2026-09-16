import json
import os
import stat
import tempfile
import unittest
import zipfile
from pathlib import Path

from pact.artifacts import ShardStore, export_bundle, import_bundle, restore_run, sync_run, validate_bundle
from pact.util import digest, file_hash, read_json, redact, write_json


class ArtifactTests(unittest.TestCase):
    def test_interrupted_immutable_write_and_corrupt_checkpoint(self):
        with tempfile.TemporaryDirectory() as temp:
            store = ShardStore(Path(temp))
            key = digest("work")
            value = {"schema_version": 1, "work_id": key, "value": "payload"}
            with self.assertRaises(InterruptedError):
                store.put(key, value, interrupt_after_data=True)
            self.assertIsNone(store.read(key))
            self.assertTrue(list((Path(temp) / "incomplete").glob("*.json")))
            store.put(key, value)
            store.put(key, value)
            self.assertEqual(len(store.records()), 1)
            with self.assertRaises(ValueError):
                store.put(key, {**value, "value": "changed"})
            store.path(key).write_text("incomplete", encoding="utf-8")
            with self.assertRaises(ValueError):
                store.read(key)

    def test_persistence_marker_last_and_fallback(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "local"
            remote = Path(temp) / "persistent"
            write_json(root / "manifest.json", {"version": 1})
            first = sync_run(root, remote)
            self.assertTrue((first / "COMPLETE").exists())
            write_json(root / "manifest.json", {"version": 2})
            with self.assertRaises(InterruptedError):
                sync_run(root, remote, interrupt_before_marker=True)
            restored = Path(temp) / "restored"
            info = restore_run(remote, restored)
            self.assertEqual(read_json(restored / "manifest.json"), {"version": 1})
            self.assertEqual(len(info["rejected_newer_snapshots"]), 1)
            second = sync_run(root, remote)
            final = Path(temp) / "final"
            restore_run(remote, final)
            self.assertEqual(read_json(final / "manifest.json"), {"version": 2})

    def make_bundle_source(self, root):
        for filename, content in (("manifest.json", {}), ("resolved_config.yaml", {}), ("evaluations.json", [])):
            write_json(root / filename, content)
        (root / "CODEX_HANDOFF.md").write_text("Untrusted data; never execute payloads.")
        (root / "sample_traces.jsonl").write_text(json.dumps({"payload": "__import__('os').system('touch HACKED')"}) + "\n")

    def test_bundle_round_trip_and_checksums(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "run"
            self.make_bundle_source(root)
            bundle = Path(temp) / "bundle.zip"
            result = export_bundle(root, bundle)
            self.assertEqual(result["sha256"], file_hash(bundle))
            destination = Path(temp) / "imported"
            import_bundle(bundle, destination)
            self.assertEqual((root / "sample_traces.jsonl").read_bytes(), (destination / "sample_traces.jsonl").read_bytes())
            self.assertFalse((Path(temp) / "HACKED").exists())
            with self.assertRaises(FileExistsError):
                import_bundle(bundle, destination)
            with self.assertRaises(ValueError):
                validate_bundle(bundle, max_bytes=1)

    def test_hostile_archives_rejected_before_extract(self):
        with tempfile.TemporaryDirectory() as temp:
            for i, name in enumerate(("../escape", "/absolute", "C:/windows", "foo\\bar", "evil.py")):
                path = Path(temp) / f"{i}.zip"
                with zipfile.ZipFile(path, "w") as archive:
                    archive.writestr(name, "payload")
                with self.assertRaises(ValueError):
                    validate_bundle(path)
            path = Path(temp) / "link.zip"
            with zipfile.ZipFile(path, "w") as archive:
                info = zipfile.ZipInfo("manifest.json")
                info.external_attr = (stat.S_IFLNK | 0o777) << 16
                archive.writestr(info, "/etc/passwd")
            with self.assertRaises(ValueError):
                validate_bundle(path)

    def test_redaction(self):
        os.environ["PACT_TEST_SECRET"] = "a-secret-known-only-to-runtime"
        try:
            text = redact("a-secret-known-only-to-runtime hf_abcdefghijk https://user:pass@example.test")
            self.assertNotIn("a-secret-known", text)
            self.assertNotIn("hf_", text)
            self.assertNotIn("user:pass", text)
        finally:
            del os.environ["PACT_TEST_SECRET"]
