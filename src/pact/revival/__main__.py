"""Thin guarded CLI; no default GPU work and no automatic stage portfolio."""
import argparse
from pathlib import Path
import time
import tempfile
from ..util import read_json,write_json,digest,file_hash,canonical
from ..artifacts import run_lock
from ..storage import persist_bundle
from . import contracts as c, data, study as s, runtime,probe


def main(argv=None,probe_cli=False):
    p=argparse.ArgumentParser(prog='pact update-probe' if probe_cli else 'pact revival')
    choices=['plan','collect-base','temporary-update','evaluate-branches','score','assign','report','export'] if probe_cli else ['inspect','prepare-source','plan','preflight','source-smoke','collect-fit','acquire-attacks','build-training-bank','train-sanity','train-agent','freeze-team','evaluate','evaluate-peer-use','report','export','restore']
    p.add_argument('stage',nargs='?',default='report' if probe_cli else 'inspect',choices=choices)
    p.add_argument('--run-dir',type=Path,required=True);p.add_argument('--source',type=Path);p.add_argument('--exposure',type=Path)
    p.add_argument('--cache-dir',type=Path,default=Path('/content/pact-revival/cache'));p.add_argument('--persistent',type=Path)
    p.add_argument('--plan-hash');p.add_argument('--probe-plan-hash');p.add_argument('--stage-i-review-sha')
    p.add_argument('--execute',action='store_true');p.add_argument('--mock',action='store_true');p.add_argument('--download',action='store_true');p.add_argument('--resume',action='store_true')
    p.add_argument('--family',choices=c.FAMILIES);p.add_argument('--arm',choices=c.ARMS);p.add_argument('--split',choices=['validation','source_evaluation'])
    p.add_argument('--block',type=int,choices=range(8));p.add_argument('--bundle',type=Path);p.add_argument('--sha256')
    a=p.parse_args(argv);root=a.run_dir
    if a.stage=='restore':
        if a.persistent:runtime.restore_latest(a.persistent,root)
        elif a.bundle:runtime.unpack(a.bundle,a.sha256,root)
        else:raise ValueError('--persistent latest snapshot or explicit --bundle/--sha256 required')
        print('Verified recovery restored');return
    if a.stage=='prepare-source':
        if a.source is None or a.source.exists():raise ValueError('New --source path required')
        from ..studies.forensics import private_root
        private_root(a.source.parent,a.mock)
        if a.mock:value=data.fixture()
        else:
            if a.exposure is None:raise ValueError('Reviewed current exposure inventory required')
            train,val=data.load_training_sources(a.cache_dir/'data',download=a.download);value=data.allocate(train,val,read_json(a.exposure))
        write_json(a.source,value);print(canonical({'status':value['status'],'shortfall':value.get('shortfall')}));return
    if a.stage=='plan' and not probe_cli:
        print(canonical(s.plan(root,read_json(a.source))));return
    if a.stage=='inspect':
        print(canonical({'plan_hash':digest(read_json(root/'plan.json')),'budgets':c.BUDGETS}));return
    from ..studies.forensics import private_root
    private_root(root,a.mock)
    with run_lock(root):
        plan=read_json(root/'plan.json');factory=None
        if a.mock:
            if not plan['source']['fixture']:raise ValueError('Cannot mock real plan')
            from .mock import Backend
            factory=Backend
        if a.stage=='report':out=probe.report(root) if probe_cli else s.report(root)
        elif a.stage=='export':
            s.report(root)
            if probe_cli:probe.report(root)
            stamp=time.time_ns();out={}
            # Recovery weights are separate from private review / sanitized results.
            for name,weights,sanitized in [('PRIVATE',False,False),('SANITIZED',False,True),('RECOVERY',True,False)]:
                path=root.parent/'bundles'/f'{c.RUN}-{name}-{stamp}.zip'
                out[name]=runtime.package(root,path,weights=weights,sanitized=sanitized)
                if a.persistent:persist_bundle(path,a.persistent/'bundles'/path.name,out[name]['sha256'],timeout_seconds=600)
                if name=='PRIVATE' and (root/'source_smoke.json').exists() and not (root/'source_smoke_export.json').exists():write_json(root/'source_smoke_export.json',out['PRIVATE'])
        elif a.stage=='plan' and probe_cli:out=probe.plan(root,plan,a.stage_i_review_sha)
        else:
            plan=s.guard(root,a.plan_hash,a.mock)
            if probe_cli:probe.guard(root,a.probe_plan_hash)
            computational=a.stage in ('preflight','source-smoke','collect-fit','acquire-attacks','train-sanity','train-agent','evaluate','evaluate-peer-use','collect-base','temporary-update','evaluate-branches','score')
            if computational and not a.execute:raise ValueError('Explicit --execute required; no automatic calls')
            if a.stage=='preflight':out={'fixture':True} if a.mock else runtime.preflight(root,a.cache_dir)
            elif a.stage in ('source-smoke','collect-fit'):out=s.collect_fit(root,plan,a.cache_dir,a.stage=='source-smoke',factory,a.persistent)
            elif a.stage=='acquire-attacks':out=s.attacks(root,plan,a.cache_dir,factory=factory,persistent=a.persistent)
            elif a.stage=='build-training-bank':out=s.fit_bank(root,plan)
            elif a.stage=='train-sanity':out=s.sanity(root,plan,a.cache_dir,factory,a.persistent)
            elif a.stage=='train-agent':out=s.train_agent(root,plan,a.cache_dir,a.arm,a.family,resume=a.resume,factory=factory,persistent=a.persistent)
            elif a.stage=='freeze-team':out=s.freeze(root,plan,a.arm)
            elif a.stage=='evaluate':out={'rows':len(s.live(root,plan,a.cache_dir,a.arm,a.split,factory=factory,persistent=a.persistent))}
            elif a.stage=='evaluate-peer-use':out=s.peer_use(root,plan,a.cache_dir,a.arm,factory,a.persistent)
            elif a.stage=='collect-base':out=probe.collect(root,plan,a.cache_dir,factory,a.persistent)
            elif a.stage=='temporary-update':out=probe.temporary(root,plan,a.cache_dir,a.block,a.family,factory,a.persistent)
            elif a.stage=='evaluate-branches':out=probe.evaluate(root,plan,a.cache_dir,a.block,a.family,factory,a.persistent)
            elif a.stage=='score':out=probe.score(root,plan,a.cache_dir,factory,a.persistent)
            elif a.stage=='assign':out=probe.assignments(root)
            else:raise ValueError('Unknown stage')
        runtime.checkpoint(root,a.persistent)
        print(canonical(out))

if __name__=='__main__':main()
