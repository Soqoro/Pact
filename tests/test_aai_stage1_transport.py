"""CPU-only transport integrity checks; no real study inputs or network."""
import contextlib
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest
import zipfile

spec = importlib.util.spec_from_file_location('aai_transport', Path(__file__).resolve().parents[1] / 'tools/aai_stage1_transport.py')
t = importlib.util.module_from_spec(spec)
spec.loader.exec_module(t)


class TransportTests(unittest.TestCase):
    def test_paths_rejected(self):
        for value in ('../escape', '/absolute', 'a/../../escape', 'a\\escape', ''):
            with self.assertRaises(ValueError):
                t.safe_name(value)

    def test_pending_stops_before_snapshot_access(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'INFLIGHT.json').write_text('{}')
            with self.assertRaisesRegex(ValueError, 'Pending'):
                t.safe_boundary(root)

    def test_no_fallback_to_older_snapshot(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            old = root / 'snapshots/001'
            old.mkdir(parents=True)
            raw = json.dumps({'files': {'state.zip': 'a'*64, 'receipt.json': 'b'*64}}).encode()
            (old / 'index.json').write_bytes(raw)
            (old / 'COMPLETE').write_text(t.hashlib.sha256(raw).hexdigest())
            self.assertEqual(t.safe_boundary(root)[0], old)
            (root / 'snapshots/002').mkdir()
            with self.assertRaises(FileNotFoundError):
                t.safe_boundary(root)

    def test_transport_checks_outer_and_inner_hashes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for corrupt in (False, True):
                path = root / str(corrupt)
                payload = b'fixture'
                meta = {'format': 'aai_stage1_transport_v1', 'run_id': t.RUN,
                        'plan_hash': t.PLAN, 'resolution_hash': t.RESOLUTION, 'snapshot': 'fixture',
                        'files': {'inputs/fixture': t.hashlib.sha256(payload).hexdigest()}}
                with zipfile.ZipFile(path, 'w') as z:
                    z.writestr('inputs/fixture', b'changed' if corrupt else payload)
                    z.writestr('TRANSPORT.json', json.dumps(meta))
                if corrupt:
                    with self.assertRaisesRegex(ValueError, 'member checksum'):
                        t.verify(path, t.file_sha(path))
                else:
                    with contextlib.redirect_stdout(io.StringIO()):
                        t.verify(path, t.file_sha(path))
                    with self.assertRaisesRegex(ValueError, 'archive checksum'):
                        t.verify(path, '0'*64)

    def test_pack_preserves_existing_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'existing.zip'
            path.write_bytes(b'evidence')
            with self.assertRaisesRegex(ValueError, 'Output exists'):
                t.pack(Path(tmp), path)
            self.assertEqual(path.read_bytes(), b'evidence')


if __name__ == '__main__':
    unittest.main()
