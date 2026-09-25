"""Fictional CPU study; no pretrained downloads, GPQA or GPU work."""
import contextlib
import copy
import dataclasses as dc
import io
import json
import os
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from pact.util import digest,canonical,write_json,read_json,node_seed
from pact.schemas import TaskInput,TaskLabel,Option,CallRecord
from pact.training.specialization_plan import build_plan,budgets,SETTINGS
from pact.training.specialization_collect import runtime,collect,replay,immutable
from pact.training.assignment_contrast import contrast,ARMS,export_contrast
from pact.training.specialization_study import evaluate,report,export,offline_backend,validate_recovery,load_plan
from pact.training.specialization_train import examples_for,training_audit,schedule
from pact.training.receiver import CallBoundaryStop
from pact.training.assignment import solve_assignment,loss_coefficients


class Tokenizer:
    eos_token_id=0
    def encode(self,text,**kw):return [ord(c)+1 for c in text]
    def decode(self,ids,**kw):return ''.join(chr(i-1) for i in ids)


def fixture():
    tasks=[];labels={};entries=[]
    for family in ('arc_challenge','logiqa'):
        for i in range(32):
            tid=f'{family}:fiction-{i}'
            t=TaskInput(tid,family,'train',str(i),'0'*40,'a'*64,f'Fictional {family} object {i}?',
                (Option('A','yes','A'),Option('B','no','B')))
            tasks.append(t);labels[tid]=TaskLabel(tid,'A');entries.append({'task_id':tid,'group_id':digest(tid),'content_group':digest(['content',tid])})
    identity={'snapshot':digest('initial'),'template_hash':digest('template'),'precision':'float32','runtime_fingerprint':digest('runtime'),
              'tokenizer_revision':'0'*40,'effective_actor_tensor_hashes':['a','b','c']}
    params={kind:{'max_new_tokens':cap,'do_sample':sample,'temperature':.7,'top_p':.8,'top_k':20,'eos_token_id':0} for kind,cap,sample in [('packet',256,True),('final',64,False)]}
    return build_plan(tasks,labels,{'selected':entries},{'task_ids':[]},{'checkpoint':identity,'parameters':params}, {'fixture':True},synthetic=True)


class Backend:
    def __init__(self,plan,*,unsupported=False,identity=None):
        self.plan=plan;self.identity=identity or plan['frozen_arm']['checkpoint'];self.tokenizer=Tokenizer();self.calls=[];self.forwards=[]
        self.scorer=self;self.unsupported=unsupported;self.counter={}
    def count_tokens(self,text):return len(self.tokenizer.encode(text))
    def truncate(self,text,n):return text[:n]
    def assert_unchanged(self):pass
    def generate(self,r):
        payload=json.loads(r.messages[1].content)
        if r.phase=='private':
            # Four additional candidates alternate A/B after the one anchor.
            key=(r.task.task_id,r.actor,payload['advisory']['text']);n=self.counter.get(key,0);self.counter[key]=n+1
            answer=('A' if r.actor=='agent-0' else 'B') if n==0 else ('A' if n%2 else 'B')
        elif r.phase=='revision':answer=json.loads(payload['own_private']['text'])['answer']
        else:answer='A' if any(json.loads(p['text'])['answer']=='A' for p in payload['packets']) else 'B'
        if self.unsupported:answer='B'
        raw=canonical({'answer':answer} if r.phase=='final' else {'answer':answer,'justification':'Fiction.'})
        rendered=canonical([dc.asdict(m) for m in r.messages]);prompt=self.tokenizer.encode(rendered);completion=self.tokenizer.encode(raw)+[0]
        call=CallRecord(r.actor,r.phase,self.identity['snapshot'],r.seed,r.messages,rendered,digest(rendered),self.identity['template_hash'],
            canonical(self.plan['frozen_arm']['parameters']['final' if r.phase=='final' else 'packet']),len(prompt),len(completion),'eos',0.)
        self.last_generation={'raw':raw,'prompt_ids':prompt,'completion_ids':completion,'context_hash':digest(rendered)};self.calls.append(call)
        return raw,call
    def answer_score(self,agent,prompt,completion):return self.token_score(f'agent{agent}',prompt,self.tokenizer.encode(prompt),completion,self.tokenizer.encode(completion)+[0])
    def token_score(self,adapter,prompt,prompt_ids,completion,completion_ids):
        r={'adapter':adapter,'prompt_hash':digest(prompt),'prompt_ids':prompt_ids,'completion':completion,'completion_ids':completion_ids,
           'token_count':len(completion_ids),'sum_logp':-float(len(completion_ids)),'mean_nll':1.,'elapsed_seconds':0.}
        self.forwards.append(r);return r


def setup(root,plan):
    write_json(root/'plan.json',plan);write_json(root/'state.json',{'plan_hash':digest(plan),'recovery_safe':True})


class AssignmentTests(unittest.TestCase):
    def test_symmetry_row_constants_singletons_mask_and_perturbation(self):
        costs=[[1.,1.,1.],[2.,2.,2.],[None,1.,None],[None,None,None]]
        a=solve_assignment(costs);b=solve_assignment([[None if x is None else x+17*(j+1) for x in r] for j,r in enumerate(costs)])
        self.assertEqual(a['status'],'converged')
        for l,r in zip(a['weights'],b['weights']):
            for x,y in zip(l,r):self.assertAlmostEqual(x,y,places=6)
        self.assertEqual(a['weights'][2],[0.,1.,0.]);self.assertEqual(a['weights'][3],[0.,0.,0.])
        uniform=solve_assignment([[0.,0.,0.] for _ in range(8)])['weights']
        self.assertAlmostEqual(uniform[0][0],1/3)
        shifted=solve_assignment([[-1.,0.,0.],*[ [0.,0.,0.] for _ in range(7)]])['weights']
        self.assertGreater(shifted[0][0],uniform[0][0])
    def test_missing_scores_and_incompatible_provenance(self):
        rows=[{'row_id':str(j),'task_id':str(j),'split':'train','identity':{'snapshot':'a'},'initial_correct':[True,False,False],
            'cells':[{'eligible':True,'answer_nll':1.,'delta':1.,'positive_tokens':8} for _ in range(3)]} for j in range(8)]
        result=contrast(rows);self.assertLess(result['D_credit_local']['multi'],1e-6);self.assertEqual(result['status'],'no_assignment_contrast')
        rows[0]['cells'][0]['answer_nll']=None
        self.assertEqual(contrast(rows)['status'],'missing_answer_scores')
        rows[0]['identity']['snapshot']='changed'
        with self.assertRaises(ValueError):contrast(rows)
        rows[0]['identity']['snapshot']='a';rows[0]['split']='validation'
        with self.assertRaises(ValueError):contrast(rows)
    def test_budgets_and_fixed_exposure_selection(self):
        self.assertEqual(budgets()['total'],{'generation_calls_upper_bound':6336,'generated_tokens_upper_bound':1363968})
        self.assertEqual(budgets(5)['replay']['generation_calls_upper_bound'],80)
        self.assertEqual(budgets(5)['packet_scoring_forwards'],5)
        p=fixture();self.assertEqual(len(p['selection']),64)
        self.assertEqual(len({e['group_id'] for e in p['selection']}),64)


class StudyTests(unittest.TestCase):
    def test_full_mock_roundtrip_and_reconstruction(self):
        with tempfile.TemporaryDirectory() as temp,contextlib.redirect_stdout(io.StringIO()):
            root=Path(temp)/'run';plan=fixture();setup(root,plan);backend=Backend(plan)
            support=collect(plan,backend,root);self.assertEqual(support['eligible_cells'],192)
            self.assertLessEqual(len(backend.calls),1216)
            rows,records=replay(plan,backend,root);self.assertLessEqual(len(backend.calls),4288)
            self.assertEqual(len(backend.forwards),384)
            result=contrast(rows);self.assertEqual(result['status'],'ready');self.assertGreater(result['D_credit_local']['multi'],.1)
            export_contrast(rows,result,root)
            offline_rows,offline_records=replay(plan,offline_backend(plan),root,readonly=True)
            self.assertEqual(canonical(records),canonical(offline_records));self.assertEqual(rows,offline_rows)
            identities=[]
            for arm in ARMS:
                examples=examples_for(records,result,arm,backend.tokenizer)
                audit=training_audit(examples,plan['seed']);self.assertEqual(audit['base_forwards'],384);self.assertEqual(audit['packet_forwards'],384)
                self.assertEqual(len(schedule(examples,plan['seed'])),96)
                # Explicit mock optimizer: real neural train/resume tested separately.
                identity={**backend.identity,'snapshot':digest(arm)};identities.append(identity)
                write_json(root/'training'/arm/'status.json',{'complete':True,'completed_steps':96,'training_executed':False,'mock_updates':96})
                evaluate(plan,Backend(plan,identity=identity),root,arm)
            evaluate(plan,Backend(plan),root,'frozen')
            report1=report(root);self.assertLessEqual(report1['generation_accounting']['attempted_calls'],6336)
            self.assertTrue(all(n==0 for n in report1['missing_evaluation_rows'].values()))
            self.assertFalse(report1['training_executed']);self.assertTrue(report1['synthetic_fixture'])
            self.assertEqual(report1,report(root));bundle=export(root)
            from pact.training.feasibility import read_review
            content=read_review(Path(bundle['path']),bundle['sha256'],max_members=40000,max_bytes=512*1024**2,allow_text=True)
            self.assertEqual(content['specialization_results.json'],report1)
            from pact.training.specialization_study import audit_bundle
            self.assertEqual(audit_bundle(bundle['path'],bundle['sha256']),report1)
    def test_candidate_gate_pause_resume_and_changed_checkpoint(self):
        with tempfile.TemporaryDirectory() as temp,contextlib.redirect_stdout(io.StringIO()):
            root=Path(temp)/'run';plan=fixture();setup(root,plan);backend=Backend(plan,unsupported=True)
            with self.assertRaises(CallBoundaryStop):collect(plan,backend,root,stop_after=1)
            support=collect(plan,backend,root);self.assertLessEqual(len(backend.calls),1216)
            self.assertEqual(support['status'],'insufficient_assignment_support')
            with self.assertRaisesRegex(ValueError,'insufficient'):replay(plan,backend,root)
            self.assertFalse((root/'replay/call-intents').exists())
            with self.assertRaises(ValueError):collect(plan,Backend(plan,identity={**backend.identity,'snapshot':'changed'}),root,readonly=True)
    def test_restore_latest_safety_and_preserve_adapter_routing(self):
        from pact.artifacts import _sync_run
        from pact.training.colab import _restore_snapshot
        from pact.training.specialization_study import backend_for
        from pact.config import AdapterConfig
        with tempfile.TemporaryDirectory() as temp:
            base=Path(temp);root=base/'run';plan=fixture();setup(root,plan)
            snap=_sync_run(root,base/'durable')
            _restore_snapshot(snap,base/'restored',kind='specialization_fixed_bank')
            self.assertEqual(load_plan(base/'restored'),load_plan(root))
            write_json(root/'state.json',{'plan_hash':digest(plan),'recovery_safe':False})
            newer=_sync_run(root,base/'durable')
            with self.assertRaisesRegex(ValueError,'latest'):_restore_snapshot(snap,base/'old',kind='specialization_fixed_bank')
            with self.assertRaisesRegex(ValueError,'Unsafe'):_restore_snapshot(newer,base/'unsafe',kind='specialization_fixed_bank')
            rt=runtime(plan);rt=dc.replace(rt,model=dc.replace(rt.model,adapters=tuple(AdapterConfig(f'agent{i}',f'/fiction/{i}',str(i)*64) for i in range(3))))
            backend=SimpleNamespace(config=rt)
            with patch('pact.training.specialization_study.load_initial',return_value=(rt,backend,{})):
                actual,_=backend_for(plan,None,None,root)
                self.assertEqual(actual.config.model.adapters,rt.model.adapters)
                self.assertEqual(actual.config.probe.revision_candidates,0)

    def test_ambiguous_journal_and_changed_plan(self):
        with tempfile.TemporaryDirectory() as temp,contextlib.redirect_stdout(io.StringIO()):
            root=Path(temp)/'run';plan=fixture();setup(root,plan)
            backend=Backend(plan)
            with patch.object(backend,'generate',side_effect=RuntimeError('fixture failure')):
                with self.assertRaises(RuntimeError):collect(plan,backend,root)
            with self.assertRaisesRegex(ValueError,'Ambiguous'):validate_recovery(root,plan)
            with self.assertRaises(ValueError):load_plan(root,'wrong')


@unittest.skipUnless(os.environ.get('PACT_TINY_SPECIALIZATION')=='1','optional locally initialized torch test')
class TinyNeuralTests(unittest.TestCase):
    def test_global_gradient_accumulation_reference(self):
        import torch
        torch.set_num_threads(1)
        from pact.training.specialization_train import token_nll
        weights=[[.9,.1,0.],[0.,1.,0.],[0.,0.,0.],[.2,.3,.5]]
        coeff=loss_coefficients(weights,[[True,False,False],[False]*3,[True]*3,[False]*3])
        def model():
            m=torch.nn.Sequential(torch.nn.Embedding(5,4),torch.nn.Linear(4,5)).double()
            class Wrapper(torch.nn.Module):
                def __init__(self):super().__init__();self.net=m
                def forward(self,input_ids,**kw):return SimpleNamespace(logits=self.net(input_ids))
            return Wrapper()
        torch.manual_seed(2);a=model();b=copy.deepcopy(a)
        seq={'input_ids':[1,2,3],'attention_mask':[1,1,1],'completion_mask':[0,1,1]}
        # Independent explicit full-bank scalar; different actors represented by
        # independent copies with unequal total responsibility.
        for actor in range(3):
            a.zero_grad();b.zero_grad();total=0
            for row in range(4):
                loss=token_nll(a,seq)
                base=loss/12
                omega=coeff['omega'][row]
                spec=omega*weights[row][actor]*loss/3 if any(weights[row]) else 0
                total=total+base+spec
            total.backward()
            from pact.training.specialization_train import backward_rows
            examples=[{'row_id':str(row),'cells':[{'base':seq,'packet':seq if any(weights[row]) else None,
                'base_coefficient':coeff['base'][row][i],'packet_coefficient':coeff['specialization'][row][i]} for i in range(3)]} for row in range(4)]
            # Two production minibatches, U/batch=2; average their gradients.
            for indices in ([0,1],[2,3]):backward_rows(b,examples,{'indices':indices,'scale':2.},actor)
            for pa,pb in zip(a.parameters(),b.parameters()):torch.testing.assert_close(pa.grad,pb.grad/2,rtol=1e-10,atol=1e-10)
        self.assertNotEqual(sum(r[0] for r in coeff['specialization']),sum(r[1] for r in coeff['specialization']))

    def test_real_three_actor_updates_resume_and_isolation(self):
        import torch
        from pact.training.specialization_train import train_team
        from pact.training.warmstart import _weights_hash,adapter_parameters
        torch.set_num_threads(1)
        class Tiny(torch.nn.Module):
            def __init__(self):
                super().__init__();self.embedding=torch.nn.Embedding(5,5)
                self.layers=torch.nn.ModuleDict({'lora_A':torch.nn.ModuleDict({f'agent{i}':torch.nn.Linear(5,5,bias=False) for i in range(3)})})
                self.active_adapter='agent0'
                for p in self.parameters():p.requires_grad_(False)
            def set_adapter(self,name):self.active_adapter=name
            def forward(self,input_ids,**kw):
                x=self.embedding(input_ids);return SimpleNamespace(logits=x+self.layers['lora_A'][self.active_adapter](x))
        torch.manual_seed(1);initial=Tiny();plan=fixture()
        weights=[[.8,.2,0.] if j%2 else [0.,0.,0.] for j in range(64)]
        coefficients=loss_coefficients(weights,[[True,False,False]]*64)
        seq={'input_ids':[1,2,0],'attention_mask':[1,1,1],'completion_mask':[0,1,1]}
        examples=[{'row_id':str(j),'task_id':str(j//2),'cells':[{'base':seq,'packet':seq if j%2 else None,
                   'base_coefficient':coefficients['base'][j][i],'packet_coefficient':coefficients['specialization'][j][i]} for i in range(3)]} for j in range(64)]
        identity={'arm':ARMS[2],'fixture':True};frozen=initial.embedding.weight.detach().clone()
        with tempfile.TemporaryDirectory() as temp,contextlib.redirect_stdout(io.StringIO()),patch('pact.training.specialization_train.export_references',return_value={'fixture_only':True}):
            a=copy.deepcopy(initial);b=copy.deepcopy(initial);root=Path(temp)
            full=train_team(a,examples,plan,root/'full',identity)
            partial=train_team(b,examples,plan,root/'resume',identity,stop_after=35)
            self.assertEqual(partial['completed_steps'],35)
            # Restart from exactly the declared initial tensor values, not in-memory partial tensors.
            b=copy.deepcopy(initial)
            resumed=train_team(b,examples,plan,root/'resume',identity,resume=True)
            self.assertEqual(full['completed_steps'],96);self.assertEqual(full['final_weight_hash'],resumed['final_weight_hash'])
            torch.testing.assert_close(a.embedding.weight,frozen,rtol=0,atol=0)
            for i in range(3):self.assertNotEqual(_weights_hash(adapter_parameters(initial,f'agent{i}')),_weights_hash(adapter_parameters(a,f'agent{i}')))
            c=copy.deepcopy(initial);again=train_team(c,examples,plan,root/'resume',identity,resume=True)
            self.assertEqual(again,resumed)
            bad=copy.deepcopy(examples);bad[0]['cells'][0]['base_coefficient']*=2
            with self.assertRaises(ValueError):train_team(copy.deepcopy(initial),bad,plan,root/'resume',identity,resume=True)
