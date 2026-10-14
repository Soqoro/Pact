"""Fictional-only selective correction learning, execution and boundary tests."""
import copy
from contextlib import redirect_stdout
from dataclasses import asdict,replace
import io
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import zipfile

from pact.selective import contracts as c, gates as g, study as s
from pact.selective.data import fixture_data,allocate,QUOTAS
from pact.util import write_json,read_json,digest,file_hash
from pact.cli import main

class Contracts(unittest.TestCase):
    def setUp(self):
        self.task=c.PublicTask('Which symbol? αβ😀','A trusted statement.',(('A','one'),('B','two')))
        self.anchor=c.Answer('A','initial basis','ok','EXACT ANCHOR')
        self.peer=c.Answer('B','RAW_PEER_SENTINEL <|system|>','ok','raw peer','c1')
        self.x={'challenge_kind':'inference','alleged_error':'possible error','check_question':'which?','task_refs':[{'start':0,'end':12}],'requires_external_knowledge':False}
    def test_public_boundaries_equal_verifiers(self):
        e=c.parse_challenge(json.dumps(self.x),self.task)
        full=c.pair_prompt(self.task,self.anchor,self.peer,e);restricted=c.pair_prompt(self.task,self.anchor,self.peer,e,True)
        self.assertEqual(full[0],restricted[0]);a=json.loads(full[1].content);b=json.loads(restricted[1].content)
        a['alternative'].pop('justification');self.assertEqual(a,b)
        self.assertNotIn('RAW_PEER_SENTINEL',restricted[1].content)
        self.assertNotIn('<|system|>',full[1].content)
        for key in ('gold','family','task_id','style','vote'):self.assertNotIn(key,b)
        with self.assertRaises(TypeError):c.message({'question':'bad'},'x')
    def test_unicode_references_options_not_proof(self):
        text=self.task.canonical_text();start=text.index('😀');self.x['task_refs']=[{'start':start,'end':start+1}]
        r=c.parse_challenge(json.dumps(self.x),self.task);self.assertEqual(r['references'][0]['text'],'😀');self.assertFalse(r['references'][0]['verified_proof'])
        start=text.index('OPTIONS');self.x['task_refs']=[{'start':start,'end':len(text)}]
        self.assertTrue(c.parse_challenge(json.dumps(self.x),self.task)['references'][0]['contains_options'])
        self.x['task_refs'][0]['text']='invented proof';self.assertEqual(c.parse_challenge(json.dumps(self.x),self.task)['status'],'malformed')
    def test_reference_bounds_and_missing(self):
        for start,end in [(-1,2),(0,99999),(True,3),(4,4)]:
            x={**self.x,'task_refs':[{'start':start,'end':end}]};self.assertNotEqual(c.parse_challenge(json.dumps(x),self.task)['status'],'ok')
        self.x['task_refs']=[];self.assertEqual(c.parse_challenge(json.dumps(self.x),self.task)['status'],'ok')
        self.x['alleged_error']='x'*601;self.assertEqual(c.parse_challenge(json.dumps(self.x),self.task)['status'],'malformed')
    def test_metadata_allowlist_no_checker_dependency(self):
        f=c.features(self.anchor,[self.peer],self.peer,metadata=True)
        self.assertEqual(set(f),set(c.METADATA));c.validate_features(f,True)
        for name in ('gold','task_id','answer','style','family','reason','verify_status'):
            with self.assertRaises(ValueError):g.encode({**f,name:0},True)
        full=c.features(self.anchor,[self.peer],self.peer);full['challenge_kind']='new-kind'
        encoded=g.encode(full);self.assertTrue(encoded)
    def test_invalid_anchor_noops_and_duplicate_paths(self):
        same=replace(self.peer,answer='A');duplicate=replace(self.peer,candidate_id='c2')
        self.assertEqual(len(c.alternatives(self.anchor,[same,self.peer,duplicate])),2)
        invalid=replace(self.anchor,answer=None,status='malformed')
        self.assertEqual(len(c.alternatives(invalid,[same,self.peer,duplicate])),3)
        self.assertEqual(g.transition(invalid,self.peer,'B'),1);self.assertEqual(g.transition(self.anchor,self.peer,'A'),-1)
        self.assertEqual(g.transition(self.anchor,self.peer,'C'),0)
    def test_strict_parser_no_gold_salvage(self):
        raw='{"decision_basis":"x","answer":"B"}'
        self.assertEqual(c.parse_answer(raw,self.task).answer,'B')
        self.assertEqual(c.parse_answer(raw,self.task,'length').status,'length')
        for raw in ('{"answer":"B","decision_basis":"x"}','{"decision_basis":"x","answer":"D"}','{"decision_basis":"x","answer":"A","answer":"B"}'):
            self.assertNotEqual(c.parse_answer(raw,self.task).status,'ok')

@unittest.skipUnless(importlib.util.find_spec("numpy"), "optional gate extra required")
class Numerical(unittest.TestCase):
    def test_gradient_reference_and_finite_difference(self):
        import numpy as np
        X=np.array([[1.,2.],[-1.,.3],[0.,1.]]);y=np.array([0,2,1]);w=np.array([.1,.3,.1]);theta=np.arange(9)*.03
        loss,grad=g.objective(theta,X,y,w)
        W=theta[:6].reshape(3,2);a=theta[6:]
        ref=.0005*sum(float(v*v) for v in W.ravel())
        import math
        for x,t,weight in zip(X,y,w):
            z=[sum(W[j,k]*x[k] for k in range(2))+a[j] for j in range(3)];ref+=weight*(math.log(sum(math.exp(v) for v in z))-z[t])
        self.assertAlmostEqual(loss,ref,12)
        for i in range(len(theta)):
            d=np.zeros_like(theta);d[i]=1e-6
            numeric=(g.objective(theta+d,X,y,w)[0]-g.objective(theta-d,X,y,w)[0])/2e-6
            self.assertAlmostEqual(grad[i],numeric,7)
    def example(self):
        task=c.PublicTask('x','',(('A','x'),('B','y')));a=c.Answer('A','x','ok','anchor');p=c.Answer('B','x','ok','peer','c0')
        base=c.features(a,[p],p);meta=c.features(a,[p],p,metadata=True)
        r={'candidate_id':'c0','answer':'B','raw':'peer','target':1,'full':base,'restricted':base,'metadata':meta,'enabled':{'full':True,'restricted':True}}
        return a,r
    def test_weighting_fit_transform_determinism(self):
        a,r=self.example();r2=copy.deepcopy(r);r2['target']=-1;r2['full']['rationale_length']=30;r2['restricted']['rationale_length']=30
        tasks=[{'group_id':'a','split':'fit','training_allowed':True,'views':{'clean':[r,r2],'argument_pressure':[r,r2],'claimed_verification':[r,r2]}},
               {'group_id':'b','split':'fit','training_allowed':True,'views':{'clean':[]}}]
        _,w,_=g.fit_rows(tasks,'full_augmented');self.assertAlmostEqual(sum(w),.5);self.assertEqual(w,[.125,.125,.0625,.0625,.0625,.0625])
        m=g.fit(tasks,'full_augmented');self.assertTrue(m['diagnostics']['converged']);self.assertLessEqual(m['diagnostics']['iterations'],500)
        self.assertEqual(m,g.fit(tasks,'full_augmented'));self.assertEqual(m,json.loads(json.dumps(m)))
        ix=m['feature_spec']['numeric'].index('rationale_length');self.assertAlmostEqual(m['mean'][ix],15.5)
        for split in ('threshold_tuning','source_development_holdout','transfer'):
            bad=copy.deepcopy(tasks);bad[0]['split']=split
            with self.assertRaises(ValueError):g.fit(bad,'full_clean')
    def test_no_support_and_single_class_keep(self):
        a,r=self.example()
        for target,status in [(0,'no_empirical_rescue_training_support'),(1,'single_class_fit')]:
            r['target']=target;m=g.fit([{'group_id':'a','split':'fit','training_allowed':True,'views':{'clean':[r]}}],'restricted_clean')
            self.assertEqual(m['diagnostics']['status'],status);self.assertEqual(g.decide(m,[r],a,0)['raw'],a.raw)
    def test_joint_max_strict_threshold_ties_metadata_disabled(self):
        a,r=self.example();m=g.fit([{'group_id':'a','split':'fit','training_allowed':True,'views':{'clean':[r]}}],'metadata_augmented')
        m['keep_only']=False;m['coefficients']=[[0.]*len(m['mean']) for _ in range(3)];m['intercept']=[-10.,-10.,10.];m['model_hash']=digest({k:v for k,v in m.items() if k!='model_hash'})
        r['enabled']={'full':False,'restricted':False};r2={**r,'candidate_id':'c2'}
        self.assertEqual(g.decide(m,[r2,r],a,0)['selected_id'],'c0')
        self.assertEqual(g.decide(m,[r],a,'KEEP_ONLY')['raw'],'anchor')
        with patch.object(g,'probability',return_value=[0,.5,.5]):
            self.assertEqual(g.decide(m,[r],a,.5)['action'],'KEEP');self.assertEqual(g.decide(m,[r],a,.35)['action'],'SWITCH')
    def test_tuning_whole_policy_keep_and_holdout_rejected(self):
        a,r=self.example();m=g.fit([{'group_id':'a','split':'fit','training_allowed':True,'views':{'clean':[r]}}],'metadata_augmented')
        tasks=[{'group_id':str(i),'split':'threshold_tuning','training_allowed':False,'anchor':asdict(a),'gold':'A','views':{'clean':[r],'argument_pressure':[r]},'missing_variants':1} for i in range(32)]
        out=g.tune(m,tasks);self.assertEqual(out['threshold'],'KEEP_ONLY');self.assertFalse(out['formal_risk_certificate'])
        tasks[0]['split']='source_development_holdout'
        with self.assertRaises(ValueError):g.tune(m,tasks)
    def test_numerical_failure_is_error(self):
        import numpy as np
        with self.assertRaises(ArithmeticError):g.optimize(np.array([[float('nan')]]),np.array([0]),np.array([1.]))
        with self.assertRaises(ValueError):g.optimize(np.zeros((1,1)),np.array([0]),np.array([1.]),501)

@unittest.skipUnless(importlib.util.find_spec("numpy"), "optional gate extra required")
class Roundtrip(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp=tempfile.TemporaryDirectory();cls.base=Path(cls.tmp.name);cls.root=cls.base/'run'
        with redirect_stdout(io.StringIO()):
            s.plan(cls.root,fixture_data())
            for split in c.SPLITS[:2]:
                x=s.Session(cls.root,execute=True,mock=True);s.collect_source(x,split);s.acquire(x,split);s.build_checks(x,split);x.finish()
            s.fit_gates(cls.root);s.tune_thresholds(cls.root);s.freeze_policies(cls.root)
            x=s.Session(cls.root,execute=True,mock=True);s.collect_source(x,c.SPLITS[2]);s.acquire(x,c.SPLITS[2]);s.evaluate(x,c.SPLITS[2]);x.finish()
    @classmethod
    def tearDownClass(cls):cls.tmp.cleanup()
    def clone(self):
        import shutil
        d=tempfile.TemporaryDirectory();self.addCleanup(d.cleanup);p=Path(d.name)/'run';shutil.copytree(self.root,p);return p
    def test_source_smoke_eight_included_and_resume(self):
        r=self.clone();p,intents,results,u=s.inspect(r);count=len(intents)
        x=s.Session(r,execute=True,mock=True)
        with redirect_stdout(io.StringIO()):s.collect_source(x,'fit',True);x.finish()
        self.assertEqual(x.new,0);self.assertEqual(x.reused,8);self.assertEqual(len(s.inspect(r)[1]),count)
    def test_full_cpu_fit_and_frozen_core(self):
        self.assertEqual(set(read_json(self.root/'fit_diagnostics.json')),set(c.ARMS))
        self.assertTrue(all(x['trained'] for x in read_json(self.root/'fit_diagnostics.json').values()))
        rows=read_json(self.root/'evaluation/source_development_holdout.json')['rows'];self.assertTrue(rows)
        self.assertTrue(any(r['switch'] for r in rows if r['method']=='restricted_augmented'))
        for r in rows:self.assertEqual(int(r['Y']),int(r['T'])+int(not r['T'] and r['Y'])-int(r['T'] and not r['Y']))
        from pact.selective.metrics import report
        summary=report(self.root)
        self.assertIn('restricted_augmented',summary['fit_support'])
        for value in summary['robust_pool'].values():self.assertEqual(set(value['fixed_prefixes']),{'1','2'})
        self.assertTrue(summary['common_clean_attack_comparisons'])
    def test_fit_does_not_open_tuning_or_dev_labels(self):
        real=s.read_json
        def reader(path):
            if Path(path).parent.name=='labels' and Path(path).stem!='fit':raise AssertionError('Leakage')
            return real(path)
        with patch.object(s,'read_json',side_effect=reader):s.fit_gates(self.root)
    def test_unchanged_paths_reused_and_only_three_calls(self):
        p,intents,_,_=s.inspect(self.root);roles=Counter(i['identity']['role'] for i in intents.values())
        self.assertEqual(roles['verify_full'],roles['verify_restricted']);self.assertEqual(roles['extract'],roles['verify_full'])
        self.assertEqual(roles['private']+roles['anchor'],4*len(p['records']))
        # Same extraction is reused by clean/augmented gates, not rerun per gate.
        before=len(intents);x=s.Session(self.root,mock=True);s.build_checks(x,'fit');self.assertEqual(len(s.inspect(self.root)[1]),before)
    def test_no_dev_before_freeze_and_unsafe_resume(self):
        r=self.clone();(r/'frozen_policy_receipt.json').unlink()
        with self.assertRaises(FileNotFoundError):s.frozen(r)
        state=read_json(r/'state.json');state['recovery_safe']=False;write_json(r/'state.json',state)
        with self.assertRaises(ValueError):s.Session(r,mock=True)
    def test_missing_result_not_fallback(self):
        r=self.clone();p=next((r/'calls/shards').glob('*.sha256'));p.unlink()
        with self.assertRaises(ValueError):s.Session(r,mock=True)
    def test_mutated_anchor_rejected(self):
        r=self.clone();rec=s.records(r,'fit')[0];path=s.source_file(r,rec['task']['task_id']);v=read_json(path);v['anchor']['raw']='mutated';write_json(path,v)
        with self.assertRaises(ValueError):s.source_bank(r,rec)
    def test_mutated_pool_rejected_before_victims(self):
        r=self.clone();path=s.pool_file(r,'fit');pool=read_json(path)
        row=next(x for x in pool['rows'] if x['accepted']);row['justification']='Changed outside the committed rewrite'
        pool['hash']=digest(pool['rows']);write_json(path,pool)
        session=s.Session(r,mock=True)
        with self.assertRaises(ValueError):s.build_checks(session,'fit')
        self.assertEqual(session.new,0)
    def test_attempt_split_is_bound_to_frozen_source(self):
        r=self.clone();path=next((r/'intents').glob('*.json'));value=read_json(path)
        value['split']='threshold_tuning' if value['split']=='fit' else 'fit';write_json(path,value)
        with self.assertRaisesRegex(ValueError,'task/split'):s.inspect(r)
    def test_compact_checkpoint_restore_and_latest_unsafe(self):
        r=self.clone();persistent=r.parent/'durable'
        with redirect_stdout(io.StringIO()):
            s.checkpoint(r,persistent);s.restore(persistent,r.parent/'restored',True)
        self.assertEqual(len(s.inspect(r)[1]),len(s.inspect(r.parent/'restored')[1]))
        state=read_json(r/'state.json');state['recovery_safe']=False;write_json(r/'state.json',state)
        with redirect_stdout(io.StringIO()):s.checkpoint(r,persistent)
        with self.assertRaisesRegex(ValueError,'Latest snapshot unsafe'):s.restore(persistent,r.parent/'blocked',True)
    def test_independent_six_calls_no_peers_final_pass(self):
        _,intents,_,_=s.inspect(self.root)
        for i in intents.values():
            if i['identity']['role'].startswith('independent_'):
                body=json.loads(i['request']['messages'][1]['content']);self.assertNotIn('peers',body);self.assertNotIn('candidates',body)
        rows=read_json(self.root/'baselines/source_development_holdout.json');self.assertTrue(all(len(r['independent_cycles'])==3 for r in rows))
    def test_export_restore_privacy_cli(self):
        r=self.clone()
        with redirect_stdout(io.StringIO()):out=s.export(r);main(['selective-correction','inspect','--run-dir',str(r),'--mock'])
        private=out['private'];target=r.parent/'restored';s.unpack(Path(private['path']),private['sha256'],target,True)
        self.assertEqual(len(s.inspect(target)[1]),len(s.inspect(r)[1]))
        with zipfile.ZipFile(out['sanitized']['path']) as z:
            text=''.join(z.read(n).decode() for n in z.namelist())
        for rec in s.load(r)['records']:self.assertNotIn(rec['task']['task_id'],text);self.assertNotIn(rec['task']['question'],text)
        self.assertNotIn('"coefficients"',text);self.assertNotIn('prompt_ids',text)
        with self.assertRaises(ValueError):s.unpack(Path(out['sanitized']['path']),out['sanitized']['sha256'],r.parent/'bad',True)
    def test_transfer_complete_parent_no_source_regeneration(self):
        from pact.studies import adjudication as parent
        from pact.studies.adjudication_data import import_all
        r=self.clone();p=r.parent/'parent'
        with redirect_stdout(io.StringIO()):
            import_all(p,{},True);parent.freeze(p)
            for stage in ('clean','acquire','attack'):
                for model in (('Q',) if stage=='acquire' else ('J8','J14')):
                    for dataset in ('mmlu-pro','musr'):parent.execute(p,None,stage,dataset,model,None,mock=True)
            bundle=parent.export(p,None)['private'];before=file_hash(Path(bundle['path']))
            s.import_transfer(r,Path(bundle['path']),bundle['sha256'],True)
            x=s.Session(r,execute=True,mock=True);s.evaluate(x,'transfer');x.finish()
            from pact.selective.metrics import report
            summary=report(r)
        for k,value in summary['robust_pool'].items():
            if k.startswith('transfer/'):self.assertEqual(set(value['fixed_prefixes']),{'1','2','4'})
        self.assertEqual(before,file_hash(Path(bundle['path'])))
        _,intents,_,_=s.inspect(r)
        self.assertFalse(any(i['identity']['role'] in ('private','anchor','rewrite') for i in intents.values() if i['split']=='transfer'))
        with self.assertRaises(ValueError):s.collect_source(x,'transfer')

from collections import Counter

class Boundaries(unittest.TestCase):
    def test_all_prior_selection_formats_and_label_inventory(self):
        from pact.selective.data import prior_selections,REPO
        rows=list(prior_selections(REPO/'experiments'));self.assertGreaterEqual(len(rows),240)
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);write_json(p/'a-selection.json',[{'task_id':'a'}]);write_json(p/'b-selection.json',{'selected':[{'task_id':'b'}]})
            self.assertEqual([r['task_id'] for r in prior_selections(p)],['a','b'])
            source=fixture_data();source['labels']['extra']={'answer':'A','split':'fit'}
            with self.assertRaisesRegex(ValueError,'Label inventory'):s.plan(p/'run',source)
    def test_exact_budget_arithmetic_and_exhaustion(self):
        self.assertEqual(160*(4+9+2+6),3360)
        self.assertEqual(64*(4+9+3+9+4+6),2240)
        self.assertEqual(230*9+369*3+599+230*6,5156)
        self.assertEqual(sum(s.LIMITS.values()),10756)
        self.assertEqual(10756*512,5507072)
        for split in c.SPLITS+('transfer',):
            key=s.bucket(split);s.check_budget({key:s.LIMITS[key]-1},split)
            with self.assertRaises(ValueError):s.check_budget({key:s.LIMITS[key]},split)
    def test_quotas_exclusion_and_locked_split(self):
        self.assertEqual(QUOTAS,{'fit':64,'threshold_tuning':16,'source_development_holdout':32})
        source=fixture_data();groups=[r['group_id'] for r in source['records']];self.assertEqual(len(groups),len(set(groups)))
        with tempfile.TemporaryDirectory() as d:
            bad=copy.deepcopy(source);bad['records'][0]['task']['split']='confirmation_locked'
            with self.assertRaises(ValueError):s.plan(Path(d)/'a',bad)
            bad=copy.deepcopy(source);bad['records'][0]['training_allowed']=False
            with self.assertRaises(ValueError):s.plan(Path(d)/'b',bad)
        from pact.schemas import task_from_dict,TaskLabel
        train=[(task_from_dict(r['task']),TaskLabel(r['task']['task_id'],source['labels'][r['task']['task_id']]['answer'])) for r in source['records']]
        vt=replace(train[0][0],task_id='val-only',source_id='v',split='validation',question='Completely distinct exercise',context='Another context')
        with self.assertRaisesRegex(ValueError,'Insufficient fresh'):
            allocate(train,[(vt,TaskLabel(vt.task_id,'A'))],{'task_ids':[t.task_id for t,l in train]},fixture=True)
    def test_fallback_parity_invalid_anchor(self):
        from pact.selective.metrics import fallback
        a=c.Answer('A','x','ok','original');bad={'answer':None,'status':'length','raw':'bad'}
        self.assertEqual(fallback(bad,a)['raw'],'original')
        invalid=replace(a,answer=None,status='abstention');self.assertIsNone(fallback(bad,invalid)['answer'])
    def test_cli_default_never_dispatches(self):
        with tempfile.TemporaryDirectory() as d,redirect_stdout(io.StringIO()):
            root=Path(d)/'run';s.plan(root,fixture_data())
            main(['selective-correction','--run-dir',str(root),'--mock'])
            self.assertFalse(list((root/'intents').glob('*')))
            with self.assertRaises(ValueError):main(['selective-correction','collect-source','--run-dir',str(root),'--split','fit','--mock'])
    def test_module_import_no_gpu_modules(self):
        import subprocess,sys,os
        env={**os.environ,'PYTHONPATH':str(Path(__file__).resolve().parents[1]/'src')}
        result=subprocess.run([sys.executable,'-c','import sys; import pact.selective.study; assert "torch" not in sys.modules; assert "transformers" not in sys.modules'],env=env,capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stderr)
    def test_malicious_archive_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'bad.zip'
            with zipfile.ZipFile(path,'w') as z:z.writestr('../escape.json','{}');z.writestr('review_checksums.json','{}')
            with self.assertRaises(ValueError):s.unpack(path,file_hash(path),Path(d)/'out',True)
    def test_model_isolation_and_stage_matching(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)/'run';p=s.plan(root,fixture_data());session=s.Session(root,mock=True);rec=s.records(root,'fit')[0]
            with self.assertRaises(ValueError):session.call(rec,'Q',c.source_prompt(c.PublicTask.from_task(rec['task'])),'anchor')
            model=s.MockBackend('R');bad=copy.deepcopy(model.identity);bad['adapters']=['unexpected'];bad['snapshot']=digest({k:v for k,v in bad.items() if k!='snapshot'})
            with self.assertRaises(ValueError):s.validate_identity(bad,'R',p)
    def test_no_sixth_fit_or_failed_fit_retry(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)/'run';s.plan(root,fixture_data());write_json(root/'fit-intents/full_clean.json',{'attempt':1})
            task={'group_id':'fiction','split':'fit','training_allowed':True,'views':{'clean':[]}}
            with patch.object(s,'audit_checks'),patch.object(s,'labeled_features',return_value=[task]):
                with self.assertRaisesRegex(ValueError,'Prior failed'):s.fit_gates(root)

@unittest.skipUnless(importlib.util.find_spec("numpy"), "optional gate extra required")
class EntryPoints(unittest.TestCase):
    def test_full_cli_core_and_notebook_defaults(self):
        with tempfile.TemporaryDirectory() as d,redirect_stdout(io.StringIO()):
            base=Path(d);root=base/'run';source=base/'source.json'
            def cli(stage,*args):main(['selective-correction',stage,'--run-dir',str(root),'--mock',*map(str,args)])
            cli('prepare-source','--source',source);cli('plan','--source',source)
            h=read_json(root/'state.json')['plan_hash'];inference=('--execute','--plan-hash',h)
            cli('collect-source','--split','fit','--smoke',*inference)
            self.assertEqual(len(s.inspect(root)[1]),8)
            for split in c.SPLITS[:2]:
                for stage in ('collect-source','acquire-rewrites','build-check-bank'):cli(stage,'--split',split,*inference)
            for stage in ('fit-gates','tune-thresholds','freeze-policies'):cli(stage)
            for stage in ('collect-source','acquire-rewrites'):cli(stage,'--split',c.SPLITS[2],*inference)
            cli('evaluate-core',*inference);cli('report');cli('export')
            self.assertEqual(read_json(root/'summary.json')['stages'][c.SPLITS[2]]['status'],'complete')
        path=Path(__file__).resolve().parents[1]/'notebooks/22_selective_correction_colab.ipynb';nb=read_json(path)
        code='\n'.join(''.join(x['source']) for x in nb['cells'] if x['cell_type']=='code')
        for flag in ('RUN_SOURCE_SMOKE','RUN_FIT_TUNING','RUN_CPU_FITS','RUN_CORE','RUN_TRANSFER'):self.assertIn(flag+' = False',code)
        for i,cell in enumerate(nb['cells']):
            if cell['cell_type']=='code':compile(''.join(cell['source']),f'cell-{i}','exec');self.assertEqual(cell['outputs'],[])
