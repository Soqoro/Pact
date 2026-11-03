import tempfile
import unittest
from pathlib import Path
from pact.util import read_json, file_hash, digest
from pact.revival.documented_child import review
from pact.revival.gpqa_source import fixtures
from pact.revival import documented_freeze as freeze


class FreezeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp=tempfile.TemporaryDirectory();cls.root=Path(cls.tmp.name)/'audit'
        source,candidate,_=fixtures.inputs()
        lineage={'S0':{'fixture':True}}
        audit={'fixture':True,'blockers':[],'eligibility':{'screened_unique_groups':{'gpqa_main':70,'logiqa':70}}}
        summary=review.save(cls.root,source,lineage,audit,candidate)
        bundle=review.export(cls.root)['PRIVATE']
        cls.archive=cls.root/'bundles'/bundle['filename']
        cls.expected={k:summary[k] for k in ('candidate_digest','graph_digest','training_dependency_hash')}
        cls.expected['archive_sha256']=bundle['sha256']

    @classmethod
    def tearDownClass(cls):cls.tmp.cleanup()

    def test_exact_freeze_idempotent_and_unchanged_parent(self):
        before=file_hash(self.root/'manifest.json')
        dest=Path(self.tmp.name)/'sealed'
        a=freeze.seal(self.root,self.archive,dest,self.expected,fixture=True)
        self.assertTrue(a['candidate_frozen']);self.assertFalse(a['execution_authorized'])
        self.assertFalse(a['wallet_active']);self.assertIsNone(a['historical_spending'])
        self.assertEqual(freeze.seal(self.root,self.archive,dest,self.expected,fixture=True),a)
        self.assertEqual(file_hash(self.root/'manifest.json'),before)
        self.assertFalse(read_json(self.root/'summary.sanitized.json')['cohort_frozen'])
        self.assertEqual(digest(read_json(dest/'sealed/prospective.private.json')),self.expected['candidate_digest'])
        self.assertEqual(digest(read_json(dest/'sealed/graph.private.json')),self.expected['graph_digest'])
        self.assertFalse((dest/'events').exists())
        self.assertEqual((dest/'COMPLETE').read_text().strip(),file_hash(dest/'checksums.json'))

    def test_wrong_identity_and_fixture_refused(self):
        dest=Path(self.tmp.name)/'wrong'
        for key in self.expected:
            with self.assertRaises(ValueError):freeze.seal(self.root,self.archive,dest,{**self.expected,key:'0'*64},fixture=True)
        with self.assertRaises(ValueError):freeze.seal(self.root,self.archive,dest,self.expected)
        self.assertFalse(dest.exists())

    def test_incomplete_destination_not_repaired(self):
        dest=Path(self.tmp.name)/'incomplete';dest.mkdir()
        (dest/'old').write_text('preserve')
        with self.assertRaises(ValueError):freeze.seal(self.root,self.archive,dest,self.expected,fixture=True)
        self.assertEqual((dest/'old').read_text(),'preserve')

    def test_no_in_place_or_symlink_freeze(self):
        with self.assertRaises(ValueError):freeze.seal(self.root,self.archive,self.root/'seal',self.expected,fixture=True)
        dest=Path(self.tmp.name)/'link';dest.symlink_to(self.root,target_is_directory=True)
        with self.assertRaises(ValueError):freeze.seal(self.root,self.archive,dest,self.expected,fixture=True)

if __name__=='__main__':unittest.main()
