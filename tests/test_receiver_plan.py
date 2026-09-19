import contextlib
import copy
import dataclasses
import io
from collections import Counter
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from pact.cli import main
from pact.schemas import TaskInput, TaskLabel, Option
from pact.training.receiver_plan import ReceiverFeasibilityConfig, receiver_feasibility_plan
from pact.util import digest, write_json


def fixtures():
    """Invented provenance for planner tests; never scientific evidence."""
    tasks, labels, entries = [], {}, []
    for family in ('arc_challenge', 'logiqa'):
        for i in range(600):
            key = f'{family}:train-{i:04}'
            task = TaskInput(key, family, 'train', str(i), '0'*40, digest(family),
                f'Fixture {key}', (Option('A','One','A'), Option('B','Two','B')))
            tasks.append(task); labels[key] = TaskLabel(key, 'A')
            entries.append({'task_id':key, 'source_id':str(i), 'group_id':digest(['group',key]),
                'content_group':digest(['content',key]), 'input_hash':digest(task), 'label_hash':digest(labels[key])})
    manifest = {'selected':entries, 'training_pool_hash':digest('train'),
        'validation_pool_hash':digest('validation'), 'overlap_audit_hash':digest('audit'), 'sources':{'fixture':True}}
    warm_tasks = tasks[:6]+tasks[600:606]
    warm_ids = {t.task_id for t in warm_tasks}
    warm_manifest = {**manifest, 'selected':[e for e in entries if e['task_id'] in warm_ids]}
    pool = (tasks, labels, manifest, {})
    warm = (warm_tasks, {k:v for k,v in labels.items() if k in warm_ids}, warm_manifest, {})
    config = ReceiverFeasibilityConfig(digest(manifest), digest(warm_manifest), digest('reference-manifest'),
        tuple(digest(['adapter',i]) for i in range(3)), digest('base'), digest('runtime'))
    return config, pool, warm


class ReceiverPlanTests(unittest.TestCase):
    def plan(self, config, pool, warm, selection=None):
        with patch('pact.training.receiver_plan.read_training_data', side_effect=[pool, warm]):
            return receiver_feasibility_plan(config, 'pool', 'warm', selection)

    def test_determinism_exclusion_and_family_sender_balance(self):
        config, pool, warm = fixtures()
        plan = self.plan(config,pool,warm)
        self.assertEqual(plan,self.plan(config,pool,warm))
        selected = plan['selection']['selected']
        self.assertEqual(Counter(e['family'] for e in selected), {'arc_challenge':12,'logiqa':12})
        self.assertTrue({e['task_id'] for e in selected}.isdisjoint(t.task_id for t in warm[0]))
        for family in ('arc_challenge','logiqa'):
            self.assertEqual(Counter(e['exchange_sender'] for e in selected if e['family']==family),{0:4,1:4,2:4})
        self.assertEqual([e['position'] for e in selected],list(range(24)))
        self.assertTrue(plan['execution_implemented'])

    def test_selection_does_not_use_order_labels_or_outcomes(self):
        config,pool,warm=fixtures()
        expected=self.plan(config,pool,warm)['selection']['selected']
        reordered=(list(reversed(pool[0])),pool[1],pool[2],pool[3])
        self.assertEqual(expected,self.plan(config,reordered,warm)['selection']['selected'])
        # Changing allowed training targets changes pins, but never selection ranks.
        pool=copy.deepcopy(pool)
        excluded={t.task_id for t in warm[0]}
        for entry in pool[2]['selected']:
            if entry['task_id'] not in excluded:
                label=TaskLabel(entry['task_id'],'B');pool[1][entry['task_id']]=label
                entry['label_hash']=digest(label)
        changed=self.plan(dataclasses.replace(config,data_manifest_hash=digest(pool[2])),pool,warm)
        self.assertEqual([e['task_id'] for e in expected],
                         [e['task_id'] for e in changed['selection']['selected']])

    def test_changed_selection_or_source_is_rejected(self):
        config,pool,warm=fixtures()
        selection=self.plan(config,pool,warm)['selection']
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'selection.json';write_json(path,selection)
            self.plan(config,pool,warm,path)
            selection['selected'][0]['exchange_sender']=2
            write_json(path,selection)
            with self.assertRaisesRegex(ValueError,'Frozen task selection'):
                self.plan(config,pool,warm,path)
        with self.assertRaisesRegex(ValueError,'manifest differs'):
            self.plan(dataclasses.replace(config,data_manifest_hash=digest('wrong')),pool,warm)
        warm=copy.deepcopy(warm);warm[2]['validation_pool_hash']=digest('other')
        with self.assertRaisesRegex(ValueError,'audited source pools'):
            self.plan(dataclasses.replace(config,warmstart_data_manifest_hash=digest(warm[2])),pool,warm)

    def test_validation_relabel_duplicate_groups_and_changed_warmstart_rejected(self):
        config,pool,warm=fixtures()
        invalid=copy.deepcopy(pool)
        invalid[0][30]=dataclasses.replace(invalid[0][30],split='validation')
        with self.assertRaisesRegex(ValueError,'train-only'):self.plan(config,invalid,warm)
        invalid=copy.deepcopy(pool)
        invalid[2]['selected'][30]['group_id']=invalid[2]['selected'][31]['group_id']
        with self.assertRaisesRegex(ValueError,'repeated audited groups'):
            self.plan(dataclasses.replace(config,data_manifest_hash=digest(invalid[2])),invalid,warm)
        invalid=copy.deepcopy(warm);invalid[2]['selected'][0]['input_hash']=digest('changed')
        with self.assertRaisesRegex(ValueError,'unchanged subset'):
            self.plan(dataclasses.replace(config,warmstart_data_manifest_hash=digest(invalid[2])),pool,invalid)

    def test_caps_and_fixed_design_cannot_silently_expand(self):
        config,pool,warm=fixtures();budget=self.plan(config,pool,warm)['budget']
        self.assertEqual((budget['records'],budget['receiver_contexts_maximum']),(48,144))
        self.assertEqual(budget['generation_calls_upper_bound'],336+144*4)
        self.assertEqual(budget['generated_tokens_upper_bound'],48*(6*256+64)+144*4*256)
        self.assertEqual(budget['input_tokens_upper_bound']+budget['generated_tokens_upper_bound'],912*4096)
        self.assertEqual(budget['teacher_forced_forwards'],0)
        for kwargs in ({'items':48},{'receiver_candidates':8},{'conditions':('clean','early','exchange')},
                       {'schema_version':True},{'selection_seed':True},{'generation_seed':-1},
                       {'reference_hashes':(digest('same'),)*3}):
            with self.assertRaises(ValueError):dataclasses.replace(config,**kwargs).validate()

    def test_plan_cli_is_read_only_and_has_no_execute_mode(self):
        config,pool,warm=fixtures();selection=self.plan(config,pool,warm)['selection']
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);write_json(root/'config.json',config);write_json(root/'selection.json',selection)
            argv=['plan-receiver-feasibility','--config',str(root/'config.json'),'--data-dir','absent-pool',
                '--warmstart-data-dir','absent-warm','--selection',str(root/'selection.json')]
            before={p.name:p.read_bytes() for p in root.iterdir()}
            with patch('pact.training.receiver_plan.read_training_data',side_effect=[pool,warm]), \
                 patch('pact.backends.transformers.TransformersBackend') as backend, \
                 contextlib.redirect_stdout(io.StringIO()) as output:
                self.assertEqual(main(argv),0);backend.assert_not_called()
            self.assertIn('receiver_feasibility_plan_only',output.getvalue())
            self.assertEqual(before,{p.name:p.read_bytes() for p in root.iterdir()})
            with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
                main([*argv,'--execute'])
