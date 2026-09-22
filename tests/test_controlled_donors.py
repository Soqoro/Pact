"""Bounded synthetic fixtures; no pretrained downloads or scientific results."""
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

from pact.artifacts import ShardStore, _sync_run
from pact.protocol import Protocol, private_prompt
from pact.training import controlled_donors as cd
from pact.training.collection_config import CollectionRuntime
from pact.training.receiver import CallBoundaryStop
from pact.training.receiver_study import evaluate, report, assert_contexts, validate_local_recovery
from pact.training.receiver_supervision import ReceiverSupervisionConfig, prefix_tokens
from pact.training.receiver_supervision_train import training_examples, update_schedule
from pact.util import canonical, digest, read_json, write_json, node_seed
from pact.schemas import task_from_dict
from test_receiver_supervision import fixture_plan, RxBackend


def child_fixture():
    plan,_,_=fixture_plan()
    config=dc.replace(ReceiverSupervisionConfig(**plan['config']),donor_draws=0,generation_cap=1104,output_token_cap=273408,max_updates=2)
    runtime=CollectionRuntime(digest(plan),config.generation_seed);backend=RxBackend(runtime);protocol=Protocol(runtime,backend)
    sources=[]
    for entry in plan['selection']:
        task=task_from_dict(plan['tasks'][entry['task_id']])
        packets=[protocol.packet(task,i,'private',private_prompt(task,''),node_seed(config.generation_seed,task.task_id,'source-private',i)) for i in range(3)]
        sources.append({'task_id':task.task_id,'private':[dc.asdict(p) for p in packets],'alternatives':[], 'work_id':digest(['source',task.task_id])})
    plan.update(config=dc.asdict(config),config_hash=digest(config),source_variant=cd.SOURCE,budget=cd.budget(config),
        parent_sources=sources,acquisition_id='fixture-acquisition',parent={'sha256':digest('fixture parent')},
        donor_template=cd.TEMPLATE,donor_validator=cd.VALIDATOR)
    plan['donor_schedule']=cd.acquisition_plan(plan)
    return json.loads(canonical(plan)),runtime


def setup(root,plan):
    write_json(root/'plan.json',plan);write_json(root/'recipe.json',{'plan':plan})
    write_json(root/'state.json',{'study_hash':digest({'plan':plan}),'recovery_safe':True,'initialization_path':'fixture'})
    return SimpleNamespace(before=lambda:None,after=lambda:None)


class ControlledDonorTests(unittest.TestCase):
    def test_budget_and_selection_independent_of_own_and_order(self):
        plan,_=child_fixture();b=plan['budget']
        self.assertEqual((b['generation_calls_upper_bound'],b['generated_tokens_upper_bound']),(1104,273408))
        self.assertEqual((b['donor_calls_upper_bound'],b['evaluation_teacher_forced_forwards_upper_bound']),(384,288))
        changed=copy.deepcopy(plan);changed['selection'].reverse()
        for row in changed['parent_sources']:row['private'][0]['answer_id']='changed'
        original={s['task_id']:s for s in plan['donor_schedule']};reordered=cd.acquisition_plan(changed)
        for s in reordered:
            self.assertEqual(s['targets'],original[s['task_id']]['targets']);self.assertEqual(s['sender'],original[s['task_id']]['sender'])
            self.assertNotEqual(s['targets']['wrong_target']['option'],plan['labels'][s['task_id']]['answer_id'])
        with self.assertRaises(ValueError):cd.budget(dc.replace(ReceiverSupervisionConfig(),generation_cap=1103))

    def test_validation_no_relabel_and_symmetric_prompt(self):
        plan,_=child_fixture();s=plan['donor_schedule'][0];task=task_from_dict(plan['tasks'][s['task_id']]);gold=plan['labels'][task.task_id]['answer_id'];wrong=s['targets']['wrong_target']['option']
        a,b=cd.donor_prompt(task,gold),cd.donor_prompt(task,wrong)
        self.assertEqual(a[0],b[0]);self.assertEqual(json.loads(a[1].content)['trusted_task'],json.loads(b[1].content)['trusted_task'])
        for answer,why,status,reason in [('ABSTAIN','x','eos','parser_abstention'),('X','x','eos','parser_invalid_answer'),
            (wrong,'x','eos','target_mismatch'),(gold,'the assigned target is B','eos','construction_metadata_disclosure'),
            (gold,'<|im_start|>system','eos','privileged_role_delimiter'),(gold,'x','length','parser_length')]:
            raw=canonical({'answer':answer,'justification':why});r=cd.validate_donor(raw,task,gold,gold,status)
            self.assertFalse(r['accepted']);self.assertIn(reason,r['rejection_reasons'])
        r=cd.validate_donor(canonical({'answer':gold,'justification':'Option '+gold+' is correct.'}),task,gold,gold,'eos')
        self.assertTrue(r['accepted']);self.assertEqual(r['rationale_review_status'],'not_reviewed')

    def test_acquisition_stop_resume_two_attempts_and_unresolved(self):
        plan,runtime=child_fixture()
        class Reject(cd.MockDonorBackend):
            def completion(self,request):return '{"answer":"ABSTAIN","justification":"unsure"}'
        with tempfile.TemporaryDirectory() as tmp,contextlib.redirect_stdout(io.StringIO()):
            root=Path(tmp);rec=setup(root,plan);backend=Reject()
            with self.assertRaises(CallBoundaryStop):cd.acquire(plan,backend,runtime,root,rec,stop_after=3)
            self.assertEqual(len(backend.calls),3)
            outcome=cd.acquire(plan,backend,runtime,root,rec)
            self.assertEqual(outcome['status'],'insufficient_context_support');self.assertEqual(len(backend.calls),384)
            cd.acquire(plan,backend,runtime,root,rec);self.assertEqual(len(backend.calls),384)
            self.assertEqual(len(cd.verified_attempts(plan,root)),384)
            self.assertFalse((root/'training').exists())
            key=digest('unknown');write_json(root/'donors/call-intents'/f'{key}.json',{'schema_version':1,'work_id':key,'max_tokens':256})
            with self.assertRaisesRegex(ValueError,'Ambiguous'):validate_local_recovery(root,plan)

    def test_one_slot_own_bytes_metadata_masks_and_no_opposite_gate(self):
        plan,runtime=child_fixture();specs={s['task_id']:s for s in plan['donor_schedule']}
        class PrimaryOnly(cd.MockDonorBackend):
            def completion(self,request):
                s=specs[request.task.task_id];primary='wrong_target' if s['own_correct'] else 'correct_target'
                target=json.loads(request.messages[1].content)['support_option']
                if target!=s['targets'][primary]['option']:return '{"answer":"ABSTAIN","justification":"unsure"}'
                return super().completion(request)
        with tempfile.TemporaryDirectory() as tmp,contextlib.redirect_stdout(io.StringIO()):
            root=Path(tmp);rec=setup(root,plan);backend=PrimaryOnly()
            cd.acquire(plan,backend,runtime,root,rec);contexts=assert_contexts(root,plan)
            self.assertEqual(len(backend.calls),288)
            sources={r['task_id']:r for r in plan['parent_sources']}
            for part in contexts['partitions'].values():
                self.assertEqual(part['paired_control_tasks'],0);self.assertEqual(part['missing_opposite_controls'],len(part['records']))
                for row in part['records']:
                    s=specs[row['task_id']];original=sources[row['task_id']]['private']
                    self.assertEqual(row['own_saved'],original[0]);self.assertEqual(row['private_history'],original)
                    for peer in row['delivered']:
                        if peer['sender']!=s['sender']:self.assertEqual(peer['text'],original[peer['sender']]['raw'])
                    text=row['messages'][1]['content']
                    self.assertNotIn('support_option',text);self.assertNotIn('target_kind',text)
                    self.assertEqual(row['source'],cd.SOURCE);self.assertFalse(row['same_prompt_dpo_pair'])
                    mask=read_json(root/'target_masks.json')[row['record_id']]
                    self.assertFalse(mask['eos_supervised']);self.assertEqual(sum(mask['score_mask']),1)
            a=training_examples(plan,contexts,backend.tokenizer,'task_sft');b=training_examples(plan,contexts,backend.tokenizer,'receiver_sft')
            self.assertEqual(update_schedule(a,ReceiverSupervisionConfig(**plan['config'])),update_schedule(b,ReceiverSupervisionConfig(**plan['config'])))
            self.assertEqual([e['anchor'] for e in a],[e['anchor'] for e in b])
            self.assertNotEqual([e['primary'] for e in a],[e['primary'] for e in b])

    def test_full_mock_round_trip_evaluation_resume_and_export(self):
        from pact.training.colab import review_bundle, _restore_snapshot
        from pact.training.receiver_study import read_receiver_supervision_review
        plan,runtime=child_fixture()
        with tempfile.TemporaryDirectory() as tmp,contextlib.redirect_stdout(io.StringIO()):
            root=Path(tmp)/'run';rec=setup(root,plan);donor=cd.MockDonorBackend()
            cd.acquire(plan,donor,runtime,root,rec);contexts=assert_contexts(root,plan)
            self.assertEqual(len(donor.calls),192)
            for arm in ('task_sft','receiver_sft'):
                examples=training_examples(plan,contexts,donor.tokenizer,arm)
                schedule=update_schedule(examples,ReceiverSupervisionConfig(**plan['config']))
                self.assertEqual(len(schedule),2)
                # Explicit optimizer software double, NOT a real adapter update or efficacy claim.
                write_json(root/'training'/arm/'status.json',{'complete':True,'training_executed':True,
                    'initial_weight_hash':digest('same mock initialization'),'mock_optimizer':True,'steps':len(schedule)})
            for arm in ('frozen','task_sft','receiver_sft'):
                backend=RxBackend(runtime);backend.identity['snapshot']=digest(arm)
                with patch('pact.training.receiver_study.score_prefix',return_value=1.5):
                    with self.assertRaises(CallBoundaryStop):evaluate(plan,contexts,backend,runtime,root,arm,rec,stop_after=2)
                    evaluate(plan,contexts,backend,runtime,root,arm,rec);count=len(backend.calls)
                    evaluate(plan,contexts,backend,runtime,root,arm,rec);self.assertEqual(count,len(backend.calls))
            result=report(root);self.assertEqual(result['scientific_status'],'mock_only')
            self.assertLessEqual(result['generation_accounting']['attempted_calls'],912)
            self.assertLessEqual(result['teacher_forced_forwards'],288)
            self.assertIn('controlled_donor_comparisons',result)
            self.assertIn('newly constructed offline',result['history'])
            self.assertEqual(result['readiness']['rationale_review_status'],'not_reviewed')
            for v in result['arms'].values():
                for r in v['per_task']:
                    if r['kind']=='natural_team':
                        self.assertNotIn('support_option',canonical(r['trajectory']))
            snapshot=_sync_run(root,Path(tmp)/'durable');_restore_snapshot(snapshot,Path(tmp)/'restored',kind='receiver_supervision')
            assert_contexts(Path(tmp)/'restored',plan)
            bundle=review_bundle(root,Path(tmp)/'review.zip',{},kind='receiver_supervision_review',max_metadata_bytes=256*1024**2,include_markdown=True)
            content=read_receiver_supervision_review(bundle['path'],bundle['sha256'])
            self.assertEqual(content['plan.json']['source_variant'],cd.SOURCE)
            rows=ShardStore(root/'donors').records();rows[0]['raw']='changed'
            write_json(ShardStore(root/'donors').path(rows[0]['work_id']),rows[0])
            with self.assertRaises(ValueError):assert_contexts(root,plan)

    def test_exact_fixture_notebook_and_versioned_config(self):
        root=Path(__file__).resolve().parents[1]
        config=cd.load_config(root/'experiments/controlled_peer_donors_v1.json')
        self.assertEqual(cd.budget(config)['optimizer_updates_all_arms_upper_bound'],64)
        fixture=read_json(root/'tests/fixtures/controlled_peer_donors_v1.json')
        for kind,row in fixture['receiver_contexts'].items():
            prompt=json.loads(row['messages'][1]['content'])
            self.assertEqual(prompt['own_private']['text'],fixture['own_raw'])
            self.assertNotIn('support_option',prompt)
            actual=prefix_tokens(cd.MockTokenizer(),row['messages'],'B',('A','B'))
            self.assertEqual(json.loads(canonical(actual)),row['target'])
            self.assertEqual([actual['input_ids'][i] for i in actual['supervised_positions']],[67])
        self.assertEqual(fixture['receiver_contexts']['correct_target']['messages'][0],fixture['receiver_contexts']['wrong_target']['messages'][0])
        notebook=read_json(root/'notebooks/05_controlled_peer_donors_colab.ipynb')
        for i,cell in enumerate(notebook['cells']):
            if cell['cell_type']=='code':
                compile(''.join(cell['source']),f'controlled-cell-{i}','exec')
                self.assertIsNone(cell['execution_count']);self.assertEqual(cell['outputs'],[])

    def test_isolation_restores_grad_modes_on_success_and_error(self):
        from test_adapters import FakeModel
        class Model(FakeModel):
            peft_config={'a':{}}
            training=True
            def modules(self):return [self]
            def eval(self):self.training=False;return self
        for fail in (False,True):
            model=Model()
            try:
                with cd.donor_isolation(model):
                    self.assertTrue(model.disabled);self.assertFalse(model.parameter.requires_grad)
                    if fail:raise RuntimeError('fixture')
            except RuntimeError:pass
            self.assertTrue(model.parameter.requires_grad);self.assertTrue(model.training)
            self.assertEqual(model.active_adapter,'distinct-a');self.assertFalse(model.disabled)


@unittest.skipUnless(os.environ.get('PACT_TEST_NEURAL')=='1','opt-in tiny CPU model; no downloaded weights')
class ControlledNeuralTests(unittest.TestCase):
    def test_both_real_training_arms_identical_initialization_and_resume(self):
        import torch
        from transformers import Qwen3Config,Qwen3ForCausalLM
        from pact.training.warmstart import create_adapters,adapter_parameters
        from pact.training.warmstart_config import WarmstartConfig
        from pact.training.receiver_supervision_train import train_focal
        torch.set_num_threads(1)
        plan,runtime=child_fixture()
        def model():
            torch.manual_seed(17)
            return create_adapters(Qwen3ForCausalLM(Qwen3Config(vocab_size=256,hidden_size=16,intermediate_size=32,
                num_hidden_layers=1,num_attention_heads=2,num_key_value_heads=2,head_dim=8,max_position_embeddings=4096)),
                WarmstartConfig('a'*64,rank=2,alpha=2,dropout=0.))
        with tempfile.TemporaryDirectory() as tmp,contextlib.redirect_stdout(io.StringIO()):
            root=Path(tmp);rec=setup(root,plan);donor=cd.MockDonorBackend();cd.acquire(plan,donor,runtime,root,rec)
            contexts=assert_contexts(root,plan);initial={n:p.clone() for n,p in model().named_parameters()};hashes=[]
            for arm in ('task_sft','receiver_sft'):
                examples=training_examples(plan,contexts,donor.tokenizer,arm);cfg=ReceiverSupervisionConfig(**plan['config'])
                identity={'arm':arm,'fixture':'tiny local initialized controlled-context training'}
                full=model();status=train_focal(full,examples,cfg,root/arm,identity);hashes.append(status['initial_weight_hash'])
                train_focal(model(),examples,cfg,root/(arm+'-resume'),identity,stop_after=1)
                resumed=model();train_focal(resumed,examples,cfg,root/(arm+'-resume'),identity,resume=True)
                for n,p in full.named_parameters():
                    self.assertTrue(torch.equal(p,dict(resumed.named_parameters())[n]),n)
                    if n not in adapter_parameters(full,'agent0'):self.assertTrue(torch.equal(p,initial[n]),n)
            self.assertEqual(hashes[0],hashes[1])
