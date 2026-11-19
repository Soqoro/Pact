import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import aai_documented_training_batch as t
from pact.revival.allocation_v3 import design as d

class TrainingBatchGuards(unittest.TestCase):
    def fixture(self):
        blocks=[{'family':'arc_challenge' if i<3 else 'logiqa','fit':[f'{i}-{j}' for j in range(64)]} for i in range(8)]
        allocation=d.compile_policies(blocks,[[1,2,3]]*8,[[3,2,1]]*8,d.derangement(blocks),t.b.S0)
        # Real frozen handoff has ten distinct owners; fixture scores may alias.
        allocation['aliases']={k:k for k in allocation['plans']}
        plan={'blocks':blocks,'probes':{'arc_challenge':['probe']},'training_source':{'records':[
            {'task':{'task_id':task},'split':'main_fit'} for block in blocks for task in block['fit']]}}
        return allocation,plan
    def test_exact_batch_and_probe_isolation(self):
        a,p=self.fixture();jobs=t.jobs(a,p)
        self.assertEqual(len(jobs),30)
        self.assertEqual(sum(len(j[3]) for j in jobs),2880)
        p['probes']['arc_challenge'].append(jobs[0][3][0]['tasks'][0])
        with self.assertRaises(t.b.CheckFailed):t.jobs(a,p)
    def test_alias_or_checkpoint_change_rejected(self):
        a,p=self.fixture();a['aliases'][next(iter(a['plans']))]='other'
        with self.assertRaises(t.b.CheckFailed):t.jobs(a,p)
        a,p=self.fixture();next(iter(a['plans'].values()))['s0']={'Q':'other'}
        with self.assertRaises(t.b.CheckFailed):t.jobs(a,p)
    def test_extra_physical_work_rejected(self):
        initial={'physical_attempts':{'assay':dict(generation=7320,scores=2442,training_forwards=1536,updates=192),
            'policy':dict(generation=0,scores=0,training_forwards=80,updates=10)},'committed_operations':9964,'unresolved':0,'recovery_safe':True}
        for k in ('reserved_output_tokens','input_tokens','output_tokens','format_status_counts','historical_spending','remaining_historical_budget','stages'):initial[k]=None
        t.accounting(initial,initial,10)
        for part,kind in [('assay','generation'),('policy','generation'),('policy','scores'),('policy','updates')]:
            bad=copy.deepcopy(initial);bad['physical_attempts'][part][kind]+=1
            with self.assertRaises(t.b.CheckFailed):t.accounting(bad,initial,10)
    def test_update_delta_bound_to_exact_fit(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);(root/'events/shards').mkdir(parents=True);(root/'attempts').mkdir()
            path=root/'continuations/uniform/113/Q';schedule=[{'tasks':['x']}];contract={'family':'Q'}
            identity={'owner':t.b.RUN,'plan_hash':t.b.PLAN,'part':'policy','kind':'update','dependency':{
                'path':path.relative_to(root).as_posix(),'family':'Q','contract':t.b.digest(contract),'step':1,'batch':schedule[0]}}
            key=t.b.digest(identity);intent={'identity':identity,'cost':{'updates':1,'training_forwards':8}}
            event={'intent':intent,'value':{'step':1}}
            (root/'events/shards'/f'{key}.json').write_text(json.dumps(event));(root/'attempts'/f'{key}.json').write_text(json.dumps(intent))
            t.delta(root,{}, {key:None},path,contract,schedule)
            with self.assertRaises(t.b.CheckFailed):t.delta(root,{}, {key:None},root/'continuations/uniform/113/L',contract,schedule)
    def test_resume_counts_only_suffix(self):
        prior={'original':('hash','intent')}
        t.delta(None,prior,prior,None,None,[{}]*77,77)
        with self.assertRaises(t.b.CheckFailed):
            t.delta(None,prior,prior,None,None,[{}]*96,77)
        with self.assertRaises(t.b.CheckFailed):
            t.delta(None,prior,{},None,None,[{}]*77,77)

    def test_no_automatic_resume_or_next_stage(self):
        source=(Path(__file__).resolve().parents[1]/'tools/aai_documented_training_batch.py').read_text()
        self.assertNotIn("'resume':True",source)
        self.assertIn("'stage':'continuation'",source)
        self.assertNotIn("'stage':'evaluate'",source)
