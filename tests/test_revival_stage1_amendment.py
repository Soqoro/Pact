import copy
import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from pact.util import read_json,write_json,digest,file_hash
from pact.revival.stage1 import amendment,evidence,engine,weights,io as exports,metrics
from pact.revival import runtime,study,contracts as c

try:
    import torch
    import safetensors
    TORCH=True
except ImportError:TORCH=False


class Approval(unittest.TestCase):
    def test_approved_proposal_and_caps(self):
        p=amendment.proposal()
        self.assertEqual(digest(p),amendment.PROPOSAL_HASH)
        self.assertFalse(p['approved'])  # Original proposal remains historical.
        self.assertTrue(amendment.APPROVAL['approved'])
        self.assertFalse(amendment.APPROVAL['automatic_gpu_execution'])
        self.assertEqual(sum(amendment.CAPS.values()),14592)
        self.assertEqual(14592*512,7471104)
        self.assertEqual(amendment.CAPS['attack'],0)

    def test_old_storage_transition_rejects_new_science_source(self):
        from pact.revival.stage1 import storage_recovery
        self.assertNotEqual(storage_recovery.protected_code_hash(),storage_recovery.PROTECTED)

    def test_real_verified_parent_adoption_without_models(self):
        bundle=amendment.REPO/'pact-revival-stage1-evaluation-001-PRIVATE-1792766354718085784.zip'
        if not bundle.exists():self.skipTest('Optional returned verification archive absent')
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)/amendment.RUN
            current={'git_commit':'a'*40,'dirty':False,'source_hash':'b'*64}
            def private(path,fixture=False):path.mkdir(parents=True)
            with patch.object(amendment,'code_identity',return_value=current),patch('pact.revival.stage1.amendment.private_root',side_effect=private):
                result=amendment.initialize(root,bundle,amendment.PROPOSAL_HASH)
                self.assertEqual(result['model_calls'],0)
                r=evidence.guard(root)
                self.assertEqual(len(r['original_blockers_preserved']),2)
                self.assertFalse(r['historical_execution_closed'])
                b=read_json(root/'reconciled_generation_budget.json')
                self.assertEqual(b['previous_evaluation_attack_attempts'],384)
                self.assertEqual(b['verified_ancestor_attempts'],2438)
                self.assertEqual(b['new_attempt_cap'],14592)
                self.assertFalse((root/'synthetic').exists())
                self.assertEqual(len(list((root/'parent_verification/synthetic/results').glob('*.json'))),16)
                engine.freeze(root)
                p=engine.validate(root)
                self.assertEqual(p['smoke_generation_cap'],66)
                items=engine.attack_items(root,p,study.records(p,'validation')+study.records(p,'source_evaluation'))
                self.assertEqual(len(items),384)
                self.assertTrue(all('ancestor' in x for x in items))

    def test_cli_parent_write_protection(self):
        from pact.revival.stage1.__main__ import main
        with self.assertRaisesRegex(ValueError,'parents are read-only'):
            main(['init-amended','--run-dir','/tmp/'+amendment.RUN,'--persistent','/tmp/'+evidence.RUN])
        with self.assertRaisesRegex(ValueError,'Original child'):
            main(['resolve','--run-dir','/tmp/'+amendment.RUN])


@unittest.skipUnless(TORCH,'optional tiny local neural fixtures')
class Amended(unittest.TestCase):
    def setUp(self):
        from pact.revival.stage1.fixture import build,Backend
        torch.set_num_threads(1)
        self.tmp=tempfile.TemporaryDirectory();self.base=Path(self.tmp.name);self.backend=Backend
        with contextlib.redirect_stdout(io.StringIO()):
            private,sanitized,mapping=build(self.base/'input')
            parent=self.base/'input/parent'
            study.attacks(parent,read_json(parent/'plan.json'),None,factory=Backend)
            runtime.package(parent,self.base/'input/new-parent.zip')
            (self.base/'input/training/parent-private.zip').write_bytes((self.base/'input/new-parent.zip').read_bytes())
            runtime.package(self.base/'input/training',private)
            self.verified=self.base/'verified'
            evidence.resolve(self.verified,private,sanitized,{},mapping,fixture=True)
            weights.verify(self.verified,None,Backend)
            exported=exports.export(self.verified,'verify')
        self.bundle=Path(exported['PRIVATE']['path'])
        self.original_hash=file_hash(self.bundle)
        self.root=self.base/amendment.RUN
        amendment.initialize(self.root,self.bundle,amendment.PROPOSAL_HASH,fixture=True)
        self.parent_inventory={p.relative_to(self.verified).as_posix():file_hash(p) for p in self.verified.rglob('*') if p.is_file()}
        self.plan=engine.freeze(self.root);self.p=read_json(self.root/'plan.json')

    def tearDown(self):self.tmp.cleanup()

    def test_complete_round_trip_and_privacy(self):
        with contextlib.redirect_stdout(io.StringIO()):
            for stage in ('smoke','validation','source_evaluation','fixed_history'):
                engine.execute(self.root,stage,digest(self.p),None,self.backend)
                out=exports.export(self.root,stage)
        summary=metrics.report(self.root);a=summary['accounting']
        self.assertTrue(summary['all_outputs_observed'])
        self.assertEqual(a['synthetic_attempts'],0)
        self.assertEqual(a['inherited_verification_forwards'],16)
        self.assertNotIn('attack',a['component_attempts'])
        self.assertEqual(a['budget_ownership'],'approved_additional_envelope')
        self.assertFalse(a['historical_accounting']['historical_execution_closed'])
        self.assertEqual(file_hash(self.bundle),self.original_hash)
        self.assertEqual(self.parent_inventory,{p.relative_to(self.verified).as_posix():file_hash(p) for p in self.verified.rglob('*') if p.is_file()})
        for v in engine.Journal(self.root,self.p).intents.values():
            self.assertEqual(v['owner_run_id'],amendment.RUN)
            self.assertEqual(v['physical_attempt_id'],digest([amendment.RUN,digest(self.p),digest(v['request'])]))
        z,checks=evidence.archive(Path(out['SANITIZED']['path']))
        with z:self.assertTrue(set(checks)<= {'summary.json','paired_metrics.json','peer_access_interaction.json','runtime_and_cost_report.json'})
        before=len(engine.Journal(self.root,self.p).intents)
        engine.execute(self.root,'smoke',digest(self.p),None,self.backend)
        self.assertEqual(before,len(engine.Journal(self.root,self.p).intents))

    def test_no_repeat_verification_or_wrong_approval(self):
        with self.assertRaisesRegex(ValueError,'synthetic'):weights.verify(self.root,None,self.backend)
        with self.assertRaisesRegex(ValueError,'proposal hash'):
            amendment.initialize(self.base/'other',self.bundle,'0'*64,fixture=True)
        write_json(self.root/'synthetic/intents/01.json',{})
        with self.assertRaisesRegex(ValueError,'synthetic'):evidence.guard(self.root)

    def test_no_missing_attack_reacquisition(self):
        # A missing original record is a hard failure, never a new attack draw.
        rows=study.records(self.p,'validation');items=engine.attack_items(self.root,self.p,rows)
        self.assertTrue(all('ancestor' in x for x in items))
        with patch.object(runtime,'Journal') as journal:
            journal.return_value.intents={};journal.return_value.results={}
            with self.assertRaisesRegex(ValueError,'acquisition forbidden'):
                engine.attack_items(self.root,self.p,rows)

    def test_caps_and_unresolved_dispatch(self):
        row=study.records(self.p,'validation')[0]
        x=study.item(row,'Q','private',c.prompt(row['task']),['fresh','validation',study.tid(row),'private',0])
        b=self.backend('Q');req=engine.request_for(x)
        try:
            j=engine.Journal(self.root,self.p,66)
            j.intents={str(i):{'component':'validation'} for i in range(66)}
            with self.assertRaisesRegex(ValueError,'smoke budget'):j.request(b,req,x['logical'],'validation',lambda:None)
            j=engine.Journal(self.root,self.p)
            j.intents={str(i):{'component':'validation'} for i in range(4224)}
            with self.assertRaisesRegex(ValueError,'Component budget'):j.request(b,req,x['logical'],'validation',lambda:None)
            j=engine.Journal(self.root,self.p)
            with self.assertRaisesRegex(ValueError,'Component budget'):j.request(b,req,x['logical'],'attack',lambda:None)
            j.budget={**j.budget,'new_attempt_cap':0}
            with self.assertRaisesRegex(ValueError,'Additional envelope'):j.request(b,req,x['logical'],'validation',lambda:None)
            j=engine.Journal(self.root,self.p)
            with patch.object(b,'generate',side_effect=RuntimeError('interrupted')):
                with self.assertRaisesRegex(RuntimeError,'interrupted'):j.request(b,req,x['logical'],'validation',lambda:None)
            with self.assertRaisesRegex(ValueError,'Unresolved'):engine.Journal(self.root,self.p)
        finally:b.close()

    def test_tampered_plan_budget_and_physical_owner(self):
        original=copy.deepcopy(self.p)
        for field,value in [('smoke',[]),('amendment_hash','0'*64),('run_id',evidence.RUN)]:
            bad={**original,field:value}
            write_json(self.root/'plan.json',bad);write_json(self.root/'frozen_stage1_evaluation_plan.json',bad)
            with self.assertRaisesRegex(ValueError,'Approved evaluation'):engine.validate(self.root,digest(bad))
        write_json(self.root/'plan.json',original);write_json(self.root/'frozen_stage1_evaluation_plan.json',original)
        p=self.root/'amendment_approval.json';write_json(p,{**amendment.APPROVAL,'approved':False})
        with self.assertRaises(ValueError):evidence.guard(self.root)

    def test_physical_owner_tamper_rejected(self):
        row=study.records(self.p,'validation')[0]
        logical=['fresh','validation',study.tid(row),'private',0]
        x=study.item(row,'Q','private',c.prompt(row['task']),logical)
        b=self.backend('Q')
        try:
            journal=engine.Journal(self.root,self.p)
            value=journal.request(b,engine.request_for(x),logical,'validation',lambda:None)
        finally:b.close()
        bad=copy.deepcopy(value);bad['intent']['owner_run_id']='wrong-parent'
        write_json(self.root/'intents'/f"{bad['work_id']}.json",bad['intent'])
        with patch('pact.revival.stage1.engine.ShardStore.records',return_value=iter([bad])):
            with self.assertRaisesRegex(ValueError,'Physical attempt owner'):engine.Journal(self.root,self.p)

    def test_stage_boundaries_and_compact_restore(self):
        with self.assertRaisesRegex(ValueError,'Previous stage'):engine.execute(self.root,'validation',digest(self.p),None,self.backend)
        drive=self.base/'drive'
        with contextlib.redirect_stdout(io.StringIO()):
            exports.persist(self.root,drive)
            restored=self.base/'restored';exports.restore(drive,restored)
        self.assertEqual(evidence.guard(restored)['run_id'],amendment.RUN)
        self.assertEqual(read_json(restored/'recovery.json')['run_id'],amendment.RUN)
