import contextlib
import copy
import dataclasses as dc
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from pact.benchmarks.registry import REGISTRY,budget
from pact.benchmarks.contracts import BenchmarkInput,messages,parse,boxed
from pact.benchmarks.data import normalize,literal_choices,partition,live_membership,ReadinessError,group_variants
from pact.benchmarks.fixtures import dataset,EXAMPLES,MockNative
from pact.benchmarks.scoring import score,scoring_job,import_result
from pact.studies.breadth import freeze,schedule,collect,reconstruct,score_run,report,export,unpack,checkpoint,restore
from pact.util import digest,read_json,write_json
from pact.environment import code_identity

ROOT=Path(__file__).resolve().parents[1]

class BreadthTests(unittest.TestCase):
    def test_zero_support_is_completed_not_gated(self):
        with tempfile.TemporaryDirectory() as tmp,contextlib.redirect_stdout(io.StringIO()):
            root=Path(tmp)/'run';p=self.plan(root)
            for k in 'QLM':collect(root,p,'private',k,MockNative(k,p))
            with patch('pact.benchmarks.fixtures.fixture_score',return_value={'availability':'scored','syntactic_valid':True,'full_success':False,'native_score':0.0}):
                score_run(root)
            summary=report(root)
            self.assertEqual(summary['phases']['A']['status'],'complete')
            self.assertEqual(summary['teams']['QLM']['complete_case']['coverage']['value'],0)
            collect(root,p,'revision','Q',MockNative('Q',p))

    def test_live_native_dispatch_preserves_fractional_score(self):
        import types
        from pact.benchmarks.score_worker import live_score
        calls=[]
        common=types.ModuleType('livebench.common');common.MatchSingle=lambda **kw:kw
        judging=types.ModuleType('livebench.gen_ground_truth_judgment')
        def judge(match,*args):calls.append(match);return {'score':0.5}
        judging.play_a_match_gt=judge
        with patch.dict(sys.modules,{'livebench.common':common,'livebench.gen_ground_truth_judgment':judging}),patch('pact.benchmarks.score_worker.require_pin'):
            result=live_score({'identity':{'code':'fixture'},'eval':{'problem':EXAMPLES['livebench']},'prediction':'FALSE'})
        self.assertEqual(result['native_score'],.5);self.assertFalse(result['full_success'])
        self.assertEqual(calls[0]['answer']['choices'][0]['turns'],['FALSE'])

    def test_joint_exposure_index_blocks_earlier_locked_groups(self):
        from pact.benchmarks.data import exposure_index
        rows=[]
        for i in range(12):
            r=copy.deepcopy(EXAMPLES['math-500']);r.update(unique_id=str(i),problem='Fictional task '+str(i))
            rows.append(normalize('math-500',r,'sha'))
        _,m=partition('math-500',copy.deepcopy(rows),n=4)
        index=exposure_index([{'dataset':'math-500','manifest':m}])
        self.assertEqual(len(index['blocked_fingerprints']),12)
        with self.assertRaises(ReadinessError):partition('math-500',rows,n=4,known=index)

    def test_pinned_models_and_live_scorer_registration(self):
        from pact.benchmarks.registry import live_registered
        self.assertTrue(live_registered({'category':'reasoning','task':'web_of_lies_v3'}))
        self.assertFalse(live_registered({'category':'reasoning','task':'unregistered_task'}))
        self.assertFalse(live_registered({'category':'coding','task':'agentic_coding'}))
        with patch('pact.studies.breadth.model_registry',return_value={}):
            with self.assertRaises(ValueError):freeze(dataset('mmlu-pro'),{},True)

    def plan(self,root,name='mmlu-pro'):
        p=freeze(dataset(name),code_identity(ROOT),True)
        write_json(root/'plan.json',p);write_json(root/'state.json',{'plan_hash':digest(p),'recovery_safe':True})
        return p

    def test_compact_restore_and_unsafe_refusal(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)/'run';persistent=Path(tmp)/'persist';p=self.plan(root)
            checkpoint(root,persistent)
            dest=Path(tmp)/'restored';restore(persistent,dest)
            self.assertEqual(read_json(root/'plan.json'),read_json(dest/'plan.json'))
            write_json(root/'state.json',{'plan_hash':digest(p),'recovery_safe':False})
            checkpoint(root,persistent)
            with self.assertRaises(ValueError):restore(persistent,Path(tmp)/'unsafe')

    def test_score_import_binds_all_identities_and_fractional_credit(self):
        with tempfile.TemporaryDirectory() as tmp,contextlib.redirect_stdout(io.StringIO()):
            root=Path(tmp)/'run';p=self.plan(root,'livebench')
            collect(root,p,'private','Q',MockNative('Q',p),stop_after=1)
            _,results,_,rows=reconstruct(root,p);row=next(r for r in rows if r['key'] in results);item=p['data']['selected'][0]
            job=scoring_job(BenchmarkInput.from_dict(item['task']),item['eval'],results[row['key']],row['key'])
            v={'job_hash':job['job_hash'],'identity':job['identity'],'sandbox':{'enforced':True},
               'score':{'availability':'scored','full_success':False,'native_score':.5}}
            self.assertEqual(import_result(job,v)['native_score'],.5)
            binary=copy.deepcopy(job);binary['kind']='python_program'
            with self.assertRaises(ValueError):import_result(binary,v)
            v['score']['full_success']=True
            with self.assertRaises(ValueError):import_result(job,v)
            v['job_hash']='0'*64
            with self.assertRaises(ValueError):import_result(job,v)

    def test_four_variants_stay_grouped_without_quota_inflation(self):
        rows=[]
        for domain in ('murder_mysteries','object_placements','team_allocation'):
            for group in range(6):
                for variant in range(4):
                    r=dict(EXAMPLES['musr']);r['narrative']=f'Fictional story {domain} {group}.'
                    r['answer_index']=str(variant%2);r['answer_choice']=['room one','room two'][variant%2]
                    rows.append(normalize('musr',r,'sha',domain=domain,index=group*4+variant))
        selected,m=partition('musr',rows,n=6)
        self.assertEqual(len(selected),6)
        for members in m['group_members'].values():
            self.assertEqual(len({m['variant_partition_by_id'][i] for i in members}),1)
        self.assertEqual(len(m['variant_partition_by_id']),72)

    def test_response_caps_and_phase_b_only_initial_peers(self):
        from pact.studies.breadth import request_for
        with tempfile.TemporaryDirectory() as tmp,contextlib.redirect_stdout(io.StringIO()):
            root=Path(tmp)/'run';p=self.plan(root,'mbpp-plus')
            for k in 'QLM':collect(root,p,'private',k,MockNative(k,p))
            _,results,_,rows=reconstruct(root,p)
            row=next(r for r in rows if r['stage']=='revision')
            before,deps=request_for(p,row,rows,results)
            collect(root,p,'revision','Q',MockNative('Q',p),stop_after=1)
            after,after_deps=request_for(p,row,rows,reconstruct(root,p)[1])
            self.assertEqual(before,after);self.assertEqual(deps,after_deps)
            self.assertEqual(before.max_tokens,1024)
            self.assertNotIn('plus_input',str(before.messages))
            self.assertTrue(all(next(r for r in rows if r['key']==k)['stage']=='private' for k in deps))

    def test_notebook_cells_compile_and_default_plan(self):
        for name in ('10_benchmark_breadth_colab.ipynb','11_isolated_code_scoring.ipynb'):
            notebook=json.loads((ROOT/'notebooks'/name).read_text())
            for i,c in enumerate(notebook['cells']):
                if c['cell_type']=='code':compile(''.join(c['source']),name+str(i),'exec');self.assertFalse(c.get('outputs'))
            text='\n'.join(''.join(c['source']) for c in notebook['cells'])
            self.assertIn('EXECUTE = False',text)

    def test_gpqa_parent_allocation_preserves_exposure(self):
        from pact.studies.gpqa_data import partition as gpqa_partition,DOMAINS as GPQA_DOMAINS
        from pact.benchmarks.data import gpqa_child_rows
        raw=[]
        for i in range(198):
            raw.append({'Record ID':str(i),'Question':f'Invented question {i}?','Correct Answer':'one',
                        'Incorrect Answer 1':'one' if i<2 else 'two','Incorrect Answer 2':'three','Incorrect Answer 3':'four',
                        'High-level domain':GPQA_DOMAINS[i%3]})
        _,parent=gpqa_partition(raw,'fixture')
        rows=gpqa_child_rows(raw,'fixture',parent);selected,m=partition('gpqa',rows)
        self.assertEqual([len(m['partitions'][k]) for k in ('characterization_dev','confirmation_locked','reserve_locked')],[32,32,100])
        self.assertFalse(set(parent['selected_ids'])&set(m['partitions']['characterization_dev']))
        tampered=copy.deepcopy(parent);tampered['selected_ids'][0]='unknown'
        with self.assertRaises(ReadinessError):gpqa_child_rows(raw,'fixture',tampered)

    def test_pending_scores_not_failures_and_no_communication_zeros(self):
        with tempfile.TemporaryDirectory() as tmp,contextlib.redirect_stdout(io.StringIO()):
            root=Path(tmp)/'run';p=self.plan(root,'mbpp-plus')
            for k in 'QLM':collect(root,p,'private',k,MockNative(k,p))
            # No scores: all intended tasks remain visible with bounds, not fake failures.
            out=report(root)
            self.assertEqual(out['phases']['A']['generated'],18)
            self.assertEqual(out['phases']['A']['scored'],0)
            self.assertEqual(out['teams']['QLM']['complete_case']['coverage_intended_bounds'],[0,1])
            self.assertIsNone(out['teams']['QLM']['complete_case']['terminal']['debate'])
            self.assertIsNone(out['teams']['QLM']['complete_case']['erasure'])

    def test_plan_matches_user_budget_json(self):
        design=json.loads((ROOT/'docs/benchmark_breadth_design.json').read_text())
        aliases={'mmlu_pro':'mmlu-pro','math500':'math-500','math_500':'math-500','mbppplus':'mbpp-plus','mbpp_plus':'mbpp-plus','gpqa_diamond':'gpqa','livebench':'livebench','musr':'musr'}
        for item in design['datasets']:
            name=aliases.get(item['key'])
            self.assertIsNotNone(name,item['key'])
            b=budget(name)
            self.assertEqual(item['ceilings'],{'phase_a_calls':b['A']['calls'],'phase_a_output_tokens':b['A']['tokens'],'phase_b_calls':b['B']['calls'],'phase_b_output_tokens':b['B']['tokens']})

    @unittest.skipUnless(os.environ.get('PACT_ISOLATED_PYTHON'),'Pinned isolated EvalPlus runtime not available')
    def test_official_expanded_fixture_scoring(self):
        from pact.benchmarks.isolation import Bubblewrap
        from pact.benchmarks.scoring import evaluator_identity
        worker=Bubblewrap(os.environ['PACT_ISOLATED_PYTHON'])
        problem=EXAMPLES['mbpp-plus']
        for code,base,plus in [('def fixture_increment(x): return x+1',True,True),('def fixture_increment(x): return 1',True,False)]:
            body={'kind':'python_program','eval':{'problem':problem},'prediction':code,'identity':evaluator_identity('python_program')}
            result=worker.run({**body,'job_hash':digest(body)})['score']
            self.assertEqual(result['availability'],'scored',result)
            self.assertEqual((result['base_pass'],result['plus_pass']),(base,plus))

    def test_exact_budgets(self):
        values=[budget(k) for k in REGISTRY]
        self.assertEqual(sum(b['A']['calls'] for b in values),5058)
        self.assertEqual(sum(b['A']['tokens'] for b in values),3898368)
        self.assertEqual(sum(b['B']['calls'] for b in values),9030)
        self.assertEqual(sum(b['B']['tokens'] for b in values),5846400)
        for name in REGISTRY:
            p=freeze(dataset(name,REGISTRY[name].n),{},True);rows=schedule(p)
            self.assertEqual(sum(r['task_id'] in p['smoke_ids'] and r['phase']=='A' for r in rows),18)
            self.assertEqual(len(rows),sum(v['calls'] for v in p['budgets'].values()))
            self.assertEqual(sum(r['cap'] for r in rows),sum(v['tokens'] for v in p['budgets'].values()))

    def test_mcq_J_and_label_boundary(self):
        row=normalize('mmlu-pro',EXAMPLES['mmlu-pro'],'sha');t=BenchmarkInput.from_dict(row['task'])
        self.assertEqual(parse(t,'{"answer":"J","justification":"why"}')['value'],'J')
        self.assertNotIn('EVALUATOR_ONLY',str(messages(t)))
        altered=copy.deepcopy(EXAMPLES['mmlu-pro']);altered['answer']='A'
        with self.assertRaises(ReadinessError):normalize('mmlu-pro',altered,'sha')
        with self.assertRaises(TypeError):messages(row)
        with self.assertRaises(ValueError):messages(dc.replace(t,split='confirmation_locked'))
        self.assertEqual(len(t.options),10)

    def test_musr_literal_group_variants(self):
        with self.assertRaises(ReadinessError):literal_choices("__import__('os').system('false')")
        a=normalize('musr',EXAMPLES['musr'],'sha',domain='object_placements')
        b=copy.deepcopy(EXAMPLES['musr']);b.update(answer_index='0',answer_choice='room one')
        b=normalize('musr',b,'sha',domain='object_placements',index=1)
        grouped=group_variants([a,b]);self.assertEqual(grouped[0]['group_id'],grouped[1]['group_id'])
        self.assertNotEqual(grouped[0]['eval'],grouped[1]['eval'])
        self.assertIn(EXAMPLES['musr']['narrative'],str(messages(BenchmarkInput.from_dict(a['task']))))

    def test_math_code_native_contracts(self):
        for name in REGISTRY:
            t=BenchmarkInput.from_dict(dataset(name)['selected'][0]['task'])
            if t.kind!='mcq':self.assertFalse(t.options)
        t=BenchmarkInput.from_dict(dataset('math-500')['selected'][0]['task'])
        self.assertEqual(boxed(r'work \boxed{\frac{1}{2}}'),r'\frac{1}{2}')
        self.assertIsNone(boxed(r'\boxed{1} then \boxed{2}'))
        self.assertEqual(parse(t,r'\boxed{1}',stop='length')['status'],'length')
        t=BenchmarkInput.from_dict(dataset('mbpp-plus')['selected'][0]['task'])
        raw='```python\ndef f(): return 1\n```'
        self.assertEqual(parse(t,raw)['value'],'def f(): return 1')
        self.assertIsNone(parse(t,raw)['vote_key'])
        self.assertNotIn('canonical_solution',str(messages(t)))
        self.assertNotIn('plus_input',str(messages(t)))
        self.assertEqual(score(t,{},raw)['availability'],'pending_isolated_scoring')

    def test_live_release_boundaries(self):
        r=EXAMPLES['livebench'].copy()
        self.assertTrue(live_membership(r))
        r['livebench_removal_date']='2026-06-25';self.assertFalse(live_membership(r))
        r['livebench_removal_date']='2026-06-26';self.assertTrue(live_membership(r))
        r['livebench_release_date']='2027-01-01';self.assertFalse(live_membership(r))

    def test_partition_determinism_and_shortfall(self):
        rows=[]
        for i in range(12):
            r=copy.deepcopy(EXAMPLES['math-500']);r.update(unique_id=str(i),problem='Fictional distinct task '+str(i))
            rows.append(normalize('math-500',r,'sha'))
        a,m=partition('math-500',copy.deepcopy(rows),n=4);b,n=partition('math-500',copy.deepcopy(rows),n=4)
        self.assertEqual(m,n);self.assertEqual(a,b)
        sets=[set(v) for v in m['partitions'].values()]
        self.assertEqual(sum(map(len,sets)),12);self.assertFalse(sets[0]&sets[1])
        with self.assertRaises(ReadinessError):partition('math-500',rows,n=7)

    def test_full_roundtrips_all_types(self):
        for name in ('mmlu-pro','musr','math-500','mbpp-plus','livebench','gpqa'):
            with self.subTest(name=name),tempfile.TemporaryDirectory() as tmp,contextlib.redirect_stdout(io.StringIO()):
                root=Path(tmp)/'run';p=self.plan(root,name)
                for k in 'QLM':collect(root,p,'private',k,MockNative(k,p),smoke=True)
                self.assertEqual(len(reconstruct(root,p)[1]),18)
                for k in 'QLM':self.assertEqual(collect(root,p,'private',k,MockNative(k,p))['new_attempts'],0)
                score_run(root);a=report(root)
                self.assertEqual(a['phases']['A']['status'],'complete')
                self.assertIsNone(a['teams']['QLM']['complete_case']['utilization'])
                if p['profile']['core']:
                    for k in 'QLM':collect(root,p,'revision',k,MockNative(k,p))
                    collect(root,p,'readout','R',MockNative('R',p));score_run(root)
                    b=report(root);self.assertEqual(b['phases']['B']['status'],'complete')
                else:b=a
                z=export(root,None);dest=Path(tmp)/'import';unpack(Path(z['private']['path']),z['private']['sha256'],dest)
                self.assertEqual(report(dest),b)
                import zipfile
                with zipfile.ZipFile(z['sanitized']['path']) as archive:
                    content=archive.read('summary.json').decode()
                    self.assertNotIn('Fictional',content);self.assertNotIn('canonical_solution',content)

    def test_barrier_budget_unknown_tamper_and_reuse(self):
        with tempfile.TemporaryDirectory() as tmp,contextlib.redirect_stdout(io.StringIO()):
            root=Path(tmp)/'run';p=self.plan(root)
            with self.assertRaises(ValueError):collect(root,p,'revision','Q',MockNative('Q',p))
            collect(root,p,'private','Q',MockNative('Q',p),stop_after=1)
            self.assertEqual(collect(root,p,'private','Q',MockNative('Q',p))['new_attempts'],5)
            path=next((root/'calls/shards').glob('*.sha256'));path.unlink()
            with self.assertRaises(ValueError):collect(root,p,'private','Q',MockNative('Q',p))

    def test_real_cli_entrypoints(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)/'pact-breadth-mmlu-pro-001';data=Path(tmp)/'data.json';write_json(data,dataset('mmlu-pro'))
            env={**os.environ,'PYTHONPATH':str(ROOT/'src')}
            def run(*args,ok=True):
                p=subprocess.run([sys.executable,'-m','pact',*map(str,args)],env=env,capture_output=True,text=True)
                self.assertEqual(p.returncode,0 if ok else 2,p.stdout+p.stderr);return p
            run('benchmarks','list')
            run('breadth','plan','--run-dir',root,'--data',data,'--mock')
            h=digest(read_json(root/'plan.json'))
            run('breadth','smoke','--run-dir',root,'--plan-hash',h,'--execute','--mock')
            run('breadth','score','--run-dir',root,'--plan-hash',h,'--mock')
            run('breadth','report','--run-dir',root,'--mock')
            run('breadth','readout','--run-dir',root,'--phase','A','--plan-hash',h,'--execute','--mock',ok=False)
            for model in 'QLM':
                run('breadth','revisions','--run-dir',root,'--phase','B','--model',model,'--plan-hash',h,'--execute','--mock')
            run('breadth','readout','--run-dir',root,'--phase','B','--plan-hash',h,'--execute','--mock')
            run('breadth','score','--run-dir',root,'--plan-hash',h,'--mock')
            run('breadth','export','--run-dir',root,'--mock')
            self.assertEqual(read_json(root/'summary.json')['phases']['B']['status'],'complete')
            bundle=next((root.parent/'bundles').glob('*PRIVATE*.zip'))
            from pact.util import file_hash
            run('breadth','audit','--run-dir',Path(tmp)/'audit','--bundle',bundle,'--sha256',file_hash(bundle),'--mock')

    def test_isolation_refuses_missing_backend(self):
        from pact.benchmarks.isolation import Bubblewrap,IsolationUnavailable
        with patch('pact.benchmarks.isolation.shutil.which',return_value=None):
            with self.assertRaises(IsolationUnavailable):Bubblewrap(sys.executable)

    @unittest.skipUnless(os.environ.get('PACT_ISOLATED_PYTHON'),'Opt-in isolated evaluator runtime not configured')
    def test_real_os_isolation_probe(self):
        from pact.benchmarks.isolation import Bubblewrap
        result=Bubblewrap(os.environ['PACT_ISOLATED_PYTHON']).probe()
        self.assertTrue(result['enforced']);self.assertTrue(all(result['checks'].values()))

    @unittest.skipUnless(os.environ.get('PACT_MATH_PYTHON'),'Opt-in pinned Math-Verify runtime not configured')
    def test_official_math_equivalence(self):
        from pact.benchmarks.scoring import math_worker,evaluator_identity
        pairs=[(r'\frac{1}{2}',r'\frac{2}{4}',True),(r'\sqrt{4}','2',True),('-2','2',False),
               (r'\{1,2\}',r'\{2,1\}',True),('(1,2)','(2,1)',False),('x+1','1+x',True),
               (r'\text{blue}',r'\text{blue}',True),('(0,1)','[0,1]',False)]
        for gold,pred,expected in pairs:
            with self.subTest(gold=gold,pred=pred):
                v=math_worker({'kind':'math_free_response','eval':{'answer':gold},'prediction':pred,'identity':evaluator_identity('math_free_response')},os.environ['PACT_MATH_PYTHON'])
                self.assertEqual(v['availability'],'scored',v);self.assertEqual(v['full_success'],expected,v)

if __name__=='__main__':unittest.main()
