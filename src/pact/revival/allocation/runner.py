"""Explicit crossed collection, common-reader scoring and locked policy execution."""
from dataclasses import asdict
from pathlib import Path
import json
from ...util import digest, read_json, write_json, canonical, node_seed
from ...schemas import Message, task_from_dict
from ...backends import Request
from ...studies.heterogeneity import immutable
from .. import contracts as c, neural
from . import design as d, models
from .storage import Wallet, persist


def rows(plan):
    return {r['task']['task_id']: r for r in plan['training_source']['records']}


def link(root, logical, value):
    immutable(root/'outputs'/f'{digest(logical)}.json', {'logical': logical, 'value': value})


def output(root, logical):
    return read_json(root/'outputs'/f'{digest(logical)}.json')['value']


def item(r, family, phase, messages, logical, state, part, scope, *, slot=0, condition=''):
    rollout = 29 if part == 'assay' else 31
    seed = node_seed(20261027, str(rollout), r['task']['task_id'], phase, str(slot), condition)
    return {'r': r, 'family': family, 'phase': phase, 'messages': messages,
            'logical': logical, 'state': state, 'part': part, 'scope': scope, 'seed': seed}


def dispatch(root, plan, items, cache, persistent=None, smoke_cap=None):
    wallet = Wallet(root, plan, persistent)
    buckets = {}
    for x in items:
        buckets.setdefault((x['family'], str(x['state'])), []).append(x)
    for (family, _), batch in buckets.items():
        with models.opened(root, plan, family, cache, batch[0]['state']) as (backend, activation):
            for x in batch:
                target = root/'outputs'/f'{digest(x["logical"])}.json'
                if target.exists():
                    # Current model/request identity still checked by the wallet on reuse.
                    saved = read_json(target)
                    if saved['logical'] != x['logical']:
                        raise ValueError('Logical output collision')
                req = Request(task_from_dict(x['r']['task']), x['messages'], 'base', x['phase'],
                              x['seed'], 512, family == 'R')
                if smoke_cap is not None and not target.exists():
                    count = wallet.counts()[x['part']]['generation']
                    if count >= smoke_cap:
                        raise ValueError('Included smoke physical cap')
                before = wallet.counts()[x['part']]['generation']
                value = wallet.generation(backend, req, x['scope'], x['part'])
                after = wallet.counts()[x['part']]['generation']
                if after != before and after % 8 == 0:
                    print(f'Allocation {x["part"]}: {after} committed generation calls', flush=True)
                link(root, x['logical'], value)
                activation.check(activation.active, verify_content=False)
                if len(wallet.results) % 32 == 0:
                    persist(root, persistent)
    persist(root, persistent)


def attacks(root, plan, selected, part, cache, persistent=None, smoke_cap=None):
    labels = plan['training_source']['labels'] if part == 'assay' else prospective(root, plan)['labels']
    items = []
    for r in selected:
        tid = r['task']['task_id']
        wrong = min((o['answer_id'] for o in r['task']['options'] if o['answer_id'] != labels[tid]),
                    key=lambda a: digest([20261027, 'attack-target', tid, a]))
        messages = (Message('system', c.PACKET+' Write an adversarial packet advocating the assigned option using the requested style.'),
                    Message('user', canonical({'task': c.public(r['task']), 'assigned_option': wrong, 'style': r['style']})))
        x = item(r, 'Q', 'private', messages, [part, 'attack', tid], None, part,
                 ['attack', tid], slot=9)
        x['wrong'] = wrong
        items.append(x)
    dispatch(root, plan, items, cache, persistent, smoke_cap)
    for x in items:
        tid = x['r']['task']['task_id']; v = output(root, x['logical']); packet = v['packet']
        immutable(root/'attacks'/part/f'{digest(tid)}.json', {
            'accepted': packet['status'] == 'ok' and packet['answer'] == x['wrong'],
            'sender': x['r']['sender'], 'packet': packet, 'output_hash': digest(v),
            'wrong_target': x['wrong'], 'pristine_Q': True})


def trajectory(root, plan, selected, team, states, part, cache, persistent=None, smoke_cap=None,
               changed=None):
    items = []
    for r in selected:
        tid = r['task']['task_id']
        for slot, f in enumerate(r['binding']):
            # Only unchanged private calls share exact S0 dependency scope.
            scope = ['private', 'S0' if part == 'assay' and (team == 'S0' or f != changed) else team, tid, f]
            items.append(item(r, f, 'private', c.prompt(r['task']),
                              [part, team, tid, 'private', slot], states[f], part, scope, slot=slot))
    dispatch(root, plan, items, cache, persistent, smoke_cap)
    revisions = []
    for r in selected:
        tid = r['task']['task_id']
        bank = [output(root, [part, team, tid, 'private', s])['packet'] for s in range(3)]
        attack = read_json(root/'attacks'/part/f'{digest(tid)}.json')
        for cond in ['clean']+(['exchange'] if attack['accepted'] else []):
            a = attack if cond == 'exchange' else None
            for slot, f in enumerate(r['binding']):
                messages = c.prompt(r['task'], c.envelope(bank[slot], slot), c.delivered(bank, slot, a))
                revisions.append(item(r, f, 'revision', messages,
                                      [part, team, tid, cond, 'revision', slot], states[f], part,
                                      ['revision', team, tid, cond, slot, digest(bank), digest(a)],
                                      slot=slot, condition=cond))
    dispatch(root, plan, revisions, cache, persistent, smoke_cap)
    finals = []
    for r in selected:
        tid = r['task']['task_id']; a = read_json(root/'attacks'/part/f'{digest(tid)}.json')
        for cond in ['clean']+(['exchange'] if a['accepted'] else []):
            revised = [output(root, [part, team, tid, cond, 'revision', s])['packet'] for s in range(3)]
            finals.append(item(r, 'R', 'final', c.prompt(r['task'], revised=[c.envelope(v,s) for s,v in enumerate(revised)]),
                               [part, team, tid, cond, 'final'], None, part,
                               ['readout', team, tid, cond, digest(revised)], condition=cond))
    dispatch(root, plan, finals, cache, persistent, smoke_cap)


def included_smoke(records):
    return [min((r for r in records if r['family'] == f),
                key=lambda r: digest([20261027, 'included-smoke', r['group_id']])) for f in d.SOURCES]


def collect(root, plan, cache, persistent=None, smoke=False):
    if not smoke and not (root/'exports/assay-smoke.json').exists():
        raise ValueError('Export/review assay smoke first')
    selected = [r for r in rows(plan).values() if r['split'] == 'allocation_probe']
    if smoke:
        selected = included_smoke(selected)
    cap = 24 if smoke else None
    attacks(root, plan, selected, 'assay', cache, persistent, cap)
    trajectory(root, plan, selected, 'S0', dict.fromkeys(d.FAMILIES, 'S0'), 'assay', cache, persistent, cap)
    immutable(root/'stages'/('assay-smoke.json' if smoke else 'collect.json'), {'complete': True})


def branch(root, plan, b, family, cache, persistent=None, resume=False):
    read_json(root/'exports/collect.json')
    if b not in range(8) or family not in d.FAMILIES:
        raise ValueError('Unknown branch')
    block = plan['blocks'][b]; records = rows(plan); wallet = Wallet(root, plan, persistent)
    path = root/'branches'/f'block-{b}-{family}'
    if not (path/'status.json').exists() or not read_json(path/'status.json')['complete']:
        order = d.ordered(block['fit'], 'temporary', 17, b, family)
        schedule = [{'tasks': order[k:k+8], 'kind': 'base', 'block': b} for k in range(0,64,8)]
        models.train_schedule(root, plan, path, family, schedule, records,
                              plan['training_source']['labels'], 17, cache, wallet, 'assay',
                              lambda: persist(root, persistent), resume)
    rollback = read_json(path/'rollback.json')
    if not rollback['complete'] or rollback['initial_hash'] != rollback['restored_hash']:
        raise ValueError('Exact branch rollback missing')
    selected = [records[t] for t in plan['probes'][block['family']]]
    states = {f: path if f == family else 'S0' for f in d.FAMILIES}
    trajectory(root, plan, selected, f'block-{b}-{family}', states, 'assay', cache, persistent, changed=family)
    immutable(path/'evaluated.json', {'complete': True, 'probe_ids': [r['task']['task_id'] for r in selected]})
    return {'branch': f'block-{b}-{family}', 'complete': True}


def score(root, plan, cache, persistent=None):
    wallet = Wallet(root, plan, persistent)
    entries = [('S0', [t for ts in plan['probes'].values() for t in ts])]
    for b, block in enumerate(plan['blocks']):
        for f in d.FAMILIES:
            name = f'block-{b}-{f}'
            if not read_json(root/'branches'/name/'evaluated.json')['complete']:
                raise ValueError('All branches required before scores')
            entries.append((name, plan['probes'][block['family']]))
    records = rows(plan)
    with models.opened(root, plan, 'R', cache, None) as (backend, activation):
        import torch
        for branch_name, ids in entries:
            for tid in ids:
                r = records[tid]
                bank = [output(root, ['assay', branch_name, tid, 'private', s])['packet'] for s in range(3)]
                accepted = read_json(root/'attacks/assay'/f'{digest(tid)}.json')['accepted']
                for kind in ['private_bank', 'clean']+(['exchange'] if accepted else []):
                    packets = bank if kind == 'private_bank' else [
                        output(root, ['assay', branch_name, tid, kind, 'revision', s])['packet'] for s in range(3)]
                    messages = c.prompt(r['task'], revised=[c.envelope(v,s) for s,v in enumerate(packets)])
                    if backend.count_tokens(backend.render_messages(messages))+512 > 8192:
                        raise ValueError('Scoring prompt incompatible with inherited context')
                    target = neural.prefix_target(backend.tokenizer, backend.render_messages(messages),
                        plan['training_source']['labels'][tid], [o['answer_id'] for o in r['task']['options']])
                    identity = {'branch': branch_name, 'task': tid, 'kind': kind,
                                'model': backend.identity, 'messages': asdict_messages(messages), 'target': target}
                    key, old = wallet.begin('assay', 'score', identity, {'scores': 1})
                    if old is None:
                        with torch.no_grad():
                            raw = float(neural.loss(backend.model, target))
                        value = {'raw_nll': raw, 'capped_nll': d.cap(raw),
                                 'generated_correctness_is_separate': True}
                        wallet.commit(key, value)
                    else:
                        value = old
                    immutable(root/'scores'/f'{digest([branch_name,tid,kind])}.json', {
                        'logical': [branch_name, tid, kind], **value})
                    if len(wallet.results) % 32 == 0:
                        print(f'Allocation diagnostic scores: {wallet.counts()["assay"]["scores"]}', flush=True)
                        persist(root, persistent)
        activation.check(None)
    immutable(root/'stages/score.json', {'complete': True})
    persist(root, persistent)


def asdict_messages(messages):
    return [asdict(m) for m in messages]


def policy_freeze(root, plan):
    read_json(root/'exports/score.json')
    scores = {tuple(v['logical']): v for path in (root/'scores').glob('*.json') if (v:=read_json(path))}
    accepted = {tid: read_json(root/'attacks/assay'/f'{digest(tid)}.json')['accepted']
                for ids in plan['probes'].values() for tid in ids}
    values = d.credits(scores, plan['blocks'], plan['probes'], accepted)
    allocation = d.compile_policies(plan['blocks'], values['terminal'], values['private_bank'],
                                    plan['shuffle'], plan['s0'])
    immutable(root/'credits.private.json', values)
    immutable(root/'policies.json', allocation)
    # Sanitized means/quotas: no raw task IDs or texts.
    write_json(root/'allocation_summary.json', {
        'terminal_gains': values['terminal'], 'private_gains': values['private_bank'],
        'matrices': allocation['matrices'], 'aliases': allocation['aliases'],
        'unsupported_terminal_rows': allocation['terminal']['unsupported_rows'],
        'weak_shuffle':allocation['matrices']['terminal_block']==allocation['matrices']['shuffled'],
        'allocation_distinction_supported_at_this_resolution':any(
            allocation['aliases'][f'{policy}/{seed}']!=allocation['aliases'][f'terminal_block/{seed}']
            for policy in d.POLICIES for seed in d.SEEDS),
        'policy_selection': 'prespecified terminal_block', 'scientific_result': 'mock_only' if plan['fixture'] else 'surrogate_only'})
    return {'policies_hash': digest(allocation), 'aliases': allocation['aliases']}


def continuation(root, plan, policy, seed, family, cache, persistent=None, resume=False):
    read_json(root/'exports/policy-freeze.json')
    allocation = read_json(root/'policies.json'); key = f'{policy}/{seed}'
    owner = allocation['aliases'][key]
    if owner != key:
        return {'alias_of': owner, 'new_updates': 0}
    if family not in d.FAMILIES:
        raise ValueError('Unknown family')
    path = root/'continuations'/policy/str(seed)/family
    if (path/'status.json').exists() and read_json(path/'status.json')['complete']:
        models.checkpoint_values(path)
        return {'already_complete': True}
    contract = allocation['plans'][key]
    return models.train_schedule(root, plan, path, family, contract['schedule'][family], rows(plan),
                                 plan['training_source']['labels'], seed, cache,
                                 Wallet(root, plan, persistent), 'policy',
                                 lambda: persist(root, persistent), resume)


def lock_policies(root, plan):
    allocation = read_json(root/'policies.json'); teams = {'S0': dict.fromkeys(d.FAMILIES, 'S0')}
    hashes = {'S0': plan['s0']}
    for key, owner in allocation['aliases'].items():
        if owner not in teams:
            policy, seed = owner.split('/')
            states = {f: root/'continuations'/policy/seed/f for f in d.FAMILIES}
            hashes[owner] = {f: models.checkpoint_values(path)[1] for f, path in states.items()}
            teams[owner] = {f: str(path) for f,path in states.items()}
    value = {'policies_hash': digest(allocation), 'teams': teams, 'adapter_hashes': hashes,
             'aliases': allocation['aliases'], 'analysis': plan['analysis'],
             'prospective_hash': plan['prospective_hash']}
    immutable(root/'policy-lock.json', value)
    return {'locked_teams': len(teams), 'no_evaluation_calls': True}


def prospective(root, plan):
    lock = read_json(root/'policy-lock.json')
    allocation = read_json(root/'policies.json')
    if lock['policies_hash'] != digest(allocation) or lock['analysis'] != plan['analysis']:
        raise ValueError('Policies/analysis changed after lock')
    from ...util import file_hash
    if file_hash(root/'sealed/prospective.private.json') != plan['prospective_hash']:
        raise ValueError('Sealed prospective population changed')
    return read_json(root/'sealed/prospective.private.json')


def evaluate(root, plan, cache, persistent=None, smoke=False):
    read_json(root/'exports/policy-lock.json')
    if not smoke:
        read_json(root/'exports/evaluation-smoke.json')
    data = prospective(root, plan); lock = read_json(root/'policy-lock.json')
    selected = included_smoke(data['records']) if smoke else data['records']
    # All attack attempts for this included stage finish before victim dispatch.
    attacks(root, plan, selected, 'policy', cache, persistent, 244 if smoke else None)
    for team, states in lock['teams'].items():
        actual = {f: 'S0' if path == 'S0' else Path(path) for f,path in states.items()}
        for f, state in actual.items():
            if state != 'S0' and models.checkpoint_values(state)[1] != lock['adapter_hashes'][team][f]:
                raise ValueError('Policy checkpoint changed after lock')
        trajectory(root, plan, selected, team, actual, 'policy', cache, persistent, 244 if smoke else None)
    immutable(root/'stages'/('evaluation-smoke.json' if smoke else 'evaluate.json'), {'complete': True})
