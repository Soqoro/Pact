"""Invented fixtures: no model/tokenizer downloads and no real study dispatch."""
import copy
from contextlib import redirect_stdout
from dataclasses import asdict, replace
import io
import json
import math
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile

from pact.cli import main
from pact.selective import contracts as c, gates as g, study as s
from pact.selective import diagnostics as d, selector_contract as q, closed_parent as cp
from pact.util import digest, read_json, write_json, file_hash
import test_selective_correction as fixtures


class Numerics(unittest.TestCase):
    def model(self):
        a,r=fixtures.Numerical().example()
        # Construct a saved, hashed fixture model without running an optimizer.
        size=len(g.encode(r['metadata'],True))
        m={'arm':'metadata_augmented','class_order':['harm','neutral','improve'],'feature_spec':c.feature_spec(True),
           'mean':[0.]*size,'scale':[1.]*size,'coefficients':[[0.]*size for _ in range(3)],'intercept':[0.,0.,0.],'keep_only':False}
        m['model_hash']=digest(m)
        return a,r,m
    def test_saved_score_class_order_stability_and_cost(self):
        a,r,m=self.model()
        for logits in ([1000,1000,1002],[-1000,-998,-1000],[0,1000,1],[0,0,math.log(2)]):
            m['intercept']=logits;m['model_hash']=digest({k:v for k,v in m.items() if k!='model_hash'})
            x=d.scores(m,r['metadata']);self.assertAlmostEqual(sum(x['probabilities']),1)
            if not x['numeric_boundary']:self.assertEqual(x['u2']>0,x['log_odds_IH']>math.log(2))
        m['class_order']=['improve','neutral','harm'];m['model_hash']=digest({k:v for k,v in m.items() if k!='model_hash'})
        with self.assertRaisesRegex(ValueError,'Class order'):d.scores(m,r['metadata'])
    def test_negative_location_informative_rank_vs_constant(self):
        rank=d.rank_metrics([-.9,-.8,-.2,-.1],[False,False,True,True],[.25]*4,list('abcd'))
        constant=d.rank_metrics([-.2]*4,[False,False,True,True],[.25]*4,list('abcd'))
        self.assertEqual(rank['roc_auc'],1);self.assertEqual(constant['roc_auc'],.5)
        self.assertEqual(constant['average_precision'],.5)
    def test_undefined_rank_and_group_unit(self):
        self.assertIsNone(d.rank_metrics([1],[True],[1],['a'])['roc_auc'])
        self.assertIsNone(d.rank_metrics([1,2],[True,False],[1,1],['a','a'])['roc_auc'])
        self.assertIsNone(d.clustered_interval([]))
        with self.assertRaises(ValueError):d.clustered_interval([('f','a',1),('f','a',0)])
        with self.assertRaises(ValueError):d.clustered_interval([],2001)
    def test_weights_no_alternatives_reused_views(self):
        a,r,m=self.model();tasks=[{'group_id':'a','split':'fit','training_allowed':True,'views':{'clean':[r],'attack1':[r],'attack2':[r]}},
                                 {'group_id':'b','split':'fit','training_allowed':True,'views':{'clean':[]}}]
        wr=d.weighted_rows(tasks,'metadata_augmented');self.assertEqual([v[3] for v in wr],[.25,.125,.125])
        self.assertEqual([v[3] for v in wr],g.fit_rows(tasks,'metadata_augmented')[1])
    def test_improve_harm_same_anchor_rejected(self):
        a,r,m=self.model()
        with self.assertRaises(ValueError):d.weighted_rows([{'views':{'clean':[r,{**r,'target':-1}]}}],'full_clean')
    def test_sensitivity_dev_forbidden_and_not_a_policy(self):
        a,r,m=self.model()
        with self.assertRaises(ValueError):d.sensitivity(m,[{'split':c.SPLITS[2]}],{})
        with self.assertRaises((ValueError,KeyError)):g.decide({'diagnostic_only':True,'policy_selection_authorized':False},[],a,0)
        with self.assertRaises(ValueError):g.decide(m,[],a,-.1)
    def test_mask_metadata_stable_tie_and_keep(self):
        a,r,m=self.model();r['enabled']={'full':False,'restricted':False};m['intercept']=[-2,0,2];m['model_hash']=digest({k:v for k,v in m.items() if k!='model_hash'})
        cache={digest(r['metadata']):d.scores(m,r['metadata'])}
        r2={**r,'candidate_id':'c2'}
        self.assertEqual(d.select(m,[r2,r],asdict(a),2,0,cache)['candidate_id'],'c0')
        self.assertIsNone(d.select(m,[r],asdict(a),2,'KEEP_ONLY',cache))


class Contracts(unittest.TestCase):
    def setUp(self):
        self.task=c.PublicTask('INVENTED <script>alert(1)</script>','',(('A','one'),('B','two')))
        self.a=c.Answer('A','basis','ok','raw anchor');self.peers=[c.Answer('B','PEER TEXT','ok','peer','c0')]
        self.view={'task':{'question':self.task.question,'options':[{'answer_id':k,'text':v} for k,v in self.task.options],'context':''},'anchor':asdict(self.a),'peers':[asdict(x) for x in self.peers],
                   'allowed':q.allowed(self.a,self.peers),'gold':'B','target':'c0','task_id':'fictional','group_id':'fictional','dataset':'logiqa','view':'clean','view_id':'v',
                   'historical':asdict(c.Answer(None,'','malformed','old extra key'))}
    def score(self,raw,stop='eos'):
        return q.score_view(self.view,{'raw':raw,'call':{'stop_reason':stop}})
    def test_prompt_only_diff_public_allowed_order(self):
        old=q.render(self.task,self.a,self.peers,q.ARMS[0]);new=q.render(self.task,self.a,self.peers,q.ARMS[1])
        self.assertEqual(old,c.selection_prompt(self.task,self.a,self.peers));self.assertEqual(old[1:],new[1:])
        self.assertEqual(old[0].content.replace(q.OLD,''),new[0].content.replace(q.V2.format(choices='["anchor","c0","ABSTAIN"]'),''))
        self.assertIn('"anchor" is a possible VALUE',new[0].content)
        for token in ('gold','group_id','target'):self.assertNotIn(token,new[1].content)
    def test_extra_key_never_salvaged_and_fallback_separate(self):
        raw='{"decision_basis":"x","candidate_id":"c0","anchor":"A"}'
        value=self.score(raw);self.assertFalse(value['strict_valid']);self.assertTrue(value['fallback']);self.assertFalse(value['Y'])
        good=self.score('{"decision_basis":"x","candidate_id":"c0"}')
        self.assertTrue(good['strict_correct']);self.assertTrue(good['rescue']);self.assertTrue(good['Y'])
    def test_anchor_choice_vs_failure_and_abstain(self):
        v=self.score('{"decision_basis":"x","candidate_id":"anchor"}')
        self.assertTrue(v['intentional_anchor']);self.assertFalse(v['fallback'])
        v=self.score('{"decision_basis":"x","candidate_id":"ABSTAIN"}')
        self.assertTrue(v['fallback']);self.assertEqual(v['schema'],'ok')
        self.assertIsNone(q.score_view(self.view,None))
    def test_duplicate_unknown_unavailable_anchor(self):
        for raw in ('{"decision_basis":"x","candidate_id":"c0","candidate_id":"anchor"}',
                    '{"decision_basis":"x","candidate_id":"c1"}'):
            self.assertFalse(self.score(raw)['strict_valid'])
        a=replace(self.a,status='malformed',answer=None);self.view['anchor']=asdict(a);self.view['allowed']=q.allowed(a,self.peers)
        self.assertNotIn('anchor',self.view['allowed']);self.assertFalse(self.score('{"decision_basis":"x","candidate_id":"anchor"}')['Y'])
        with self.assertRaises(ValueError):q.allowed(a,[*self.peers,*self.peers])
    def test_exact_identity_and_no_adapters(self):
        m=s.MockBackend('R').identity
        for key,value in [('precision','float32'),('adapters',['x']),('template_hash','changed')]:
            with self.assertRaises(ValueError):q.same_model(m,{**m,key:value})
    def test_module_import_no_model_stack(self):
        r=subprocess.run([sys.executable,'-c','import sys; import pact.selective.diagnostics; import pact.selective.selector_contract; assert "torch" not in sys.modules; assert "transformers" not in sys.modules'],capture_output=True,text=True)
        self.assertEqual(r.returncode,0,r.stderr)


class Roundtrip(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        fixtures.Roundtrip.setUpClass();cls.tmp=tempfile.TemporaryDirectory();cls.base=Path(cls.tmp.name)
        with redirect_stdout(io.StringIO()):
            bundle=s.export(fixtures.Roundtrip.root)['private']
            cls.root=cls.base/'child';cp.import_parent(cls.root,Path(bundle['path']),bundle['sha256'],True)
            with patch.object(g,'fit',side_effect=AssertionError('No new fitting')),patch.object(g,'optimize',side_effect=AssertionError('No optimization')),patch.object(s.MockBackend,'generate',side_effect=AssertionError('Offline generation')):
                cls.analysis=d.analyze(cls.root,True)
            cls.plan=q.plan(cls.root,True)
    @classmethod
    def tearDownClass(cls):cls.tmp.cleanup();fixtures.Roundtrip.tearDownClass()
    def clone(self):
        temp=tempfile.TemporaryDirectory();self.addCleanup(temp.cleanup);root=Path(temp.name)/'child';shutil.copytree(self.root,root);return root
    def test_complete_offline_original_parity_and_artifacts(self):
        self.assertEqual(self.analysis['new_fits'],0)
        for name in ('score_reconstruction.json','weighted_class_support.json','checker_transition_tables.json','feature_collision_summary.json',
                     'original_tuning_reconstruction.json','fit_tuning_sensitivity.json','opportunity_dossier.private.html','diagnostic_decision_review.md'):
            self.assertTrue((self.root/name).is_file(),name)
        grid=read_json(self.root/'fit_tuning_sensitivity.json');self.assertFalse(grid['policy_selection_authorized']);self.assertEqual(len(grid['results']),10)
        self.assertTrue(all(len(x['grid'])==52 for x in grid['results'].values()))
        self.assertNotIn(c.SPLITS[2],canonical_keys(grid['results']))
        cp.verified_parent(self.root,True)
    def test_fixture_full_entrypoints_resume_export_import(self):
        root=self.clone();h=self.plan['plan_hash']
        def cli(stage,*args):main(['selector-contract',stage,'--run-dir',str(root),'--mock',*args])
        with redirect_stdout(io.StringIO()):
            with self.assertRaises(ValueError):cli('smoke','--plan-hash',h)
            with self.assertRaises(ValueError):cli('run','--execute','--plan-hash',h)
            cli('smoke','--execute','--plan-hash',h)
            count=len(q.inspect(root)[1]);self.assertLessEqual(count,16);self.assertGreater(count,0)
            cli('smoke','--execute','--plan-hash',h);self.assertEqual(len(q.inspect(root)[1]),count)
            cli('run','--execute','--plan-hash',h);cli('report');cli('export')
            result=q.report(root);self.assertTrue(result['complete']);self.assertEqual(result['resources']['attempted'],q.load(root)['expected_calls'])
            out=q.export(root);target=root.parent/'restored';q.unpack(Path(out['private']['path']),out['private']['sha256'],target,True)
            self.assertEqual(q.report(target),result)
            self.assertEqual(q.execute(root,'run',h,mock=True)['new_calls'],0)
            with zipfile.ZipFile(out['sanitized']['path']) as z:public=''.join(z.read(n).decode() for n in z.namelist())
            for v in q.load(root)['views']:
                self.assertNotIn(v['task_id'],public);self.assertNotIn(v['task']['question'],public)
            self.assertNotIn('prompt_ids',public)
    def test_unknown_dispatch_blocks_no_reset(self):
        root=self.clone();p=q.load(root);row=p['requests'][0];key=q.request_key(p,row)
        write_json(root/'intents'/f'{key}.json',{'key':key,'plan_hash':digest(p),'row':row})
        self.assertEqual(len(q.inspect(root)[3]),1)
        with self.assertRaisesRegex(ValueError,'Unsafe'):q.execute(root,'smoke',digest(p),mock=True)
        self.assertIsNone(q.score_view(p['views'][0],None))
    def test_pairing_fresh_cache_and_exact_budget(self):
        p=q.load(self.root);group=defaultdict(list)
        for r in p['requests']:group[r['view_id']].append(r)
        _,parent_intents,_,_=s.inspect(self.root/'parent')
        for rs in group.values():
            self.assertEqual(rs[0]['request']['seed'],rs[1]['request']['seed'])
            self.assertNotEqual(q.request_key(p,rs[0]),q.request_key(p,rs[1]))
            self.assertNotIn(q.request_key(p,rs[0]),parent_intents)
        self.assertEqual(p['budgets'],{'calls':404,'reserved_output_tokens':206848,'smoke_calls':16,'smoke_tokens':8192})
        self.assertEqual(202*2*512,206848)
        with self.assertRaises(ValueError):q.plan(self.root,True)
    def test_missing_changed_parent_precise_stop(self):
        root=self.clone();(root/'parent/gates/full_clean.json').unlink()
        with self.assertRaisesRegex(ValueError,'missing_parent_evidence'):cp.validate(root/'parent',True)
        with self.assertRaisesRegex(ValueError,'changed'):cp.verified_parent(root,True)
    def test_unsafe_latest_snapshot_and_restore(self):
        root=self.clone();persistent=root.parent/'drive'
        with redirect_stdout(io.StringIO()):
            q.checkpoint(root,persistent);q.restore(persistent,root.parent/'restored',True)
            write_json(root/'state.json',{'plan_hash':self.plan['plan_hash'],'recovery_safe':False});q.checkpoint(root,persistent)
        with self.assertRaisesRegex(ValueError,'Latest snapshot unsafe'):q.restore(persistent,root.parent/'blocked',True)
    def test_broken_v2_is_valid_negative_result(self):
        root=self.clone();original=s.MockBackend.generate
        def broken(backend,req):
            raw,call=original(backend,req)
            if 'possible VALUE' in req.messages[0].content:
                raw='{"decision_basis":"x","candidate_id":"anchor","anchor":"A"}';backend.last_generation['raw']=raw
            return raw,call
        with patch.object(s.MockBackend,'generate',broken),redirect_stdout(io.StringIO()):
            q.execute(root,'smoke',self.plan['plan_hash'],mock=True);q.export(root)
            q.execute(root,'run',self.plan['plan_hash'],mock=True)
            report=q.report(root)
        v=[x for k,x in report['summary'].items() if q.ARMS[1] in k and k.endswith('/all')]
        self.assertTrue(all(x['strict_valid']==0 and x['fallback']==x['scored'] for x in v))
    def test_html_escape_and_private_export(self):
        with patch.object(d,'canonical',return_value='<script>alert(1)</script>'):
            root=self.clone();parent=root/'parent'
            with cp.cached_reads():
                p,t,m,th=cp.validate(parent,True,False);rs={r['task']['task_id']:r for r in p['records']}
                cache={a:{digest(r[d.layout(model)]):d.scores(model,r[d.layout(model)]) for ts in t.values() for task in ts for rows in task['views'].values() for r in rows} for a,model in m.items()}
                d.dossier(root,parent,t,rs,m,th,cache)
            text=(root/'opportunity_dossier.private.html').read_text();self.assertNotIn('<script>',text);self.assertIn('&lt;script&gt;',text)
        out=d.export(self.root)
        with zipfile.ZipFile(out['sanitized']['path']) as z:text=''.join(z.read(n).decode() for n in z.namelist())
        self.assertNotIn('prompt_ids',text)
        for rec in s.load(self.root/'parent')['records']:self.assertNotIn(rec['task']['task_id'],text)

from collections import defaultdict

def canonical_keys(obj):return json.dumps(list(obj))

class NotebookAndDesign(unittest.TestCase):
    def test_thin_notebook_defaults_and_syntax(self):
        repo=Path(__file__).resolve().parents[1]
        nb=read_json(repo/'notebooks/23_gate_diagnostics_selector_colab.ipynb')
        code='\n'.join(''.join(c['source']) for c in nb['cells'] if c['cell_type']=='code')
        for flag in ('RUN_PREFLIGHT','RUN_SMOKE','RUN_REMAINDER'):self.assertIn(flag+' = False',code)
        for i,cell in enumerate(nb['cells']):
            if cell['cell_type']=='code':compile(''.join(cell['source']),f'cell-{i}','exec');self.assertEqual(cell['outputs'],[])
    def test_fixed_budgets_and_design_checker(self):
        repo=Path(__file__).resolve().parents[1]
        result=subprocess.run([sys.executable,str(repo/'tools/verify_gate_diagnostics_design.py')],capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stderr)

class AdditionalBoundaries(unittest.TestCase):
    def test_no_support_saved_models_and_offline_cli(self):
        from pact.selective.data import fixture_data
        source=fixture_data()
        for label in source['labels'].values():label['answer']='A'
        with tempfile.TemporaryDirectory() as directory, redirect_stdout(io.StringIO()):
            base=Path(directory);parent=base/'parent'
            s.plan(parent,source)
            for split in c.SPLITS[:2]:
                session=s.Session(parent,execute=True,mock=True)
                s.collect_source(session,split);s.acquire(session,split);s.build_checks(session,split);session.finish()
            s.fit_gates(parent);s.tune_thresholds(parent);s.freeze_policies(parent)
            session=s.Session(parent,execute=True,mock=True);s.collect_source(session,c.SPLITS[2]);s.acquire(session,c.SPLITS[2]);s.evaluate(session,c.SPLITS[2]);session.finish()
            bundle=s.export(parent)['private'];root=base/'diagnostic'
            main(['gate-diagnostics','import-parent','--run-dir',str(root),'--bundle',bundle['path'],'--sha256',bundle['sha256'],'--mock'])
            with patch.object(g,'optimize',side_effect=AssertionError('Forbidden refit')):
                main(['gate-diagnostics','analyze','--run-dir',str(root),'--mock'])
            models=read_json(root/'score_reconstruction.json');self.assertTrue(all(x['not_trained'] for x in models.values()))
            support=read_json(root/'weighted_class_support.json');self.assertTrue(all(1 in x['zero_prior_classes'] for x in support.values()))
            signals=read_json(root/'candidate_signal_summary.json');self.assertTrue(all(x['rank']['improve_vs_nonimprove']['u2']['roc_auc'] is None for x in signals.values()))
    def test_bad_archive_no_execution(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);archive=root/'bad.zip'
            with zipfile.ZipFile(archive,'w') as z:z.writestr('../escape','malicious');z.writestr('review_checksums.json','{}')
            with self.assertRaises(ValueError):cp.import_parent(root/'out',archive,file_hash(archive),True)
            self.assertFalse((root/'escape').exists())
