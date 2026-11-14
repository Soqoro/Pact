import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from pact.util import digest, read_json, write_json
from pact.revival.allocation_v3 import storage

spec=importlib.util.spec_from_file_location('apply_transition',Path(__file__).resolve().parents[1]/'tools/aai_apply_documented_source_transition.py')
t=importlib.util.module_from_spec(spec);spec.loader.exec_module(t)


class ApplyTransitionTests(unittest.TestCase):
    def test_successor_changes_only_two_fields_and_preserves_old(self):
        old={'source_code':{'git_commit':'old'},'scratch_root':'/local/old',
             'execution_authorized_by_plan':False,'historical_spending':None,
             's0':{'Q':'frozen'},'freeze':{'candidate':'frozen'},'budgets':{'generation':23728},
             'training_source':{'labels':{'invented':'A'}},'analysis':{'unchanged':True}}
        before=digest(old);new=t.successor(old,t.TARGET,Path('/local/new'))
        self.assertEqual(digest(old),before)
        self.assertEqual({k for k in old if old[k]!=new[k]},{'source_code','scratch_root'})
        self.assertFalse(new['execution_authorized_by_plan']);self.assertIsNone(new['historical_spending'])
        new['training_source']['labels']['invented']='B'
        self.assertEqual(old['training_source']['labels']['invented'],'A')

    def test_activated_or_zero_history_plan_rejected(self):
        base={'source_code':{},'scratch_root':'/local/old','execution_authorized_by_plan':False,'historical_spending':None}
        for changes in ({'execution_authorized_by_plan':True},{'historical_spending':0}):
            with self.assertRaises(ValueError):t.successor({**base,**changes},t.TARGET,Path('/local/new'))

    def test_scoped_inactivity_rejects_attempts_and_activated_metadata(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);t.assert_inactive(root)
            write_json(root/'attempts/unknown.json',{})
            with self.assertRaises(ValueError):t.assert_inactive(root)
            (root/'attempts/unknown.json').unlink()
            write_json(root/'execution-preflight.json',{})
            with self.assertRaises(ValueError):t.assert_inactive(root)

    def test_durable_inactive_snapshot_verified_and_latest_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            base=Path(tmp);root=base/'scratch/fixture';durable=base/'durable/fixture'
            p={'run_id':'fixture','fixture':True};write_json(root/'plan.json',p)
            storage.persist(root,durable)
            latest=sorted((durable/'snapshots').iterdir())[-1]
            with patch.object(t,'OLD_PLAN',digest(p)),patch.object(t,'OLD_SNAPSHOT',latest.name):
                self.assertEqual(len(t.verify_durable(durable)),64)
                write_json(durable/'INFLIGHT.json',{})
                with self.assertRaises(ValueError):t.verify_durable(durable)
                (durable/'INFLIGHT.json').unlink()
                (durable/'snapshots/99999999999999999999-unknown').mkdir()
                with self.assertRaises(ValueError):t.verify_durable(durable)


if __name__=='__main__':unittest.main()
