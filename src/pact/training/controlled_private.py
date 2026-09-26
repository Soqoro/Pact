"""Controlled shared packets and explicit slot interventions; never natural pairs."""
import contextlib
import copy
import dataclasses as dc
import json
from collections import Counter
from types import SimpleNamespace

from ..artifacts import ShardStore
from ..backends import Request
from ..protocol import Protocol
from ..schemas import PrivatePacket, AttackRecord, task_from_dict
from ..util import canonical, digest, node_seed, read_json, write_json
from .controlled_donors import donor_prompt, validate_donor, donor_isolation, DonorJournal
from .receiver import JournalBackend
from .receiver_supervision import packet_from_dict
from .specialization_collect import StudyJournal, immutable, runtime, score_once
from .specialization_study import offline_backend
from .controlled_private_plan import SOURCE, ESTIMATOR, ARMS, budgets
from .assignment_contrast import contrast, ARMS as NATURAL_ARMS
from .assignment import solve_assignment
from .losses import answer_target
from .specialization_train import sequence


class BaseGenerator:
    """Reuse the restored model, but physically disable all adapters for donors."""
    def __init__(self, backend):
        self.backend = backend
        self.identity = {**backend.base_identity, 'adapters':[], 'adapter_policy':'all_disabled'}
        self.tokenizer = backend.tokenizer
    def generate(self, request):
        if request.actor != 'base' or request.phase != 'controlled_donor': raise ValueError('Not a donor request')
        with donor_isolation(self.backend.model):
            raw,call = self.backend.generate(request)
        self.last_generation = dict(self.backend.last_generation)
        return raw, dc.replace(call, snapshot=self.identity['snapshot'])
    def count_tokens(self, text): return self.backend.count_tokens(text)
    def assert_unchanged(self): self.backend.assert_unchanged()


def check_generator(plan, identity):
    if plan['synthetic_fixture']:
        if identity.get('backend') != 'mock': raise ValueError('Fixture donor requires mock')
        return
    want = plan['frozen_arm']['model']
    if identity.get('adapters') != [] or identity.get('adapter_policy') != 'all_disabled':
        raise ValueError('Generator adapters must be disabled')
    for k in ('snapshot','runtime_fingerprint','revision','tokenizer_revision','template_hash','precision','attention','enable_thinking'):
        if identity.get(k) != want[k]: raise ValueError('Generator base identity changed: '+k)


def acquire(plan, backend, root, *, readonly=False, stop_after=None, before_new=lambda:None, after_task=lambda:None):
    if plan.get('source_variant')!=SOURCE or plan.get('estimator')!=ESTIMATOR:
        raise ValueError('Explicit controlled donor source required')
    check_generator(plan, backend.identity)
    plan_hash = digest(plan)
    journal = DonorJournal(backend, root/'acquire', budgets()['acquire'],
                           stop_after=0 if readonly else stop_after, before_new=before_new)
    attempts = []; pairs = {}
    for spec in plan['donor_schedule']:
        tid = spec['task_id']; task = task_from_dict(plan['tasks'][tid]); accepted = {}
        for kind in ('positive','negative'):
            target = spec['targets'][kind]
            for index,seed in enumerate(target['seeds']):
                request = Request(task, donor_prompt(task,target['option']), 'base','controlled_donor',seed,256,False)
                key = digest([plan_hash, SOURCE, tid, kind, index, request, backend.identity])
                journal.begin_record(key)
                raw,call = journal.generate(request)
                if json.loads(call.parameters_json) != plan['frozen_arm']['parameters']['packet']:
                    raise ValueError('Donor decoding differs from frozen packet decoding')
                row = {'schema_version':1,'work_id':key,'source_variant':SOURCE,'task_id':tid,
                    'kind':kind,'target':target['option'],'attempt':index,'request':dc.asdict(request),
                    'raw':raw,'call':dc.asdict(call),'tokens':journal.last_generation,
                    **validate_donor(raw,task,target['option'],plan['labels'][tid]['answer_id'],call.stop_reason)}
                # Frozen extra metadata disclosure patterns extend the old validator for private targets.
                import re
                if re.search(r'(?i)\b(?:assigned (?:option|answer|target)|(?:correct|wrong|positive|negative)[- ]target|synthetic (?:packet|training)|construction instructions)\b', raw):
                    row['rejection_reasons'] = [*row['rejection_reasons'],'private_construction_metadata_disclosure']
                    row['accepted'] = False
                row['validator'] = 'controlled_private_validator_v1'
                if readonly:
                    if canonical(ShardStore(root/'donor_attempts').read(key)) != canonical(row): raise ValueError('Donor attempt changed')
                else: ShardStore(root/'donor_attempts').put(key,row)
                attempts.append(row)
                if row['accepted']:
                    accepted[kind] = row
                    break
        pair = {'task_id':tid,'source_variant':SOURCE,'estimator':ESTIMATOR,'accepted':accepted,
                'complete':set(accepted)=={'positive','negative'},'rationale_review_status':'not_reviewed'}
        pair['pair_id'] = digest(pair)
        if pair['complete']:
            a,b = (accepted[k]['call']['output_tokens'] for k in ('positive','negative'))
            pair.update(token_length_difference=a-b, length_bin_matched=a//32==b//32)
        pairs[tid] = pair
        if not readonly:
            print(f'Controlled pairs {len(pairs)}/32; accepted targets {len(accepted)}/2',flush=True)
            after_task()
    if journal.seen != journal.results.keys(): raise ValueError('Unplanned donor calls')
    manifest = {'source_variant':SOURCE,'estimator':ESTIMATOR,'plan_hash':digest(plan),
                'generator':backend.identity,'pairs':pairs,'attempted_calls':len(attempts)}
    if readonly:
        if canonical(read_json(root/'controlled_pair_manifest.json')) != canonical(manifest): raise ValueError('Pair manifest changed')
    else:
        backend.assert_unchanged()
        immutable(root/'controlled_pair_manifest.json',manifest)
        (root/'controlled_pair_attempts.jsonl').write_text(''.join(canonical(r)+'\n' for r in attempts))
        immutable(root/'pair_quality_and_review.json',{'rationale_review_status':'not_reviewed',
            'review_task_ids':plan['review_task_ids'], 'sample':[pairs[t] for t in plan['review_task_ids']],
            'rejection_reasons':dict(Counter(reason for a in attempts for reason in a['rejection_reasons'])),
            'structural_acceptance_is_not_reasoning_verification':True})
        after_task()
    return manifest


def verified_pairs(plan, root):
    manifest = read_json(root/'controlled_pair_manifest.json')
    fake = SimpleNamespace(identity=manifest['generator'],
        tokenizer=SimpleNamespace(eos_token_id=plan['frozen_arm']['parameters']['packet']['eos_token_id']))
    return acquire(plan,fake,root,readonly=True)


def build_bank(plan, root):
    pairs = verified_pairs(plan,root)['pairs']; rows = []
    for anchor in plan['anchors']:
        tr = anchor['trajectory']; pair = pairs[tr['task']['task_id']]
        reasons = []
        if not pair['complete']: reasons.append('missing_controlled_pair')
        if any(p['parser_status']=='context_overflow' for p in tr['private']): reasons.append('original_context_overflow')
        if tr['condition'] not in ('clean','early') or len(tr['private']) != 3: reasons.append('incompatible_original_snapshot')
        rows.append({'row_id':anchor['work_id'],'task_id':pair['task_id'],'condition':tr['condition'],
                     'mask':[not reasons]*3,'missing_reasons':reasons,'pair_id':pair['pair_id']})
    tasks = {r['task_id'] for r in rows if any(r['mask'])}
    multi = {r['task_id'] for r in rows if sum(r['mask'])>1}
    result = {'source_variant':SOURCE,'estimator':ESTIMATOR,'plan_hash':digest(plan),
        'rows':rows,'supported_tasks':len(tasks),'multi_tasks':len(multi),
        'eligible_cells':sum(sum(r['mask']) for r in rows),
        'status':'ready_for_replay' if len(tasks)>=8 and len(multi)>=8 else 'insufficient_controlled_support'}
    immutable(root/'controlled_support.json',result)
    return result


class BranchJournal(StudyJournal):
    """Branch identity is separate from common physical-node seeds."""
    def generate(self, request):
        if request.phase not in ('revision','final'): raise ValueError('No anchor/candidate acquisition in controlled replay')
        self.begin_record(digest([SOURCE,ESTIMATOR,self.branch,request,self.identity]))
        if self.readonly and digest([self.record_key,0]) not in self.results: raise ValueError('Missing controlled replay call')
        # JournalBackend validates actual prompt+reservation even on committed reuse.
        return JournalBackend.generate(self,request)


def inserted_packet(row, agent):
    """Generator call stays source metadata; only raw packet enters defender views."""
    from .receiver import call_from_dict
    if row.get('source_variant') != SOURCE or not row['accepted']: raise ValueError('Explicit accepted controlled source required')
    return PrivatePacket(row['task_id'],agent,row['raw'],row['answer_id'],row['explanation'],row['parser_status'],call_from_dict(row['call']))


def replay(plan, backend, root, *, readonly=False, stop_after=None, before_new=lambda:None, after_cell=lambda:None):
    if backend.identity['snapshot']!=plan['frozen_arm']['checkpoint']['snapshot']:
        raise ValueError('Controlled replay requires the frozen parent actors')
    support = build_bank(plan,root)
    if support['status'] != 'ready_for_replay': raise ValueError('insufficient_controlled_support')
    plan_hash = digest(plan)
    pairs = verified_pairs(plan,root)['pairs']; anchors = {a['work_id']:a for a in plan['anchors']}
    eligible = {r['row_id'] for r in support['rows'] if any(r['mask'])}
    rows = []; used = 0
    for stage,order in (('primary','original'),('order','reversed'),('calibration','original')):
        journal = BranchJournal(backend,root/stage,budgets()[stage],plan,'fit',readonly=readonly,
            stop_after=None if stop_after is None else max(0,stop_after-used),before_new=before_new)
        protocol = Protocol(runtime(plan),journal); store = ShardStore(root/(stage+'-cells'))
        specs = ([(a['work_id'],i) for a in plan['anchors'] for i in range(3)
                  if a['work_id'] in eligible and (stage!='order' or a['trajectory']['task']['task_id'] in plan['order_task_ids'])]
                 if stage!='calibration' else [(s['row_id'],s['agent']) for s in plan['natural_calibration']])
        for rid,i in specs:
            anchor = anchors[rid]; tr = anchor['trajectory']; tid = tr['task']['task_id']; pair = pairs[tid]
            task = task_from_dict(tr['task']); attack = AttackRecord(**{k:v for k,v in tr['attack'].items() if k!='schema_version'})
            original = tuple(packet_from_dict(p) for p in tr['private'])
            if stage=='calibration':
                natural = next(s for s in plan['natural_calibration'] if s['row_id']==rid and s['agent']==i)
                replacements = {sign:packet_from_dict(natural[sign]) for sign in ('positive','negative')}
                source_id = digest(natural)
            else:
                replacements = {sign:inserted_packet(pair['accepted'][sign],i) for sign in ('positive','negative')}
                source_id = pair['pair_id']
            key = digest([plan_hash,stage,rid,i,source_id])
            saved = store.read(key); branches = {sign:[] for sign in replacements}
            seeds = [node_seed(plan['seed'],ESTIMATOR,tid,tr['condition'],'suffix',k) for k in range(2)]
            for sign,replacement in replacements.items():
                private = tuple(replacement if j==i else p for j,p in enumerate(original))
                for k,seed in enumerate(seeds):
                    journal.branch = {'row':digest(anchor),'pair':source_id,'agent':i,'sign':sign,'display':order,
                                      'source_variant':SOURCE if stage!='calibration' else 'retained_natural_private_v1'}
                    branch = dc.asdict(protocol.suffix(task,'debate',attack,private,seed,digest([key,sign,k]),display_order=order))
                    if readonly and saved: branch['readout_low_trust_tokens'] = saved['branches'][sign][k]['readout_low_trust_tokens']
                    branches[sign].append(branch)
            success = {s:[int(b['final']['parser_status']=='ok' and b['final']['answer_id']==plan['labels'][tid]['answer_id']) for b in v] for s,v in branches.items()}
            differences = [p-n for p,n in zip(success['positive'],success['negative'])]
            cell = {'schema_version':1,'work_id':key,'source_variant':SOURCE if stage!='calibration' else 'retained_natural_private_v1',
                'estimator':ESTIMATOR,'stage':stage,'row_id':rid,'task_id':tid,'condition':tr['condition'],'agent':i,
                'pair_id':source_id,'seeds':seeds,'branches':branches,'per_seed_success':success,
                'per_seed_differences':differences,'q_plus':sum(success['positive'])/2,
                'q_minus':sum(success['negative'])/2,'delta':sum(differences)/2}
            if readonly:
                if canonical(saved)!=canonical(cell): raise ValueError('Controlled replay reconstruction mismatch')
            else:
                store.put(key,cell);after_cell()
                print(f'{stage}: {rid[:8]} actor{i} delta={cell["delta"]}',flush=True)
            rows.append(cell)
        if journal.results.keys()!=journal.seen: raise ValueError('Unplanned replay calls')
        used += journal.new_calls
    if not readonly:
        immutable(root/'replay_complete.json',{'plan_hash':digest(plan),'cells_hash':digest(rows),'cells':len(rows)})
        (root/'controlled_replay_cells.jsonl').write_text(''.join(canonical(r)+'\n' for r in rows))
    return rows


def score_bank(plan, backend, root, replay_cells, *, readonly=False, before_new=lambda:None, after_row=lambda:None):
    if plan.get('source_variant')!=SOURCE or plan.get('estimator')!=ESTIMATOR:
        raise ValueError('Explicit controlled scoring source required')
    if backend.identity['snapshot']!=plan['frozen_arm']['checkpoint']['snapshot']:
        raise ValueError('Frozen parent scoring actors required')
    if any(c['source_variant']!=SOURCE for c in replay_cells if c['stage']=='primary'):
        raise ValueError('Not a controlled primary replay')
    pairs = verified_pairs(plan,root)['pairs']; lookup = {(c['row_id'],c['agent']):c for c in replay_cells if c['stage']=='primary'}
    rows=[]; records=[]
    for anchor in plan['anchors']:
        tr=anchor['trajectory']; rid=anchor['work_id']; tid=tr['task']['task_id']; gold=plan['labels'][tid]['answer_id']
        answer=[]; packets=[]; cells=[]
        for i,private in enumerate(tr['private']):
            prompt=private['call']['rendered_prompt']
            request=[SOURCE,ESTIMATOR,backend.identity,rid,i,prompt,answer_target(gold)]
            if not readonly: before_new()
            a=score_once(root,digest([rid,'answer',i]),'answer',request,
                lambda i=i,prompt=prompt:backend.scorer.answer_score(i,prompt,answer_target(gold)),192,readonly=readonly)
            answer.append(a)
            evidence=lookup.get((rid,i)); target=pairs[tid]['accepted'].get('positive'); packet_score=None
            if evidence:
                target_ids=target['tokens']['completion_ids']
                req=[SOURCE,ESTIMATOR,backend.identity,rid,i,prompt,target['raw'],target_ids,pairs[tid]['pair_id']]
                packet_score=score_once(root,digest([rid,'packet',i]),'packet',req,
                    lambda i=i,prompt=prompt,target=target:backend.scorer.token_score(f'agent{i}',prompt,
                        backend.tokenizer.encode(prompt,add_special_tokens=False),target['raw'],target['tokens']['completion_ids']),192,readonly=readonly)
            for s,completion in ((a,answer_target(gold)),(packet_score,target['raw'] if target else None)):
                if s is not None:
                    import math
                    if (s['adapter']!=f'agent{i}' or s['prompt_hash']!=private['call']['context_hash'] or s['completion']!=completion
                        or s['token_count']!=len(s['completion_ids']) or not s['token_count']
                        or not math.isfinite(s['mean_nll']) or s['mean_nll']<0
                        or not math.isclose(s['mean_nll'],-s['sum_logp']/s['token_count'])): raise ValueError('Controlled score contract mismatch')
            if packet_score and packet_score['completion_ids']!=target['tokens']['completion_ids']: raise ValueError('Synthetic target tokens changed')
            packets.append(packet_score)
            cells.append({'agent':i,'eligible':evidence is not None,'answer_nll':a['mean_nll'],
                'delta':evidence['delta'] if evidence else None,'per_seed_differences':evidence['per_seed_differences'] if evidence else [],
                'q_plus':evidence['q_plus'] if evidence else None,'q_minus':evidence['q_minus'] if evidence else None,
                'positive_tokens':packet_score['token_count'] if packet_score else None,
                'pair_id':pairs[tid]['pair_id'] if evidence else None,'rationale_review':'not_reviewed'})
        initial=[p['parser_status']=='ok' and p['answer_id']==gold for p in tr['private']]
        row={'row_id':rid,'task_id':tid,'condition':tr['condition'],'split':'train',
             'identity':{'snapshot':backend.identity['snapshot'],'source_variant':SOURCE,'estimator':ESTIMATOR},
             'initial_correct':initial,'cells':cells}
        record={'schema_version':1,'source_variant':SOURCE,'estimator':ESTIMATOR,'work_id':rid,
                'trajectory':tr,'gold':gold,'pair_id':pairs[tid]['pair_id'],
                'answer_scores':answer,'packet_scores':packets,'row':row}
        if readonly:
            if canonical(ShardStore(root/'scored-bank').read(rid))!=canonical(record): raise ValueError('Scored controlled bank changed')
        else: ShardStore(root/'scored-bank').put(rid,record);after_row()
        rows.append(row);records.append(record)
    return rows,records


def assignment(rows, replay_cells):
    if any(r['identity'].get('source_variant')!=SOURCE or r['identity'].get('estimator')!=ESTIMATOR for r in rows):
        raise ValueError('Explicit controlled assignment provenance required')
    if any(c['source_variant']!=SOURCE for c in replay_cells if c['stage']=='primary'):
        raise ValueError('Natural calibration cannot enter controlled assignment')
    raw=contrast(rows)
    result=copy.deepcopy(raw)
    for field in ('weights','coefficients','solvers','exposure'):
        result[field]={ARMS[NATURAL_ARMS.index(k)]:v for k,v in result[field].items()}
    result.update(source_variant=SOURCE,estimator=ESTIMATOR)
    result['row_ids']=[r['row_id'] for r in rows]
    result['task_ids']=[r['task_id'] for r in rows]
    result['row_constant_credit_rows']=sum(d<=1e-6 for d in result['within_row_delta_ranges'])
    result['credit_by_row']=[{'row_id':r['row_id'],'task_id':r['task_id'],'condition':r['condition'],
        'cells':[{k:c.get(k) for k in ('agent','eligible','delta','q_plus','q_minus','per_seed_differences')} for c in r['cells']]} for r in rows]
    active_tasks=sorted({r['task_id'] for j,r in enumerate(rows) if any(result['mask'][j])})
    result['per_task_allocation']={t:{a:[sum(w[j][i] for j,r in enumerate(rows) if r['task_id']==t and any(result['mask'][j]))/
        sum(r['task_id']==t and any(result['mask'][j]) for j,r in enumerate(rows)) for i in range(3)] for a,w in result['weights'].items()} for t in active_tasks}
    tasks={r['task_id'] for j,r in enumerate(rows) if sum(result['mask'][j])>1}
    per_task={t:sum(sum(abs(x-y) for x,y in zip(result['weights'][ARMS[2]][j],result['weights'][ARMS[1]][j]))
        for j,r in enumerate(rows) if r['task_id']==t and sum(result['mask'][j])>1)/sum(r['task_id']==t and sum(result['mask'][j])>1 for j,r in enumerate(rows)) for t in sorted(tasks)}
    mean=sum(per_task.values())/len(per_task) if per_task else None
    result['practical_screen']={'task_mean_l1':mean,'per_task_l1':per_task,
        'tasks_at_least_0_10':sum(v>=.10 for v in per_task.values()),'threshold':.10,'minimum_tasks':8}
    if raw['status']=='insufficient_assignment_support':result['status']='insufficient_controlled_support'
    elif raw['status']=='ready':
        result['status']='ready_for_user_review' if mean>=.10 and sum(v>=.10 for v in per_task.values())>=8 else 'insufficient_practical_contrast'
    result['training_requires_explicit_review']=True
    result['interpretation']='Controlled full-packet insertion effect, not on-policy credit or exact policy gradient; engineering contrast is not reliability.'
    # Fixed full-bank transform and masks for both seed and order sensitivity.
    def solve(changes):
        stats=result['transform'];costs=[]
        for r in rows:
            costs.append([((c['answer_nll']-stats['mean'])/stats['scale']-changes.get((r['row_id'],i),c['delta'])) if c['eligible'] else None for i,c in enumerate(r['cells'])])
        fit=solve_assignment(costs,tau=.2,balance=.1)
        if fit['status']!='converged':raise ValueError('Sensitivity solver failed')
        return fit['weights']
    sensitivities={}
    for k in range(2):
        sensitivities[str(k)]=solve({(r['row_id'],i):c['per_seed_differences'][k] for r in rows for i,c in enumerate(r['cells']) if c['eligible']})
    controls={(c['row_id'],c['agent']):c for c in replay_cells if c['stage']=='order'}
    reversed_weights=solve({key:c['delta'] for key,c in controls.items()})
    primary={(c['row_id'],c['agent']):c for c in replay_cells if c['stage']=='primary'}
    raw_order=[]
    for key,c in controls.items():
        p=primary[key]; rid=key[0]
        original_mean=sum(primary[(rid,i)]['delta'] for i in range(3))/3
        control_mean=sum(controls[(rid,i)]['delta'] for i in range(3))/3
        raw_order.append({'row_id':rid,'agent':key[1],'primary_delta':p['delta'],'reversed_delta':c['delta'],
                          'primary_centered':p['delta']-original_mean,'reversed_centered':c['delta']-control_mean})
    movement=[{'row_id':r['row_id'],'task_id':r['task_id'],'controlled_row':(r['row_id'],0) in controls,
        'l1':sum(abs(a-b) for a,b in zip(reversed_weights[j],result['weights'][ARMS[2]][j]))} for j,r in enumerate(rows)]
    natural=[{'row_id':c['row_id'],'task_id':c['task_id'],'agent':c['agent'],
        'natural':{k:c[k] for k in ('q_plus','q_minus','delta','per_seed_differences')},
        'controlled':{k:primary[(c['row_id'],c['agent'])][k] for k in ('q_plus','q_minus','delta','per_seed_differences')} if (c['row_id'],c['agent']) in primary else None}
        for c in replay_cells if c['stage']=='calibration']
    def winners(w):return [i for i,v in enumerate(w) if abs(v-max(w))<1e-6]
    result['actor_dominance']={'credit_winner_counts':dict(Counter(str(winners(w)) for w in result['weights'][ARMS[2]] if sum(w))),
                             'ties_retained':True,'not_evidence_of_task_specialization':True}
    order={'display':'reverse peers/readout only','primary_unchanged':True,'full_bank_transform':result['transform'],
        'raw_and_centered':raw_order,'weights':reversed_weights,'movement':movement,
        'preference_changed_rows':[r['row_id'] for j,r in enumerate(rows) if (r['row_id'],0) in controls and
            winners([primary[(r['row_id'],i)]['delta'] for i in range(3)])!=winners([controls[(r['row_id'],i)]['delta'] for i in range(3)])],
        'strict_preference_reversals':[{'row_id':rid,'actors':[i,j]} for rid in sorted({key[0] for key in controls}) for i in range(3) for j in range(i+1,3)
            if (primary[(rid,i)]['delta']-primary[(rid,j)]['delta'])*(controls[(rid,i)]['delta']-controls[(rid,j)]['delta'])<0],
        'limitation':'Eight prespecified tasks; order ambiguity is not resolved by selecting a favored order.'}
    seeds={'transform_fixed':True,'masks_fixed':True,'weights':sensitivities,
           'l1_from_primary':{k:[sum(abs(a-b) for a,b in zip(w,result['weights'][ARMS[2]][j])) for j,w in enumerate(v)] for k,v in sensitivities.items()}}
    return result,order,seeds,{'cells':natural,'limitation':'Five selected natural cells on two tasks; not population validation.'}


def write_assignments(root, rows, records, replay_cells):
    result,order,seeds,calibration=assignment(rows,replay_cells)
    for name,value in [('assignment_contrast',result),('assignment_transform',result['transform']),('order_sensitivity',order),
                       ('seed_assignment_sensitivity',seeds),('natural_controlled_calibration',calibration)]:
        immutable(root/(name+'.json'),value)
    for arm,short in zip(ARMS,('uniform','local','credit')):
        immutable(root/f'assignment_{short}.json',{'source_variant':SOURCE,'estimator':ESTIMATOR,
            'weights':result['weights'][arm],'coefficients':result['coefficients'][arm]})
    immutable(root/'bank_manifest.json',{'source_variant':SOURCE,'estimator':ESTIMATOR,'rows_hash':digest(rows),
                                       'records_hash':digest(records),'replay_hash':digest(replay_cells)})
    (root/'pretraining_decision.md').write_text(f"# Pretraining decision\n\nStatus: {result['status']}.\nTask-average contrast: {result['practical_screen']['task_mean_l1']}.\nReview packet quality, seed/order sensitivity and actor dominance. Training requires a separate invocation and a hashed review decision. No automatic follow-up or efficacy claim.\n")
    return result


def examples_for(records, assignments, arm, tokenizer):
    if (arm not in ARMS or assignments['source_variant']!=SOURCE or assignments['estimator']!=ESTIMATOR
        or assignments['status']!='ready_for_user_review'):raise ValueError('Controlled supported practical contrast required')
    if assignments['bank_hash'] != digest([r['row'] for r in records]): raise ValueError('Controlled training bank changed')
    coefficients=assignments['coefficients'][arm];examples=[]
    for b,r in enumerate(records):
        if r.get('source_variant')!=SOURCE or r.get('estimator')!=ESTIMATOR:raise ValueError('Not controlled supervision')
        cells=[]
        for i in range(3):
            prompt=r['trajectory']['private'][i]['call']['rendered_prompt'];a=r['answer_scores'][i];p=r['packet_scores'][i]
            if a['completion']!=answer_target(r['gold']):raise ValueError('Base target changed')
            for s in (a,p):
                if s is not None and (s['adapter']!=f'agent{i}' or s['prompt_hash']!=digest(prompt)
                    or s['prompt_ids']!=list(tokenizer.encode(prompt,add_special_tokens=False))
                    or s['completion_ids'][-1]!=tokenizer.eos_token_id or tokenizer.eos_token_id in s['completion_ids'][:-1]
                    or tokenizer.decode(s['completion_ids'][:-1],skip_special_tokens=True)!=s['completion']):raise ValueError('Original-context synthetic token contract mismatch')
            cells.append({'base':sequence(a),'packet':sequence(p) if p else None,
                'base_coefficient':coefficients['base'][b][i], 'packet_coefficient':coefficients['specialization'][b][i]})
        examples.append({'row_id':r['work_id'],'task_id':r['row']['task_id'],'source_variant':SOURCE,'estimator':ESTIMATOR,'cells':cells})
    return examples
