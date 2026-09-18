import contextlib
import dataclasses
import io
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

from pact.cli import main
from pact.datasets import _normalize, normalize, parse_arc, parse_logiqa, SOURCES
from pact.training.data import (TRAIN_SOURCES, ARTIFACT_FILES, _source_file, parse_arc_train,
                                parse_logiqa_train, load_training_sources, audit_training_overlap,
                                select_training, prepare_training_data, read_training_data)
from pact.util import digest, file_hash, read_json, write_json


def record(family, source_id, split, question, *, context="", reverse=False, answer="first"):
    source = (TRAIN_SOURCES if split == "train" else SOURCES)[family]
    choices = [("first", "blue planet"), ("second", "red desert")]
    if reverse:
        choices.reverse()
    return _normalize(family=family, source_id=source_id, revision=source["revision"],
                      source_hash=source["sha256"], question=question, choices=choices,
                      answer=answer, context=context, split=split)


def pools():
    training, validation = [], []
    for family in TRAIN_SOURCES:
        for i, word in enumerate(("apple", "grape", "pear", "lemon")):
            training.append(record(family, f"train-{i}", "train", f"{family} {word} question {i}"))
        validation.append(record(family, "eval-0", "validation", f"{family} wholly different evaluation prompt"))
    return training, validation


class TrainingDataTests(unittest.TestCase):
    def test_train_parsers_preserve_labels_and_validation_boundary(self):
        row = {"id": "test-id", "question": "Question", "choices": {"label": ["z", "q"], "text": ["one", "two"]}, "answerKey": "q"}
        train, label = parse_arc_train([row], "hash")[0]
        validation, old_label = parse_arc([row], "hash")[0]
        self.assertEqual(train.split, "train")
        self.assertEqual(dataclasses.replace(train, split="validation"), validation)
        self.assertEqual(label, old_label)
        self.assertEqual(train.options[1].source_label, "q")
        self.assertNotIn("answerKey", dataclasses.asdict(train))
        text = "\nb\nContext\nQuestion\nA.One\nB.Two\nC.Three\nD.Four\n"
        train, label = parse_logiqa_train(text, "hash")[0]
        old, _ = parse_logiqa(text, "hash")[0]
        self.assertEqual(train.source_id, "train-0000")
        self.assertEqual(old.source_id, "eval-0000")
        self.assertNotEqual(train.task_id, old.task_id)
        self.assertEqual(label.answer_id, "B")
        with self.assertRaises(ValueError):
            normalize(family="f", source_id="1", revision="r", source_hash="h", question="Q",
                      choices=[("a", "one"), ("b", "two")], answer="a", split="train")
        with self.assertRaises(ValueError):
            parse_logiqa_train(text.replace("\nb\n", "\nB\n"), "hash")

    def test_cross_split_ids_and_reordered_content_exclude_training(self):
        a = record("arc_challenge", "same-id", "train", "original text")
        b = record("arc_challenge", "same-id", "validation", "changed text")
        c = record("logiqa", "train-1", "train", "EXACT, question!")
        d = record("logiqa", "eval-2", "validation", "exact question", reverse=True)
        eligible, audit = audit_training_overlap([a, c], [b, d])
        self.assertEqual(eligible, [])
        self.assertEqual(len(audit["exclusions"]), 2)
        self.assertEqual({x["reason"] for x in audit["exclusions"]}, {"validation_overlap"})
        self.assertEqual(audit["label_conflicts"], [])  # Compare gold text, not canonical option position.
        self.assertEqual({x["reason"] for x in audit["edges"]}, {"source_id", "normalized_content"})

    def test_train_duplicates_conflicts_and_lexical_copy(self):
        a = record("arc_challenge", "a", "train", "matching prompt")
        b = record("arc_challenge", "b", "train", "matching prompt", reverse=True)
        validation = record("logiqa", "eval", "validation", "unrelated external task")
        eligible, audit = audit_training_overlap([b, a], [validation])
        self.assertEqual([p[0][0].task_id for p in eligible], [a[0].task_id])
        self.assertEqual(audit["exclusions"][0]["reason"], "duplicate_training_group")
        wrong = record("arc_challenge", "b", "train", "matching prompt", answer="second")
        eligible, audit = audit_training_overlap([a, wrong], [validation])
        self.assertEqual(eligible, [])
        self.assertEqual({x["reason"] for x in audit["exclusions"]}, {"conflicting_duplicate_labels"})
        words = [f"word{i}" for i in range(100)]
        a = record("logiqa", "train-a", "train", "Reason about these facts", context=" ".join(words))
        words[50] = "changed"
        b = record("logiqa", "train-b", "train", "Reason about these facts", context=" ".join(words))
        words[60] = "changed_again"
        c = record("logiqa", "eval", "validation", "Reason about these facts", context=" ".join(words))
        eligible, audit = audit_training_overlap([a, b], [c])
        self.assertEqual(eligible, [])
        self.assertTrue(any(e["reason"] == "lexical_near_duplicate" for e in audit["edges"]))
        self.assertTrue(audit["semantic_paraphrase_audit"].startswith("not_run"))
        self.assertEqual(audit_training_overlap([b, a], [c]), audit_training_overlap([a, b], [c]))

    def test_determinism_balance_nested_selection_and_provenance(self):
        train, validation = pools()
        small = select_training(train, validation, items=4, seed=17)
        large = select_training(train, validation, items=8, seed=17)
        self.assertEqual(small, select_training(list(reversed(train)), validation, items=4, seed=17))
        self.assertTrue({t.task_id for t in small[0]} <= {t.task_id for t in large[0]})
        self.assertEqual(small[2]["family_counts"], {"arc_challenge": 2, "logiqa": 2})
        self.assertTrue(all(t.split == "train" for t in small[0]))
        self.assertEqual(small[2]["overlap_audit_hash"], digest(small[3]))
        with self.assertRaises(ValueError):
            select_training(train, validation, items=10, seed=17)
        with self.assertRaises(ValueError):
            audit_training_overlap([(dataclasses.replace(train[0][0], split="test"), train[0][1])], validation)
        with self.assertRaises(ValueError):
            audit_training_overlap(train + [train[0]], validation)
        with self.assertRaises(ValueError):
            select_training(train, [], items=4, seed=17)

    def test_cache_offline_checksum_and_download_bounds(self):
        import hashlib
        data = b"fixture source"
        source = {"filename": "source.txt", "url": "https://example.invalid/source", "sha256": hashlib.sha256(data).hexdigest()}
        with tempfile.TemporaryDirectory() as tmp, patch("pact.training.data.urllib.request.urlopen") as fetch:
            root = Path(tmp)
            with self.assertRaises(FileNotFoundError):
                _source_file(root, source, download=False)
            fetch.assert_not_called()
            fetch.return_value.__enter__.return_value.read.return_value = b"corrupted"
            with self.assertRaises(ValueError):
                _source_file(root, source, download=True)
            self.assertFalse((root / "source.txt").exists())
            fetch.return_value.__enter__.return_value.read.return_value = data
            self.assertEqual(_source_file(root, source, download=True).read_bytes(), data)
            fetch.reset_mock()
            self.assertEqual(_source_file(root, source, download=False).read_bytes(), data)
            fetch.assert_not_called()
            (root / "source.txt").write_bytes(b"modified")
            with self.assertRaises(ValueError):
                _source_file(root, source, download=True)
            fetch.assert_not_called()  # Never silently replace an incompatible cached source.

    def test_official_count_check_and_no_test_source(self):
        table = MagicMock()
        table.read_table.return_value.to_pylist.return_value = []
        with patch.dict("sys.modules", {"pyarrow": MagicMock(), "pyarrow.parquet": table}), \
                patch("pact.training.data._source_file", return_value=Path("unused")), \
                patch("pact.training.data.parse_arc_train", return_value=[]):
            with self.assertRaisesRegex(ValueError, "row count"):
                load_training_sources(Path("unused"))
        self.assertTrue(all("test" not in s["official_split"].lower() for s in TRAIN_SOURCES.values()))
        self.assertEqual(TRAIN_SOURCES["logiqa"]["expected_rows"], 7376)

    def test_manifest_roundtrip_integrity_and_no_overwrite(self):
        with tempfile.TemporaryDirectory() as tmp, patch("pact.training.data.load_training_sources", return_value=pools()):
            root = Path(tmp) / "prepared"
            result = prepare_training_data(Path(tmp), root, items=4, seed=17)
            tasks, labels, manifest, audit = read_training_data(root)
            self.assertEqual(result["manifest_hash"], digest(manifest))
            self.assertEqual(len(tasks), 4)
            self.assertEqual(set(labels), {t.task_id for t in tasks})
            with self.assertRaises(ValueError):
                prepare_training_data(Path(tmp), root, items=4, seed=17)
            path = root / "tasks.json"
            data = read_json(path)
            data[0]["split"] = "validation"
            write_json(path, data)
            with self.assertRaisesRegex(ValueError, "checksum"):
                read_training_data(root)
            checksums = read_json(root / "checksums.json")
            checksums["tasks.json"] = file_hash(path)
            write_json(root / "checksums.json", checksums)
            with self.assertRaisesRegex(ValueError, "provenance"):
                read_training_data(root)

    def test_cli_roundtrip_and_rejection_before_fetch(self):
        with tempfile.TemporaryDirectory() as tmp, patch("pact.training.data.load_training_sources", return_value=pools()) as loader, \
                contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            root = Path(tmp) / "cli"
            args = ["prepare-training-data", "--cache-dir", tmp, "--output-dir", str(root), "--seed", "17", "--items"]
            self.assertEqual(main([*args, "3", "--download"]), 2)
            loader.assert_not_called()
            self.assertEqual(main([*args, "4"]), 0)
            self.assertEqual(main(["inspect-training-data", "--data-dir", str(root)]), 0)
            self.assertEqual(main([*args, "4"]), 2)
            (root / "checksums.json").unlink()
            self.assertEqual(main(["inspect-training-data", "--data-dir", str(root)]), 2)

    def test_completion_marker_follows_payload_validation(self):
        with tempfile.TemporaryDirectory() as tmp, patch("pact.training.data.load_training_sources", return_value=pools()), \
                patch("pact.training.data._validate_payloads", side_effect=ValueError("simulated failure")):
            root = Path(tmp) / "incomplete"
            with self.assertRaises(ValueError):
                prepare_training_data(Path(tmp), root, items=4, seed=17)
            self.assertTrue(all((root / name).exists() for name in ARTIFACT_FILES))
            self.assertFalse((root / "checksums.json").exists())
