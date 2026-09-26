"""Versioned child design; imports the closed natural bank without new draws."""
import copy
from collections import Counter
from pathlib import Path
import random
import tempfile
import zipfile

from ..artifacts import ShardStore
from ..environment import code_identity
from ..replay import choose_pair
from ..util import canonical, digest, file_hash, node_seed, read_json, write_json
from .feasibility import read_review
from .receiver_supervision import packet_from_dict
from .specialization_collect import collect, immutable
from .specialization_study import load_plan as load_parent, offline_backend, report as parent_report, validate_recovery

SOURCE = 'controlled_private_packets_v1'
ESTIMATOR = 'controlled_slot_delta_v1'
VARIANT = 'controlled_specialization_fixed_bank_v1'
RUN_ID = 'qwen3-controlled-specialization-001'
ARMS = ('controlled_uniform_sft', 'controlled_local_specialization', 'controlled_continuation_specialization')
PARENT_SHA = '555d9bd2e724c59ca4a91db156d450f814d0149ed6413922e965c3a85fb4e69f'
PARENT_PLAN = '99ff21066f93f26fae33e6cbf70623313b0f9acd09e9e6d49e0702674af5131c'
EFFECTIVE = ['eef7b26388dabd812e7519b6cef0ececd1737bd9989c5a5715378694dcbad7ad',
             '505e04c7518134abfc38222ab7e507ee392c1913292cc387bcc2c7ddd74ce18c',
             '07ae09c5803bd2603beb88097208da3929a61b98a9f1bd691b4244a53cd79662']


def budgets():
    def cap(n, tokens): return {'generation_calls_upper_bound': n, 'generated_tokens_upper_bound': tokens}
    return {'acquire': cap(32*2*2, 32*2*2*256),
            'primary': cap(64*3*2*2*4, 64*3*2*2*832),
            'order': cap(8*2*3*2*2*4, 8*2*3*2*2*832),
            'calibration': cap(5*2*2*4, 5*2*2*832),
            'evaluate_per_arm': cap(32*2*8, 32*2*1664),
            'total': cap(128+3072+768+80+2048, 32768+638976+159744+16640+425984),
            'answer_scoring_forwards': 192, 'packet_scoring_forwards': 192,
            'updates_per_actor': 32, 'updates_per_arm': 96, 'total_updates': 288}


def unpack_review(bundle, sha, root, *, max_members=40000):
    """Safe reader validates paths, sizes and checksums before copying metadata."""
    content = read_review(Path(bundle), sha, max_members=max_members, max_bytes=512*1024**2, allow_text=True)
    with zipfile.ZipFile(bundle) as archive:
        for name in content:
            path = root/name
            raw = archive.read(name)
            if path.exists() and path.read_bytes() != raw: raise ValueError('Imported artifact changed')
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(raw)
            if '/shards/' in name: path.with_suffix('.sha256').write_text(file_hash(path))
    return content


def characterize_parent(root, *, fixture=False):
    plan = load_parent(root)
    if not fixture and (digest(plan) != PARENT_PLAN or plan['synthetic_fixture'] or
                        plan['frozen_arm']['checkpoint']['effective_actor_tensor_hashes'] != EFFECTIVE):
        raise ValueError('Wrong stopped parent or effective actors')
    if read_json(root/'HANDOFF.json')['kind'] != 'specialization_fixed_bank': raise ValueError('Wrong parent kind')
    validate_recovery(root, plan)
    saved_report = read_json(root/'specialization_results.json')
    # report writes deterministic derived files, only in the private import copy.
    if canonical(parent_report(root)) != canonical(saved_report): raise ValueError('Parent report reconstruction failed')
    support = collect(plan, offline_backend(plan), root, readonly=True)
    if canonical(support) != canonical(read_json(root/'candidate_support.json')): raise ValueError('Parent mask mismatch')
    counts = saved_report['generation_accounting']
    if (support['eligible_cells'] != 5 or support['supported_tasks'] != 2 or support['multi_tasks'] != 2
        or support['status'] != 'insufficient_assignment_support'
        or counts['teacher_forced_scores'] or saved_report['training_executed'] or saved_report['evaluation_executed']
        or any(v['attempted_calls'] for k,v in counts['by_stage'].items() if k != 'collection')
        or (not fixture and counts['attempted_calls'] != 1216)):
        raise ValueError('Parent is not the closed five-cell acquisition; no expanded calibration')
    anchors = sorted(ShardStore(root/'anchors').records(), key=lambda r:r['work_id'])
    cells = []; calibration = []
    for anchor in anchors:
        tr = anchor['trajectory']; tid = tr['task']['task_id']; gold = plan['labels'][tid]['answer_id']
        for i,pool in enumerate(anchor['candidates']):
            packets = [packet_from_dict(p) for p in pool]
            plus,minus,matched,reason = choose_pair(packets, gold, 32)
            categories = Counter('valid_correct' if p.parser_status == 'ok' and p.answer_id == gold else
                'valid_wrong' if p.parser_status == 'ok' else 'length_limited' if p.parser_status == 'length' else
                'abstention' if p.parser_status == 'abstention' else 'malformed_or_invalid' for p in packets)
            cells.append({'row_id':anchor['work_id'], 'task_id':tid, 'condition':tr['condition'], 'agent':i,
                          'categories':dict(categories), 'parser_statuses':[p.parser_status for p in packets],
                          'selector_rejection':reason, 'positive_index':plus, 'negative_index':minus,
                          'length_bin_matched':matched})
            if reason is None:
                calibration.append({'row_id':anchor['work_id'], 'agent':i,
                                    'positive':pool[plus], 'negative':pool[minus]})
    if len(anchors) != 64 or len(calibration) != 5: raise ValueError('Incomplete parent rows/calibration')
    diagnostic = {'source':'closed_parent_observations', 'cells':cells,
        'candidate_categories':dict(sum((Counter(c['categories']) for c in cells), Counter())),
        'selector_rejections':dict(Counter(c['selector_rejection'] or 'eligible' for c in cells)),
        'not_equivalent_to_coverage_or_agreement':True, 'new_calls':0}
    return plan, anchors, calibration, diagnostic


def build_plan(parent, anchors, calibration, exposure, source, *, parent_sha=PARENT_SHA):
    if (exposure.get('reviewed') is not True or not exposure.get('provenance') or
        exposure.get('development_used_for_optimization_or_outcome_selection') != []):
        raise ValueError('Review later development exposure before planning; never replace tasks')
    if len(calibration) != 5 or len(anchors) != 64: raise ValueError('Expected 64 rows and five natural cells')
    plan = copy.deepcopy(parent)
    plan.update(variant=VARIANT, source_variant=SOURCE, estimator=ESTIMATOR, run_id=RUN_ID,
        source=source, parent={'bundle_sha256':parent_sha, 'plan_hash':digest(parent), 'source':parent['source'],
                              'imported_calls':1216, 'new_parent_calls':0},
        budget=budgets(), arms=list(ARMS), development_exposure_review=exposure,
        donor_template='controlled_peer_template_v1', donor_validator='controlled_private_validator_v1',
        packet_score_definition='mean complete synthetic positive packet plus EOS under original actor prompt; rationale unreviewed',
        settings={**parent['settings'], 'practical_task_mean_l1':.10, 'minimum_practical_tasks':8,
                  'source_variant':SOURCE, 'estimator':ESTIMATOR, 'max_attempts_per_target':2})
    schedule = []
    for e in plan['selection']:
        if e['partition'] != 'fit': continue
        tid = e['task_id']; gold = plan['labels'][tid]['answer_id']
        seed = node_seed(plan['seed'], SOURCE, tid, 'wrong-option')
        wrong = random.Random(seed).choice(sorted(o['answer_id'] for o in plan['tasks'][tid]['options'] if o['answer_id'] != gold))
        schedule.append({'task_id':tid, 'family':e['family'], 'wrong_target_seed':seed,
            'targets':{kind:{'option':option, 'seeds':[node_seed(plan['seed'], SOURCE, tid, kind, j) for j in range(2)]}
                       for kind,option in (('positive',gold),('negative',wrong))}})
    def fixed_eight(namespace):
        return [e['task_id'] for family in ('arc_challenge','logiqa') for e in
                sorted((e for e in schedule if e['family']==family), key=lambda e:digest([SOURCE,namespace,e['task_id']]))[:4]]
    plan.update(donor_schedule=schedule, order_task_ids=fixed_eight('order-control'),
                review_task_ids=fixed_eight('packet-review'), anchors=anchors, natural_calibration=calibration)
    return plan


def plan_from_bundle(bundle, root, exposure, repo):
    if file_hash(bundle) != PARENT_SHA: raise ValueError('Wrong parent ZIP checksum')
    # Work in a temporary import first so a failed preflight cannot initialize a child.
    with tempfile.TemporaryDirectory(prefix='controlled-parent-') as tmp:
        imported = Path(tmp)
        unpack_review(bundle, PARENT_SHA, imported)
        parent, anchors, calibration, missing = characterize_parent(imported)
    plan = build_plan(parent, anchors, calibration, exposure, code_identity(repo))
    unpack_review(bundle, PARENT_SHA, root/'parent_metadata')
    immutable(root/'plan.json', plan)
    immutable(root/'parent_import_receipt.json', {**plan['parent'], 'parent_unchanged':True,
        'anchor_hashes':[digest(a) for a in anchors], 'natural_calibration_hash':digest(calibration),
        'verified_report_and_collection':True, 'metadata_only_not_weights':True})
    immutable(root/'natural_candidate_missingness.json', missing)
    if not (root/'state.json').exists(): write_json(root/'state.json', {'plan_hash':digest(plan), 'recovery_safe':True})
    return plan
