import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
import zipfile

spec = importlib.util.spec_from_file_location('batch', Path(__file__).resolve().parents[1]/'tools/aai_documented_remaining_batch.py')
b = importlib.util.module_from_spec(spec)
spec.loader.exec_module(b)

class BatchGuards(unittest.TestCase):
    def test_scope_and_ceiling(self):
        self.assertEqual(len(b.REMAINING),13)
        self.assertEqual(b.REMAINING[0],(3,'M'))
        self.assertFalse(set(b.REMAINING)&set(b.COMPLETED))
        self.assertEqual(set(b.REMAINING)|set(b.COMPLETED),{(x,f) for x in range(8) for f in 'QLM'})
        self.assertEqual(13*328,4264)

    def summary(self):
        return {'physical_attempts':{'assay':dict(generation=7320,scores=0,training_forwards=1536,updates=192),'policy':dict(generation=0,scores=0,training_forwards=0,updates=0)},'committed_operations':7512,'unresolved':0,'recovery_safe':True,'reserved_output_tokens':3747840,'historical_spending':None,'remaining_historical_budget':None}

    def test_rejects_spending_overrun_and_later_work(self):
        s=self.summary(); b.accounting(s,13)
        s['physical_attempts']['assay']['generation']+=1
        with self.assertRaises(ValueError):b.accounting(s,13)
        s=self.summary();s['physical_attempts']['policy']['generation']=1
        with self.assertRaises(ValueError):b.accounting(s,13)
        s=self.summary();s['historical_spending']=0
        with self.assertRaises(ValueError):b.accounting(s,13)

    def test_prior_event_mutation_stops(self):
        with self.assertRaisesRegex(ValueError,'prior_events_changed'):
            b.delta(Path('/unused'),{'old':('a','b')},{'old':('c','b')},'Q')

    def test_unresolved_intent_stops(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);(root/'attempts').mkdir();(root/'events/shards').mkdir(parents=True)
            (root/'attempts/x.json').write_text('{}')
            with self.assertRaisesRegex(ValueError,'unresolved_events'):b.events(root)

    def test_archive_member_and_scratch_tampering(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);p=root/'bundle.zip';(root/'summary.json').write_text('{}')
            h=b.sha(root/'summary.json')
            def make(payload):
                with zipfile.ZipFile(p,'w') as z:
                    z.writestr('summary.json',payload)
                    z.writestr('checksums.json',json.dumps({'summary.json':h}))
                    z.writestr('HANDOFF.json','{"recovery_safe":true}')
            make('{}');b.archive(p,b.sha(p),root)
            (root/'summary.json').write_text('{"changed":true}')
            with self.assertRaisesRegex(ValueError,'scratch_differs'):b.archive(p,b.sha(p),root)
            make('{"corrupt":true}')
            with self.assertRaisesRegex(ValueError,'archive_member'):b.archive(p,b.sha(p),root)

    def test_checkpoint_rollback_and_tensor_corruption(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d); path=root/'branches/block-3-M';cp=path/'checkpoints/step-000008';cp.mkdir(parents=True)
            ids=[str(i) for i in range(64)]
            plan={'blocks':[{}, {}, {}, {'family':'logiqa','fit':ids}], 'probes':{'logiqa':['p']},'training_source':{'records':[{'task':{'task_id':t},'split':'main_fit'} for t in ids]}}
            contract={'family':'M','plan_hash':b.PLAN,'initial':b.S0['M'],'seed':17,'schedule':b.schedule(plan,3,'M')}
            for name,value in [('contract.json',contract),('status.json',{'complete':True,'completed_steps':8,'planned_steps':8,'forwards':64,'adapter_hash':'recorded'}),('evaluated.json',{'complete':True,'probe_ids':['p']}),('rollback.json',{'complete':True,'initial_hash':b.S0['M'],'restored_hash':b.S0['M'],'probe_training_tokens':0,'temporary_optimizer_discarded':True})]:
                b.save(path/name,value)
            b.save(cp/'state.json',{'step':8,'identity':contract})
            (cp/'tensors.safetensors').write_bytes(b'CPU checksum fixture, not real tensors')
            b.save(cp/'checksums.json',{n:b.sha(cp/n) for n in ('state.json','tensors.safetensors')})
            self.assertFalse(b.checkpoint(root,plan,3,'M')['adapter_hash_recomputed'])
            rollback=b.read(path/'rollback.json');rollback['restored_hash']='wrong'
            (path/'rollback.json').write_text(json.dumps(rollback))
            with self.assertRaisesRegex(ValueError,'rollback'):b.checkpoint(root,plan,3,'M')
            rollback['restored_hash']=b.S0['M'];(path/'rollback.json').write_text(json.dumps(rollback))
            (cp/'tensors.safetensors').write_bytes(b'changed')
            with self.assertRaisesRegex(ValueError,'tensor_hash'):b.checkpoint(root,plan,3,'M')

    def test_approvals_not_overwritten(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'approval.json';b.save(p,{'scope':'old'})
            with self.assertRaises(FileExistsError):b.save(p,{'scope':'new'})
            self.assertEqual(b.read(p),{'scope':'old'})

if __name__=='__main__':unittest.main()
