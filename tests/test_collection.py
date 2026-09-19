import contextlib
import dataclasses
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from pact.backends.mock import MockBackend
from pact.cli import main
from pact.datasets import fixtures
from pact.util import canonical, digest, file_hash, read_json, write_json
from pact.training.bank import read_bank
from pact.training.collection import collect_records, bank_for, cache_reference_scores, run_collection
from pact.training.collection_config import CollectionConfig, CollectionRuntime, load_collection_config, collection_plan
from pact.training.reference import ReferenceRequest
from pact.training.scoring import ACTORS, REFERENCES, FrozenScorer, scoring_adapter, load_frozen_adapters, verify_references


class CharTokenizer:
    eos_token_id = 0
    def encode(self, text, **kwargs):
        return [ord(c)+1 for c in text]
    def decode(self, ids, **kwargs):
        return ''.join(chr(i-1) for i in ids if i)


class FixtureScorer:
    def __init__(self, hashes):
        self.reference_hashes = hashes
        self.forwards = []
    def token_score(self, adapter, prompt, prompt_ids, completion, completion_ids):
        record = {'adapter': adapter, 'sum_logp': -float(len(completion_ids)), 'mean_nll': 1.,
                  'token_count': len(completion_ids), 'prompt_ids': list(prompt_ids),
                  'completion_ids': list(completion_ids), 'completion': completion}
        self.forwards.append(record)
        return record
    def answer_score(self, agent, prompt, completion):
        t=CharTokenizer()
        return self.token_score(ACTORS[agent],prompt,t.encode(prompt),completion,t.encode(completion)+[0])
    def reference_score(self, request):
        request.payload()
        return self.token_score(REFERENCES[request.agent], request.prompt, request.prompt_ids,
                                request.completion, request.completion_ids)['sum_logp']


class FixtureBackend(MockBackend):
    def __init__(self, runtime, hashes):
        super().__init__(runtime)
        self.tokenizer=CharTokenizer()
        self.base_identity={'snapshot':digest('fixture-base'),'runtime_fingerprint':digest('fixture-runtime'),
                            'tokenizer_revision':'0'*40,'template_hash':digest('mock-json'),'precision':'float32'}
        self.identity.update(snapshot=digest(['fixture-actors',hashes]),runtime_fingerprint=self.base_identity['runtime_fingerprint'])
        self.scorer=FixtureScorer(hashes)
        self.generation_tokens={}
    def assert_unchanged(self):
        pass
    def generate(self, request):
        raw,call=super().generate(request)
        if request.phase=='revision':
            raw=canonical({'answer':'A' if request.seed%2 else 'B','justification':'Explicit synthetic fixture.'})
        prompt_ids=self.tokenizer.encode(call.rendered_prompt)
        output=self.tokenizer.encode(raw)+[0]
        call=dataclasses.replace(call,input_tokens=len(prompt_ids),output_tokens=len(output))
        self.calls[-1]=call
        self.generation_tokens[digest(call)]={'prompt_ids':prompt_ids,'completion_ids':output,'raw':raw,'context_hash':call.context_hash}
        return raw,call


def fixture():
    selected=[fixtures(8)[i] for i in (4,5)]
    tasks=[dataclasses.replace(t,split='train') for t,l in selected]
    labels={l.task_id:l for t,l in selected}
    hashes=tuple(digest(['fixture-reference',i]) for i in range(3))
    config=CollectionConfig(digest('fixture-data'),digest('fixture-manifest'),hashes)
    runtime=CollectionRuntime(digest(config),config.seed)
    return config,tasks,labels,runtime


class CollectionTests(unittest.TestCase):
    def test_empty_reference_cache_skips_model_and_rejects_incompatible_recipe(self):
        from pact.training.collection import reference_cache_plan, run_reference_cache
        cfg,tasks,labels,runtime=fixture()
        with tempfile.TemporaryDirectory() as tmp, contextlib.redirect_stdout(io.StringIO()):
            root=Path(tmp);backend=FixtureBackend(runtime,cfg.reference_hashes)
            records,_=collect_records(cfg,tasks,labels,runtime,backend,root/'raw',synthetic=True)
            # Explicit test-only provenance conversion exercises the production gate.
            bank=dataclasses.replace(bank_for(records,cfg,backend,synthetic=True),kind='training',receivers=())
            self.assertEqual(reference_cache_plan(cfg,bank)['teacher_forced_forwards_upper_bound'],0)
            with patch('pact.training.collection.CollectionBackend') as model:
                result=run_reference_cache(cfg,bank,root/'absent',root/'cache',root/'unused')
                self.assertEqual(result['status'],'no_eligible_preferences');model.assert_not_called()
                self.assertEqual(result,run_reference_cache(cfg,bank,root/'absent',root/'cache',root/'unused',resume=True))
                with self.assertRaises(ValueError):
                    run_reference_cache(cfg,bank,root/'absent',root/'cache',root/'unused')
            with self.assertRaises(ValueError):
                reference_cache_plan(dataclasses.replace(cfg,data_manifest_hash=digest('changed')),bank)
            with self.assertRaises(ValueError):reference_cache_plan(cfg,dataclasses.replace(bank,rows=bank.rows[:1]))

    def test_plan_is_train_only_bounded_and_does_not_load_model(self):
        config,tasks,labels,runtime=fixture()
        manifest={'fixture':True};config=dataclasses.replace(config,data_manifest_hash=digest(manifest))
        with patch('pact.training.collection_config.read_training_data',return_value=(tasks,labels,manifest,{})):
            chosen,_,_,_,plan=collection_plan(config,Path('unused'))
            self.assertEqual({t.task_id for t in chosen},{t.task_id for t in tasks})
            self.assertEqual(plan['generation_calls_upper_bound'],474)
            self.assertEqual(plan['teacher_forced_forwards_upper_bound'],72)
            for changes in ({'items':4},{'items':True},{'conditions':('clean',)},{'reference_hashes':('a'*64,)}, {'seed':True}):
                with self.assertRaises(ValueError): dataclasses.replace(config,**changes).validate()
            with tempfile.TemporaryDirectory() as tmp, contextlib.redirect_stdout(io.StringIO()):
                root=Path(tmp);write_json(root/'config.json',config)
                with patch('pact.training.collection.CollectionBackend') as model:
                    self.assertEqual(main(['collect-bank','--config',str(root/'config.json'),'--references-dir','absent',
                        '--data-dir','unused','--run-dir',str(root/'run')]),0)
                    model.assert_not_called();self.assertFalse((root/'run').exists())
            with patch('pact.training.collection_config.read_training_data',return_value=([dataclasses.replace(t,split='validation') for t in tasks],labels,manifest,{})):
                with self.assertRaises(ValueError): collection_plan(config,Path('unused'))

    def test_collection_pairs_resume_and_reference_cache_round_trip(self):
        cfg,tasks,labels,runtime=fixture()
        with tempfile.TemporaryDirectory() as tmp, contextlib.redirect_stdout(io.StringIO()):
            root=Path(tmp)
            first=FixtureBackend(runtime,cfg.reference_hashes)
            records,complete=collect_records(cfg,tasks,labels,runtime,first,root,stop_after=1,synthetic=True)
            self.assertFalse(complete);self.assertEqual(len(records),1)
            hashes={p.name:file_hash(p) for p in (root/'shards').iterdir()}
            backend=FixtureBackend(runtime,cfg.reference_hashes)
            records,complete=collect_records(cfg,tasks,labels,runtime,backend,root,synthetic=True)
            self.assertTrue(complete);self.assertEqual(len(records),6)
            for name,h in hashes.items():self.assertEqual(file_hash(root/'shards'/name),h)
            self.assertEqual(len(backend.calls),sum(r['generation_calls'] for r in records[1:]))
            bank=bank_for(records,cfg,backend,synthetic=True)
            self.assertEqual(bank.kind,'synthetic_fixture')
            self.assertTrue(any(v is None for row in bank.rows for v in row.delta))
            self.assertTrue(any(v is not None for row in bank.rows for v in row.delta))
            # Reused replay implementation must actually execute paired branches.
            eligible=0
            for rec in records:
                tr=rec['trajectory']
                for pair in rec['replays']:
                    if pair['status']!='eligible':continue
                    eligible+=1
                    for pos,neg in zip(pair['positive_suffixes'],pair['negative_suffixes']):
                        self.assertEqual(pos['attack'],neg['attack'])
                        self.assertEqual([c['seed'] for c in pos['calls']],[c['seed'] for c in neg['calls']])
                        for branch in (pos,neg):
                            self.assertEqual(branch['calls'][-1]['actor'],'base')
                            for j,p in enumerate(branch['private']):
                                if j!=pair['agent']:self.assertEqual(p,tr['private'][j])
                            if tr['condition']=='exchange':
                                self.assertTrue(all(m['text']==tr['attack']['payload'] for m in branch['delivered'] if m['sender']==tr['attack']['sender']))
            self.assertGreater(eligible,0)
            prefs,scores=cache_reference_scores(bank,backend,root/'reference-cache',synthetic=True)
            self.assertGreater(len(scores['scores']),0)
            self.assertEqual(set(prefs['pair_counts']),{'hold','repair'})
            calls=len(backend.scorer.forwards)
            self.assertEqual(scores,cache_reference_scores(bank,backend,root/'reference-cache',synthetic=True)[1])
            self.assertEqual(len(backend.scorer.forwards),calls)
            cache_file=next((root/'reference-cache').glob('*.json'));cache_file.write_text('{}')
            with self.assertRaises(ValueError):cache_reference_scores(bank,backend,root/'reference-cache',synthetic=True)
            shard=next((root/'shards').glob('*.json'));shard.write_text('{}')
            with self.assertRaises(ValueError):collect_records(cfg,tasks,labels,runtime,backend,root,synthetic=True)

    def test_invalid_and_length_candidates_retained_not_negative_preferences(self):
        cfg,tasks,labels,runtime=fixture()
        with tempfile.TemporaryDirectory() as tmp, contextlib.redirect_stdout(io.StringIO()):
            backend=FixtureBackend(runtime,cfg.reference_hashes)
            records,_=collect_records(cfg,tasks,labels,runtime,backend,Path(tmp),stop_after=1,synthetic=True)
            bank=bank_for(records,cfg,backend,synthetic=True)
            # Corrupt candidate text while preserving the exact same context.
            contexts=tuple(dataclasses.replace(c,candidates=tuple(dataclasses.replace(p,raw='invalid',stop_reason='length') for p in c.candidates)) for c in bank.receivers)
            bank=dataclasses.replace(bank,receivers=contexts)
            prefs,scores=cache_reference_scores(bank,backend,Path(tmp)/'empty-cache',synthetic=True)
            self.assertEqual(scores['scores'],[]);self.assertFalse(prefs['full_revision_ready'])
            self.assertTrue(any(c['candidate_count'] for c in prefs['contexts']))

    def test_verified_references_reject_changes_and_symlinks_before_model_load(self):
        from pact.backends.transformers import adapter_hash
        cfg,*_=fixture()
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            for name in ACTORS:
                write_json(root/name/'adapter_config.json',{'r':16,'lora_alpha':32,'target_modules':['q_proj','v_proj'],
                    'lora_dropout':0,'bias':'none','peft_type':'LORA','task_type':'CAUSAL_LM','modules_to_save':None})
                (root/name/'adapter_model.safetensors').write_bytes(b'fixture bytes, not neural weights')
            hashes=tuple(adapter_hash(root/n) for n in ACTORS)
            manifest={'schema_version':1,'final_step':9,'identity':{'model_snapshot':digest('fixture-base')},
                'references':[{'agent':i,'identity':name,'path':name,'kind':'warm_start_adapter','sha256':hashes[i]} for i,name in enumerate(ACTORS)]}
            write_json(root/'references.json',manifest)
            cfg=dataclasses.replace(cfg,reference_hashes=hashes,reference_manifest_hash=digest(manifest))
            self.assertEqual(verify_references(root,cfg),manifest)
            target=root/'agent0'/'adapter_model.safetensors';target.write_bytes(b'corrupt')
            with self.assertRaises(ValueError):verify_references(root,cfg)
            target.unlink();target.symlink_to(root/'agent1'/'adapter_model.safetensors')
            with self.assertRaises(ValueError):verify_references(root,cfg)

    def test_runner_failure_retains_diagnostic_and_resume_identity_fails_early(self):
        cfg,tasks,labels,runtime=fixture()
        plan={'fixture':True};data={'fixture':'training'}
        with tempfile.TemporaryDirectory() as tmp, contextlib.redirect_stdout(io.StringIO()):
            root=Path(tmp)/'run'
            with patch('pact.training.collection.collection_plan',return_value=(tasks,labels,data,runtime,plan)), \
                 patch('pact.training.collection.verify_references'), \
                 patch('pact.training.collection.CollectionBackend',side_effect=RuntimeError('fixture model load failure')):
                result=run_collection(cfg,Path('unused'),Path('unused'),root,Path('unused'))
            self.assertEqual(result['exit_code'],2);self.assertTrue(Path(result['path']).exists())
            self.assertEqual(read_json(root/'manifest.json')['status'],'failed')
            with patch('pact.training.collection.collection_plan',return_value=(tasks,labels,data,runtime,plan)), \
                 patch('pact.training.collection.CollectionBackend') as model:
                with self.assertRaises(ValueError):run_collection(cfg,Path('unused'),Path('unused'),root,Path('unused'),resume=True)
                model.assert_not_called()

    def test_runner_round_trip_persistence_and_failed_sync_retry(self):
        cfg,tasks,labels,runtime=fixture()
        with tempfile.TemporaryDirectory() as tmp, contextlib.redirect_stdout(io.StringIO()):
            root=Path(tmp)/'run';remote=Path(tmp)/'durable'
            with patch('pact.training.collection.collection_plan',return_value=(tasks,labels,{'fixture':'training'},runtime,{'fixture':True})), \
                 patch('pact.training.collection.verify_references'), \
                 patch('pact.training.collection.CollectionBackend',side_effect=lambda *args:FixtureBackend(runtime,cfg.reference_hashes)):
                with patch('pact.training.collection.sync_run',side_effect=TimeoutError('fixture mount stall')):
                    failed=run_collection(cfg,Path('unused'),Path('unused'),root,Path('unused'),persistent=remote)
                self.assertEqual(failed['exit_code'],2)
                self.assertFalse(failed['persistent_copy_verified'])
                self.assertTrue(Path(failed['path']).exists())
                self.assertEqual(failed['completed_records'],1)
                original={p.name:file_hash(p) for p in (root/'shards').iterdir()}
                completed=run_collection(cfg,Path('unused'),Path('unused'),root,Path('unused'),resume=True,persistent=remote)
                self.assertEqual(completed['exit_code'],0,completed)
                self.assertEqual(completed['status'],'collection_complete_local')
                self.assertTrue(completed['persistent_copy_verified'])
                self.assertEqual(completed['scientific_status'],'synthetic_fixture')
                import zipfile
                with zipfile.ZipFile(completed['path']) as archive:
                    self.assertEqual(json.loads(archive.read('HANDOFF.json'))['scientific_status'],'synthetic_fixture')
                self.assertTrue((Path(completed['persistent_snapshot'])/'COMPLETE').is_file())
                bank=read_bank(root/'bank.json',allow_synthetic=True)
                self.assertEqual(len(bank.rows),6)
                self.assertGreater(len(read_json(root/'reference_scores.json')['scores']),0)
                for n,h in original.items():self.assertEqual(file_hash(root/'shards'/n),h)
                from pact.training.collection import restore_collection
                restored=Path(tmp)/'restored'
                restore_collection(completed['persistent_snapshot'],restored,timeout_seconds=10)
                self.assertEqual(file_hash(restored/'bank.json'),file_hash(root/'bank.json'))
                self.assertEqual(file_hash(Path(completed['persistent_bundle'])),completed['sha256'])
                with self.assertRaises(ValueError):
                    restore_collection(completed['persistent_snapshot'],restored,timeout_seconds=10)
                prior_bank_hash=file_hash(root/'bank.json')
                # An idempotent repeat may load a model but regenerates/rescores nothing.
                repeated=run_collection(cfg,Path('unused'),Path('unused'),root,Path('unused'),resume=True)
                self.assertEqual(repeated['exit_code'],0)
                self.assertEqual(file_hash(root/'bank.json'),prior_bank_hash)
                usage=read_json(root/'resources.json')
                self.assertEqual(usage['invocation_generation_calls'],0)
                self.assertEqual(usage['invocation_teacher_forced_forwards'],0)
                self.assertEqual(len(list((root/'attempts').glob('*.json'))),3)
            changed=dataclasses.replace(cfg,seed=1730)
            with patch('pact.training.collection.collection_plan',return_value=(tasks,labels,{'fixture':'training'},runtime,{})), \
                 patch('pact.training.collection.CollectionBackend') as model:
                with self.assertRaisesRegex(ValueError,'before model load'):
                    run_collection(changed,Path('unused'),Path('unused'),root,Path('unused'),resume=True)
                model.assert_not_called()


@unittest.skipUnless(os.environ.get('PACT_TEST_NEURAL')=='1','explicit opt-in tiny CPU model; no downloaded weights')
class FrozenReferenceNeuralTests(unittest.TestCase):
    def test_backend_retains_sampled_ids_without_round_trip_and_clears_on_overflow(self):
        import torch
        from types import SimpleNamespace
        from transformers import BatchEncoding
        from pact.backends import Request
        from pact.backends.transformers import TransformersBackend
        from pact.schemas import Message
        class Tokenizer(CharTokenizer):
            pad_token_id=0
            def apply_chat_template(self,*args,**kwargs):return 'P'
            def __call__(self,text,**kwargs):
                return BatchEncoding({'input_ids':torch.tensor([self.encode(text)]),'attention_mask':torch.ones(1,1,dtype=torch.long)})
            def decode(self,ids,**kwargs):return 'A' if ids==[200,0] else super().decode(ids,**kwargs)
        class Model(torch.nn.Module):
            device=torch.device('cpu')
            generation_config=SimpleNamespace(eos_token_id=0)
            def generate(self,input_ids,**kwargs):return torch.cat([input_ids,torch.tensor([[200,0]])],dim=1)
        cfg,tasks,_,runtime=fixture()
        backend=TransformersBackend.__new__(TransformersBackend)
        backend.config=dataclasses.replace(runtime,model=dataclasses.replace(runtime.model,device='cpu'))
        backend.torch=torch;backend.model=Model();backend.tokenizer=Tokenizer();backend.calls=[]
        backend.identity={'snapshot':digest('fixture'),'template_hash':digest('P')}
        request=Request(tasks[0],(Message('user','fixture'),),'base','private',1,2,True)
        raw,call=backend.generate(request)
        self.assertEqual(raw,'A');self.assertEqual(call.stop_reason,'eos')
        self.assertEqual(backend.last_generation['completion_ids'],[200,0])
        self.assertNotEqual(backend.last_generation['completion_ids'],backend.tokenizer.encode(raw)+[0])
        _,call=backend.generate(dataclasses.replace(request,max_tokens=4096))
        self.assertEqual(call.stop_reason,'context_overflow')
        self.assertEqual(backend.last_generation['completion_ids'],[])
        self.assertIsNone(backend.pending_call)

    def test_reload_reference_logits_actor_mutation_masks_and_restoration(self):
        import torch
        import torch.nn.functional as F
        from transformers import Qwen3Config,Qwen3ForCausalLM
        from pact.training.warmstart import create_adapters,adapter_parameters
        from pact.training.warmstart_config import WarmstartConfig
        from pact.backends.transformers import adapter_hash,inference_adapter
        torch.set_num_threads(1)
        def base():
            torch.manual_seed(19)
            return Qwen3ForCausalLM(Qwen3Config(vocab_size=256,hidden_size=16,intermediate_size=32,
                num_hidden_layers=1,num_attention_heads=2,num_key_value_heads=2,head_dim=8,max_position_embeddings=64))
        cfg=WarmstartConfig('a'*64,rank=2,alpha=2,dropout=.2)
        trained=create_adapters(base(),cfg)
        with torch.no_grad():
            for i,name in enumerate(ACTORS):
                for n,p in adapter_parameters(trained,name).items():
                    if '.lora_B.' in n:p.fill_(.15*(i+1))
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            trained.save_pretrained(root,selected_adapters=list(ACTORS),safe_serialization=True,save_embedding_layers=False)
            hashes=tuple(adapter_hash(root/name) for name in ACTORS)
            model=load_frozen_adapters(base(),[root/n for n in ACTORS])
            tok=CharTokenizer()
            identity={'snapshot':digest('fixture-base'),'tokenizer_revision':'0'*40,'template_hash':digest('fixture-template'),
                      'precision':'float32','runtime_fingerprint':digest('fixture-runtime')}
            scorer=FrozenScorer(model,tok,identity,hashes,context_limit=64)
            request=ReferenceRequest('warm_start_adapter',0,hashes[0],identity['snapshot'],'0'*40,identity['template_hash'],
                'float32',identity['runtime_fingerprint'],'P',tuple(tok.encode('P')),'A',tuple(tok.encode('A')+[0]),0)
            # Independently compute the two shifted supervised log probabilities.
            tokens=torch.tensor([tok.encode('PA')+[0]])
            with scoring_adapter(model,'reference0'),torch.inference_mode():
                logits=model(tokens,use_cache=False).logits
                expected=F.log_softmax(logits[0,:2].float(),dim=-1)[torch.arange(2),tokens[0,1:]].sum().item()
            value=scorer.reference_score(request)
            self.assertAlmostEqual(value,expected,places=6)
            self.assertEqual(scorer.forwards[-1]['token_count'],2)
            self.assertAlmostEqual(scorer.forwards[-1]['mean_nll'],-expected/2,places=6)
            initial_reference={n:p.detach().clone() for n,p in model.named_parameters() if '.reference0.' in n}
            with scoring_adapter(model,'agent0'),torch.inference_mode():before=model(tokens,use_cache=False).logits.clone()
            with inference_adapter(model,None,True),torch.inference_mode():base_before=model(tokens,use_cache=False).logits.clone()
            with torch.no_grad():
                for n,p in adapter_parameters(model,'agent0').items():
                    if '.lora_B.' in n:p.normal_(mean=0,std=2.)
            with scoring_adapter(model,'agent0'),torch.inference_mode():after=model(tokens,use_cache=False).logits.clone()
            self.assertFalse(torch.equal(before,after))
            self.assertAlmostEqual(scorer.reference_score(request),value,places=6)
            with inference_adapter(model,None,True),torch.inference_mode():base_after=model(tokens,use_cache=False).logits.clone()
            self.assertTrue(torch.equal(base_before,base_after))
            for n,p in model.named_parameters():
                if n in initial_reference:self.assertTrue(torch.equal(initial_reference[n],p),n)
            # Scoring must restore the caller's active actor, train mode and grad flags.
            model.set_adapter('agent1');model.train()
            flags=[p.requires_grad for p in model.parameters()];modes=[m.training for m in model.modules()]
            self.assertAlmostEqual(scorer.reference_score(request),value,places=6)
            self.assertEqual(model.active_adapter,'agent1')
            self.assertEqual([p.requires_grad for p in model.parameters()],flags)
            self.assertEqual([m.training for m in model.modules()],modes)
            with patch.object(model,'forward',side_effect=RuntimeError('fixture failed forward')):
                with self.assertRaises(RuntimeError):scorer.reference_score(request)
            self.assertEqual(model.active_adapter,'agent1');self.assertEqual([p.requires_grad for p in model.parameters()],flags)
            for change in ({'adapter_hash':'f'*64},{'base_snapshot':'f'*64},{'prompt':'X'},
                           {'completion':'B'},{'completion_ids':(0,)},{'runtime_fingerprint':'f'*64}):
                with self.assertRaises(ValueError):scorer.reference_score(dataclasses.replace(request,**change))
            with self.assertRaises(ValueError):
                scorer.token_score('reference0','P'*64,tok.encode('P'*64),'A',tok.encode('A')+[0])
            with torch.no_grad():
                next(p for n,p in model.named_parameters() if '.reference0.' in n).add_(1.)
            with self.assertRaisesRegex(RuntimeError,'Frozen'):scorer.reference_score(request)
