"""Invented CPU fixtures only; never substitute these outcomes for official scores."""
import dataclasses as dc
from .data import normalize
from .registry import REGISTRY
from .contracts import BenchmarkInput,parse
from ..backends.registry import generation_parameters
from ..schemas import CallRecord
from ..util import digest,canonical
from types import SimpleNamespace

EXAMPLES={
 'mmlu-pro':{'question_id':0,'question':'Fictional fixture: choose the tenth token.','options':['token-'+str(i) for i in range(10)],'answer':'J','answer_index':9,'category':'math','cot_content':'EVALUATOR_ONLY'},
 'musr':{'narrative':'A fictional blue cube is carried from room one to room two.','question':'Where is the cube?','choices':"['room one', 'room two']",'answer_index':'1','answer_choice':'room two'},
 'math-500':{'unique_id':'fixture/0','problem':'Fictional fixture: compute one half plus one half.','answer':'1','solution':'EVALUATOR_ONLY','subject':'Algebra','level':1},
 'mbpp-plus':{'task_id':'Mbpp/0','prompt':'"""Write fixture_increment(x), returning x plus one."""\n','entry_point':'fixture_increment','canonical_solution':'def fixture_increment(x): return x+1','base_input':[[0]],'plus_input':[[7]],'atol':0.0},
 'livebench':{'question_id':'fixture-0','category':'reasoning','task':'web_of_lies_v3','turns':['Fictional task: output TRUE.'],'ground_truth':'TRUE','livebench_release_date':'2026-06-25','livebench_removal_date':''},
}

def dataset(name,n=2):
    if name=='gpqa':
        row=normalize('mmlu-pro',EXAMPLES['mmlu-pro'],'fixture');row['task'].update(family='gpqa',dataset_revision=REGISTRY['gpqa'].revision)
        row['task']['options']=row['task']['options'][:4]
        row['task']['question']='Invented four-choice fixture: choose token-1.'
        row['eval']['answer']='B'
    else:row=normalize(name,EXAMPLES[name],'fixture',domain='object_placements')
    rows=[]
    import copy
    for i in range(n):
        r=copy.deepcopy(row);r['task']['task_id']=name+':fixture-'+str(i);r['group_id']=digest([name,i]);r['stratum']='fixture';rows.append(r)
    return {'schema_version':1,'fixture':True,'dataset':name,'receipt':{'fixture':True},'selected':rows,
            'manifest':{'partitions':{'characterization_dev':[r['task']['task_id'] for r in rows],'confirmation_locked':[],'reserve_locked':[]},'training_allowed':False}}

class MockNative:
    def __init__(self,key,plan):
        self.key=key;self.plan=plan;self.calls=[]
        tokenizer=SimpleNamespace(eos_token_id=2,pad_token_id=2,bos_token_id=1)
        body={'spec':plan['models'][key],'adapters':[],'template_hash':digest('fixture'),
              'parameters':{k:generation_parameters(tokenizer,{'eos_token_id':[2,3]},final=k=='final') for k in ('packet','final')}}
        self.identity={**body,'snapshot':digest(body)}
    def generate(self,r):
        kind=r.task.kind;raw=canonical({'answer':'J' if len(r.task.options)==10 else 'B',**({} if r.deterministic else {'justification':'Fictional fixture.'})}) if kind=='mcq' else '\\boxed{1}' if kind=='math_free_response' else '```python\ndef fixture_increment(x): return x+1\n```' if kind=='python_program' else 'TRUE'
        rendered=canonical(r.messages);params={**self.identity['parameters']['final' if r.deterministic else 'packet'],'max_new_tokens':r.max_tokens}
        call=CallRecord(r.actor,r.phase,self.identity['snapshot'],r.seed,r.messages,rendered,digest(rendered),self.identity['template_hash'],canonical(params),4,2,'eos',0.01)
        self.last_generation={'prompt_ids':[1]*4,'completion_ids':[1,3],'raw':raw,'context_hash':digest(rendered)};self.calls.append(call)
        return raw,call
    def resource_usage(self):return {'mock_only':True}
    def close(self):pass

def fixture_score(task,spec,result):
    p=parse(task,result['raw'],final=result['call']['phase']=='final',stop=result['call']['stop_reason'])
    return {'availability':'scored','syntactic_valid':p['status']=='ok','full_success':p['status']=='ok','native_score':float(p['status']=='ok'),'fixture':True}
