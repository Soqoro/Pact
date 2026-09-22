import copy
import os
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch
from pact.training import receiver_recovery as rr
from pact.util import digest,write_json,read_json


class RecoveryBoundaryTests(unittest.TestCase):
    def test_explicit_transition_rejects_other_studies_and_work(self):
        recipe={'source':rr.PRIOR_SOURCE,'plan':{'fixture':True}}
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);write_json(root/'recipe.json',recipe)
            write_json(root/'state.json',{'study_hash':digest(recipe)})
            review={'plan.json':recipe['plan'],'state.json':{'study_hash':digest(recipe)},'recipe.json':recipe}
            with patch.object(rr,'STUDY',digest(recipe)):
                rr.check_transition(root,recipe['plan'],{'current':'fixture'},'evaluate',review)
                for stage in ('train','acquire','contexts','plan','restore'):
                    with self.assertRaisesRegex(ValueError,'ONLY'):rr.check_transition(root,recipe['plan'],{},stage,review)
                write_json(root/'evaluation/frozen/call-intents/x.json',{})
                with self.assertRaisesRegex(ValueError,'prior evaluation'):rr.check_transition(root,recipe['plan'],{},'evaluate',review)
                write_json(root/rr.RECEIPT,{'implementation_source':{},'policy':rr.POLICY,'review_sha256':rr.REVIEW_SHA})
                rr.check_transition(root,recipe['plan'],{},'evaluate',review)
                with self.assertRaisesRegex(ValueError,'implementation'):rr.check_transition(root,recipe['plan'],{'changed':True},'evaluate',review)
                with self.assertRaisesRegex(ValueError,'restricted'):rr.check_transition(root,{'changed':True},{},'evaluate',review)

    def test_nonfocal_exception_requires_scoped_receipt_and_both_hashes(self):
        receipt={'policy':rr.POLICY,'original_reference_hashes':['a','b','c'],
                 'reference_hashes':{'task_sft':['d','e','f']}}
        self.assertTrue(rr.permits_nonfocal(receipt,'task_sft',1,'b','e'))
        for i,old,new in [(0,'a','d'),(1,'WRONG','e'),(1,'b','WRONG')]:
            self.assertFalse(rr.permits_nonfocal(receipt,'task_sft',i,old,new))
        self.assertFalse(rr.permits_nonfocal(None,'task_sft',1,'b','e'))


@unittest.skipUnless(os.environ.get('PACT_TEST_NEURAL')=='1','tiny local CPU model; no pretrained weights')
class EffectiveInitializationTests(unittest.TestCase):
    def test_real_bf16_reload_certification_and_actual_model_guard(self):
        import torch
        from transformers import Qwen3Config,Qwen3ForCausalLM
        from peft import get_peft_model_state_dict
        from safetensors.torch import load_file
        from pact.training.warmstart import create_adapters,export_references,adapter_parameters
        from pact.training.warmstart_config import WarmstartConfig
        from pact.training.scoring import load_frozen_adapters
        torch.set_num_threads(1)
        def base():
            torch.manual_seed(17)
            return Qwen3ForCausalLM(Qwen3Config(vocab_size=32,hidden_size=16,intermediate_size=32,
                num_hidden_layers=1,num_attention_heads=2,num_key_value_heads=2,head_dim=8)).to(torch.bfloat16)
        def tensors(model):return {k:v.detach().clone() for k,v in adapter_parameters(model).items()}
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);original=create_adapters(base(),WarmstartConfig('a'*64,rank=2,alpha=2,dropout=0.))
            with torch.no_grad():
                for p in adapter_parameters(original).values():p.copy_(torch.randn_like(p)*.012345)
            export_references(original,root,{},0)
            paths=[root/'references'/f'agent{i}' for i in range(3)]
            originals={i:load_file(str(p/'adapter_model.safetensors')) for i,p in enumerate(paths)}
            starts={};ends={};exports={};loaded_models={}
            for arm in rr.ARMS:
                model=load_frozen_adapters(base(),paths);starts[arm]=tensors(model)
                with torch.no_grad():
                    for p in adapter_parameters(model,'agent0').values():p.add_(.001 if arm=='task_sft' else .002)
                ends[arm]=tensors(model)
                (root/arm).mkdir()
                export_references(model,root/arm,{},24)
                exports[arm]={i:load_file(str(root/arm/'references'/f'agent{i}'/'adapter_model.safetensors')) for i in range(3)}
                loaded_models[arm]=load_frozen_adapters(base(),[root/arm/'references'/f'agent{i}' for i in range(3)])
            proof=rr.certify(originals,starts,ends,exports)
            self.assertNotEqual(proof['original_tensor_hashes'][1],proof['effective_tensor_hashes']['frozen'][1])
            self.assertEqual(proof['original_tensor_hashes'][0],proof['effective_tensor_hashes']['frozen'][0])
            for arm,model in {'frozen':load_frozen_adapters(base(),paths),**loaded_models}.items():
                backend=SimpleNamespace(model=model,identity={'snapshot':'export'},base_identity={'snapshot':'base'},assert_unchanged=lambda:None)
                rr.verify_loaded(backend,arm,proof)
                self.assertEqual(backend.identity['effective_actor_tensor_hashes'],proof['effective_tensor_hashes'][arm])
                with torch.no_grad():next(iter(adapter_parameters(model,'agent1').values())).add_(.001)
                with self.assertRaisesRegex(ValueError,'Actual loaded'):rr.verify_loaded(backend,arm,proof)
            changed=copy.deepcopy(ends)
            next(v for k,v in changed['task_sft'].items() if '.agent1.' in k).add_(.001)
            with self.assertRaises(ValueError):rr.certify(originals,starts,changed,exports)
            changed=copy.deepcopy(starts)
            next(v for k,v in changed['receiver_sft'].items() if '.agent0.' in k).add_(.001)
            with self.assertRaises(ValueError):rr.certify(originals,changed,ends,exports)
