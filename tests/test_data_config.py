import dataclasses
import tempfile
import unittest
from pathlib import Path

from pact.config import Config, Limits, ModelConfig, ProbeConfig, config_from_dict, load_config, budget
from pact.datasets import fixtures, normalize, parse_arc, parse_logiqa, prepare, overlaps
from pact.parsing import parse_answer


class DataConfigTests(unittest.TestCase):
    def test_arbitrary_answer_labels_variable_choices(self):
        task, label = normalize(family="fixture", source_id="1", revision="r", source_hash="h", question="Question",
                                 choices=[("z", "first"), ("7", "second"), ("AA", "third"), ("q", "fourth"), ("!", "fifth")], answer="7")
        self.assertEqual(label.answer_id, "B")
        self.assertEqual(task.options[-1].answer_id, "E")
        self.assertEqual(task.options[1].source_label, "7")
        self.assertNotIn("answer_id", dataclasses.asdict(task))
        with self.assertRaises(ValueError):
            normalize(family="x", source_id="1", revision="r", source_hash="h", question="q", choices=[("A", "x"), ("A", "y")], answer="A")

    def test_strict_logiqa_original_format(self):
        text = "\nb\nA permitted context.\nWhich option?\nA.One\nB.Two\nC.Three\nD.Four\n"
        rows = parse_logiqa(text, "source")
        self.assertEqual(rows[0][1].answer_id, "B")
        for bad in (text[1:], text.replace("\nb\n", "\nB\n"), text.replace("D.Four", ""), text + "garbage"):
            with self.assertRaises(ValueError):
                parse_logiqa(bad, "source")
        unusual = parse_logiqa(text.replace("C.Three", "Researcher C.Wang is a doctor.").replace("D.Four", "d.Four"), "source")
        self.assertEqual(unusual[0][0].options[2].text, "Researcher C.Wang is a doctor.")
        self.assertEqual(unusual[0][0].options[3].text, "Four")

    def test_arc_strict_shape(self):
        row = {"id": "x", "question": "Question", "choices": {"label": ["1", "2", "3"], "text": ["a", "b", "c"]}, "answerKey": "3"}
        self.assertEqual(parse_arc([row], "source")[0][1].answer_id, "C")
        with self.assertRaises(ValueError):
            parse_arc([row, row], "source")
        with self.assertRaises(ValueError):
            parse_arc([{**row, "answerKey": "9"}], "source")

    def test_parser_fail_closed(self):
        good = '{"answer":"A","justification":"Because."}'
        self.assertEqual(parse_answer(good, ("A", "B"))[0], "A")
        for raw in ('```json\n' + good + '\n```', good + good, '{"answer":"A","answer":"B","justification":"x"}',
                    '{"answer":["A","B"],"justification":"x"}', '{"answer":"C","justification":"x"}',
                    '{"answer":"A","justification":""}', '{"answer":"A or B","justification":"x"}'):
            self.assertIsNone(parse_answer(raw, ("A", "B"))[0])
        self.assertEqual(parse_answer(good, ("A", "B"), stop_reason="length")[2], "length")
        self.assertEqual(parse_answer('{"answer":"ABSTAIN"}', ("A",), final=True)[2], "abstention")
        self.assertEqual(parse_answer('{"answer":"A"}', ("A",), final=True)[0], "A")

    def test_presets_validate_and_no_tests(self):
        for path in Path("configs").rglob("*.yaml"):
            config = load_config(path)
            self.assertTrue(budget(config)["trajectory_calls_upper_bound"] > 0)
        for change in ({"split": "test"}, {"items": 81}, {"items": True}, {"unexpected": 1},
                       {"methods": ["SAC"]}, {"methods": ["debate", "debate"]},
                       {"model": {"revision": "main"}}, {"model": {"enable_thinking": True}}):
            with self.assertRaises((ValueError, TypeError)):
                config_from_dict(change)

    def test_deterministic_balanced_manifest(self):
        config = Config(items=8, probe=ProbeConfig(tasks=0))
        with tempfile.TemporaryDirectory() as temp:
            a = prepare(config, Path(temp))
            b = prepare(config, Path(temp))
        self.assertEqual(a, b)
        self.assertEqual(a[2]["family_counts"], {"mock_arc": 4, "mock_logiqa": 4})
        self.assertEqual(len({t.task_id for t in a[0]}), 8)
        self.assertEqual(a[2]["split"], "validation")
        same = dataclasses.replace(a[0][0], split="train", task_id="other")
        self.assertEqual(overlaps([a[0][0]], [same])[0]["splits"], ["train", "validation"])
