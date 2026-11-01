"""Reviewed v2 invariants; no network, pretrained weights or CUDA."""
import copy
import json
import math
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from pact.util import read_json, write_json, digest
from pact.revival.allocation_v3 import design as d, evidence, storage, runner, models, report
from pact.revival.allocation_v3.__main__ import create_plan, guard, main
from pact.revival import neural
from pact.revival.mock import Tokenizer


class DesignTests(unittest.TestCase):
    def setUp(self):
        self.source=evidence.fixture_source()
        self.blocks=self.source['blocks']

    def test_exact_budgets(self):
        self.assertEqual(64+64*11+3*(3*24+5*40)*9, d.BUDGET['assay']['generation'])
        self.assertEqual(128+128*11*11,d.BUDGET['policy']['generation'])
        self.assertEqual(23728*512,d.BUDGET['reserved_tokens'])
        self.assertEqual(24*8,d.BUDGET['assay']['updates'])
        self.assertEqual(10*288,d.BUDGET['policy']['updates'])
        self.assertEqual((64+3*(3*24+5*40))*3,d.BUDGET['scores'])

    def test_shared_probe_identity_and_historical_conflict(self):
        contract=evidence.source_contract(self.source)
        self.assertEqual(contract['status'],'ready')
        for b in self.blocks:
            self.assertEqual(len(contract['probes'][b['family']]),d.PROBE_COUNTS[b['family']])
        historical=copy.deepcopy(self.source)
        historical['blocks'][3]['family']='arc_challenge'
        r=evidence.source_contract(historical)
        self.assertIn('source_contract_conflict:block_membership_counts',r['blockers'])

    def test_solver_equal_row_invariance_and_rounding(self):
        a=d.quotas([[.1,.2,.3]]*8)
        b=d.quotas([[i+.1,i+.2,i+.3] for i in range(8)])
        self.assertEqual(a['quotas'],b['quotas'])
        self.assertEqual(d.quotas([[3.,3.,3.]]*8)['quotas'],[[4]*3]*8)
        self.assertTrue(all(sum(r)==12 for r in a['quotas']))
        self.assertEqual(d.quotas([[None]*3]*8)['unsupported_rows'],list(range(8)))
        with self.assertRaises(ValueError):d.quotas([[1,None,2]]*8)

    def test_source_family_exact_margins_and_shuffle(self):
        terminal=[[12,0,0],[0,10,2],[0,0,12],[5,4,3]]*2
        balanced=d.source_family(terminal,self.blocks)
        for ix in (range(3),range(3,8)):
            for i in range(3):
                total=sum(terminal[b][i] for b in ix)
                self.assertEqual(sum(balanced[b][i] for b in ix),total)
                self.assertTrue(all(balanced[b][i] in (total//len(ix),math.ceil(total/len(ix))) for b in ix))
        self.assertTrue(all(sum(r)==12 for r in balanced))
        shuffle=d.derangement(self.blocks)
        self.assertTrue(all(i!=j and self.blocks[i]['family']==self.blocks[j]['family'] for i,j in enumerate(shuffle)))
        self.assertEqual(shuffle,d.derangement(self.blocks))

    def test_schedules_actual_exposure_and_aliases(self):
        quotas=[[12,0,0]]*8
        schedule=d.schedules(self.blocks,quotas,113)
        self.assertEqual([len(schedule[f]) for f in d.FAMILIES],[160,64,64])
        for f,entries in schedule.items():
            base=[t for e in entries if e['kind']=='base' for t in e['tasks']]
            self.assertEqual(len(base),512);self.assertEqual(len(set(base)),512)
            self.assertTrue(all(len(e['tasks'])==8 for e in entries))
        result=d.compile_policies(self.blocks,[[0]*3]*8,[[0]*3]*8,d.derangement(self.blocks),{'Q':'fixed'})
        self.assertEqual(len(set(result['aliases'].values())),2)
        self.assertNotEqual(result['aliases']['uniform/113'],result['aliases']['uniform/227'])
        changed=d.schedules(self.blocks,[[4]*3]*8,113)
        self.assertNotEqual(schedule,changed)

    def test_native_mask_and_cap(self):
        t=neural.prefix_target(Tokenizer(),'private prompt','AB',['AB','C'])
        self.assertEqual(sum(t['score_mask']),2)
        self.assertTrue(all(not m for m in t['score_mask'][:len('private prompt')]))
        self.assertFalse(t['eos_supervised'])
        self.assertEqual(d.cap(40),10)
        for value in (float('nan'),float('inf'),-1):
            with self.assertRaises(ValueError):d.cap(value)

    def test_missing_scores_not_zero_and_common_attacks(self):
        probes={f:[f] for f in d.SOURCES}
        blocks=[{'family':f} for f in d.SOURCES]
        scores={}
        for f in d.SOURCES:
            for kind in ('clean','exchange','private_bank'):
                scores['S0',f,kind]={'raw_nll':12.,'capped_nll':10.}
        for b,block in enumerate(blocks):
            for f in d.FAMILIES:
                for kind in ('clean','exchange','private_bank'):
                    scores[f'block-{b}-{f}',block['family'],kind]={'raw_nll':9.,'capped_nll':9.}
        credits=d.credits(scores,blocks,probes,dict.fromkeys(d.SOURCES,True))
        self.assertEqual(credits['terminal'],[[1]*3]*2)
        unsupported=d.credits(scores,blocks,probes,dict.fromkeys(d.SOURCES,False))
        self.assertEqual(unsupported['terminal'],[[None]*3]*2)
        del scores['block-0-Q','arc_challenge','clean']
        with self.assertRaises(KeyError):d.credits(scores,blocks,probes,dict.fromkeys(d.SOURCES,True))

    def test_task_cluster_and_missing_source(self):
        v={f:{str(i):.1 for i in range(10)} for f in d.SOURCES}
        result=report.intervals(v,10000)
        self.assertAlmostEqual(result['estimate'],.1)
        self.assertAlmostEqual(result['95'][0],.1)
        self.assertIsNone(report.intervals({'arc_challenge':{'x':1},'logiqa':{}})['estimate'])

    def test_offline_cli_and_sealed_tasks(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)/'run'
            self.assertEqual(main(['evaluate','--run-dir',str(root)]),0)
            self.assertFalse(root.exists())
            create_plan(root,True)
            p=read_json(root/'plan.json')
            self.assertEqual(p['prospective_count'],128)
            self.assertFalse(set(read_json(root/'sealed/prospective.private.json')['labels']) & set(p['training_source']['labels']))
            with self.assertRaises(FileNotFoundError):runner.prospective(root,p)
            with self.assertRaises(ValueError):guard(root,'wrong',True)
            with self.assertRaises(ValueError):create_plan(root,True)

    def test_unknown_attempt_and_physical_budget(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);p={'run_id':'fixture'}
            w=storage.Wallet(root,p)
            key,_=w.begin('assay','generation',{'x':1},{'generation':1})
            with self.assertRaisesRegex(ValueError,'Unresolved'):storage.Wallet(root,p)
            with self.assertRaisesRegex(ValueError,'Unknown'):w.begin('assay','generation',{'x':1},{'generation':1})
            with patch.object(w,'counts',return_value={'assay':dict(d.BUDGET['assay'])}):
                with self.assertRaisesRegex(ValueError,'budget'):w.begin('assay','score',{'x':2},{'scores':1})

    def test_source_shortage_and_exclusions(self):
        from pact.schemas import task_from_dict,TaskLabel
        training=[(task_from_dict(r['task']),TaskLabel(r['task']['task_id'],self.source['labels'][r['task']['task_id']]))
                  for r in self.source['records']]
        excluded={'records':[r for r in self.source['records'] if r['split']!='prospective_development']}
        # Complete official validation fixtures are unnecessary for an empty-candidate shortfall.
        with patch('pact.training.data.audit_training_overlap',return_value=([],{})):
            result=evidence.select_fresh(excluded,training,[],{},True)
        self.assertEqual(result['status'],'prospective_eval_not_feasible')
        self.assertEqual(result['available'],dict.fromkeys(d.SOURCES,0))

    def test_sanitized_export_and_unsafe_evidence(self):
        import zipfile
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)/'run';create_plan(root,True);p=read_json(root/'plan.json')
            write_json(root/'summary.json',{'fixture':True})
            info=storage.package(root,Path(temp)/'safe.zip','SANITIZED')
            with zipfile.ZipFile(info['path']) as z:
                self.assertEqual(set(z.namelist()),{'summary.json','checksums.json','HANDOFF.json'})
            wallet=storage.Wallet(root,p)
            with self.assertRaisesRegex(ValueError,'budget'):
                wallet.begin('policy','score',{'test':True},{'scores':1})
            wallet.begin('assay','score',{'test':True},{'scores':1})
            self.assertFalse(storage.safe(root))
            guard(root,digest(p),True,allow_incomplete=True)
            self.assertTrue(storage.export(root,'manual')['PRIVATE'])
            # policy scoring is prohibited by its zero scoring budget.

    def test_compact_snapshot_latest_only_roundtrip(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)/'scratch'/d.ASSAY;root.parent.mkdir()
            create_plan(root,True);p=read_json(root/'plan.json')
            destination=Path(temp)/'drive'/d.ASSAY
            storage.persist(root,destination)
            storage.persist(root,destination)
            restored=Path(temp)/'restored'/d.ASSAY
            self.assertTrue(storage.restore(destination,restored)['restored'])
            self.assertEqual(read_json(restored/'plan.json'),p)
            self.assertEqual(storage.Wallet(restored,p).counts(),storage.Wallet(root,p).counts())
            write_json(destination/'SNAPSHOT_PENDING.json',{'pending':True})
            with self.assertRaisesRegex(ValueError,'safe latest'):
                storage.restore(destination,Path(temp)/'other')

    def test_locked_policy_tamper_and_old_execution(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)/'run';create_plan(root,True);p=read_json(root/'plan.json')
            write_json(root/'policies.json',{'aliases':{}})
            write_json(root/'policy-freeze-receipt.json',{'sha256':'wrong'})
            with self.assertRaisesRegex(ValueError,'policy matrices'):
                guard(root,digest(p),True)
            write_json(root/'probe_training/x/status.json',{'complete':True})
            self.assertTrue(evidence.old_assay_conflicts([root]))

    def test_random_joint_integer_constraints_and_witness(self):
        import random
        rng=random.Random(27)
        for _ in range(40):
            terminal=[]
            for b in self.blocks:
                a=rng.randrange(13);c=rng.randrange(13-a);terminal.append([a,c,12-a-c])
            output=d.source_family(terminal,self.blocks)
            for source in d.SOURCES:
                ix=[b for b,v in enumerate(self.blocks) if v['family']==source]
                for f in range(3):
                    total=sum(terminal[b][f] for b in ix)
                    self.assertEqual(sum(output[b][f] for b in ix),total)
                    self.assertTrue(all(output[b][f] in (total//len(ix),math.ceil(total/len(ix))) for b in ix))
            self.assertTrue(all(sum(r)==12 for r in output))
            self.assertEqual(output,d.source_family(terminal,self.blocks))
        with self.assertRaisesRegex(ValueError,'witness'):d.source_family([[0,0,0]]*8,self.blocks)
        with self.assertRaisesRegex(ValueError,'Eight'):d.quotas([[1,2,3]]*7)

    def test_v2_plan_refused_and_capacity_bound(self):
        from pact.revival.allocation.__main__ import create_plan as old_plan
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)/'run';old_plan(root,True)
            p=read_json(root/'plan.json')
            with self.assertRaisesRegex(ValueError,'Exact plan'):guard(root,digest(p),True)
        source=copy.deepcopy(self.source)
        counts={f:sum(r['family']==f for r in source['records']) for f in d.SOURCES}
        source['available']={f:counts[f]+(6 if f=='arc_challenge' else 6000) for f in d.SOURCES}
        result=evidence.prospective_capacity(source)
        self.assertEqual(result['status'],'prospective_eval_not_feasible')
        self.assertEqual(result['shortfall_at_least']['arc_challenge'],58)

    def test_exact_source_identity_not_just_counts(self):
        from pact.util import file_hash
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            write_json(root/'plan.json',{'source':self.source})
            write_json(root/'evidence/plan.json',{'source':self.source})
            files={n:file_hash(root/n) for n in ('plan.json','evidence/plan.json')}
            with patch.object(evidence,'AUTHORITATIVE_FILES',files),patch.object(evidence,'EXECUTED_SOURCE_HASH',digest(self.source)):
                self.assertEqual(digest(evidence.executed_source(root)),digest(self.source))
                changed=copy.deepcopy(self.source);changed['blocks'][0]['fit'].reverse()
                write_json(root/'plan.json',{'source':changed})
                with self.assertRaisesRegex(ValueError,'source_contract_conflict'):evidence.executed_source(root)

    def test_external_history_blocks_real_guard(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)/'run';create_plan(root,True)
            p=read_json(root/'plan.json');p['fixture']=False
            write_json(root/'plan.json',p)
            with patch('pact.revival.allocation_v3.__main__.code_identity',return_value=p['source_code']):
                with self.assertRaisesRegex(ValueError,'external Stage II/probe history'):
                    guard(root,digest(p),False)
        self.assertFalse(evidence.reviewed_history({'reviewed':True}))

    def test_intended_bounds_and_missing_support(self):
        v={'arc_challenge':[1.],'logiqa':[]}
        r=report.intended_bounds(v,dict.fromkeys(d.SOURCES,2),-1.,1.)
        self.assertEqual(r['by_source']['arc_challenge'],[0.,1.])
        self.assertEqual(r['equal_source'],[-.5,1.])
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)/'run';create_plan(root,True);p=read_json(root/'plan.json')
            support=report.assay_support(root,p)
            self.assertEqual(support['sources']['arc_challenge']['intended_tasks'],24)
            self.assertEqual(support['sources']['logiqa']['intended_tasks'],40)
            self.assertEqual(support['sources']['arc_challenge']['common_support_all_branches']['clean'],0)
            self.assertFalse(support['selection_uses_common_support_intersection'])

    def test_sender_privacy_and_strict_failure(self):
        from pact.revival import contracts as c
        bank=[{'status':'ok','answer':a,'justification':a} for a in 'ABC']
        original=copy.deepcopy(bank)
        attack={'sender':1,'packet':{'status':'ok','answer':'A','justification':'hostile'}}
        self.assertEqual(c.delivered(bank,0,attack)[0]['packet'],attack['packet'])
        self.assertEqual(c.delivered(bank,2,attack)[1]['packet'],attack['packet'])
        self.assertNotIn('hostile',str(c.delivered(bank,1,attack)))
        self.assertEqual(bank,original)
        self.assertEqual(c.parse('invalid',self.source['records'][0]['task'])['status'],'invalid')


class NeuralTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:import torch,safetensors
        except ImportError:raise unittest.SkipTest('Optional local torch/safetensors unavailable')
        torch.set_num_threads(1)

    def test_adam_scaling_and_distinct_schedule_updates(self):
        import torch
        def run(scale,values):
            x=torch.nn.Parameter(torch.tensor([.2]))
            opt=torch.optim.AdamW([x],lr=.01,weight_decay=0.,eps=1e-12)
            for y in values:
                opt.zero_grad();((x-y)**2*scale).backward();opt.step()
            return x.detach()
        self.assertTrue(torch.allclose(run(1,[1.]*8),run(10,[1.]*8),atol=1e-7))
        self.assertFalse(torch.allclose(run(1,[1.]*8),run(1,[-1.]*8)))

    def test_compiled_schedule_changes_tiny_adapter_updates(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)/'run';create_plan(root,True);p=read_json(root/'plan.json')
            records=runner.rows(p)
            uniform=d.schedules(p['blocks'],[[4]*3]*8,113)['Q']
            focused=d.schedules(p['blocks'],[[12,0,0]]*8,113)['Q']
            # First differing optimizer slot from the genuinely compiled plans.
            a,b=next((a,b) for a,b in zip(uniform,focused) if a['tasks']!=b['tasks'])
            hashes=[]
            for name,entry in [('uniform',a),('focused',b)]:
                result=models.train_schedule(root,p,root/name,'Q',[entry],records,
                    p['training_source']['labels'],113,None,storage.Wallet(root,p),'assay')
                hashes.append(result['adapter_hash'])
            self.assertNotEqual(hashes[0],hashes[1])

    def test_real_temporary_update_and_exact_rollback(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)/'run';create_plan(root,True);p=read_json(root/'plan.json')
            records=runner.rows(p);b=p['blocks'][0]
            schedule=[{'tasks':b['fit'][i:i+8]} for i in range(0,64,8)]
            path=root/'branches/block-0-Q'
            result=models.train_schedule(root,p,path,'Q',schedule,records,p['training_source']['labels'],
                                         17,None,storage.Wallet(root,p),'assay')
            rollback=read_json(path/'rollback.json')
            self.assertEqual(result['completed_steps'],8)
            self.assertEqual(result['forwards'],64)
            self.assertEqual(rollback['initial_hash'],rollback['restored_hash'])
            self.assertNotEqual(result['adapter_hash'],rollback['initial_hash'])
            durable=Path(temp)/'durable'/d.ASSAY
            storage.persist(root,durable)
            restored=Path(temp)/'restored'
            storage.restore(durable,restored)
            self.assertEqual(models.checkpoint_values(restored/'branches/block-0-Q')[1],result['adapter_hash'])
            with models.opened(root,p,'Q',None,path) as (backend,a):
                self.assertEqual(a.active,result['adapter_hash'])
                a.check(a.active)
            with models.opened(root,p,'R',None,None) as (backend,a):
                self.assertFalse(neural.parameters(backend.model))
            with self.assertRaises(ValueError):
                models.train_schedule(root,p,path,'Q',schedule,records,p['training_source']['labels'],
                                      17,None,storage.Wallet(root,p),'assay')

    def test_included_smoke_reuse_and_score_is_same_readout(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)/'run';create_plan(root,True);p=read_json(root/'plan.json')
            runner.collect(root,p,None,smoke=True)
            w=storage.Wallet(root,p)
            self.assertEqual(w.counts()['assay']['generation'],24)
            runner.collect(root,p,None,smoke=True)
            self.assertEqual(storage.Wallet(root,p).counts()['assay']['generation'],24)
            selected=runner.included_smoke([r for r in runner.rows(p).values() if r['split']=='allocation_probe'])
            # Reusing unchanged S0 private requests adds zero calls.
            runner.trajectory(root,p,selected,'branch-test',dict.fromkeys(d.FAMILIES,'S0'),'assay',None,changed='Q')
            self.assertEqual(storage.Wallet(root,p).counts()['assay']['generation'],42)
            # 1 changed private + 8 affected suffix calls per task, all three initial peers frozen.
            scopes=[v['identity']['dependency']['scope'] for v in storage.Wallet(root,p).intents.values()]
            self.assertEqual(sum(s[0]=='revision' and s[1]=='branch-test' for s in scopes),12)
