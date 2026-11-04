"""One explicit stage, one export, then stop. No default execution approval."""
import argparse
from pathlib import Path
from ...util import canonical
from ...artifacts import run_lock
from ..gpqa_source.sources import private_path
from ..allocation_v3 import storage
from . import plan, guard, runner, report, recovery


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('stage',choices=('prepare','report','export','restore',*guard.STAGES))
    p.add_argument('--run-dir',required=True,type=Path)
    for name in ('seal','cpu-preflight','parent','approval','cache-dir','persistent'):
        p.add_argument('--'+name,type=Path)
    for name in ('plan-hash','approval-sha256','family','policy'):p.add_argument('--'+name)
    p.add_argument('--block',type=int);p.add_argument('--seed',type=int)
    p.add_argument('--execute',action='store_true');p.add_argument('--resume',action='store_true')
    a=p.parse_args(argv)
    try:
        private_path(a.run_dir)
        if a.persistent:private_path(a.persistent)
        if a.stage=='prepare':out=plan.prepare(a.run_dir,a.seal,a.cpu_preflight,a.parent)
        elif a.stage=='restore':out=recovery.restore(a.persistent,a.run_dir,a.plan_hash)
        else:
            if not a.run_dir.is_dir():raise ValueError('prepared_run_required')
            if a.stage in guard.STAGES and not a.execute:raise PermissionError('explicit_execute_required')
            with run_lock(a.run_dir):
                value=plan.validate(a.run_dir,a.plan_hash)
                if a.stage=='report':out=report.report(a.run_dir,value)
                elif a.stage=='export':
                    report.report(a.run_dir,value);out=storage.export(a.run_dir,'manual',a.persistent)
                else:
                    requested=guard.scope(a.stage,a.block,a.family,a.policy,a.seed)
                    out=runner.execute(a.run_dir,a.plan_hash,requested,a.approval,a.approval_sha256,
                                       a.cache_dir,a.persistent,a.resume)
        print(canonical(out));return 0
    except Exception as e:
        # Exception text may include private paths, model responses or prompts.
        print(canonical({'status':'stopped','exception_type':type(e).__name__,
                         'action':'preserve_evidence_no_automatic_retry'}));return 1


if __name__=='__main__':raise SystemExit(main())
