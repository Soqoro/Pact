import json
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch
from pact.revival import continuation as child, replacement, runtime, neural, contracts as c, persistence
from pact.util import read_json, write_json, digest, file_hash, canonical


class Continuation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            import torch, safetensors
            torch.set_num_threads(1)
        except ImportError:raise unittest.SkipTest('Optional local tiny-model dependencies')

    def make(self):
        from test_revival_replacement import Replacement
        from pact.revival.mock import Backend
        class TinyBackend(Backend):
            def __init__(self,key,checkpoint=None):
                super().__init__(key,checkpoint)
                self.identity['native_projection_shapes']={n:list(m.weight.shape) for n,m in neural.projections(self.model)}
            def generate(self,*a,**kw):raise AssertionError('No continuation generation')
        helper=Replacement();helper.setUp();self.addCleanup(helper.doCleanups)
        parent=helper.create(TinyBackend)
        replacement.preflight(helper.root,helper.base/'cache',factory=TinyBackend)
        for f in c.FAMILIES:
            replacement.train(helper.root,digest(parent),helper.base/'cache',c.ARMS[1],f,factory=TinyBackend)
        replacement.train(helper.root,digest(parent),helper.base/'cache',child.JOINT,'Q',factory=TinyBackend,stop_after=1)
        fit=helper.root/'training'/child.JOINT/'Q'
        # The fixture has four steps per fit; preserve the same unresolved-next-step pattern.
        intent=read_json(fit/'update_attempt.json');intent['step']=94
        write_json(fit/'update_attempt.json',intent)
        snapshot=Path(persistence.persist_files(helper.root,helper.base/'drive')['snapshot'])
        fs=read_json(snapshot/'index.json')['files']
        selected={f'snapshots/{snapshot.name}/index.json':snapshot/'index.json',
                  f'snapshots/{snapshot.name}/COMPLETE':snapshot/'COMPLETE',
                  'SNAPSHOT_PENDING.json':helper.base/'marker.json'}
        write_json(helper.base/'marker.json',{'plan_hash':digest(parent)})
        for name,h in fs.items():selected['objects/'+h]=helper.base/'drive/objects'/h
        evidence=helper.base/'forensic.zip'
        with zipfile.ZipFile(evidence,'w') as z:
            for n,p in selected.items():z.write(p,n)
            z.writestr('FORENSIC_MANIFEST.json',canonical({'files':{n:{'sha256':file_hash(p),'bytes':p.stat().st_size} for n,p in selected.items()}}))
        baselines={f'{c.ARMS[1]}/{f}':4 for f in c.FAMILIES};baselines[f'{child.JOINT}/Q']=1
        for attr,value in [('FORENSIC_SHA',file_hash(evidence)),('PARENT_PLAN',digest(parent)),('SNAPSHOT',snapshot.name),('BASELINES',baselines)]:
            p=patch.object(child,attr,value);p.start();self.addCleanup(p.stop)
        dest=helper.base/'continuation'
        with patch.object(replacement,'proposal',return_value=helper.review):
            child.prepare(helper.bundle,evidence,dest,child.REVIEW_HASH)
        return helper,dest,TinyBackend,evidence

    def test_tiny_continuation_restore_and_immutable_independent(self):
        helper,root,backend,evidence=self.make()
        original=file_hash(evidence)
        p=read_json(root/'plan.json')
        before={n:h for n,h in p['inherited_files'].items() if c.ARMS[1] in n}
        child.preflight(root,helper.base/'cache',factory=backend)
        # Resume exact imported optimizer/RNG state. Q starts at one in this tiny fixture.
        child.train(root,digest(p),helper.base/'cache','Q',factory=backend,resume=True,stop_after=2,persistent=helper.base/'newdrive')
        restored=helper.base/'restored';runtime.restore_latest(helper.base/'newdrive',restored)
        for f in c.FAMILIES:
            child.train(restored,digest(p),helper.base/'cache',f,factory=backend,resume=f=='Q')
        out=child.report(restored)
        self.assertTrue(out['training_complete'])
        self.assertEqual(out['new_work']['committed_updates'],11)
        self.assertEqual(out['new_work']['generation_calls'],0)
        for n,h in before.items():self.assertEqual(file_hash(restored/n),h)
        # Match uninterrupted tiny training, including optimizer and RNG tensors.
        from pact.revival import study
        import torch
        from safetensors.torch import load_file
        b=backend('Q');shapes=neural.attach(b.model,c.SEED)
        groups=study.groups_for(restored,p,b,'Q',child.JOINT)
        reference=helper.base/'reference'
        identity={'plan':child.PARENT_PLAN,'family':'Q','arm':child.JOINT,'native':b.identity,'shapes':shapes}
        neural.train(b.model,groups,reference,identity)
        actual=load_file(str(restored/'training'/child.JOINT/'Q/checkpoints/step-000004/tensors.safetensors'))
        expected=load_file(str(reference/'checkpoints/step-000004/tensors.safetensors'))
        self.assertEqual(set(actual),set(expected))
        for key in actual:self.assertTrue(torch.equal(actual[key],expected[key]),key)
        b.close()
        self.assertEqual(file_hash(evidence),original)
        self.assertEqual(read_json(restored/'lineage/parent_step94_intent.json')['step'],94)
        with self.assertRaisesRegex(ValueError,'not authorized'):runtime.Journal(restored).request(None,None,None)
        runtime.package(restored,helper.base/'sanitized.zip',sanitized=True)
        with zipfile.ZipFile(helper.base/'sanitized.zip') as z:
            self.assertEqual(set(z.namelist()),{'summary.json','HANDOFF.json','checksums.json'})

    def test_tamper_and_review_guards(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(ValueError,'review'):
                child.prepare(Path(tmp)/'absent',Path(tmp)/'absent',Path(tmp)/'child','wrong')
        helper,root,backend,evidence=self.make()
        with self.assertRaisesRegex(ValueError,'hash mismatch'):child.validate(root,'wrong')
        with self.assertRaisesRegex(ValueError,'source changed'):
            with patch.object(replacement,'source_identity',return_value={}):child.validate(root,check_source=True)
        write_json(root/'training'/child.JOINT/'L/update_attempt.json',{'step':1})
        pending=child.report(root)
        self.assertFalse(pending['recovery_safe'])
        self.assertEqual(pending['new_work']['unresolved_optimizer_attempts'],[{'family':'L','step':1}])
        write_json(root/'lineage/parent_step94_intent.json',{'step':93})
        with self.assertRaisesRegex(ValueError,'Lineage'):child.validate(root)


class OfficialEvidence(unittest.TestCase):
    def test_official_evidence_and_fixed_bank_prerequisites(self):
        repo=Path(__file__).resolve().parents[1]
        evidence=repo/'results_import/replacement-002-FORENSIC-PRIVATE-1792568005277432071.zip'
        bundle=repo/'pact-heterogeneous-receiver-training-001-PRIVATE-1792171769996477145.zip'
        if not evidence.exists() or not bundle.exists():self.skipTest('Private evidence not distributed')
        parent,fs=child.forensic(evidence)
        from pact.revival.replacement_review import proposal
        proposal(bundle)
        mapping={'plan.json':'parent_plan.json','training_bank.json':'training_bank.json',
                 'access.json':'access.json','sanity_complete.json':'sanity_complete.json'}
        for f in c.FAMILIES:
            mapping[f'sanity/{f}/contract.json']=f'parent_contracts/{f}.json'
            mapping[f'sanity/{f}/receipt.json']=f'parent_receipts/{f}.json'
        import hashlib
        with zipfile.ZipFile(bundle) as z:
            for name,dest in mapping.items():
                self.assertEqual(hashlib.sha256(z.read(name)).hexdigest(),parent['imported_files'][dest])
        self.assertEqual(file_hash(bundle),parent['imported_files']['parent-private.zip'])

    def test_official_q_optimizer_and_rng_structure(self):
        try:
            import torch
            from safetensors.torch import load
        except ImportError:self.skipTest('Optional CPU tensor reader')
        from pact.training.checkpoints import decode_state
        path=Path(__file__).resolve().parents[1]/'results_import/replacement-002-FORENSIC-PRIVATE-1792568005277432071.zip'
        if not path.exists():self.skipTest('Private evidence not distributed')
        with zipfile.ZipFile(path) as z:
            fs=json.loads(z.read(f'snapshots/{child.SNAPSHOT}/index.json'))['files']
            prefix=f'run/training/{child.JOINT}/Q/checkpoints/step-000093/'
            metadata=json.loads(z.read('objects/'+fs[prefix+'state.json']))
            state=decode_state(metadata['tree'],load(z.read('objects/'+fs[prefix+'tensors.safetensors'])))
            self.assertEqual(state['sampler_position'],93)
            self.assertEqual(state['scheduler']['completed_steps'],93)
            self.assertEqual(len(state['logs']),93)
            self.assertEqual(set(state['rng']),{'python','torch','cuda'})
            self.assertEqual(len(state['rng']['cuda']),1)
            self.assertEqual(state['rng']['torch'].dtype,torch.uint8)
            self.assertTrue(state['optimizer']['state'])
            for v in state['optimizer']['state'].values():
                self.assertEqual(int(v['step']),93)
                for k in ('exp_avg','exp_avg_sq'):
                    self.assertEqual(v[k].dtype,torch.float32)
                    self.assertTrue(torch.isfinite(v[k]).all())
            for v in state['adapters'].values():
                self.assertEqual(v.dtype,torch.float32)
                self.assertTrue(torch.isfinite(v).all())

    def test_official_prepare_without_models(self):
        import os
        base=Path(os.environ.get('PACT_PRIVATE_TEST_TMP',tempfile.gettempdir()))
        if any((p/'.git').exists() for p in (base,*base.parents)):
            self.skipTest('Private preparation requires temp directory outside Git')
        repo=Path(__file__).resolve().parents[1]
        evidence=repo/'results_import/replacement-002-FORENSIC-PRIVATE-1792568005277432071.zip'
        bundle=repo/'pact-heterogeneous-receiver-training-001-PRIVATE-1792171769996477145.zip'
        if not evidence.exists() or not bundle.exists():self.skipTest('Private evidence not distributed')
        # Simulate a future clean checkout solely for the offline preparation test.
        # No model load, training, original directory mutation, or GPU verification.
        identity={**replacement.source_identity(),'dirty':False}
        with tempfile.TemporaryDirectory(dir=base) as tmp:
            with patch.object(replacement,'source_identity',return_value=identity):
                root=Path(tmp)/child.RUN
                out=child.prepare(bundle,evidence,root,child.REVIEW_HASH)
                self.assertEqual(out['new_work']['committed_updates'],0)
                self.assertEqual(out['combined_committed_updates'],477)
                self.assertTrue(out['recovery_safe'])
                self.assertFalse(out['training_complete'])
                self.assertEqual(read_json(root/'lineage/parent_step94_intent.json')['step'],94)
                self.assertFalse((root/'training/uniform_joint_sft/Q/update_attempt.json').exists())
