"""Invented content only, real parsers/graph/scoring/export, zero model work."""
from ..evaluation_source.fixtures import inputs as old_inputs
from ...util import digest,canonical,write_json
from . import sources as s,review,results


def inputs():
    source,ob,train,val,ex=old_inputs()
    raw=[]
    for i in range(70):
        word=digest(['invented-main',i])
        raw.append({'Question':'Invented exercise '+word,'Correct Answer':word+' correct',
            'Incorrect Answer 1':word+' wrong one','Incorrect Answer 2':word+' wrong two',
            'Incorrect Answer 3':word+' wrong three','High-level domain':'Physics','Record ID':'invented-'+str(i)})
    import csv,io
    stream=io.StringIO();writer=csv.DictWriter(stream,fieldnames=list(raw[0]));writer.writeheader();writer.writerows(raw)
    raw=s.parse_csv(stream.getvalue())
    gp,labels,aud=s.reconcile(raw,[],[],'b'*64,reviewed=True)
    lr,ll,la=s.old.eligibility([],train,val,source,ex,fixture=True)
    candidate={**s.select([*gp,*lr],{**labels,**ll}),'fixture':True}
    return source,candidate,raw


def build(root):
    source,candidate,raw=inputs()
    ln={'S0':{'fixture':True},'current_tensor_reload_verified':False,'external_history_reconciled':False}
    audit={'fixture':True,'status':'implemented_fixture_only','blockers':['real_source_and_execution_unverified'],
        'sources':{f:{'status':'invented_fixture'} for f in s.SOURCES_EVAL},'eligibility':{'permitted_counts':dict.fromkeys(s.SOURCES_EVAL,70)}}
    review.save(root,source,ln,audit,candidate)
    from ..allocation_v3 import design as d
    probes={f:[r['task']['task_id'] for r in source['records'] if r['split']=='allocation_probe' and r['family']==f] for f in d.SOURCES}
    scores={}
    for tid in sum(probes.values(),[]):
        for kind in ('private_bank','clean','exchange'):scores['S0',tid,kind]={'raw_nll':2.,'capped_nll':2.}
    for b,block in enumerate(source['blocks']):
        for f in d.FAMILIES:
            for tid in probes[block['family']]:
                for kind in ('private_bank','clean','exchange'):
                    value=1.+.1*d.FAMILIES.index(f)
                    scores[f'block-{b}-{f}',tid,kind]={'raw_nll':value,'capped_nll':value}
    credits=d.credits(scores,source['blocks'],probes,dict.fromkeys(sum(probes.values(),[]),True))
    policies=d.compile_policies(source['blocks'],credits['terminal'],credits['private_bank'],d.derangement(source['blocks']),ln['S0'])
    write_json(root/'mock-assay.private.json',{'fixture':True,'score_records':len(scores),'credits':credits,'policies':policies})
    outcomes=[]
    for r in candidate['records']:
        gold=candidate['labels'][r['task']['task_id']]
        packet=canonical({'answer':gold,'justification':'Invented fixture'})
        attack={'accepted':True,'sender':r['sender'],'packet':{'status':'ok','answer':'A','justification':'invented'}}
        for team in results.TEAMS:
            for cond in ('clean','exchange'):
                outcomes.append(results.score(r,gold,team,cond,[packet]*3,[packet]*3,packet,attack))
    write_json(root/'mock-outcomes.private.json',outcomes)
    return review.export(root)
