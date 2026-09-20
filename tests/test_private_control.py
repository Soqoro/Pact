import contextlib
import copy
import dataclasses as dc
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from pact.cli import main
from pact.protocol import Protocol
from pact.training.collection_config import CollectionRuntime
from pact.training.feasibility import read_review
from pact.training.private_control import (PrivateControlConfig,private_control_plan,private_report,
    run_private_control,restore_private_control)
from pact.training.receiver_plan import receiver_feasibility_plan
from pact.util import canonical,digest,file_hash,node_seed,read_json,write_json
from test_receiver import FixtureBackend
from test_receiver_plan import fixtures


def fixture():
    cfg,pool,warm=fixtures()
    with patch('pact.training.receiver_plan.read_training_data',side_effect=[pool,warm]):
        parent=receiver_feasibility_plan(cfg,'unused','unused')
    tasks={t.task_id:t for t in pool[0]}; labels=pool[1]
    selected=[tasks[e['task_id']] for e in parent['selection']['selected']]
    runtime=CollectionRuntime(digest(cfg),1729);backend=FixtureBackend(runtime,cfg)
    proto=Protocol(runtime,backend)
    recipe={'plan_hash':digest(parent),'source':{'dirty':False}}
    source={'plan.json':parent,'manifest.json':{'status':'receiver_feasibility_complete_local',
        'completed_records':48,'recipe':recipe,'recipe_hash':digest(recipe)},'report.json':{'complete':True},
        'model_identity.json':{'actors':backend.identity,'base':backend.base_identity},
        'tasks.json':[dc.asdict(t) for t in selected],
        'labels.json':{t.task_id:dc.asdict(labels[t.task_id]) for t in selected}}
    source['model_identity.json']['actors']['adapters']=[{'sha256':h} for h in cfg.reference_hashes]
    for task in selected:
        packets=[]
        for agent in range(3):
            from pact.protocol import private_prompt
            packet=proto.packet(task,agent,'private',private_prompt(task,''),
                                node_seed(node_seed(1729,task.task_id,'trajectory'),'private',agent))
            packets.append(dc.asdict(packet))
            source[f'calls/shards/{digest(packet.call)}.json']={'call':dc.asdict(packet.call),
                                                              'tokens':dict(backend.last_generation)}
        for condition in ('clean','exchange'):
            key=digest([task,condition])
            source[f'shards/{key}.json']={'trajectory':{'task':dc.asdict(task),'private':packets,'condition':condition}}
    config=PrivateControlConfig('a'*64,parent['selection_hash'])
    with patch('pact.training.private_control.read_receiver_review',return_value=source):
        plan=private_control_plan(config,'unused')
    return config,cfg,source,plan


@contextlib.contextmanager
def execution(config,parent,plan,backends,mode='mixed'):
    def create(runtime,*args):
        b=FixtureBackend(runtime,parent,mode=mode);backends.append(b);return b
    with patch('pact.training.private_control.private_control_plan',return_value=plan), \
         patch('pact.training.private_control.runtime_fingerprint',return_value=parent.runtime_fingerprint), \
         patch('pact.training.private_control.verify_references'), \
         patch('pact.training.private_control.CollectionBackend',side_effect=create), \
         contextlib.redirect_stdout(io.StringIO()):
        yield


def run(cfg,root,**kw):
    return run_private_control(cfg,'unused','unused',root,Path('unused'),**kw)


class PrivateControlTests(unittest.TestCase):
    def test_plan_seed_only_and_reject_source_tampering(self):
        cfg,parent,source,plan=fixture()
        self.assertEqual(len(plan['requests']),72)
        self.assertEqual(plan['budget']['generated_tokens_upper_bound'],18432)
        for item in plan['requests']:
            self.assertEqual(item['seed'],node_seed(node_seed(1730,item['task']['task_id'],'trajectory'),'private',item['agent']))
            self.assertNotEqual(item['seed'],item['baseline_call']['seed'])
            self.assertNotIn('gold',canonical(item['baseline_call']['messages']))
        for mutate in ('label','seed','prompt','split','selection'):
            changed=copy.deepcopy(source)
            if mutate=='label':next(iter(changed['labels.json'].values()))['answer_id']='B'
            elif mutate=='selection':changed['plan.json']['selection']['selected'][0]['task_id']='changed'
            elif mutate=='split':changed['tasks.json'][0]['split']='validation'
            else:
                record=next(v for k,v in changed.items() if k.startswith('shards/'))
                call=record['trajectory']['private'][0]['call']
                call['seed' if mutate=='seed' else 'rendered_prompt']='changed'
            with patch('pact.training.private_control.read_receiver_review',return_value=changed):
                with self.assertRaises((ValueError,KeyError)):private_control_plan(cfg,'unused')
        with self.assertRaises(ValueError):dc.replace(cfg,generation_seed=1731).validate()

    def test_call_pause_resume_and_zero_call_repeat(self):
        cfg,parent,source,plan=fixture();backends=[]
        with tempfile.TemporaryDirectory() as tmp,execution(cfg,parent,plan,backends):
            root=Path(tmp)/'run'
            paused=run(cfg,root,stop_after=2)
            self.assertEqual(paused['status'],'interrupted_at_call_boundary')
            partial=read_json(root/'partial_report.json')
            self.assertEqual(partial['completed_records'],2)
            self.assertEqual(partial['summary']['all']['control']['tasks'],0)
            before={p.name:file_hash(p) for p in (root/'calls/shards').iterdir()}
            done=run(cfg,root,resume=True)
            self.assertEqual(done['status'],'private_support_complete_local',done)
            self.assertEqual(done['committed_calls'],72)
            self.assertEqual(sum(len(b.calls) for b in backends),72)
            for name,h in before.items():self.assertEqual(file_hash(root/'calls/shards'/name),h)
            report=read_json(root/'report.json');report_hash=file_hash(root/'report.json')
            self.assertEqual(report['summary']['all']['control']['tasks'],24)
            self.assertFalse(report['training_pairs_exported']);self.assertFalse(report['full_pact_ready'])
            for b in backends:
                self.assertFalse(b.scorer.forwards)
                self.assertTrue(all(c.phase=='private' and c.actor!='base' for c in b.calls))
            repeat=run(cfg,root,resume=True)
            self.assertEqual(repeat['exit_code'],0,repeat)
            self.assertEqual(len(backends[-1].calls),0)
            self.assertEqual(file_hash(root/'report.json'),report_hash)

    def test_verified_restore_and_stale_snapshot_rejection(self):
        cfg,parent,_,plan=fixture();backends=[]
        with tempfile.TemporaryDirectory() as tmp,execution(cfg,parent,plan,backends):
            root=Path(tmp)/'run';persistent=Path(tmp)/'durable'
            paused=run(cfg,root,stop_after=2,persistent=persistent)
            self.assertTrue(paused['persistent_copy_verified'],paused)
            read_review(paused['path'],paused['sha256'])
            restored=Path(tmp)/'restored'
            restore_private_control(paused['persistent_snapshot'],restored)
            done=run(cfg,restored,resume=True,persistent=persistent)
            self.assertEqual(done['exit_code'],0,done)
            with self.assertRaisesRegex(ValueError,'latest snapshot'):
                restore_private_control(paused['persistent_snapshot'],Path(tmp)/'stale')
            latest=Path(done['persistent_snapshot'])
            self.assertTrue(latest.exists())

    def test_failed_call_cannot_regenerate_and_error_zip_survives(self):
        cfg,parent,_,plan=fixture();backends=[]
        with tempfile.TemporaryDirectory() as tmp,execution(cfg,parent,plan,backends,mode='crash'):
            root=Path(tmp)/'run';failed=run(cfg,root)
            self.assertEqual(failed['exit_code'],2)
            self.assertTrue(Path(failed['path']).exists())
            self.assertFalse(read_json(root/'manifest.json')['recovery_safe'])
            with self.assertRaisesRegex(ValueError,'Ambiguous attempted call'):run(cfg,root,resume=True)
            self.assertEqual(len(backends),1)

    def test_preflight_and_storage_fail_before_generation(self):
        cfg,parent,_,plan=fixture();backends=[]
        with tempfile.TemporaryDirectory() as tmp,execution(cfg,parent,plan,backends):
            with patch('pact.training.private_control.runtime_fingerprint',return_value='wrong'):
                failed=run(cfg,Path(tmp)/'mismatch')
            self.assertEqual(failed['exit_code'],2);self.assertEqual(len(backends),0)
            with patch('pact.training.private_control.sync_run',side_effect=TimeoutError('fixture deadline')):
                failed=run(cfg,Path(tmp)/'storage',persistent=Path(tmp)/'durable')
            self.assertEqual(failed['exit_code'],2)
            self.assertTrue(Path(failed['path']).exists());self.assertEqual(len(backends[-1].calls),0)
            with self.assertRaisesRegex(ValueError,'source/recipe'):
                run(dc.replace(cfg,source_bundle_sha256='b'*64),Path(tmp)/'storage',resume=True)

    def test_report_separate_draws_invalid_failure_and_partial_triples(self):
        _,_,_,plan=fixture();records=[]
        for i,item in enumerate(plan['requests'][:3]):
            records.append({'work_id':item['work_id'],'raw':'invalid' if i==0 else canonical({'answer':'B'}),
                            'call':{'stop_reason':'eos'}})
        report=private_report(plan,records)
        task=next(t for t in report['tasks'] if t['complete'])
        self.assertEqual(task['control']['correct_agents'],0)
        self.assertFalse(task['control']['unanimous_valid_answer'])
        self.assertEqual(task['control']['potential_clean_repair_contexts'],0)
        self.assertEqual(task['baseline']['correct_agents'],1)
        self.assertFalse(report['complete'])
        with self.assertRaises(ValueError):private_report(plan,records+records)

    def test_cli_default_never_loads_model(self):
        cfg,_,source,_=fixture()
        with tempfile.TemporaryDirectory() as tmp,patch('pact.training.private_control.read_receiver_review',return_value=source), \
             patch('pact.training.private_control.CollectionBackend',side_effect=AssertionError('must not load')), \
             contextlib.redirect_stdout(io.StringIO()) as output:
            config=Path(tmp)/'config.json';write_json(config,cfg);root=Path(tmp)/'run'
            code=main(['private-support-control','--config',str(config),'--bundle','unused',
                '--references-dir','unused','--run-dir',str(root)])
            self.assertEqual(code,0,output.getvalue());self.assertFalse(root.exists())
