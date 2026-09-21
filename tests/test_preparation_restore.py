"""Small verified probe exports and narrowly scoped source migration."""
import copy
import dataclasses as dc
from pathlib import Path
import tempfile
import unittest
from pact.artifacts import _sync_run
from pact.backends.transformers import adapter_hash
from pact.training.preparation_runner import training_inputs,preparation_references,run_preparation_training
from pact.training.preparation_restore import (PRIOR_SOURCE,SELECTED,MARKER,
    restore_preparation_references,verify_inference_export,compatible_probe_resume)
from pact.util import read_json,write_json,digest,file_hash
from test_preparation_execution import training_fixture


def snapshot_fixture(tmp):
    root=Path(tmp)/'full';plan=training_fixture();cfg,prepared=training_inputs(plan)
    recipe={'config':dc.asdict(cfg),'data_manifest_hash':cfg.data_manifest_hash,'source':PRIOR_SOURCE}
    identity={'recipe_hash':digest(recipe),'model_snapshot':'base','runtime_fingerprint':'runtime'}
    write_json(root/'run.json',{'recipe':recipe,'recipe_hash':digest(recipe),'identity':identity,'plan':prepared[3]})
    write_json(root/'preparation_plan.json',plan)
    refs=[]
    for i in range(3):
        path=root/f'references/agent{i}'
        write_json(path/'adapter_config.json',{'peft_type':'LORA','r':16,'lora_alpha':32,
            'target_modules':['q_proj','v_proj'],'lora_dropout':0,'bias':'none','task_type':'CAUSAL_LM'})
        (path/'adapter_model.safetensors').write_bytes(f'synthetic-{i}'.encode())
        refs.append({'agent':i,'identity':f'agent{i}','kind':'warm_start_adapter','path':f'agent{i}','sha256':adapter_hash(path)})
    manifest={'schema_version':1,'identity':identity,'final_step':90,'references':refs}
    write_json(root/'references/references.json',manifest)
    logs=[{'step':j+1,'agent':f'agent{j//30}','agent_step':j%30+1,
        'task_ids':plan['training']['agent_task_ids'][j//30][(j%30)*4:(j%30+1)*4]} for j in range(90)]
    write_json(root/'status.json',{'status':'warmstart_updates_complete','completed_steps':90,'logs':logs,
        'scientific_status':'train_only_actor_preparation_120','references':manifest})
    checkpoint=root/'checkpoints/step-000090'
    write_json(checkpoint/'state.json',{'schema_version':1,'identity':identity,'step':90,'tree':{}})
    (checkpoint/'tensors.safetensors').write_bytes(b'optimizer-must-not-be-read')
    write_json(checkpoint/'checksums.json',{n:file_hash(checkpoint/n) for n in ('state.json','tensors.safetensors')})
    return plan,root,_sync_run(root,Path(tmp)/'durable')


class PreparationRestoreTests(unittest.TestCase):
    def test_restore_omits_optimizer_objects_and_preserves_final_gate(self):
        with tempfile.TemporaryDirectory() as tmp:
            plan,root,snapshot=snapshot_fixture(tmp)
            entries=read_json(snapshot/'index.json')['files']
            # Deliberately remove the optimizer object: the probe must not access it.
            (snapshot.parent.parent/'objects'/entries['checkpoints/step-000090/tensors.safetensors']).unlink()
            destination=Path(tmp)/'inference'
            result=restore_preparation_references(snapshot,destination,timeout_seconds=10)
            self.assertEqual(result['copied_files'],12)
            self.assertFalse(list(destination.glob('checkpoints/**/*.safetensors')))
            self.assertEqual(verify_inference_export(destination)['step'],90)
            self.assertEqual(preparation_references(plan,destination).reference_final_step,90)
            with self.assertRaisesRegex(ValueError,'cannot resume training'):
                run_preparation_training(plan,destination,'cache',persistent=Path(tmp)/'other',resume=True)
            write_json(destination/'status.json',{'completed_steps':89})
            with self.assertRaises(ValueError):verify_inference_export(destination)

    def test_corrupt_adapter_or_marker_rejected_without_partial_destination(self):
        for corrupt in ('adapter','marker'):
            with self.subTest(corrupt=corrupt),tempfile.TemporaryDirectory() as tmp:
                _,_,snapshot=snapshot_fixture(tmp);destination=Path(tmp)/'inference'
                if corrupt=='marker':(snapshot/'COMPLETE').write_text('wrong')
                else:
                    entries=read_json(snapshot/'index.json')['files']
                    (snapshot.parent.parent/'objects'/entries['references/agent0/adapter_model.safetensors']).write_bytes(b'bad')
                with self.assertRaises(ValueError):restore_preparation_references(snapshot,destination,timeout_seconds=10)
                self.assertFalse(destination.exists())

    def test_incomplete_training_or_unreviewed_source_rejected(self):
        for change in ('steps','source'):
            with self.subTest(change=change),tempfile.TemporaryDirectory() as tmp:
                _,root,_=snapshot_fixture(tmp)
                if change=='steps':
                    v=read_json(root/'status.json');v['completed_steps']=89;write_json(root/'status.json',v)
                else:
                    v=read_json(root/'run.json');v['recipe']['source']['source_hash']='0'*64;write_json(root/'run.json',v)
                snapshot=_sync_run(root,Path(tmp)/'other')
                with self.assertRaises(ValueError):restore_preparation_references(snapshot,Path(tmp)/'inference',timeout_seconds=10)
                self.assertFalse((Path(tmp)/'inference').exists())

    def test_migration_requires_exact_old_source_and_unchanged_scientific_recipe(self):
        recipe={'config':{'fixed':1},'plan_hash':'plan','source':PRIOR_SOURCE}
        old={'recipe':recipe,'recipe_hash':digest(recipe),'identity':{'recipe_hash':digest(recipe),'actor':'same'},'committed_calls':74}
        new={**recipe,'source':{'git_commit':'new','source_hash':'new','dirty':False}}
        before=copy.deepcopy(old)
        migrated,record=compatible_probe_resume(old,new)
        self.assertEqual(old,before);self.assertEqual(migrated['committed_calls'],74)
        self.assertEqual(migrated['identity']['actor'],'same');self.assertTrue(record['no_call_budget_reset'])
        self.assertEqual(migrated['identity']['recipe_hash'],digest(new))
        for bad in ({**new,'plan_hash':'changed'},{**new,'config':{'fixed':2}}):
            with self.assertRaises(ValueError):compatible_probe_resume(old,bad)
        bad=copy.deepcopy(old);bad['recipe']['source']={**PRIOR_SOURCE,'dirty':True};bad['recipe_hash']=digest(bad['recipe']);bad['identity']['recipe_hash']=bad['recipe_hash']
        with self.assertRaises(ValueError):compatible_probe_resume(bad,new)
