"""Offline audit by default; acquisition requires explicit user invocation."""
import argparse
from pathlib import Path
from ...util import read_json,canonical,write_json
from . import sources,review


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('stage',choices=['audit','validate','export','reconstruct','mock','acquire','inventory','recovery-check','seal','static-context'])
    p.add_argument('--config',type=Path);p.add_argument('--run-dir',type=Path)
    p.add_argument('--directory',type=Path);p.add_argument('--source-access-approved',action='store_true')
    p.add_argument('--assets',type=Path)
    p.add_argument('--destination',type=Path);p.add_argument('--review-hash')
    p.add_argument('--bundle',type=Path);p.add_argument('--sha256');p.add_argument('--plan',type=Path)
    a=p.parse_args(argv)
    try:
        if a.stage=='acquire':
            if not a.directory:p.error('--directory required')
            out=sources.acquire(a.directory,approved=a.source_access_approved)
        elif a.stage=='inventory':
            out={'repository':sources.native.REPO,'revision':sources.native.REVISION,'files':list(sources.FILES),
                 'automatic_download':False,'maximum_bytes_per_file':sources.MAX_BYTES,'model_calls':0}
        elif a.stage=='audit':
            if not a.config:p.error('--config required')
            cfg=read_json(a.config);root=Path(cfg['run_dir'])
            # A requeued CPU audit validates the same committed input identity, never overwrites.
            from ...util import digest
            from ...artifacts import run_lock
            root.parent.mkdir(parents=True,exist_ok=True)
            owner=root.parent/(root.name+'-audit-owner')
            if (owner/'.lock').exists():raise ValueError('existing_audit_owner_requires_review')
            with run_lock(owner):
                if root.exists():
                    if read_json(root/'audit-input.json')['sha256']!=digest(cfg):raise ValueError('audit_resume_input_conflict')
                    out=review.validate(root)
                else:
                    kwargs={k:cfg.get(k) for k in ('parent_bundle','gpqa_dir','data_dir')}
                    for name in ('exposure','inventory','history'):kwargs[name]=read_json(Path(cfg[name])) if cfg.get(name) else None
                    out=review.audit(root,Path(cfg['parent_dir']),history_roots=cfg.get('history_roots',[]),**kwargs)
                    write_json(root/'audit-input.json',{'sha256':digest(cfg)})
        else:
            if a.config and not a.run_dir:a.run_dir=Path(read_json(a.config)['run_dir'])
            if not a.run_dir:p.error('--run-dir required')
            if a.stage=='validate':out=review.validate(a.run_dir)
            elif a.stage=='export':out=review.export(a.run_dir)
            elif a.stage=='static-context':
                if not a.assets:p.error('--assets required')
                from .context import check
                out=check(a.run_dir,read_json(a.assets))
            elif a.stage=='seal':
                if not a.destination or not a.review_hash:p.error('--destination and --review-hash required')
                from .plan import seal
                out=seal(a.run_dir,a.destination,a.review_hash)
            elif a.stage=='reconstruct':out=review.reconstruct(a.bundle,a.sha256,a.run_dir)
            elif a.stage=='recovery-check':
                from .recovery import inspect
                out=inspect(a.run_dir,read_json(a.plan))
            else:
                from .fixtures import build
                out=build(a.run_dir)
        print(canonical(out));return 0
    except Exception as exc:
        # No raw row, question, label, path, token, URL query or traceback in Slurm logs.
        print(canonical({'status':'blocked','exception_type':type(exc).__name__,'detail':'private_cpu_audit_failed; preserve inputs; no automatic retry','model_calls':0}))
        return 1

if __name__=='__main__':raise SystemExit(main())
