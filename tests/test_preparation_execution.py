"""Synthetic orchestration tests; no neural performance claims."""
import contextlib
import copy
import dataclasses as dc
import io
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch
from pact.artifacts import ShardStore
from pact.backends import Request
from pact.cli import main
from pact.protocol import Protocol,private_prompt
from pact.schemas import Message,task_from_dict
from pact.training.actor_preparation import ActorPreparationConfig,select_preparation_tasks
from pact.training.collection_config import CollectionRuntime
from pact.training.curated_repair import paired_contexts,CuratedRepairConfig,curated_requests,curated_report
from pact.training.preparation_runner import PreparationTrainingConfig,training_inputs,run_preparation_training,preparation_references
from pact.training.preparation_probe import probe_plan,probe_report,run_preparation_probe,restore_preparation_probe
from pact.training.warmstart_config import WarmstartConfig
from pact.util import canonical,digest,read_json,write_json,file_hash
from test_receiver import FixtureBackend
from test_receiver_plan import fixtures
from test_private_control import fixture as private_fixture


def training_fixture():
    _,pool,warm=fixtures();tasks,labels,m,_=pool
    selected=select_preparation_tasks(tasks,m,warm[2],m['selected'][20:32]+m['selected'][620:632],20260920)
    ids={e['task_id'] for e in selected};tasks=[t for t in tasks if t.task_id in ids]
    training={'agent_task_ids':[sorted(ids,key=lambda t:(digest([seed,t]),t)) for seed in (1729,1730,1731)]}
    return {'selection':selected,'selection_hash':digest(selected),'training':training,'training_recipe_hash':digest(training),
        'training_tasks':[dc.asdict(t) for t in tasks],'training_labels':{k:dc.asdict(v) for k,v in labels.items() if k in ids},
        'baseline_models':{'base':{'snapshot':'base','runtime_fingerprint':'runtime'}}}


def probe_fixture():
    _,old_parent,_,private=private_fixture()
    cfg=ActorPreparationConfig(*['a'*64]*5)
    runtime=CollectionRuntime(digest(cfg),20260920);backend=FixtureBackend(runtime,old_parent,mode='all_wrong')
    contexts=[];tasks={};labels={};prefixes={};records=[]
    for item in private['requests'][::3][:2]:
        task=task_from_dict(item['task']);tasks[task.task_id]=item['task'];labels[task.task_id]=item['gold']
        proto=Protocol(runtime,backend)
        packets=tuple(proto.packet(task,i,'private',private_prompt(task,''),i) for i in range(3))
        donor={'task_id':task.task_id,'agent':2,'raw':canonical({'answer':'A','justification':'Fixture.'}),'call_hash':digest('donor')}
        contexts+=paired_contexts(task,packets,donor,CuratedRepairConfig('a'*64,'b'*64))
    cp={'contexts':contexts,'tasks':tasks,'labels':labels,'models':private['models'],'scope':'synthetic_fixture'}
    for item in curated_requests(cp):
        c=item['context'];messages=tuple(Message(m['role'],m['content']) for m in c['messages'])
        raw,call=backend.generate(Request(task_from_dict(tasks[c['task_id']]),messages,f"agent-{c['recipient']}",'revision',item['seed'],256,False))
        prefixes[c['context_id']]={'rendered_prompt':call.rendered_prompt,'prompt_ids':backend.last_generation['prompt_ids'],'context_hash':call.context_hash}
        records.append({'work_id':item['work_id'],'request_hash':digest(item),'context_id':c['context_id'],
            'sample_index':item['sample_index'],'raw':raw,'call':dc.asdict(call),'tokens':dict(backend.last_generation)})
    design={'private_probe_requests':private['requests'],'receiver_contexts':contexts,'receiver_prefixes':prefixes,
            'baseline_models':private['models'],'baseline_receiver_report':curated_report(cp,records),'scope':'synthetic_fixture',
            'budget':{'generation_calls_upper_bound':104,'generated_tokens_upper_bound':26624}}
    parent=SimpleNamespace(reference_hashes=tuple(digest(['new',i]) for i in range(3)),reference_manifest_hash=digest('new refs'),
        base_snapshot=old_parent.base_snapshot,runtime_fingerprint=old_parent.runtime_fingerprint,reference_final_step=90)
    return cfg,design,parent


@contextlib.contextmanager
def execution(parent,backends,mode='mixed'):
    def create(runtime,*args):
        b=FixtureBackend(runtime,parent,mode=mode)
        b.identity['snapshot']=digest({'base':parent.base_snapshot,'actors':parent.reference_hashes})
        b.tokenizer.apply_chat_template=lambda messages,**kw:canonical([{'schema_version':1,**m} for m in messages])
        b.tokenizer.encode=lambda text,**kw:[ord(c)+1 for c in text]
        backends.append(b);return b
    with patch('pact.training.preparation_probe.preparation_references',return_value=parent), \
         patch('pact.training.preparation_probe.runtime_fingerprint',return_value=parent.runtime_fingerprint), \
         patch('pact.training.preparation_probe.verify_references'), \
         patch('pact.training.preparation_probe.CollectionBackend',side_effect=create),contextlib.redirect_stdout(io.StringIO()):
        yield


def run(cfg,design,tmp,**kwargs):
    tmp=Path(tmp);training=tmp/'training';training.mkdir(exist_ok=True)
    write_json(training/'fixture.json',{'synthetic':True})
    return run_preparation_probe(cfg,design,training,tmp/'run','cache',persistent=tmp/'drive/probe',**kwargs)


class PreparationExecutionTests(unittest.TestCase):
    def test_new_training_bounds_orders_and_old_limits(self):
        plan=training_fixture();config,prepared=training_inputs(plan)
        self.assertEqual(config.steps_per_agent*3,90)
        self.assertEqual(len(prepared[0]),120)
        for order in prepared[2]:self.assertEqual(sorted(order),list(range(120)))
        with self.assertRaises(ValueError):dc.replace(WarmstartConfig('a'*64),steps_per_agent=30).validate()
        for field,value in [('steps_per_agent',31),('effective_batch',8),('learning_rate',2e-5),('purpose','other')]:
            with self.assertRaises(ValueError):dc.replace(config,**{field:value}).validate()
        changed=copy.deepcopy(plan);changed['training_tasks'][0]['question']='changed'
        with self.assertRaises(ValueError):training_inputs(changed)
        changed=copy.deepcopy(plan);changed['training']['agent_task_ids'][0].reverse();changed['training_recipe_hash']=digest(changed['training'])
        with self.assertRaises(ValueError):training_inputs(changed)

    def test_training_failure_still_produces_local_zip_and_same_design_resume_required(self):
        plan=training_fixture()
        with tempfile.TemporaryDirectory() as tmp,contextlib.redirect_stdout(io.StringIO()):
            root=Path(tmp)/'training'
            with patch('pact.training.preparation_runner._run_prepared_warmstart',side_effect=RuntimeError('preflight overflow')):
                result=run_preparation_training(plan,root,'cache',persistent=Path(tmp)/'drive')
            self.assertEqual(result['exit_code'],2);self.assertTrue(Path(result['path']).exists())
            self.assertFalse((root/'checkpoints').exists())
            changed={**plan,'scope':'changed'}
            with self.assertRaisesRegex(ValueError,'design changed'):
                run_preparation_training(changed,root,'cache',persistent=Path(tmp)/'drive',resume=True)
            with self.assertRaises((ValueError,FileNotFoundError)):preparation_references(plan,root)

    def test_training_boundary_handoff_restore_final_gate_and_exact_schedule(self):
        from pact.training.checkpoints import commit_checkpoint,latest_checkpoint
        from pact.training.colab import restore_snapshot
        from pact.environment import code_identity
        plan=training_fixture();executed=[]
        def fake_engine(config,prepared,root,cache,*,resume,stop_after,expected_base,checkpoint_callback,**kw):
            recipe={'config':dc.asdict(config),'data_manifest_hash':prepared[3]['data_manifest_hash'],
                    'source':code_identity(Path.cwd())}
            identity={'recipe_hash':digest(recipe),'model_snapshot':'base','runtime_fingerprint':'runtime'}
            if resume:
                _,last=latest_checkpoint(root/'checkpoints',identity);start=last['step']
            else:
                start=0
                write_json(root/'run.json',{'recipe':recipe,'recipe_hash':digest(recipe),'identity':identity,'plan':prepared[3]})
                write_json(root/'examples.json',{'synthetic':True})
                commit_checkpoint(root/'checkpoints',step=0,identity=identity,tree={},write_tensors=lambda p:p.write_bytes(b'fixture'))
            finish=min(90,start+stop_after) if stop_after else 90
            for step in range(start+1,finish+1):
                commit_checkpoint(root/'checkpoints',step=step,identity=identity,tree={},write_tensors=lambda p:p.write_bytes(b'fixture'))
                executed.append(step);checkpoint_callback(step)
            logs=[{'step':i+1,'agent':f'agent{i//30}','agent_step':i%30+1,
                   'task_ids':plan['training']['agent_task_ids'][i//30][(i%30)*4:(i%30+1)*4]} for i in range(finish)]
            result={'status':'warmstart_updates_complete' if finish==90 else 'interrupted_at_optimizer_boundary',
                    'completed_steps':finish,'logs':logs,'scientific_status':'train_only_actor_preparation_120'}
            write_json(root/'status.json',result)
            if finish==90:write_json(root/'references/references.json',{'schema_version':1,'identity':identity,'final_step':90,
                'references':[{'sha256':digest(i)} for i in range(3)]})
            return result
        with tempfile.TemporaryDirectory() as tmp,contextlib.redirect_stdout(io.StringIO()), \
             patch('pact.training.preparation_runner._run_prepared_warmstart',side_effect=fake_engine), \
             patch('pact.training.preparation_runner.verify_references'):
            root=Path(tmp)/'training';durable=Path(tmp)/'drive'
            first=run_preparation_training(plan,root,'cache',persistent=durable,stop_after=1)
            self.assertTrue(first['persistent_copy_verified'],first)
            with self.assertRaisesRegex(ValueError,'completed matching'):preparation_references(plan,root)
            restored=Path(tmp)/'restored';restore_snapshot(first['persistent_snapshot'],restored)
            done=run_preparation_training(plan,restored,'cache',persistent=durable,resume=True)
            self.assertEqual(done['exit_code'],0,done);self.assertEqual(executed,list(range(1,91)))
            self.assertEqual(preparation_references(plan,restored).reference_final_step,90)
            repeat=run_preparation_training(plan,restored,'cache',persistent=durable,resume=True)
            self.assertEqual(repeat['exit_code'],0);self.assertEqual(executed,list(range(1,91)))
            status=read_json(restored/'status.json');status['logs'][0]['task_ids'].reverse();write_json(restored/'status.json',status)
            with self.assertRaisesRegex(ValueError,'update log'):preparation_references(plan,restored)

    def test_probe_pause_resume_104_calls_final_identity_and_zero_call_repeat(self):
        cfg,design,parent=probe_fixture();backends=[]
        with tempfile.TemporaryDirectory() as tmp,execution(parent,backends):
            first=run(cfg,design,tmp,stop_after=74)
            self.assertEqual(first['status'],'interrupted_at_call_boundary',first)
            root=Path(tmp)/'run';partial=read_json(root/'partial_report.json')
            self.assertTrue(partial['private']['complete']);self.assertFalse(partial['receiver']['complete'])
            self.assertEqual(len(partial['receiver_checkpoint_comparisons']),2)
            # Simulate an existing probe produced by the reviewed pre-repair source.
            from pact.training.preparation_restore import PRIOR_SOURCE
            manifest=read_json(root/'manifest.json')
            manifest['recipe']['source']=PRIOR_SOURCE
            manifest['recipe_hash']=digest(manifest['recipe'])
            manifest['identity']['recipe_hash']=manifest['recipe_hash']
            write_json(root/'manifest.json',manifest)
            old={p.name:file_hash(p) for p in (root/'calls/shards').iterdir()}
            final=run(cfg,design,tmp,resume=True)
            self.assertEqual(final['status'],'preparation_probe_complete_local',final)
            migration=read_json(next((root/'source-migrations').glob('*.json')))
            self.assertEqual(migration['committed_calls'],74)
            self.assertTrue(migration['no_call_budget_reset'])
            report=read_json(root/'report.json');self.assertEqual(report['completed_records'],104)
            self.assertEqual(sum(len(b.calls) for b in backends),104)
            self.assertEqual(len(report['receiver_checkpoint_comparisons']),32)
            self.assertFalse(report['full_pact_ready']);self.assertFalse(report['training_pairs_exported'])
            for name,h in old.items():self.assertEqual(file_hash(root/'calls/shards'/name),h)
            repeat=run(cfg,design,tmp,resume=True)
            self.assertEqual(repeat['exit_code'],0)
            self.assertEqual(len(backends[-1].calls),0)
            all_calls=[c for b in backends for c in b.calls]
            self.assertEqual(sum(c.phase=='private' for c in all_calls),72)
            self.assertEqual(sum(c.phase=='revision' for c in all_calls),32)
            self.assertTrue(all(not b.scorer.forwards for b in backends))
            restored=Path(tmp)/'restored';restore_preparation_probe(repeat['persistent_snapshot'],restored)
            self.assertEqual(len(ShardStore(restored).records()),104)
            with self.assertRaisesRegex(ValueError,'latest snapshot'):
                restore_preparation_probe(first['persistent_snapshot'],Path(tmp)/'stale')

    def test_probe_context_mismatch_before_generation_and_ambiguous_attempt(self):
        cfg,design,parent=probe_fixture();backends=[]
        with tempfile.TemporaryDirectory() as tmp,execution(parent,backends):
            changed=copy.deepcopy(design);next(iter(changed['receiver_prefixes'].values()))['prompt_ids'][0]+=1
            failed=run(cfg,changed,tmp)
            self.assertEqual(failed['exit_code'],2);self.assertEqual(len(backends[0].calls),0)
        with tempfile.TemporaryDirectory() as tmp,execution(parent,backends,mode='crash'):
            failed=run(cfg,design,tmp)
            self.assertEqual(failed['exit_code'],2);self.assertTrue(Path(failed['path']).exists())
            with self.assertRaisesRegex(ValueError,'Ambiguous attempted call'):run(cfg,design,tmp,resume=True)

    def test_cli_plan_never_trains(self):
        cfg=ActorPreparationConfig(*['a'*64]*5)
        with tempfile.TemporaryDirectory() as tmp,contextlib.redirect_stdout(io.StringIO()):
            p=Path(tmp)/'config.json';write_json(p,cfg)
            args=['actor-preparation','--config',str(p),'--stage','training']
            for name in ('data-dir','warmstart-data-dir','receiver-bundle','private-bundle','curated-bundle','run-dir','persistent'):
                args+=['--'+name,str(Path(tmp)/name)]
            with patch('pact.training.actor_preparation.actor_preparation_plan',return_value={'training_executed':False}), \
                 patch('pact.training.preparation_runner._run_prepared_warmstart',side_effect=AssertionError('must not execute')):
                self.assertEqual(main(args),0);self.assertFalse((Path(tmp)/'run-dir').exists())
