import copy
import tempfile
import unittest
import zipfile
from pathlib import Path
from pact.util import digest, read_json, write_json
from pact.revival.documented_child import audit, review
from pact.revival.gpqa_source import fixtures, graph, sources
from pact.revival.evaluation_source.fixtures import inputs
from pact.revival.allocation_v3 import design


class DocumentedChildTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source, cls.candidate, cls.raw = fixtures.inputs()
        cls.lineage={'S0':{'fixture':True}}
        cls.aud={'fixture':True,'blockers':[], 'eligibility':{'screened_unique_groups':dict.fromkeys(sources.SOURCES_EVAL,70)}}

    def test_graph_exact_limits_and_distinct_namespace(self):
        a=graph.compile_graph(self.source,self.candidate,self.lineage)
        b=review.compile_graph(self.source,self.candidate,self.lineage)
        self.assertEqual(b['counts'], {p:design.BUDGET[p] for p in ('assay','policy')})
        self.assertEqual(b['reserved_output_tokens'],12148736)
        self.assertFalse(set(n['id'] for n in a['nodes'])&set(n['id'] for n in b['nodes']))
        self.assertEqual([n.get('seed') for n in a['nodes']],[n.get('seed') for n in b['nodes']])
        known=set()
        for n in b['nodes']:
            self.assertTrue(set(n['dependencies'])<=known);known.add(n['id'])
        for part, families, cap in [('assay',{'arc_challenge','logiqa'},24),('policy',{'gpqa_main','logiqa'},244)]:
            ids=b['smoke_manifest'][part];self.assertEqual(len(ids),cap)
            rows=self.source['records'] if part=='assay' else self.candidate['records']
            taskfamily={r['task']['task_id']:r['family'] for r in rows}
            self.assertEqual({taskfamily[n['task_id']] for n in b['nodes'] if n['id'] in ids},families)

    def screening(self, **kwargs):
        source, _, train, val, ex = inputs()
        return audit.screen(self.raw,[],[],'b'*64,train,val,source,ex,fixture=True,**kwargs)

    def test_real_screening_algorithm_on_invented_bytes(self):
        rows,labels,result=self.screening()
        self.assertTrue(all(n>=64 for n in result['screened_unique_groups'].values()))
        candidate=sources.select(rows,labels)
        self.assertEqual(len(candidate['records']),128)
        self.assertFalse(result['semantic_decontamination'])
        self.assertFalse(candidate['cohort_approved'])

    def test_candidate_unknown_and_preview_are_not_waived(self):
        rows,_,_=self.screening();tid=rows[0]['task']['task_id']
        for reason in ('unresolved_concrete_exposure','recorded_preview','unrecognized_reason'):
            selected,_,result=self.screening(cases=[{'task_id':tid,'reason':reason}])
            self.assertNotIn(tid,{r['task']['task_id'] for r in selected})
            self.assertTrue(any(r['task_id']==tid and r['state']!='screened' for r in result['decisions']))

    def test_unmapped_case_fails_closed(self):
        with self.assertRaisesRegex(ValueError,'mapping'):self.screening(cases=[{'task_id':'missing','reason':'recorded_preview'}])

    def test_diamond_protected_without_legacy_review(self):
        source,_,train,val,ex=inputs()
        rows,_,result=audit.screen(self.raw,self.raw[:1],[],'b'*64,train,val,source,ex,fixture=True)
        protected=sources.native._normalize_for_partition(self.raw[0],'b'*64)[0].task_id
        self.assertNotIn(protected,{r['task']['task_id'] for r in rows})
        self.assertIn('diamond_protected',result['gpqa_integrity']['reason_counts'])

    def test_actual_group_shortfall_stays_visible(self):
        source,_,train,val,ex=inputs()
        rows,_,result=audit.screen(self.raw[:63],[],[],'b'*64,train,val,source,ex,fixture=True)
        self.assertLess(result['screened_unique_groups']['gpqa_main'],64)

    def test_training_interface_never_contains_evaluation(self):
        values=review.assemble(self.source,self.lineage,self.aud,self.candidate)
        train=values['training.private.json'];eval_ids={r['task']['task_id'] for r in self.candidate['records']}
        import json
        encoded=json.dumps(train)
        self.assertFalse(any(tid in encoded for tid in eval_ids))
        self.assertEqual(values['method.private.json']['S0'],self.lineage['S0'])

    def test_roundtrip_privacy_recovery_and_idempotence(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)/'audit';out=review.save(root,self.source,self.lineage,self.aud,self.candidate)
            self.assertEqual(review.save(root,self.source,self.lineage,self.aud,self.candidate),out)
            receipts=review.export(root)
            public=root/'bundles'/receipts['SANITIZED']['filename']
            with zipfile.ZipFile(public) as z:
                self.assertEqual(set(z.namelist()),{'summary.sanitized.json','checksums.json','HANDOFF.json'})
                payload=z.read('summary.sanitized.json').decode()
                self.assertNotIn(self.candidate['records'][0]['task']['task_id'],payload)
            private=root/'bundles'/receipts['PRIVATE']['filename']
            self.assertEqual(review.restore(private,receipts['PRIVATE']['sha256'],Path(tmp)/'restored'),out)
            with self.assertRaises(ValueError):review.restore(private,'0'*64,Path(tmp)/'wrong')
            self.assertFalse((root/'events').exists());self.assertFalse((root/'attempts').exists())
            with self.assertRaises(ValueError):review.save(root,self.source,{'S0':{'fixture':'other'}},self.aud,self.candidate)

    def test_guard_no_wallet_even_with_matching_checkpoint(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)/'audit';review.save(root,self.source,self.lineage,self.aud,self.candidate)
            method=read_json(root/'method.private.json');h=digest(method)
            with self.assertRaisesRegex(ValueError,'checkpoint'):review.execution_guard(root,'assay-smoke',h)
            kw={'checkpoint_receipt':{'S0':self.lineage['S0'],'tensors_verified':True}}
            with self.assertRaises(PermissionError):review.execution_guard(root,'assay-smoke',h,**kw)
            with self.assertRaisesRegex(ValueError,'lock'):review.execution_guard(root,'evaluate',h,**kw)
            self.assertFalse((root/'events').exists())
            write_json(root/'INFLIGHT.json',{})
            with self.assertRaisesRegex(ValueError,'unresolved'):review.execution_guard(root,'assay-smoke',h,**kw)

    def test_mutated_graph_and_wrong_checkpoint_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)/'audit';review.save(root,self.source,self.lineage,self.aud,self.candidate)
            method=read_json(root/'method.private.json')
            with self.assertRaises(ValueError):review.execution_guard(root,'collect',digest(method),checkpoint_receipt={'S0':{},'tensors_verified':True})
            write_json(root/'graph.private.json',{})
            with self.assertRaises(ValueError):review.validate(root)

    def test_legacy_training_lexical_results_are_preserved(self):
        from pact.training.data import audit_training_overlap
        from pact.revival.documented_child.lexical import audit_components
        source,_,train,val,ex=inputs()
        self.assertEqual(audit_training_overlap(train,val)[0], audit_components(train,val)[0])

    def test_documented_exclusion_union_is_enforced(self):
        source,_,train,val,ex=inputs()
        tid=train[0][0].task_id
        ex['task_ids'].append(tid)
        rows,_,a=audit.screen(self.raw,[],[],'b'*64,train,val,source,ex,fixture=True)
        self.assertNotIn(tid,{r['task']['task_id'] for r in rows})
        self.assertTrue(any(r['task_id']==tid and 'historical_or_protected_overlap' in r['reasons'] for r in a['decisions']))

    def test_policy_freeze_uses_only_training_and_preserves_five_policies(self):
        from pact.revival.documented_child import policies
        from pact.revival.gpqa_source.contracts import training_contract
        contract=training_contract(self.source,self.lineage['S0'])
        probes={f:[r['task']['task_id'] for r in contract['records'] if r['split']=='allocation_probe' and r['family']==f] for f in design.SOURCES}
        scores={}
        for ids in probes.values():
            for tid in ids:
                for kind in ('clean','exchange','private_bank'):
                    scores['S0',tid,kind]={'raw_nll':2.,'capped_nll':2.}
        for b,block in enumerate(contract['blocks']):
            for family in design.FAMILIES:
                for tid in probes[block['family']]:
                    for kind in ('clean','exchange','private_bank'):
                        scores[f'block-{b}-{family}',tid,kind]={'raw_nll':1.,'capped_nll':1.}
        accepted=dict.fromkeys(sum(probes.values(),[]),True)
        result=policies.freeze(contract,scores,accepted,'a'*64)
        self.assertEqual(set(result['policies']['matrices']),set(design.POLICIES))
        self.assertEqual(result['evaluation_source_weights'],{'gpqa_main':.5,'logiqa':.5})
        self.assertEqual(len(scores),2640)
        incomplete=dict(scores);incomplete.pop(next(iter(incomplete)))
        with self.assertRaises(KeyError):policies.freeze(contract,incomplete,accepted,'a'*64)

    def test_labels_do_not_choose_candidate(self):
        rows,labels,_=self.screening()
        a=sources.select(rows,labels);b=sources.select(rows,{k:'changed' for k in labels})
        self.assertEqual(a['records'],b['records'])

if __name__=='__main__':unittest.main()
