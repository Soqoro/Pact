import contextlib
import dataclasses as dc
import hashlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import zipfile

from pact.cli import main
from pact.schemas import TaskInput, TaskLabel, Option, Message, CallRecord
from pact.training.bank import BankRow, ReceiverContext, Candidate, ScoredBank, WarmstartReference
from pact.training.feasibility import FeasibilityConfig, prepare_feasibility, read_review, collect_control, diagnose, run_feasibility, restore_feasibility, copy_source_bundle
from pact.training.preferences import build_preferences
from pact.util import canonical, digest, file_hash, read_json, write_json


def encode(text):return [ord(c)+1 for c in text]


def fixture_bundle(root):
    """Invented training-shaped records solely for offline control-path tests."""
    base={'snapshot':digest('fixture-base'),'runtime_fingerprint':digest('fixture-runtime'),'adapters':[]}
    actors={'snapshot':digest('fixture-actors')}
    rows=[];contexts=[];files={}
    for family in range(2):
        task=TaskInput(f'mock:{family}',f'mock_{family}','train',str(family),'0'*40,digest(['source',family]),
                       'Synthetic choice?',(Option('A','First','A'),Option('B','Second','B')))
        for condition in ('clean','early','exchange'):
            row_id=digest([task,condition]);eligible=family==1 and condition!='early'
            row=BankRow(row_id,task.task_id,'train',task.source_hash,digest(TaskLabel(task.task_id,'A')),
                ('A','B'),'A',(eligible,False,False),(1.,1.,1.),(None,None,None),(None,None,None))
            rows.append(row);tokens={};private=[];replays=[];probes=[]
            def packet(agent,phase,index,answer):
                messages=(Message('system','Synthetic fixture; return answer and justification.'),
                          Message('user',canonical({'question':task.question,'context':f'{family}/{condition}/{agent}/{phase}'})))
                prompt=canonical([dc.asdict(m) for m in messages]);raw=canonical({'answer':answer,'justification':'Fixture.'})
                ids=encode(raw)+[0]
                params={'max_new_tokens':256,'do_sample':True,'temperature':.7,'top_p':.8,'top_k':20}
                call=CallRecord(f'agent-{agent}',phase,actors['snapshot'],index,messages,prompt,digest(prompt),digest('template'),
                    canonical(params),len(encode(prompt)),len(ids),'eos',0.)
                tokens[digest(call)]={'prompt_ids':encode(prompt),'completion_ids':ids,'raw':raw,'context_hash':digest(prompt)}
                return {'call':dc.asdict(call),'raw':raw}
            for agent in range(3):
                private.append(packet(agent,'private',100,'A' if eligible and agent==0 else 'B'))
                replays.append({'candidates':[packet(agent,'private',i,'B') for i in range(4)]})
                candidates=[packet(agent,'revision',i,'B') for i in range(4)] if eligible else []
                example=packet(agent,'revision',101,'B')
                prompt=example['call']['rendered_prompt'];prefix=encode(prompt)
                contexts.append(ReceiverContext(row_id,agent,prompt,tuple(prefix),eligible and agent!=0,True,
                    tuple(Candidate(p['raw'],digest(prompt),tuple(prefix),tuple(tokens[digest(p['call'])]['completion_ids']),'eos') for p in candidates)))
                probes.append({'candidates':candidates})
            files[f'shards/{row_id}.json']={'work_id':row_id,'row':dc.asdict(row),'trajectory':{'task':dc.asdict(task),
                'condition':condition,'private':private},'replays':replays,'receiver_probes':probes,'generation_tokens':tokens}
    bank=ScoredBank(1,'training','train',actors['snapshot'],base['snapshot'],digest('data'),'0'*40,digest('template'),
        'float32',base['runtime_fingerprint'],0,tuple(WarmstartReference(i,'warm_start_adapter',digest(['ref',i])) for i in range(3)),
        tuple(rows),tuple(contexts))
    files.update({'bank.json':bank,'preferences.json':build_preferences(bank),'model_identity.json':{'base':base,'actors':actors},
        'manifest.json':{'status':'collection_complete_local','completed_records':6,'bank_hash':bank.identity,
                         'recipe':{'data_manifest_hash':bank.data_manifest_hash}},
        'HANDOFF.json':{'kind':'training_bank_engineering_review'}})
    payload={n:canonical(v).encode() for n,v in files.items()}
    payload['review_checksums.json']=canonical({n:hashlib.sha256(v).hexdigest() for n,v in payload.items()}).encode()
    bundle=root/'fixture.zip'
    with zipfile.ZipFile(bundle,'w',zipfile.ZIP_DEFLATED) as z:
        for n,v in payload.items():z.writestr(n,v)
    return bundle,FeasibilityConfig(file_hash(bundle),bank.identity)


class FixtureBase:
    def __init__(self,plan):
        self.plan=plan;self.identity={**plan['models']['base'],'backend':'mock'};self.calls=[]
    def generate(self,request):
        assert request.actor=='base' and request.deterministic is False
        assert isinstance(request.task,TaskInput) and not hasattr(request.task,'gold')
        prompt=canonical([dc.asdict(m) for m in request.messages])
        raw=canonical({'answer':'A' if request.seed%2==0 else 'B','justification':'Synthetic base control.'})
        ids=encode(raw)+[0]
        call=CallRecord('base',request.phase,self.identity['snapshot'],request.seed,request.messages,prompt,digest(prompt),
            digest('template'),canonical({'do_sample':True,'max_new_tokens':256}),len(encode(prompt)),len(ids),'eos',0.)
        self.calls.append(call)
        self.last_generation={'prompt_ids':encode(prompt),'completion_ids':ids,'raw':raw,'context_hash':digest(prompt)}
        return raw,call
    def resource_usage(self):return {'compute_units':None,'peak_allocated_bytes':None,'peak_reserved_bytes':None}


class FeasibilityTests(unittest.TestCase):
    def test_plan_pins_counts_and_cli_never_loads_model(self):
        with tempfile.TemporaryDirectory() as tmp,contextlib.redirect_stdout(io.StringIO()):
            root=Path(tmp);bundle,cfg=fixture_bundle(root);plan=prepare_feasibility(cfg,bundle)
            self.assertEqual(len(plan['requests']),54)
            self.assertEqual(plan['summary']['generated_tokens_upper_bound'],13824)
            self.assertEqual(plan['summary']['receiver_contexts'],{'hold':2,'repair':4})
            write_json(root/'config.json',cfg)
            with patch('pact.training.feasibility.TransformersBackend') as model:
                self.assertEqual(main(['preference-diagnostic','--config',str(root/'config.json'),'--bundle',str(bundle),
                    '--run-dir',str(root/'absent')]),0)
                model.assert_not_called();self.assertFalse((root/'absent').exists())
            with self.assertRaises(ValueError):prepare_feasibility(dc.replace(cfg,source_bank_hash=digest('other')),bundle)
            with self.assertRaises(ValueError):dc.replace(cfg,schema_version=True).validate()

    def test_archive_hash_corruption_and_traversal_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);bundle,cfg=fixture_bundle(root)
            with self.assertRaises(ValueError):read_review(bundle,'0'*64)
            with zipfile.ZipFile(bundle,'a') as z:z.writestr('../escape.json','{}')
            with self.assertRaises(ValueError):read_review(bundle,file_hash(bundle))
            bundle.unlink();bundle,cfg=fixture_bundle(root)
            with zipfile.ZipFile(bundle) as z:data={n:z.read(n) for n in z.namelist()}
            data['bank.json']=b'{}'
            with zipfile.ZipFile(bundle,'w') as z:
                for n,v in data.items():z.writestr(n,v)
            with self.assertRaises(ValueError):read_review(bundle,file_hash(bundle))
            link=root/'link.zip';link.symlink_to(bundle)
            with self.assertRaises(ValueError):read_review(link,file_hash(bundle))

    def test_timed_source_copy_reuses_verified_bytes_and_rejects_overwrite(self):
        with tempfile.TemporaryDirectory() as tmp,contextlib.redirect_stdout(io.StringIO()):
            root=Path(tmp);bundle,cfg=fixture_bundle(root);destination=root/'scratch/source.zip'
            copied=copy_source_bundle(bundle,destination,cfg,timeout_seconds=10)
            self.assertEqual(copied['sha256'],file_hash(destination))
            self.assertTrue(copy_source_bundle(bundle,destination,cfg)['reused'])
            destination.write_bytes(b'corrupt existing file')
            with self.assertRaises(ValueError):copy_source_bundle(bundle,destination,cfg)
            self.assertEqual(destination.read_bytes(),b'corrupt existing file')
            with patch('pact.training.feasibility.storage_operation',side_effect=TimeoutError('fixture stall')):
                with self.assertRaises(TimeoutError):copy_source_bundle(bundle,root/'scratch/timeout.zip',cfg)
            self.assertFalse((root/'scratch/timeout.zip').exists())

    def test_collection_resume_same_requests_and_diagnostic_pair_separation(self):
        with tempfile.TemporaryDirectory() as tmp,contextlib.redirect_stdout(io.StringIO()):
            root=Path(tmp);bundle,cfg=fixture_bundle(root);plan=prepare_feasibility(cfg,bundle)
            first=FixtureBase(plan);partial=collect_control(plan,first,root/'run',stop_after=7)
            self.assertEqual(len(partial),7)
            before={p.name:file_hash(p) for p in (root/'run/shards').iterdir()}
            fresh=FixtureBase(plan);complete=collect_control(plan,fresh,root/'run')
            self.assertEqual(len(complete),54);self.assertEqual(len(fresh.calls),47)
            for n,h in before.items():self.assertEqual(file_hash(root/'run/shards'/n),h)
            report=diagnose(plan,complete)
            self.assertFalse(report['training_pairs_exported']);self.assertFalse(report['training_executed'])
            self.assertEqual(report['base_receiver_pair_contexts'],{'hold':2,'repair':4})
            self.assertFalse(any(g['actor_pair_available'] for g in report['groups']))
            # Invalid completions cannot serve as negatives even with a positive.
            revision={i['request_id'] for i in plan['requests'] if i['phase']=='revision'}
            altered=[{**r,'raw':'malformed'} if r['request_id'] in revision and json.loads(r['raw'])['answer']=='B' else r for r in complete]
            self.assertEqual(diagnose(plan,altered)['base_receiver_pair_contexts'],{'hold':0,'repair':0})
            shard=next((root/'run/shards').glob('*.json'));shard.write_text('{}')
            with self.assertRaises(ValueError):collect_control(plan,FixtureBase(plan),root/'run')

    def test_changed_prompt_prefix_fails_before_shard_publication(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);bundle,cfg=fixture_bundle(root);plan=prepare_feasibility(cfg,bundle)
            backend=FixtureBase(plan);original=backend.generate
            def wrong(request):
                result=original(request);backend.last_generation['prompt_ids']=[999];return result
            backend.generate=wrong
            with self.assertRaises(ValueError):collect_control(plan,backend,root/'run')
            self.assertEqual(list((root/'run/shards').glob('*.sha256')),[])

    def test_runner_failure_resume_snapshot_restore_and_idempotence(self):
        with tempfile.TemporaryDirectory() as tmp,contextlib.redirect_stdout(io.StringIO()):
            root=Path(tmp);bundle,cfg=fixture_bundle(root);plan=prepare_feasibility(cfg,bundle)
            with patch('pact.training.feasibility.TransformersBackend',side_effect=lambda *a:FixtureBase(plan)):
                with patch('pact.training.feasibility.sync_run',side_effect=TimeoutError('fixture deadline')):
                    failed=run_feasibility(cfg,bundle,root/'run',root/'cache',persistent=root/'durable')
                self.assertEqual(failed['exit_code'],2);self.assertEqual(failed['completed_records'],6)
                self.assertFalse(failed['persistent_copy_verified']);self.assertTrue(Path(failed['path']).exists())
                result=run_feasibility(cfg,bundle,root/'run',root/'cache',resume=True,persistent=root/'durable')
                self.assertEqual(result['exit_code'],0,result);self.assertEqual(result['completed_records'],54)
                self.assertEqual(result['scientific_status'],'synthetic_fixture');self.assertTrue(result['persistent_copy_verified'])
                self.assertEqual(file_hash(Path(result['persistent_bundle'])),result['sha256'])
                restore_feasibility(result['persistent_snapshot'],root/'restored',timeout_seconds=10)
                self.assertEqual(file_hash(root/'restored/report.json'),file_hash(root/'run/report.json'))
                with self.assertRaises(ValueError):restore_feasibility(result['persistent_snapshot'],root/'restored',timeout_seconds=10)
                repeated=run_feasibility(cfg,bundle,root/'run',root/'cache',resume=True)
                self.assertEqual(repeated['exit_code'],0)
                self.assertEqual(read_json(root/'run/resources.json')['generation_calls'],0)
                self.assertEqual(len(list((root/'run/attempts').glob('*.json'))),3)
            with patch('pact.training.feasibility.code_identity',return_value={'source_hash':'changed'}), \
                 patch('pact.training.feasibility.TransformersBackend') as model:
                with self.assertRaises(ValueError):run_feasibility(cfg,bundle,root/'run',root/'cache',resume=True)
                model.assert_not_called()

    def test_runtime_mismatch_and_model_load_failure_retain_local_diagnostic(self):
        with tempfile.TemporaryDirectory() as tmp,contextlib.redirect_stdout(io.StringIO()):
            root=Path(tmp);bundle,cfg=fixture_bundle(root);plan=prepare_feasibility(cfg,bundle)
            wrong=FixtureBase(plan);wrong.identity['runtime_fingerprint']=digest('wrong')
            with patch('pact.training.feasibility.TransformersBackend',return_value=wrong):
                result=run_feasibility(cfg,bundle,root/'mismatch',root/'cache')
                self.assertEqual(result['exit_code'],2);self.assertEqual(wrong.calls,[])
            with patch('pact.training.feasibility.TransformersBackend',side_effect=RuntimeError('fixture load failure')):
                result=run_feasibility(cfg,bundle,root/'failure',root/'cache')
                self.assertEqual(result['exit_code'],2);self.assertTrue(Path(result['path']).exists())
            with patch('pact.training.feasibility.TransformersBackend') as model:
                with self.assertRaises(ValueError):run_feasibility(cfg,bundle,root/'failure',root/'cache',resume=True)
                model.assert_not_called()
