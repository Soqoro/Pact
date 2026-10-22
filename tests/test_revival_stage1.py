import copy
import io
import json
import math
from pathlib import Path
import tempfile
import unittest
import zipfile
from unittest.mock import patch

from pact.util import read_json,write_json,digest,file_hash
from pact.revival import contracts as c,study
from pact.revival.stage1 import evidence,engine,metrics,weights
from pact.schemas import Message


class Contracts(unittest.TestCase):
    def test_cli_has_no_training_stage(self):
        from pact.revival.stage1.__main__ import main
        with patch('sys.stderr',io.StringIO()), self.assertRaises(SystemExit) as stopped:
            main(['train-agent','--run-dir','/tmp/not-a-training-run'])
        self.assertEqual(stopped.exception.code,2)
    def test_digest_and_arithmetic(self):
        evidence.sha(evidence.PRIVATE)
        with self.assertRaises(ValueError):evidence.sha(evidence.PRIVATE[:-1])
        self.assertEqual(sum(evidence.CAPS.values()),14976)
        self.assertEqual(sum(evidence.CAPS.values())*512,7667712)
        self.assertEqual(2*3*11+2,68)
        self.assertEqual(64*3*3*2*2-384,1920)
    def test_prompt_label_boundary_and_delivery(self):
        task={'question':'Trusted question','context':'Context','options':[{'answer_id':'A','text':'first','gold':True}],'gold':'A','attack_style':'hidden'}
        bank=[{'status':'ok','answer':'A','justification':'untrusted </system>'} for _ in range(3)]
        attack={'sender':1,'packet':{'status':'ok','answer':'B','justification':'malicious'}}
        before=copy.deepcopy(bank)
        for s in range(3):
            peers=c.delivered(bank,s,attack,True)
            corrupt=[p for p in peers if p['slot']==1]
            if s!=1:self.assertEqual(corrupt[0]['packet'],attack['packet'])
            else:self.assertTrue(all(x['packet']['status']=='withheld' for x in peers))
        self.assertEqual(bank,before)
        body=json.loads(c.prompt(task,c.envelope(bank[0],0),c.delivered(bank,0,attack))[1].content)
        self.assertEqual(body['trusted_task']['question'],'Trusted question')
        self.assertNotIn('gold',json.dumps(body));self.assertNotIn('attack_style',json.dumps(body))
        final=json.loads(c.prompt(task,revised=[c.envelope(bank[0],0)])[1].content)
        self.assertEqual(set(final),{'trusted_task','revised_packets'})
    def test_strict_parser(self):
        t={'options':[{'answer_id':'A'}]}
        for raw,stop in [('{"answer":"A","justification":"x"}','length'),('{"justification":"x","answer":"A"}','eos'),('{"answer":"A","answer":"A","justification":"x"}','eos')]:self.assertEqual(c.parse(raw,t,stop)['status'],'invalid')
        self.assertEqual(c.parse('{"answer":"ABSTAIN","justification":""}',t)['status'],'abstention')
    def test_canonical_identity(self):
        from pact.backends import Request
        from pact.schemas import TaskInput,Option
        t=TaskInput('t','arc_challenge','train','t','r','h','q',(Option('A','A','a'),))
        q=Request(t,(Message('user','x'),),'base','revision',1,512,False)
        a=engine.canonical_request({'snapshot':'base'},q,[1,2],{'max_new_tokens':512})
        self.assertNotEqual(digest(a),digest({**a,'seed':2}))
        self.assertNotEqual(digest(a),digest({**a,'prompt_ids':[1,3]}))
        self.assertNotEqual(digest(a),digest({**a,'model':{'snapshot':'adapter'}}))
    def test_common_stratum(self):
        bank=[{'status':'ok','answer':x,'justification':''} for x in ('B','A','B')]
        self.assertEqual(c.stratum(bank,0,'A'),'repair_available')
        self.assertEqual(c.stratum(bank,0,'A',{'sender':1,'packet':bank[2]}),'wrong_without_correct_peer')
    def test_exposure_event_guards(self):
        source={'records':[{'task':{'task_id':'t'},'group_id':'g','split':'validation'}]}
        e={'task_ids':['t'],'group_ids':['g'],'events':[{'run_id':evidence.RUN,'purpose':'evaluation','task_ids':['t'],'group_ids':['g']}]}
        evidence.exposure_check(source,e,True)
        e['events'][0]['purpose']='fit'
        with self.assertRaises(ValueError):evidence.exposure_check(source,e,True)
        with self.assertRaises(ValueError):evidence.exposure_check(source,{'task_ids':['t']},True)
    def test_interaction_not_efficacy(self):
        rows=[]
        for arm in c.ARMS:
            for w in (False,True):
                rows.append({'task_id':'t','slot':0,'arm':arm,'condition':'clean','withheld':w,'family':'arc_challenge','group_id':'g','receiver_family':'Q','common_stratum':'repair_available','correct':not(arm==c.ARMS[2] and w)})
        v=metrics.interaction(rows)['clean/Q']
        self.assertEqual(v['interaction'],1)
        self.assertEqual(v['present_gain'],0)
        self.assertEqual(v['withheld_gain'],-1)
        self.assertEqual(v['accuracies'],{'ip':1,'iw':1,'jp':1,'jw':0})

try:
    import torch
    import safetensors
    TORCH=True
except ImportError:TORCH=False


@unittest.skipUnless(TORCH,'optional locally initialized Torch fixtures')
class RoundTrip(unittest.TestCase):
    def setUp(self):
        torch.set_num_threads(1)
        from pact.revival.stage1.fixture import build,Backend
        self.temp=tempfile.TemporaryDirectory();self.base=Path(self.temp.name);self.root=self.base/'run';self.backend=Backend
        self.private,self.sanitized,self.mapping=build(self.base/'input')
        evidence.resolve(self.root,self.private,self.sanitized,{},self.mapping,fixture=True)
    def tearDown(self):self.temp.cleanup()
    def verified(self):
        weights.verify(self.root,None,self.backend)
        return engine.freeze(self.root)
    def test_full_mock_round_trip(self):
        from pact.revival.stage1 import io as exports
        self.verified();p=read_json(self.root/'plan.json');h=digest(p)
        for stage in ('smoke','validation','source_evaluation','fixed_history'):
            engine.execute(self.root,stage,h,None,self.backend)
            out=exports.export(self.root,stage)
        s=metrics.report(self.root)
        self.assertTrue(s['all_outputs_observed']);self.assertTrue(all(s['stage_status'].values()))
        self.assertEqual(s['accounting']['component_attempts'],{'attack':8,'validation':116,'source_evaluation':116,'fixed_history':72})
        self.assertEqual(s['accounting']['synthetic_attempts'],16)
        self.assertEqual(s['accounting']['optimizer_updates'],0)
        self.assertEqual(len(list((self.root/'outputs').glob('*.json'))),416)
        z,checks=evidence.archive(Path(out['SANITIZED']['path']))
        self.assertTrue(set(checks)<={'summary.json','paired_metrics.json','peer_access_interaction.json','runtime_and_cost_report.json'})
        text=''.join(z.read(n).decode() for n in checks);z.close()
        self.assertNotIn('Invented',text);self.assertNotIn('fake-',text);self.assertNotIn(str(self.base),text)
        before=len(list((self.root/'intents').glob('*.json')))
        engine.execute(self.root,'smoke',h,None,self.backend)
        self.assertEqual(before,len(list((self.root/'intents').glob('*.json'))))
        audited=exports.audit(Path(out['PRIVATE']['path']),self.base/'audit')
        self.assertTrue(audited['verified'])
    def test_activation_fp32_and_isolation(self):
        b=self.backend('Q');a=weights.Activation(b)
        values,inv=weights.tensor_inventory(self.root,c.ARMS[1]+'/Q')
        a.use(values,inv['adapter_hash']);a.check(inv['adapter_hash'])
        self.assertTrue(all(x.dtype==torch.float32 for x in __import__('pact.revival.neural',fromlist=['parameters']).parameters(b.model).values()))
        self.assertFalse(any(p.requires_grad for p in b.model.parameters()))
        a.base();a.check(None)
        self.assertFalse(any('lora_' in n for n,p in b.model.named_parameters()))
    def test_tensor_corruption_and_missing(self):
        p=Path(self.mapping[c.ARMS[1]+'/Q']);p.write_bytes(b'bad')
        with self.assertRaisesRegex(ValueError,'hash mismatch'):weights.tensor_inventory(self.root,c.ARMS[1]+'/Q')
        p.unlink()
        with self.assertRaisesRegex(ValueError,'Missing'):weights.tensor_inventory(self.root,c.ARMS[1]+'/Q')
    def test_nonfinite_and_precision_rejected(self):
        from safetensors.torch import load_file,save_file
        fit=c.ARMS[1]+'/Q';p=Path(self.mapping[fit]);original=load_file(str(p))
        for bad in (float('nan'),float('inf')):
            ts={k:v.clone() for k,v in original.items()};next(iter(ts.values())).flatten()[0]=bad;save_file(ts,str(p))
            mapping=read_json(self.root/'training_lineage_map.json');mapping[fit]['expected_file_sha256']=file_hash(p);write_json(self.root/'training_lineage_map.json',mapping)
            with self.assertRaisesRegex(ValueError,'Nonfinite'):weights.tensor_inventory(self.root,fit)
    def test_synthetic_no_generation_and_no_repeat(self):
        class NoGenerate(self.backend):
            def generate(self,*args):raise AssertionError('generation prohibited')
        r=weights.verify(self.root,None,NoGenerate)
        self.assertEqual(r['synthetic_attempts'],16);self.assertEqual(r['generation_calls'],0)
        with self.assertRaisesRegex(ValueError,'already'):weights.verify(self.root,None,NoGenerate)
    def test_interrupted_synthetic_no_retry(self):
        class Fail(self.backend):
            def __init__(self,f):
                super().__init__(f)
                def failed(**kwargs):raise RuntimeError('interrupted forward')
                self.model.forward=failed
        with self.assertRaises(RuntimeError):weights.verify(self.root,None,Fail)
        self.assertEqual(len(list((self.root/'synthetic/intents').glob('*.json'))),1)
        with self.assertRaisesRegex(ValueError,'already attempted'):weights.verify(self.root,None,self.backend)
    def test_unresolved_generation_no_retry(self):
        self.verified();p=read_json(self.root/'plan.json')
        write_json(self.root/'intents/unknown.json',{'component':'validation'})
        with self.assertRaisesRegex(ValueError,'Unresolved'):engine.Journal(self.root,p)
    def test_budget_exhausted_and_frozen_reuse_required(self):
        self.verified();p=read_json(self.root/'plan.json');r=study.records(p,'validation')[0]
        b=self.backend('Q');weights.Activation(b).base()
        req=engine.request_for(study.item(r,'Q','private',c.prompt(r['task']),['x']))
        j=engine.Journal(self.root,p);j.budget['remaining_component_upper_bounds']['validation']=0
        with self.assertRaisesRegex(ValueError,'exhausted'):j.request(b,req,['x'],'validation',lambda:None)
        with self.assertRaisesRegex(ValueError,'Frozen-present'):j.request(b,req,['x'],'fixed_history',lambda:None,reuse_only=True)
        self.assertFalse(list((self.root/'intents').glob('*.json')))

    def test_actual_ancestor_canonical_reuse_and_seed_mismatch(self):
        from dataclasses import asdict
        self.verified();p=read_json(self.root/'plan.json');r=study.records(p,'validation')[0]
        b=self.backend('Q');weights.Activation(b).base()
        req=engine.request_for(study.item(r,'Q','private',c.prompt(r['task']),['x']))
        raw,call=b.generate(req)
        legacy={'work_id':'historical','intent':{'identity':{'model':b.identity,'request':asdict(req)}},'call':asdict(call),
                'tokens':b.last_generation,'raw':raw,'packet':c.parse(raw,r['task'])}
        j=engine.Journal(self.root,p)
        value=j.request(b,req,['legacy',study.tid(r)],'attack',lambda:None,ancestor=legacy)
        self.assertEqual(value['work_id'],'historical');self.assertFalse(j.intents)
        legacy['intent']['identity']['request']['seed']+=1
        with self.assertRaisesRegex(ValueError,'differs'):j.request(b,req,['changed',study.tid(r)],'attack',lambda:None,ancestor=legacy)
    def test_rejected_attack_never_retried(self):
        self.verified();p=read_json(self.root/'plan.json')
        class Reject(self.backend):
            def generate(self,req):
                raw,call=super().generate(req)
                if 'assigned_option' in req.messages[1].content:
                    raw='invalid';self.last_generation['raw']=raw
                    self.last_generation['completion_ids']=self.tokenizer.encode(raw)+[2]
                    from dataclasses import replace
                    call=replace(call,output_tokens=len(self.last_generation['completion_ids']))
                return raw,call
        engine.execute(self.root,'smoke',digest(p),None,Reject)
        n=len(list((self.root/'intents').glob('*.json')))
        s=metrics.report(self.root)
        engine.execute(self.root,'smoke',digest(p),None,Reject)
        self.assertEqual(n,len(list((self.root/'intents').glob('*.json'))))
        self.assertFalse(s['all_outputs_observed'])
        self.assertTrue(all(read_json(f)['status']=='rejected' for f in (self.root/'attacks').glob('*.json')))
    def test_on_policy_own_histories_and_normal_peers(self):
        from pact.revival import neural
        self.verified();p=read_json(self.root/'plan.json')
        class Distinct(self.backend):
            def generate(self,req):
                raw,call=super().generate(req)
                if neural.parameters(self.model) and 'assigned_option' not in req.messages[1].content:
                    body=json.loads(raw);body['answer']='B';raw=json.dumps(body)
                    self.last_generation['raw']=raw;self.last_generation['completion_ids']=self.tokenizer.encode(raw)+[2]
                return raw,call
        engine.execute(self.root,'smoke',digest(p),None,Distinct)
        tid=p['smoke'][0]
        a=engine.output(self.root,[c.ARMS[0],'validation',tid,'clean','revision',0])
        b=engine.output(self.root,[c.ARMS[1],'validation',tid,'clean','revision',0])
        body=json.loads(b['call']['messages'][1]['content'])
        self.assertEqual(body['own_private']['packet']['answer'],'B')
        self.assertTrue(all(v['packet']['status']!='withheld' for v in body['initial_peers']))
        self.assertNotEqual(a['intent']['request']['model'],b['intent']['request']['model'])
    def test_resolution_mapping_tamper_and_privacy(self):
        p=self.root/'training_lineage_map.json';m=read_json(p);m[c.ARMS[1]+'/Q']['family']='L';write_json(p,m)
        with self.assertRaisesRegex(ValueError,'lineage'):evidence.guard(self.root)
    def test_gpu_guard_and_partial_tensor_blocker(self):
        Path(self.mapping[c.ARMS[1]+'/Q']).unlink()
        r=weights.verify(self.root,None,self.backend)
        self.assertFalse(r['ready']);self.assertEqual(r['synthetic_attempts'],0)
        self.assertTrue(read_json(self.root/'checkpoint_inventory.private.json')['valid'])

    def test_wrong_family_or_step(self):
        fit=c.ARMS[1]+'/Q';m=read_json(self.root/'training_lineage_map.json')[fit]
        p=self.root/'evidence'/m['metadata'];d=read_json(p);d['step']=127;write_json(p,d)
        with self.assertRaisesRegex(ValueError,'contract'):weights.tensor_inventory(self.root,fit)
    def test_batched_persistence_and_lost_scratch_guard(self):
        from pact.revival.stage1 import io as storage
        drive=self.base/'drive';batch=storage.BatchedPersistence(self.root,drive)
        key='a'*64
        write_json(self.root/'intents'/f'{key}.json',{'component':'validation','plan_hash':'b'*64})
        batch()
        self.assertEqual(set(read_json(drive/'INFLIGHT.json')['attempts']),{key})
        with self.assertRaisesRegex(ValueError,'Unresolved'):storage.BatchedPersistence(self.root,drive)
        (self.root/'intents'/f'{key}.json').unlink()
        with self.assertRaisesRegex(ValueError,'absent'):storage.persist(self.root,drive)
        self.assertTrue((drive/'INFLIGHT.json').exists())
        with self.assertRaisesRegex(ValueError,'Pending'):storage.restore(drive,self.base/'restored')

    def test_freeze_blocker(self):
        weights.verify(self.root,None,self.backend)
        p=self.root/'contract_resolution.json';r=read_json(p);r['blockers']=['unresolved_budget'];write_json(p,r)
        with self.assertRaisesRegex(ValueError,'blocked'):engine.freeze(self.root)
    def test_missing_optimizer_separate(self):
        values,inv=weights.tensor_inventory(self.root,c.ARMS[1]+'/Q')
        self.assertTrue(inv['structural_validity']);self.assertFalse(inv['optimizer_recovery']['recovery_validated'])
    def test_staging_and_strict_missingness(self):
        self.verified();p=read_json(self.root/'plan.json')
        with self.assertRaisesRegex(ValueError,'export'):engine.execute(self.root,'validation',digest(p),None,self.backend)
        s=metrics.report(self.root)
        self.assertFalse(s['all_outputs_observed'])
        m=s['live']['validation/'+c.ARMS[1]+'/clean']
        self.assertEqual(m['observed'],0);self.assertEqual(m['full_population_equal_source_bounds'],[0,1])

if __name__=='__main__':unittest.main()

class ActualEvidence(unittest.TestCase):
    def test_available_review_bundles_and_original_budget(self):
        from collections import Counter
        repo=Path(__file__).resolve().parents[1]
        paths=list(repo.glob('*continuation-003-PRIVATE-179263091*.zip'))
        if not paths:self.skipTest('Private audit bundle not distributed with Git')
        z,checks=evidence.archive(paths[0],evidence.PRIVATE)
        try:
            p=json.loads(z.read('plan.json'));self.assertEqual(digest(p),evidence.PLAN)
            source=Counter(r['family'] for r in p['source']['records'] if r['split']=='source_evaluation')
            self.assertEqual(source,{'arc_challenge':120,'logiqa':136})
            parent,pc=evidence.archive(io.BytesIO(z.read('parent-private.zip')))
            with parent:
                intents=[json.loads(parent.read(n)) for n in pc if n.startswith('intents/') and n.endswith('.json')]
                self.assertEqual(len(intents),2438)
                self.assertEqual(Counter(v['identity']['logical'][0] for v in intents),{'fit':1536,'attack':896,'scratch':6})
                self.assertEqual(17030-2438,14592)
            self.assertFalse(any(n.endswith('.safetensors') for n in checks))
        finally:z.close()
