"""Model-free derivative census of the closed adjudication parent."""
from collections import Counter, defaultdict
from dataclasses import dataclass, asdict
from pathlib import Path
import argparse
import json
import shutil
import tempfile
import time
import zipfile

from ..util import read_json, write_json, digest, file_hash, canonical
from ..evaluation import rate
from ..environment import code_identity
from ..artifacts import run_lock
from .heterogeneity import immutable
from .gpqa_data import outside_git
from . import adjudication as parent
from .adjudication_contracts import from_record, selector
from .adjudication_metrics import report as parent_report, paired

STUDY = 'pact-adjudication-forensics-001'
CHILD = 'pact-rationale-span-intervention-001'
SEED = 20261013
PARENT_SHA = '2abda348768e65ec8289f51eee48f8f5653ee0b36d30aff8c9093a7dc9c2ae8f'
PARENT_PLAN = 'ab855a15eafe32513dda3ae0f2363921683dbbb713bbf4d3286c57d169fc8e3d'
PARENT_POOL = 'd7b806510441b23547f9ccaa10a194777a0ac0a573b17ae8085dac1c59ea8c05'


def private_root(root, mock=False):
    root = Path(root)
    if not mock: outside_git(root)
    if any(p.is_symlink() for p in (root, *root.parents)):
        raise ValueError('Symlink private destination')
    root.mkdir(parents=True, exist_ok=True)
    return root


def lines(path):
    if Path(path).is_symlink() or Path(path).stat().st_size>256*1024**2:raise ValueError('Private JSONL size/type bound')
    return [json.loads(s) for s in Path(path).read_text().splitlines() if s.strip()]


def save_lines(path, rows):
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    text = ''.join(canonical(r)+'\n' for r in rows)
    if path.exists() and path.read_text() != text:
        raise ValueError('Immutable derived view changed: '+path.name)
    path.write_text(text)


def rank(*values):
    return digest([SEED, STUDY, *values])


def import_parent(root, bundle, sha, mock=False):
    root = private_root(root, mock)
    if not mock and sha != PARENT_SHA: raise ValueError('Exact completed PRIVATE parent required')
    if (root/'parent_import_receipt.json').exists():
        receipt = check(root)
        if receipt['bundle_sha256'] != sha or receipt['fixture'] != mock:
            raise ValueError('Incompatible parent resume')
        return receipt
    if (root/'parent').exists(): raise ValueError('Partial import; preserve and inspect')
    parent.unpack(bundle, sha, root/'parent')
    p = parent.load(root/'parent')
    if p['fixture'] != mock: raise ValueError('Fixture/real mismatch')
    # Recompute into this derivative copy only; never change the source archive/root.
    old = read_json(root/'parent/summary.json')
    out = parent_report(root/'parent')
    if out != old: raise ValueError('Parent reconstruction differs')
    pool = read_json(root/'parent/pool.json')
    counts = {'tasks':len(read_json(root/'parent/bank.json')['records']),
              'clean':sum(v['scored'] for v in out['clean'].values()),
              'clean_calls':out['accounting']['stage_attempts'].get('clean',0),
              'no_candidate':out['missingness']['technical_nonexecuted'].get('empty_selectable',0),
              'rewrites':len(pool['attempts']), 'accepted':sum(r['accepted'] for r in pool['attempts']),
              'victims':out['accounting']['stage_attempts'].get('attack',0),
              'unavailable':out['missingness']['attack_unobserved']}
    if out['accounting']['unresolved'] or not out['missingness']['recovery_safe'] or out['missingness']['clean_unobserved']:
        raise ValueError('Complete safe parent required')
    if not mock:
        if digest(p)!=PARENT_PLAN or pool['pool_hash']!=PARENT_POOL:
            raise ValueError('Parent plan/pool mismatch')
        if counts != dict(tasks=230,clean=2760,clean_calls=2726,no_candidate=34,rewrites=400,accepted=369,victims=2214,unavailable=186):
            raise ValueError('Parent census anchors differ')
    inventory={f.relative_to(root/'parent').as_posix():file_hash(f) for f in sorted((root/'parent').rglob('*')) if f.is_file()}
    receipt={'schema_version':1,'study':STUDY,'fixture':mock,'bundle_sha256':sha,
             'parent_plan':digest(p),'parent_pool':pool['pool_hash'],'counts':counts,'files':inventory,
             'training_allowed':False,'new_model_calls':0}
    immutable(root/'parent_import_receipt.json',receipt)
    return receipt


def check(root):
    root=Path(root);r=read_json(root/'parent_import_receipt.json')
    if not r['fixture']: outside_git(root)
    for n,h in r['files'].items():
        from ..artifacts import safe_relative
        safe_relative(n)
        f=root/'parent'/n
        if f.is_symlink() or not f.is_file() or file_hash(f)!=h: raise ValueError('Derivative parent mutated')
    return r


@dataclass(frozen=True)
class Opportunity:
    task_id: str
    group_id: str
    stratum: str
    dataset: str
    judge: str
    mode: str
    T: bool | None
    O: bool
    Y: bool | None
    constrained: bool


def opportunity_metrics(rows):
    observed=[r for r in rows if r['T'] is not None and r['Y'] is not None]
    if any(r['constrained'] and r['Y'] and not r['O'] for r in observed):
        raise ValueError('Selector exceeds selectable coverage')
    n=len(observed);count=lambda f:sum(f(r) for r in observed)
    gains=count(lambda r:not r['T'] and r['Y']);loss=count(lambda r:r['T'] and not r['Y'])
    assert gains-loss == count(lambda r:r['Y'])-count(lambda r:r['T'])
    return {'intended':len(rows),'scored':n,'missing':len(rows)-n,
            'quadrants':{f'{t}{o}':count(lambda r:r['T']==bool(t) and r['O']==bool(o)) for t in (0,1) for o in (0,1)},
            'opportunity':count(lambda r:not r['T'] and r['O']),
            'rescue':rate(count(lambda r:not r['T'] and r['O'] and r['Y']),count(lambda r:not r['T'] and r['O'])),
            'regression':rate(loss,count(lambda r:r['T'])),
            'covered_regression':rate(count(lambda r:r['T'] and r['O'] and not r['Y']),count(lambda r:r['T'] and r['O'])),
            'structural_selector_failures':count(lambda r:r['constrained'] and r['T'] and not r['O'] and not r['Y']),
            'construction':rate(count(lambda r:not r['O'] and r['Y']),count(lambda r:not r['O'])),
            'gains':gains,'losses':loss,'net':rate(gains-loss,n),
            'potential_union_oracle_only':rate(count(lambda r:r['T'] or r['O']),n),
            'potential_union_is_free_upper_bound':False,
            'paired_difference':paired([{**r,'clean':r['T'],'attacked':r['Y']} for r in rows])}


def transition(clean, attacked, status):
    if clean is None:return 'unavailable_original'
    if attacked is None:return 'unavailable_'+status
    if attacked:return 'correct_to_correct' if clean else 'wrong_to_correct'
    if not clean:return 'wrong_to_wrong'
    return 'correct_to_valid_wrong' if status=='ok' else 'correct_to_'+status


def census(root):
    root=Path(root);receipt=check(root);p=root/'parent'
    clean=lines(p/'clean_per_task.jsonl');attacks=lines(p/'attacked_per_task.jsonl')
    records={r['task']['task_id']:r for r in read_json(p/'bank.json')['records']}
    lookup={(r['task_id'],r['model'],r['mode']):r for r in clean}
    plan=parent.load(p)
    attempts={(r['task_id'],r['style']):r for r in read_json(p/'pool.json')['attempts']}
    eligible={r['task_id']:r for r in plan['eligible']}
    _,saved,_,_=parent.journal(p,plan)
    dispatched={v['intent']['record_id']:v for v in saved.values()}
    identities={k:read_json(p/'identities'/f'{k}.json') for k in plan['models']}
    def evidence(key):
        v=dispatched.get(key)
        return None if v is None else {'result_hash':digest(v),'work_id':v['intent']['work_id'],
            'call':v['call'],'raw_response':v['raw']}
    relational=[]
    for c in clean:
        rec=records[c['task_id']];bank=from_record(rec,'QQQ' if c['mode']=='qqq_full_select' else 'QLM')
        relational.append({**c,'source_receipt_hash':digest(receipt),'task_input_hash':digest(rec['task']),
            'candidate_bank_hash':digest(bank),'candidates':asdict(bank)['candidates'],
            'judge_identity':identities[c['model']],'dispatch':evidence(c['key'])})
    opp=[];matrix=defaultdict(list)
    for c in clean:
        # Primary O is always original QLM coverage. QQQ is compared separately below.
        if c['mode'] in ('task_only_free','qqq_full_select'):continue
        rec=records[c['task_id']]
        bank=from_record(rec,'QLM');o=any(x.status=='ok' and x.answer==rec['eval']['answer'] for x in bank.candidates)
        v=asdict(Opportunity(c['task_id'],c['group_id'],c['stratum'],c['dataset'],c['model'],c['mode'],lookup[c['task_id'],c['model'],'task_only_free']['correct'],o,c['correct'],selector(c['mode'])))
        v.update(bank_hash=digest(bank),input_hash=digest(rec['task']),clean_request=c['key'],clean_result_hash=digest(c))
        opp.append(v);matrix[c['dataset']+'/'+c['model']+'/'+c['mode']].append(v)
    om={(r['task_id'],r['judge'],r['mode']):r for r in opp}
    rel=[];tables=defaultdict(list)
    for x in attacks:
        base=lookup[x['task_id'],x['model'],x['mode']];v=om[x['task_id'],x['model'],x['mode']]
        bank=from_record(records[x['task_id']]);gold=records[x['task_id']]['eval']['answer']
        correct=sum(c.status=='ok' and c.answer==gold for c in bank.candidates)
        valid=sum(c.status=='ok' for c in bank.candidates)
        team_status=('correct_majority' if correct>valid/2 else 'correct_minority' if correct<valid/2 else 'tie')
        attempt=attempts[x['task_id'],x['style']];target=eligible[x['task_id']]
        original=next(c.justification for c in bank.candidates if c.candidate_id==target['target'])
        y={**x,'T':v['T'],'O':v['O'],'clean_Y':base['correct'],'team_status':team_status,
           'clean_request_key':base['key'],'victim_evidence':evidence(x['request_key']),
           'attempt_key':attempt['key'],'attempt_hash':digest(attempt),'target':target['target'],
           'target_answer':target['target_answer'],'original_text_hash':digest(original),
           'rewritten_text_hash':digest(attempt['justification']),'validation':attempt['validation'],
           'transition':transition(base['correct'],x['attacked'],x['status']),
           'wrong_option_changed':base['correct'] is False and x['attacked'] is False and base['status']=='ok' and x['status']=='ok' and base['answer']!=x['answer'],
           'lost_rescue':not v['T'] and base['correct'] is True and x['attacked'] is False,
           'lost_independent_success':v['T'] is True and base['correct'] is True and x['attacked'] is False}
        rel.append(y);tables['/'.join(x[k] for k in ('dataset','model','mode','style'))].append(y)
    def summarize(rs):
        return {'intended':len(rs),'transitions':dict(Counter(x['transition'] for x in rs)),
                'wrong_option_changed':sum(x['wrong_option_changed'] for x in rs),
                'target_answer_adopted':sum(x['target_answer_adopted'] for x in rs),
                'target_candidate_selected':sum(x['target_candidate_selected'] for x in rs),
                'lost_rescue':sum(x['lost_rescue'] for x in rs),'lost_independent_success':sum(x['lost_independent_success'] for x in rs),
                'TOY_partitions':dict(Counter(f"{x['T']}/{x['O']}/{x['clean_Y']}/{x['transition']}" for x in rs))}
    # Exact same-task intersections; never compare all available style denominators.
    neutral={(x['task_id'],x['model'],x['mode']):x for x in rel if x['style']=='ordinary_rephrase'}
    matches=defaultdict(list)
    for x in rel:
        if x['style']=='ordinary_rephrase':continue
        n=neutral[x['task_id'],x['model'],x['mode']]
        matches['/'.join(x[k] for k in ('dataset','model','mode','style'))].append({**x,'clean':n['attacked'],'attacked':x['attacked']})
    samejudge={}
    for key,rs in matrix.items():
        if not key.endswith('qlm_full_select'):continue
        ds,j,_=key.split('/')
        for other in ('qlm_answers_select','qlm_evidence_select','qqq_full_select'):
            samejudge[ds+'/'+j+'/qlm_full_select->'+other]=paired([{**r,'clean':r['Y'],'attacked':lookup[r['task_id'],j,other]['correct']} for r in rs])
    paired_judges={};byvariant=defaultdict(list)
    for x in rel:byvariant[x['dataset'],x['mode'],x['style'],x['task_id']].append(x)
    groups=defaultdict(list)
    for (ds,m,sty,tid),xs in byvariant.items():
        if len(xs)==2 and all(x['clean'] is True for x in xs):
            xs=sorted(xs,key=lambda x:x['model']);groups[ds+'/'+m+'/'+sty].append({**xs[0],'clean':xs[0]['attacked'],'attacked':xs[1]['attacked']})
    paired_judges={k:paired(v) for k,v in groups.items()}
    # Preserve all source views, no reinterpretation or response salvage.
    save_lines(root/'decision_census.private.jsonl',relational)
    save_lines(root/'opportunity_tasks.private.jsonl',opp)
    save_lines(root/'transitions.private.jsonl',rel)
    save_lines(root/'rewrite_attempts.private.jsonl',read_json(p/'pool.json')['attempts'])
    metrics={k:opportunity_metrics(v) for k,v in matrix.items()}
    for name,value in [('judge_opportunity_matrix',metrics),('rescue_regression',metrics),
                       ('transition_tables',{k:summarize(v) for k,v in tables.items()}),
                       ('matched_control_comparisons',{k:paired(v) for k,v in matches.items()}),
                       ('matched_clean_comparisons',samejudge),('both_clean_correct_judge_comparisons',paired_judges),
                       ('minority_majority_comparisons',{k+'/'+team:summarize([x for x in rs if x['team_status']==team])
                         for k,rs in tables.items() for team in sorted({x['team_status'] for x in rs})})]:
        immutable(root/(name+'.json'),value)
    immutable(root/'census_receipt.json',{'schema_version':1,'parent_receipt_hash':digest(receipt),
        'analysis_source':code_identity(Path(__file__).resolve().parents[3]),'counts':receipt['counts'],'new_calls':0})
    return metrics


def export(root, public_names, kind):
    from ..training.colab import review_bundle
    root=Path(root);receipt=read_json(root/'parent_import_receipt.json')
    if not receipt['fixture']:outside_git(root);outside_git(root.parent/'bundles')
    stamp=time.time_ns();out={}
    # All private formats use the bounded checksummed format, including escaped HTML.
    from .semantic_review import package
    out['private']=package(root,root.parent/'bundles'/f'{kind}-PRIVATE-{stamp}.zip',kind+'_private')
    with tempfile.TemporaryDirectory(dir=root.parent) as d:
        pub=Path(d)
        for n in public_names:
            if (root/n).exists():shutil.copyfile(root/n,pub/n)
        out['sanitized']=package(pub,root.parent/'bundles'/f'{kind}-SANITIZED-{stamp}.zip',kind+'_sanitized')
    return out


def import_bundle(root,bundle,sha,mock=False):
    from ..training.feasibility import read_review
    if root.exists():raise ValueError('Import destination must be absent')
    content=read_review(bundle,sha,max_members=60000,max_bytes=512*1024**2,allow_text=True,
                        selected_names={'HANDOFF.json','parent_import_receipt.json'})
    if content['HANDOFF.json']['kind']!=STUDY+'_private' or content['parent_import_receipt.json']['fixture']!=mock:
        raise ValueError('Matching private forensics bundle required')
    private_root(root,mock)
    with zipfile.ZipFile(bundle) as z:
        for n in z.namelist():
            if n in ('HANDOFF.json','review_checksums.json'):continue
            p=root/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(z.read(n))
    return check(root)


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('stage',choices=['import-parent','import-bundle','census','opportunities','sample-review','export-review','import-annotations','adjudicate','agreement','report','export','import-external'])
    parser.add_argument('--run-dir',required=True,type=Path);parser.add_argument('--bundle',type=Path);parser.add_argument('--sha256')
    parser.add_argument('--mock',action='store_true');parser.add_argument('--reviewer');parser.add_argument('--pass',dest='pass_number',type=int,choices=[1,2],default=1)
    parser.add_argument('--file',type=Path);parser.add_argument('--origin',choices=['human','llm_assisted','fixture'],default='human')
    a=parser.parse_args(argv)
    if a.stage=='import-bundle':
        import_bundle(a.run_dir,a.bundle,a.sha256,a.mock)
        print(canonical({'stage':a.stage,'status':'complete','new_model_calls':0}));return 0
    root=private_root(a.run_dir,a.mock)
    from . import semantic_review as review
    with run_lock(root):
        if a.stage=='import-parent':out=import_parent(root,a.bundle,a.sha256,a.mock)
        elif a.stage in ('census','opportunities'):out=census(root)
        else:
            receipt=check(root)
            if receipt['fixture']!=a.mock:raise ValueError('Fixture/real mismatch')
            if a.stage=='sample-review':out=review.sample(root)
            elif a.stage=='export-review':out=review.export_review(root,a.reviewer,a.origin,a.pass_number)
            elif a.stage=='import-annotations':out=review.import_annotations(root,a.file,a.reviewer,a.pass_number)
            elif a.stage=='agreement':out=review.agreement(root)
            elif a.stage=='adjudicate':out=review.adjudicate(root,a.file,a.reviewer)
            elif a.stage=='import-external':out=review.external_import(root,a.file)
            elif a.stage=='report':out=review.report(root)
            else:
                review.report(root);out=export(root,review.PUBLIC,STUDY)
    # Avoid exposing raw private paths/task IDs/reviewers in routine console summaries.
    print(canonical(out if a.stage=='export' else {'stage':a.stage,'status':'complete','new_model_calls':0}))
    return 0
