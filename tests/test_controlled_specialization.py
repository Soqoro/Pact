"""Fictional controlled-private study, no network, weights or GPU."""
import contextlib
import copy
import dataclasses as dc
import io
import json
from pathlib import Path
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from test_specialization import fixture, Backend, Tokenizer, setup
from pact.util import canonical,digest,read_json,write_json,node_seed
from pact.artifacts import ShardStore
from pact.training.specialization_collect import collect
from pact.training.specialization_study import export as parent_export, offline_backend, evaluate
from pact.training.specialization_train import training_audit,schedule
from pact.training.receiver import CallBoundaryStop
from pact.training.controlled_private_plan import (budgets,build_plan,characterize_parent,unpack_review,ARMS,SOURCE,ESTIMATOR,VARIANT)
from pact.training.controlled_private import (acquire,verified_pairs,build_bank,replay,score_bank,write_assignments,assignment,examples_for,BaseGenerator)
from pact.training.controlled_specialization import report,export,audit,validate_recovery,review_contract


class ParentBackend(Backend):
    def __init__(self,plan):
        super().__init__(plan)
        fit=[e for e in plan['selection'] if e['partition']=='fit']
        self.eligible={(fit[0]['task_id'],i) for i in range(3)}|{(fit[1]['task_id'],i) for i in (0,2)}
    def generate(self,r):
        # Existing natural fixture samples alternating valid options only in five
        # clean cells. All other candidate cells contain four valid wrong packets.
        if r.phase=='private':
            advisory=json.loads(r.messages[1].content)['advisory']['text']
            valid=(r.task.task_id,int(r.actor[-1])) in self.eligible and not advisory
            key=(r.task.task_id,r.actor,advisory)
            if self.counter.get(key,0)==0 or not valid:
                prior=self.unsupported;self.unsupported=True
                try:return super().generate(r)
                finally:self.unsupported=prior
        return super().generate(r)


class Donor(Backend):
    def __init__(self,plan,fail=False,retry=False):
        super().__init__(plan,identity={**plan['frozen_arm']['checkpoint'],'backend':'mock','adapters':[],'adapter_policy':'all_disabled'})
        self.fail=fail;self.retry=retry;self.seen={}
    def generate(self,r):
        target=json.loads(r.messages[1].content)['support_option'];key=(r.task.task_id,target)
        n=self.seen.get(key,0);self.seen[key]=n+1
        raw=canonical({'answer':target,'justification':'Fictional controlled evidence.'})
        if self.fail or self.retry and n==0:raw='{}'
        rendered=canonical([dc.asdict(m) for m in r.messages]);prompt=self.tokenizer.encode(rendered);out=self.tokenizer.encode(raw)+[0]
        from pact.schemas import CallRecord
        call=CallRecord('base',r.phase,self.identity['snapshot'],r.seed,r.messages,rendered,digest(rendered),self.identity['template_hash'],
            canonical(self.plan['frozen_arm']['parameters']['packet']),len(prompt),len(out),'eos',0.)
        self.last_generation={'raw':raw,'prompt_ids':prompt,'completion_ids':out,'context_hash':digest(rendered)};self.calls.append(call)
        return raw,call


class Continuation(Backend):
    def __init__(self,plan,*,symmetric=False,identity=None):super().__init__(plan,identity=identity);self.symmetric=symmetric
    def generate(self,r):
        if r.phase!='final':return super().generate(r)
        payload=json.loads(r.messages[1].content)
        if self.symmetric:answer='B'
        else:
            actor=node_seed(17,r.task.task_id,'fictional-relevant-position')%3
            packet=next(p for p in payload['packets'] if p['source']==f'peer-{actor+1}')
            answer=json.loads(packet['text'])['answer']
        # Reuse fixture call/token recorder with an exact one-packet view only inside
        # this software double, then restore original request provenance.
        from pact.schemas import CallRecord
        raw=canonical({'answer':answer});rendered=canonical([dc.asdict(m) for m in r.messages])
        prompt=self.tokenizer.encode(rendered);out=self.tokenizer.encode(raw)+[0]
        call=CallRecord(r.actor,r.phase,self.identity['snapshot'],r.seed,r.messages,rendered,digest(rendered),self.identity['template_hash'],
            canonical(self.plan['frozen_arm']['parameters']['final']),len(prompt),len(out),'eos',0.)
        self.last_generation={'raw':raw,'prompt_ids':prompt,'completion_ids':out,'context_hash':digest(rendered)};self.calls.append(call)
        return raw,call


class ControlledTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory();cls.base=Path(cls.temp.name);cls.parent=cls.base/'parent'
        cls.old=fixture();setup(cls.parent,cls.old)
        with contextlib.redirect_stdout(io.StringIO()):
            support=collect(cls.old,ParentBackend(cls.old),cls.parent)
            assert support['eligible_cells']==5,support
            cls.bundle=parent_export(cls.parent)
            imported=cls.base/'imported';unpack_review(cls.bundle['path'],cls.bundle['sha256'],imported)
            p,anchors,cal,missing=characterize_parent(imported,fixture=True)
        cls.missing=missing
        cls.plan=build_plan(p,anchors,cal,{'reviewed':True,'provenance':'fictional exposure audit',
            'development_used_for_optimization_or_outcome_selection':[]},{'fixture':True},parent_sha=cls.bundle['sha256'])
    @classmethod
    def tearDownClass(cls):cls.temp.cleanup()
    def child(self,root):
        setup(root,self.plan)
        write_json(root/'parent_import_receipt.json',{'plan_hash':self.plan['parent']['plan_hash'],
                   'anchor_hashes':[digest(a) for a in self.plan['anchors']]})
        write_json(root/'natural_candidate_missingness.json',self.missing)
        unpack_review(self.bundle['path'],self.bundle['sha256'],root/'parent_metadata')

    def test_budget_parent_missingness_and_split(self):
        self.assertEqual(budgets()['total'],{'generation_calls_upper_bound':6096,'generated_tokens_upper_bound':1274112})
        self.assertEqual(sum(budgets()[s]['generation_calls_upper_bound'] for s in ('acquire','primary','order','calibration')),4048)
        self.assertEqual(self.missing['selector_rejections']['eligible'],5)
        self.assertGreater(self.missing['candidate_categories']['valid_wrong'],0)
        self.assertEqual(len(self.plan['review_task_ids']),8)
        self.assertEqual(len(self.plan['order_task_ids']),8)
        for s in self.plan['donor_schedule']:self.assertNotEqual(s['targets']['positive']['option'],s['targets']['negative']['option'])
        with self.assertRaises(ValueError):build_plan(self.old,self.plan['anchors'],self.plan['natural_calibration'],{'reviewed':True}, {})
        from pact.training.assignment_contrast import reconstruct_record
        with self.assertRaisesRegex(ValueError,'controlled'):reconstruct_record({'source_variant':SOURCE}, {})

    def test_donor_pause_first_valid_caps_and_missing_support(self):
        with tempfile.TemporaryDirectory() as t,contextlib.redirect_stdout(io.StringIO()):
            root=Path(t);self.child(root);backend=Donor(self.plan,retry=True)
            with self.assertRaises(CallBoundaryStop):acquire(self.plan,backend,root,stop_after=1)
            result=acquire(self.plan,backend,root)
            self.assertEqual(result['attempted_calls'],128);self.assertEqual(len(backend.calls),128)
            verified_pairs(self.plan,root)
            self.assertEqual(acquire(self.plan,backend,root)['attempted_calls'],128);self.assertEqual(len(backend.calls),128)
            for pair in result['pairs'].values():
                p,n=pair['accepted']['positive'],pair['accepted']['negative']
                self.assertEqual(p['request']['messages'][0],n['request']['messages'][0])
                user=json.loads(p['request']['messages'][1]['content'])
                self.assertEqual(set(user),{'trusted_task','support_option'})
                self.assertEqual(p['attempt'],1)
        with tempfile.TemporaryDirectory() as t,contextlib.redirect_stdout(io.StringIO()):
            root=Path(t);self.child(root);acquire(self.plan,Donor(self.plan,fail=True),root)
            self.assertEqual(build_bank(self.plan,root)['status'],'insufficient_controlled_support')
            with self.assertRaisesRegex(ValueError,'insufficient'):replay(self.plan,Continuation(self.plan),root)
            self.assertFalse((root/'primary').exists())
            self.assertFalse(report(root)['evaluation_executed'])

    def test_full_mock_roundtrip_and_interventions(self):
        with tempfile.TemporaryDirectory() as t,contextlib.redirect_stdout(io.StringIO()):
            root=Path(t);self.child(root);frozen_hash=digest(self.plan['anchors'])
            donors=acquire(self.plan,Donor(self.plan),root);support=build_bank(self.plan,root)
            self.assertEqual(support['eligible_cells'],192)
            backend=Continuation(self.plan)
            with self.assertRaises(CallBoundaryStop):replay(self.plan,backend,root,stop_after=3)
            cells=replay(self.plan,backend,root)
            self.assertEqual(len(cells),192+48+5)
            self.assertEqual(digest(self.plan['anchors']),frozen_hash)
            self.assertEqual(canonical(cells),canonical(replay(self.plan,offline_backend(self.plan),root,readonly=True)))
            changed=offline_backend(self.plan,{**backend.identity,'snapshot':'different-checkpoint'})
            with self.assertRaises(ValueError):replay(self.plan,changed,root,readonly=True)
            primary=[c for c in cells if c['stage']=='primary'];rid=primary[0]['row_id']
            for tid in {c['task_id'] for c in primary}:
                self.assertEqual(len({c['pair_id'] for c in primary if c['task_id']==tid}),1)
            for c in [c for c in primary if c['row_id']==rid]:
                for sign in ('positive','negative'):
                    for k,b in enumerate(c['branches'][sign]):
                        self.assertEqual([x['seed'] for x in b['calls']],
                            [node_seed(c['seeds'][k],'revision',i) for i in range(3)]+[node_seed(c['seeds'][k],'final')])
                        self.assertEqual(c['seeds'],primary[0]['seeds'])
                        raw=donors['pairs'][c['task_id']]['accepted'][sign]['raw']
                        self.assertEqual(b['private'][c['agent']]['raw'],raw)
                        for rev in b['revised']:
                            data=json.loads(rev['call']['messages'][1]['content'])
                            views=[data['own_private'],*data['peers']]
                            self.assertEqual(next(p['text'] for p in views if p['source']==f'peer-{c["agent"]+1}'),raw)
                            self.assertNotIn('support_option',rev['call']['messages'][1]['content'])
            original={(c['row_id'],c['agent']):c for c in primary}
            for c in [c for c in cells if c['stage']=='order']:
                a=original[(c['row_id'],c['agent'])]
                for sign in ('positive','negative'):
                    for p,q in zip(a['branches'][sign],c['branches'][sign]):
                        self.assertEqual(p['private'],q['private']);self.assertEqual(p['attack'],q['attack'])
                        for x,y in zip(p['calls'],q['calls']):
                            self.assertEqual(x['seed'],y['seed'])
                            u=json.loads(x['messages'][1]['content']);v=json.loads(y['messages'][1]['content'])
                            key='packets' if x['phase']=='final' else 'peers'
                            self.assertEqual(u[key],list(reversed(v[key])))
            rows,records=score_bank(self.plan,backend,root,cells)
            self.assertEqual(len(backend.forwards),384)
            assignments=write_assignments(root,rows,records,cells)
            self.assertEqual(assignments['status'],'ready_for_user_review')
            self.assertEqual(canonical((rows,records)),canonical(score_bank(self.plan,offline_backend(self.plan),root,cells,readonly=True)))
            with self.assertRaises(ValueError):review_contract(root,self.plan,{})
            exposures=[]
            for arm in ARMS:
                examples=examples_for(records,assignments,arm,backend.tokenizer)
                exposure=training_audit(examples,self.plan['seed']);self.assertEqual(exposure['base_forwards'],384);self.assertEqual(exposure['packet_forwards'],384)
                exposures.append([[{k:v for k,v in cell.items() if not k.endswith('coefficient')} for cell in e['cells']] for e in examples])
                # Explicit CPU mock optimizer traverses the actual schedule. Real
                # production optimization is tested with tiny local neural tests.
                steps=list(schedule(examples,self.plan['seed']));self.assertEqual(len(steps),96)
                write_json(root/'training'/arm/'status.json',{'complete':True,'training_executed':False,'mock_updates':len(steps)})
                identity={**backend.identity,'snapshot':digest(arm)}
                evaluate(self.plan,Continuation(self.plan,identity=identity),root,arm,arms=ARMS)
            self.assertEqual(exposures[0],exposures[1]);self.assertEqual(exposures[0],exposures[2])
            evaluation=evaluate(self.plan,Continuation(self.plan),root,'frozen',arms=ARMS)
            for r in evaluation:
                for call in r['trajectory']['calls']:
                    self.assertNotIn('support_option',canonical(call['messages']))
                    self.assertNotIn('Fictional controlled evidence.',canonical(call['messages']))
            result=report(root);self.assertFalse(result['training_executed']);self.assertEqual(set(result['missing_evaluation_rows'].values()),{0})
            self.assertLessEqual(result['generation_accounting']['attempted_calls'],6096)
            bundle=export(root);self.assertEqual(canonical(audit(bundle['path'],bundle['sha256'])),canonical(result))
            validate_recovery(root,self.plan)

    def test_latest_restore_and_immutable_parent(self):
        from pact.artifacts import _sync_run
        from pact.training.colab import _restore_snapshot
        from pact.training.controlled_specialization import load_plan
        from pact.util import file_hash
        before=file_hash(Path(self.bundle['path']))
        with tempfile.TemporaryDirectory() as t:
            root=Path(t)/'run';self.child(root)
            snap=_sync_run(root,Path(t)/'durable')
            _restore_snapshot(snap,Path(t)/'restored',kind=VARIANT)
            self.assertEqual(load_plan(root),load_plan(Path(t)/'restored'))
            write_json(root/'state.json',{'plan_hash':digest(self.plan),'recovery_safe':False})
            newer=_sync_run(root,Path(t)/'durable')
            with self.assertRaisesRegex(ValueError,'latest'):_restore_snapshot(snap,Path(t)/'older',kind=VARIANT)
            with self.assertRaisesRegex(ValueError,'Unsafe'):_restore_snapshot(newer,Path(t)/'unsafe',kind=VARIANT)
        self.assertEqual(file_hash(Path(self.bundle['path'])),before)

    def test_identical_credit_and_practical_stop(self):
        rows=[{'row_id':str(b),'task_id':str(b//2),'condition':'clean' if b%2==0 else 'early','split':'train',
            'identity':{'snapshot':'fixture','source_variant':SOURCE,'estimator':ESTIMATOR},'initial_correct':[False]*3,'cells':[
                {'eligible':True,'answer_nll':1.,'delta':0.,'per_seed_differences':[0,0],'positive_tokens':10} for i in range(3)]} for b in range(64)]
        untyped=copy.deepcopy(rows);untyped[0]['identity'].pop('source_variant')
        with self.assertRaisesRegex(ValueError,'provenance'):assignment(untyped,[])
        result,*_=assignment(rows,[]);self.assertEqual(result['status'],'no_assignment_contrast')
        rows[0]['cells'][0].update(delta=.5,per_seed_differences=[1,0])
        result,*_=assignment(rows,[]);self.assertEqual(result['status'],'insufficient_practical_contrast')
        self.assertLess(result['practical_screen']['tasks_at_least_0_10'],8)


class GuardTests(unittest.TestCase):
    def test_base_generator_restores_state_even_on_exception(self):
        from test_adapters import FakeModel
        class Model(FakeModel):
            peft_config={'a':{}}
            training=True
            def modules(self):return [self]
        for fail in (False,True):
            model=Model()
            def generate(request):
                self.assertTrue(model.disabled)
                self.assertFalse(model.parameter.requires_grad)
                if fail:raise RuntimeError('fixture')
                return 'raw',SimpleNamespace()
            backend=SimpleNamespace(base_identity={'snapshot':'base'},tokenizer=None,model=model,generate=generate,last_generation={})
            generator=BaseGenerator(backend)
            request=SimpleNamespace(actor='base',phase='controlled_donor')
            if fail:
                with self.assertRaises(RuntimeError):generator.generate(request)
            else:
                # Only intercept CallRecord copying, leaving real isolation active.
                with patch('pact.training.controlled_private.dc.replace',return_value='base-call'):
                    self.assertEqual(generator.generate(request),('raw','base-call'))
            self.assertFalse(model.disabled);self.assertTrue(model.parameter.requires_grad)
            self.assertTrue(model.training);self.assertEqual(model.active_adapter,'distinct-a')

    def test_symmetric_continuation_and_fixture_notebook(self):
        from pact.schemas import task_from_dict,AttackRecord
        from pact.protocol import Protocol
        from pact.training.specialization_collect import runtime
        from pact.training.controlled_private import inserted_packet
        from pact.training.controlled_donors import donor_prompt
        root=Path(__file__).resolve().parents[1]
        example=read_json(root/'tests/fixtures/controlled_private_v1.json')
        task=task_from_dict(example['task'])
        for sign,target in (('positive','A'),('negative','B')):
            self.assertEqual(canonical(donor_prompt(task,target)),canonical(example['generator_requests'][sign]))
        self.assertEqual(example['branch_views']['positive']['node_seeds'],example['branch_views']['negative']['node_seeds'])
        p=fixture();backend=Continuation(p,symmetric=True);backend.unsupported=True
        protocol=Protocol(runtime(p),backend)
        attack=AttackRecord(**{k:v for k,v in p['attacks'][task.task_id]['clean'].items() if k!='schema_version'})
        private=tuple(protocol.private_packet(task,i,attack,node_seed(1,i)) for i in range(3))
        # Equal fixed receiver/readout policies: inserted option cannot induce a
        # systematic physical-actor advantage, regardless of branch order.
        deltas=[]
        for actor in range(3):
            success=[]
            for answer in ('A','B'):
                packet=dc.replace(private[actor],raw=canonical({'answer':answer,'justification':'Fiction.'}),answer_id=answer,parser_status='ok')
                clone=tuple(packet if i==actor else v for i,v in enumerate(private))
                success.append(sum(protocol.suffix(task,'debate',attack,clone,node_seed(1,'suffix',k),digest([actor,answer,k])).final.answer_id=='A' for k in range(2))/2)
            deltas.append(success[0]-success[1])
        self.assertEqual(deltas,[0.,0.,0.])
        notebook=read_json(root/'notebooks/08_controlled_private_specialization_colab.ipynb')
        for i,cell in enumerate(notebook['cells']):
            if cell['cell_type']=='code':
                compile(''.join(cell['source']),f'controlled-private-cell-{i}','exec')
                self.assertIsNone(cell['execution_count']);self.assertEqual(cell['outputs'],[])
        first=''.join(notebook['cells'][1]['source'])
        self.assertIn('STAGE = "plan"',first);self.assertIn('EXECUTE = False',first)

    def test_review_is_bound_and_defects_veto_training(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);plan={'review_task_ids':['fiction-'+str(i) for i in range(8)]}
            names=('assignment_contrast.json','pair_quality_and_review.json','order_sensitivity.json','seed_assignment_sensitivity.json')
            for name in names:write_json(root/name,{'status':'ready_for_user_review','fixture':name})
            review={'plan_hash':digest(plan),'artifact_hashes':{n:digest(read_json(root/n)) for n in names},
                'decision':'approve_training','systematic_packet_defect':False,'reviewer':'fictional tester',
                'notes':'Software test only; no real approval','reviewed_task_ids':plan['review_task_ids']}
            self.assertEqual(review_contract(root,plan,review),review)
            with self.assertRaises(ValueError):review_contract(root,plan,{**review,'systematic_packet_defect':True})
            write_json(root/'order_sensitivity.json',{'changed':True})
            with self.assertRaises(ValueError):review_contract(root,plan,review)

    def test_partial_export_does_not_certify_science(self):
        from pact.training.controlled_private_plan import RUN_ID
        p=fixture();p.update(variant=VARIANT,source_variant=SOURCE,estimator=ESTIMATOR,run_id=RUN_ID,
                            budget=budgets(),arms=list(ARMS),anchors=[],parent={'plan_hash':'fictional'})
        with tempfile.TemporaryDirectory() as t,contextlib.redirect_stdout(io.StringIO()):
            root=Path(t)/'run';setup(root,p)
            write_json(root/'parent_import_receipt.json',{'anchor_hashes':[],'plan_hash':'fictional'})
            with patch('pact.training.controlled_specialization.report',side_effect=ValueError('incomplete fixture')):
                bundle=export(root)
            result=audit(bundle['path'],bundle['sha256'])
            self.assertEqual(result['status'],'partial_requires_review')
            self.assertFalse(result['scientific_results_verified'])

    def test_initialization_and_evaluation_receipts_are_distinct(self):
        from pact.training.controlled_specialization import record_environment
        with tempfile.TemporaryDirectory() as t:
            root=Path(t)
            before=record_environment(root,'train',ARMS[0],{'snapshot':'initial'},{})
            after=record_environment(root,'evaluate',ARMS[0],{'snapshot':'trained'},{})
            self.assertNotEqual(before,after)
            self.assertEqual(read_json(before)['identity']['snapshot'],'initial')
            record_environment(root,'evaluate',ARMS[0],{'snapshot':'trained'},{})
            with self.assertRaises(ValueError):record_environment(root,'evaluate',ARMS[0],{'snapshot':'different'},{})

    def test_changed_frozen_snapshot_stops_before_work(self):
        plan={'source_variant':SOURCE,'estimator':ESTIMATOR,'frozen_arm':{'checkpoint':{'snapshot':'expected'}}}
        backend=SimpleNamespace(identity={'snapshot':'different'})
        with tempfile.TemporaryDirectory() as t:
            root=Path(t)
            with self.assertRaisesRegex(ValueError,'frozen parent'):replay(plan,backend,root)
            with self.assertRaisesRegex(ValueError,'Frozen parent'):score_bank(plan,backend,root,[])
            self.assertEqual(list(root.iterdir()),[])

    def test_hard_dispatch_cap_and_unknown_attempt(self):
        from pact.training.controlled_donors import DonorJournal,donor_prompt
        from pact.backends import Request
        from pact.schemas import task_from_dict
        old=fixture();backend=Donor(old);task=task_from_dict(next(iter(old['tasks'].values())))
        with tempfile.TemporaryDirectory() as t,contextlib.redirect_stdout(io.StringIO()):
            root=Path(t);journal=DonorJournal(backend,root,{'generation_calls_upper_bound':1,'generated_tokens_upper_bound':256})
            journal.begin_record('one');journal.generate(Request(task,donor_prompt(task,'A'),'base','controlled_donor',1,256,False))
            journal.begin_record('two')
            with self.assertRaisesRegex(ValueError,'budget'):journal.generate(Request(task,donor_prompt(task,'B'),'base','controlled_donor',2,256,False))
            self.assertEqual(len(backend.calls),1)
        with tempfile.TemporaryDirectory() as t,contextlib.redirect_stdout(io.StringIO()):
            root=Path(t);journal=DonorJournal(backend,root,budgets()['acquire']);journal.begin_record('failed')
            with patch.object(backend,'generate',side_effect=RuntimeError('fixture')):
                with self.assertRaises(RuntimeError):journal.generate(Request(task,donor_prompt(task,'A'),'base','controlled_donor',1,256,False))
            with self.assertRaisesRegex(ValueError,'Ambiguous'):DonorJournal(backend,root,budgets()['acquire'])

@unittest.skipUnless(__import__('os').environ.get('PACT_TINY_SPECIALIZATION')=='1', 'optional locally initialized neural test')
class ControlledTinyTests(unittest.TestCase):
    def test_unequal_length_full_packet_global_gradients(self):
        import torch
        from pact.training.specialization_train import token_nll,backward_rows
        from pact.training.assignment import loss_coefficients
        torch.set_num_threads(1)
        class Tiny(torch.nn.Module):
            def __init__(self):
                super().__init__();self.embedding=torch.nn.Embedding(7,4);self.head=torch.nn.Linear(4,7)
            def forward(self,input_ids,**kw):return SimpleNamespace(logits=self.head(self.embedding(input_ids)))
        torch.manual_seed(8);a=Tiny().double();b=copy.deepcopy(a)
        weights=[[.8,.2,0.],[0.,0.,0.],[.1,.3,.6],[0.,1.,0.]]
        initial=[[True,False,False],[False]*3,[True]*3,[False]*3]
        coefficients=loss_coefficients(weights,initial)
        def seq(ids,prompt):return {'input_ids':ids,'attention_mask':[1]*len(ids),'completion_mask':[0]*prompt+[1]*(len(ids)-prompt)}
        base=seq([1,2,3,0],2)
        packets=[seq([1,2,4,5,0],2),None,seq([1,2,4,6,5,4,0],2),seq([1,2,5,0],2)]
        examples=[{'row_id':str(j),'source_variant':SOURCE,'estimator':ESTIMATOR,'cells':[
            {'base':base,'packet':packets[j],'base_coefficient':coefficients['base'][j][i],
             'packet_coefficient':coefficients['specialization'][j][i]} for i in range(3)]} for j in range(4)]
        for actor in range(3):
            a.zero_grad();b.zero_grad();total=0
            # Independent formula: B=3, U=4, m=3, omega normalized only eligible rows.
            omega_raw=[1/(1+sum(initial[j])) for j in (0,2,3)];mean=sum(omega_raw)/3
            for j in range(4):
                total=total+token_nll(a,base)/12
                if packets[j] is not None:
                    omega=(1/(1+sum(initial[j])))/mean
                    total=total+omega*weights[j][actor]*token_nll(a,packets[j])/3
            total.backward()
            for indices in ([0,1],[2,3]):backward_rows(b,examples,{'indices':indices,'scale':2.},actor)
            for x,y in zip(a.parameters(),b.parameters()):torch.testing.assert_close(x.grad,y.grad/2,rtol=1e-10,atol=1e-10)


if __name__=='__main__':unittest.main()
