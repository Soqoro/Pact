"""Offline frozen-bank responsibility contrasts; never fills absent neural scores."""
import math
from collections import Counter
from pathlib import Path

from ..util import canonical, digest, write_json, node_seed
from ..parsing import parse_answer
from ..replay import choose_pair
from .assignment import solve_assignment, loss_coefficients, standardize_answer_nll
from .feasibility import read_review
from .receiver_supervision import packet_from_dict

ARMS=('uniform_supported_sft','local_specialization','continuation_specialization')
TOL=1e-6


def contrast(rows, *, scope='eligible_cells', mode='standardized'):
    if not rows:raise ValueError('Empty assignment bank')
    identities={canonical(r['identity']) for r in rows}
    if len(identities)!=1 or any(r['split']!='train' or r['task_id'].startswith('gpqa') for r in rows):
        raise ValueError('Cross-snapshot/split/precision mixing or forbidden fitting data')
    if len({r['row_id'] for r in rows})!=len(rows):raise ValueError('Duplicate bank rows')
    mask=[[bool(c['eligible']) for c in r['cells']] for r in rows]
    if any(len(r)!=3 for r in mask):raise ValueError('Three cells per row required')
    active=[b for b,m in enumerate(mask) if any(m)]
    multi=[b for b,m in enumerate(mask) if sum(m)>1]
    values=[c['answer_nll'] for b,r in enumerate(rows) for i,c in enumerate(r['cells'])
            if scope=='all_cells' or mask[b][i]]
    missing_scores=sum(x is None for x in values)
    weights={ARMS[0]:[[float(v)/sum(m) if sum(m) else 0. for v in m] for m in mask]}
    stats={'scope':scope,'mode':mode,'missing_scores':missing_scores,'count':len(values)}
    solvers={}
    if values and not missing_scores:
        if any(not math.isfinite(x) or x<0 for x in values):raise ValueError('Invalid stored NLL')
        _,base=standardize_answer_nll([values],split='train',snapshot=rows[0]['identity']['snapshot'],bank_hash=digest(rows),mode=mode)
        stats.update(base);stats['scope']=scope
        for arm,gamma in zip(ARMS[1:],(0.,1.)):
            costs=[[(c['answer_nll']-stats['mean'])/stats['scale'] if mode=='standardized' else c['answer_nll']
                    for c in r['cells']] if all(c['answer_nll'] is not None for c in r['cells']) else
                   [((c['answer_nll']-stats['mean'])/stats['scale'] if mode=='standardized' else c['answer_nll'])
                    if c['answer_nll'] is not None else None for c in r['cells']] for r in rows]
            costs=[[costs[b][i]-gamma*c['delta'] if mask[b][i] else None for i,c in enumerate(r['cells'])] for b,r in enumerate(rows)]
            solvers[arm]=solve_assignment(costs,tau=.2,balance=.1)
            if solvers[arm]['status'] not in ('converged','no_eligible_rows'):raise ValueError('Assignment solver did not converge')
            weights[arm]=solvers[arm]['weights']
    elif not active:
        weights.update({a:[[0.]*3 for _ in rows] for a in ARMS[1:]})
    coeff={a:loss_coefficients(w,[r['initial_correct'] for r in rows]) for a,w in weights.items()}
    def distance(a,b,indices):
        return sum(sum(abs(x-y) for x,y in zip(weights[a][j],weights[b][j])) for j in indices)/len(indices) if indices and a in weights and b in weights else None
    def describe(a):
        w=weights[a];c=coeff[a]
        return {'column_sums':[sum(r[i] for r in w) for i in range(3)],
            'fragile_weighted_column_sums':[sum(c['omega'][b]*w[b][i] for b in active) for i in range(3)],
            'specialization_coefficient_sums':[sum(r[i] for r in c['specialization']) for i in range(3)],
            'weighted_target_token_exposure':[sum(c['specialization'][b][i]*(rows[b]['cells'][i].get('positive_tokens') or 0) for b in active) for i in range(3)],
            'unique_task_support':[len({rows[b]['task_id'] for b in active if mask[b][i]}) for i in range(3)],
            'row_entropies':[-sum(x*math.log(x) for x in row if x) for row in w],
            'allocation_distinct_rows':len({canonical(w[b]) for b in active})}
    deltas=[max(rows[b]['cells'][i]['delta'] for i in range(3) if mask[b][i])-min(rows[b]['cells'][i]['delta'] for i in range(3) if mask[b][i]) for b in multi]
    dc=distance(ARMS[2],ARMS[1],multi)
    tasks={rows[b]['task_id'] for b in active};mt={rows[b]['task_id'] for b in multi}
    ready=('missing_answer_scores' if missing_scores else 'insufficient_assignment_support' if len(tasks)<8 or len(mt)<8 else
           'no_assignment_contrast' if dc is None or dc<=TOL else 'ready')
    return {'schema_version':1,'bank_hash':digest(rows),'identity':rows[0]['identity'],
        'distinct_tasks':len({r['task_id'] for r in rows}),'rows':len(rows),'cells':len(rows)*3,
        'eligible_count_histogram':{str(i):sum(sum(m)==i for m in mask) for i in range(4)},
        'supported_tasks':len(tasks),'multi_eligible_tasks':len(mt),'mask':mask,
        'within_row_delta_ranges':deltas,'varying_credit_rows':sum(d>TOL for d in deltas),
        'D_credit_local':{'all':distance(ARMS[2],ARMS[1],active),'multi':dc},
        'D_local_uniform':{'all':distance(ARMS[1],ARMS[0],active),'multi':distance(ARMS[1],ARMS[0],multi)},
        'task_grouped':{t:{'D_credit_local':distance(ARMS[2],ARMS[1],[b for b in active if rows[b]['task_id']==t])} for t in sorted(tasks)},
        'transform':stats,'weights':weights,'coefficients':coeff,'solvers':solvers,
        'exposure':{a:describe(a) for a in weights},'status':ready,'numerical_tolerance':TOL,
        'readiness':{'artifact_integrity':True,'split_and_snapshot_compatibility':True,'pair_support':len(tasks)>=8 and len(mt)>=8,
                     'assignment_contrast':dc is not None and dc>TOL,'training_executed':False,'evaluation_executed':False,'scientific_efficacy':False},
        'interpretation':'Equal per-row credits and singleton rows cannot provide a credit-driven choice; tiny mass changes are not efficacy.'}


def reconstruct_record(record, identity):
    """Natural raw collection only; verify selected packets, K=2 credits and scores."""
    if record.get('source_variant', 'natural') != 'natural' or 'estimator' in record:
        raise ValueError('Legacy natural loader rejects controlled provenance')
    row=record['row'];tr=record['trajectory'];task=tr['task'];gold=row['gold']
    if task['split']!='train' or row['split']!='train' or task['family'] not in ('arc_challenge','logiqa'):
        raise ValueError('Only original ARC/LogiQA training records are fitting banks')
    if task['task_id']!=row['task_id'] or tr['snapshot']!=identity['snapshot'] or len(record['replays'])!=3:
        raise ValueError('Bank provenance mismatch')
    cells=[]
    for i,pair in enumerate(record['replays']):
        if (pair['agent']!=i or pair['snapshot']!=identity['snapshot'] or pair['split']!='train'
            or pair['task_id']!=task['task_id'] or pair['attack_id']!=tr['attack']['attack_id']):raise ValueError('Pair identity mismatch')
        original=tr['private'][i];scores=record.get('answer_scores',[])
        score=next((s for s in scores if s['adapter']==f'agent{i}'),None)
        nll=None
        if score:
            from .losses import answer_target
            if (score['prompt_hash']!=original['call']['context_hash'] or score['completion']!=answer_target(gold)
                or score['token_count']!=len(score['completion_ids']) or not math.isclose(score['mean_nll'],-score['sum_logp']/score['token_count'])):
                raise ValueError('Answer score prompt/target/reduction mismatch')
            nll=score['mean_nll']
            if row['answer_nll'][i] is not None and not math.isclose(nll,row['answer_nll'][i]):raise ValueError('Stored answer NLL mismatch')
        candidates=[packet_from_dict(p) for p in pair['candidates']]
        for packet in candidates:
            parsed=parse_answer(packet.raw,tuple(row['allowed_answers']),stop_reason=packet.call.stop_reason)
            if (parsed[0]!=packet.answer_id or parsed[2]!=packet.parser_status or packet.call.snapshot!=identity['snapshot']
                or canonical(packet.call.messages)!=canonical(original['call']['messages']) or packet.call.context_hash!=original['call']['context_hash']):
                raise ValueError('Private candidate differs from original actor context')
        if len(candidates)!=4:raise ValueError('Four additional natural candidates required')
        plus,minus,matched,reason=choose_pair(candidates,gold,32)
        if pair['positive_index']!=plus or pair['negative_index']!=minus:raise ValueError('Natural pair selection mismatch')
        eligible=reason is None;delta=None;diff=[];target=None;missing=reason
        if eligible:
            if len(pair['suffix_seeds'])!=2 or len(pair['positive_suffixes'])!=2 or len(pair['negative_suffixes'])!=2:
                eligible=False;missing='missing_replay_evidence'
            else:
                outcomes=[[],[]]
                for k,seed in enumerate(pair['suffix_seeds']):
                    branches=(pair['positive_suffixes'][k],pair['negative_suffixes'][k])
                    expected_seeds=[node_seed(seed,'revision',j) for j in range(3)]+[node_seed(seed,'final')]
                    if any([c['seed'] for c in branch['calls']]!=expected_seeds for branch in branches):raise ValueError('Unpaired suffix node seeds')
                    for side,branch in enumerate(branches):
                        if branch['snapshot']!=identity['snapshot'] or canonical(branch['attack'])!=canonical(tr['attack']):raise ValueError('Replay attack/snapshot changed')
                        expected=[pair['candidates'][plus if side==0 else minus] if j==i else p for j,p in enumerate(tr['private'])]
                        if canonical(branch['private'])!=canonical(expected):raise ValueError('Replay private state changed')
                        outcomes[side].append(int(branch['final']['answer_id']==gold))
                    diff.append(outcomes[0][-1]-outcomes[1][-1])
                delta=sum(diff)/2
                if delta!=pair['delta'] or diff!=list(pair['paired_differences']) or pair['q_plus']!=sum(outcomes[0])/2 or pair['q_minus']!=sum(outcomes[1])/2:
                    raise ValueError('Replay credit mismatch')
                target=pair['candidates'][plus]
                tokens=record.get('generation_tokens',{}).get(digest(target['call']))
                ps=next((s for s in record.get('packet_scores',[]) if s['agent']==i),None)
                if tokens is None or ps is None:
                    eligible=False;missing='missing_positive_target_tokens_or_score'
                elif (tokens['raw']!=target['raw'] or ps['completion']!=target['raw']
                    or ps['completion_ids']!=tokens['completion_ids'] or ps['prompt_ids']!=tokens['prompt_ids']
                    or ps['prompt_hash']!=target['call']['context_hash'] or ps['pair_id']!=pair['pair_id']
                    or ps['token_count']!=len(tokens['completion_ids'])
                    or not math.isclose(ps['mean_nll'],-ps['sum_logp']/ps['token_count'])):
                    raise ValueError('Selected positive token/score provenance mismatch')
                if row['delta'][i]!=delta or row['private_pair_ids'][i]!=pair['pair_id']:raise ValueError('Scored bank pair mismatch')
        cells.append({'agent':i,'eligible':eligible,'missing_reason':missing,'answer_nll':nll,'delta':delta,
            'pair_id':pair['pair_id'] if eligible else None,'per_seed_differences':diff,
            'q_plus':pair['q_plus'],'q_minus':pair['q_minus'],'positive_tokens':target['call']['output_tokens'] if target else None,
            'positive_packet_hash':digest(target) if target else None,'context_hash':original['call']['context_hash'],
            'rationale_review':'not_reviewed; label-correct is not verified reasoning'})
    return {'row_id':row['row_id'],'task_id':row['task_id'],'condition':tr['condition'],'split':'train',
            'identity':identity,'initial_correct':row['initial_correct'],'cells':cells}


def characterize(bundle,sha,output):
    source=read_review(Path(bundle),sha)
    if source['HANDOFF.json']['kind']!='training_bank_engineering_review':raise ValueError('Not a natural training bank')
    bank=source['bank.json']
    if bank['kind']!='training' or bank['split']!='train':raise ValueError('Not training data')
    identity={k:bank[k] for k in ('base_snapshot','precision','runtime_fingerprint','tokenizer_revision','template_hash','data_manifest_hash')}
    identity['snapshot']=bank['actor_snapshot']
    models=source['model_identity.json']
    if (models['actors']['snapshot']!=bank['actor_snapshot'] or models['base']['snapshot']!=bank['base_snapshot']
        or any(models['base'][k]!=bank[k] for k in ('precision','runtime_fingerprint','tokenizer_revision','template_hash'))):raise ValueError('Bank model provenance mismatch')
    records={r['work_id']:r for n,r in source.items() if n.startswith('shards/') and n.endswith('.json')}
    if set(records)!={r['row_id'] for r in bank['rows']}:raise ValueError('Missing original bank records')
    rows=[]
    for r in bank['rows']:
        if canonical(r)!=canonical(records[r['row_id']]['row']):raise ValueError('Bank row mismatch')
        rows.append(reconstruct_record(records[r['row_id']],identity))
    result=contrast(rows,scope='all_cells')
    result['source_bundle_sha256']=sha
    result['raw_nll_sensitivity']=contrast(rows,scope='all_cells',mode='raw')['D_credit_local']
    export_contrast(rows,result,output)
    return result


def export_contrast(rows,result,output):
    output=Path(output);output.mkdir(parents=True,exist_ok=True)
    for name,value in [('bank_characterization.json',{k:result[k] for k in ('distinct_tasks','rows','cells','eligible_count_histogram','supported_tasks','multi_eligible_tasks')}),
        ('assignment_contrast.json',result),('assignment_transform.json',result['transform']),
        ('provenance_and_missingness.json',{'identity':result['identity'],'source_bundle_sha256':result.get('source_bundle_sha256'),
         'missing':[{'row_id':r['row_id'],'cells':r['cells']} for r in rows]})]:write_json(output/name,value)
    (output/'assignment_rows.jsonl').write_text(''.join(canonical(r)+'\n' for r in rows))
    for arm,short in zip(ARMS,('uniform','local','credit')):
        if arm in result['weights']:write_json(output/f'assignment_{short}.json',{'weights':result['weights'][arm],'coefficients':result['coefficients'][arm]})
    (output/'assignment_contrast.md').write_text(f"# Assignment contrast\n\nDistinct tasks: {result['distinct_tasks']}; rows: {result['rows']}.\n\nEligible histogram: {result['eligible_count_histogram']}.\n\nCredit/local L1: {result['D_credit_local']}.\n\nLocal/uniform L1: {result['D_local_uniform']}.\n\nStatus: {result['status']}. No training or efficacy demonstrated.\n")
