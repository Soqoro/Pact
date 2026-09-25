"""Invented questions only. No gated access, pretrained downloads or local CUDA."""
import contextlib
import copy
import dataclasses as dc
import hashlib
import io
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from pact.studies import gpqa_data as data, gpqa_study as study
from pact.studies.gpqa_metrics import support,summarize
from pact.studies.gpqa_model import check_loaded
from pact.training.receiver import CallBoundaryStop
from pact.training.collection_config import CollectionRuntime
from pact.training.colab import _restore_snapshot
from pact.artifacts import _sync_run,ShardStore
from pact.util import canonical,digest,write_json,read_json
from pact.schemas import task_from_dict
from pact.backends import Request
from pact.protocol import private_prompt
from test_receiver import FixtureBackend
from test_receiver_supervision import CharacterTokenizer


def rows():
    return [{'Question':f'Fictional machine {i}: choose its invented symbol Ω.',
             'Correct Answer':f'symbol {i} red','Incorrect Answer 1':f'symbol {i} blue',
             'Incorrect Answer 2':f'symbol {i} green','Incorrect Answer 3':f'symbol {i} yellow',
             'High-level domain':data.DOMAINS[i%3],'Explanation':'PRIVATE_EXPLANATION_SENTINEL',
             'Question before revision':'DO_NOT_USE_OLD_QUESTION'} for i in range(198)]


class Backend(FixtureBackend):
    def __init__(self,runtime):
        super().__init__(runtime,SimpleNamespace(reference_hashes=('a','b','c'),runtime_fingerprint='fixture',base_snapshot='base'))
        self.tokenizer=CharacterTokenizer()
    def generate(self,request):
        raw,call=super().generate(request)
        params=json.loads(call.parameters_json);params['eos_token_id']=0
        call=dc.replace(call,parameters_json=canonical(params));self.calls[-1]=call
        return raw,call


def fixture():
    selected,manifest=data.partition(rows(),'a'*64)
    prepared={'selected':[{'task':dc.asdict(t),'label':dc.asdict(l),'private_metadata':m} for t,l,m in selected],
        'receipt':{'revision':data.REVISION},'manifest':manifest,'schema_version':1}
    runtime=CollectionRuntime('fixture',data.SEED);backend=Backend(runtime)
    contract={'checkpoint':{**backend.identity,'effective_actor_tensor_hashes':['a','b','c'],'recovery_receipt_hash':'r'},
        'parameters':{k:{'max_new_tokens':cap,'do_sample':sample,'temperature':.7,'top_p':.8,'top_k':20,'eos_token_id':0}
            for k,cap,sample in [('packet',256,True),('final',64,False)]}}
    backend.identity=contract['checkpoint']
    plan=json.loads(canonical(study.freeze_plan(prepared,contract,{'fixture':True})))
    return plan,runtime,backend


def initialize(root,plan):
    write_json(root/'plan.json',plan);write_json(root/'state.json',{'plan_hash':digest(plan),'recovery_safe':True})


class GPQADataTests(unittest.TestCase):
    def test_official_shape_stable_mapping_and_prompt_isolation(self):
        source=rows();normalized=[data.normalize(r,'a'*64) for r in source]
        self.assertGreater(len({l.answer_id for t,l,m in normalized}),1)
        for row,(t,l,m) in zip(source,normalized):
            self.assertEqual(next(o.text for o in t.options if o.answer_id==l.answer_id),row['Correct Answer'])
            self.assertEqual(m['source_to_canonical']['Correct Answer'],l.answer_id)
            prompt=canonical(private_prompt(t,''))
            for secret in ('PRIVATE_EXPLANATION_SENTINEL','DO_NOT_USE_OLD_QUESTION','Correct Answer','High-level domain'):
                self.assertNotIn(secret,prompt)
            self.assertIn('Ω',t.question)
        self.assertEqual(data.normalize(source[0],'a'*64),normalized[0])
        for key,value in [('Correct Answer',''),('High-level domain','invented'),('Incorrect Answer 1',source[0]['Correct Answer'])]:
            bad={**source[0],key:value}
            with self.assertRaises(ValueError):data.normalize(bad,'a'*64)

    def test_stratification_order_invariance_and_group_isolation(self):
        a,ma=data.partition(rows(),'a'*64);b,mb=data.partition(list(reversed(rows())),'a'*64)
        self.assertEqual(ma,mb);self.assertEqual(a,b)
        self.assertEqual(ma['selected_domain_counts'],{'Biology':11,'Chemistry':11,'Physics':10})
        known={'groups':[[a[0][0].task_id,ma['protected_ids'][0]]], 'exposed_content_hashes':[],'exposed_group_hashes':[]}
        # Cross-domain groups must stop rather than infer a domain.
        if a[0][2]['domain']!=dict((t.task_id,m['domain']) for t,l,m in [data.normalize(r,'a'*64) for r in rows()])[ma['protected_ids'][0]]:
            with self.assertRaises(ValueError):data.partition(rows(),'a'*64,known=known)
        known={'exposed_content_hashes':[a[0][2]['content_hash']],'groups':[]}
        _,m=data.partition(rows(),'a'*64,known=known)
        self.assertIn(a[0][0].task_id,m['excluded_ids'])
        self.assertNotIn(a[0][0].task_id,m['protected_ids'])
        with self.assertRaises(ValueError):data.partition(rows()[:-1],'a'*64)
        task=a[0][0]
        for split in ('train','test','validation'):
            with self.assertRaises(ValueError):data.require_development(dc.replace(task,split=split))

    def test_access_pinning_and_no_secret_exception(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(RuntimeError,'dataset_access_required'):data.acquire(tmp)
            fake=SimpleNamespace(hf_hub_download=lambda *a,**kw:(_ for _ in ()).throw(RuntimeError('SECRET_TOKEN')))
            with patch.dict('sys.modules',{'huggingface_hub':fake}):
                with self.assertRaises(RuntimeError) as ctx:data.acquire(tmp,download=True,token='SECRET_TOKEN')
                self.assertNotIn('SECRET_TOKEN',str(ctx.exception))
            raw=b'fictional only';p=Path(tmp)/'fiction.csv';p.write_bytes(raw)
            blob=hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()
            with patch.object(data,'FILES',{'fiction.csv':(blob,len(raw))}):
                self.assertEqual(data.verified_source(tmp)['fiction.csv'],hashlib.sha256(raw).hexdigest())
                p.write_bytes(raw+b'x')
                with self.assertRaises(ValueError):data.verified_source(tmp)
        with self.assertRaisesRegex(ValueError,'outside'):data.outside_git(Path(__file__).parent)


class GPQARunnerTests(unittest.TestCase):
    def test_full_roundtrip_smoke_private_resume_and_public_privacy(self):
        plan,runtime,backend=fixture()
        with tempfile.TemporaryDirectory() as tmp,contextlib.redirect_stdout(io.StringIO()):
            root=Path(tmp)/study.RUN_ID;initialize(root,plan)
            study.collect(plan,root,backend,runtime,'complete',smoke=True)
            self.assertEqual(len(backend.calls),16)
            self.assertEqual(len({c.seed for c in backend.calls[:8]}),8)
            smoke=dict(study.journals(root,plan)[1])
            study.collect(plan,root,backend,runtime,'private')
            self.assertEqual(len(backend.calls),106)
            study.collect(plan,root,backend,runtime,'complete')
            self.assertEqual(len(backend.calls),256)
            for k,v in smoke.items():self.assertEqual(study.journals(root,plan)[1][k],v)
            study.collect(plan,root,backend,runtime,'complete')
            self.assertEqual(len(backend.calls),256)
            result=study.report(root)
            self.assertEqual(result['completed_tasks'],32)
            self.assertEqual(result['accounting']['reserved_output_tokens'],53248)
            self.assertEqual(result['accounting']['teacher_forced_forwards'],0)
            self.assertEqual(result['communication']['decomposition']['success_lhs'],result['communication']['decomposition']['success_rhs'])
            self.assertEqual(result['communication']['decomposition']['availability_lhs'],result['communication']['decomposition']['availability_rhs'])
            for record in ShardStore(root/'complete').records():
                self.assertEqual(record['synthesis']['private'],record['debate']['private'])
                for p in record['debate']['revised']:
                    msg=json.loads(p['call']['messages'][1]['content'])
                    self.assertEqual(msg['own_private']['text'],record['debate']['private'][p['agent']]['raw'])
                    expected={x['raw'] for x in record['debate']['private'] if x['agent']!=p['agent']}
                    self.assertEqual({x['text'] for x in msg['peers']},expected)
            # Real local persistence worker and both archive views.
            output=study.export(root,Path(tmp)/'durable')
            public=study.read_bundle(output['sanitized']['path'],output['sanitized']['sha256'])
            private=study.read_bundle(output['private']['path'],output['private']['sha256'],private=True)
            serialized=canonical(public)
            for secret in ('Fictional machine','symbol 0 red','PRIVATE_EXPLANATION_SENTINEL','prompt_ids','completion_ids','rendered_prompt','"justification":'):
                self.assertNotIn(secret,serialized)
            self.assertIn('plan.json',private)
            self.assertEqual(study.audit_private_bundle(output['private']['path'],output['private']['sha256']),result)
            with self.assertRaises(ValueError):study.read_bundle(output['private']['path'],output['private']['sha256'])
            restored=Path(tmp)/'restored'
            _restore_snapshot(Path(output['snapshot']),restored,kind='gpqa_support')
            self.assertEqual(study.report(restored),result)
            bad=copy.deepcopy(plan);bad['budget']['generation_calls_upper_bound']=257
            write_json(restored/'plan.json',bad)
            with self.assertRaises(ValueError):study.load_plan(restored)

    def test_boundary_pause_ambiguous_attempt_and_missingness(self):
        plan,runtime,backend=fixture()
        with tempfile.TemporaryDirectory() as tmp,contextlib.redirect_stdout(io.StringIO()):
            root=Path(tmp)/study.RUN_ID;initialize(root,plan)
            with self.assertRaises(CallBoundaryStop):study.collect(plan,root,backend,runtime,'complete',stop_after=5)
            partial=study.report(root)
            self.assertEqual(partial['completed_tasks'],0)
            self.assertEqual(partial['missing_tasks'],32)
            self.assertEqual(partial['support']['completed_private_tasks'],1)
            study.collect(plan,root,backend,runtime,'complete',smoke=True)
            self.assertEqual(len(backend.calls),16)
            backend.mode='crash'
            with self.assertRaises(RuntimeError):study.collect(plan,root,backend,runtime,'private')
            self.assertEqual(study.report(root)['accounting']['unresolved_attempts'],1)
            with self.assertRaisesRegex(ValueError,'Ambiguous'):study.collect(plan,root,backend,runtime,'complete')

    def test_stage_protected_task_caps_sampling_and_identity(self):
        plan,runtime,backend=fixture()
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);initialize(root,plan);journal=study.GPQAJournal(backend,root,plan)
            task=task_from_dict(plan['dataset']['selected'][0]['task']);journal.begin_record(digest(task.task_id))
            request=Request(task,private_prompt(task,''),'agent-0','private',study.request_seed(task.task_id,0),256,False)
            for req in [dc.replace(request,max_tokens=257),dc.replace(request,phase='revision'),dc.replace(request,seed=request.seed+1),dc.replace(request,actor='agent-1'),dc.replace(request,task=dc.replace(task,task_id='protected'))]:
                with self.assertRaises(ValueError):journal.generate(req)
            with self.assertRaises(ValueError):study.collect(plan,root,backend,runtime,'train')
            with self.assertRaises(ValueError):study.collect(plan,root,backend,runtime,'private',smoke=True)
            backend.identity={**backend.identity,'snapshot':'changed'}
            with self.assertRaisesRegex(ValueError,'snapshot'):study.collect(plan,root,backend,runtime,'complete')

    def test_preflight_context_and_exact_global_reservation(self):
        plan,runtime,backend=fixture()
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);initialize(root,plan)
            with patch.object(backend,'count_tokens',return_value=5000):
                with self.assertRaisesRegex(ValueError,'overflow'):study.collect(plan,root,backend,runtime,'complete',smoke=True)
            self.assertEqual(len(backend.calls),0)
            journal=study.GPQAJournal(backend,root,plan)
            journal.intents={str(i):{'max_tokens':256} for i in range(208)} # exactly53248 reserved
            task=task_from_dict(plan['dataset']['selected'][0]['task']);journal.begin_record(digest(task.task_id))
            with self.assertRaisesRegex(ValueError,'budget exhausted'):journal.generate(Request(task,private_prompt(task,''),'agent-0','private',study.request_seed(task.task_id,0),256,False))
            self.assertEqual(len(backend.calls),0)

    def test_effective_identity_mismatch_stops(self):
        plan,_,backend=fixture();contract=plan['frozen_arm']
        with patch('pact.studies.gpqa_model.verify_loaded'):
            contract['recovery_receipt']={}
            contract['checkpoint']['revision']='expected'
            backend.identity={**backend.identity,'revision':'wrong'}
            with self.assertRaisesRegex(ValueError,'revision'):check_loaded(backend,contract)


class GPQAMetricTests(unittest.TestCase):
    def test_wrong_diversity_abstention_support_and_boundary(self):
        def row(k,answers,valid,c):return {'task_id':k,'answers0':answers,'valid0':valid,'c0':c,'parser0':['ok' if v else 'abstention' for v in valid]}
        rows_=[row('a',['A',None,None],[True,False,False],[True,False,False]),
               row('b',['B','C','D'],[True]*3,[False]*3),
               row('c',['A','B',None],[True,True,False],[True,False,False])]
        s=support(rows_)
        self.assertEqual(s['mixed_support']['numerator'],1)
        self.assertEqual(s['all_wrong_diverse']['numerator'],1)
        self.assertEqual(s['coverage']['numerator'],2)
        self.assertEqual(s['opportunities']['repair']['agent_contexts'],1)
        self.assertEqual(s['opportunities']['hold']['agent0_contexts'],1)
        r=summarize([],[],{'unresolved_attempts':0})
        self.assertIsNone(r['communication']['terminal_success']['value'])
        self.assertEqual(r['missing_tasks'],32)
        self.assertEqual(r['screen_flag'],'qualified_incomplete_or_invalid')

class GPQABoundaryTests(unittest.TestCase):
    def test_same_domain_known_groups_never_straddle(self):
        src=rows();_,m=data.partition(src,'a'*64)
        allrows={t.task_id:(t,l,meta) for t,l,meta in [data.normalize(r,'a'*64) for r in src]}
        a=m['selected_ids'][0]
        b=next(k for k in m['protected_ids'] if allrows[k][2]['domain']==allrows[a][2]['domain'])
        _,grouped=data.partition(src,'a'*64,known={'groups':[[a,b]]})
        self.assertEqual(grouped['group_by_id'][a],grouped['group_by_id'][b])
        for k in (a,b):
            if k in grouped['selected_ids']:
                self.assertNotIn(a,grouped['protected_ids']);self.assertNotIn(b,grouped['protected_ids'])

    def test_training_block_and_effective_readout_isolation(self):
        from pact.training.warmstart import prepare_examples
        from pact.backends.transformers import inference_adapter
        task,label,_=data.normalize(rows()[0],'a'*64)
        with self.assertRaisesRegex(ValueError,'forbidden'):prepare_examples(None,[task],{task.task_id:label},None)
        # The existing inference context must disable all adapters for readout,
        # restore previous selection on exceptions, and leave inference frozen.
        class Parameter:
            requires_grad=True
            def requires_grad_(self,x):self.requires_grad=x
        class Model:
            active_adapter='agent2';disabled=False;training=True
            def __init__(self):self.p=Parameter()
            def parameters(self):return [self.p]
            def eval(self):self.training=False
            def set_adapter(self,x):self.active_adapter=x;self.p.requires_grad=True
            @contextlib.contextmanager
            def disable_adapter(self):
                self.disabled=True
                try:yield
                finally:self.disabled=False
        m=Model()
        with self.assertRaises(RuntimeError):
            with inference_adapter(m,None,True):
                self.assertTrue(m.disabled);self.assertFalse(m.training);self.assertFalse(m.p.requires_grad)
                raise RuntimeError('fixture')
        self.assertEqual(m.active_adapter,'agent2');self.assertFalse(m.disabled);self.assertFalse(m.p.requires_grad)
        self.assertFalse(m.training)

    def test_failed_restore_cannot_roll_back_or_accept_unsafe(self):
        plan,_,_=fixture()
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)/'run';initialize(root,plan);durable=Path(tmp)/'durable'
            first=_sync_run(root,durable)
            write_json(root/'state.json',{'plan_hash':digest(plan),'recovery_safe':False})
            second=_sync_run(root,durable)
            with self.assertRaisesRegex(ValueError,'latest'):_restore_snapshot(first,Path(tmp)/'out',kind='gpqa_support')
            with self.assertRaisesRegex(ValueError,'Unsafe'):_restore_snapshot(second,Path(tmp)/'out',kind='gpqa_support')
            self.assertFalse((Path(tmp)/'out').exists())

    def test_errors_stay_private_and_rate_boundaries_explicit(self):
        from pact.studies.gpqa_metrics import boundary
        value=boundary({'rate':{'numerator':0,'denominator':32,'value':0.}})
        self.assertTrue(value['rate']['boundary_uncertainty'])
        plan,_,_=fixture()
        with tempfile.TemporaryDirectory() as tmp,contextlib.redirect_stdout(io.StringIO()) as stream:
            root=Path(tmp)/study.RUN_ID;initialize(root,plan)
            study.save_failure(root,RuntimeError('SECRET_TOKEN RAW_QUESTION completion_ids'))
            text=stream.getvalue()
            self.assertNotIn('SECRET_TOKEN',text)
            for p in (root/'errors').glob('*.json'):
                self.assertNotIn('SECRET_TOKEN',p.read_text());self.assertNotIn('RAW_QUESTION',p.read_text())

    def test_call_count_budget_and_corrupt_stage_rejected(self):
        plan,runtime,backend=fixture()
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);initialize(root,plan);journal=study.GPQAJournal(backend,root,plan)
            task=task_from_dict(plan['dataset']['selected'][0]['task']);journal.begin_record(digest(task.task_id))
            journal.intents={str(i):{'max_tokens':64} for i in range(256)}
            with self.assertRaisesRegex(ValueError,'budget exhausted'):journal.generate(Request(task,private_prompt(task,''),'agent-0','private',study.request_seed(task.task_id,0),256,False))
            key=digest([digest(task.task_id),0]);write_json(root/'call-intents'/f'{key}.json',
                {'work_id':key,'schema_version':1,'slot':0,'record_id':digest(task.task_id),'max_tokens':64})
            with self.assertRaisesRegex(ValueError,'stage'):study.journals(root,plan)

class GPQAPreparationTests(unittest.TestCase):
    def test_real_csv_parser_and_selection_only_retention(self):
        import csv
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);src=rows()
            with (root/'gpqa_diamond.csv').open('w',newline='') as f:
                writer=csv.DictWriter(f,fieldnames=list(src[0]));writer.writeheader();writer.writerows(src)
            (root/'README.md').write_text('Fictional notice')
            (root/'license.txt').write_text('Fictional license')
            pins={}
            for name in ('gpqa_diamond.csv','README.md','license.txt'):
                raw=(root/name).read_bytes();pins[name]=(hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest(),len(raw))
            with patch.object(data,'FILES',pins):
                out=root/'prepared.json';data.prepare(root,out)
                prepared=read_json(out)
                self.assertEqual(len(prepared['selected']),32)
                self.assertEqual(len(prepared['manifest']['protected_ids']),166)
                self.assertNotIn('PRIVATE_EXPLANATION_SENTINEL',out.read_text())
                protected=prepared['manifest']['protected_ids'][0]
                question=next(data.normalize(r,'a'*64)[0].question for r in src if data.normalize(r,'a'*64)[0].task_id==protected)
                self.assertNotIn(question,out.read_text())
                data.prepare(root,out)
                with self.assertRaisesRegex(ValueError,'changed'):
                    data.prepare(root,out,known={'exposed_content_hashes':[prepared['selected'][0]['private_metadata']['content_hash']]})

    def test_notebook_thin_unexecuted_and_default_gpu_off(self):
        notebook=read_json(Path(__file__).resolve().parents[1]/'notebooks/06_gpqa_support_colab.ipynb')
        code=''
        for c in notebook['cells']:
            if c['cell_type']=='code':
                source=''.join(c['source']);compile(source,'colab','exec');code+=source
                self.assertIsNone(c['execution_count']);self.assertEqual(c['outputs'],[])
        self.assertIn('RUN_GPU = False',code)
        self.assertIn('"--smoke"',code)
        self.assertNotIn('trust_remote_code',code)
        self.assertNotIn('"train"',code)
