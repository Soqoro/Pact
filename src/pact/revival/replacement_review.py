"""Offline review proposal only: cannot initialize, migrate, or execute a run."""
import hashlib
import json
import zipfile
from pathlib import Path

from ..artifacts import safe_relative
from ..util import file_hash, digest
from .retention import POLICY

PARENT_SHA = 'f9a78141d0c662c06be903b49318f0235f6253d11e42f5bb17b2dd8adf9f2793'
PARENT_PLAN = 'a8ee5cf50d0878dbe6fec8c36364e8b1469cc79c39afd66244b9ecf5f1e5bc71'
BANK_SHA = '66d5233b247aec6d6f833cbe31c845818caecde2094035e9ca6cf9ebdad3bf6c'


def proposal(bundle):
    bundle = Path(bundle)
    if file_hash(bundle) != PARENT_SHA:raise ValueError('Exact reviewed scratch PRIVATE bundle required')
    with zipfile.ZipFile(bundle) as z:
        names = z.namelist()
        if len(set(names)) != len(names) or len(names)>150000 or sum(i.file_size for i in z.infolist())>2*1024**3:
            raise ValueError('Archive bounds/duplicates')
        for i in z.infolist():
            safe_relative(i.filename)
            if (i.external_attr >> 16)&0o170000 == 0o120000:raise ValueError('Archive symlink')
        checks = json.loads(z.read('checksums.json'))
        if set(names) != set(checks)|{'checksums.json','HANDOFF.json'}:raise ValueError('Archive inventory')
        for name, expected in checks.items():
            h=hashlib.sha256()
            with z.open(name) as src:
                while chunk:=src.read(1024**2):h.update(chunk)
            if h.hexdigest()!=expected:raise ValueError('Member checksum')
        plan = json.loads(z.read('plan.json'))
        if digest(plan)!=PARENT_PLAN or checks['training_bank.json']!=BANK_SHA:
            raise ValueError('Parent plan/bank differs')
    return {
        'schema':'revival_replacement_review_v1', 'status':'review_required_not_executable',
        'proposed_run_id':'pact-heterogeneous-receiver-training-replacement-002',
        'parent_run_id':'pact-heterogeneous-receiver-training-001',
        'parent_plan_hash':PARENT_PLAN, 'parent_private_sha256':PARENT_SHA,
        'training_bank_sha256':BANK_SHA, 'parent_plan_file_sha256':checks['plan.json'],
        'historical_accounting':{'confirmed_generation_calls':2438,'confirmed_scratch_updates':48,
            'main_updates_confirmed_at_least':28,'main_updates_actual':None,
            'later_execution_history':'unresolved; never subtracted from replacement budget'},
        'proposed_additional_budget':{'main_updates':768,'training_forwards':18432,
            'generation_calls':0,'scratch_updates':0,'evaluation_calls':0},
        'initialization':'original per-family seeded B-zero FP32 LoRA; verify against retained sanity receipts',
        'reuse':'exact parent bank, task splits, weights, attack decisions, source smoke and scratch evidence; no regeneration',
        'parent_mutations_allowed':False, 'resume_from_step28_allowed':False,
        'storage_retention':POLICY, 'max_object_bytes':32*1024**3,
        'required_before_execution':['artifact-bound user review of additional compute and unresolved parent history',
            'separate executable child import preserving original journal identities and parent provenance',
            'source revision pin and same native model/runtime/initialization checks',
            'capacity preflight including two rolling snapshots, initial/epoch tensors and staging headroom'],
        'gpu_execution_authorized':False,
    }


def main():
    import argparse
    from ..util import write_json
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--parent-private',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    if args.output.exists():raise ValueError('Review output already exists; no overwrite')
    result=proposal(args.parent_private)
    write_json(args.output,result)
    print(json.dumps({'review_sha256':file_hash(args.output),'status':result['status'], 'model_calls':0}))

if __name__=='__main__':main()
