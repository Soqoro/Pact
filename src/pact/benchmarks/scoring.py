"""Offline native scoring. No generated program is ever executed in this process."""
import importlib.metadata
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import time
from .contracts import parse
from .registry import MATH_REV, EVALPLUS_REV, LIVEBENCH_REV
from ..util import digest, file_hash, read_json, write_json

LIMITS={'wall_seconds':120,'cpu_seconds':100,'memory_bytes':4*1024**3,'processes':64,'output_bytes':1024**2,
        'min_time_limit':1.0,'gt_time_limit_factor':4.0}
MATH_POLICY={'float_rounding':6,'numeric_precision':15,'strict':True,'allow_set_relation_comp':False,
             'timeout_seconds':5,'extraction':'one_box_no_fallback','plain_text':'text_command_or_alphabetic_words_exact', 'dependencies':{'latex2sympy2_extended':'1.11.0','sympy':'1.14.0','mpmath':'1.3.0','antlr4-python3-runtime':'4.13.2'}}

def evaluator_identity(kind):
    return {'schema_version':1,'kind':kind,'code':{'math_free_response':MATH_REV,'python_program':EVALPLUS_REV,
        'native_livebench':LIVEBENCH_REV,'mcq':'strict_mcq_v1'}[kind],
        'limits':LIMITS,'math_policy':MATH_POLICY,'adapter_hash':file_hash(Path(__file__)),
        'worker_hash':file_hash(Path(__file__).with_name('score_worker.py'))}

def unavailable(reason):return {'availability':reason,'syntactic_valid':None,'full_success':None,'native_score':None}

def score(task,eval_spec,raw,*,final=False,stop='eos',python=None):
    pred=parse(task,raw,final=final,stop=stop)
    if stop=='context_overflow':return {**unavailable('context_overflow'),'parse':pred}
    if pred['status']!='ok':return {'availability':'scored','syntactic_valid':False,'full_success':False,'native_score':0.0,'parse':pred}
    if task.kind=='mcq':
        success=pred['value']==eval_spec['answer']
        return {'availability':'scored','syntactic_valid':True,'full_success':success,'native_score':float(success),'parse':pred}
    if task.kind in ('python_program','native_livebench'):
        return {**unavailable('pending_isolated_scoring'),'parse':pred}
    job={'kind':task.kind,'eval':eval_spec,'prediction':pred['value'],'identity':evaluator_identity(task.kind)}
    result=math_worker(job,python or sys.executable)
    return {**result,'parse':pred}


def math_worker(job,python):
    """Bounded parser subprocess; neither prediction nor gold is Python source."""
    started=time.monotonic()
    with tempfile.TemporaryDirectory(prefix='pact-math-') as temp:
        root=Path(temp);write_json(root/'job.json',job)
        command=[str(python),'-I',str(Path(__file__).with_name('score_worker.py')),str(root/'job.json'),str(root/'result.json')]
        proc=subprocess.Popen(command,stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,
            cwd=root,env={'PATH':os.defpath,'HOME':str(root),'OMP_NUM_THREADS':'1'},start_new_session=True)
        try:proc.wait(timeout=20)
        except subprocess.TimeoutExpired:
            os.killpg(proc.pid,signal.SIGKILL);proc.wait();return unavailable('scorer_timeout')
        if proc.returncode or not (root/'result.json').exists():return unavailable('scorer_unavailable_or_crashed')
        result=read_json(root/'result.json');result['scoring_seconds']=time.monotonic()-started
        return result


def scoring_job(task,eval_spec,result,request_key):
    pred=parse(task,result['raw'],final=result['call']['phase']=='final',stop=result['call']['stop_reason'])
    body={'kind':task.kind,'task_id':task.task_id,'task_hash':digest(task),'eval':eval_spec,
          'test_hash':digest(eval_spec),'response_hash':digest(result['raw']),'prediction':pred['value'],
          'parse_status':pred['status'],'request_key':request_key,'identity':evaluator_identity(task.kind)}
    return {**body,'job_hash':digest(body)}


def import_result(job,result):
    if result.get('job_hash')!=job['job_hash'] or result.get('identity')!=job['identity']:
        raise ValueError('Scoring job/evaluator identity mismatch')
    if not result.get('sandbox',{}).get('enforced'):raise ValueError('Missing enforced sandbox receipt')
    v=result['score'];status=v['availability']
    if status=='scored':
        n=v['native_score']
        if type(n) not in (int,float) or not 0<=n<=1 or type(v['full_success']) is not bool or v['full_success']!=(n==1):
            raise ValueError('Invalid full-credit/native score semantics')
        if job['kind']!='native_livebench' and n not in (0,1):raise ValueError('Binary evaluator cannot import fractional credit')
    elif v['full_success'] is not None or v['native_score'] is not None:raise ValueError('Unavailable scorer cannot fabricate outcome')
    return v
