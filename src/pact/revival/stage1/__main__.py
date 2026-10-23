"""Explicit single-stage evaluation CLI. Defaults never generate."""
import argparse
from pathlib import Path
from ...artifacts import run_lock
from ...util import canonical,read_json,write_json,digest
from . import evidence,weights,engine,metrics,io


def main(argv=None):
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('stage',choices=['recover-inspection','resolve','inspect','verify','freeze','smoke','validation','source_evaluation','fixed_history','report','export','restore','map-recovery','fixture','audit','repair-tokenizer-cache'])
    ap.add_argument('--run-dir',type=Path,required=True);ap.add_argument('--persistent',type=Path)
    ap.add_argument('--private',type=Path);ap.add_argument('--sanitized',type=Path);ap.add_argument('--exposure',type=Path)
    ap.add_argument('--checkpoint-map',type=Path);ap.add_argument('--cache-dir',type=Path)
    ap.add_argument('--recovery-bundle',type=Path);ap.add_argument('--recovery-sha');ap.add_argument('--tensor-dir',type=Path)
    ap.add_argument('--execute',action='store_true');ap.add_argument('--plan-hash');ap.add_argument('--mock',action='store_true')
    ap.add_argument('--export-stage',default='inspect')
    a=ap.parse_args(argv);root=a.run_dir
    if not a.mock and a.stage!='audit' and root.name!=evidence.RUN:raise ValueError('Separate reserved evaluation run directory required')
    if a.persistent is not None and a.persistent.name!=evidence.RUN:raise ValueError('Separate evaluation persistence root required; parents are read-only')
    if a.stage=='recover-inspection':
        if not a.execute or a.mock:raise ValueError('Explicit real storage recovery required')
        from .storage_recovery import recover
        out=recover(root,a.persistent,a.private,a.plan_hash)
    elif a.stage=='fixture':
        if not a.mock:raise ValueError('Explicit --mock required')
        from .fixture import build
        private,sanitized,mapping=build(root.parent/'fixture-inputs')
        out=evidence.resolve(root,private,sanitized,{},mapping,fixture=True)
    elif a.stage=='map-recovery':
        out=io.map_recovery(a.recovery_bundle,evidence.sha(a.recovery_sha),a.private,a.tensor_dir)
    elif a.stage=='audit':out=io.audit(a.private,root)
    elif a.stage=='resolve':
        out=evidence.resolve(root,a.private,a.sanitized,read_json(a.exposure),read_json(a.checkpoint_map) if a.checkpoint_map else None,fixture=a.mock)
    elif a.stage=='restore':out=io.restore(a.persistent,root)
    else:
        with run_lock(root):
            resolution=evidence.guard(root)
            if a.mock!=resolution['fixture']:raise ValueError('Fixture/real boundary')
            if a.persistent and ((a.persistent/'SNAPSHOT_PENDING.json').exists() or (a.persistent/'INFLIGHT.json').exists()) and a.stage not in ('inspect','export','report'):raise ValueError('Pending persistence/dispatch; no retry')
            factory=None
            if a.mock:
                from .fixture import Backend
                factory=Backend
            persist=lambda:io.persist(root,a.persistent)
            if a.stage=='inspect':out=resolution
            elif a.stage=='repair-tokenizer-cache':
                if not a.execute or a.plan_hash!=digest(resolution) or a.mock:raise ValueError('Explicit real metadata repair and resolution hash required')
                from ..mistral_cache import repair
                out=repair(a.cache_dir);write_json(root/'cache_repair_receipt.json',out);persist()
            elif a.stage=='verify':
                if not a.execute or a.plan_hash!=digest(resolution):raise ValueError('Explicit verification and resolution hash required')
                out=weights.verify(root,a.cache_dir,factory,persist)
                io.export(root,'verify',a.persistent)
            elif a.stage=='freeze':
                if not (root/'exports/verify.json').exists():raise ValueError('Export verification and stop first')
                out=engine.freeze(root);persist()
            elif a.stage in ('smoke','validation','source_evaluation','fixed_history'):
                if not a.execute or not a.plan_hash:raise ValueError('Explicit stage and frozen plan hash required')
                out=engine.execute(root,a.stage,a.plan_hash,a.cache_dir,factory,io.BatchedPersistence(root,a.persistent))
                metrics.report(root);io.export(root,a.stage,a.persistent)
            elif a.stage=='report':out=metrics.report(root)
            else:out=io.export(root,a.export_stage,a.persistent)
    # Do not print raw inputs, paths from evidence, or full private contracts.
    if a.stage in ('resolve','inspect','fixture'):
        out={k:out[k] for k in ('version','fixture','status','blockers') }|{'resolution_hash':digest(out)}
    elif a.stage=='verify':out={k:out[k] for k in ('ready','synthetic_attempts','generation_calls','optimizer_updates')}
    print(canonical(out))

if __name__=='__main__':main()
