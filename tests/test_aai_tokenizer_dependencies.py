import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location('tokenizer_fix', Path(__file__).resolve().parents[1] / 'tools/aai_tokenizer_dependencies.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


class DependencyRepairTests(unittest.TestCase):
    def test_exact_additions(self):
        before = {'torch': '2.11.0+cu130', 'transformers': '4.57.6'}
        m.validate_additions(before, {**before, **m.PINS})

    def test_existing_package_upgrade_rejected(self):
        before = {'transformers': '4.57.6'}
        with self.assertRaises(ValueError):
            m.validate_additions(before, {**m.PINS, 'transformers': '5.0.0'})

    def test_extra_install_rejected(self):
        with self.assertRaises(ValueError):
            m.validate_additions({}, {**m.PINS, 'tiktoken': 'unrequested'})

    def test_preexisting_optional_dependency_rejected(self):
        with self.assertRaises(ValueError):
            m.validate_additions({'sentencepiece': '0.2.1'}, m.PINS)


if __name__ == '__main__':
    unittest.main()
