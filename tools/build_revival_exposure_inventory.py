"""Reviewed metadata-only extension of the closed selective parent's exclusions."""
import argparse
from pathlib import Path
from pact.util import digest,read_json,file_hash,write_json
from pact.selective.data import LEDGER,validate_exposure
from pact.studies.forensics import private_root

PARENT_PLAN='848b8e6941f958628e8697e96fcd11a465237c056f313d84b12b7088c461c0d6'
TRAIN_MANIFEST='92771b288958e6a1c23b731936dedb4db6285803465fb468bb05e5e2f497c62a'
# Refreshed only after reviewing the ledger; changing a CLI hash cannot bypass it.
REVIEWED_LEDGER='b07ef7b89055cb869f1f6ba103d7fa37099785d6eeded0dd97540331ce16bfe6'


def build(parent,training_manifest):
    if file_hash(LEDGER)!=REVIEWED_LEDGER:raise ValueError('Ledger advanced; review new allocations before certifying inventory')
    p=read_json(parent/'plan.json');e=read_json(parent/'source_exposure_manifest.json');m=read_json(training_manifest)
    if digest(p)!=PARENT_PLAN or digest(e)!=p['exposure_hash'] or digest(m)!=TRAIN_MANIFEST:raise ValueError('Audited parent/manifests differ')
    old=e['inventory'];result={**old}
    fields={'task_ids':set(old['task_ids']),'group_ids':set(old['group_ids']),'content_groups':set(old['content_groups']),'cross_dataset_fingerprints':set(old['cross_dataset_fingerprints'])}
    for r in p['records']:
        fields['task_ids'].add(r['task']['task_id'])
        for key,field in [('group_ids','group_id'),('content_groups','content_group'),('cross_dataset_fingerprints','cross_dataset_fingerprint')]:fields[key].add(r[field])
    result.update({k:sorted(v) for k,v in fields.items()})
    result.update(ledger_sha256=REVIEWED_LEDGER,reviewed_complete=True,review='2026-10-16: closed selective 224 plus selector reuse; no new cohort allocated',source_receipts=[*old['source_receipts'],{'name':'closed_selective_plan','sha256':file_hash(parent/'plan.json'),'plan_hash':PARENT_PLAN}])
    validate_exposure(result)
    a={r['task_id'] for r in m['selected'] if r['task_id'].startswith('arc_challenge:')}
    b={r['task']['task_id'] for r in p['records'] if r['family']=='arc_challenge'}
    bound={'official_arc_rows':1119,'prior_arc_allocation':len(a),'selective_arc_groups':len(b),'overlap':len(a&b),
           'remaining_arc_upper_bound':1119-len(a|b),'required_arc_groups':480,'minimum_arc_shortfall':max(0,480-(1119-len(a|b))),
           'exact_eligible_count_computed':False,'status':'source_shortfall','model_calls':0}
    return result,bound

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--parent',type=Path,required=True);p.add_argument('--training-manifest',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();private_root(a.output.parent)
    if a.output.exists():raise ValueError('Refuse overwrite')
    inventory,bound=build(a.parent,a.training_manifest);write_json(a.output,inventory);write_json(a.output.with_name('revival-source-feasibility.json'),bound);print(bound)
