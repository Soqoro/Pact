"""Source-specific development reports; strict stored packets, no re-parsing."""
from collections import Counter
from ...util import read_json, write_json, digest
from ...artifacts import ShardStore
from ..allocation_v3 import report as old, runner, storage
from ..gpqa_source import results
from .plan import VERSION


def policy_report(root,p):
    candidate=runner.prospective(root,p);lock=read_json(root/'policy-lock.json')
    aliases={'S0':'S0',**lock['aliases']};outcomes=[]
    for row in candidate['records']:
        tid=row['task']['task_id'];path=root/'attacks/policy'/f'{digest(tid)}.json'
        accepted=read_json(path)['accepted'] if path.exists() else None
        for team,owner in aliases.items():
            for condition in ('clean','exchange'):
                value=old.outcome(root,row,'policy',owner,condition,candidate['labels'][tid])
                value.update(team=team,attack_accepted=accepted)
                value['format_status']=value.pop('final_status')
                outcomes.append(value)
    report=results.report(candidate,outcomes)
    report.update(aliases=lock['aliases'],source_standard=p['source_standard'],
                  limitations=p['limitations'],fixture=p['fixture'],analysis=p['analysis'])
    for name,value in report['contrasts'].items():
        value['primary']=name.startswith('exchange/') and name.split('/',1)[1] in p['analysis']['primary']
        if name.startswith('clean/'):
            estimate=value['equal_source'].get('estimate')
            value['prespecified_clean_tolerance']=p['analysis']['clean_tolerance']
            value['point_estimate_within_tolerance']=(estimate>=-p['analysis']['clean_tolerance']) if estimate is not None else None
            value['utility_target_not_certified_bound']=True
    write_json(root/'policy_outcomes.private.json',outcomes)
    write_json(root/'policy_results.json',report)
    return report


def report(root,p):
    intents=[read_json(path) for path in (root/'attempts').glob('*.json')]
    events=list(ShardStore(root/'events').records()) if (root/'events').exists() else []
    counts={part:{kind:sum(i['cost'].get(kind,0) for i in intents if i['identity']['part']==part)
                  for kind in ('generation','scores','updates','training_forwards')} for part in ('assay','policy')}
    generated=[e['value'] for e in events if e['intent']['identity']['kind']=='generation']
    summary={'version':VERSION,'fixture':p['fixture'],'scientific_result':'mock_only' if p['fixture'] else 'development_only',
        'physical_attempts':counts,'committed_operations':len(events),'unresolved':len(intents)-len(events),
        'recovery_safe':storage.safe(root),'conditional_limits':p['budgets'],
        'reserved_output_tokens':512*sum(v['generation'] for v in counts.values()),
        'input_tokens':sum(v['call']['input_tokens'] for v in generated),
        'output_tokens':sum(v['call']['output_tokens'] for v in generated),
        'format_status_counts':dict(Counter(v['packet']['status'] for v in generated)),
        'historical_spending':None,'remaining_historical_budget':None,
        'source_standard':p['source_standard'],'limitations':p['limitations'],
        'evaluation_source_weights':p['evaluation_source_weights'],
        'implementation_authorizes_execution':False,
        'stages':sorted(v.stem for v in (root/'stages').glob('*.json'))}
    if any((root/'outputs').glob('*.json')):old.assay_support(root,p)
    if (root/'stages/score.json').exists():old.assay_report(root,p)
    if (root/'policy-lock.json').exists():policy_report(root,p)
    write_json(root/'summary.json',summary)
    return summary
