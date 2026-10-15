"""Read-only, hash-bound import of the closed selective-correction parent."""
from contextlib import contextmanager
from functools import lru_cache
from pathlib import Path
import copy
import zipfile
from ..util import digest, file_hash, read_json, write_json
from ..training.feasibility import read_review
from ..studies.forensics import private_root
from . import study as s, gates as g

PRIVATE_SHA = 'b013fc63b8c4331b25f0589374b162cdade24759b1a5442bb85ca89c81926449'
PLAN_HASH = '848b8e6941f958628e8697e96fcd11a465237c056f313d84b12b7088c461c0d6'


def inventory(root):
    return {str(p.relative_to(root)): file_hash(p) for p in sorted(root.rglob('*')) if p.is_file() and p.name != '.lock'}


@contextmanager
def cached_reads():
    """Scoped immutable metadata cache; never changes a dispatch implementation."""
    originals = {name: getattr(s, name) for name in ('load', 'records', 'source_bank')}
    s.load = lru_cache(None)(s.load)
    s.records = lru_cache(None)(s.records)
    bank = {}
    def source(root, rec):
        key = str(root), digest(rec)
        if key not in bank:
            bank[key] = originals['source_bank'](root, rec)
        return copy.deepcopy(bank[key])
    s.source_bank = source
    try:
        yield
    finally:
        for name, value in originals.items():
            setattr(s, name, value)


def required(root):
    names = ['plan.json', 'state.json', 'source_exposure_manifest.json', 'frozen_policy_receipt.json',
             'threshold_selection.json', 'baselines/source_development_holdout.json',
             'evaluation/source_development_holdout.json', 'feature_schema.json']
    names += [f'gates/{a}.json' for a in s.ARMS]
    names += [f'{folder}/{split}.json' for split in s.SPLITS
              for folder in ('labels', 'features', 'pools', 'targets', 'feature_bank_identity')]
    missing = [n for n in names if not (root/n).is_file()]
    if missing:
        raise ValueError('missing_parent_evidence: ' + ', '.join(missing))


def validate(root, mock=False, reconstruct=True):
    required(root)
    before = inventory(root)
    # Existing immutable() calls are allowed to compare, never create missing evidence.
    original = s.immutable
    def compare(path, value):
        if not path.is_file():
            raise ValueError('missing_parent_evidence: ' + str(path.relative_to(root)))
        if read_json(path) != value:
            raise ValueError('Parent reconstruction mismatch: ' + str(path.relative_to(root)))
    try:
        s.immutable = compare
        with cached_reads():
            p, intents, calls, unknown = s.inspect(root)
            if p['fixture'] != mock or unknown or not read_json(root/'state.json')['recovery_safe']:
                raise ValueError('Closed safe matching parent required')
            if not mock and digest(p) != PLAN_HASH:
                raise ValueError('Wrong closed parent plan')
            if len({r['group_id'] for r in p['records']}) != len(p['records']):
                raise ValueError('Repeated parent group')
            if reconstruct:
                for split in s.SPLITS:
                    s.audit_checks(root, split)
                session = s.Session(root, mock=mock)
                s.baselines(session, s.SPLITS[2])
            tasks = {split: s.labeled_features(root, split) for split in s.SPLITS}
            models = {a: read_json(root/'gates'/f'{a}.json') for a in s.ARMS}
            thresholds = read_json(root/'threshold_selection.json')
            for arm, model in models.items():
                g.validate_model(model)
                if model['class_order'] != ['harm', 'neutral', 'improve'] or model['fit_hash'] != digest(tasks['fit']):
                    raise ValueError('Parent class order/fit identity changed')
                rows, weights, support = g.fit_rows(tasks['fit'], arm)
                if weights != model['weights'] or support != model['weight_support']:
                    raise ValueError('Parent fitting weights changed')
                # Reconstruct the fit-only transform; never replace or re-estimate on tuning.
                import numpy as np
                layout = 'metadata' if arm=='metadata_augmented' else 'restricted' if arm.startswith('restricted') else 'full'
                means=np.zeros(len(model['mean']));scales=np.ones(len(means))
                if rows:
                    X=np.asarray([g.encode(r[layout],arm=='metadata_augmented') for r in rows])
                    n=len(model['feature_spec']['numeric'])
                    means[:n]=np.average(X[:,:n],axis=0,weights=weights)
                    variance=np.average((X[:,:n]-means[:n])**2,axis=0,weights=weights)
                    scales[:n]=np.where(variance>1e-12,np.sqrt(variance),1.)
                if not np.allclose(means,model['mean'],rtol=0,atol=1e-12) or not np.allclose(scales,model['scale'],rtol=0,atol=1e-12):
                    raise ValueError('Saved fit-only transform mismatch')
                if g.tune(model, tasks['threshold_tuning']) != thresholds[arm]:
                    raise ValueError('Original tuning reconstruction mismatch')
            s.frozen(root)
            from .metrics import evaluate_records
            if evaluate_records(root, s.SPLITS[2]) != read_json(root/'evaluation'/f'{s.SPLITS[2]}.json')['rows']:
                raise ValueError('Original policy reconstruction mismatch')
        return p, tasks, models, thresholds
    finally:
        s.immutable = original
        if inventory(root) != before:
            raise ValueError('Parent bytes changed during read-only reconstruction')


def import_parent(root, bundle, sha, mock=False):
    if root.exists():
        raise ValueError('Import destination exists; do not overwrite')
    if not mock and sha != PRIVATE_SHA:
        raise ValueError('Exact closed PRIVATE parent required')
    data = read_review(bundle, sha, max_members=60000, max_bytes=512*1024**2,
                       selected_names={'HANDOFF.json', 'plan.json'}, allow_text=True)
    if data['HANDOFF.json']['kind'] != s.VERSION+'_private' or data['plan.json']['fixture'] != mock:
        raise ValueError('Matching PRIVATE parent required')
    private_root(root, mock)
    # read_review verifies all member paths, sizes and checksums before extraction.
    with zipfile.ZipFile(bundle) as z:
        for name in z.namelist():
            if name in ('HANDOFF.json', 'review_checksums.json'):
                continue
            path = root/'parent'/name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(z.read(name))
    p, _, _, _ = validate(root/'parent', mock)
    receipt = {'schema_version':1, 'private_sha256':sha, 'parent_plan_hash':digest(p),
               'fixture':mock, 'verified_files':inventory(root/'parent'), 'new_model_calls':0, 'new_fits':0}
    write_json(root/'parent_import_receipt.json', receipt)
    return receipt


def verified_parent(root, mock=False):
    receipt = read_json(root/'parent_import_receipt.json')
    parent = root/'parent'
    if receipt['fixture'] != mock or (not mock and receipt['private_sha256'] != PRIVATE_SHA):
        raise ValueError('Parent receipt identity mismatch')
    if inventory(parent) != receipt['verified_files']:
        raise ValueError('Parent files changed since trusted import')
    return parent
