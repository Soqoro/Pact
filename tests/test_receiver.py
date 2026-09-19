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

from pact.artifacts import _sync_run, ShardStore
from pact.backends import Request
from pact.cli import main
from pact.protocol import Protocol, private_prompt
from pact.schemas import CallRecord
from pact.training.collection_config import CollectionRuntime
from pact.training.receiver import (JournalBackend, CallBoundaryStop, inspect_journal,
    run_receiver, receiver_report, restore_receiver, read_receiver_review)
from pact.training.receiver_plan import receiver_feasibility_plan
from pact.util import canonical, digest, file_hash, read_json, write_json
from test_receiver_plan import fixtures


class FixtureBackend:
    """Invented outputs exercise recovery/accounting, never real model results."""
    def __init__(self, runtime, config, *, mode='mixed'):
        self.config, self.mode = runtime, mode
        self.identity = {'backend':'mock','snapshot':digest(['actors',config.reference_hashes]),
            'template_hash':digest('fixture-template'), 'runtime_fingerprint':config.runtime_fingerprint}
        self.base_identity = {'snapshot':config.base_snapshot, 'runtime_fingerprint':config.runtime_fingerprint}
        self.tokenizer = SimpleNamespace(eos_token_id=0)
        self.scorer = SimpleNamespace(forwards=[])
        self.calls=[]; self.generation_tokens={}; self.pending_call=None
    def assert_unchanged(self): pass
    def count_tokens(self,text): return len(text)
    def truncate(self,text,tokens): return text[:tokens]
    def resource_usage(self): return {'compute_units':None,'cache_hits':0}
    def generate(self, request):
        if self.mode == 'crash':raise RuntimeError('fixture interruption after intent')
        actor = int(request.actor[-1]) if request.actor!='base' else -1
        answer = ('A' if actor==0 else 'B') if request.phase=='private' else ('A' if request.seed%2 else 'B')
        if self.mode == 'all_correct':answer='A'
        if self.mode == 'all_wrong':answer='B'
        raw = canonical({'answer':answer} if request.phase=='final' else {'answer':answer,'justification':'Fixture.'})
        if self.mode=='invalid' and request.phase=='revision':raw='invalid fixture text'
        rendered=canonical([dc.asdict(m) for m in request.messages])
        prompt_ids=[ord(c)+1 for c in rendered]; completion_ids=[ord(c)+1 for c in raw]+[0]
        params={'max_new_tokens':request.max_tokens,'do_sample':not request.deterministic,
                'temperature':.7,'top_p':.8,'top_k':20}
        stop='eos'
        if len(prompt_ids)+request.max_tokens>4096:
            raw='';completion_ids=[];stop='context_overflow'
        call=CallRecord(request.actor,request.phase,self.identity['snapshot'],request.seed,request.messages,
            rendered,digest(rendered),self.identity['template_hash'],canonical(params),
            len(prompt_ids),len(completion_ids),stop,0.)
        self.calls.append(call)
        self.last_generation={'raw':raw,'prompt_ids':prompt_ids,'completion_ids':completion_ids,'context_hash':digest(rendered)}
        return raw,call


def setup_fixture():
    cfg,pool,warm=fixtures()
    with patch('pact.training.receiver_plan.read_training_data',side_effect=[pool,warm]):
        plan=receiver_feasibility_plan(cfg,'unused','unused')
    # The production planner stays fixed at 24. Four synthetic tasks keep runner
    # persistence tests small while exercising all three exchange sender positions.
    plan['selection']['selected']=plan['selection']['selected'][:4]
    plan['budget'].update(tasks=4,records=8,receiver_contexts_maximum=24,main_generation_calls=56,
        receiver_generation_calls_upper_bound=96,generation_calls_upper_bound=152,
        generated_tokens_upper_bound=37376,input_tokens_upper_bound=585216)
    return cfg,pool,warm,plan


@contextlib.contextmanager
def runner_fixture(cfg,pool,plan,backends,mode='mixed'):
    def create(runtime,*unused):
        backend=FixtureBackend(runtime,cfg,mode=mode);backends.append(backend);return backend
    with patch('pact.training.receiver.receiver_feasibility_plan',return_value=plan), \
         patch('pact.training.receiver.read_training_data',return_value=pool), \
         patch('pact.training.receiver.runtime_fingerprint',return_value=cfg.runtime_fingerprint), \
         patch('pact.training.receiver.verify_references'), \
         patch('pact.training.receiver.CollectionBackend',side_effect=create):
        yield


def execute(cfg,root,**kwargs):
    return run_receiver(cfg,'unused','unused','unused','unused',root,Path('unused'),**kwargs)


class ReceiverTests(unittest.TestCase):
    def test_call_boundary_resume_preserves_samples_protocol_and_zero_scoring(self):
        cfg,pool,_,plan=setup_fixture();backends=[]
        with tempfile.TemporaryDirectory() as tmp, contextlib.redirect_stdout(io.StringIO()), \
             runner_fixture(cfg,pool,plan,backends):
            root=Path(tmp)/'run'
            first=execute(cfg,root,stop_after=9)
            self.assertEqual(first['status'],'interrupted_at_call_boundary',first)
            self.assertEqual(first['committed_calls'],9)
            partial=read_json(root/'partial_report.json')
            self.assertEqual(partial['decision'],'incomplete')
            self.assertFalse(any(c['pair'] for c in partial['contexts']))
            hashes={p.name:file_hash(p) for p in (root/'calls/shards').iterdir()}
            completed=execute(cfg,root,resume=True)
            self.assertEqual(completed['exit_code'],0,completed)
            self.assertEqual(completed['status'],'receiver_feasibility_complete_local')
            report=read_json(root/'report.json')
            self.assertEqual(report['completed_records'],8)
            for name,h in hashes.items():self.assertEqual(file_hash(root/'calls/shards'/name),h)
            self.assertEqual(sum(len(b.calls) for b in backends),completed['committed_calls'])
            self.assertEqual(completed['committed_calls'],56+4*sum(s['eligible_contexts_observed'] for s in report['strata'].values()))
            for b in backends:self.assertEqual(b.scorer.forwards,[])
            for record in ShardStore(root).records():
                trajectory=record['trajectory']
                for c in record['receivers']:
                    for candidate in c['candidates']:
                        self.assertEqual(candidate['call']['rendered_prompt'],c['prompt'])
                        self.assertEqual(candidate['tokens']['prompt_ids'],c['prompt_ids'])
                    self.assertEqual(len({p['call']['seed'] for p in c['candidates']}),len(c['candidates']))
                sender=trajectory['attack']['sender']
                if sender is not None:
                    delivered=[m for m in trajectory['delivered'] if m['sender']==sender]
                    self.assertEqual(len(delivered),2)
                    self.assertTrue(all(m['text']==trajectory['attack']['payload'] for m in delivered))
                    self.assertNotEqual(trajectory['private'][sender]['raw'],trajectory['attack']['payload'])
                self.assertEqual(trajectory['final']['call']['actor'],'base')
                for packet in trajectory['revised']:
                    content=json.loads(packet['call']['messages'][-1]['content'])
                    self.assertEqual(content['own_private']['text'],trajectory['private'][packet['agent']]['raw'])
            before=file_hash(root/'report.json')
            repeated=execute(cfg,root,resume=True)
            self.assertEqual(repeated['exit_code'],0,repeated)
            self.assertEqual(len(backends[-1].calls),0)
            self.assertEqual(file_hash(root/'report.json'),before)

    def test_journal_rejects_corruption_ambiguous_calls_and_budget_expansion(self):
        cfg,pool,_,plan=setup_fixture();runtime=CollectionRuntime(digest(cfg),1729)
        task=pool[0][0];request=Request(task,private_prompt(task,''),'agent-0','private',1,256)
        with tempfile.TemporaryDirectory() as tmp,contextlib.redirect_stdout(io.StringIO()):
            root=Path(tmp)/'journal';backend=FixtureBackend(runtime,cfg)
            journal=JournalBackend(backend,root,plan['budget']);journal.begin_record(digest('record'))
            journal.generate(request)
            cached=JournalBackend(backend,root,plan['budget']);cached.begin_record(digest('record'))
            with self.assertRaisesRegex(ValueError,'provenance'):
                cached.generate(dc.replace(request,seed=2))
            self.assertEqual(len(backend.calls),1)
            marker=next((root/'calls/shards').glob('*.sha256'));marker.unlink()
            with self.assertRaisesRegex(ValueError,'Ambiguous'):inspect_journal(root,plan['budget'])
            fresh=Path(tmp)/'budget';budget={**plan['budget'],'generation_calls_upper_bound':0}
            journal=JournalBackend(backend,fresh,budget);journal.begin_record(digest('record'))
            with self.assertRaisesRegex(ValueError,'budget exhausted'):journal.generate(request)
            self.assertFalse((fresh/'call-intents').exists())

    def test_failed_attempt_exports_review_and_cannot_automatically_retry(self):
        cfg,pool,_,plan=setup_fixture();backends=[]
        with tempfile.TemporaryDirectory() as tmp,contextlib.redirect_stdout(io.StringIO()), \
             runner_fixture(cfg,pool,plan,backends,mode='crash'):
            root=Path(tmp)/'run';failed=execute(cfg,root)
            self.assertEqual(failed['exit_code'],2)
            self.assertTrue(Path(failed['path']).exists())
            self.assertFalse(read_json(root/'manifest.json')['recovery_safe'])
            self.assertEqual(read_json(root/'resources.json')['attempted_calls_total'],1)
            with self.assertRaisesRegex(ValueError,'Ambiguous'):execute(cfg,root,resume=True)

    def test_persistence_partial_restore_and_no_snapshot_rollback(self):
        cfg,pool,_,plan=setup_fixture();backends=[]
        with tempfile.TemporaryDirectory() as tmp,contextlib.redirect_stdout(io.StringIO()), \
             runner_fixture(cfg,pool,plan,backends):
            root=Path(tmp)/'run';durable=Path(tmp)/'durable'
            first=execute(cfg,root,stop_after=9,persistent=durable,timeout_seconds=10)
            self.assertTrue(first['persistent_copy_verified'],first)
            reviewed=read_receiver_review(first['path'],first['sha256'])
            self.assertEqual(reviewed['HANDOFF.json']['scientific_status'],'synthetic_fixture')
            restored=Path(tmp)/'restored'
            restore_receiver(first['persistent_snapshot'],restored,timeout_seconds=10)
            self.assertEqual(file_hash(restored/'partial_record.json'),file_hash(root/'partial_record.json'))
            completed=execute(cfg,restored,resume=True,persistent=durable,timeout_seconds=10)
            self.assertEqual(completed['exit_code'],0,completed)
            self.assertEqual(file_hash(Path(completed['persistent_bundle'])),completed['sha256'])
            with self.assertRaisesRegex(ValueError,'latest snapshot'):
                restore_receiver(first['persistent_snapshot'],Path(tmp)/'rollback',timeout_seconds=10)
            manifest=read_json(restored/'manifest.json');manifest['recovery_safe']=False
            write_json(restored/'manifest.json',manifest)
            unsafe=_sync_run(restored,durable)
            with self.assertRaisesRegex(ValueError,'possible lost calls'):
                restore_receiver(unsafe,Path(tmp)/'unsafe',timeout_seconds=10)
            self.assertFalse((Path(tmp)/'unsafe').exists())

    def test_timeout_before_sampling_keeps_local_zip_and_no_calls(self):
        cfg,pool,_,plan=setup_fixture();backends=[]
        with tempfile.TemporaryDirectory() as tmp,contextlib.redirect_stdout(io.StringIO()), \
             runner_fixture(cfg,pool,plan,backends), \
             patch('pact.training.receiver.sync_run',side_effect=TimeoutError('fixture timeout')):
            result=execute(cfg,Path(tmp)/'run',persistent=Path(tmp)/'durable')
            self.assertEqual(result['exit_code'],2)
            self.assertTrue(Path(result['path']).exists())
            self.assertEqual(len(backends[0].calls),0)
            self.assertFalse(result['persistent_copy_verified'])

    def test_runtime_and_resume_identity_rejection_before_model_generation(self):
        cfg,pool,_,plan=setup_fixture();backends=[]
        with tempfile.TemporaryDirectory() as tmp,contextlib.redirect_stdout(io.StringIO()), \
             runner_fixture(cfg,pool,plan,backends):
            root=Path(tmp)/'run'
            with patch('pact.training.receiver.runtime_fingerprint',return_value=digest('changed')):
                result=execute(cfg,root)
                self.assertEqual(result['exit_code'],2)
                self.assertEqual(backends,[])
            root=Path(tmp)/'valid';execute(cfg,root,stop_after=1)
            with self.assertRaisesRegex(ValueError,'source/recipe'):
                execute(dc.replace(cfg,generation_seed=4),root,resume=True)
            self.assertEqual(len(backends),1)

    def test_ineligible_and_invalid_pools_do_not_manufacture_pairs(self):
        cfg,pool,_,plan=setup_fixture()
        for mode in ('all_wrong','invalid'):
            with self.subTest(mode=mode),tempfile.TemporaryDirectory() as tmp, \
                 contextlib.redirect_stdout(io.StringIO()),runner_fixture(cfg,pool,plan,[],mode=mode):
                root=Path(tmp)/'run';result=execute(cfg,root)
                self.assertEqual(result['exit_code'],0,result)
                report=read_json(root/'report.json')
                self.assertTrue(report['complete'])
                self.assertFalse(any(c['pair'] for c in report['contexts']))
                if mode=='all_wrong':
                    self.assertEqual(result['committed_calls'],56)
                    self.assertIsNone(report['strata']['hold']['pair_yield']['value'])
                    self.assertEqual(report['decision'],'missing_eligible_stratum')
                else:
                    self.assertTrue(any(c['counts'].get('malformed')==4 for c in report['contexts']))
                    self.assertEqual(report['decision'],'no_pairs')

    def test_cli_plan_never_loads_model_or_requires_references(self):
        cfg,pool,_,plan=setup_fixture()
        with tempfile.TemporaryDirectory() as tmp,contextlib.redirect_stdout(io.StringIO()):
            root=Path(tmp);write_json(root/'config.json',cfg)
            with patch('pact.training.receiver_plan.receiver_feasibility_plan',return_value=plan), \
                 patch('pact.training.receiver.CollectionBackend') as backend:
                self.assertEqual(main(['receiver-feasibility','--config',str(root/'config.json'),
                    '--data-dir','unused','--warmstart-data-dir','unused','--selection','unused',
                    '--references-dir','absent','--run-dir',str(root/'absent')]),0)
                backend.assert_not_called();self.assertFalse((root/'absent').exists())

    def test_coverage_gate_requires_distinct_tasks_and_both_families(self):
        cfg,pool,_,plan=setup_fixture();backends=[]
        with tempfile.TemporaryDirectory() as tmp,contextlib.redirect_stdout(io.StringIO()), \
             runner_fixture(cfg,pool,plan,backends):
            root=Path(tmp)/'run';execute(cfg,root)
            original=ShardStore(root).records()[0]
            records=[]
            # Invented pools test the coverage gate independently of RNG outcomes.
            for i in range(8):
                record=copy.deepcopy(original);record['work_id']=digest(['record',i])
                task_id=plan['selection']['selected'][i//2]['task_id']
                task=record['trajectory']['task'];task.update(task_id=task_id,family=task_id.split(':')[0])
                record['evaluation']['task_id']=task_id
                for agent,context in enumerate(record['receivers']):
                    context['stratum']='hold' if agent==0 else 'repair';context['complete']=True
                    context['candidates']=[{'raw':canonical({'answer':'A' if n%2 else 'B','justification':'Fixture.'}),
                        'call':{'stop_reason':'eos'},'tokens':{'completion_ids':[1,0]}} for n in range(4)]
                records.append(record)
            report=receiver_report(plan,records)
            self.assertEqual(report['decision'],'broader_support_observed')
            self.assertFalse(report['full_pact_ready'])
            self.assertEqual(receiver_report(plan,records[:-1])['decision'],'incomplete')
            for record in records:record['trajectory']['task']['family']='arc_challenge'
            self.assertEqual(receiver_report(plan,records)['decision'],'limited_both_strata')

    @unittest.skipUnless(os.environ.get('PACT_TEST_NEURAL')=='1','opt-in tiny CPU model; no model download')
    def test_real_neural_journal_preserves_actors_references_and_base_readout(self):
        import torch
        from transformers import Qwen3Config,Qwen3ForCausalLM,BatchEncoding
        from pact.config import AdapterConfig
        from pact.training.scoring import CollectionBackend,load_frozen_adapters,FrozenScorer,ACTORS
        from pact.training.warmstart import create_adapters
        from pact.training.warmstart_config import WarmstartConfig
        torch.set_num_threads(1)
        def base():
            torch.manual_seed(17)
            return Qwen3ForCausalLM(Qwen3Config(vocab_size=16,hidden_size=16,intermediate_size=32,
                num_hidden_layers=1,num_attention_heads=2,num_key_value_heads=2,head_dim=8,
                max_position_embeddings=512,eos_token_id=0,pad_token_id=0,bos_token_id=1))
        class Tokenizer:
            eos_token_id=0;pad_token_id=0
            def apply_chat_template(self,messages,**kwargs):return canonical(messages)
            def __call__(self,text,**kwargs):
                return BatchEncoding({'input_ids':torch.tensor([[1,2]]),'attention_mask':torch.ones(1,2,dtype=torch.long)})
            def decode(self,ids,**kwargs):return ' '.join(str(t) for t in ids if t)
        cfg,pool,_,plan=setup_fixture()
        with tempfile.TemporaryDirectory() as tmp,contextlib.redirect_stdout(io.StringIO()):
            root=Path(tmp)
            trained=create_adapters(base(),WarmstartConfig('a'*64,rank=2,alpha=2,dropout=0))
            trained.save_pretrained(root/'refs',selected_adapters=list(ACTORS),safe_serialization=True,save_embedding_layers=False)
            backend=CollectionBackend.__new__(CollectionBackend)
            backend.model=load_frozen_adapters(base(),[root/'refs'/name for name in ACTORS])
            backend.model.generation_config.forced_eos_token_id=0
            backend.torch=torch;backend.tokenizer=Tokenizer();backend.calls=[];backend.generation_tokens={}
            runtime=CollectionRuntime(digest(cfg),1729)
            backend.config=dc.replace(runtime,model=dc.replace(runtime.model,device='cpu',
                adapters=tuple(AdapterConfig(name,str(root/'refs'/name),h) for name,h in zip(ACTORS,cfg.reference_hashes))))
            backend.identity={'snapshot':digest('fixture-team'),'template_hash':digest('fixture-template')}
            backend.base_identity={'snapshot':cfg.base_snapshot}
            backend.scorer=FrozenScorer(backend.model,backend.tokenizer,backend.base_identity,cfg.reference_hashes)
            backend.versions=[(n,p,p._version) for n,p in backend.model.named_parameters()]
            before={n:p.detach().clone() for n,p in backend.model.named_parameters()}
            previous=backend.model.active_adapter
            journal=JournalBackend(backend,root/'run',plan['budget']);journal.begin_record(digest('record'))
            task=pool[0][0]
            for actor,phase,cap in [('agent-0','private',256),('agent-2','revision',256),('base','final',64)]:
                request=Request(task,private_prompt(task,''),actor,phase,1,cap,phase=='final')
                journal.generate(request)
                self.assertEqual(backend.model.active_adapter,previous)
                backend.assert_unchanged()
            for n,p in backend.model.named_parameters():self.assertTrue(torch.equal(before[n],p),n)
            self.assertEqual(backend.scorer.forwards,[])
            self.assertEqual(len(backend.calls),3)
