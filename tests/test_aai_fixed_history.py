"""CPU guards for the AAI entry point. No model imports or network."""
import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

TOOLS = Path(__file__).resolve().parents[1] / 'tools'
sys.path.insert(0, str(TOOLS))
try:
    spec = importlib.util.spec_from_file_location('fixed_history', TOOLS / 'aai_fixed_history.py')
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
finally:
    sys.path.pop(0)


class FixedHistoryEntryTests(unittest.TestCase):
    def test_exact_single_stage_command(self):
        cmd = m.invocation(Path('/run'), Path('/durable'), Path('/cache'))
        self.assertEqual(cmd[cmd.index('-m') + 1:cmd.index('--run-dir')],
                         ['pact.revival.stage1', 'fixed_history'])
        self.assertEqual(cmd[-2:], ['--plan-hash', m.transport.PLAN])
        self.assertNotIn('--mock', cmd)
        self.assertIn('--execute', cmd)

    def test_token_permissions_and_symlink(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / 'token'
            p.write_text('fixture-token\n')
            p.chmod(0o600)
            self.assertEqual(m.load_token(p), 'fixture-token')
            p.chmod(0o644)
            with self.assertRaisesRegex(ValueError, 'private'):
                m.load_token(p)
            alias = Path(tmp) / 'alias'
            alias.symlink_to(p)
            with self.assertRaisesRegex(ValueError, 'Symlink'):
                m.load_token(alias)

    def test_changed_plan_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'plan.json').write_text('{}')
            with self.assertRaisesRegex(ValueError, 'Plan changed'):
                m.boundary(root)

    def test_completed_fixed_history_cannot_restart(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'plan.json').write_text('{}')
            (root / 'contract_resolution.json').write_text('{}')
            (root / 'stages').mkdir()
            for stage in ('smoke', 'validation', 'source_evaluation'):
                (root / 'stages' / (stage + '.json')).write_text(json.dumps({
                    'execution_complete': True, 'fixture': False, 'plan_hash': m.transport.PLAN}))
            (root / 'stages/fixed_history.json').write_text('{}')
            with patch.object(m.transport, 'digest', side_effect=[m.transport.PLAN, m.transport.RESOLUTION]):
                with self.assertRaisesRegex(ValueError, 'already recorded'):
                    m.boundary(root)

    def test_reviewed_continuation_owner_and_stops(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            execution = base / 'execution'
            local = base / 'local'
            run = local / 'run'
            run.mkdir(parents=True)
            execution.mkdir()
            persistent = execution / 'persistent' / m.transport.RUN
            persistent.mkdir(parents=True)
            start = {'job_id': m.PREVIOUS_JOB, 'plan_hash': m.transport.PLAN, 'local': str(local)}
            (execution / 'STARTED.json').write_text(json.dumps(start))
            (execution / 'local-path.txt').write_text(str(local))
            (execution / 'container-exit-code.txt').write_text('1')
            with patch.object(m, 'PREVIOUS_LOCAL', str(local)), patch.object(m, 'boundary') as bound:
                self.assertEqual(m.continuation_owner(execution, local, run), persistent)
                bound.assert_called_once_with(run)
                for marker in (persistent / 'INFLIGHT.json', persistent / 'SNAPSHOT_PENDING.json',
                               run / '.lock', execution / 'execution-provenance.json', execution / 'COMPLETED.json'):
                    marker.write_text('{}')
                    with self.assertRaises(ValueError):
                        m.continuation_owner(execution, local, run)
                    marker.unlink()
                (execution / 'STARTED.json').write_text(json.dumps({**start, 'job_id': 'different'}))
                with self.assertRaisesRegex(ValueError, 'dispatch owner'):
                    m.continuation_owner(execution, local, run)

    def test_second_preflight_rejects_dispatch_or_environment_drift(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            execution = base / 'execution'
            prior = execution / 'preflight-continuation-1106891'
            prior.mkdir(parents=True)
            local = base / 'local'
            repair = base / 'repair'
            repair.mkdir()
            (prior / 'STARTED.json').write_text(json.dumps({
                'previous_job': m.PREVIOUS_JOB, 'job_id': '1106899',
                'plan_hash': m.transport.PLAN, 'local': str(local)}))
            (prior / 'container-exit-code.txt').write_text('1')
            (prior / 'PRE_DISPATCH_BOUNDARY_VERIFIED.json').write_text(json.dumps({
                'previous_job': m.PREVIOUS_JOB, 'initial_committed': 11712,
                'new_fixed_history_attempts': 0, 'starting_files_unchanged': True}))
            dispatch = prior / 'execution-provenance.json'
            dispatch.write_text('{}')
            with self.assertRaisesRegex(ValueError, 'entered execution'):
                m.repaired_preflight_owner(execution, local, repair)
            dispatch.unlink()
            (repair / 'before.json').write_text('{}')
            (repair / 'after.json').write_text(json.dumps({'sentencepiece': '0.2.1', 'protobuf': '6.33.0'}))
            with patch('importlib.metadata.distributions', return_value=[]):
                with self.assertRaisesRegex(ValueError, 'differs from verified repair'):
                    m.repaired_preflight_owner(execution, local, repair)

    def test_second_preflight_wrong_owner_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            prior = base / 'preflight-continuation-1106891'
            prior.mkdir()
            (prior / 'STARTED.json').write_text('{}')
            with self.assertRaisesRegex(ValueError, 'second preflight owner'):
                m.repaired_preflight_owner(base, Path('/local/wrong'), base / 'repair')

    def test_certificate_failure_owner_and_dispatch_guard(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            prior = base / 'preflight-continuation-1106899'
            prior.mkdir()
            local = Path('/local/fixture')
            (prior / 'STARTED.json').write_text(json.dumps({
                'previous_job': '1106899', 'job_id': '1106916',
                'plan_hash': m.transport.PLAN, 'local': str(local)}))
            (prior / 'container-exit-code.txt').write_text('1')
            (prior / 'PRE_DISPATCH_BOUNDARY_VERIFIED.json').write_text(json.dumps({
                'previous_job': m.PREVIOUS_JOB, 'initial_committed': 11712,
                'new_fixed_history_attempts': 0, 'starting_files_unchanged': True}))
            m.certificate_preflight_owner(base, local)
            (prior / 'execution-provenance.json').write_text('{}')
            with self.assertRaisesRegex(ValueError, 'entered execution'):
                m.certificate_preflight_owner(base, local)

    def test_certificate_identity_and_environment_guards(self):
        from unittest.mock import MagicMock
        context = MagicMock()
        context.get_ca_certs.return_value = [{}] * 146
        env = {k: '/etc/ssl/certs/ca-certificates.crt'
               for k in ('SSL_CERT_FILE', 'REQUESTS_CA_BUNDLE', 'CURL_CA_BUNDLE')}
        with patch.object(m.transport, 'file_sha', return_value=m.CERTIFICATE_SHA256), \
             patch('ssl.create_default_context', return_value=context), \
             patch.dict(os.environ, env):
            self.assertTrue(m.certificate_receipt()['tls_verification_enabled'])
            with patch.object(m.transport, 'file_sha', return_value='changed'):
                with self.assertRaisesRegex(ValueError, 'store changed'):
                    m.certificate_receipt()
            with patch.dict(os.environ, {'SSL_CERT_FILE': '/wrong'}):
                with self.assertRaisesRegex(ValueError, 'environment mismatch'):
                    m.certificate_receipt()


if __name__ == '__main__':
    unittest.main()
