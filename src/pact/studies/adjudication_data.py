"""Pinned private parent import and offline, non-generative reconstruction."""
from collections import Counter
from dataclasses import asdict
from pathlib import Path
import tempfile
from ..parsing import parse_answer
from ..benchmarks.contracts import BenchmarkInput
from ..util import digest, read_json, write_json, canonical
from . import breadth
from .adjudication_contracts import Candidate, STYLES, SEED, EvalSpec, from_record

PARENTS = {
 'mmlu-pro':{'n':140,'e':42,'plan':'516dcaba5ba4200e2e194c55b7470a774c116c733b06a912fb514937b0b088a9','sha256':'7e15746dbc7832dda3c5698e86737af66d806f25954ce1fc5910844e5b521bad','file':'pact-breadth-mmlu-pro-001-PRIVATE-1791270113690429538.zip'},
 'musr':{'n':90,'e':38,'plan':'a706c424665a7feec213c5864a2bd591c5781c5136bbeba16b365f96e75166ae','sha256':'1eaa5a5a04f4feb2405ae29ff17c90c831886691ea060ee69fe978025f44dd57','file':'pact-breadth-musr-001-PRIVATE-1791278710347362192.zip'},
 'math-500':{'n':100,'plan':'e27e7c6db74ac478ddfb90c6255ac8254be2c1d9da7fcf09070914c563ecc5c6','sha256':'0cb8d640bf6b039df046fafdb7d1785fc0ef23dabedea082cd8d42f15c72f748','file':'pact-breadth-math-500-001-PRIVATE-1791412685067931571.zip'},
}
SOURCE = '7185b0c4bda278edabfbe45865d922844bf206d6'


def write_lines(path, rows):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(''.join(canonical(r)+'\n' for r in rows),encoding='utf-8')


def eligibility(records):
    rows=[]
    for r in records:
        bank=from_record(r);gold=r['eval']['answer']
        correct=[c for c in bank.candidates if c.status=='ok' and c.answer==gold]
        wrong=[c for c in bank.candidates if c.status=='ok' and c.answer!=gold]
        if not correct or not wrong: continue
        target=min(wrong,key=lambda c:digest([SEED,r['task']['task_id'],'wrong-target',c.candidate_id]))
        order=sorted(STYLES[:4],key=lambda s:digest([SEED,r['task']['task_id'],'attack-order',s]))
        rows.append({'task_id':bank.task.task_id,'dataset':r['dataset'],'group_id':r['group_id'],
                     'target':target.candidate_id,'target_answer':target.answer,'attack_order':order})
    return rows


def joint(rows):
    counts=Counter();totals=Counter()
    for r in rows:
        if any(r.get(k) is None for k in ('c0','c1','debate')):raise ValueError('Historical completeness missing')
        o0,o1,y=any(r['c0']),any(r['c1']),r['debate']
        counts[f'{int(o0)}{int(o1)}{int(y)}']+=1
        for k,v in {'initial_coverage':o0,'revised_coverage':o1,'final_correct':y,
          'synthesis':r['synthesis'],'task_only':r['task_only'], 'erasure':o0 and not o1,
          'new_availability':not o0 and o1,'initially_covered_terminal_loss':o0 and not y,
          'revised_readout_loss':o1 and not y,'construction_from_initial':not o0 and y,
          'construction_from_revised':not o1 and y}.items():totals[k]+=int(v)
    n=len(rows)
    if n-totals['final_correct'] != n-totals['revised_coverage']+totals['revised_readout_loss']-totals['construction_from_revised']:
        raise ValueError('Joint failure identity mismatch')
    if n-totals['revised_coverage'] != n-totals['initial_coverage']-totals['new_availability']+totals['erasure']:
        raise ValueError('Availability identity mismatch')
    transitions={}
    for a,b in (('synthesis','debate'),('debate','task_only'),('synthesis','task_only')):
        transitions[a+'->'+b]=dict(Counter(f'{int(r[a])}->{int(r[b])}' for r in rows))
    return {'n':n,'joint_O0_O1_Y':{f'{a}{b}{c}':counts[f'{a}{b}{c}'] for a in range(2) for b in range(2) for c in range(2)},
            **totals,'paired_historical_transitions':transitions,'identities_verified':True}


def import_parent(bundle, name, scratch):
    anchor=PARENTS[name]
    with tempfile.TemporaryDirectory(dir=scratch) as temp:
        root=Path(temp)/'parent'
        breadth.unpack(bundle,anchor['sha256'],root)
        p=breadth.load(root)
        if digest(p)!=anchor['plan'] or p['dataset']!=name or p['fixture'] or p['training_allowed'] or p['code']['git_commit']!=SOURCE:
            raise ValueError('Pinned parent provenance mismatch')
        if len(p['data']['selected'])!=anchor['n']:raise ValueError('Parent cohort changed')
        _,results,unknown,schedule=breadth.reconstruct(root,p)
        if unknown or len(results)!=len(schedule):raise ValueError('Parent generation incomplete')
        old=read_json(root/'summary.json');out=breadth.report(root)
        if old!=out or any(x['status']!='complete' for x in out['phases'].values()):raise ValueError('Parent report incomplete or changed')
        tables=read_json(root/'per_task_metrics.json')
        saved_scores={v['request_key']:v['score'] for v in (read_json(p) for p in (root/'scores/shards').glob('*.json'))}
        formats=Counter()
        evidence=[];records=[]
        for item in p['data']['selected']:
            tid=item['task']['task_id'];task=BenchmarkInput.from_dict(item['task'])
            selected=[r for r in schedule if r['task_id']==tid]
            for row in selected:
                result=results[row['key']]
                parsed=breadth.parse(task,result['raw'],final=row['stage'] in ('synthesis','debate','task_only'),stop=result['call']['stop_reason'])
                formats[row['model']+'/'+row['stage']+'/'+parsed['status']]+=1
                if name!='math-500':
                    actual=breadth.score(task,item['eval'],result['raw'],final=row['stage'] in ('synthesis','debate','task_only'),stop=result['call']['stop_reason'])
                    if actual!=saved_scores[row['key']]:raise ValueError('Parent MCQ rescoring mismatch')
            if name=='math-500':continue
            banks={}
            for team in ('QLM','QQQ'):
                candidates=[]
                for b in p['bindings'][tid][team]:
                    row=next(r for r in selected if r['stage']=='private' and r['model']==b['family'] and r['replica']==b['replica'])
                    result=results[row['key']]
                    answer,rationale,status=parse_answer(result['raw'],tuple(o.answer_id for o in task.options),stop_reason=result['call']['stop_reason'])
                    candidates.append(asdict(Candidate('c'+str(b['slot']),answer,rationale,status,row['key'],digest(result),b['family'],result['raw'])))
                banks[team]=candidates
            # Recompute initial masks from parser and official label, not the old report alone.
            hist={team:next(r for r in tables[team] if r['task_id']==tid) for team in tables}
            for team in banks:
                mask=[c['status']=='ok' and c['answer']==item['eval']['answer'] for c in banks[team]]
                if mask!=hist[team]['c0']:raise ValueError('Parent label/slot/scorer mismatch')
            record={'dataset':name,'task':item['task'],'eval':{'answer':item['eval']['answer']},
                    'group_id':item['group_id'],'stratum':item['stratum'],'banks':banks,'bindings':p['bindings'][tid],
                    'historical':hist,'rationale_review_status':'not_reviewed',
                    'training_allowed':False,'untouched_final':False}
            records.append(record)
            evidence.append({'task_id':tid,'rows':selected,'results':{r['key']:results[r['key']] for r in selected}})
        offline={'teams':{team:joint(rows) for team,rows in tables.items()},'format_counts_by_family_stage':dict(formats),
                 'math_format_limited':name=='math-500','rationale_truth':'not_reviewed',
                 'scoring_validation':'stored pinned Math-Verify scores; no new symbolic rescoring' if name=='math-500' else 'all MCQ calls independently rescored'}
        review=[]
        if name!='math-500':
            byid={r['task']['task_id']:r for r in records};ev={r['task_id']:r for r in evidence}
            for stratum, pred in [('revised_readout_loss',lambda r:any(r['c1']) and not r['debate']),('covered_success',lambda r:any(r['c1']) and r['debate'])]:
                selected=sorted((r for r in tables['QLM'] if pred(r)),key=lambda r:digest([SEED,'human-review',name,stratum,r['task_id']]))[:8]
                for r in selected:
                    review.append({'dataset':name,'review_stratum':stratum,'record':byid[r['task_id']],
                                   'historical_outputs':ev[r['task_id']], 'identities':{k:read_json(root/'identities'/f'{k}.json') for k in 'QLMR'},
                                   'annotation':{k:'not_reviewed' for k in ('argument_supports_answer','decisive_contradiction','insufficient_rationale','copied_majority_cues','invalid_formatting','unknown')}})
        receipt={'dataset':name,'bundle_sha256':anchor['sha256'],'plan_hash':digest(p),'source':p['code'],
                 'models':p['models'],'selected_count':anchor['n'],'exposure_manifest_hash':digest(p['data']['manifest']),
                 'bindings_hash':digest(p['bindings']),'complete_verified':True}
        if name!='math-500':
            write_json(scratch/'parent_evidence'/f'{name}.json',{'receipt':receipt,'selected_outputs':evidence,
                       'identities':{k:read_json(root/'identities'/f'{k}.json') for k in 'QLMR'}})
        return records,offline,review,receipt


def import_all(root, paths, fixture=False):
    if not fixture:
        from .gpqa_data import outside_git
        outside_git(root)
    if (root/'bank.json').exists():raise ValueError('Import is immutable; choose the existing plan to resume')
    root.mkdir(parents=True,exist_ok=True)
    records=[];offline={};review=[];receipts=[]
    if fixture:
        records=fixture_records()
        offline={n:{'teams':{'QLM':joint([r['historical']['QLM'] for r in records if r['dataset']==n])},'fixture':True} for n in ('mmlu-pro','musr')}
        receipts=[{'fixture':True}]
    else:
        for name in PARENTS:
            if name not in paths:raise ValueError('All three pinned parent PRIVATE bundles required')
            bank,analysis,pack,receipt=import_parent(paths[name],name,root)
            records.extend(bank);offline[name]=analysis;review.extend(pack);receipts.append(receipt)
    eligible=eligibility(records)
    if not fixture and Counter(r['dataset'] for r in eligible)!=Counter({'mmlu-pro':42,'musr':38}):
        raise ValueError('Reconstructed mixed-support population differs from prespecified audit; stop before planning')
    data={'fixture':fixture,'records':records,'receipts':receipts,'offline':offline}
    write_json(root/'bank.json',data)
    write_json(root/'parent_import_receipts.json',receipts)
    write_json(root/'joint_failure_map.json',offline)
    write_lines(root/'candidate_bank_manifest.jsonl',records)
    write_lines(root/'rationale_review_sample.private.jsonl',review)
    write_json(root/'attack_eligibility.json',eligible)
    return data


def fixture_records():
    from ..benchmarks.fixtures import dataset
    records=[]
    for name in ('mmlu-pro','musr'):
        for i,r in enumerate(dataset(name)['selected']):
            task=r['task'];gold=r['eval']['answer'];wrong=next(o['answer_id'] for o in task['options'] if o['answer_id']!=gold)
            banks={}
            for team in ('QLM','QQQ'):
                cs=[]
                for j in range(3):
                    a=gold if j==0 else wrong; raw=canonical({'answer':a,'justification':'Fictional argument '+str(j)})
                    cs.append(asdict(Candidate('c'+str(j),a,'Fictional argument '+str(j),'ok',digest([name,i,team,j]),digest(raw),team[j],raw)))
                banks[team]=cs
            h={'task_id':task['task_id'],'c0':[True,False,False],'c1':[True,False,False],'debate':i==0,'synthesis':True,'task_only':False}
            records.append({'dataset':name,'task':task,'eval':{'answer':gold},'group_id':r['group_id'],'stratum':r['stratum'],
                            'banks':banks,'historical':{'QLM':h,'QQQ':h},'training_allowed':False,'untouched_final':False,'rationale_review_status':'not_reviewed'})
    return records
