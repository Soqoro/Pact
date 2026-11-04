"""CPU-only adapter tests. No torch, model downloads, cluster or real source text."""
import copy
import tempfile
import unittest
import zipfile
from contextlib import contextmanager
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from pact.util import digest, file_hash, read_json, write_json, canonical
from pact.revival.documented_execution import plan, guard, runner, report, recovery
from pact.revival.documented_child import review
from pact.revival.gpqa_source import fixtures, contracts
from pact.revival.allocation_v3 import design as d, storage, runner as native
from pact.revival.mock import Backend, Tokenizer


class ExecutionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source,cls.candidate,_=fixtures.inputs()
        cls.s0={f:{'adapter_hash':digest(f)} for f in d.FAMILIES}
        cls.training=contracts.training_contract(cls.source,cls.s0)
        cls.graph=review.compile_graph(cls.source,cls.candidate,{'S0':cls.s0})
        cls.receipt={'candidate_digest':digest(cls.candidate),'graph_digest':digest(cls.graph),
                     'training_dependency_hash':digest(cls.training),'method_digest':'a'*64,
                     'limitations':['semantic_review_not_performed','historical_spending_unknown']}

    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)/plan.RUN;self.root.mkdir()
        self.p=plan.assemble(self.training,self.candidate,self.graph,self.receipt,self.root/'parent',{'fixture':True},True)
        write_json(self.root/'sealed/prospective.private.json',self.candidate)
        write_json(self.root/'sealed/graph.private.json',self.graph)
        self.p['prospective_hash']=file_hash(self.root/'sealed/prospective.private.json')
        self.p['graph_file_hash']=file_hash(self.root/'sealed/graph.private.json')
        write_json(self.root/'plan.json',self.p)

    def approval(self,stage,**scope):
        req=guard.scope(stage,**scope)
        write_json(self.root/'execution-preflight.json',{'plan_hash':digest(self.p),'fixture':True,
            'gpu_runtime_checked':True,'effective_S0_loading_checked':True,
            'native_access_checked':True,'context_checks_enabled':True})
        # Invented fixture decision only; never a real approval or signature.
        value={'version':'documented_stage2_stage_approval_v1','run_id':plan.RUN,
            'plan_hash':digest(self.p),'freeze':self.p['freeze'],'fixture':True,
            'scope':req,'limits':d.BUDGET,'historical_spending':None,'historical_budget_reset':False,
            'source_code':self.p['source_code'],'user_decision':'CPU test fixture only',
            'execution_approved':True,'spending_approved':stage!='preflight',
            'preflight_sha256':file_hash(self.root/'execution-preflight.json')}
        path=Path(self.temp.name)/'fixture-approval.json';write_json(path,value)
        return req,path,file_hash(path)

    @contextmanager
    def backend(self,root,p,family,cache,state):
        # Reuse token/call protocol fixture without instantiating its Torch model.
        b=Backend.__new__(Backend);b.key=family;b.tokenizer=Tokenizer();b.calls=[]
        b.identity={'snapshot':digest([family,str(state)]),'template_hash':digest(family)}
        yield b,SimpleNamespace(active=state,check=lambda *a,**k:None)

    def lock(self):
        aliases={f'{p}/{s}':'uniform/113' for p in d.POLICIES for s in d.SEEDS}
        write_json(self.root/'policies.json',{'aliases':aliases})
        write_json(self.root/'policy-freeze-receipt.json',{'sha256':file_hash(self.root/'policies.json')})
        write_json(self.root/'policy-lock.json',{'policies_hash':digest(read_json(self.root/'policies.json')),
            'analysis':self.p['analysis'],'aliases':aliases,'teams':{'S0':dict.fromkeys(d.FAMILIES,'S0'),
            'uniform/113':dict.fromkeys(d.FAMILIES,'S0')},'adapter_hashes':{'S0':self.p['s0']}})
        write_json(self.root/'exports/policy-lock.json',{'safe':True})
        write_json(self.root/'policy-lock-receipt.json',{'sha256':file_hash(self.root/'policy-lock.json')})

    def test_budget_and_training_embargo(self):
        self.assertEqual(self.graph['counts'],{p:d.BUDGET[p] for p in ('assay','policy')})
        self.assertEqual(self.graph['reserved_output_tokens'],12148736)
        for row in self.candidate['records']:
            self.assertNotIn(row['task']['task_id'],canonical(self.p['training_source']))
        self.assertEqual({f:len(v) for f,v in self.p['probes'].items()},{'arc_challenge':24,'logiqa':40})
        bad=copy.deepcopy(self.graph);bad['counts']['assay']['generation']+=1
        with self.assertRaises(ValueError):plan.assemble(self.training,self.candidate,bad,self.receipt,'/tmp',{},True)

    def test_denied_approval_has_no_wallet_or_model_side_effect(self):
        with patch.object(runner.models,'opened') as model,patch.object(storage,'Wallet') as wallet:
            with self.assertRaises(PermissionError):
                runner.execute(self.root,digest(self.p),guard.scope('assay-smoke'),None,None)
            model.assert_not_called();wallet.assert_not_called()
        self.assertFalse((self.root/'events').exists())
        self.assertFalse((self.root/'approvals').exists())

    def test_stage_scope_and_preflight_binding(self):
        req,path,h=self.approval('branch',block=0,family='Q')
        guard.authorize(self.root,self.p,req,path,h)
        for other in (guard.scope('branch',block=1,family='Q'),guard.scope('collect')):
            with self.assertRaises(PermissionError):guard.authorize(self.root,self.p,other,path,h)
        write_json(self.root/'execution-preflight.json',{'plan_hash':'changed'})
        with self.assertRaises(PermissionError):guard.authorize(self.root,self.p,req,path,h)
        with self.assertRaises(ValueError):guard.scope('continuation',policy='unknown',seed=113,family='Q')

    def test_native_smoke_counts_and_exact_reuse(self):
        req,path,h=self.approval('assay-smoke')
        with patch.object(runner.models,'opened',side_effect=self.backend):
            result=runner.execute(self.root,digest(self.p),req,path,h)
            self.assertTrue(result['stop_for_review'])
            self.assertEqual(storage.Wallet(self.root,self.p).counts()['assay']['generation'],24)
            runner.execute(self.root,digest(self.p),req,path,h)
            self.assertEqual(storage.Wallet(self.root,self.p).counts()['assay']['generation'],24)
        self.assertTrue(storage.safe(self.root))
        with zipfile.ZipFile(result['bundles']['SANITIZED']['path']) as z:
            text=''.join(z.read(n).decode() for n in z.namelist())
            self.assertNotIn('plan.json',z.namelist())
            self.assertNotIn('sealed/prospective.private.json',z.namelist())
            for r in self.candidate['records']:self.assertNotIn(r['task']['task_id'],text)
        with zipfile.ZipFile(result['bundles']['PRIVATE']['path']) as z:
            self.assertIn('sealed/prospective.private.json',z.namelist())

    def test_policy_smoke_is_gpqa_logiqa_and_uses_frozen_nodes(self):
        selected=runner.smoke_rows(self.root,self.p,self.candidate['records'],'policy')
        self.assertEqual({r['family'] for r in selected},{'gpqa_main','logiqa'})
        self.lock()
        req,path,h=self.approval('evaluation-smoke')
        with patch.object(runner.models,'opened',side_effect=self.backend):
            runner.execute(self.root,digest(self.p),req,path,h)
        # Two unique teams instead of eleven logical teams; aliases reduce work.
        self.assertEqual(storage.Wallet(self.root,self.p).counts()['policy']['generation'],46)
        outs=[read_json(p)['logical'] for p in (self.root/'outputs').glob('*.json')]
        self.assertEqual({o[2] for o in outs},{r['task']['task_id'] for r in selected})
        metrics=read_json(self.root/'policy_results.json')
        self.assertEqual(metrics['source_weights'],{'gpqa_main':.5,'logiqa':.5})
        self.assertEqual(metrics['by_source']['gpqa_main']['planned'],64)
        self.assertIsNone(metrics['by_source']['gpqa_main']['teams']['S0/clean']['accuracy'])

    def test_initial_peer_protocol_matches_graph_seeds(self):
        rows=runner.smoke_rows(self.root,self.p,self.candidate['records'],'policy')
        self.lock()
        with patch.object(runner.models,'opened',side_effect=self.backend):runner.evaluate(self.root,self.p,None,None,True)
        nodes={(n['task_id'],n['phase'],n['slot'],n['condition']):n for n in self.graph['nodes']
               if n['part']=='policy' and n.get('team')=='S0' and n['kind']=='generation'}
        for row in rows:
            tid=row['task']['task_id']
            bank=[native.output(self.root,['policy','S0',tid,'private',s])['packet'] for s in range(3)]
            from pact.revival import contracts as c
            for slot in range(3):
                v=native.output(self.root,['policy','S0',tid,'clean','revision',slot])
                self.assertEqual(v['call']['seed'],nodes[tid,'revision',slot,'clean']['seed'])
                from dataclasses import asdict
                expected=c.prompt(row['task'],c.envelope(bank[slot],slot),c.delivered(bank,slot,None))
                self.assertEqual(v['call']['messages'],[asdict(m) for m in expected])

    def test_unknown_attempt_and_pending_snapshot_never_retry(self):
        req,path,h=self.approval('assay-smoke')
        wallet=storage.Wallet(self.root,self.p)
        wallet.begin('assay','score',{'test':'ambiguous'},{'scores':1})
        with self.assertRaisesRegex(ValueError,'unresolved'):
            guard.authorize(self.root,self.p,req,path,h)
        with self.assertRaises(ValueError):storage.Wallet(self.root,self.p)
        dest=Path(self.temp.name)/'durable'/plan.RUN;write_json(dest/'SNAPSHOT_PENDING.json',{})
        with self.assertRaisesRegex(ValueError,'durable'):guard.authorize(self.root,self.p,req,path,h,dest)

    def test_wallet_caps_and_no_partial_limit_override(self):
        wallet=storage.Wallet(self.root,self.p)
        wallet._counts['assay']['scores']=2640
        with self.assertRaisesRegex(ValueError,'exhausted'):wallet.begin('assay','score',{}, {'scores':1})
        req,path,h=self.approval('score');a=read_json(path);a['limits']={};write_json(path,a)
        with self.assertRaises(PermissionError):guard.authorize(self.root,self.p,req,path,file_hash(path))

    def test_policy_checkpoint_substitution_stops_before_trajectory(self):
        self.lock();lock=read_json(self.root/'policy-lock.json')
        lock['teams']={'uniform/113':dict.fromkeys(d.FAMILIES,'/tmp/checkpoint')}
        lock['adapter_hashes']={'uniform/113':dict.fromkeys(d.FAMILIES,'expected')}
        write_json(self.root/'policy-lock.json',lock)
        with patch.object(native,'attacks') as attacks,patch.object(native,'trajectory') as calls, \
             patch.object(runner.models,'checkpoint_values',return_value=({},'different')):
            with self.assertRaises(ValueError):runner.evaluate(self.root,self.p,None,None,True)
            calls.assert_not_called();attacks.assert_not_called()

    def test_safe_restore_checks_expected_plan_and_keeps_history(self):
        dest=Path(self.temp.name)/'durable'/plan.RUN
        with patch('pact.storage.storage_operation') as op:
            # Build a real compact snapshot using its existing serializer,
            # emulate only the filesystem transport into content addresses.
            def snapshot(operation,source,destination,**kw):
                checks={}
                for f in source.rglob('*'):
                    if f.is_file():
                        h=file_hash(f);target=destination/'objects'/h;target.parent.mkdir(parents=True,exist_ok=True)
                        target.write_bytes(f.read_bytes());checks[f.relative_to(source).as_posix()]=h
                snap=destination/'snapshots/001';write_json(snap/'index.json',{'files':checks})
                (snap/'COMPLETE').write_text(file_hash(snap/'index.json'))
            op.side_effect=snapshot;storage.persist(self.root,dest)
        restored=Path(self.temp.name)/'restored'/plan.RUN
        with self.assertRaises(ValueError):recovery.restore(dest,restored,'0'*64)
        self.assertFalse(restored.exists())
        self.assertTrue(recovery.restore(dest,restored,digest(self.p))['restored'])
        self.assertEqual(digest(read_json(restored/'plan.json')),digest(self.p))
        (dest/'snapshots/002').mkdir()
        with self.assertRaises((ValueError,FileNotFoundError)):
            recovery.restore(dest,Path(self.temp.name)/'another'/plan.RUN,digest(self.p))

    def test_changed_seal_or_policy_denies_dispatch(self):
        write_json(self.root/'sealed/prospective.private.json',{'changed':True})
        with self.assertRaisesRegex(ValueError,'sealed'):plan.validate(self.root,digest(self.p))

    def test_branch_and_continuation_use_native_training_and_explicit_resume(self):
        for stage,kw,method,args in (
            ('branch',{'block':2,'family':'L'},'branch',(2,'L')),
            ('continuation',{'policy':'uniform','seed':227,'family':'M'},'continuation',('uniform',227,'M'))):
            req,path,h=self.approval(stage,**kw)
            with patch.object(native,method,return_value={'fixture':'no_training'}) as call:
                runner.execute(self.root,digest(self.p),req,path,h,resume=True)
                self.assertEqual(call.call_args.args[2:2+len(args)],args)
                self.assertTrue(call.call_args.args[-1])

    def test_invalid_and_missing_policy_outputs_remain_distinct(self):
        self.lock();row=self.candidate['records'][0];tid=row['task']['task_id']
        native.link(self.root,['policy','S0',tid,'clean','final'],
                    {'packet':{'status':'invalid','answer':None,'justification':''}})
        report.policy_report(self.root,self.p)
        rows=read_json(self.root/'policy_outcomes.private.json')
        invalid=next(r for r in rows if r['task']==tid and r['team']=='S0' and r['condition']=='clean')
        missing=next(r for r in rows if r['task']!=tid and r['team']=='S0' and r['condition']=='clean')
        self.assertIs(invalid['correct'],False);self.assertEqual(invalid['format_status'],'invalid')
        self.assertIsNone(missing['correct']);self.assertEqual(missing['format_status'],'missing')

    def test_policy_lock_hash_is_checked_before_execution(self):
        self.lock();lock=read_json(self.root/'policy-lock.json');lock['teams'].pop('S0')
        write_json(self.root/'policy-lock.json',lock)
        with self.assertRaisesRegex(ValueError,'lock_changed'):plan.validate(self.root,digest(self.p))


if __name__=='__main__':unittest.main()
