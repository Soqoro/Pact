"""Bounded read-only history discovery. No absence-of-execution certification."""
import argparse
from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import time

PREFIXES = ('pact-update-allocation-', 'pact-allocation-policy-', 'pact-stage2-')
SKIP = {'.git', '__pycache__', 'cache', '.cache', 'venv', 'models', 'objects',
        'node_modules', 'site-packages'}
MARKERS = {'plan.json', 'state.json', 'status.json', 'update_attempt.json',
           'INFLIGHT.json', 'SNAPSHOT_PENDING.json'}
PROBE_DIRS = {'probe_training', 'probe_scores', 'score_intents'}
JOURNAL_DIRS = {'intents', 'attempts', 'call-intents', 'update_attempts'}


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=True)


def identity_signal(value):
    """Only known control fields; never search prompt/response strings for keywords."""
    if not isinstance(value, dict):
        return False
    for key in ('owner', 'run_id', 'child', 'assay', 'policy'):
        v = value.get(key)
        if isinstance(v, str) and v.startswith(PREFIXES):
            return True
    if value.get('budget_stage') == 'II':
        return True
    return any(identity_signal(value.get(key)) for key in ('identity', 'intent', 'plan'))


def inspect(roots, *, max_files=200000, max_depth=22, max_bytes=16*1024*1024, seconds=1200):
    started = time.monotonic()
    counts = Counter()
    records, gaps, root_states = [], [], []
    seen = set()
    for root_value in roots:
        root = Path(root_value)
        state = {'path': str(root), 'present': root.is_dir(), 'files_seen': 0}
        root_states.append(state)
        if root.is_symlink() or not root.is_dir():
            gaps.append({'path': str(root), 'reason': 'root_missing_or_symlink'})
            continue
        def walk_error(error):
            gaps.append({'path': str(error.filename), 'reason': 'directory_unreadable'})
        for parent, dirs, files in os.walk(root, followlinks=False, onerror=walk_error):
            relative = Path(parent).relative_to(root)
            for name in list(dirs):
                path = Path(parent) / name
                if name in SKIP or path.is_symlink() or len(relative.parts) >= max_depth:
                    dirs.remove(name)
                    gaps.append({'path': str(path), 'reason': 'directory_not_inspected'})
            for name in files:
                if counts['files_seen'] >= max_files or time.monotonic()-started >= seconds:
                    gaps.append({'path': str(root), 'reason': 'global_limit_reached'})
                    return finish(root_states, counts, records, gaps)
                path = Path(parent) / name
                counts['files_seen'] += 1
                state['files_seen'] += 1
                if path.is_symlink():
                    gaps.append({'path': str(path), 'reason': 'file_symlink_not_followed'})
                    continue
                key = str(path.absolute())
                if key in seen:
                    continue
                seen.add(key)
                parts = path.relative_to(root).parts
                path_signal = any(part.startswith(PREFIXES) or part in PROBE_DIRS for part in parts)
                if path.suffix.lower() == '.zip':
                    counts['archives_not_opened'] += 1
                    if path_signal:
                        records.append({'path': str(path), 'kind': 'possible_stage2_archive', 'content_verified': False})
                    continue
                is_json = path.suffix == '.json'
                if not is_json or not (path_signal or name in MARKERS or set(parts) & JOURNAL_DIRS):
                    continue
                try:
                    size = path.stat().st_size
                    if size > max_bytes:
                        gaps.append({'path': str(path), 'reason': 'metadata_size_limit'})
                        continue
                    with path.open('rb') as stream:
                        data = stream.read(max_bytes + 1)
                    if len(data) > max_bytes:
                        raise ValueError('size_changed')
                    value = json.loads(data)
                    counts['json_inspected'] += 1
                    signal = identity_signal(value)
                    if path_signal or signal:
                        if set(parts) & JOURNAL_DIRS or name == 'update_attempt.json':
                            kind = 'possible_attempt_record'
                        elif set(parts) & PROBE_DIRS:
                            kind = 'possible_probe_artifact'
                        elif name == 'plan.json':
                            kind = 'plan_only_not_execution_proof'
                        else:
                            kind = 'possible_stage2_metadata'
                        records.append({'path': str(path), 'kind': kind,
                            'sha256': hashlib.sha256(data).hexdigest(), 'bytes': len(data),
                            'identity_signal': signal, 'path_signal': path_signal})
                except (OSError, ValueError, TypeError, RecursionError):
                    gaps.append({'path': str(path), 'reason': 'metadata_read_or_parse_failed'})
    return finish(root_states, counts, records, gaps)


def finish(roots, counts, records, gaps):
    private = {'version': 'stage2_history_discovery_v1', 'roots': roots,
               'records': records, 'gaps': gaps, 'counts': dict(counts)}
    public = {'version': private['version'], 'status': 'inventory_only_consumption_unresolved',
              'roots_requested': len(roots), 'roots_present': sum(x['present'] for x in roots),
              'counts': dict(counts), 'candidate_counts': dict(Counter(x['kind'] for x in records)),
              'gap_counts': dict(Counter(x['reason'] for x in gaps)),
              'private_inventory_sha256': hashlib.sha256(canonical(private).encode()).hexdigest(),
              'archives_contents_inspected': False, 'no_execution_claim_from_absence': True,
              'spent_budget': None, 'remaining_budget': None, 'model_calls': 0,
              'execution_authorized': False, 'existing_evidence_modified': False}
    return private, public


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', action='append', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    try:
        if args.output.exists() or any(p.is_symlink() for p in (args.output, *args.output.parents)):
            raise ValueError('output_collision_or_symlink')
        private, public = inspect(args.root)
        args.output.mkdir(parents=True, mode=0o700, exist_ok=False)
        for name, value in [('inventory.private.json', private), ('summary.sanitized.json', public)]:
            with (args.output/name).open('x') as stream:
                stream.write(canonical(value)+'\n')
        print(canonical(public))
        return 0
    except Exception as exc:
        print(canonical({'status': 'inventory_stopped', 'exception_type': type(exc).__name__, 'model_calls': 0}))
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
