"""CPU audit only. No execute, approve, seal, inference or download command."""
import argparse
from pathlib import Path
from ...util import read_json, canonical
from . import review


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('stage',choices=['audit','validate','export','reconstruct','acquisition-plan','mock'])
    p.add_argument('--run-dir',type=Path)
    p.add_argument('--parent-dir',type=Path)
    p.add_argument('--parent-bundle',type=Path)
    p.add_argument('--openbook-file',type=Path)
    p.add_argument('--source-spec',type=Path)
    p.add_argument('--data-dir',type=Path)
    p.add_argument('--exposure',type=Path)
    p.add_argument('--history-receipt',type=Path)
    p.add_argument('--history-root',type=Path,action='append',default=[])
    p.add_argument('--bundle',type=Path)
    p.add_argument('--sha256')
    a=p.parse_args(argv)
    load=lambda path:read_json(path) if path else None
    if a.stage=='acquisition-plan': out=review.acquisition_plan(load(a.source_spec))
    else:
        if not a.run_dir:p.error('--run-dir required')
        if a.stage=='audit':
            if not a.parent_dir:p.error('--parent-dir required')
            out=review.audit(a.run_dir,a.parent_dir,a.openbook_file,load(a.source_spec),a.data_dir,
                             load(a.exposure),load(a.history_receipt),a.history_root,a.parent_bundle)
        elif a.stage=='validate':out=review.validate(a.run_dir)
        elif a.stage=='export':out=review.export(a.run_dir)
        elif a.stage=='reconstruct':
            if not a.bundle or not a.sha256:p.error('--bundle and --sha256 required')
            out=review.reconstruct(a.bundle,a.sha256,a.run_dir)
        else:
            from .fixtures import build
            out=build(a.run_dir)
    print(canonical(out))
    return 0

if __name__=='__main__':raise SystemExit(main())
