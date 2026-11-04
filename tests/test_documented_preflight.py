import hashlib
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from pact.util import canonical, digest, write_json
from pact.revival import documented_preflight as p
from pact.revival.gpqa_source import fixtures, contracts


class PreflightTests(unittest.TestCase):
    def test_inventory_corruption_and_unsealed_addition(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);(root/'a').write_bytes(b'bound')
            write_json(root/'checksums.json',{'a':hashlib.sha256(b'bound').hexdigest()})
            h=hashlib.sha256((root/'checksums.json').read_bytes()).hexdigest()
            (root/'COMPLETE').write_text(h+'\n')
            self.assertEqual(set(p.checked_inventory(root,h)),{'a'})
            (root/'extra').write_text('unexpected')
            with self.assertRaises(ValueError):p.checked_inventory(root,h)
            (root/'extra').unlink();(root/'a').write_bytes(b'changed')
            with self.assertRaises(ValueError):p.checked_inventory(root,h)

    def test_inventory_traversal_and_symlink(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            write_json(root/'checksums.json',{'../outside':'0'*64})
            h=hashlib.sha256((root/'checksums.json').read_bytes()).hexdigest()
            (root/'COMPLETE').write_text(h)
            with self.assertRaisesRegex(ValueError,'unsafe'):p.checked_inventory(root,h)
            (root/'alias').symlink_to(root/'checksums.json')
            with self.assertRaises(ValueError):p.checked_inventory(root,'0'*64)

    def test_checkpoint_isolation_and_precision(self):
        expected={'file_sha256':'a'*64,'adapter_hash':'b'*64,'keys_shapes':{'x':[2,4]},'saved_dtype':'float32'}
        actual={**expected,'fit':'uniform_joint_sft/Q','structural_validity':True,'historical_tensor_verified':True}
        self.assertEqual(p.check_checkpoint_result('Q',actual,expected)['adapter_hash'],'b'*64)
        for changes in ({'fit':'independent_adversarial_sft/Q'}, {'saved_dtype':'bfloat16'},
                        {'file_sha256':'c'*64},{'adapter_hash':'c'*64},{'historical_tensor_verified':False}):
            with self.assertRaises(ValueError):p.check_checkpoint_result('Q',{**actual,**changes},expected)

    def test_bridge_excludes_evaluation_and_cannot_grant_work(self):
        source,candidate,_=fixtures.inputs();s0={f:{'adapter_hash':f*64} for f in 'QLM'}
        training=contracts.training_contract(source,s0)
        receipt={'method_digest':'a'*64,'candidate_digest':digest(candidate),'graph_digest':'b'*64,
                 'training_dependency_hash':digest(training)}
        bridge=p.execution_contract(receipt,training,{'S0':s0})
        raw=canonical(bridge)
        for r in candidate['records']:self.assertNotIn(r['task']['task_id'],raw)
        self.assertEqual(bridge['budgets']['generation'],23728)
        self.assertEqual(bridge['evaluation_source_weights'],{'gpqa_main':.5,'logiqa':.5})
        self.assertIsNone(bridge['historical_spending'])
        for value in (bridge,{**bridge,'execution_authorized':True}):
            with self.assertRaises(PermissionError):p.require_execution_authority(value)

    def test_package_inspection_never_claims_gpu_verification(self):
        with patch.object(p.importlib.metadata,'version',side_effect=lambda n:p.PACKAGES[n]), \
             patch.object(p.platform,'python_version',return_value='3.13.15'), \
             patch.object(p.platform,'system',return_value='Linux'), \
             patch.object(p.platform,'machine',return_value='x86_64'):
            result=p.package_check()
            self.assertTrue(result['matches']);self.assertFalse(result['gpu_runtime_checked'])
        with patch.object(p.importlib.metadata,'version',return_value='changed'):
            self.assertFalse(p.package_check()['matches'])

if __name__=='__main__':unittest.main()
