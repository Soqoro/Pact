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
from pact.schemas import TaskInput, TaskLabel, Option
from pact.training.collection_config import CollectionRuntime
from pact.training.receiver import CallBoundaryStop
from pact.training.receiver_supervision import (ReceiverSupervisionConfig, study_budget, study_plan,
    answer_prefix, prefix_tokens, balanced_weights, receiver_objective, build_contexts)
from pact.training.receiver_supervision_train import training_examples, update_schedule
from pact.training.receiver_study import collect, evaluate, report, validate_local_recovery, Recovery
from pact.util import digest, canonical, read_json, write_json
from test_receiver import FixtureBackend
from test_receiver_plan import fixtures


class CharacterTokenizer:
    """Transparent local tokenizer fixture, never represented as Qwen tokenization."""
    eos_token_id=0
    def apply_chat_template(self, messages, **kwargs):
        return ''.join(f'<{m["role"]}>\n{m["content"]}\n' for m in messages)+'<assistant>\n'
    def encode(self,text,**kwargs):return [ord(c)+1 for c in text]
    def __call__(self,text,**kwargs):
        return {'input_ids':self.encode(text),'offset_mapping':[(i,i+1) for i in range(len(text))]}


def fixture_plan():
    _,pool,_=fixtures();tasks,labels,manifest,_=pool
    c=ReceiverSupervisionConfig(data_manifest_hash=digest(manifest))
    old={'selection':manifest['selected'][:120],
         'private_probe_requests':[{'task':dc.asdict(t)} for t in tasks[120:144]],
         'baseline_models':{'base':{'snapshot':'base','runtime_fingerprint':'runtime'}}}
    review={'preparation_plan.json':old,'references/references.json':{'final_step':90},'status.json':{'completed_steps':90}}
    with patch('pact.training.receiver_supervision.read_training_data',return_value=pool),patch('pact.training.receiver_supervision.read_review',return_value=review):
        plan=study_plan(c,'unused','unused')
    return json.loads(canonical(plan)),pool,review


class RxBackend(FixtureBackend):
    def __init__(self, runtime):
        super().__init__(runtime,SimpleNamespace(reference_hashes=('a','b','c'),runtime_fingerprint='runtime',base_snapshot='base'))
        self.tokenizer=CharacterTokenizer()
    def generate(self, request):
        # Alternate the prespecified focal draws; natural initial packets remain actual fixture outputs.
        original=self.mode
        if request.phase=='private' and request.actor=='agent-0':self.mode='all_correct' if request.seed%2 else 'all_wrong'
        result=super().generate(request);self.mode=original;return result


def collected(tmp, stop_after=None):
    plan,_,_=fixture_plan();runtime=CollectionRuntime(digest(plan),plan['config']['generation_seed'])
    backend=RxBackend(runtime);root=Path(tmp)
    rec=SimpleNamespace(before=lambda:None,after=lambda:None)
    with contextlib.redirect_stdout(io.StringIO()):collect(plan,backend,runtime,root,rec,stop_after)
    return plan,backend,runtime,rec


class ReceiverSupervisionTests(unittest.TestCase):
    def test_budget_and_strict_defaults(self):
        c=ReceiverSupervisionConfig().validate();b=study_budget(c)
        self.assertEqual((b['generation_calls_upper_bound'],b['generated_tokens_upper_bound']),(1296,322560))
        self.assertEqual(b['training_forward_backward_upper_bound'],512)
        for change in ({'donor_draws':5},{'lambda_dpo':1},{'generation_cap':1200},{'passes':3}):
            with self.assertRaises(ValueError):dc.replace(c,**change).validate()

    def test_frozen_split_exclusions_and_duplicates(self):
        plan,pool,review=fixture_plan();selection=plan['selection']
        self.assertEqual(len(selection),96);self.assertEqual(len({e['group_id'] for e in selection}),96)
        self.assertFalse(set(e['task_id'] for e in selection)&set(plan['excluded_task_ids']))
        for partition,count in (('fit',32),('heldout',16)):
            for family in ('arc_challenge','logiqa'):
                self.assertEqual(sum(e['partition']==partition and e['family']==family for e in selection),count)
        c=ReceiverSupervisionConfig(data_manifest_hash=digest(pool[2]))
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'selection.json';write_json(path,selection[:-1])
            with patch('pact.training.receiver_supervision.read_training_data',return_value=pool),patch('pact.training.receiver_supervision.read_review',return_value=review):
                with self.assertRaisesRegex(ValueError,'membership'):study_plan(c,'unused','unused',path)

    def test_prefix_mask_multitoken_no_eos_no_label_input(self):
        tok=CharacterTokenizer();messages=[{'role':'user','content':'Exact trusted task and untrusted saved packets.'}]
        tokens=prefix_tokens(tok,messages,'XY',('XY','Z'))
        self.assertEqual(tokens['output_prefix'],'{"answer":"XY"')
        self.assertEqual(''.join(chr(tokens['input_ids'][i]-1) for i in tokens['supervised_positions']),'XY')
        self.assertEqual(sum(tokens['score_mask']),2);self.assertNotIn(0,tokens['input_ids'])
        self.assertNotIn('XY',tokens['prompt'])
        complete=json.loads(tokens['output_prefix']+',"justification":"An explanation."}')
        self.assertEqual(complete['answer'],'XY');self.assertFalse(tokens['is_generated_packet'])
        with self.assertRaises(ValueError):prefix_tokens(tok,messages,'Z',('Z',),context_limit=5)

    def test_task_weighting_missing_stratum_and_dpo_routing(self):
        rows=[{'record_id':str(i),'task_id':t,'stratum':s} for i,(t,s) in enumerate([('a','hold'),('a','hold'),('b','hold'),('c','repair')])]
        weights=balanced_weights(rows,1)['weights'];self.assertEqual(list(weights.values()),[.125,.125,.25,.5])
        self.assertEqual(balanced_weights(rows[:3],1)['status'],'insufficient_context_support')
        self.assertEqual(receiver_objective(base=2,specialization=5,receiver=3),5)
        self.assertEqual(receiver_objective(base=2,specialization=5,receiver=3,lambda_spec=.2),6)
        with self.assertRaises(ValueError):receiver_objective(base=0,specialization=0,receiver=1,lambda_dpo=1)
        self.assertEqual(receiver_objective(base=0,specialization=0,receiver=1,lambda_dpo=1,dpo=2,dpo_validated=True),3)

    def test_collection_resume_contexts_eligibility_and_no_pairs(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(CallBoundaryStop):collected(tmp,stop_after=9)
            root=Path(tmp);first=len(ShardStore(root/'contexts'/'calls').records());self.assertEqual(first,9)
            plan,backend,_,_=collected(tmp)
            self.assertEqual(len(backend.calls),672-9)
            contexts=read_json(root/'contexts.json');self.assertEqual(contexts['status'],'ready')
            for partition in contexts['partitions'].values():
                for row in partition['records']:
                    self.assertIn(row['source'],('natural','curated'))
                    self.assertEqual(row['baseline_completion_class'],'not_required')
                    self.assertNotIn('target_answer',row['messages'][1]['content'])
                    for donor in row['donor_origins']:
                        self.assertEqual(donor['packet']['task_id'],row['task_id'])
            for baseline in ('all_wrong','all_correct','abstention'):
                changed=copy.deepcopy(contexts)
                for row in changed['partitions']['fit']['records']:row['baseline_completion_class']=baseline
                examples=training_examples(plan,changed,CharacterTokenizer(),'receiver_sft')
                self.assertTrue(examples)
            qa=training_examples(plan,contexts,CharacterTokenizer(),'task_sft')
            rx=training_examples(plan,contexts,CharacterTokenizer(),'receiver_sft')
            self.assertEqual(update_schedule(qa,ReceiverSupervisionConfig()),update_schedule(rx,ReceiverSupervisionConfig()))
            self.assertEqual([e['anchor'] for e in qa],[e['anchor'] for e in rx])
            rows=ShardStore(root/'contexts').records();rows[0]['alternatives'][0]['task_id']='foreign'
            with self.assertRaises(ValueError):build_contexts(plan,rows)

    def test_matched_identity_and_missing_weights_preflight(self):
        from pact.training.receiver_study import validate_receiver_match,initial_recipe
        match={'task_id':'a','context_hash':'h','actor':0,'seed':1,'decoding':'fixed'}
        left={'match':match,'checkpoint':'prepared'};right={'match':dict(match),'checkpoint':'trained'}
        validate_receiver_match(left,right,'prepared','trained')
        for key in ('context_hash','seed','actor','decoding'):
            changed=copy.deepcopy(right);changed['match'][key]='changed'
            with self.assertRaises(ValueError):validate_receiver_match(left,changed,'prepared','trained')
        with self.assertRaises(ValueError):validate_receiver_match(left,right,'prepared','wrong trained checkpoint')
        plan,_,_=fixture_plan()
        with tempfile.TemporaryDirectory() as tmp,patch('pact.training.receiver_study.CollectionBackend') as load:
            with self.assertRaises((FileNotFoundError,KeyError,ValueError)):initial_recipe(plan,Path(tmp)/'missing')
            load.assert_not_called()

    def test_bounded_absent_support_and_ambiguous_recovery(self):
        plan,_,_=fixture_plan();runtime=CollectionRuntime(digest(plan),plan['config']['generation_seed'])
        one=copy.deepcopy(plan);one['selection']=one['selection'][:1]
        with tempfile.TemporaryDirectory() as tmp,contextlib.redirect_stdout(io.StringIO()):
            root=Path(tmp);backend=RxBackend(runtime);recovery=SimpleNamespace(before=lambda:None,after=lambda:None)
            result=collect(one,backend,runtime,root,recovery)
            self.assertEqual(result['status'],'insufficient_context_support');self.assertEqual(len(backend.calls),7)
            key=digest('unresolved')
            write_json(root/'contexts/call-intents'/f'{key}.json',{'schema_version':1,'work_id':key,'max_tokens':256})
            with self.assertRaisesRegex(ValueError,'Ambiguous'):validate_local_recovery(root,one)

    def test_notebook_cells_compile_and_markdown_review(self):
        from pact.training.colab import review_bundle
        from pact.training.receiver_study import read_receiver_supervision_review
        notebook=read_json(Path(__file__).resolve().parents[1]/'notebooks/04_receiver_supervision_colab.ipynb')
        for i,cell in enumerate(notebook['cells']):
            if cell['cell_type']=='code':
                compile(''.join(cell['source']),f'cell-{i}','exec')
                self.assertIsNone(cell['execution_count']);self.assertEqual(cell['outputs'],[])
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)/'run';root.mkdir();write_json(root/'plan.json',{'variant':'receiver_supervision_v1'})
            (root/'CODEX_HANDOFF.md').write_text('Synthetic review fixture, no GPU evidence.')
            bundle=review_bundle(root,Path(tmp)/'review.zip',{},kind='receiver_supervision_review',include_markdown=True)
            content=read_receiver_supervision_review(bundle['path'],bundle['sha256'])
            self.assertIn('CODEX_HANDOFF.md',content)

    def test_actual_source_plan_matches_frozen_selection(self):
        root=Path(__file__).resolve().parents[1]
        bundle=root/'results_import/qwen3-preparation-120-001-handoff-1789930640697369191.zip'
        if not bundle.exists():self.skipTest('Retained local evidence absent')
        plan=study_plan(ReceiverSupervisionConfig(),root/'results_import/training-data-001/proposal-1200',bundle,root/'experiments/receiver_supervision_selection.json')
        self.assertEqual(len(plan['excluded_task_ids']),144)

    def test_evaluation_three_arms_and_cache_checkpoint_rejection(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);plan,backend,runtime,recovery=collected(tmp)
            contexts=read_json(root/'contexts.json');write_json(root/'plan.json',plan)
            for arm in ('frozen','task_sft','receiver_sft'):
                b=RxBackend(runtime);b.identity['snapshot']=digest(arm)
                with contextlib.redirect_stdout(io.StringIO()),patch('pact.training.receiver_study.score_prefix',return_value=1.5):
                    result=evaluate(plan,contexts,b,runtime,root,arm,recovery)
                    n=len(b.calls);evaluate(plan,contexts,b,runtime,root,arm,recovery)
                self.assertEqual(len(b.calls),n);self.assertEqual(result['committed_calls'],208)
                write_json(root/'training'/arm/'status.json',{'complete':True,'training_executed':True,'initial_weight_hash':digest('fixture initial adapters'),'fixture':True})
            result=report(root);self.assertEqual(result['generation_accounting']['attempted_calls'],1296)
            self.assertEqual(result['teacher_forced_forwards'],192)
            self.assertIn('c',result['arms']['frozen']['natural_team']['clean'])
            b=RxBackend(runtime);b.identity['snapshot']=digest('changed checkpoint')
            with self.assertRaisesRegex(ValueError,'provenance'):
                evaluate(plan,contexts,b,runtime,root,'frozen',recovery)

    def test_restore_rejects_unsafe_and_export_checksums(self):
        from pact.training.colab import _restore_snapshot, review_bundle
        from pact.training.feasibility import read_review
        with tempfile.TemporaryDirectory() as tmp:
            tmp=Path(tmp);root=tmp/'run';root.mkdir();plan,_,_=fixture_plan();recipe={'plan':plan}
            write_json(root/'plan.json',plan);write_json(root/'recipe.json',recipe)
            write_json(root/'state.json',{'study_hash':digest(recipe),'recovery_safe':False})
            snapshot=_sync_run(root,tmp/'durable')
            with self.assertRaisesRegex(ValueError,'Unsafe'):_restore_snapshot(snapshot,tmp/'bad',kind='receiver_supervision')
            write_json(root/'state.json',{'study_hash':digest(recipe),'recovery_safe':True})
            snapshot=_sync_run(root,tmp/'durable');_restore_snapshot(snapshot,tmp/'restored',kind='receiver_supervision')
            bundle=review_bundle(root,tmp/'review.zip',{},kind='receiver_supervision_review')
            imported=read_review(bundle['path'],bundle['sha256']);self.assertIn('plan.json',imported)


@unittest.skipUnless(os.environ.get('PACT_TEST_NEURAL')=='1','opt-in tiny CPU model, no downloaded weights')
class ReceiverSupervisionNeuralTests(unittest.TestCase):
    def test_independent_shift_padding_multitoken_and_accumulation(self):
        import torch
        from pact.training.receiver_supervision import torch_answer_ce
        torch.set_num_threads(1);torch.manual_seed(11)
        logits=torch.randn(2,6,9,dtype=torch.float64,requires_grad=True)
        ids=torch.tensor([[1,2,3,4,5,0],[1,2,3,4,0,0]])
        attention=torch.tensor([[1,1,1,1,1,0],[1,1,1,1,0,0]])
        mask=torch.tensor([[0,0,0,1,1,0],[0,0,0,1,0,0]])
        actual=torch_answer_ce(logits,ids,attention,mask)
        expected=torch.stack([-(logits[0,2].log_softmax(-1)[4]+logits[0,3].log_softmax(-1)[5])/2,-logits[1,2].log_softmax(-1)[4]])
        torch.testing.assert_close(actual,expected)
        expected_loss=(actual*torch.tensor([.3,.7])).sum();expected_loss.backward();grad=logits.grad.clone();logits.grad=None
        for i,w in enumerate((.3,.7)):(torch_answer_ce(logits[i:i+1],ids[i:i+1],attention[i:i+1],mask[i:i+1])[0]*w).backward()
        torch.testing.assert_close(logits.grad,grad)
        self.assertEqual(logits.grad[:,4:].abs().sum(),0)
        invalid=mask.clone();invalid[0,5]=1
        with self.assertRaises(ValueError):torch_answer_ce(logits,ids,attention,invalid)

    def test_real_adapter_training_isolation_improvement_and_exact_resume(self):
        import torch
        from transformers import Qwen3Config,Qwen3ForCausalLM
        from pact.training.warmstart import create_adapters,adapter_parameters,training_adapter
        from pact.training.warmstart_config import WarmstartConfig
        from pact.training.receiver_supervision_train import train_focal,token_loss
        torch.set_num_threads(1)
        def model():
            torch.manual_seed(17)
            base=Qwen3ForCausalLM(Qwen3Config(vocab_size=32,hidden_size=16,intermediate_size=32,num_hidden_layers=1,
                num_attention_heads=2,num_key_value_heads=2,head_dim=8,max_position_embeddings=64,attention_dropout=0.))
            value=create_adapters(base,WarmstartConfig('a'*64,rank=2,alpha=2,dropout=0.))
            value.gradient_checkpointing_enable(gradient_checkpointing_kwargs={'use_reentrant':False})
            value.config.use_cache=False
            return value
        tokens={'input_ids':[1,2,3,4,5],'attention_mask':[1]*5,'score_mask':[0,0,0,1,1]}
        examples=[{'record_id':str(i),'task_id':str(i),'stratum':'hold' if i<2 else 'repair','weight':.25,'primary':tokens,'anchor':tokens} for i in range(4)]
        config=dc.replace(ReceiverSupervisionConfig(),passes=2)
        identity={'arm':'receiver_sft','fixture':'locally initialized tiny Qwen, not scientific evidence'}
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);full=model();initial={n:p.detach().clone() for n,p in full.named_parameters()}
            with training_adapter(full,'agent0'),torch.no_grad():before=float(token_loss(full,tokens))
            status=train_focal(full,examples,config,root/'full',identity)
            with training_adapter(full,'agent0'),torch.no_grad():after=float(token_loss(full,tokens))
            self.assertLess(after,before);self.assertTrue(status['complete'])
            partial=model();train_focal(partial,examples,config,root/'split',identity,stop_after=1)
            resumed=model();train_focal(resumed,examples,config,root/'split',identity,resume=True)
            for n,p in full.named_parameters():
                self.assertTrue(torch.equal(p,dict(resumed.named_parameters())[n]),n)
                if n not in adapter_parameters(full,'agent0'):self.assertTrue(torch.equal(p,initial[n]),n)
            fresh=model()
            for n,p in fresh.named_parameters():self.assertTrue(torch.equal(p,initial[n]),n)
            count=len(list((root/'split'/'checkpoints').glob('step-*')))
            train_focal(model(),examples,config,root/'split',identity,resume=True)
            self.assertEqual(len(list((root/'split'/'checkpoints').glob('step-*'))),count)
            with self.assertRaisesRegex(ValueError,'identity'):
                train_focal(model(),examples,config,root/'split',{**identity,'arm':'task_sft'},resume=True)

    def test_exported_exact_prompt_fixture_independent_tiny_loss(self):
        import torch
        from transformers import Qwen3Config,Qwen3ForCausalLM
        from pact.training.receiver_supervision import torch_answer_ce
        torch.set_num_threads(1);torch.manual_seed(29)
        fixture=read_json(Path(__file__).parent/'fixtures/receiver_answer_ce_v1.json')
        actual=prefix_tokens(CharacterTokenizer(),fixture['messages'],'B',('A','B'))
        for key,value in actual.items():self.assertEqual(json.loads(canonical(value)),fixture[key])
        model=Qwen3ForCausalLM(Qwen3Config(vocab_size=256,hidden_size=16,intermediate_size=32,num_hidden_layers=1,
            num_attention_heads=2,num_key_value_heads=2,head_dim=8,max_position_embeddings=2048))
        ids=torch.tensor([fixture['input_ids']]);attention=torch.tensor([fixture['attention_mask']]);mask=torch.tensor([fixture['score_mask']])
        logits=model(input_ids=ids,attention_mask=attention).logits
        measured=torch_answer_ce(logits,ids,attention,mask)[0]
        independent=torch.stack([-logits[0,p-1].log_softmax(-1)[ids[0,p]] for p in fixture['supervised_positions']]).mean()
        torch.testing.assert_close(measured,independent)
