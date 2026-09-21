"""Frozen answer-only prompt intervention; cached prepared packets are the comparator."""
import dataclasses as dc
from collections import Counter
from pathlib import Path
from types import SimpleNamespace
from ..parsing import parse_answer
from ..schemas import task_from_dict
from ..util import canonical,digest,read_json
from .feasibility import read_review
from .preparation_probe import probe_plan,probe_report
from .warmstart_config import warmstart_prompt
from .curated_repair import curated_requests

CONFIG_HASH='c5d805b46992b1b1720448b45735d27a32e4b6e8246780957021f3612c897935'


def load_prompt_config(path):
    config=read_json(Path(path))
    if digest(config)!=CONFIG_HASH:raise ValueError('Prompt control requires the frozen 72-call design')
    return config


def prompt_plan(config,training_bundle,probe_bundle):
    if digest(config)!=CONFIG_HASH:raise ValueError('Prompt control configuration changed')
    training=read_review(training_bundle,config['training_bundle_sha256'])
    probe=read_review(probe_bundle,config['probe_bundle_sha256'])
    design=training['preparation_plan.json'];refs=training['references/references.json']
    if (training['status.json']['status']!='warmstart_updates_complete' or refs['final_step']!=90
            or digest(refs)!=config['reference_manifest_hash']):
        raise ValueError('Require completed pinned preparation')
    parent=SimpleNamespace(base_snapshot=refs['identity']['model_snapshot'],
        reference_hashes=tuple(r['sha256'] for r in refs['references']),reference_manifest_hash=digest(refs))
    baseline=probe_plan(design,parent)
    if canonical(baseline)!=canonical(probe['plan.json']):raise ValueError('Completed probe plan mismatch')
    records=[v for k,v in probe.items() if k.startswith('shards/')]
    report=probe_report(baseline,records);saved=dict(probe['report.json']);saved.pop('generation_accounting',None)
    if canonical(report)!=canonical(saved) or not report['complete']:raise ValueError('Incomplete or changed baseline report')
    plan=build_prompt_plan(config,design,baseline,records)
    if plan['requests_hash']!=config['requests_hash'] or plan['models']['actors']['snapshot']!=config['actor_snapshot']:
        raise ValueError('Frozen prompt-control requests/model changed')
    return plan


def build_prompt_plan(config,design,baseline,records):
    """No label participates in messages or request identity construction."""
    indexed={r['context_id']:r for r in records}
    requests=[];contexts=[];saved={};tasks={};labels={}
    for c in baseline['contexts']:
        if c['arm']!='private':continue
        tid=c['task_id'];task=task_from_dict(baseline['tasks'][tid]);record=indexed[c['context_id']]
        if task.split!='train' or record['call']['seed']!=c['seeds'][0]:raise ValueError('Private comparator split/seed mismatch')
        row={'task':dc.asdict(task),'agent':c['recipient'],'seed':c['seeds'][0],
             'messages':[dc.asdict(m) for m in warmstart_prompt(task)],'baseline_probe_work_id':record['work_id'],
             'baseline_context_id':c['context_id'],'max_new_tokens':256}
        row['request_id']=digest(row);requests.append(row)
        context={'task_id':tid,'family':task.family,'recipient':c['recipient'],'phase':'private',
                 'arm':'answer_only','messages':row['messages'],'seeds':[row['seed']]}
        context['context_id']=digest(context);contexts.append(context);saved[context['context_id']]=record
        tasks[tid]=dc.asdict(task);labels[tid]=baseline['labels'][tid]
    if (len(contexts)!=72 or len(tasks)!=24 or len(saved)!=72
            or Counter(t['family'] for t in tasks.values())!={'arc_challenge':12,'logiqa':12}
            or any(sorted(c['recipient'] for c in contexts if c['task_id']==tid)!=[0,1,2] for tid in tasks)):
        raise ValueError('Require 24 balanced tasks and three actors each')
    return {'kind':'preparation_prompt_control','execution_implemented':True,'gpu_verified':False,
        'training_design':design,'config':config,'requests':requests,'requests_hash':digest(requests),
        'contexts':contexts,'tasks':tasks,'labels':labels,'baseline_records':saved,'models':baseline['models'],
        'reference_manifest_hash':baseline['reference_manifest_hash'],
        'budget':{'generation_calls_upper_bound':72,'generated_tokens_upper_bound':18432,
                  'input_tokens_upper_bound':276480,'optimizer_steps':0,'teacher_forced_forwards':0},
        'training_executed':False,'full_pact_ready':False}


def prompt_report(plan,records):
    items={i['work_id']:i for i in curated_requests(plan)}
    if len({r['work_id'] for r in records})!=len(records) or any(r['work_id'] not in items for r in records):
        raise ValueError('Unknown/duplicate prompt-control records')
    rows=[]
    for r in records:
        item=items[r['work_id']];c=item['context'];call=r['call'];old=plan['baseline_records'][c['context_id']]
        if (r['request_hash']!=digest(item) or call['seed']!=item['seed'] or call['seed']!=old['call']['seed']
                or call['snapshot']!=plan['models']['actors']['snapshot'] or call['snapshot']!=old['call']['snapshot']
                or call['phase']!='private' or call['actor']!=f"agent-{c['recipient']}"
                or canonical(call['messages'])!=canonical(c['messages'])):
            raise ValueError('Prompt-control provenance mismatch')
        allowed=tuple(o['answer_id'] for o in plan['tasks'][c['task_id']]['options']);gold=plan['labels'][c['task_id']]
        before,_,bs=parse_answer(old['raw'],allowed,stop_reason=old['call']['stop_reason'])
        after,_,ns=parse_answer(r['raw'],allowed,final=True,stop_reason=call['stop_reason'])
        rows.append({'task_id':c['task_id'],'family':c['family'],'agent':c['recipient'],'seed':item['seed'],
            'baseline_work_id':old['work_id'],'work_id':r['work_id'],'baseline_answer':before,'answer':after,
            'baseline_parser_status':bs,'parser_status':ns,'baseline_correct':bs=='ok' and before==gold,
            'correct':ns=='ok' and after==gold,'raw':r['raw'],'stop_reason':call['stop_reason'],
            'input_tokens':call['input_tokens'],'output_tokens':call['output_tokens']})
    def summary(values):
        return {'paired_responses':len(values),'baseline_correct':sum(r['baseline_correct'] for r in values),
            'correct':sum(r['correct'] for r in values),'parser_counts':dict(Counter(r['parser_status'] for r in values)),
            'transitions':dict(Counter(f"{r['baseline_correct']}->{r['correct']}" for r in values))}
    teams=[]
    for tid in plan['tasks']:
        rs=[r for r in rows if r['task_id']==tid]
        teams.append({'task_id':tid,'complete':len(rs)==3,'baseline_correct_agents':sum(r['baseline_correct'] for r in rs) if len(rs)==3 else None,
                      'correct_agents':sum(r['correct'] for r in rs) if len(rs)==3 else None})
    return {'kind':'preparation_prompt_control','complete':len(rows)==72,'completed_records':len(rows),
        'expected_records':72,'missing_records':72-len(rows),'decision':'complete_requires_review' if len(rows)==72 else 'incomplete',
        'baseline':'cached completed prepared-actor packet probe; same actor and seed; different prompt contract',
        'summary':summary(rows),'by_family':{f:summary([r for r in rows if r['family']==f]) for f in ('arc_challenge','logiqa')},
        'by_agent':{str(a):summary([r for r in rows if r['agent']==a]) for a in range(3)},'teams':teams,'comparisons':rows,
        'training_executed':False,'training_pairs_exported':False,'full_pact_ready':False}
