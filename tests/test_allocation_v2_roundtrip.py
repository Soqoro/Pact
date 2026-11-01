"""Opt-in complete CPU toy-model path; no downloads or CUDA.
Run PACT_ALLOCATION_FULL_CPU=1 with an installed CPU Torch/Safetensors environment.
"""
import os, unittest
from pathlib import Path
import tempfile,time
from pact.util import read_json,write_json,file_hash
from pact.revival.allocation import runner,storage,report,design as d
from pact.revival.allocation.__main__ import create_plan

@unittest.skipUnless(os.environ.get('PACT_ALLOCATION_FULL_CPU') == '1', 'Opt-in full CPU round trip')
class FullRoundTrip(unittest.TestCase):
 def test_complete(self):
  try: import torch, safetensors
  except ImportError: self.skipTest('Optional CPU Torch/Safetensors unavailable')
  with tempfile.TemporaryDirectory(prefix='allocation-full-') as temp:
   root=Path(temp)/'run'
   torch.set_num_threads(1)
   create_plan(root,True);p=read_json(root/'plan.json')
   def exported(stage):write_json(root/'exports'/f'{stage}.json',{'stage':stage,'safe':True})
   print(root,flush=True)
   runner.collect(root,p,None,smoke=True);exported('assay-smoke')
   runner.collect(root,p,None);exported('collect')
   for b in range(8):
    for f in d.FAMILIES:
     runner.branch(root,p,b,f,None)
     print('branch',b,f,flush=True)
   runner.score(root,p,None);exported('score')
   runner.policy_freeze(root,p);write_json(root/'policy-freeze-receipt.json',{'sha256':file_hash(root/'policies.json')});exported('policy-freeze')
   print('scored',storage.Wallet(root,p).counts(),flush=True)
   for policy in d.POLICIES:
    for seed in d.SEEDS:
     for f in d.FAMILIES:runner.continuation(root,p,policy,seed,f,None)
     print('continued',policy,seed,flush=True)
   runner.lock_policies(root,p);exported('policy-lock')
   runner.evaluate(root,p,None,smoke=True);exported('evaluation-smoke')
   runner.evaluate(root,p,None)
   print('evaluated',storage.Wallet(root,p).counts(),flush=True)
   report.report(root,p)
   out=storage.export(root,'evaluate')
   print('EXPORT',out,flush=True)
   from pact.revival.stage1.evidence import archive
   z,checks=archive(Path(out['RECOVERY']['path']),out['RECOVERY']['sha256'])
   other=root.parent/'reimport';other.mkdir()
   for n in checks:
    path=other/n;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(z.read(n))
   z.close()
   assert storage.Wallet(other,p).counts()==storage.Wallet(root,p).counts()
   print('ROUNDTRIP_OK',flush=True)
