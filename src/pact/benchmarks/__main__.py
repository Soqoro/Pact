"""Explicit source preparation and isolated scoring, independent per dataset."""
import argparse
from pathlib import Path
from .registry import REGISTRY, registry, budget
from .data import acquire,prepare,exposure_index,ReadinessError
from ..util import canonical,read_json,write_json


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('stage',choices=['list','status','inspect-source','prepare','exposure-index','code-probe','code-run','suite-report'])
    p.add_argument('--dataset',choices=list(REGISTRY));p.add_argument('--source-dir',type=Path)
    p.add_argument('--output',type=Path);p.add_argument('--download',action='store_true');p.add_argument('--parent',type=Path)
    p.add_argument('--exposure',type=Path);p.add_argument('--evaluator-python',type=Path);p.add_argument('--jobs',type=Path)
    p.add_argument('--runs-root',type=Path)
    p.add_argument('--prepared',type=Path,nargs='+')
    a=p.parse_args(argv)
    try:
        if a.stage=='exposure-index':
            if not a.prepared or not a.output:p.error('--prepared and --output required')
            write_json(a.output,exposure_index([read_json(f) for f in a.prepared]));return
        if a.stage in ('list','status'):
            print(canonical({k:{'spec':v,'budget':budget(k),'implementation':'implemented_runtime_prerequisites_required','gpu_verified':False,
                  'external_prerequisite':('verified isolated evaluator' if k=='mbpp-plus' else 'requested_release_unavailable_until_official_inventory_verified' if k=='livebench' else 'authorized official source plus parent partition' if k=='gpqa' else 'pinned Math-Verify installation' if k=='math-500' else None)} for k,v in registry().items()}));return
        if a.stage=='suite-report':
            out={}
            for name in REGISTRY:
                path=a.runs_root/('pact-breadth-'+name+'-001')/'summary.json'
                out[name]=read_json(path) if path.exists() else {'status':'not_executed','scientific_result':None}
            write_json(a.output,out);return
        if a.stage.startswith('code-'):
            from .isolation import Bubblewrap
            worker=Bubblewrap(a.evaluator_python)
            if a.stage=='code-probe':print(canonical(worker.probe()));return
            if a.output.exists():raise ValueError('Never overwrite scorer results')
            jobs=read_json(a.jobs)['jobs'];results=[]
            for job in jobs:
                from .scoring import evaluator_identity
                from ..util import digest
                body={k:v for k,v in job.items() if k!='job_hash'}
                if digest(body)!=job['job_hash'] or job['identity']!=evaluator_identity(job['kind']):raise ValueError('Untrusted scoring job identity')
                if job['parse_status']!='ok':continue
                results.append(worker.run(job))
                write_json(a.output,{'results':results,'completed':False})
            write_json(a.output,{'results':results,'completed':True});return
        if not a.dataset or not a.source_dir:p.error('--dataset and --source-dir required')
        if a.stage=='inspect-source':print(canonical(acquire(a.dataset,a.source_dir,download=a.download)))
        else:
            if not a.output:p.error('--output required')
            print(canonical(prepare(a.dataset,a.source_dir,a.output,download=a.download,parent=a.parent,
                                    known=read_json(a.exposure) if a.exposure else None)))
    except ReadinessError as exc:
        print(canonical({'status':str(exc),'dataset':a.dataset,'other_datasets_blocked':False}));raise SystemExit(1) from None

if __name__=='__main__':main()
