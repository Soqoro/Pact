import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'tools'))
import aai_documented_evaluation_smoke as smoke


class SmokeReview(unittest.TestCase):
    def test_accepted_attack_controls_full_trajectory_and_cap(self):
        for accepted in (0, 1, 2):
            with self.subTest(accepted=accepted), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                for directory in ('attempts', 'events/shards', 'attacks/policy'):
                    (root/directory).mkdir(parents=True)
                nodes = []
                for i in range(2):
                    tid = f'fixture-{i}'
                    smoke.b.save(root/'attacks/policy'/(smoke.b.digest(tid)+'.json'), {'accepted': i < accepted})
                    slots = [('shared', 'attack', 'Q', '')]
                    for team in map(str, range(11)):
                        slots.extend((team, 'private', f, '') for f in 'QLM')
                        for cond in ('clean', 'exchange'):
                            slots.extend((team, 'revision', f, cond) for f in 'QLM')
                            slots.append((team, 'final', 'R', cond))
                    for seed, (team, phase, family, condition) in enumerate(slots):
                        nodes.append(dict(team=team, task_id=tid, phase=phase, family=family,
                                          seed=seed, condition=condition))
                        if condition == 'exchange' and i >= accepted:
                            continue
                        role = 'readout' if phase == 'final' else phase
                        dep = {'scope': [role, tid] if role == 'attack' else [role, team, tid],
                               'model': {'spec': {'key': family}},
                               'request': {'phase': 'private' if phase == 'attack' else phase,
                                           'seed': seed, 'max_tokens': 512, 'task': {'task_id': tid}}}
                        identity = dict(owner=smoke.b.RUN, plan_hash=smoke.b.PLAN, part='policy',
                                        kind='generation', dependency=dep)
                        key = smoke.b.digest(identity)
                        intent = {'identity': identity, 'cost': {'generation': 1}}
                        smoke.b.save(root/'attempts'/(key+'.json'), intent)
                        path = root/'events/shards'/(key+'.json')
                        path.with_suffix('.sha256').write_text(smoke.b.save(path, {'intent': intent}))
                self.assertEqual(smoke.verify_delta(root, nodes, {}), 156 + 44 * accepted)
                nodes[0]['task_id'] = 'outside-smoke'
                with self.assertRaises(smoke.b.CheckFailed):
                    smoke.verify_delta(root, nodes, {})
