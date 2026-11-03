"""Synthetic CPU decisions, with active gates and histories left unchanged."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from pact.util import digest, file_hash
from pact.revival import exposure_accounting as x
from pact.revival.allocation_v3 import evidence as e
from pact.revival.gpqa_source import fixtures, graph, sources


class Decisions(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source, cls.candidate, _ = fixtures.inputs()
        cls.lineage = {'S0': {'fixture': True}}

    def packet(self, candidate=None):
        return x.assess(self.source, self.lineage, {'blockers': [], 'eligibility': None}, {}, {},
                        candidate=candidate, fixture=True)

    def test_digest_types_and_bounds(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'e.json';p.write_text('{ "a": 1 }\n')
            self.assertEqual(x.bounded_json(p,digest({'a':1}),'canonical_json')[0],{'a':1})
            with self.assertRaises(ValueError):x.bounded_json(p,digest({'a':1}),'file_sha256')
            with patch.object(x,'MAX_BYTES',2):
                with self.assertRaises(ValueError):x.bounded_json(p)

    def test_scoped_relations(self):
        self.assertEqual(x.scope_relation({'a'},{'b'},source_verified=True), 'conditional_nonintersection_requires_review')
        self.assertEqual(x.scope_relation({'a'},{'b'},source_verified=True,enforcement_bound=True), 'supported_nonintersection_within_bound_run_scope')
        self.assertEqual(x.scope_relation({'a'},{'a'},source_verified=True), 'supported_overlap')
        self.assertEqual(x.scope_relation({'a'},None,source_verified=True), 'unresolved')

    def test_exclusion_precedence_and_namespace_unique_counts(self):
        rows=[{'family':'gpqa_main','group_id':'g','reasons':['protected'],'definite_exclusion':True},
              {'family':'gpqa_main','group_id':'g','reasons':['scope_unknown']},
              {'family':'logiqa','group_id':'g','reasons':[]}, {'family':'gpqa_main'}]
        states, counts=x.classify_groups(rows)
        self.assertEqual(counts['grouped_unique_groups'],2)
        self.assertEqual(counts['unique_group_statuses'],{'excluded':1,'unresolved':1})
        self.assertEqual(counts['ungrouped_records'],1)
        self.assertEqual(x.classify_groups(rows+rows)[1]['grouped_unique_groups'],2)
        self.assertEqual(states[0]['reasons'],['protected','scope_unknown'])

    def test_acceptance_distinct_from_facts_and_spending(self):
        row={'family':'logiqa','group_id':'g','factual_inclusion_verified':True}
        states,_=x.classify_groups([row])
        self.assertTrue(states[0]['acceptance_only_gap'])
        row['scope_acceptance_verified']=True
        row['spending']='unknown'
        self.assertEqual(x.classify_groups([row])[0][0]['state'],'eligible_within_reviewed_scope')
        row['factual_inclusion_verified']=False
        self.assertEqual(x.classify_groups([row])[0][0]['state'],'unresolved')

    def event(self,physical='p1',kind='generation',status='completed'):
        return {'physical_id':physical,'execution_origin':'fixture','logical_id':'same-logical',
                'kind':kind,'status':status,'payload_digest':'a'*64}

    def test_exports_dedup_but_two_executions_count_twice(self):
        event=self.event()
        counts=x.physical_accounting([event,{**event,'export':'another'}])
        self.assertEqual(counts['unique_bound_records'],1)
        counts=x.physical_accounting([event,self.event('p2')])
        self.assertEqual(counts['unique_bound_records'],2)
        self.assertEqual(counts['logical_requests'],1)
        self.assertEqual(counts['late_discovery_refund'],0)

    def test_unknown_and_optimizer_attempts_preserved(self):
        events=[self.event('p1','optimizer_update','unresolved'),self.event('p2','optimizer_update')]
        out=x.physical_accounting(events)
        self.assertEqual(out['unique_bound_records'],2)
        self.assertEqual(out['records_by_kind_and_status']['optimizer_update/unresolved'],1)
        self.assertIsNone(out['verified_remaining_balance'])
        self.assertEqual(x.physical_accounting([{**self.event(),'physical_id':None}])['unbound_records'],1)
        with self.assertRaises(ValueError):x.physical_accounting([self.event(),{**self.event(),'status':'intent_only'}])

    def test_exact_reuse_avoids_future_only_never_refunds(self):
        target={'logical_id':'same-logical','request_digest':'r','contract_digest':'c','lineage_digest':'l'}
        receipt={**target,'status':'complete','reuse_decision':'accepted','decision_digest':'d','result_digest':'s'}
        out=x.reuse_projection([target],[receipt],[self.event()])
        self.assertEqual(out['future_logical_dispatches'],0)
        self.assertEqual(out['avoided_future_dispatches'],1)
        late=x.reuse_projection([target],[receipt],[self.event(),self.event('p2')],['same-logical'])
        self.assertEqual(late['refund'],0)
        self.assertEqual(late['avoided_future_dispatches'],0)
        self.assertEqual(late['past_physical']['unique_bound_records'],2)
        with self.assertRaises(ValueError):x.reuse_projection([target],[{**receipt,'status':'unresolved'}],[])
        with self.assertRaises(ValueError):x.reuse_projection([target],[{**receipt,'contract_digest':'wrong'}],[])

    def test_intents_are_not_completed_calls(self):
        out=x.physical_accounting([self.event(status='intent_only')])
        self.assertNotIn('generation/completed',out['records_by_kind_and_status'])
        private,_=self.packet()
        self.assertIsNone(private['history']['reported_evidence']['original_retained']['completed_calls_established_by_this_inspection'])

    def test_conditional_ceiling_without_fake_request_ids(self):
        work=x.future_work(self.source)
        self.assertEqual(work['arithmetic']['total_calls_conditional'],23728)
        self.assertEqual(work['arithmetic']['reserved_tokens_conditional'],12148736)
        self.assertEqual(work['arithmetic']['updates'],3072)
        self.assertEqual(work['arithmetic']['supervised_forwards'],24576)
        self.assertEqual(work['arithmetic']['diagnostic_forwards'],2640)
        self.assertIsNone(work['real_request_ids'])
        self.assertIsNone(work['runnable_balance'])
        with self.assertRaises(ValueError):x.future_work(self.source,reuses=[{'logical_id':'unverified'}])

    def test_inactive_proposal_rejected_by_active_history_gate(self):
        private,summary=self.packet()
        proposal=private['accounting_proposal']
        self.assertFalse(e.reviewed_history(proposal))
        self.assertIsNone(proposal['signature'])
        self.assertIsNone(proposal['accepted'])
        self.assertFalse(summary['execution_authorized'])
        self.assertEqual(proposal['current_authorized_real_work'],{'generation':0,'updates':0,'forwards':0})

    def test_original_and_replacement_not_repaired_by_continuation(self):
        private,_=self.packet()
        h=private['history']
        self.assertTrue(h['replacement_unsafe_preserved'])
        self.assertFalse(h['original_terminal_closure'])
        self.assertFalse(h['accepted_reviewed_history'])
        self.assertIn('training_use',h['possible_probe_use'])

    def test_derived_union_preserves_protection_without_event_claim(self):
        exposure={k:['protected-'+k] for k in x.FIELDS}
        before=copy.deepcopy(exposure)
        private,summary=x.assess(self.source,self.lineage,{'blockers':[]},exposure,{},fixture=True)
        for key in x.FIELDS:
            self.assertIn('protected-'+key,private['derived_exclusion_union'][key])
        self.assertEqual(exposure,before)
        self.assertTrue(summary['exclusion_union_counts']['four_fields_are_not_four_exposure_events'])
        self.assertNotIn('derived_exclusion_union',summary)
        self.assertEqual(private['allocation_unique_content_groups'],len({(r['family'],r['content_group']) for r in self.source['records']}))

    def test_missing_bindings_not_fabricated_acceptance(self):
        private,_=self.packet()
        by={r['field']:r for r in private['binding_gap_table']}
        self.assertEqual(by['parent_source_sha256']['gap_kind'],'mechanical_binding')
        self.assertFalse(by['coverage']['present_in_supplied_inventory'])
        self.assertIsNone(private['derived_binding_proposal']['accepted'])
        self.assertEqual(private['review_queue_total'],2)

    def test_candidate_source_gap_not_spending_gap(self):
        audit={'blockers':['relevant_external_consumption_unresolved']}
        _,summary=x.assess(self.source,self.lineage,audit,{}, {},candidate=self.candidate,fixture=True)
        self.assertTrue(summary['candidate_exists'])
        self.assertFalse(summary['candidate_frozen'])
        audit['blockers'].append('exposure_coverage_unknown')
        with self.assertRaises(ValueError):x.assess(self.source,self.lineage,audit,{}, {},candidate=self.candidate,fixture=True)

    def test_complete_synthetic_roundtrip_idempotent_and_private(self):
        before=copy.deepcopy((self.source,self.candidate))
        private,summary=self.packet(self.candidate)
        private['review_queue'][0]['private_case']='SECRET_SYNTHETIC'
        with tempfile.TemporaryDirectory() as tmp:
            out=Path(tmp)/'packet'
            first=x.save(out,private,summary)
            hashes={p.name:file_hash(p) for p in out.iterdir()}
            second=x.save(out,private,summary)
            self.assertEqual(second['status'],'identical_packet_reused')
            self.assertEqual(hashes,{p.name:file_hash(p) for p in out.iterdir()})
            self.assertNotIn('SECRET_SYNTHETIC',(out/'summary.sanitized.json').read_text())
            self.assertNotIn('SECRET_SYNTHETIC',(out/'accounting-proposal.sanitized.json').read_text())
            private['changed']=True
            with self.assertRaises(ValueError):x.save(out,private,summary)
        self.assertEqual(before,(self.source,self.candidate))
        self.assertEqual(summary['conditional_future']['basis'],'compiled_proposed_graph')

    def test_no_network_or_model_or_scheduler_path(self):
        with patch('socket.socket',side_effect=AssertionError('network')), \
             patch('subprocess.Popen',side_effect=AssertionError('process')):
            private,summary=self.packet()
        self.assertEqual(summary['new_real_work'],0)

    def test_cli_errors_are_sanitized(self):
        import contextlib,io
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'config.json';p.write_text('{SECRET_SYNTHETIC')
            out=io.StringIO()
            with contextlib.redirect_stdout(out):code=x.main(['--config',str(p)])
            self.assertEqual(code,1)
            self.assertNotIn('SECRET_SYNTHETIC',out.getvalue())
            self.assertNotIn(tmp,out.getvalue())


if __name__=='__main__':unittest.main()
