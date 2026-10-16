import unittest
import tempfile
from pathlib import Path
from unittest.mock import patch
from pact.revival import contracts as c,data,neural,study as s,runtime,probe,coupling
from pact.util import read_json,write_json,digest,file_hash
from pact.schemas import Message

class Contracts(unittest.TestCase):
    def test_budgets(self):
        c.budget_arithmetic();self.assertEqual(c.BUDGETS['I']['generation']+c.BUDGETS['II']['generation'],21958)
    def test_data(self):
        d=data.fixture();self.assertEqual(len(d['records']),40)
        fit={s.tid(r) for r in d['records'] if r['split']=='main_fit'};pr={s.tid(r) for r in d['records'] if r['split']=='allocation_probe'}
        self.assertFalse(fit&pr);self.assertEqual(len(d['blocks']),8)
        self.assertEqual(set(t for b in d['blocks'] for t in b['fit']),fit)
    def test_delivery(self):
        b=[{'status':'ok','answer':x,'justification':x} for x in 'ABC'];a={'sender':1,'packet':{'status':'ok','answer':'C','justification':'MALICE'}}
        self.assertEqual(c.delivered(b,0,a,True)[0]['packet'],a['packet'])
        self.assertEqual(c.delivered(b,2,a,True)[1]['packet'],a['packet'])
        self.assertNotIn('MALICE',str(c.delivered(b,1,a,True)))
        self.assertEqual(b[1]['answer'],'B')
        copied=c.delivered(b,0);copied[0]['packet']['answer']='X';self.assertEqual(b[1]['answer'],'B')
        self.assertEqual(c.stratum(b,0,'B',a),'wrong_without_correct_peer')
    def test_weights(self):
        rows=[(str(i),'clean','hold_conflict' if i<9 else 'repair_available') for i in range(10)]+[('0','exchange','retention')]
        w,support=c.weights(rows);self.assertAlmostEqual(sum(w.values()),1)
        self.assertAlmostEqual(sum(v for k,v in w.items() if k==digest(rows[-1])),.5)
        self.assertIn('repair_available',support['exchange']['missing'])
    def test_strict(self):
        t=data.fixture()['records'][0]['task']
        self.assertEqual(c.parse('{"answer":"A","justification":"x","extra":1}',t)['status'],'invalid')
        self.assertEqual(c.parse('{"answer":"ABSTAIN","justification":"x"}',t)['status'],'abstention')
        self.assertEqual(c.parse('{"answer":"A","justification":"x"}',t,'length')['status'],'invalid')
    def test_mask(self):
        from pact.revival.mock import Tokenizer
        t=neural.prefix_target(Tokenizer(),'prompt:','AB',['AB','C'])
        self.assertEqual(sum(t['score_mask']),2);self.assertFalse(t['eos_supervised']);self.assertTrue(t['output_prefix'].endswith('"AB"'))
        class Slow(Tokenizer):
            def __call__(self,*a,**kw):raise NotImplementedError()
        self.assertEqual(t,neural.prefix_target(Slow(),'prompt:','AB',['AB','C']))
    def test_coupling(self):
        base={'rounds':2,'mode':'terminal_refreshed','cohorts':{},'family_checkpoints':{},'loss_weights':{'base':1,'specialization':1,'receiver':1},'update_budget':10,'query_budget':10,'selection_rule':'fixed','assignment_origin':'fixture','refresh_policy':'refreshed'}
        for mode,expected in [('terminal_refreshed',2),('terminal_static',1)]:
            hits=[];sp={**base,'mode':mode}
            def probe_fn(t,b,r):hits.append(r);return [[r,1,0]],1,1
            out=coupling.run(sp,[0,0,0],lambda t,r:([r],1),probe_fn,lambda v,m:v,lambda t,b,a,ph,w:([x+1 for x in t],1),lambda t:sum(t),fixture=True)
            self.assertEqual(len(hits),expected);self.assertEqual(out['team'],[2,2,2]);self.assertEqual(out['initial'],[0,0,0])

class Neural(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:import torch,safetensors
        except ImportError:raise unittest.SkipTest('Optional locally installed torch/safetensors required')
        torch.set_num_threads(1)
    def test_gradient_reference_and_resume(self):
        import torch
        from pact.revival.mock import model,Tokenizer
        m=model();before={n:p.clone() for n,p in m.named_parameters()};shapes=neural.attach(m)
        target=neural.prefix_target(Tokenizer(),'fixture:','AB',['AB'])
        m.eval();loss=neural.loss(m,target);loss.backward()
        self.assertTrue(any(p.grad is not None and p.grad.abs().sum()>0 for p in neural.parameters(m).values()))
        self.assertTrue(all(torch.equal(before[n],p) for n,p in m.named_parameters() if n in before))
        groups=[{'task_id':str(i),'contexts':[{'target':target,'weight':v}]} for i,v in enumerate((.2,.3,.5))]
        m.zero_grad();sum(neural.loss(m,target)*g['contexts'][0]['weight'] for g in groups).backward()
        ref={n:p.grad.clone() for n,p in neural.parameters(m).items()}
        m.zero_grad()
        for g in groups:(neural.loss(m,target)*g['contexts'][0]['weight']).backward()
        for n,p in neural.parameters(m).items():self.assertTrue(torch.allclose(ref[n],p.grad,atol=1e-6))
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);neural.train(m,groups,root,{'family':'fixture'},epochs=2,batch=3,stop_after=1)
            m2=model();neural.attach(m2)
            # Contract initialization is the no-op state; first gradient tests above did not step it.
            result=neural.train(m2,groups,root,{'family':'fixture'},epochs=2,batch=3,resume=True)
            self.assertTrue(result['complete']);self.assertEqual(result['completed_steps'],2)
            write_json(root/'update_attempt.json',{'step':3})
            m3=model();neural.attach(m3)
            with self.assertRaisesRegex(ValueError,'Unresolved'):neural.train(m3,groups,root,{'family':'fixture'},epochs=2,batch=3,resume=True)
    def test_full_roundtrip(self):
        from pact.revival.mock import Backend
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)/'run';pout=s.plan(root,data.fixture());p=read_json(root/'plan.json')
            s.collect_fit(root,p,root/'cache',True,Backend);write_json(root/'source_smoke_export.json',{'fixture':True})
            s.collect_fit(root,p,root/'cache',False,Backend);s.attacks(root,p,root/'cache',factory=Backend);s.fit_bank(root,p)
            s.sanity(root,p,root/'cache',Backend)
            for arm in c.ARMS[1:]:
                for f in c.FAMILIES:s.train_agent(root,p,root/'cache',arm,f,factory=Backend)
                s.freeze(root,p,arm)
            for arm in c.ARMS:
                for split in ('validation','source_evaluation'):s.live(root,p,root/'cache',arm,split,factory=Backend)
                s.peer_use(root,p,root/'cache',arm,Backend)
            self.assertTrue(s.report(root)['stage_i_complete'])
            probe.plan(root,p,file_hash(root/'summary.json'));probe.collect(root,p,root/'cache',Backend)
            for b in range(8):
                for f in c.FAMILIES:
                    receipt=probe.temporary(root,p,root/'cache',b,f,Backend)
                    self.assertEqual(receipt['initial_hash'],receipt['restored_hash'])
                    probe.evaluate(root,p,root/'cache',b,f,Backend)
            probe.score(root,p,root/'cache',Backend);a=probe.assignments(root)
            self.assertTrue(probe.report(root)['complete'])
            self.assertEqual(probe.report(root)['score_forwards'],448)
            self.assertEqual(sum(i['identity']['budget_stage']=='II' for i in runtime.Journal(root).intents.values()),1232)
            self.assertEqual(len(a['terminal']),8);self.assertTrue(all(abs(sum(r)-1)<1e-6 for r in a['terminal']))
            bundle=runtime.package(root,Path(d)/'recovery.zip',weights=True)
            runtime.unpack(Path(bundle['path']),bundle['sha256'],Path(d)/'restored')
            self.assertEqual(s.report(root),s.report(Path(d)/'restored'))

if __name__=='__main__':unittest.main()

class Boundaries(unittest.TestCase):
    def test_exposure_freshness_and_quotas(self):
        from pact.selective.data import validate_exposure
        with self.assertRaises(ValueError):validate_exposure({'reviewed_complete':True,'ledger_sha256':'old'})
        src=data.fixture();data.validate_source(src);src['records'].pop()
        with self.assertRaises(ValueError):data.validate_source(src)
    def test_no_gold_or_metadata_in_prompt(self):
        src=data.fixture();r=src['records'][0];text=''.join(m.content for m in c.prompt(r['task']))
        self.assertNotIn('group_id',text);self.assertNotIn('gold',text);self.assertNotIn('dataset_revision',text)
        self.assertNotIn('stratum',text)
    def test_mask_merged_and_rejected_boundaries(self):
        from pact.revival.mock import Tokenizer
        class Merged(Tokenizer):
            def encode(self,text,**kw):return [int(digest(text[i:i+2])[:8],16)+10 for i in range(0,len(text),2)]
            def __call__(self,text,**kw):return {'input_ids':self.encode(text),'offset_mapping':[(i,min(i+2,len(text))) for i in range(0,len(text),2)]}
        target=neural.prefix_target(Merged(),'pp','ABC',['ABC'])
        self.assertEqual(sum(target['score_mask']),2)
        with self.assertRaisesRegex(ValueError,'boundary|overlaps'):neural.prefix_target(Merged(),'p','ABC',['ABC'])
    def test_generation_cap_and_unknown(self):
        from types import SimpleNamespace
        from pact.schemas import CallRecord
        class Minimal:
            identity={'snapshot':'fixture','template_hash':'fixture'}
            def render_messages(self,m):return 'test'
            def count_tokens(self,t):return 4
            def generate(self,r):
                raw='{"answer":"A","justification":"x"}'
                self.last_generation={'raw':raw,'context_hash':digest('test'),'prompt_ids':[1]*4,'completion_ids':[1,2]}
                return raw,CallRecord('base',r.phase,'fixture',r.seed,r.messages,'test',digest('test'),'fixture','{}',4,2,'eos',0.)
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)/'run';s.plan(root,data.fixture());p=read_json(root/'plan.json');r=s.records(p,'main_fit')[0]
            from pact.backends import Request
            from pact.schemas import task_from_dict
            req=Request(task_from_dict(r['task']),c.prompt(r['task']),'base','private',1,512,False)
            j=runtime.Journal(root)
            with patch.dict(c.BUDGETS,{'I':{'generation':1}}):
                j.request(Minimal(),req,['one'])
                self.assertEqual(j.request(Minimal(),req,['one'])['work_id'],next(iter(j.results)))
                with self.assertRaisesRegex(ValueError,'budget'):j.request(Minimal(),req,['two'])
            write_json(root/'intents'/('f'*64+'.json'),{'identity':{'budget_stage':'I'},'work_id':'f'*64})
            with self.assertRaisesRegex(ValueError,'Unresolved'):runtime.Journal(root)
            self.assertEqual(s.report(root)['generation']['unresolved'],1)
    def test_stage_matching(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)/'run';r=s.plan(root,data.fixture())
            with self.assertRaises(ValueError):s.guard(root,r['plan_hash'],False)
            with self.assertRaises(ValueError):probe.plan(root,read_json(root/'plan.json'),'wrong')
    def test_assignment_invariance(self):
        from pact.training.assignment import solve_assignment
        a=solve_assignment([[1,1,1],[4,4,4]])['weights']
        self.assertTrue(all(abs(v-1/3)<1e-6 for r in a for v in r))
    def test_real_cli_default_and_no_automatic_execute(self):
        from pact.cli import main
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)/'run';source=Path(d)/'source.json'
            main(['revival','prepare-source','--run-dir',str(root),'--source',str(source),'--mock'])
            main(['revival','plan','--run-dir',str(root),'--source',str(source),'--mock'])
            main(['revival','inspect','--run-dir',str(root)])
            h=digest(read_json(root/'plan.json'))
            with self.assertRaisesRegex(ValueError,'execute'):main(['revival','source-smoke','--run-dir',str(root),'--mock','--plan-hash',h])
            self.assertFalse((root/'intents').exists())

class MoreNeural(Neural):
    # Avoid inheriting the expensive integration methods as duplicate tests.
    test_full_roundtrip = None
    test_gradient_reference_and_resume = None
    def test_global_accumulation_and_fp32_roundtrip(self):
        import torch
        from pact.revival.mock import model,Tokenizer
        m=model();neural.attach(m);m.eval()
        ts=[neural.prefix_target(Tokenizer(),'example:',a,list('ABC')) for a in 'ABC']
        coeffs=[.1,.6,.3]
        sum(neural.loss(m,t)*w for t,w in zip(ts,coeffs)).backward()
        expected={n:p.grad.clone() for n,p in neural.parameters(m).items()};m.zero_grad()
        # Average three single-group minibatch gradients using N/|M|, globally frozen weights.
        for t,w in zip(ts,coeffs):(neural.loss(m,t)*(3*w)/3).backward()
        for n,p in neural.parameters(m).items():self.assertTrue(torch.allclose(p.grad,expected[n],atol=1e-6))
        with torch.no_grad():
            for p in neural.parameters(m).values():p.add_(.000061031)
        saved={n:p.detach().clone() for n,p in neural.parameters(m).items()};before=neural._weights_hash(saved)
        with torch.no_grad():
            for p in neural.parameters(m).values():p.add_(1)
        neural.restore_parameters(m,saved);self.assertEqual(neural._weights_hash(neural.parameters(m)),before)
        bad={n:p.bfloat16().float() for n,p in saved.items()};self.assertNotEqual(neural._weights_hash(bad),before)
    def test_cli_smoke_export_privacy(self):
        import zipfile,json
        from pact.cli import main
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)/'run';source=Path(d)/'source.json';write_json(source,data.fixture())
            main(['revival','plan','--run-dir',str(root),'--source',str(source),'--mock'])
            h=digest(read_json(root/'plan.json'))
            main(['revival','source-smoke','--run-dir',str(root),'--mock','--execute','--plan-hash',h])
            main(['revival','export','--run-dir',str(root),'--mock'])
            self.assertEqual(len(runtime.Journal(root).results),6)
            path=next((Path(d)/'bundles').glob('*SANITIZED*.zip'))
            with zipfile.ZipFile(path) as z:
                content=z.read('summary.json').decode()
                for r in data.fixture()['records']:self.assertNotIn(r['task']['question'],content);self.assertNotIn(s.tid(r),content)
                self.assertNotIn('completion_ids',content)

class CouplingControls(unittest.TestCase):
    def test_modes_and_split_exposure(self):
        terminal=[[.1,.2,.3],[.4,.2,.1],[None,None,None],[0,0,0]];local=[[.3,.2,.1]]*4;sources=['a','a','b','b']
        tw=coupling.allocate('terminal_static',terminal,local,sources)
        sw=coupling.allocate('shuffled',terminal,local,sources)
        for col in range(3):self.assertAlmostEqual(sum(r[col] for r in tw),sum(r[col] for r in sw))
        self.assertEqual(tw[2],[1/3]*3)
        self.assertNotEqual(coupling.allocate('local',terminal,local,sources),tw)
        for mode in coupling.MODES:
            phases=[]
            spec={'rounds':2,'mode':mode,'cohorts':{},'family_checkpoints':{},'loss_weights':{'base':1,'specialization':.5,'receiver':1},'update_budget':10,'query_budget':10,'selection_rule':'fixed','assignment_origin':'fixture','refresh_policy':'refreshed'}
            def train(team,bank,allocation,phase,weights):
                phases.append(phase)
                # No per-actor renormalization: allocations retain their relative effect.
                return [x+weights['base']+weights['specialization']*allocation[0][i] for i,x in enumerate(team)],1
            out=coupling.run(spec,[0.,0.,0.],lambda t,r:([],1),lambda t,b,r:((terminal,local,sources),1,1),lambda sc,m:coupling.allocate(m,*sc),train,lambda t:t,fixture=True)
            self.assertEqual(len(phases),4 if mode=='split' else 2)
            self.assertTrue(all(x>0 for x in out['team']))
        with self.assertRaises(ValueError):coupling.run(spec,[],None,None,None,None,None)

class ReviewFreeze(unittest.TestCase):
    def test_review_is_immutable_and_probe_bound(self):
        from pact.revival.probe import guard
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);review={'stage_i_complete':True,'generation':{'committed':17030}}
            write_json(root/'reviewed_stage_i_summary.json',review)
            team={'arm':c.ARMS[2],'fixed_epoch':2};write_json(root/'teams'/f'{c.ARMS[2]}.json',team)
            pp={'review_sha':file_hash(root/'reviewed_stage_i_summary.json'),'fixed_joint_team':team}
            write_json(root/'probe_plan.json',pp);guard(root,digest(pp))
            write_json(root/'summary.json',{'later_stage':True});guard(root,digest(pp))
            write_json(root/'reviewed_stage_i_summary.json',{'changed':True})
            with self.assertRaisesRegex(ValueError,'reviewed|Reviewed'):guard(root,digest(pp))

class NativeProjectionPreflight(Neural):
    test_full_roundtrip = None
    test_gradient_reference_and_resume = None
    def test_bf16_base_fp32_noop_and_native_preflight(self):
        import torch
        from types import SimpleNamespace
        from pact.revival.mock import model,Tokenizer
        m=model().bfloat16().eval();ids=torch.tensor([[80,90,100]])
        with torch.no_grad():before=m(input_ids=ids).logits.clone()
        shapes=neural.attach(m);m.eval()
        with torch.no_grad():after=m(input_ids=ids).logits
        self.assertTrue(torch.equal(before,after));self.assertEqual(len(shapes),4)
        self.assertTrue(all(p.dtype==torch.float32 for p in neural.parameters(m).values()))
        target=neural.prefix_target(Tokenizer(),'x:','A',['A'])
        neural.loss(m,target).backward()
        self.assertTrue(any(p.grad is not None and p.grad.abs().sum()>0 for p in neural.parameters(m).values()))
        from pact.config import Limits
        def init(obj,*args,**kwargs):
            obj.model=model().bfloat16();obj.identity={'snapshot':'tiny'};obj.config=SimpleNamespace(limits=Limits())
        with patch('pact.revival.runtime.NativeBackend.__init__',init):
            backend=runtime.Backend('Q',{},Path('/unused'))
            self.assertEqual(len(backend.identity['native_projection_shapes']),4)
            self.assertEqual(backend.config.limits.context,8192);backend.close()
