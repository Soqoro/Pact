import copy
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from pact.util import digest, file_hash, write_json
from pact.revival.evaluation_source import sources as s, graph as g, review, fixtures, results
from pact.revival.allocation_v3 import evidence as e, design as d
from pact.revival import contracts as c


class EvaluationSourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source,cls.ob,cls.train,cls.val,cls.exposure=fixtures.inputs()
        rows,labels,cls.aud=s.eligibility(cls.ob,cls.train,cls.val,cls.source,cls.exposure,fixture=True)
        cls.candidate=s.select(rows,labels)
        cls.graph=g.compile_graph(cls.source,cls.candidate,{'fixture':True})

    def row(self):
        return {'id':'fixture','question_stem':'What symbol follows?',
                'choices':{'label':['D','B','A','C'],'text':['four','two','one','three']},'answerKey':'B'}

    def test_nested_choice_roundtrip(self):
        t,l=s.openbook_row(self.row(),'a'*40,'b'*64)
        self.assertEqual([o.answer_id for o in t.options],list('DBAC'))
        self.assertEqual(next(o.text for o in t.options if o.answer_id==l.answer_id),'two')
        self.assertEqual(c.parse('{"answer":"B","justification":"x"}',__import__('dataclasses').asdict(t))['status'],'ok')
        self.assertNotIn('answerKey',c.prompt(__import__('dataclasses').asdict(t))[1].content)

    def test_malformed_schema(self):
        variants=[]
        for key,value in [('fact1','gold hint'),('humanScore',1),('clarity',1)]:
            row=self.row();row[key]=value;variants.append(row)
        for labels in (['A','A','C','D'],['A','B','C','E'],['A','B','C']):
            row=self.row();row['choices']['label']=labels;variants.append(row)
        for key,value in [('answerKey','E'),('question_stem',''),('question_stem','bad\ud800')]:
            row=self.row();row[key]=value;variants.append(row)
        for row in variants:
            with self.subTest(row=repr(row)),self.assertRaises((ValueError,UnicodeError)):
                s.openbook_row(row,'a'*40,'b'*64)

    def spec(self,sha):
        return {'repository':'allenai/openbookqa','config':'main','split':'train',
                'path':'main/train.jsonl','revision':'a'*40,'sha256':sha,'format':'jsonl'}

    def test_bytes_rights_identity_distinct(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'raw.jsonl';spec=self.spec('b'*64)
            rows,report=s.load_openbook(path,spec)
            self.assertIsNone(rows);self.assertEqual(report['status'],'source_bytes_unavailable')
            path.write_text(json.dumps(self.row())+'\n');spec['sha256']=file_hash(path)
            rows,report=s.load_openbook(path,spec)
            self.assertEqual(len(rows),1);self.assertFalse(report['rights_reviewed']);self.assertFalse(report['source_identity_reviewed'])
            spec['sha256']='c'*64
            with self.assertRaisesRegex(ValueError,'digest'):s.load_openbook(path,spec)

    def test_unpinned_and_additional_rejected(self):
        for key,value in [('revision','main'),('config','additional'),('split','test'),('path','refs/convert/parquet/main/train.parquet')]:
            spec=self.spec('b'*64);spec[key]=value
            with self.assertRaises(ValueError):s.check_spec(spec)

    def test_rights_bound_to_exact_identity(self):
        ident=s.source_identity(self.spec('b'*64))
        rights={'status':'approved_for_proposed_use','reviewed_by_human':True,'item_scope_reviewed':True,
                'source_identity_sha256':digest(ident),'terms':[{'url':'https://example.invalid/terms','sha256':'a'*64}],
                'review_receipt_sha256':'c'*64}
        self.assertTrue(s.rights_status(rights,ident))
        self.assertFalse(s.rights_status(rights,{**ident,'revision':'d'*40}))
        self.assertFalse(s.rights_status({'status':'Apache-2.0'},ident))

    def test_rights_documents_must_exist_and_match(self):
        identity=s.source_identity(self.spec('b'*64))
        with tempfile.TemporaryDirectory() as tmp:
            terms=Path(tmp)/'terms';terms.write_text('Invented test-only permission text')
            terms_info={'url':'https://example.invalid/terms','sha256':file_hash(terms)}
            receipt=Path(tmp)/'review.json'
            saved={'source_identity_sha256':digest(identity),'reviewed_by_human':True,
                   'status':'approved_for_proposed_use','item_scope_reviewed':True,'terms':[terms_info]}
            write_json(receipt,saved)
            rights={**saved,'terms':[{**terms_info,'local_file':str(terms)}],
                    'review_receipt_file':str(receipt),'review_receipt_sha256':file_hash(receipt)}
            self.assertTrue(s.reviewed_documents(rights,identity))
            terms.write_text('changed')
            self.assertFalse(s.reviewed_documents(rights,identity))

    def test_current_source_revision_and_row_count_guards(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'rows';path.write_text(json.dumps(self.row())+'\n')
            spec=self.spec(file_hash(path));spec['expected_rows']=4957
            with self.assertRaisesRegex(ValueError,'row_count'):s.load_openbook(path,spec)

    def test_branch_probe_support_and_exact_original_update_order(self):
        for b,block in enumerate(self.source['blocks']):
            expected=24 if block['family']=='arc_challenge' else 40
            for family in d.FAMILIES:
                team=f'branch/{b}/{family}'
                selected=[n for n in self.graph['nodes'] if n['kind']=='generation' and n.get('team')==team and n['phase']=='private']
                self.assertEqual(len(selected),expected)
                updates=[n for n in self.graph['nodes'] if n['kind']=='update' and n['part']=='assay' and n['key'][0]==team]
                self.assertEqual([t for n in updates for t in n['fit_task_ids']],d.ordered(block['fit'],'temporary',17,b,family))
        self.assertEqual(g.budget_reconciliation(self.source)['supervised_forwards'],24576)

    def test_duplicate_stable_ids_both_denied(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'rows';path.write_text((json.dumps(self.row())+'\n')*2)
            rows,report=s.load_openbook(path,self.spec(file_hash(path)))
            self.assertEqual(rows,[]);self.assertEqual(report['rejection_counts']['duplicate_stable_id'],2)

    def test_exposure_unknown_not_fresh(self):
        ex=copy.deepcopy(self.exposure);ex.pop('coverage')
        rows,labels,a=s.eligibility(self.ob,self.train,self.val,self.source,ex,fixture=True)
        self.assertEqual(rows,[]);self.assertEqual(a['counts']['logiqa']['unknown_items'],70)
        self.assertFalse(s.exposure_status(self.exposure,self.source)['status']=='verified')

    def test_rights_unknown_not_permitted(self):
        rows,labels,a=s.eligibility(self.ob,self.train,self.val,self.source,self.exposure,
            fixture=True,source_reviewed={'openbookqa':False,'logiqa':True})
        self.assertEqual(a['counts']['openbookqa']['unknown_items'],70)
        self.assertEqual(a['counts']['openbookqa']['permitted_items'],0)

    def test_exact_and_cross_source_exclusions(self):
        ex=copy.deepcopy(self.exposure);ex['content_groups']=[s.content_group(self.ob[0][0])]
        rows,labels,a=s.eligibility(self.ob,self.train,self.val,self.source,ex,fixture=True)
        self.assertEqual(a['counts']['openbookqa']['permitted_items'],69)
        self.assertEqual(a['denied'][self.ob[0][0].task_id],'historical_or_protected_overlap')
        from dataclasses import replace
        t=self.ob[1][0];copytask=replace(t,task_id='logiqa:copy',family='logiqa')
        tr=[*self.train,(copytask,replace(self.ob[1][1],task_id='logiqa:copy'))]
        rows,labels,a=s.eligibility(self.ob,tr,self.val,self.source,self.exposure,fixture=True)
        self.assertEqual(len({r['content_group'] for r in rows}),len(rows))

    def test_selection_independent_of_answers_order_and_no_reroll(self):
        rows,labels,a=s.eligibility(self.ob,self.train,self.val,self.source,self.exposure,fixture=True)
        one=s.select(rows,labels);two=s.select(list(reversed(rows)),dict.fromkeys(labels,'D'))
        self.assertEqual(one['records'],two['records']);self.assertFalse(one['cohort_approved'])
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)/'child';review.immutable_root(root,fixture=True);write_json(root/'marker',{})
            with self.assertRaisesRegex(ValueError,'collision'):review.immutable_root(root,fixture=True)

    def test_v3_unchanged_and_old_source_conflict(self):
        actual=e.fixture_source();actual['available']={'arc_challenge':406,'logiqa':6605}
        # Fixture counts differ from actual; use explicit actual record count for capacity test.
        actual['records']=[{'family':'arc_challenge','group_id':str(i)} for i in range(400)]+[{'family':'logiqa','group_id':str(i)} for i in range(560)]
        self.assertEqual(e.prospective_capacity(actual)['fresh_upper_bound']['arc_challenge'],6)
        bad=copy.deepcopy(self.source);bad['blocks'][3]['family']='arc_challenge'
        with self.assertRaises(ValueError):g.compile_graph(bad,self.candidate,{})
        self.assertNotIn(g.ASSAY,(d.ASSAY,d.POLICY));self.assertNotEqual(g.VERSION,d.VERSION)

    def test_graph_exact_counts_dependencies_smokes(self):
        graph=self.graph;self.assertEqual(graph['counts']['assay'],d.BUDGET['assay'])
        self.assertEqual(graph['counts']['policy'],d.BUDGET['policy'])
        self.assertEqual(graph['reserved_output_tokens'],12148736)
        ids={n['id'] for n in graph['nodes']};self.assertEqual(len(ids),len(graph['nodes']))
        self.assertEqual({p:len(v) for p,v in graph['smoke_manifest'].items()},{'assay':24,'policy':244})
        for v in graph['smoke_manifest'].values():self.assertTrue(set(v)<=ids)
        self.assertFalse(graph['dispatchable'])
        self.assertNotEqual(graph['binding_hash'],g.compile_graph(self.source,self.candidate,{'fixture':True,'changed':'yes'})['binding_hash'])

    def test_native_prompts_own_team_dependency_and_attack(self):
        r=self.candidate['records'][0];gold=self.candidate['labels'][r['task']['task_id']]
        attacker=g.attack_messages(r,gold)[1].content
        payload=json.loads(attacker)
        self.assertEqual(set(payload),{'task','assigned_option','style'})
        self.assertNotEqual(payload['assigned_option'],gold)
        node=next(n for n in self.graph['nodes'] if n.get('task_id')==r['task']['task_id'] and n.get('phase')=='revision' and n.get('condition')=='exchange')
        bank=[{'status':'ok','answer':'B','justification':'own'} for _ in range(3)]
        saved=copy.deepcopy(bank)
        attack={'accepted':True,'sender':r['sender'],'packet':{'status':'ok','answer':'A','justification':'fixed'}}
        a=g.render_request(node,r,bank,attack,'checkpoint-A',{'runtime':'fixed'})
        bank[1]['justification']='new team own message'
        b=g.render_request(node,r,bank,attack,'checkpoint-B',{'runtime':'fixed'})
        self.assertNotEqual(a['request_hash'],b['request_hash'])
        self.assertEqual(saved[0]['justification'],'own')
        self.assertEqual(a['messages'][0],b['messages'][0])
        delivered=c.delivered(saved,(r['sender']+1)%3,attack)
        self.assertEqual(next(x['packet'] for x in delivered if x['slot']==r['sender']),attack['packet'])

    def test_allocator_preserved(self):
        scores=[[float(i+j) for j in range(3)] for i in range(8)]
        q=d.quotas(scores)['quotas']
        control=d.source_family(q,self.source['blocks'])
        self.assertTrue(all(sum(r)==12 for r in control))
        for family in d.SOURCES:
            ix=[i for i,b in enumerate(self.source['blocks']) if b['family']==family]
            self.assertEqual([sum(q[i][j] for i in ix) for j in range(3)],
                             [sum(control[i][j] for i in ix) for j in range(3)])
        shuffle=d.derangement(self.source['blocks']);self.assertTrue(all(i!=v for i,v in enumerate(shuffle)))

    def test_no_download_or_execute_interface(self):
        from pact.revival.evaluation_source.__main__ import main
        with patch('urllib.request.urlopen',side_effect=AssertionError('network')):
            self.assertEqual(review.acquisition_plan()['network_requests'],0)
            self.assertIsNone(s.original_sources(None)[0])
        for args in (['run'],['audit','--execute'],['audit','--download']):
            import contextlib,io
            with contextlib.redirect_stderr(io.StringIO()),self.assertRaises(SystemExit):main(args)

    def test_missing_attacks_and_invalid_outputs(self):
        r=self.candidate['records'][0];gold=self.candidate['labels'][r['task']['task_id']]
        packet='{"answer":"B","justification":"test"}'
        out=results.score(r,gold,'S0','exchange',[packet]*3,[packet]*3,packet,{'accepted':False})
        self.assertIsNone(out['correct'])
        out=results.score(r,gold,'S0','clean',[packet]*3,[packet]*3,'not JSON',None)
        self.assertFalse(out['correct']);self.assertEqual(out['format_status'],'invalid')
        self.assertIsNone(out['attack_accepted'])
        self.assertIsNone(results.interval([[],[1.]])['estimate'])


class RoundTrip(unittest.TestCase):
    def test_mock_export_reconstruct(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)/'mock'
            bundles=fixtures.build(root)
            summary=review.validate(root)
            self.assertTrue(summary['fixture']);self.assertFalse(summary['gpu_execution_authorized'])
            import zipfile
            with zipfile.ZipFile(bundles['SANITIZED']['path']) as z:
                self.assertEqual(set(z.namelist()),{'summary.json','mock-summary.json','checksums.json','HANDOFF.json'})
                raw=b''.join(z.read(n) for n in z.namelist())
                self.assertNotIn(b'Invented exercise',raw);self.assertNotIn(b'openbookqa:train:',raw)
            rec=review.reconstruct(bundles['PRIVATE']['path'],bundles['PRIVATE']['sha256'],Path(tmp)/'reimport')
            self.assertTrue(rec['reconstructed'])
            report=json.loads((root/'mock-summary.json').read_text())
            self.assertEqual(set(report['by_source']),set(s.SOURCES_EVAL))
            self.assertTrue(report['two_seeds_not_independent_method_replications'])
            self.assertIsNone(report['scientific_result'])

if __name__=='__main__':unittest.main()
