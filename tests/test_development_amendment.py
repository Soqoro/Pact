"""Inactive proposal and unchanged legacy gates; synthetic source fixtures only."""
import copy
import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from pact.util import digest
from pact.revival import development_amendment as a, exposure_accounting as prior
from pact.revival.gpqa_source import fixtures, graph
from pact.revival.allocation_v3 import evidence, design
from pact.revival.evaluation_source.sources import exposure_status


class DevelopmentAmendment(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source, cls.candidate, _ = fixtures.inputs()
        cls.lineage = {'S0': {'fixture': True}}
        _, cls.summary = prior.assess(cls.source, cls.lineage, {'eligibility': None}, {}, {}, fixture=True)

    def proposal(self, summary=None):
        return a.compile_proposal(self.source, self.lineage, summary or self.summary, {}, fixture=True)

    def test_absent_semantic_review_relaxed_only_as_disclosed_development(self):
        out = a.proposed_screen(dict.fromkeys(a.FACTS, True), list(a.DISCLOSED_LIMITATIONS))
        self.assertEqual(out['state'], 'proposed_documented_exclusion_screen_pass')
        self.assertFalse(out['freshness_certified'])
        self.assertFalse(out['execution_authorized'])

    def test_all_protections_remain_exclusions(self):
        for reason in a.EXCLUSIONS:
            with self.subTest(reason=reason):
                self.assertEqual(a.proposed_screen({}, [reason, 'exposure_scope_unverified'])['state'], 'excluded')

    def test_concrete_unknown_or_material_case_never_waived(self):
        for reason in ('material_semantic_overlap', 'unresolved_historical_mapping',
                       'unresolved_revision_or_content_mapping', 'future_unknown_reason'):
            self.assertEqual(a.proposed_screen(dict.fromkeys(a.FACTS, True), [reason])['state'], 'unresolved')

    def test_missing_or_truthy_facts_are_not_verified(self):
        for key in a.FACTS:
            for value in (None, False, 1, 'true'):
                facts = dict.fromkeys(a.FACTS, True); facts[key] = value
                self.assertEqual(a.proposed_screen(facts, [])['state'], 'unresolved')
        with self.assertRaises(ValueError): a.proposed_screen({}, 'protected')

    def test_inactive_no_approval_or_old_balance(self):
        p = self.proposal()
        self.assertIsNone(p['approval']['accepted'])
        self.assertFalse(p['wallet_created'])
        self.assertFalse(p['runner_integration']['implemented'])
        self.assertIsNone(p['old_remaining_balance'])
        self.assertIsNone(p['cumulative_past_plus_future_bound'])
        self.assertFalse(p['physical_rules']['late_duplicate_refund'])
        self.assertEqual(sum(p['current_authorized_work'].values()), 0)

    def test_exact_graph_ceiling_on_synthetic_cohort(self):
        g = graph.compile_graph(self.source, self.candidate, self.lineage)
        p = self.proposal()
        self.assertEqual(sum(n['kind']=='generation' for n in g['nodes']), 23728)
        self.assertEqual(g['reserved_output_tokens'], 12148736)
        self.assertEqual(p['future_work']['ceiling'], design.BUDGET)
        self.assertEqual(p['unchanged']['training'], design.TRAIN)
        self.assertEqual(p['unchanged']['analysis'], design.ANALYSIS)
        self.assertEqual(p['unchanged']['selection_namespace'], graph.NAMESPACE)

    def test_input_immutable_and_public_allowlist(self):
        summary = copy.deepcopy(self.summary)
        summary['untrusted_private_question'] = 'DO_NOT_EXPORT'
        before = digest(summary)
        p = self.proposal(summary)
        self.assertEqual(digest(summary), before)
        self.assertNotIn('DO_NOT_EXPORT', json.dumps(p))

    def test_candidate_and_budget_tampering_rejected(self):
        for key, value in [('candidate_exists', True), ('candidate_frozen', True),
                           ('execution_authorized', True), ('new_real_work', 1)]:
            s = copy.deepcopy(self.summary); s[key] = value
            with self.assertRaises(ValueError): self.proposal(s)
        s = copy.deepcopy(self.summary)
        s['conditional_future']['arithmetic']['total_calls_conditional'] += 1
        with self.assertRaises(ValueError): self.proposal(s)

    def test_fixture_cannot_be_promoted(self):
        with self.assertRaises(ValueError):
            a.compile_proposal(self.source, self.lineage, self.summary, {}, fixture=False)

    def test_legacy_gates_unchanged(self):
        p = self.proposal()
        self.assertFalse(evidence.reviewed_history(p))
        result = exposure_status({}, self.source, fixture=True)
        self.assertIn('semantic_overlap_review_unresolved', result['blockers'])
        self.assertIn('exposure_coverage_unknown', result['blockers'])

    def test_cli_errors_do_not_disclose_private_input(self):
        with tempfile.TemporaryDirectory() as t:
            cfg = Path(t)/'cfg.json'; cfg.write_text('{}')
            stream = io.StringIO()
            with patch.object(a, 'build', side_effect=ValueError('PRIVATE_PAYLOAD')), contextlib.redirect_stdout(stream):
                self.assertEqual(a.main(['--config', str(cfg)]), 1)
            self.assertNotIn('PRIVATE_PAYLOAD', stream.getvalue())


if __name__ == '__main__':
    unittest.main()
