"""Pure, deterministic allocation arithmetic. No model or dataset access."""
import itertools
import math
from ...util import digest
from ...training.assignment import solve_assignment

VERSION = 'stage2-allocation-executed-source-v3'
ASSAY = 'pact-update-allocation-crossed-v3-003'
POLICY = 'pact-allocation-policy-evaluation-v3-002'
FAMILIES = ('Q', 'L', 'M')
SOURCES = ('arc_challenge', 'logiqa')
POLICIES = ('terminal_block', 'uniform', 'source_family', 'private_bank', 'shuffled')
SEEDS = (113, 227)
BLOCK_COUNTS = {'arc_challenge':3,'logiqa':5}
PROBE_COUNTS = {'arc_challenge':24,'logiqa':40}
SOURCE_WEIGHTS = {'arc_challenge':3/8,'logiqa':5/8}
BUDGET = {
    'assay': {'generation': 8112, 'updates': 192, 'training_forwards': 1536, 'scores': 2640},
    'policy': {'generation': 15616, 'updates': 2880, 'training_forwards': 23040, 'scores': 0},
    'synthetic': 0, 'synthetic_input_cap': 128,
    'generation': 23728, 'reserved_tokens': 12148736, 'updates': 3072,
    'training_forwards': 24576, 'scores': 2640,
}
ANALYSIS = {'bootstrap_replicates': 10000, 'bootstrap_seed': 20261027,
            'primary': ['terminal_block-minus-uniform', 'terminal_block-minus-source_family'],
            'interval_levels': [.95, .975], 'clean_tolerance': .02,
            'unit': 'source-stratified task groups; seeds and all views together',
            'loss_cap': 10., 'condition_weights': [.5, .5], 'tau': .2, 'balance': .1}
TRAIN = {'lr': 5e-5, 'betas': [.9, .999], 'eps': 1e-8, 'weight_decay': 0.,
         'clip': 1., 'warmup': 0, 'batch': 8, 'loss': 'unit-weight mean private-answer token NLL'}


def ordered(values, *namespace):
    return sorted(values, key=lambda v: digest([20261027, *namespace, v]))


def cap(raw):
    if not isinstance(raw, (float, int)) or not math.isfinite(raw) or raw < 0:
        raise ValueError('Nonfinite/negative diagnostic loss; technical stop')
    return min(float(raw), 10.)


def derangement(blocks):
    if {f:sum(b['family']==f for b in blocks) for f in SOURCES}!=BLOCK_COUNTS:
        raise ValueError('Exact three/five source blocks required')
    out = {}
    for source in SOURCES:
        indices = [i for i, b in enumerate(blocks) if b['family'] == source]
        choices = [v for v in itertools.permutations(indices) if all(a != b for a, b in zip(indices, v))]
        if not choices:
            raise ValueError('Source needs at least two blocks')
        chosen = min(choices, key=lambda v: digest([20261027, 'derangement', source, v]))
        out.update(zip(indices, chosen))
    return [out[i] for i in range(len(blocks))]


def quotas(scores):
    if len(scores)!=8: raise ValueError('Eight block rows required; no source reweighting')
    if any(len(row) != 3 for row in scores):
        raise ValueError('Three-family rows required')
    if any(any(v is None for v in r) and not all(v is None for v in r) for r in scores):
        raise ValueError('Partial technical score row; cannot silently change support')
    for row in scores:
        for v in row:
            if v is not None and not math.isfinite(v):
                raise ValueError('Nonfinite credit')
    result = solve_assignment([[-v if v is not None else None for v in r] for r in scores],
                              tau=.2, balance=.1)
    if result['status'] not in ('converged', 'no_eligible_rows'):
        raise ValueError('Assignment solver did not converge')
    rows = []
    for b, w in enumerate(result['weights']):
        if not sum(w):
            rows.append([4, 4, 4])
            continue
        raw = [12*x for x in w]
        row = [math.floor(x) for x in raw]
        order = sorted(range(3), key=lambda i: (-(raw[i]-row[i]), digest([20261027, 'quota-tie', b, i])))
        for i in order[:12-sum(row)]:
            row[i] += 1
        rows.append(row)
    return {'solver': result, 'quotas': rows,
            'unsupported_rows': [i for i, r in enumerate(scores) if all(v is None for v in r)]}


def source_family(terminal, blocks):
    """Enumerate the tiny feasible floor/ceil polytope, choose hash-minimum."""
    if {f:sum(b['family']==f for b in blocks) for f in SOURCES}!=BLOCK_COUNTS:
        raise ValueError('Integer constraint witness: expected three/five source rows')
    if len(terminal)!=len(blocks) or any(len(row)!=3 or sum(row)!=12 or
            any(type(x) is not int or x<0 for x in row) for row in terminal):
        raise ValueError('Integer constraint witness: each input row requires three nonnegative integers summing to 12')
    out = [None]*len(blocks)
    for source in SOURCES:
        ix = [i for i, b in enumerate(blocks) if b['family'] == source]
        totals = [sum(terminal[b][i] for b in ix) for i in range(3)]
        floor = [v//len(ix) for v in totals]
        candidates = []
        for mask in itertools.product((0, 1), repeat=3):
            row = [floor[i]+mask[i] for i in range(3)]
            if sum(row) == 12 and all(row[i] <= math.ceil(totals[i]/len(ix)) for i in range(3)):
                candidates.append(row)
        feasible = [v for v in itertools.product(candidates, repeat=len(ix))
                    if all(sum(r[i] for r in v) == totals[i] for i in range(3))]
        if not feasible:
            raise ValueError(f'Integer constraint witness: source={source}, rows={len(ix)}, totals={totals}, row_sum=12, floors={floor}')
        chosen = min(feasible, key=lambda v: digest([20261027, 'source-family', source, totals, v]))
        for b, row in zip(ix, chosen):
            out[b] = row
    return out


def schedules(blocks, extra, seed):
    if len(blocks) != 8 or any(len(b['fit']) != 64 for b in blocks):
        raise ValueError('Eight immutable 64-task blocks required')
    if len(extra) != 8 or any(len(r) != 3 or sum(r) != 12 or
                              any(type(x) is not int or x < 0 for x in r) for r in extra):
        raise ValueError('Exactly 12 integer extra slots per block')
    result = {}
    for i, f in enumerate(FAMILIES):
        entries = []
        for b, block in enumerate(blocks):
            for kind, count in [('base', 8), ('extra', extra[b][i])]:
                for k in range(count):
                    cycle, offset = divmod(k, 8)
                    pool = ordered(block['fit'], 'pool', seed, f, b, kind, cycle)
                    entries.append({'block': b, 'kind': kind, 'cycle': cycle, 'slot': k,
                                    'tasks': pool[offset*8:(offset+1)*8]})
        # Policy name and score magnitudes never enter ordering or RNG namespaces.
        result[f] = sorted(entries, key=lambda e: digest(
            [20261027, 'interleave', seed, f, e['block'], e['kind'], e['slot']]))
    assert sum(map(len, result.values())) == 288
    assert all(64 <= len(v) <= 160 for v in result.values())
    return result


def compile_policies(blocks, terminal, private, shuffle, s0, execution_contract=None):
    if shuffle != derangement(blocks):
        raise ValueError('Frozen shuffle changed')
    d, p = quotas(terminal), quotas(private)
    matrices = {'terminal_block': d['quotas'], 'uniform': [[4]*3 for _ in blocks],
                'source_family': source_family(d['quotas'], blocks), 'private_bank': p['quotas'],
                'shuffled': [d['quotas'][i] for i in shuffle]}
    plans, aliases, seen = {}, {}, {}
    for seed in SEEDS:
        for policy in POLICIES:
            key = f'{policy}/{seed}'
            contract = {'s0': s0, 'seed': seed, 'train': TRAIN,
                        'execution_contract':execution_contract or {'fixture_design':VERSION},
                        'prompt_contract': 'unchanged_revival_private_answer_prefix',
                        'schedule': schedules(blocks, matrices[policy], seed),
                        'rng': 'persistent family optimizer; seed/family stream; same namespace across policies'}
            identity = digest(contract)
            aliases[key] = seen.setdefault(identity, key)
            plans[key] = contract
    return {'version':VERSION,'child_id':POLICY,'portfolio_owner':ASSAY,'allocation_source_weights':SOURCE_WEIGHTS,'matrices': matrices, 'terminal': d, 'private_bank': p, 'plans': plans,
            'aliases': aliases, 'primary': 'terminal_block', 'analysis': ANALYSIS}


def credits(scores, blocks, probes, accepted):
    """Require every common-support score; reject technical missingness."""
    terminal, private, details = [], [], []
    def get(branch, task, kind):
        value = scores[(branch, task, kind)]
        cap(value['raw_nll'])
        if value['capped_nll'] != cap(value['raw_nll']):
            raise ValueError('Capped score mismatch')
        return value['capped_nll']
    for b, block in enumerate(blocks):
        ids = probes[block['family']]
        attacks = [t for t in ids if accepted[t]]
        ds, ps = [], []
        for f in FAMILIES:
            branch = f'block-{b}-{f}'
            gains = {kind: [get('S0', t, kind)-get(branch, t, kind) for t in
                           (attacks if kind == 'exchange' else ids)]
                     for kind in ('clean', 'exchange', 'private_bank')}
            mean = lambda k: sum(gains[k])/len(gains[k]) if gains[k] else None
            ds.append(.5*mean('clean')+.5*mean('exchange') if attacks else None)
            ps.append(mean('private_bank'))
            details.append({'block': b, 'family': f, 'clean_count': len(ids),
                            'exchange_count': len(attacks), 'private_count': len(ids),
                            'gains': gains, 'clean_minus_private': mean('clean')-mean('private_bank'),
                            'unsupported_reason': None if attacks else 'zero_accepted_source_attacks'})
        terminal.append(ds); private.append(ps)
    return {'terminal': terminal, 'private_bank': private, 'details': details}
