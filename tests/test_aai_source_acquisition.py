"""Invented files, no network, credentials, model or scheduler."""
import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

spec=importlib.util.spec_from_file_location('source_tool',Path(__file__).resolve().parents[1]/'tools/aai_stage2_source_acquisition.py')
tool=importlib.util.module_from_spec(spec);spec.loader.exec_module(tool)

class Acquisition(unittest.TestCase):
    def test_approval_required_before_any_access(self):
        with patch('socket.socket',side_effect=AssertionError('no network')):
            with self.assertRaisesRegex(ValueError,'approval_required'):
                tool.acquire(Path('/unused'),Path('/unused2'))

    def test_durable_copy_and_collision(self):
        from pact.revival.gpqa_source import sources
        def fake_gpqa(path,approved=False):
            self.assertTrue(approved);path.mkdir()
            for name in (*sources.FILES,'source-receipt.json'):(path/name).write_bytes(b'invented')
        def fake_original(path,spec,download=False):
            self.assertTrue(download);(path/spec['filename']).write_bytes(b'invented-original')
        with tempfile.TemporaryDirectory() as temp, patch('socket.socket',side_effect=AssertionError('no network')):
            root=Path(temp)
            with patch.object(sources,'private_path',side_effect=Path),patch.object(sources,'acquire',side_effect=fake_gpqa),patch('pact.training.data._source_file',side_effect=fake_original):
                result=tool.acquire(root/'scratch',root/'durable',True)
                self.assertEqual(len(result['files']),9)
                self.assertFalse(result['eligibility_verified'])
                self.assertTrue((root/'durable/VERIFIED.json').exists())
                self.assertFalse((root/'durable/ACQUISITION_PENDING.json').exists())
                with self.assertRaisesRegex(ValueError,'existing_acquisition'):
                    tool.acquire(root/'scratch2',root/'durable',True)

    def test_failure_preserves_pending(self):
        from pact.revival.gpqa_source import sources
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            with patch.object(sources,'private_path',side_effect=Path),patch.object(sources,'acquire',side_effect=RuntimeError('fixture failure')):
                with self.assertRaises(RuntimeError):tool.acquire(root/'scratch',root/'durable',True)
                self.assertTrue((root/'durable/ACQUISITION_PENDING.json').exists())
                self.assertFalse((root/'durable/VERIFIED.json').exists())

    def test_cpu_wrapper(self):
        text=Path('tools/aai_stage2_source_acquisition.sbatch').read_text()
        self.assertIn('HF_TOKEN_PATH=',text)
        self.assertIn('NA100q',text)
        for forbidden in ('--nv','--gres','srun ','sbatch ','pip install','/content','cat "$PACT_TOKEN"'):
            self.assertNotIn(forbidden,text)

if __name__=='__main__':unittest.main()
