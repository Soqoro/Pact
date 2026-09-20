"""Synthetic CPU safety tests; these outputs are not research results."""
import contextlib
import copy
import dataclasses as dc
import io
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from pact.cli import main
from pact.protocol import Protocol,private_prompt
from pact.training.collection_config import CollectionRuntime
from pact.training.curated_repair import CuratedRepairConfig,paired_contexts,curated_report
from pact.training.curated_runner import run_curated_repair,restore_curated_repair
from pact.util import canonical,digest,file_hash,read_json,write_json
from test_receiver import FixtureBackend
from test_receiver_plan import fixtures


def fixture():
    parent,pool,_=fixtures();config=CuratedRepairConfig('a'*64,'b'*64)
    backend=FixtureBackend(CollectionRuntime(digest(config),config.generation_seed),parent,mode='all_wrong')
    protocol=Protocol(backend.config,backend);contexts=[]
    tasks=pool[0][:2]
    for task in tasks:
        packets=tuple(protocol.packet(task,i,'private',private_prompt(task,''),i) for i in range(3))
        donor={'task_id':task.task_id,'agent':2,'raw':canonical({'answer':'A','justification':'Stored fixture.'}),
               'call_hash':digest('donor')}
        contexts.extend(paired_contexts(task,packets,donor,config))
    plan={'actor_recipe':dc.asdict(parent),'contexts':contexts,'contexts_hash':digest(contexts),
          'tasks':{t.task_id:dc.asdict(t) for t in tasks},'labels':{t.task_id:'A' for t in tasks},
          'models':{'actors':backend.identity,'base':backend.base_identity},'scope':'synthetic_fixture',
          'budget':{'generation_calls_upper_bound':32,'generated_tokens_upper_bound':8192}}
    return config,parent,plan


@contextlib.contextmanager
def execution(parent,plan,backends,mode='mixed',overflow=False):
    def create(runtime,*unused):
        backend=FixtureBackend(runtime,parent,mode=mode)
        backend.tokenizer.apply_chat_template=lambda messages,**kw:canonical([{'schema_version':1,**m} for m in messages])
        # Overflow only in the last context: earlier contexts must not generate.
        last=canonical(plan['contexts'][-1]['messages'])
        backend.tokenizer.encode=lambda text,**kw:([1]*4096 if overflow and text==last else [ord(c)+1 for c in text])
        backends.append(backend);return backend
    with patch('pact.training.curated_runner.curated_repair_plan',return_value=plan), \
         patch('pact.training.curated_runner.runtime_fingerprint',return_value=parent.runtime_fingerprint), \
         patch('pact.training.curated_runner.verify_references'), \
         patch('pact.training.curated_runner.CollectionBackend',side_effect=create), \
         contextlib.redirect_stdout(io.StringIO()):
        yield


def run(config,root,**kw):
    return run_curated_repair(config,'receiver','private','references',root,'cache',**kw)


class CuratedRunnerTests(unittest.TestCase):
    def test_pause_resume_and_repeat_preserve_32_calls(self):
        config,parent,plan=fixture();backends=[]
        with tempfile.TemporaryDirectory() as tmp,execution(parent,plan,backends):
            root=Path(tmp)/'run';paused=run(config,root,stop_after=2)
            self.assertEqual(paused['status'],'interrupted_at_call_boundary',paused)
            partial=read_json(root/'partial_report.json')
            self.assertEqual(partial['decision'],'incomplete');self.assertEqual(partial['paired_samples'],0)
            self.assertFalse(any(p['pair'] for p in partial['pools']))
            before={p.name:file_hash(p) for p in (root/'calls/shards').iterdir()}
            done=run(config,root,resume=True)
            self.assertEqual(done['status'],'curated_repair_complete_local',done)
            self.assertEqual(done['committed_calls'],32)
            self.assertEqual(sum(len(b.calls) for b in backends),32)
            for name,h in before.items():self.assertEqual(file_hash(root/'calls/shards'/name),h)
            report=read_json(root/'report.json');report_hash=file_hash(root/'report.json')
            self.assertEqual(report['paired_samples'],16);self.assertEqual(len(report['pools']),8)
            self.assertFalse(report['training_pairs_exported']);self.assertFalse(report['full_pact_ready'])
            for b in backends:
                self.assertFalse(b.scorer.forwards)
                self.assertTrue(all(c.phase=='revision' and c.actor!='base' for c in b.calls))
            repeat=run(config,root,resume=True)
            self.assertEqual(repeat['exit_code'],0,repeat);self.assertEqual(len(backends[-1].calls),0)
            self.assertEqual(file_hash(root/'report.json'),report_hash)

    def test_all_context_preflight_and_runtime_failure_precede_generation(self):
        config,parent,plan=fixture();backends=[]
        with tempfile.TemporaryDirectory() as tmp,execution(parent,plan,backends,overflow=True):
            failed=run(config,Path(tmp)/'overflow')
            self.assertEqual(failed['exit_code'],2,failed);self.assertEqual(len(backends[0].calls),0)
            self.assertFalse(list((Path(tmp)/'overflow/call-intents').glob('*')))
            with patch('pact.training.curated_runner.runtime_fingerprint',return_value='wrong'):
                failed=run(config,Path(tmp)/'runtime')
            self.assertEqual(failed['exit_code'],2);self.assertEqual(len(backends),1)

    def test_ambiguous_attempt_cannot_regenerate(self):
        config,parent,plan=fixture();backends=[]
        with tempfile.TemporaryDirectory() as tmp,execution(parent,plan,backends,mode='crash'):
            root=Path(tmp)/'run';failed=run(config,root)
            self.assertEqual(failed['exit_code'],2);self.assertTrue(Path(failed['path']).exists())
            self.assertFalse(read_json(root/'manifest.json')['recovery_safe'])
            with self.assertRaisesRegex(ValueError,'Ambiguous attempted call'):run(config,root,resume=True)
            self.assertEqual(len(backends),1)

    def test_restore_latest_safe_snapshot_and_storage_deadline(self):
        config,parent,plan=fixture();backends=[]
        with tempfile.TemporaryDirectory() as tmp,execution(parent,plan,backends):
            root=Path(tmp)/'run';durable=Path(tmp)/'durable'
            paused=run(config,root,stop_after=2,persistent=durable)
            self.assertTrue(paused['persistent_copy_verified'],paused)
            restored=Path(tmp)/'restored';restore_curated_repair(paused['persistent_snapshot'],restored)
            done=run(config,restored,resume=True,persistent=durable)
            self.assertEqual(done['exit_code'],0,done)
            with self.assertRaisesRegex(ValueError,'latest snapshot'):
                restore_curated_repair(paused['persistent_snapshot'],Path(tmp)/'stale')
            with patch('pact.training.curated_runner.sync_run',side_effect=TimeoutError('fixture deadline')):
                failed=run(config,Path(tmp)/'fail',persistent=Path(tmp)/'fail-drive')
            self.assertEqual(failed['exit_code'],2);self.assertTrue(Path(failed['path']).exists())
            self.assertEqual(len(backends[-1].calls),0)

    def test_single_class_arms_never_form_cross_arm_pairs_and_invalids_fail(self):
        from pact.artifacts import ShardStore
        config,parent,plan=fixture();backends=[]
        with tempfile.TemporaryDirectory() as tmp,execution(parent,plan,backends,mode='all_wrong'):
            root=Path(tmp)/'run';self.assertEqual(run(config,root)['exit_code'],0)
            records=ShardStore(root).records()
            arms={c['context_id']:c['arm'] for c in plan['contexts']}
            for r in records:
                if arms[r['context_id']]=='curated_help':
                    r['raw']=canonical({'answer':'A','justification':'Fixture.'});r['tokens']['raw']=r['raw']
                    r['tokens']['completion_ids']=[ord(c)+1 for c in r['raw']]+[0]
                    r['call']['output_tokens']=len(r['tokens']['completion_ids'])
            report=curated_report(plan,records)
            self.assertEqual(report['decision'],'curated_help_without_pairs')
            self.assertEqual(report['within_arm_pairs'],0);self.assertEqual(report['correct_count_delta'],16)
            r=next(r for r in records if arms[r['context_id']]=='curated_help')
            r['raw']='invalid';r['tokens']['raw']='invalid';r['tokens']['completion_ids']=[1,0];r['call']['output_tokens']=2
            report=curated_report(plan,records)
            self.assertEqual(report['within_arm_pairs'],0);self.assertEqual(report['correct_count_delta'],15)
            self.assertEqual(sum(p['invalid_count'] for p in report['pools']),1)
            changed=copy.deepcopy(records);changed[0]['call']['seed']+=1
            with self.assertRaises(ValueError):curated_report(plan,changed)
            with self.assertRaises(ValueError):curated_report(plan,records+records)

    def test_resume_rejects_changed_recipe_and_token_prefix(self):
        config,parent,plan=fixture();backends=[]
        with tempfile.TemporaryDirectory() as tmp,execution(parent,plan,backends):
            root=Path(tmp)/'run';run(config,root,stop_after=2)
            with self.assertRaisesRegex(ValueError,'source/recipe'):
                run(dc.replace(config,private_bundle_sha256='c'*64),root,resume=True)
            prefixes=read_json(root/'prefixes.json')
            next(iter(prefixes.values()))['prompt_ids'][0]+=1
            write_json(root/'prefixes.json',prefixes)
            failed=run(config,root,resume=True)
            self.assertEqual(failed['exit_code'],2)
            self.assertEqual(len(backends[-1].calls),0)

    def test_within_arm_pairs_prefer_matching_32_token_bins(self):
        from pact.artifacts import ShardStore
        config,parent,plan=fixture();backends=[]
        with tempfile.TemporaryDirectory() as tmp,execution(parent,plan,backends):
            root=Path(tmp)/'run';run(config,root)
            records=ShardStore(root).records()
            lengths=[31,32,40,65]
            for r in records:
                i=r['sample_index'];answer='A' if i in (0,2) else 'B'
                r['raw']=canonical({'answer':answer,'justification':'Fixture.'})
                r['tokens']['raw']=r['raw'];r['tokens']['completion_ids']=[1]*(lengths[i]-1)+[0]
                r['call']['output_tokens']=lengths[i]
            report=curated_report(plan,records)
            self.assertEqual(report['within_arm_pairs'],8)
            self.assertEqual(report['curated_repair_pairs'],4)
            for pool in report['pools']:
                self.assertEqual(pool['pair'],{'positive_index':2,'negative_index':1,'length_matched':True})
            # Identical serialized text is insufficient if token prefixes differ.
            changed=copy.deepcopy(records);changed[0]['tokens']['prompt_ids'][0]+=1
            with self.assertRaisesRegex(ValueError,'prefix'):curated_report(plan,changed)

    def test_cli_defaults_to_plan_without_model_or_run_directory(self):
        config,_,plan=fixture()
        with tempfile.TemporaryDirectory() as tmp,contextlib.redirect_stdout(io.StringIO()):
            path=Path(tmp)/'config.json';write_json(path,config);root=Path(tmp)/'run'
            args=['curated-repair','--config',str(path),'--receiver-bundle','r','--private-bundle','p',
                  '--references-dir','refs','--run-dir',str(root)]
            with patch('pact.training.curated_repair.curated_repair_plan',return_value=plan), \
                 patch('pact.training.curated_runner.CollectionBackend',side_effect=AssertionError('no model')):
                self.assertEqual(main(args),0);self.assertFalse(root.exists())
