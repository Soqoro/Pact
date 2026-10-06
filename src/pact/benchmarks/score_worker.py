"""Trusted scorer entrypoint. Code/LiveBench require an OS-isolated invocation."""
import json
import os
from pathlib import Path
import sys


def require_pin(package,commit):
    import importlib.metadata as md
    distribution=md.distribution(package)
    info=json.loads(distribution.read_text('direct_url.json') or '{}')
    if info.get('vcs_info',{}).get('commit_id')!=commit and info.get('url') != 'https://github.com/huggingface/Math-Verify/archive/'+commit+'.zip':
        raise RuntimeError('scorer_revision_unverified')


def math_score(job):
    require_pin('math-verify',job['identity']['code'])
    import importlib.metadata as md
    for package,version in {'latex2sympy2_extended':'1.11.0','sympy':'1.14.0','mpmath':'1.3.0','antlr4-python3-runtime':'4.13.2'}.items():
        if md.version(package)!=version:raise RuntimeError('math_dependency_mismatch')
    from math_verify import parse,verify,LatexExtractionConfig
    import re
    def extract(v):
        if len(v)>16384:raise ValueError('expression_too_long')
        text=re.fullmatch(r'\\text\{([^{}]*)\}',v.strip())
        if text:return ['TEXT:'+text[1]]
        if re.fullmatch(r'[A-Za-z]{2,}(?: [A-Za-z]+)*',v.strip()):return ['TEXT:'+v.strip()]
        return parse('\\boxed{'+v+'}',extraction_config=[LatexExtractionConfig()],fallback_mode='no_fallback',
                     extraction_mode='first_match',parsing_timeout=5,raise_on_error=True)
    gold=extract(job['eval']['answer'])
    if not gold:raise RuntimeError('invalid_gold_reference')
    prediction=extract(job['prediction'])
    if not prediction:return {'availability':'scored','syntactic_valid':False,'full_success':False,'native_score':0.0}
    if isinstance(gold[0],str) and gold[0].startswith('TEXT:'):
        correct=gold==prediction
    else:correct=bool(verify(gold,prediction,float_rounding=6,numeric_precision=15,strict=True,
                             allow_set_relation_comp=False,timeout_seconds=5,raise_on_error=True))
    return {'availability':'scored','syntactic_valid':True,'full_success':correct,'native_score':float(correct)}


def code_score(job):
    require_pin('evalplus',job['identity']['code'])
    from evalplus.data.mbpp import mbpp_deserialize_inputs
    from evalplus.gen.util import trusted_exec
    from evalplus.evaluate import check_correctness
    from evalplus.eval._special_oracle import MBPP_OUTPUT_NOT_NONE_TASKS
    p=dict(job['eval']['problem'])
    for key in ('base_input','plus_input'):p[key]=mbpp_deserialize_inputs(p['task_id'],p[key])
    expected={}
    for kind in ('base','plus'):
        values,times=trusted_exec(p['prompt']+p['canonical_solution'],p[kind+'_input'],p['entry_point'],
                                 record_time=True,output_not_none=p['entry_point'] in MBPP_OUTPUT_NOT_NONE_TASKS)
        expected[kind]=values;expected[kind+'_time']=times
    # Gold errors above remain infrastructure errors, never model failures.
    value=check_correctness('mbpp',0,p,job['prediction'],expected,base_only=False,fast_check=False,
                           min_time_limit=1.0,gt_time_limit_factor=4.0)
    base=value['base'][0]=='pass';plus=value['plus'][0]=='pass';success=base and plus
    return {'availability':'scored','syntactic_valid':True,'full_success':success,'native_score':float(success),
            'base_pass':base,'plus_pass':plus,'base_tests':len(p['base_input']),'plus_tests':len(p['plus_input'])}


def live_score(job):
    require_pin('livebench',job['identity']['code'])
    from livebench.common import MatchSingle
    from livebench.gen_ground_truth_judgment import play_a_match_gt
    q=job['eval']['problem']
    if q['category'] not in ('reasoning','math','data_analysis','language','coding') or q['task']=='agentic_coding' or len(q['turns'])!=1:
        raise RuntimeError('unsupported_native_task')
    match=MatchSingle(question=q,model='pact-offline',answer={'choices':[{'turns':[job['prediction']]}]})
    value=play_a_match_gt(match,None,False)
    if not value or value.get('eval_status') == 'eval_error':raise RuntimeError('native_scorer_error')
    score=value['score']
    if not isinstance(score,(int,float)) or not 0<=score<=1:raise RuntimeError('unknown_native_score_scale')
    return {'availability':'scored','syntactic_valid':True,'native_score':score,'full_success':score==1}


def main():
    import resource
    # Set before parsing response/gold or importing symbolic libraries.
    resource.setrlimit(resource.RLIMIT_AS,(4*1024**3,4*1024**3))
    resource.setrlimit(resource.RLIMIT_CPU,(100,100))
    resource.setrlimit(resource.RLIMIT_FSIZE,(1024**2,1024**2))
    job=json.loads(Path(sys.argv[1]).read_text())
    try:
        if job['kind']=='math_free_response':value=math_score(job)
        else:
            if os.environ.get('PACT_ISOLATED_WORKER')!='1':raise RuntimeError('safe_execution_unavailable')
            value=code_score(job) if job['kind']=='python_program' else live_score(job)
    except Exception as exc:
        # Only type, never gold/tests/credential-bearing errors leave the worker.
        value={'availability':'evaluator_error','error_type':type(exc).__name__,
               'syntactic_valid':None,'native_score':None,'full_success':None}
    import importlib.metadata as md
    value['evaluator_environment']={'python':sys.version.split()[0],
        'packages':dict(sorted((d.metadata['Name'],d.version) for d in md.distributions() if d.metadata['Name']))}
    Path(sys.argv[2]).write_text(json.dumps(value))

if __name__=='__main__':main()
