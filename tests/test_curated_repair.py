import contextlib
import dataclasses as dc
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from pact.cli import main,parser
from pact.protocol import Protocol,private_prompt
from pact.training.collection_config import CollectionRuntime
from pact.training.curated_repair import CuratedRepairConfig,paired_contexts
from pact.util import digest,node_seed,canonical,write_json
from test_receiver import FixtureBackend
from test_receiver_plan import fixtures

class CuratedRepairTests(unittest.TestCase):
    def fixture(self):
        cfg,pool,_=fixtures();task=pool[0][0]
        backend=FixtureBackend(CollectionRuntime(digest(cfg),1729),cfg,mode='all_wrong')
        protocol=Protocol(backend.config,backend)
        packets=tuple(protocol.packet(task,i,'private',private_prompt(task,''),node_seed(i)) for i in range(3))
        donor={'task_id':task.task_id,'agent':2,'raw':canonical({'answer':'A','justification':'Stored fixture.'}),'call_hash':digest('donor')}
        return task,packets,donor,CuratedRepairConfig('a'*64,'b'*64)

    def test_one_outgoing_replacement_preserves_private_states_and_paired_seeds(self):
        task,packets,donor,cfg=self.fixture();before=canonical(packets)
        contexts=paired_contexts(task,packets,donor,cfg)
        self.assertEqual(len(contexts),4);self.assertEqual(before,canonical(packets))
        self.assertEqual({c['recipient'] for c in contexts},{0,1})
        for recipient in (0,1):
            original,curated=[c for c in contexts if c['recipient']==recipient]
            self.assertEqual(original['seeds'],curated['seeds']);self.assertEqual(len(set(curated['seeds'])),4)
            self.assertEqual(original['own_private_hash'],curated['own_private_hash'])
            self.assertEqual(original['private_state_hash'],curated['private_state_hash'])
            a=json.loads(original['messages'][1]['content']);b=json.loads(curated['messages'][1]['content'])
            self.assertEqual(a['own_private'],b['own_private']);self.assertEqual(a['trusted_task'],b['trusted_task'])
            changes=[(x,y) for x,y in zip(original['delivered'],curated['delivered']) if x!=y]
            self.assertEqual(len(changes),1);self.assertEqual(changes[0][1]['sender'],2)
            self.assertEqual(changes[0][1]['text'],donor['raw'])
            self.assertNotIn('curated_help',canonical(curated['messages']))
            self.assertNotIn(donor['call_hash'],canonical(curated['messages']))
        self.assertEqual(len({c['context_id'] for c in contexts}),4)

    def test_source_identity_train_split_and_team_size_required(self):
        task,packets,donor,cfg=self.fixture()
        for t,ps,d in [(dc.replace(task,split='validation'),packets,donor),
                       (task,packets[:2],donor),(task,packets,{**donor,'task_id':'other'}),
                       (task,packets,{**donor,'agent':3})]:
            with self.assertRaises(ValueError):paired_contexts(t,ps,d,cfg)

    def test_frozen_sampling_and_seed_recipe(self):
        _,_,_,cfg=self.fixture()
        for field,value in [('samples_per_arm',8),('generation_seed',1),('peer_order_seed',1730),('schema_version',True)]:
            with self.assertRaises(ValueError):dc.replace(cfg,**{field:value}).validate()

    def test_plan_cli_is_nonexecuting(self):
        _,_,_,cfg=self.fixture()
        with tempfile.TemporaryDirectory() as tmp,contextlib.redirect_stdout(io.StringIO()) as output:
            config=Path(tmp)/'config.json';write_json(config,cfg)
            result={'status':'curated_repair_design_only','execution_implemented':False}
            with patch('pact.training.curated_repair.curated_repair_plan',return_value=result) as make:
                self.assertEqual(main(['plan-curated-repair','--config',str(config),
                    '--receiver-bundle','receiver.zip','--private-bundle','private.zip']),0)
                make.assert_called_once()
            self.assertFalse(json.loads(output.getvalue())['execution_implemented'])
        with contextlib.redirect_stderr(io.StringIO()),self.assertRaises(SystemExit):
            parser().parse_args(['plan-curated-repair','--config','c','--receiver-bundle','r','--private-bundle','p','--execute'])
