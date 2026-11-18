import copy
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import aai_documented_policy_freeze as f
from pact.revival.allocation_v3 import design as d

class FreezeGuards(unittest.TestCase):
    def test_accounting_mutations_rejected(self):
        keys=('physical_attempts','committed_operations','unresolved','reserved_output_tokens',
              'input_tokens','output_tokens','format_status_counts','historical_spending','remaining_historical_budget')
        before={k:0 for k in keys};before['recovery_safe']=True
        f.unchanged_accounting(before,copy.deepcopy(before))
        for key in keys:
            after=copy.deepcopy(before);after[key]=1
            with self.assertRaises(f.b.CheckFailed):f.unchanged_accounting(before,after)
    def test_allocation_and_checkpoint_guards(self):
        blocks=[{'family':'arc_challenge' if i<3 else 'logiqa','fit':[f'{i}-{j}' for j in range(64)]} for i in range(8)]
        allocation=d.compile_policies(blocks,[[1,2,3]]*8,[[3,2,1]]*8,d.derangement(blocks),f.b.S0)
        f.check_allocation(allocation)
        for mutation in ('primary','quota','s0','alias'):
            bad=copy.deepcopy(allocation)
            if mutation=='primary':bad['primary']='uniform'
            elif mutation=='quota':bad['matrices']['uniform'][0]=[12,0,0]
            elif mutation=='s0':next(iter(bad['plans'].values()))['s0']['Q']='changed'
            else:bad['aliases'][next(iter(bad['plans']))]='missing'
            with self.assertRaises((f.b.CheckFailed,KeyError)):f.check_allocation(bad)
    def test_cpu_shell_has_no_gpu_or_download_path(self):
        text=(Path(__file__).resolve().parents[1]/'tools/aai_documented_policy_freeze.sbatch').read_text()
        self.assertNotIn('--gres',text);self.assertNotIn('--nv',text)
        self.assertIn('HF_HUB_OFFLINE=1',text)
        self.assertIn('--env CUDA_VISIBLE_DEVICES=',text)
