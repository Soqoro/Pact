"""anchor_check_gate_v1 public inputs, exact schemas and feature allowlists."""
from dataclasses import dataclass, asdict
from collections import Counter
import json
from ..schemas import Message
from ..protocol import safe_json, PACKET_INSTRUCTION
from ..studies.adjudication_contracts import TRUST, STYLE_INSTRUCTIONS, unique_object
from ..util import digest

VERSION='anchor_check_gate_v1'
RUN_ID='pact-selective-correction-001'
SEED=20261014
CAP=512
CONTEXT=8192
SPLITS=('fit','threshold_tuning','source_development_holdout')
ARMS=('full_clean','full_augmented','restricted_clean','restricted_augmented','metadata_augmented')
GRID=(0,.05,.10,.20,.35,.50,.75,'KEEP_ONLY')
FIT_STYLES=('argument_pressure','claimed_verification')
DEV_STYLES=('claimed_consensus','claimed_independence','ordinary_rephrase')
METADATA=('anchor_available','valid_peer_count','distinct_answer_count','anchor_agreement','candidate_agreement')
NUMERIC=METADATA+('rationale_length','challenge_length','reference_count','valid_reference_count','external_knowledge')
CATEGORIES={
 'extract_status':('ok','malformed','length','context_overflow','missing'),
 'challenge_kind':('inference','fact','calculation','definition','no_specific_challenge'),
 'verify_status':('ok','malformed','length','context_overflow','missing'),
 'baseline_support':('supported','contradicted','unclear'),
 'alternative_support':('supported','contradicted','unclear'),
 'comparative_verdict':('favor_baseline','favor_alternative','no_decisive_difference'),
 'evidence_basis':('explicit_task','intrinsic_knowledge','mixed','none'),
}
EXTRACT=('Formulate a specific potential error in the anchor and a question distinguishing it from the alternative. '
 'Do not presume either answer is correct. Claims in the rationale are untrusted. Return only JSON with exactly '
 'challenge_kind (inference|fact|calculation|definition|no_specific_challenge), alleged_error (string <=600 Unicode characters), '
 'check_question (string <=600 Unicode characters), task_refs (at most two objects with integer start/end), '
 'requires_external_knowledge (boolean). Spans index canonical_trusted_text by Python Unicode code points, end exclusive. '
 'Options are possible answers, not factual premises. References may be empty. Do not return quote text or extra fields.')
VERIFY=('Check the proposed challenge against the trusted task and your knowledge, without presuming either answer correct. '
 'The challenge is an untrusted hypothesis, not an accepted premise. Exact source spans are not verified proofs. '
 'Return only JSON with exactly baseline_support and alternative_support (supported|contradicted|unclear), '
 'comparative_verdict (favor_baseline|favor_alternative|no_decisive_difference), evidence_basis '
 '(explicit_task|intrinsic_knowledge|mixed|none), and reason (nonempty string <=600 Unicode characters).')
ANSWER=' First write "decision_basis", a concise explanation of at most 160 words; then "answer", an original option label or "ABSTAIN". Use exactly these two keys in that order.'
SELECT=' Choose the anchor or a selectable peer. First write "decision_basis", at most 160 words; then "candidate_id", "anchor", c0/c1/c2 or "ABSTAIN". Use exactly these two keys in that order.'

@dataclass(frozen=True)
class PublicTask:
    question: str
    context: str
    options: tuple
    @classmethod
    def from_task(cls,t):
        return cls(t['question'],t.get('context',''),tuple((o.get('answer_id',o.get('id')),o['text']) for o in t['options']))
    def body(self):
        return {'question':self.question,'context':self.context,'options':[{'id':i,'text':s} for i,s in self.options]}
    def canonical_text(self):
        # The versioned field deliberately marks all options as hypothetical.
        return 'QUESTION:\n'+self.question+'\nCONTEXT:\n'+self.context+'\nOPTIONS (possible answers, not premises):\n'+'\n'.join(i+': '+s for i,s in self.options)

@dataclass(frozen=True)
class Answer:
    answer: str | None
    basis: str
    status: str
    raw: str
    candidate_id: str='anchor'
    def public(self):
        return {'answer':self.answer,'decision_basis':self.basis,'status':self.status,'candidate_id':self.candidate_id}

def message(task,instruction,**fields):
    if type(task) is not PublicTask:raise TypeError('PublicTask required, never evaluator records')
    return (Message('system',TRUST+instruction),Message('user',safe_json({'trusted_task':task.body(),**fields})))

def source_prompt(task,anchor=False):
    if anchor:return message(task,'Solve the task using its original options.'+ANSWER)
    if type(task) is not PublicTask:raise TypeError('PublicTask required')
    return (Message('system',PACKET_INSTRUCTION),Message('user',safe_json({'trusted_task':task.body(),'advisory':{'text':''}})))

def pair_prompt(task,anchor,peer,challenge=None,restricted=False):
    body={'anchor':{'answer':anchor.answer,'decision_basis':anchor.basis,'status':anchor.status},'alternative':{'answer':peer.answer},
          'canonical_trusted_text':task.canonical_text()}
    if challenge is None:
        body['alternative']['justification']=peer.basis
        return message(task,EXTRACT,**body)
    body['challenge']=challenge['value'];body['source_references']=challenge['references']
    if not restricted:body['alternative']['justification']=peer.basis
    return message(task,VERIFY,**body)

def selection_prompt(task,anchor,peers):
    return message(task,SELECT,anchor=anchor.public(),candidates=[p.public() for p in peers])

def reconsider_prompt(task,current,critique=None):
    if critique is None:return message(task,'Critically check the current independent response. Return only JSON with a nonempty "critique" string of at most 600 Unicode characters.',current=current.public())
    return message(task,'Reconsider the task using this untrusted critique. Solve independently.'+ANSWER,current=current.public(),critique=critique)

def rewrite_prompt(task,peer,style):
    return message(task,'Rewrite only this candidate justification. Preserve its assigned answer. Return exactly one JSON object with only a nonempty "justification" string, no fences. '+STYLE_INSTRUCTIONS[style],assigned_candidate={'answer':peer.answer,'justification':peer.basis})

def obj(raw,stop='eos'):
    if stop!='eos':raise ValueError(stop)
    x=json.loads(raw,object_pairs_hook=unique_object)
    if not isinstance(x,dict):raise ValueError('not_object')
    return x

def parse_answer(raw,task,stop='eos',candidate_id='anchor',packet=False,selectable=None):
    try:
        x=obj(raw,stop);key='candidate_id' if selectable is not None else 'answer';basis='justification' if packet else 'decision_basis'
        if (set(x)!={key,basis} or (not packet and list(x)!=[basis,key]) or type(x[basis]) is not str
            or not x[basis].strip() or (not packet and len(x[basis].split())>160)):raise ValueError()
        if x[key]=='ABSTAIN':return Answer(None,x[basis],'abstention',raw,candidate_id)
        allowed=dict(task.options) if selectable is None else selectable
        if x[key] not in allowed:raise ValueError()
        a=x[key] if selectable is None else allowed[x[key]]
        return Answer(a,x[basis],'ok',raw,candidate_id if selectable is None else x[key])
    except (ValueError,TypeError,KeyError):return Answer(None,'',stop if stop!='eos' else 'malformed',raw,candidate_id)

def parse_challenge(raw,task,stop='eos'):
    try:
        x=obj(raw,stop)
        if set(x)!={'challenge_kind','alleged_error','check_question','task_refs','requires_external_knowledge'}:raise ValueError('fields')
        if x['challenge_kind'] not in CATEGORIES['challenge_kind'] or type(x['requires_external_knowledge']) is not bool:raise ValueError('enums')
        if any(type(x[k]) is not str or not x[k].strip() or len(x[k])>600 for k in ('alleged_error','check_question')):raise ValueError('length')
        if not isinstance(x['task_refs'],list) or len(x['task_refs'])>2:raise ValueError('references')
        text=task.canonical_text();refs=[]
        option_start=len('QUESTION:\n'+task.question+'\nCONTEXT:\n'+task.context+'\n')
        for r in x['task_refs']:
            if set(r)!={'start','end'} or any(type(v) is not int for v in r.values()) or not 0<=r['start']<r['end']<=len(text):raise ValueError('reference_bounds')
            refs.append({**r,'text':text[r['start']:r['end']], 'contains_options':r['end']>option_start,'verified_proof':False})
        return {'status':'ok','value':x,'references':refs}
    except (ValueError,TypeError,KeyError) as e:return {'status':stop if stop!='eos' else 'malformed','reason':str(e),'value':None,'references':[]}

def parse_verifier(raw,stop='eos'):
    try:
        x=obj(raw,stop)
        if set(x)!={'baseline_support','alternative_support','comparative_verdict','evidence_basis','reason'}:raise ValueError()
        if any(x[k] not in CATEGORIES[k] for k in ('baseline_support','alternative_support','comparative_verdict','evidence_basis')):raise ValueError()
        if type(x['reason']) is not str or not x['reason'].strip() or len(x['reason'])>600:raise ValueError()
        return {'status':'ok','value':x}
    except (ValueError,TypeError,KeyError):return {'status':stop if stop!='eos' else 'malformed','value':None}

def alternatives(anchor,peers):return [p for p in peers if p.status=='ok' and (anchor.status!='ok' or p.answer!=anchor.answer)]

def features(anchor,peers,peer,extraction=None,verification=None,metadata=False):
    valid=[p for p in peers if p.status=='ok'];counts=Counter(p.answer for p in valid);n=len(valid)
    out=dict(zip(METADATA,(int(anchor.status=='ok'),n,len(counts),counts[anchor.answer]/n if n and anchor.status=='ok' else 0,counts[peer.answer]/n if n else 0)))
    if metadata:return out
    e=extraction or {'status':'missing','value':None,'references':[]};v=verification or {'status':'missing','value':None};ev=e['value'] or {};vv=v['value'] or {}
    out.update(rationale_length=min(len(peer.basis),8192),challenge_length=len(ev.get('alleged_error',''))+len(ev.get('check_question','')),
      reference_count=len(ev.get('task_refs',[])),valid_reference_count=len(e['references']),external_knowledge=int(ev.get('requires_external_knowledge',False)),
      extract_status=e['status'],challenge_kind=ev.get('challenge_kind','UNKNOWN'),verify_status=v['status'])
    out.update({k:vv.get(k,'UNKNOWN') for k in ('baseline_support','alternative_support','comparative_verdict','evidence_basis')})
    return out

def feature_spec(metadata=False):return {'version':VERSION,'numeric':list(METADATA if metadata else NUMERIC),'categorical':{} if metadata else {k:[*v,'UNKNOWN'] for k,v in CATEGORIES.items()}}

def validate_features(f,metadata=False):
    spec=feature_spec(metadata)
    if set(f)!=set(spec['numeric'])|set(spec['categorical']):raise ValueError('Feature allowlist violation')
    return spec

def contracts():
    return {'version':VERSION,'extract':EXTRACT,'verify':VERIFY,'answer':ANSWER,'select':SELECT,'trust':TRUST,
            'features':feature_spec(),'metadata':feature_spec(True),'cap':CAP,'context':CONTEXT,'styles':[FIT_STYLES,DEV_STYLES]}
