"""Fictional, offline end-to-end semantic review and span dispatch contracts."""
import copy
import io
import json
from contextlib import redirect_stdout
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch
import zipfile

from pact.cli import main
from pact.util import digest, read_json, write_json, file_hash
from pact.studies import adjudication as parent
from pact.studies.adjudication_data import import_all
from pact.studies import forensics as f, semantic_review as r, rationale_spans as s


def cli(*args):
    with redirect_stdout(io.StringIO()):return main(list(map(str,args)))


def fictional_reviews(root):
    units=read_json(root/'review_manifest.private.json')['units']
    for who in ('fictional-reviewer-1','fictional-reviewer-2'):
        r.export_review(root,who,'fixture',1);rows=[]
        for u in units:
            if not u['accepted']:continue
            row=r.template(u,who,'fixture')
            row.update(status='reviewed',lock=True,independent=True,outcome_blinded=True,review_confidence='high')
            for field,allowed in r.FIELDS.items():
                row[field]=('preserved' if 'preserved' in allowed else 'none' if 'none' in allowed else 'supports' if 'supports' in allowed else 'not_applicable' if 'not_applicable' in allowed else 'explicit_support')
            # Fictional labels only: two exact disjoint spans, no real semantic claim.
            source=u['rewritten'];_,side=r.display(u,who)
            cue=dict(start=0,end=9,text=source[:9],source_hash=digest(source))
            sham=dict(start=10,end=19,text=source[10:19],source_hash=digest(source))
            row['edit_proposal']={'side':side,'cue':cue,'sham':sham,**{k:True for k in s.APPROVAL_FLAGS}}
            rows.append(row)
        path=root/(who+'.jsonl');f.save_lines(path,rows);r.import_annotations(root,path,who)


class Study(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp=tempfile.TemporaryDirectory();base=Path(cls.tmp.name);p=base/'parent'
        with redirect_stdout(io.StringIO()):
            import_all(p,{},True);parent.freeze(p)
            for stage in ('clean','acquire','attack'):
                for judge in (('Q',) if stage=='acquire' else ('J8','J14')):
                    for ds in ('mmlu-pro','musr'):parent.execute(p,None,stage,ds,judge,None,mock=True)
            cls.bundle=parent.export(p,None)['private']
            cls.root=base/'forensics'
            cli('adjudication-forensics','import-parent','--run-dir',cls.root,'--bundle',cls.bundle['path'],'--sha256',cls.bundle['sha256'],'--mock')
            cli('adjudication-forensics','census','--run-dir',cls.root,'--mock')
            cli('adjudication-forensics','sample-review','--run-dir',cls.root,'--mock')
    @classmethod
    def tearDownClass(cls):cls.tmp.cleanup()
    def setUp(self):
        self.tmp2=tempfile.TemporaryDirectory();self.addCleanup(self.tmp2.cleanup)
        self.base=Path(self.tmp2.name);self.root=self.base/'f';shutil.copytree(self.__class__.root,self.root)
    def ready_child(self):
        fictional_reviews(self.root);child=self.base/'child';s.prepare(child,self.root,True);s.validate(child);s.preflight(child,None,True);s.freeze(child)
        return child
    def approve(self,child):
        obj=read_json(child/'authorization.template.json');obj.update(approved=True,origin='fixture',approved_by='fictional-user',decision_reference='test-only')
        path=self.base/'approval.json';write_json(path,obj);s.authorize(child,path,True)
    def test_parent_counts_and_immutable(self):
        receipt=f.check(self.root);self.assertEqual(receipt['counts'],dict(tasks=4,clean=48,clean_calls=48,no_candidate=0,rewrites=20,accepted=20,victims=120,unavailable=0))
        self.assertEqual(file_hash(Path(self.bundle['path'])),self.bundle['sha256'])
        write_json(self.root/'parent/state.json',{})
        with self.assertRaises(ValueError):f.check(self.root)
    def test_full_cli_roundtrip_resume_and_privacy(self):
        child=self.ready_child();plan=s.load(child);self.assertEqual(plan['budget']['calls'],144)
        self.approve(child)
        for judge in ('J8','J14'):
            cli('rationale-spans','smoke','--mock','--execute','--resume','--run-dir',child,'--judge',judge,'--plan-hash',digest(plan))
        self.assertEqual(s.report(child)['committed'],36)
        for judge in ('J8','J14'):
            cli('rationale-spans','evaluate','--mock','--execute','--resume','--run-dir',child,'--judge',judge,'--plan-hash',digest(plan))
        summary=s.report(child);self.assertEqual(summary['committed'],144);self.assertEqual(summary['unresolved'],0)
        for x in summary['cue_minus_sham'].values():self.assertEqual(x['difference'],0)
        self.assertEqual(s.evaluate(child,'J8',None,None,True,resume=True)['new_calls'],0)
        bundles=s.export(child);restored=self.base/'restored';s.unpack(Path(bundles['private']['path']),bundles['private']['sha256'],restored,True)
        self.assertEqual(s.report(restored),summary)
        with zipfile.ZipFile(bundles['sanitized']['path']) as z:
            text=''.join(z.read(n).decode() for n in z.namelist())
        for secret in ('Fictional rewritten','fixture-0','fictional-reviewer','prompt_ids','unit_id','task_id'):self.assertNotIn(secret,text)
        rows=plan['requests']
        self.assertEqual(len({s.rowkey(plan,v) for v in rows}),144)
        for start in range(0,len(rows),3):self.assertEqual(len({x['seed'] for x in rows[start:start+3]}),1)
    def test_no_review_no_calls_no_automatic_approval(self):
        child=self.base/'child';s.prepare(child,self.root,True)
        out=s.validate(child);self.assertEqual(out['status'],'not_testable_under_current_reviews');self.assertEqual(out['edits'],[])
        s.preflight(child,None,True);s.freeze(child)
        with self.assertRaises(ValueError):s.authorize(child,child/'authorization.template.json',True)
        self.assertFalse((child/'call-intents').exists())
    def test_blinding_lock_and_origin(self):
        out=r.export_review(self.root,'alpha','fixture',1)
        html=(Path(out['path'])/'casebook.html').read_text()
        for hidden in ('claimed_consensus','claimed_verification','"gold"','"model"','"accepted"','"enriched"','judge_outputs'):self.assertNotIn(hidden,html)
        self.assertIn("default-src 'none'",html)
        self.assertEqual(r.agreement(self.root)['independent_review_pairs'],0)
        with self.assertRaises(ValueError):r.export_review(self.root,'alpha','fixture',2)
        fictional_reviews(self.root)
        self.assertEqual(r.agreement(self.root)['independent_review_pairs'],0)  # third unassigned identity remains explicit
        with self.assertRaises(ValueError):r.export_review(self.root,'fictional-reviewer-1','fixture',2) # alpha has no review -> must remain blocked
    def test_budget_and_dispatch_failure(self):
        child=self.ready_child();self.approve(child)
        with patch.object(s.MockJudge,'generate',side_effect=RuntimeError('fictional ambiguous dispatch')):
            with self.assertRaises(RuntimeError):s.evaluate(child,'J8',None,None,True)
        self.assertFalse(read_json(child/'state.json')['recovery_safe']);self.assertEqual(len(s.inspect(child,s.load(child))[2]),1)
        with self.assertRaises(ValueError):s.evaluate(child,'J8',None,None,True,resume=True)
    def test_approval_plan_binding(self):
        child=self.ready_child();obj=read_json(child/'authorization.template.json');obj.update(approved=True,origin='fixture',approved_by='x',decision_reference='fictional',plan_hash='bad')
        path=self.base/'bad.json';write_json(path,obj)
        with self.assertRaises(ValueError):s.authorize(child,path,True)
        obj=read_json(child/'span_plan.json');obj['budget']['calls']+=1;write_json(child/'span_plan.json',obj)
        with self.assertRaises(ValueError):s.load(child)
    def test_review_locks_pass2_and_disagreement(self):
        fictional_reviews(self.root)
        self.assertEqual(r.agreement(self.root)['independent_review_pairs'],20)
        out=r.export_review(self.root,'fictional-reviewer-1','fixture',2)
        self.assertIn('judge_outputs',(Path(out['path'])/'casebook.html').read_text())
        with self.assertRaises(ValueError):r.import_annotations(self.root,self.root/'fictional-reviewer-1.jsonl','fictional-reviewer-1')
        report=r.report(self.root);self.assertEqual(report['locked_independent_review_pairs'],20)
        self.assertTrue(read_json(self.root/'annotation_manifest.private.json')['complete'])
    def test_sampling_does_not_depend_on_outcome(self):
        first=read_json(self.root/'review_manifest.private.json');slots=read_json(self.root/'span_slot_manifest.json')
        rows=f.lines(self.root/'parent/attacked_per_task.jsonl')
        for row in rows:row['attacked']=not row['attacked'];row['clean']=not row['clean']
        (self.root/'parent/attacked_per_task.jsonl').write_text(''.join(json.dumps(x)+'\n' for x in rows))
        (self.root/'review_manifest.private.json').unlink();(self.root/'span_slot_manifest.json').unlink()
        with patch.object(r,'check',return_value={'fixture':True}):second=r.sample(self.root)
        self.assertEqual(first['main_tasks'],second['main_tasks']);self.assertEqual(first['main_units'],second['main_units'])
        self.assertEqual(slots['slots'],read_json(self.root/'span_slot_manifest.json')['slots'])
        self.assertEqual(len(second['units']),len({u['unit_id'] for u in second['units']}))
    def test_escaped_review_unicode(self):
        panel=read_json(self.root/'review_manifest.private.json')
        panel['units'][0]['rewritten']='</pre><script>alert(1)</script> α'
        write_json(self.root/'review_manifest.private.json',panel)
        out=r.export_review(self.root,'escape-test','fixture',1);doc=(Path(out['path'])/'casebook.html').read_text()
        self.assertNotIn('<script>',doc);self.assertIn('&lt;script&gt;',doc)
    def test_llm_origin_cannot_unlock_spans(self):
        fictional_reviews(self.root)
        key=r.reviewer_key('fictional-reviewer-2');identity=self.root/'reviewers'/key/'identity.json'
        write_json(identity,{'reviewer_id':'fictional-reviewer-2','origin':'llm_assisted'})
        self.assertEqual(r.agreement(self.root)['independent_review_pairs'],0)
        child=self.base/'child';s.prepare(child,self.root,True)
        self.assertEqual(s.validate(child)['edits'],[])
    def test_disagreement_adjudication_preserves_originals(self):
        fictional_reviews(self.root)
        who='fictional-reviewer-2';key=r.reviewer_key(who);path=sorted((self.root/'annotations'/key).glob('*.json'))[0]
        row=read_json(path);row['task_substantive_relation']='changed';write_json(path,row) # construct disagreement fixture
        result=r.agreement(self.root);self.assertGreater(result['unresolved_conflicts'],0)
        regs=[read_json(p) for p in (self.root/'reviewers').glob('*/identity.json')]
        resolution={'case_id':row['case_id'],'field':'task_substantive_relation','adjudicator':'fictional-third',
                    'origin':'fixture','label':'uncertain','reason':'Fictional unresolved support.',
                    'review_hashes':{i['reviewer_id']:digest(r.review_state(self.root,i['reviewer_id']).get(row['case_id'])) for i in regs}}
        file=self.base/'resolution.jsonl';f.save_lines(file,[resolution]);before=file_hash(path)
        r.adjudicate(self.root,file,'fictional-third');self.assertEqual(file_hash(path),before)
        self.assertEqual(r.agreement(self.root)['adjudicated_fields'],1)
    def test_external_offline_contract_and_forensic_reimport(self):
        fixture=Path('tests/fixtures/semantic_forensics/external_results.jsonl')
        self.assertEqual(r.external_import(self.root,fixture)['live_dispatch'],False)
        r.report(self.root);bundles=f.export(self.root,r.PUBLIC,f.STUDY)
        dst=self.base/'imported';f.import_bundle(dst,Path(bundles['private']['path']),bundles['private']['sha256'],True)
        self.assertEqual(f.check(dst),f.check(self.root))
        with self.assertRaises(ValueError):f.import_bundle(self.base/'invalid',Path(bundles['sanitized']['path']),bundles['sanitized']['sha256'],True)
        bad=f.lines(fixture);bad[0]['execution_enabled']=True;path=self.base/'external-bad.jsonl';f.save_lines(path,bad)
        with self.assertRaises(ValueError):r.external_import(self.root,path)
    def test_context_exclusion_and_budget_before_dispatch(self):
        child=self.ready_child();self.approve(child);plan=s.load(child)
        backend=s.MockJudge('J8');write_json(child/'identities/J8.json',backend.identity)
        wrapper=s.SpanJournal(backend,child,plan,lambda:None)
        wrapper.budget={'generation_calls_upper_bound':1,'generated_tokens_upper_bound':512}
        rows=[x for x in plan['requests'] if x['model']=='J8']
        with redirect_stdout(io.StringIO()):
            wrapper.begin_record(s.rowkey(plan,rows[0]));wrapper.generate(s.request_from(rows[0]))
            wrapper.begin_record(s.rowkey(plan,rows[1]))
            with self.assertRaises(ValueError):wrapper.generate(s.request_from(rows[1]))
        self.assertEqual(len(backend.calls),1)
        with patch.object(s.MockJudge,'count_tokens',return_value=8192):
            with self.assertRaises(ValueError):s.evaluate(child,'J14',None,None,True,resume=True)
        self.assertEqual(len(s.inspect(child,plan)[0]),1)
    def test_unsafe_durable_latest_no_fallback(self):
        child=self.ready_child();self.approve(child);persistent=self.base/'drive'
        with redirect_stdout(io.StringIO()):s.checkpoint(child,persistent);s.restore(persistent,self.base/'restored',True)
        write_json(child/'state.json',{'plan_hash':digest(s.load(child)),'recovery_safe':False})
        with redirect_stdout(io.StringIO()):s.checkpoint(child,persistent)
        with self.assertRaises(ValueError):s.restore(persistent,self.base/'unsafe',True)
    def test_negative_cue_effect_is_retained(self):
        child=self.ready_child();self.approve(child);original=s.MockJudge.generate
        def generate(backend,request):
            raw,call=original(backend,request);body=json.loads(request.messages[1].content)
            cue=next((c for c in body.get('candidates',[]) if c.get('justification','').startswith(' rewritten')),None)
            if cue:
                field='candidate_id' if '"candidate_id"' in request.messages[0].content else 'answer'
                raw=json.dumps({'decision_basis':'Fictional negative intervention.',field:cue[field]})
                backend.last_generation['raw']=raw
            return raw,call
        with patch.object(s.MockJudge,'generate',generate),redirect_stdout(io.StringIO()):
            for judge in ('J8','J14'):s.evaluate(child,judge,None,None,True,smoke=True,resume=True)
        report=s.report(child)
        self.assertEqual(report['committed'],36)
        self.assertTrue(any(v['difference'] is not None and v['difference']<0 for v in report['cue_minus_sham'].values()))
        self.assertEqual(report['planned_calls'],144) # no replacement or outcome-based expansion


class Contracts(unittest.TestCase):
    def test_notebook_cells_compile_and_default_off(self):
        path=Path('notebooks/21_rationale_spans_colab.ipynb')
        cells=read_json(path)['cells'];code=''
        for cell in cells:
            if cell['cell_type']=='code':
                source=''.join(cell['source']);compile(source,str(path),'exec');code+=source
        for flag in ('EXECUTE_SMOKE','EXECUTE_J8','EXECUTE_J14','IMPORT_USER_DECISION','METADATA_PREFLIGHT'):
            self.assertIn(flag+' = False',code)

    def test_quadrants_ceiling_and_missing(self):
        rows=[dict(T=t,O=o,Y=y,constrained=False,stratum='s',group_id=str(i)) for i,(t,o,y) in enumerate([(False,True,True),(True,False,False),(True,True,False),(False,False,True)])]
        v=f.opportunity_metrics(rows);self.assertEqual(v['quadrants'],{'00':1,'01':1,'10':1,'11':1});self.assertEqual(v['gains'],2);self.assertEqual(v['losses'],2);self.assertEqual(v['net']['value'],0)
        self.assertEqual(v['construction']['numerator'],1)
        with self.assertRaises(ValueError):f.opportunity_metrics([{**rows[-1],'constrained':True}])
        self.assertIsNone(f.opportunity_metrics([])['rescue']['value'])
    def test_unicode_deletion_and_token_lengths(self):
        text='α cue. sham. Ω';span=lambda a,b:dict(start=a,end=b,text=text[a:b],source_hash=digest(text))
        d=s.deletions(text,span(2,7),span(7,12));self.assertEqual(d['cue_deleted'],'α sham. Ω')
        with self.assertRaises(ValueError):s.deletions(text,span(2,8),span(7,12))
        bad=span(2,7);bad['source_hash']='bad'
        with self.assertRaises(ValueError):s.deletions(text,bad,span(7,12))
        lengths=s.token_match('a'*10,'b'*19,{'chars':list,'words':str.split})
        self.assertFalse(lengths['chars']['compatible']);self.assertTrue(lengths['words']['compatible'])
    def test_transitions(self):
        self.assertEqual(f.transition(True,False,'length'),'correct_to_length')
        self.assertEqual(f.transition(True,None,'rewrite_rejected'),'unavailable_rewrite_rejected')
        self.assertEqual(f.transition(False,True,'ok'),'wrong_to_correct')
    def test_private_boundary(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);(root/'.git').mkdir()
            with self.assertRaises(ValueError):f.private_root(root/'private')
