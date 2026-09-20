import contextlib
import copy
import dataclasses as dc
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from pact.cli import main,parser
from pact.training.actor_preparation import ActorPreparationConfig,select_preparation_tasks
from pact.util import digest,write_json
from test_receiver_plan import fixtures


class ActorPreparationTests(unittest.TestCase):
    def fixture(self):
        _,pool,warm=fixtures();tasks,_,manifest,_=pool
        probes=manifest['selected'][20:32]+manifest['selected'][620:632]
        return tasks,manifest,warm[2],probes

    def test_balanced_nested_selection_excludes_probe_groups_and_ignores_input_order(self):
        tasks,manifest,warm,probes=self.fixture()
        selected=select_preparation_tasks(tasks,manifest,warm,probes,20260920)
        self.assertEqual(len(selected),120)
        ids={e['task_id'] for e in selected}
        self.assertTrue({e['task_id'] for e in warm['selected']}<=ids)
        self.assertFalse(ids & {e['task_id'] for e in probes})
        for f in ('arc_challenge','logiqa'):
            self.assertEqual(sum(t.family==f and t.task_id in ids for t in tasks),60)
        reordered={**manifest,'selected':list(reversed(manifest['selected']))}
        self.assertEqual(selected,select_preparation_tasks(list(reversed(tasks)),reordered,warm,list(reversed(probes)),20260920))
        # A different task in a probe's lexical component must also be excluded.
        candidate=next(e for e in selected if e not in warm['selected'])
        changed=copy.deepcopy(manifest)
        next(e for e in changed['selected'] if e['task_id']==candidate['task_id'])['group_id']=probes[0]['group_id']
        new=select_preparation_tasks(tasks,changed,warm,probes,20260920)
        self.assertNotIn(candidate['task_id'],{e['task_id'] for e in new})

    def test_overlap_tamper_split_and_short_pool_rejected(self):
        tasks,manifest,warm,probes=self.fixture()
        with self.assertRaises(ValueError):select_preparation_tasks(tasks,manifest,warm,probes[:-1]+[warm['selected'][0]],20260920)
        changed=list(tasks);changed[0]=dc.replace(changed[0],split='validation')
        with self.assertRaises(ValueError):select_preparation_tasks(changed,manifest,warm,probes,20260920)
        changed=copy.deepcopy(warm);changed['selected'][0]['label_hash']=digest('changed')
        with self.assertRaises(ValueError):select_preparation_tasks(tasks,manifest,changed,probes,20260920)
        limited=tasks[:40]+tasks[600:640];short={**manifest,'selected':manifest['selected'][:40]+manifest['selected'][600:640]}
        with self.assertRaises(ValueError):select_preparation_tasks(limited,short,warm,probes,20260920)

    def test_config_is_fixed_and_cli_cannot_execute(self):
        cfg=ActorPreparationConfig(*['a'*64]*5)
        cfg.validate()
        for field,value in [('selection_seed',1),('schema_version',True),('purpose','train')]:
            with self.assertRaises(ValueError):dc.replace(cfg,**{field:value}).validate()
        with tempfile.TemporaryDirectory() as tmp,contextlib.redirect_stdout(io.StringIO()) as output:
            path=Path(tmp)/'config.json';write_json(path,cfg)
            args=['plan-actor-preparation','--config',str(path)]
            for name in ('data-dir','warmstart-data-dir','receiver-bundle','private-bundle','curated-bundle'):
                args+=['--'+name,'unused']
            result={'execution_implemented':False,'training_executed':False,'model_calls_executed':0}
            with patch('pact.training.actor_preparation.actor_preparation_plan',return_value=result):
                self.assertEqual(main(args),0)
            self.assertEqual(json.loads(output.getvalue()),result)
            with contextlib.redirect_stderr(io.StringIO()),self.assertRaises(SystemExit):parser().parse_args(args+['--execute'])
