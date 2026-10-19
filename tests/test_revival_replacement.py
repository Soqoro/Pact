import copy
import json
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

from pact.revival import replacement as child, runtime, study, data, contracts as c
from pact.util import write_json, read_json, digest, file_hash, canonical
from pact.environment import runtime_fingerprint


class Replacement(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.base=Path(self.tmp.name);self.parent=self.base/'parent';self.root=self.base/'child'

    def create(self, factory=None):
        study.plan(self.parent,data.fixture());p=read_json(self.parent/'plan.json')
        write_json(self.parent/'fit_complete.json',{'fixture':True})
        for r in study.records(p,'main_fit'):
            for slot in range(3):
                write_json(self.parent/'fit_private'/f"{digest(['fit',study.tid(r),slot])}.json",
                           {'packet':{'status':'ok','answer':'A','justification':'fixture'}})
            write_json(self.parent/'attacks'/f'{digest(study.tid(r))}.json',{'accepted':False})
        study.fit_bank(self.parent,p)
        write_json(self.parent/'access.json',{f:{'runtime_fingerprint':runtime_fingerprint()} for f in c.FAMILIES})
        write_json(self.parent/'sanity_complete.json',{'fixture':True})
        for f in c.FAMILIES:
            native={'fixture':True,'native_projection_shapes':{'q':[8,8]}}
            initial='fixture'
            if factory:
                from pact.revival import neural
                b=factory(f);native=b.identity
                neural.attach(b.model,c.SEED+c.FAMILIES.index(f))
                initial=neural._weights_hash(neural.parameters(b.model));b.close()
            write_json(self.parent/f'sanity/{f}/contract.json',{'initial':initial,'lora':c.LORA,'optimizer':c.OPT,
                'identity':{'family':f,'plan':digest(p),'native':native}})
            write_json(self.parent/f'sanity/{f}/receipt.json',{'initial':initial,'restored':initial})
        self.bundle=self.base/'parent.zip';runtime.package(self.parent,self.bundle)
        self.review={'historical_accounting':{'confirmed_generation_calls':0,'main_updates_confirmed_at_least':28,'main_updates_actual':None}}
        self.reviewsha=child.digest_bytes(canonical(self.review)+'\n')
        self.patch=patch.object(child,'REVIEW_SHA',self.reviewsha);self.patch.start();self.addCleanup(self.patch.stop)
        with patch.object(child,'proposal',return_value=self.review):
            child.import_parent(self.bundle,self.root,self.reviewsha)
        return read_json(self.root/'plan.json')

    def test_import_isolated_and_journal_preserved(self):
        p=self.create()
        self.assertEqual(file_hash(self.bundle),file_hash(self.root/'parent-private.zip'))
        self.assertEqual(file_hash(self.parent/'training_bank.json'),file_hash(self.root/'training_bank.json'))
        self.assertNotEqual(digest(p),p['parent_plan_hash'])
        self.assertFalse((self.root/'sanity').exists());self.assertFalse((self.root/'training').exists())
        self.assertEqual(child.report(self.root)['new_work']['committed_updates'],0)
        with self.assertRaisesRegex(ValueError,'Absent'):
            child.import_parent(self.bundle,self.root,self.reviewsha)
        with self.assertRaisesRegex(ValueError,'not authorized'):
            runtime.Journal(self.root).request(None,None,None)
        with self.assertRaises(ValueError):study.guard(self.root,digest(p),True)

    def test_tampered_bank_and_source_rejected(self):
        p=self.create()
        with self.assertRaisesRegex(ValueError,'hash mismatch'):child.validate(self.root,'wrong')
        with patch.object(child,'source_identity',return_value={'changed':True}):
            with self.assertRaisesRegex(ValueError,'source changed'):child.validate(self.root,check_source=True)
        write_json(self.root/'training_bank.json',{})
        with self.assertRaisesRegex(ValueError,'evidence changed'):child.validate(self.root)

    def test_no_new_calls_or_evaluation_cli(self):
        self.create()
        write_json(self.root/'intents/new.json',{})
        with self.assertRaisesRegex(ValueError,'no new generation'):child.validate(self.root)
        with self.assertRaises(SystemExit):child.main(['evaluate','--run-dir',str(self.root)])

    def test_capacity_and_restore(self):
        self.create();self.assertLess(child.capacity(self.root)['projected_peak_object_bytes'],32*1024**3)
        drive=self.base/'drive';runtime.checkpoint(self.root,drive)
        restored=self.base/'restored';runtime.restore_latest(drive,restored)
        child.validate(restored)
        self.assertEqual(file_hash(restored/'parent-private.zip'),file_hash(self.bundle))

    def test_explicit_review_required(self):
        with self.assertRaisesRegex(ValueError,'approved'):child.import_parent(self.base/'absent',self.root,'wrong')


class NeuralReplacement(Replacement):
    @classmethod
    def setUpClass(cls):
        try:
            import torch,safetensors
            torch.set_num_threads(1)
        except ImportError:raise unittest.SkipTest('Optional local torch/safetensors')

    def test_train_resume_and_export_real_tiny_updates(self):
        from pact.revival.mock import Backend
        from pact.revival import neural
        class TinyBackend(Backend):
            def __init__(self,key,checkpoint=None):
                super().__init__(key,checkpoint)
                self.identity['native_projection_shapes']={n:list(m.weight.shape) for n,m in neural.projections(self.model)}
            def generate(self,*a,**kw):raise AssertionError('Child must never generate')
        p=self.create(TinyBackend)
        child.preflight(self.root,self.base/'cache',factory=TinyBackend)
        drive=self.base/'drive'
        first=child.train(self.root,digest(p),self.base/'cache',c.ARMS[1],'Q',factory=TinyBackend,stop_after=1,persistent=drive)
        self.assertEqual(first['completed_steps'],1)
        restored=self.base/'restored';runtime.restore_latest(drive,restored)
        for arm in c.ARMS[1:]:
            for f in c.FAMILIES:
                child.train(restored,digest(p),self.base/'cache',arm,f,factory=TinyBackend,
                            resume=(arm==c.ARMS[1] and f=='Q'),persistent=drive)
        out=child.report(restored)
        self.assertTrue(out['training_complete']);self.assertEqual(out['new_work']['generation_calls'],0)
        self.assertEqual(out['new_work']['committed_updates'],24)
        initial=read_json(restored/'parent_receipts/Q.json')['initial']
        self.assertNotEqual(initial,read_json(restored/f'training/{c.ARMS[1]}/Q/status.json')['adapter_hash'])
        r=runtime.package(restored,self.base/'recovery.zip',weights=True)
        runtime.unpack(Path(r['path']),r['sha256'],self.base/'unpacked')
        self.assertEqual(child.report(self.base/'unpacked'),out)
        runtime.package(restored,self.base/'sanitized.zip',sanitized=True)
        with zipfile.ZipFile(self.base/'sanitized.zip') as z:
            self.assertEqual(set(z.namelist()),{'summary.json','HANDOFF.json','checksums.json'})

class OfficialImportAudit(unittest.TestCase):
    def test_actual_reviewed_private_import_without_models(self):
        bundle=Path(__file__).resolve().parents[1]/'pact-heterogeneous-receiver-training-001-PRIVATE-1792171769996477145.zip'
        if not bundle.exists():self.skipTest('Private audit bundle not distributed')
        import os
        private_temp=os.environ.get('PACT_PRIVATE_TEST_TMP',tempfile.gettempdir())
        if any((p/'.git').exists() for p in (Path(private_temp),*Path(private_temp).parents)):
            self.skipTest('Private import needs a temporary directory outside Git; set PACT_PRIVATE_TEST_TMP')
        with tempfile.TemporaryDirectory(dir=private_temp) as tmp:
            # Simulate the user's future clean pinned checkout for offline import.
            # This does not verify a real Colab runtime or authorize training.
            identity={**child.source_identity(),'dirty':False}
            with patch.object(child,'source_identity',return_value=identity):
                root=Path(tmp)/child.RUN
                out=child.import_parent(bundle,root,child.REVIEW_SHA)
                self.assertEqual(out['inherited_calls'],2438)
                self.assertEqual(out['new_updates'],0)
                self.assertEqual(child.report(root)['new_work']['generation_calls'],0)
                bound=child.capacity(root)['projected_peak_object_bytes']
                self.assertLess(bound,32*1024**3)
                print('OFFLINE_PARENT_IMPORT_OK; projected object bytes:',bound)

class TokenizerPointer(unittest.TestCase):
    def test_reviewed_git_pointer_identity_and_reject_wrong_payload(self):
        import hashlib
        from pact.revival import mistral_cache as m
        raw=(f'version https://git-lfs.github.com/spec/v1\noid sha256:{m.PAYLOAD_SHA}\nsize {m.PAYLOAD_BYTES}').encode()
        self.assertEqual(hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest(),m.GIT_BLOB)
        with self.assertRaisesRegex(ValueError,'payload checksum'):m.verify(raw,b'bad bytes')
        with self.assertRaisesRegex(ValueError,'Git identity'):m.verify(b'bad pointer',b'bad bytes')

class BankReconstruction(unittest.TestCase):
    def test_roundoff_check_does_not_replace_original_coefficients(self):
        saved={'bank':{'Q':[{'weight':0.2,'gold':'A','joint':['same context']}]},'support':{}}
        rebuilt=copy.deepcopy(saved);rebuilt['bank']['Q'][0]['weight']+=1e-16
        before=copy.deepcopy(saved)
        self.assertEqual(child.compare_bank(saved,rebuilt)['reconstruction_roundoff_fields'],1)
        self.assertEqual(saved,before)
        rebuilt['bank']['Q'][0]['gold']='B'
        with self.assertRaises(ValueError):child.compare_bank(saved,rebuilt)

    def test_changed_native_or_initial_identity_stops(self):
        from types import SimpleNamespace
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            write_json(root/'parent_contracts/Q.json',{'identity':{'native':{'snapshot':'old'}},'initial':'original'})
            with self.assertRaisesRegex(ValueError,'Native model'):
                child.verify_initial(root,'Q',SimpleNamespace(identity={'snapshot':'changed'}))
            with patch.object(child.neural,'parameters',return_value={}),patch.object(child.neural,'_weights_hash',return_value='changed'):
                with self.assertRaisesRegex(ValueError,'Seeded initialization'):
                    child.verify_initial(root,'Q',SimpleNamespace(identity={'snapshot':'old'},model=None))
