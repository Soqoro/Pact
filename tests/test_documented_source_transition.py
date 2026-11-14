import importlib.util
from pathlib import Path
import tempfile
import unittest

spec=importlib.util.spec_from_file_location('transition',Path(__file__).resolve().parents[1]/'tools/aai_documented_source_transition.py')
t=importlib.util.module_from_spec(spec);spec.loader.exec_module(t)


class SourceTransitionTests(unittest.TestCase):
    def sources(self):
        old={t.STORAGE:b'prefix\n'+t.BEFORE+b'\nsuffix\n','src/science.py':b'unchanged'}
        new={**old,t.STORAGE:old[t.STORAGE].replace(t.BEFORE,t.AFTER)}
        return old,new

    def test_exact_checksum_change_only(self):
        old,new=self.sources();r=t.compare(old,new)
        self.assertEqual(r['changed_source_files'],[t.STORAGE])
        self.assertNotEqual(r['old_source_hash'],r['new_source_hash'])

    def test_other_scientific_edits_fail(self):
        old,new=self.sources()
        for candidate in ({**new,'src/science.py':b'changed'},
                          {**new,t.STORAGE:new[t.STORAGE]+b'# another edit'}):
            with self.assertRaises(ValueError):t.compare(old,candidate)

    def test_additions_deletions_and_no_fix_fail(self):
        old,new=self.sources()
        for candidate in ({**new,'src/extra.py':b'new'}, {t.STORAGE:new[t.STORAGE]},old):
            with self.assertRaises(ValueError):t.compare(old,candidate)

    def test_inactive_guard_rejects_uncertain_attempts_and_symlinks(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);t.inactive(root)
            (root/'attempts').mkdir();attempt=root/'attempts/a.json'
            attempt.write_text('{}')
            with self.assertRaises(ValueError):t.inactive(root)
            attempt.unlink();attempt.symlink_to(root/'missing')
            with self.assertRaises(ValueError):t.inactive(root)

    def test_inactive_guard_rejects_preflight_or_policy_activation(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            for n in ('execution-preflight.json','policy-lock.json','policies.json'):
                p=root/n;p.write_text('{}')
                with self.assertRaises(ValueError):t.inactive(root)
                p.unlink()


if __name__=='__main__':unittest.main()
