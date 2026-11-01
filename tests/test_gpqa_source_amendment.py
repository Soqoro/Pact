import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from pact.util import digest,read_json,canonical
from pact.revival.gpqa_source import sources as s,graph,contracts,results,review,fixtures,recovery
from pact.revival.allocation_v3 import design as d
from pact.revival.allocation_v3.storage import Wallet

class Amendment(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.source,cls.candidate,cls.raw=fixtures.inputs()

    def test_cpu_seal_is_not_execution_or_new_wallet(self):
        from pact.revival.gpqa_source.plan import seal
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)/'review';fixtures.build(root)
            h=digest(read_json(root/'method.private.json'))
            with self.assertRaisesRegex(ValueError,'hash_conflict'):
                seal(root,Path(tmp)/'bad','not-reviewed')
            result=seal(root,Path(tmp)/'child',h)
            self.assertTrue(result['candidate_frozen'])
            self.assertFalse(result['execution_authorized'])
            self.assertFalse(result['wallet_created'])
            p=read_json(Path(tmp)/'child/plan.json')
            self.assertEqual(p['seeds']['continuation'],[113,227])
            self.assertIsNone(p['remaining_owned_budget'])
            with self.assertRaisesRegex(ValueError,'collision'):
                seal(root,Path(tmp)/'child',h)

    def test_source_change_invariance(self):
        base=contracts.training_contract(self.source,{'exact':'S0'})
        variants=[{'evaluation':'openbookqa','job':1,'root':'/old'}, {'evaluation':'gpqa_main','job':999,'root':'/new'}]
        projections=[]
        for metadata in variants:
            plan={'scientific':base,**metadata}
            projections.append(contracts.allocation_inputs(plan['scientific']))
        self.assertEqual(projections[0],projections[1])
        a=d.compile_policies(base['blocks'],[[1,2,3]]*8,[[2,1,3]]*8,base['shuffle'],base['s0'],base)
        b=d.compile_policies(base['blocks'],[[1,2,3]]*8,[[2,1,3]]*8,base['shuffle'],base['s0'],base)
        self.assertEqual(a,b)
        self.assertEqual(base['continuation_seeds'],(113,227))
        self.assertEqual(base['rng']['Q']['17'],int(digest([20261027,'training',17,'Q'])[:8],16))

    def test_actual_graph_source_substitution(self):
        from pact.revival.evaluation_source import graph as original
        c=copy.deepcopy(self.candidate)
        for r in c['records']:
            if r['family']=='gpqa_main':r['family']='openbookqa';r['task']['family']='openbookqa'
        old=original.compile_graph(self.source,c,{'S0':'fixture'})
        new=graph.compile_graph(self.source,self.candidate,{'S0':'fixture','scheduler_job':123})
        def projection(g):
            return [{k:v for k,v in n.items() if k not in ('id','dependencies')} for n in g['nodes'] if n['part']=='assay']
        self.assertEqual(projection(old),projection(new))
        self.assertNotEqual(old['binding_hash'],new['binding_hash'])

    def test_unequal_acceptance_does_not_reweight(self):
        out=self.outcomes();first=self.candidate['records'][0]['task']['task_id']
        for r in out:
            if r['source']=='gpqa_main':
                if r['task']!=first:
                    r['attack_accepted']=False
                    if r['condition']=='exchange':r.update(correct=None,format_status='missing')
                elif r['condition']=='exchange':r['correct']=r['team'].startswith('terminal_block')
        x=results.report(self.candidate,out)['contrasts']['exchange/terminal_block-minus-uniform']
        self.assertEqual(x['equal_source']['estimate'],.75)

    def test_graph_and_smoke(self):
        g=graph.compile_graph(self.source,self.candidate,{'S0':'fixture'})
        self.assertEqual(g['counts']['assay'],d.BUDGET['assay']);self.assertEqual(g['counts']['policy'],d.BUDGET['policy'])
        self.assertEqual(g['reserved_output_tokens'],12148736)
        self.assertEqual([len(g['smoke_manifest'][p]) for p in ('assay','policy')],[24,244])
        self.assertFalse(g['dispatchable'])

    def test_diamond_protected_even_unexposed(self):
        allowed,_,a=s.reconcile(self.raw,[self.raw[0]],[],'a'*64,reviewed=True)
        self.assertEqual(len(allowed),69);self.assertIn('diamond_protected',a['reason_counts'])

    def test_conflicting_gold(self):
        other=copy.deepcopy(self.raw[0]);other['Correct Answer'],other['Incorrect Answer 1']=other['Incorrect Answer 1'],other['Correct Answer']
        _,_,a=s.reconcile(self.raw,[other],[],'a'*64,reviewed=True)
        self.assertIn('conflicting_answer_keys',a['reason_counts'])

    def test_duplicates_and_unknown_mapping(self):
        _,_,a=s.reconcile(self.raw+[self.raw[0]],[],[],'a'*64,reviewed=True)
        self.assertIn('duplicate_alias',a['reason_counts'])
        h={'manifest':{'selected_ids':['unknown'],'protected_ids':[],'excluded_ids':[],'group_by_id':{'unknown':'g'}}}
        rows,_,a=s.reconcile(self.raw,[],[h],'a'*64,reviewed=True)
        self.assertEqual(rows,[]);self.assertEqual(a['unresolved_mapping_count'],1)

    def test_case_sensitive_integrity_and_role_stripping(self):
        row=copy.deepcopy(self.raw[0]);row['Incorrect Answer 1']=row['Correct Answer']
        self.assertEqual(s.reconcile([row],[],[],'b'*64,reviewed=True)[0],[])
        r=self.candidate['records'][0];gold=self.candidate['labels'][r['task']['task_id']]
        attacker=graph.attack_messages(r,gold);body=json.loads(attacker[1].content)
        self.assertNotEqual(body['assigned_option'],gold)
        self.assertEqual(set(body),{'task','assigned_option','style'})
        self.assertEqual(set(body['task']),{'question','context','options'})
        self.assertNotIn('Correct Answer',canonical(body))
        positions={label for label in self.candidate['labels'].values()};self.assertGreater(len(positions),1)

    def test_stable_options(self):
        a=s.reconcile(self.raw,[],[],'b'*64,reviewed=True)
        b=s.reconcile(list(reversed(self.raw)),[],[],'b'*64,reviewed=True)
        self.assertEqual({r['task']['task_id']:r['task']['options'] for r in a[0]}, {r['task']['task_id']:r['task']['options'] for r in b[0]})
        self.assertEqual(a[1],b[1])

    def test_embargo(self):
        v=contracts.training_contract(self.source,'S0');v['records'].append(self.candidate['records'][0])
        with self.assertRaisesRegex(ValueError,'embargo'):contracts.allocation_inputs(v)

    def test_context_no_truncate(self):
        class B:
            tokenizer=type('T',(),{'encode':lambda self,*a,**kw:list(range(8000))})()
            def render_messages(self,m):return 'fixture'
        with self.assertRaisesRegex(ValueError,'no_truncation'):contracts.context_check([],B())

    def outcomes(self):
        out=[]
        for r in self.candidate['records']:
            for team in results.TEAMS:
                for cond in ('clean','exchange'):
                    out.append({'task':r['task']['task_id'],'source':r['family'],'group':r['group_id'], 'team':team,'condition':cond,
                        'attack_accepted':True,'correct':team.startswith('terminal_block/113'),'format_status':'ok'})
        return out

    def test_seed_mean_and_source_weight(self):
        out=self.outcomes()
        rep=results.report(self.candidate,out)
        x=rep['contrasts']['clean/terminal_block-minus-uniform']
        self.assertEqual(x['equal_source']['estimate'],.5)
        self.assertEqual(x['seed_specific']['gpqa_main'],{'113':1.,'227':0.})
        self.assertEqual(rep['s0_independent_repetitions'],1)

    def test_missing_not_complete_case_primary(self):
        out=self.outcomes();out.pop(0)
        x=results.report(self.candidate,out)['contrasts']['clean/terminal_block-minus-S0']
        self.assertIsNone(x['equal_source']['estimate'])

    def test_zero_accepted_source(self):
        out=self.outcomes()
        for r in out:
            if r['source']=='gpqa_main':
                r['attack_accepted']=False
                if r['condition']=='exchange':r.update(correct=None,format_status='missing')
        x=results.report(self.candidate,out)['contrasts']['exchange/terminal_block-minus-uniform']
        self.assertIsNone(x['equal_source']['estimate'])
        self.assertEqual(x['by_source']['logiqa']['estimate'],.5)

    def test_unknown_invalid_distinct(self):
        out=self.outcomes();out[0].update(correct=True,format_status='invalid')
        with self.assertRaisesRegex(ValueError,'strict_failure'):results.report(self.candidate,out)

    def test_no_hidden_network(self):
        with patch('socket.socket',side_effect=AssertionError('network forbidden')):
            self.assertEqual(s.load(None)[1]['status'],'source_bytes_unavailable')
            contracts.training_contract(self.source,'S0')
            with self.assertRaisesRegex(ValueError,'explicit_source_access'):s.acquire('/unused')

    def test_restart_ownership_unknown_attempt(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);plan={'run_id':'fixture','fixture':True}
            (root/'plan.json').write_text(canonical(plan))
            w=Wallet(root,plan);key,old=w.begin('assay','score',{'fixture':1},{'scores':1})
            with self.assertRaises(ValueError):Wallet(root,plan)
            w.commit(key,{'fixture':True})
            w2=Wallet(root,plan);self.assertEqual(w2.begin('assay','score',{'fixture':1},{'scores':1})[1],{'fixture':True})
            self.assertEqual(recovery.inspect(root,plan)['spent']['assay']['scores'],1)
            with self.assertRaises(ValueError):Wallet(root,{**plan,'run_id':'new-job'})
            with recovery.owned(root,plan):
                with self.assertRaises(RuntimeError):
                    with recovery.owned(root,plan):pass

    def test_slurm_no_migration_or_network(self):
        text=Path('tools/aai_gpqa_source_audit.sbatch').read_text()
        self.assertIn('NA100q',text);self.assertIn('runtime-v1',text)
        for forbidden in ('/content','drive.mount','srun ','sbatch ','pip install','--nv','--gres='):self.assertNotIn(forbidden,text)
        self.assertIn('HF_HUB_OFFLINE=1',text)

    def test_fixture_roundtrip_privacy(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)/'run';receipt=fixtures.build(root)
            summary=review.validate(root);self.assertTrue(summary['fixture']);self.assertFalse(summary['execution_authorized'])
            r=receipt['PRIVATE'];new=review.reconstruct(root/'bundles'/r['filename'],r['sha256'],Path(tmp)/'restored')
            self.assertEqual(summary,new)
            import zipfile
            with zipfile.ZipFile(root/'bundles'/receipt['SANITIZED']['filename']) as z:
                raw=b''.join(z.read(n) for n in z.namelist())
                self.assertNotIn(self.raw[0]['Question'].encode(),raw)
                self.assertNotIn(b'source_to_canonical',raw)


class AuditCliPaths(unittest.TestCase):
    def test_json_config_paths_are_loaded_without_mutating_inputs(self):
        import contextlib
        import io
        from pact.revival.gpqa_source.__main__ import main
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);run=root/'audit';cfg={'run_dir':str(run),'parent_dir':str(root/'parent')}
            values={name:{'fixture':name} for name in ('exposure','inventory','history')}
            saved={}
            for name,value in values.items():
                path=root/(name+'.json');path.write_text(canonical(value))
                cfg[name]=str(path);saved[path]=path.read_bytes()
            config=root/'config.json';config.write_text(canonical(cfg))
            def audit(destination,parent,**kwargs):
                self.assertEqual(parent,root/'parent')
                for name,value in values.items():self.assertEqual(kwargs[name],value)
                destination.mkdir()
                return {'status':'BLOCKED','model_calls':0}
            output=io.StringIO()
            with patch.object(review,'audit',side_effect=audit) as call,contextlib.redirect_stdout(output):
                code=main(['audit','--config',str(config)])
            self.assertEqual(code,0,output.getvalue())
            self.assertEqual(call.call_count,1)
            self.assertEqual(read_json(run/'audit-input.json'),{'sha256':digest(cfg)})
            for path,value in saved.items():self.assertEqual(path.read_bytes(),value)

if __name__=='__main__':unittest.main()
