import importlib.util
import json
import sys
import tempfile
from pathlib import Path
import unittest

TOOLS=Path(__file__).resolve().parents[1]/'tools'
sys.path.insert(0,str(TOOLS))
import aai_documented_score as s
sys.path.pop(0)

class ScoreGuards(unittest.TestCase):
    def test_actual_graph_and_attack_changes(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);folder=root/'attacks/assay';folder.mkdir(parents=True)
            plan={'probes':{'arc_challenge':['a'+str(i) for i in range(24)],'logiqa':['l'+str(i) for i in range(40)]},'blocks':[{'family':'arc_challenge'}]*3+[{'family':'logiqa'}]*5}
            for source,n in [('arc_challenge',17),('logiqa',32)]:
                for i,t in enumerate(plan['probes'][source]):s.b.save(folder/(s.b.digest(t)+'.json'),{'accepted':i<n})
            keys=s.score_keys(root,plan)
            self.assertEqual(len(keys),2442)
            self.assertEqual(sum(k[0]=='S0' for k in keys),177)
            p=folder/(s.b.digest('a0')+'.json');p.write_text('{"accepted":false}')
            with self.assertRaisesRegex(ValueError,'attack_count'):s.score_keys(root,plan)

    def test_loss_contract(self):
        v={'raw_nll':12.0,'capped_nll':10.0,'generated_correctness_is_separate':True}
        s.check_loss(v)
        for raw in (float('nan'),float('inf'),-1,True):
            with self.assertRaises(ValueError):s.check_loss(dict(v,raw_nll=raw))
        with self.assertRaises(ValueError):s.check_loss(dict(v,capped_nll=12.0))

    def test_post_accounting_rejects_extra_training(self):
        original={'physical_attempts':{'policy':dict(generation=0,scores=0,training_forwards=0,updates=0)},'reserved_output_tokens':3747840,'input_tokens':1,'output_tokens':1,'format_status_counts':{},'historical_spending':None,'remaining_historical_budget':None}
        summary={**original,'physical_attempts':{**original['physical_attempts'],'assay':dict(generation=7320,scores=2442,training_forwards=1536,updates=192)},'committed_operations':9954,'unresolved':0,'recovery_safe':True,'stages':['assay-smoke','collect','score']}
        s.post_accounting(summary,original)
        summary['physical_attempts']['assay']['updates']+=1
        with self.assertRaisesRegex(ValueError,'score_accounting'):s.post_accounting(summary,original)

    def test_prior_event_mutation_stops(self):
        with self.assertRaisesRegex(ValueError,'prior_events_changed'):
            s.verify_score_delta(Path('/unused'),{'x':('a','b')},{'x':('bad','b')},set(),{})

if __name__=='__main__':unittest.main()
