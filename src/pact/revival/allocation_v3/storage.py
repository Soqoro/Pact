"""Owned physical wallets and compact recoverable snapshots; no silent retries."""
from dataclasses import asdict
from pathlib import Path
import json
import os
import shutil
import tempfile
import time
import zipfile
from ...util import digest, read_json, write_json, file_hash, canonical
from ...artifacts import ShardStore
from ...studies.heterogeneity import immutable
from .. import contracts as c
from ..stage1.evidence import archive
from .design import BUDGET


class Wallet:
    def __init__(self, root, plan, persistent=None, allow_incomplete=False):
        self.root, self.plan, self.persistent = root, plan, persistent
        self.hash = digest(plan)
        self.store = ShardStore(root/'events')
        self.results = {r['work_id']: r for r in self.store.records()}
        self.intents = {p.stem: read_json(p) for p in (root/'attempts').glob('*.json')}
        if set(self.results)-set(self.intents):
            raise ValueError('Result without owned intent')
        for k, intent in self.intents.items():
            identity = intent['identity']
            costs = {'generation': {'generation': 1}, 'score': {'scores': 1},
                     'update': {'updates': 1, 'training_forwards': 8}}
            if (digest(identity) != k or identity['plan_hash'] != self.hash
                or identity['owner'] != plan['run_id'] or identity['part'] not in ('assay', 'policy')
                or intent['cost'] != costs.get(identity['kind'])):
                raise ValueError('Owned operation identity/cost mismatch')
        for k, r in self.results.items():
            if r['intent'] != self.intents[k] or digest(r['intent']['identity']) != k:
                raise ValueError('Event provenance mismatch')
            intent = r['intent']
            if any(type(n) is not int or n < 0 for n in intent['cost'].values()):
                raise ValueError('Invalid physical cost')
            if intent['identity']['kind'] == 'generation':
                v = r['value']; dep = intent['identity']['dependency']
                req = dep['request']; call = v['call']; tokens = v['tokens']
                if (call['snapshot'] != dep['model']['snapshot'] or call['seed'] != req['seed']
                    or call['messages'] != req['messages'] or call['phase'] != req['phase']
                    or call['context_hash'] != digest(call['rendered_prompt'])
                    or call['input_tokens'] != len(dep['prompt_ids'])
                    or tokens['prompt_ids'] != dep['prompt_ids']
                    or call['output_tokens'] != len(tokens['completion_ids'])
                    or call['output_tokens'] > 512 or call['input_tokens']+512 > 8192
                    or v['raw'] != tokens['raw']
                    or v['packet'] != c.parse(v['raw'], req['task'], call['stop_reason'])):
                    raise ValueError('Stored native generation provenance mismatch')
            if intent['identity']['plan_hash'] != self.hash:
                raise ValueError('Wrong plan owner')
        if not allow_incomplete and set(self.intents)-set(self.results):
            raise ValueError('Unresolved physical attempt; no retry')
        self._counts = {part: {kind: 0 for kind in ('generation','updates','training_forwards','scores')}
                        for part in ('assay','policy')}
        for v in self.intents.values():
            for kind, n in v['cost'].items():
                self._counts[v['identity']['part']][kind] += n
        self.check_caps()

    def counts(self):
        return {part: dict(values) for part, values in self._counts.items()}

    def check_caps(self):
        for part, counts in self.counts().items():
            for kind, n in counts.items():
                if n > BUDGET[part][kind]:
                    raise ValueError('Physical wallet exceeded')

    def begin(self, part, kind, dependency, cost):
        identity = {'owner': self.plan['run_id'], 'plan_hash': self.hash, 'part': part,
                    'kind': kind, 'dependency': dependency}
        key = digest(identity)
        if key in self.results:
            return key, self.results[key]['value']
        if key in self.intents:
            raise ValueError('Unknown dispatch/update/score; no retry')
        if part not in ('assay', 'policy') or kind not in ('generation', 'score', 'update'):
            raise ValueError('Unknown wallet role')
        expected_cost = {'generation': {'generation': 1}, 'score': {'scores': 1},
                         'update': {'updates': 1, 'training_forwards': 8}}[kind]
        if cost != expected_cost:
            raise ValueError('Physical operation cost mismatch')
        counts = self.counts()[part]
        if any(counts[k]+n > BUDGET[part][k] for k, n in cost.items()):
            raise ValueError('Physical budget exhausted')
        value = {'identity': identity, 'cost': cost}
        immutable(self.root/'attempts'/f'{key}.json', value)
        self.intents[key] = value
        for name, n in cost.items():
            self._counts[part][name] += n
        # Keep every outstanding physical attempt durable before work begins.
        if self.persistent:
            path = self.persistent/'INFLIGHT.json'
            old = read_json(path) if path.exists() else {'plan_hash': self.hash, 'attempts': []}
            if old['plan_hash'] != self.hash:
                raise ValueError('Durable owner mismatch')
            old['attempts'] = sorted(set(old['attempts']) | {key})
            write_json(path, old)
            if read_json(path) != old:
                raise ValueError('Durable intent verification')
        return key, None

    def commit(self, key, value):
        result = {'schema_version': 1, 'work_id': key, 'intent': self.intents[key], 'value': value}
        self.store.put(key, result); self.results[key] = result

    def generation(self, backend, request, scope, part):
        rendered = backend.render_messages(request.messages)
        prompt_ids = backend.tokenizer.encode(rendered, add_special_tokens=False)
        if len(prompt_ids)+512 > 8192:
            raise ValueError('Context incompatible; no truncation')
        dependency = {'model': backend.identity, 'request': asdict(request), 'scope': scope,
                      'prompt_ids': prompt_ids}
        key, old = self.begin(part, 'generation', dependency, {'generation': 1})
        if old is not None:
            return old
        raw, call = backend.generate(request)
        tokens = backend.last_generation
        if (call.snapshot != backend.identity['snapshot'] or call.seed != request.seed or
            call.context_hash != digest(rendered) or call.rendered_prompt != rendered or
            call.input_tokens != len(prompt_ids) or tokens['prompt_ids'] != prompt_ids or
            call.output_tokens != len(tokens['completion_ids']) or call.output_tokens > 512 or
            raw != tokens['raw']):
            raise ValueError('Native generation provenance mismatch')
        value = {'raw': raw, 'call': asdict(call), 'tokens': tokens,
                 'packet': c.parse(raw, asdict(request.task), call.stop_reason)}
        self.commit(key, value)
        return value


def safe(root):
    return {p.stem for p in (root/'attempts').glob('*.json')} == {
        p.stem for p in (root/'events/shards').glob('*.sha256')}


def files(root):
    for p in sorted(root.rglob('*')):
        if p.is_symlink():
            raise ValueError('Symlink in study')
        if not p.is_file() or p.name == '.lock':
            continue
        parts = p.relative_to(root).parts
        if parts[0] in ('bundles',):
            continue
        if 'checkpoints' in parts and any(x.startswith('step-') for x in parts):
            cp = p.parent
            # Each immutable step directory has JSON plus typed tensors.
            latest = sorted(cp.parent.glob('step-*'))[-1]
            if cp != latest:
                continue
        yield p


def package(root, path, kind):
    allowed = {'summary.json', 'mechanism_synthesis.json', 'allocation_summary.json', 'policy_results.json', 'assay_results.json', 'assay_support.json'}
    checks = {}
    path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(path, 'w', zipfile.ZIP_DEFLATED) as z:
        for p in files(root):
            n = p.relative_to(root).as_posix()
            if kind == 'SANITIZED' and n not in allowed:
                continue
            if kind != 'RECOVERY' and p.suffix == '.safetensors':
                continue
            checks[n] = file_hash(p); z.write(p, n)
        z.writestr('checksums.json', canonical(checks))
        z.writestr('HANDOFF.json', canonical({'kind': kind, 'version': 'allocation_executed_source_v3',
                                             'recovery_safe': safe(root)}))
    return {'path': str(path), 'sha256': file_hash(path), 'bytes': path.stat().st_size}


def persist(root, destination):
    if destination is None or not (root/'plan.json').exists():
        return
    from ...storage import storage_operation
    p = read_json(root/'plan.json')
    if destination.name != p['run_id']:
        raise ValueError('Wrong durable owner')
    pending = destination/'SNAPSHOT_PENDING.json'
    if pending.exists():
        raise ValueError('Pending snapshot; preserve evidence')
    snapshots=sorted((destination/'snapshots').glob('*'))
    if snapshots:
        latest=snapshots[-1]
        if (latest/'COMPLETE').read_text().strip()!=file_hash(latest/'index.json'):
            raise ValueError('Incomplete latest snapshot; no overwrite')
        index=read_json(latest/'index.json')['files']
        receipt_hash=index['receipt.json']
        if len(receipt_hash)!=64 or any(c not in '0123456789abcdef' for c in receipt_hash):
            raise ValueError('Invalid persisted receipt identity')
        previous_path=destination/'objects'/receipt_hash
        if previous_path.is_symlink() or file_hash(previous_path)!=receipt_hash:
            raise ValueError('Corrupt prior receipt')
        previous=read_json(previous_path)
        if previous['plan_hash']!=digest(p) or previous['version']!='allocation_executed_source_v3':
            raise ValueError('Durable plan/format collision')
        if not previous['safe'] and safe(root):
            raise ValueError('Unsafe historical boundary requires explicit recovery review')
    write_json(pending, {'plan_hash': digest(p)})
    with tempfile.TemporaryDirectory(dir=root.parent, prefix='.allocation-snapshot-') as temp:
        stage = Path(temp)
        # Metadata packs avoid thousands of Drive small-file operations. Typed
        # tensors remain separate content-addressed objects, so unchanged families
        # are never recopied inside a new monolithic ZIP at every update.
        info = package(root, stage/'state.zip', 'PRIVATE')
        tensors = {}
        for source in files(root):
            if source.suffix != '.safetensors': continue
            h = file_hash(source); tensors[source.relative_to(root).as_posix()] = h
            target = stage/'tensors'/h; target.parent.mkdir(exist_ok=True)
            if not target.exists(): os.link(source,target)
        write_json(stage/'receipt.json', {'sha256': info['sha256'], 'safe': safe(root),
                                         'tensors':tensors,
                                         'plan_hash': digest(p), 'version': 'allocation_executed_source_v3'})
        storage_operation('snapshot', stage, destination, timeout_seconds=600)
    pending.unlink()
    if safe(root):
        (destination/'INFLIGHT.json').unlink(missing_ok=True)


def restore(destination, root):
    if root.exists() or any((destination/n).exists() for n in ('SNAPSHOT_PENDING.json', 'INFLIGHT.json')):
        raise ValueError('Absent destination and safe latest snapshot required')
    snaps = sorted((destination/'snapshots').glob('*'))
    if not snaps:
        raise ValueError('No snapshot')
    latest = snaps[-1]
    if (latest/'COMPLETE').read_text().strip() != file_hash(latest/'index.json'):
        raise ValueError('Incomplete latest snapshot')
    idx = read_json(latest/'index.json')['files']
    def obj(name):
        h = idx[name]
        if len(h) != 64 or any(c not in '0123456789abcdef' for c in h):
            raise ValueError('Bad content address')
        path = destination/'objects'/h
        if path.is_symlink() or file_hash(path) != h:
            raise ValueError('Corrupt snapshot')
        return path
    receipt = read_json(obj('receipt.json'))
    if not receipt['safe'] or receipt['version'] != 'allocation_executed_source_v3':
        raise ValueError('Unsafe snapshot')
    z, checks = archive(obj('state.zip'), receipt['sha256'])
    try:
        if digest(json.loads(z.read('plan.json'))) != receipt['plan_hash']:
            raise ValueError('Wrong snapshot plan')
        root.mkdir(parents=True, mode=0o700)
        for n in checks:
            path = root/n; path.parent.mkdir(parents=True, exist_ok=True)
            with z.open(n) as a, path.open('wb') as b:
                shutil.copyfileobj(a, b)
    finally:
        z.close()
    from ...artifacts import safe_relative
    for name,h in receipt.get('tensors',{}).items():
        safe_relative(name)
        if not name.endswith('.safetensors') or idx.get('tensors/'+h)!=h:
            raise ValueError('Snapshot tensor identity mismatch')
        source=obj('tensors/'+h);target=root/name
        if target.exists(): raise ValueError('Duplicate snapshot tensor')
        target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(source,target)
        if file_hash(target)!=h: raise ValueError('Restored tensor checksum mismatch')
    Wallet(root, read_json(root/'plan.json'))
    return {'restored': True, 'model_calls': 0}


def export(root, stage, destination=None):
    from ...storage import persist_bundle
    export_name = stage if safe(root) else stage+'-unsafe-'+str(time.time_ns())
    immutable(root/'exports'/f'{export_name}.json',
              {'stage': stage, 'safe': safe(root)})
    out = {}
    kinds=('PRIVATE','SANITIZED','RECOVERY') if (root/'plan.json').exists() else ('PRIVATE','SANITIZED')
    for kind in kinds:
        path = root.parent/'bundles'/f'{root.name}-{kind}-{time.time_ns()}.zip'
        out[kind] = package(root, path, kind)
        if destination:
            persist_bundle(path, destination/'bundles'/path.name, timeout_seconds=600)
    persist(root, destination)
    return out
