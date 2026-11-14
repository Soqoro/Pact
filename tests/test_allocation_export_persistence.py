"""Real CPU filesystem persistence, not a mock of the checksum-bearing API."""
import tempfile
import unittest
from pathlib import Path
from pact.util import digest, file_hash, read_json, write_json
from pact.revival.allocation_v3 import storage


class ExportPersistenceTests(unittest.TestCase):
    def test_all_three_bundles_and_compact_snapshot_are_verified(self):
        with tempfile.TemporaryDirectory() as tmp:
            base=Path(tmp);root=base/'scratch'/'fixture-export'
            destination=base/'durable'/root.name
            plan={'run_id':root.name,'fixture':True}
            write_json(root/'plan.json',plan)
            write_json(root/'summary.json',{'model_calls':0,'fixture':True})
            result=storage.export(root,'inactive-plan',destination)
            self.assertEqual(set(result),{'PRIVATE','SANITIZED','RECOVERY'})
            for info in result.values():
                source=Path(info['path']);copy=destination/'bundles'/source.name
                self.assertEqual(file_hash(source),info['sha256'])
                self.assertEqual(file_hash(copy),info['sha256'])
            latest=sorted((destination/'snapshots').iterdir())[-1]
            self.assertEqual((latest/'COMPLETE').read_text().strip(),file_hash(latest/'index.json'))
            index=read_json(latest/'index.json')['files']
            receipt=read_json(destination/'objects'/index['receipt.json'])
            self.assertEqual(receipt['plan_hash'],digest(plan))
            self.assertTrue(receipt['safe'])
            self.assertFalse((destination/'SNAPSHOT_PENDING.json').exists())
            self.assertFalse((root/'attempts').exists())
            self.assertFalse((root/'events').exists())


if __name__=='__main__':unittest.main()
