"""Real deterministic CPU multinomial learning. No GPU imports or model access."""
import math
from collections import Counter
from .contracts import ARMS, GRID, feature_spec, validate_features
from ..util import digest


def transition(anchor,peer,gold):return int(peer.status=='ok' and peer.answer==gold)-int(anchor.status=='ok' and anchor.answer==gold)


def encode(features,metadata=False):
    spec=validate_features(features,metadata);out=[]
    for k in spec['numeric']:
        v=features[k]
        if type(v) not in (int,float) or not math.isfinite(v):raise ValueError('Invalid numeric feature')
        out.append(float(v))
    for k,values in spec['categorical'].items():
        v=features[k] if features[k] in values else 'UNKNOWN'
        out.extend(float(v==c) for c in values)
    return out


def fit_rows(tasks,arm):
    """Tasks with no alternatives retain their share of N_fit in the loss."""
    if arm not in ARMS or any(t['split']!='fit' or t.get('training_allowed') is not True for t in tasks):raise ValueError('Fit-only source groups required')
    if len({t['group_id'] for t in tasks})!=len(tasks):raise ValueError('Repeated fit group')
    rows=[];weights=[];support=[]
    for t in tasks:
        views=t['views'];clean=views['clean'];attacks=[v for k,v in views.items() if k!='clean']
        chosen=[(clean,1.)] if arm.endswith('_clean') or not attacks else [(clean,.5)]+[(v,.5/len(attacks)) for v in attacks]
        for view,w in chosen:
            if [(r['candidate_id'],r['answer'],r['target']) for r in view]!=[(r['candidate_id'],r['answer'],r['target']) for r in clean]:raise ValueError('All original alternative identities and targets required in every view')
            for r in view:
                if r['target'] not in (-1,0,1):raise ValueError('Unknown transition target')
                rows.append(r);weights.append(w/len(tasks)/len(clean))
        support.append({'group_id':t['group_id'],'alternatives':len(clean),'accepted_attacks':len(attacks),'clean_weight':chosen[0][1],
                        'clean_only_reason':'no_accepted_applicable_attack' if not attacks else None})
    return rows,weights,support


def objective(theta,X,y,weights,l2=.001):
    import numpy as np
    d=X.shape[1];W=theta[:3*d].reshape(3,d);a=theta[3*d:];z=X@W.T+a
    z-=z.max(axis=1,keepdims=True);p=np.exp(z);p/=p.sum(axis=1,keepdims=True)
    # log-sum-exp, not clipped probabilities, for matching analytic gradients.
    logp=z-np.log(np.exp(z).sum(axis=1,keepdims=True))
    loss=-np.sum(weights*logp[np.arange(len(y)),y])+.5*l2*np.sum(W*W)
    g=p.copy();g[np.arange(len(y)),y]-=1;g*=weights[:,None]
    gradient=np.r_[(g.T@X+l2*W).ravel(),g.sum(axis=0)]
    return float(loss),gradient


def optimize(X,y,weights,max_iterations=500):
    """Deterministic full BFGS with Armijo search, zero start, fixed tolerance."""
    import numpy as np
    if not 1<=max_iterations<=500:raise ValueError('Solver iteration cap')
    theta=np.zeros(3*(X.shape[1]+1));H=np.eye(len(theta));loss,g=objective(theta,X,y,weights)
    for iteration in range(max_iterations+1):
        norm=float(np.max(np.abs(g)))
        if not np.isfinite(loss) or not np.all(np.isfinite(g)):raise ArithmeticError('Nonfinite gate optimization')
        if norm<=1e-6:return theta,{'converged':True,'iterations':iteration,'loss':loss,'gradient_inf':norm,'optimizer':'BFGS/Armijo','tolerance':1e-6}
        if iteration==max_iterations:break
        direction=-H@g
        if float(g@direction)>=0:direction=-g;H=np.eye(len(theta))
        step=1.
        for _ in range(50):
            new=theta+step*direction;value,ng=objective(new,X,y,weights)
            if np.isfinite(value) and value<=loss+1e-4*step*float(g@direction):break
            step*=.5
        else:raise ArithmeticError('Gate line search failed')
        s=new-theta;v=ng-g;sv=float(s@v)
        if sv>1e-12:
            rho=1/sv;I=np.eye(len(theta));H=(I-rho*np.outer(s,v))@H@(I-rho*np.outer(v,s))+rho*np.outer(s,s)
        else:H=np.eye(len(theta))
        theta,loss,g=new,value,ng
    raise ArithmeticError(f'Gate did not converge within {max_iterations} iterations')


def fit(tasks,arm):
    import numpy as np
    rows,weights,support=fit_rows(tasks,arm);metadata=arm=='metadata_augmented';spec=feature_spec(metadata)
    layout='metadata' if metadata else 'restricted' if arm.startswith('restricted') else 'full'
    encoded=[encode(r[layout],metadata) for r in rows];labels=[r['target']+1 for r in rows]
    d=len(encode({**{k:0 for k in spec['numeric']},**{k:'UNKNOWN' for k in spec['categorical']}},metadata))
    w=np.asarray(weights);X=np.asarray(encoded).reshape(-1,d);means=np.zeros(d);scales=np.ones(d);nnum=len(spec['numeric'])
    if len(rows):
        means[:nnum]=np.average(X[:,:nnum],axis=0,weights=w)
        var=np.average((X[:,:nnum]-means[:nnum])**2,axis=0,weights=w);scales[:nnum]=np.where(var>1e-12,np.sqrt(var),1.)
    X=(X-means)/scales
    count=Counter(labels);reason='no_empirical_rescue_training_support' if not count.get(2) else 'single_class_fit' if len(count)<2 else None
    if reason:theta=np.zeros(3*(d+1));diagnostics={'converged':True,'iterations':0,'status':reason,'trained':False}
    else:theta,diagnostics=optimize(X,np.asarray(labels),w);diagnostics.update(status='cpu_fit_complete',trained=True)
    model={'arm':arm,'class_order':['harm','neutral','improve'],'l2':.001,'feature_spec':spec,'mean':means.tolist(),'scale':scales.tolist(),
           'coefficients':theta[:3*d].reshape(3,d).tolist(),'intercept':theta[3*d:].tolist(),'keep_only':reason is not None,
           'diagnostics':diagnostics,'class_rows':{str(k-1):v for k,v in count.items()},'fit_groups':len(tasks),
           'fit_hash':digest(tasks),'weights':weights,'weight_support':support,'transform_policy':'fit-only task/view/alternative weights normalized over observed rows'}
    model['clean_candidate_classes']=dict(Counter(str(r['target']) for t in tasks for r in t['views']['clean']))
    model['task_class_support']={str(k):sum(any(r['target']==k for r in t['views']['clean']) for t in tasks) for k in (-1,0,1)}
    model['model_hash']=digest(model);return model


def validate_model(m):
    if m.get('diagnostic_only') or m.get('policy_selection_authorized') is False:
        raise ValueError('Diagnostic artifacts are not deployable gate models')
    if digest({k:v for k,v in m.items() if k!='model_hash'})!=m['model_hash']:raise ValueError('Gate changed')
    if m['arm'] not in ARMS or m['feature_spec']!=feature_spec(m['arm']=='metadata_augmented'):raise ValueError('Gate feature contract changed')


def probability(m,features):
    import numpy as np
    validate_model(m);x=(np.array(encode(features,m['arm']=='metadata_augmented'))-m['mean'])/m['scale']
    z=np.array(m['coefficients'])@x+m['intercept'];p=np.exp(z-z.max());p/=p.sum()
    if not np.all(np.isfinite(p)):raise ArithmeticError('Invalid probabilities')
    return p.tolist()


def decide(m,rows,anchor,tau):
    validate_model(m)
    if tau not in GRID:raise ValueError('Unplanned threshold')
    if m['keep_only'] or tau=='KEEP_ONLY':return {'action':'KEEP','selected_id':'anchor','answer':anchor.answer,'status':anchor.status,'raw':anchor.raw,'fallback_reason':'KEEP_ONLY'}
    layout='metadata' if m['arm']=='metadata_augmented' else 'restricted' if m['arm'].startswith('restricted') else 'full'
    scores=[]
    for row in rows:
        if layout!='metadata' and not row['enabled'][layout]:continue
        p=probability(m,row[layout]);scores.append((p[2]-2*p[0],row['candidate_id'],row['answer']))
    eligible=[x for x in scores if x[0]>tau]
    if not eligible:return {'action':'KEEP','selected_id':'anchor','answer':anchor.answer,'status':anchor.status,'raw':anchor.raw,'fallback_reason':'no_usable_score_above_threshold'}
    u,c,a=sorted(eligible,key=lambda x:(-x[0],x[1]))[0]
    row=next(r for r in rows if r['candidate_id']==c)
    return {'action':'SWITCH','selected_id':c,'answer':a,'status':'ok','raw':row['raw'],'score':u,'fallback_reason':None}


def tune(model,tasks):
    from .contracts import Answer
    if not tasks or any(t['split']!='threshold_tuning' or t.get('training_allowed') is not False for t in tasks):raise ValueError('Tuning split only')
    if len({t['group_id'] for t in tasks})!=len(tasks):raise ValueError('Duplicate tuning group')
    curves=[]
    for tau in GRID:
        clean_harm=pool_harm=net=joint=switches=0;complete=0;missing=0
        for t in tasks:
            a=Answer(**t['anchor']);T=a.status=='ok' and a.answer==t['gold'];out={v:decide(model,rs,a,tau) for v,rs in t['views'].items()}
            Y={v:r['status']=='ok' and r['answer']==t['gold'] for v,r in out.items()}
            clean_harm+=int(T and not Y['clean']);pool_harm+=int(T and not all(Y.values()));net+=int(Y['clean'])-int(T)
            joint+=int(all(Y.values()));switches+=int(any(r['action']=='SWITCH' for r in out.values()))
            missing+=t.get('missing_variants',0);complete+=int(t.get('missing_variants',0)==0)
        n=len(tasks);curves.append({'threshold':tau,'clean_harm':clean_harm,'pool_harm':pool_harm,'denominator':n,'clean_net':net,'joint_success':joint,
            'switched_tasks':switches,'eligible':clean_harm/n<=.05 and pool_harm/n<=.05,'complete_pool_tasks':complete,
            'missing_variants':missing,'unobserved_pool_harm_upper':min(n,pool_harm+sum(t.get('missing_variants',0)>0 for t in tasks)),
            'joint_success_lower':max(0,joint-sum(t.get('missing_variants',0)>0 for t in tasks))})
    valid=[c for c in curves if c['eligible']]
    best=max(valid,key=lambda c:(c['clean_net'],c['joint_success'],-c['switched_tasks'],GRID.index(c['threshold'])))
    return {'model_hash':model['model_hash'],'tuning_hash':digest(tasks),'threshold':best['threshold'],'curves':curves,
            'formal_risk_certificate':False,'screen':'empirical 5% harm on tuning tasks; not a risk guarantee','one_task_rate':1/len(tasks)}
