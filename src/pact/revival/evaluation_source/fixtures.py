"""Invented CPU records and strict mock packets. No model backend invocation."""
from dataclasses import asdict
from pathlib import Path
import tempfile
import json
import hashlib
from ...util import digest, write_json, canonical
from ...schemas import TaskInput,TaskLabel,Option
from ...datasets import content_group
from ..allocation_v3 import evidence as e
from . import sources as s,graph as g,review,results


def inputs():
    source=e.fixture_source();ob=[];training=[];validation=[]
    for family in s.SOURCES_EVAL:
        for i in range(70):
            words=' '.join(digest([family,i,k])[:12] for k in range(8))
            if family=='openbookqa':
                row={'id':f'invented-{i}','question_stem':f'Invented exercise {words}',
                     'choices':{'label':['D','B','A','C'],'text':[f'{words} choice {k}' for k in range(4)]},'answerKey':'B'}
                ob.append(s.openbook_row(row,'a'*40,'b'*64))
            else:
                t=TaskInput(f'logiqa:new-fixture-{i}',family,'train',str(i),'a'*40,'c'*64,
                            'Invented '+words,tuple(Option(k,words+' '+k,k) for k in 'ABCD'))
                training.append((t,TaskLabel(t.task_id,'B')))
    for family in ('arc_challenge','logiqa'):
        t=TaskInput(f'{family}:validation-fixture',family,'validation','val','a'*40,'c'*64,
                    f'Unrelated validation {family}',tuple(Option(k,k,k) for k in 'ABCD'))
        validation.append((t,TaskLabel(t.task_id,'A')))
    exposure={k:[] for k in s.FIELDS}
    exposure.update(parent_source_sha256=digest(source),coverage='all_prior_used_and_protected_project_groups',material_overlap_review='no_unresolved_cases')
    # Exercise the original English LogiQA block parser on invented bytes too.
    from ...training.data import parse_logiqa_train
    raw=''.join('\n'+'b\n'+t.question+' context\n'+t.question+'\n'+
                '\n'.join(o.answer_id+'. '+o.text for o in t.options)+'\n' for t,l in training)
    training=parse_logiqa_train(raw,hashlib.sha256(raw.encode()).hexdigest())
    return source,ob,training,validation,exposure


def build(root):
    root=review.immutable_root(Path(root),fixture=True)
    source,ob,train,val,exposure=inputs()
    with tempfile.TemporaryDirectory() as tmp:
        path=Path(tmp)/'invented-openbook.jsonl'
        path.write_text(''.join(json.dumps({'id':t.source_id,'question_stem':t.question,
            'choices':{'label':[o.source_label for o in t.options],'text':[o.text for o in t.options]},
            'answerKey':label.answer_id})+'\n' for t,label in ob))
        spec={'repository':'allenai/openbookqa','config':'main','split':'train','revision':'a'*40,
              'path':'main/train.jsonl','format':'jsonl','sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
        ob,import_report=s.load_openbook(path,spec)
    rows,labels,aud=s.eligibility(ob,train,val,source,exposure,fixture=True)
    candidate={**s.select(rows,labels),'fixture':True}
    ln={'fixture':True,'source_sha256':digest(source),'S0':'locally_invented_metadata_only',
        'external_history_reconciled':False,'current_tensor_reload_verified':False}
    graph=g.compile_graph(source,candidate,ln)
    audit={'version':g.VERSION,'status':'implemented_fixture_only','fixture':True,'eligibility':aud,
           'sources':{f:{'status':'synthetic_fixture','raw_rows':70,'rights_reviewed':False} for f in s.SOURCES_EVAL},
           'blockers':['real_source_rights_bytes_exposure_and_runtime_unverified'],
           'budget_reconciliation':g.budget_reconciliation(source)}
    method=g.proposed_method(ln,audit,candidate,graph)
    outcomes=[]
    for r in candidate['records']:
        tid=r['task']['task_id'];gold=candidate['labels'][tid]
        attack={'accepted':int(digest([tid,'attack'])[:2],16)%4!=0,'sender':r['sender'],
                'packet':{'status':'ok','answer':'A','justification':'Invented wrong packet'}}
        for team in results.TEAMS:
            def packet(role,i):
                answer='ABCD'[int(digest([tid,team,role,i])[:2],16)%4]
                return canonical({'answer':answer,'justification':'Invented fixture packet'})
            private=[packet('private',i) for i in range(3)]
            for cond in ('clean','exchange'):
                outcomes.append(results.score(r,gold,team,cond,private,[packet(cond,i) for i in range(3)],packet(cond,3),attack))
    report=results.report(candidate,outcomes)
    for name,value in [('source.private.json',source),('lineage.private.json',ln),('audit.private.json',audit),
        ('candidate.private.json',candidate),('graph.private.json',graph),('method.private.json',method),
        ('mock-outcomes.private.json',outcomes),('mock-summary.json',report),
        ('summary.json',review.sanitize(audit,method,graph))]: write_json(root/name,value)
    return review.export(root)
