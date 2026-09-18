import contextlib
import dataclasses
import io
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from pact.cli import main
from pact.datasets import fixtures
from pact.schemas import TaskLabel
from pact.training.checkpoints import encode_state, decode_state, commit_checkpoint, read_checkpoint, latest_checkpoint
from pact.training.warmstart_config import WarmstartConfig, warmstart_plan, warmstart_prompt, load_warmstart_config
from pact.util import digest, read_json, write_json


class WarmstartControlTests(unittest.TestCase):
    def test_recipe_bounds_and_exact_training_identity(self):
        cfg = load_warmstart_config(Path("experiments/warmstart_engineering.json"))
        self.assertEqual(cfg.steps_per_agent * cfg.effective_batch, 12)
        for kwargs in ({"seeds": (1,1,2)}, {"effective_batch": 0}, {"steps_per_agent": True},
                       {"learning_rate": float("nan")}, {"target_modules": ("all-linear",)},
                       {"data_manifest_hash": "main"}, {"dropout": 1.}, {"schema_version": True}):
            with self.assertRaises(ValueError):
                dataclasses.replace(cfg, **kwargs).validate()
        tasks = [dataclasses.replace(t, split="train") for t, _ in fixtures(4)]
        manifest = {"fixture": "explicit software test"}
        cfg = WarmstartConfig(digest(manifest), steps_per_agent=2, effective_batch=2)
        with patch("pact.training.warmstart_config.read_training_data", return_value=(tasks, {}, manifest, {})):
            plan = warmstart_plan(cfg, Path("unused"))[3]
            self.assertEqual(plan["total_optimizer_steps"], 6)
            self.assertEqual(plan["training_examples"], 12)
            self.assertFalse(plan["training_executed"])
            self.assertEqual(plan, warmstart_plan(cfg, Path("unused"))[3])
            for kwargs in ({"data_manifest_hash": "a"*64}, {"steps_per_agent": 3}):
                with self.assertRaises(ValueError):
                    warmstart_plan(dataclasses.replace(cfg, **kwargs), Path("unused"))

    def test_prompt_boundary_no_evaluator_fields(self):
        task, label = fixtures(2)[0]
        with self.assertRaises(ValueError):
            warmstart_prompt(task)
        prompt = warmstart_prompt(dataclasses.replace(task, split="train"))
        self.assertNotIn("label", prompt[1].content)
        self.assertNotIn("scenario", prompt[1].content)
        self.assertNotIn("source_hash", prompt[1].content)
        self.assertIn('"trusted_task"', prompt[1].content)
        with self.assertRaises((ValueError, AttributeError, TypeError)):
            warmstart_prompt(label)

    def test_typed_checkpoint_tree_without_pickle(self):
        class Tensor:
            pass
        tensor = Tensor()
        state = {"state": {0: {"step": tensor, "lr": 0.001}}, "rng": (3, (1,2,3), None), "list": [True, 0]}
        tree, tensors = encode_state(state, lambda x: isinstance(x, Tensor))
        self.assertEqual(decode_state(tree, tensors), state)
        for invalid in (float("nan"), object(), {"set"}):
            with self.assertRaises(ValueError):
                encode_state(invalid, lambda x: False)
        with self.assertRaises(ValueError):
            decode_state(tree, {})
        with self.assertRaises(ValueError):
            decode_state(tree, {**tensors, "extra": tensor})
        with self.assertRaises(ValueError):
            decode_state({"dict": [["same", 1], ["same", 2]]}, {})

    def test_targets_change_without_changing_prompt_and_overflow_fails(self):
        from pact.training.warmstart import prepare_examples
        class Tokenizer:
            eos_token_id = 0
            def apply_chat_template(self, messages, **kwargs):
                if kwargs != {"tokenize": False, "add_generation_prompt": True, "enable_thinking": False}:
                    raise AssertionError("Unexpected rendering policy")
                return "\n".join(m["content"] for m in messages) + "\nassistant:"
            def encode(self, text, **kwargs):
                return [ord(c)+1 for c in text]
        task = dataclasses.replace(fixtures(2)[0][0], split="train")
        cfg = WarmstartConfig("a"*64)
        a = prepare_examples(Tokenizer(), [task], {task.task_id: TaskLabel(task.task_id, "A")}, cfg)[0]
        b = prepare_examples(Tokenizer(), [task], {task.task_id: TaskLabel(task.task_id, "B")}, cfg)[0]
        self.assertEqual(a["prompt"], b["prompt"])
        self.assertEqual(a["prompt_ids"], b["prompt_ids"])
        self.assertNotEqual(a["completion_ids"], b["completion_ids"])
        self.assertEqual(a["completion_ids"][-1], 0)
        with self.assertRaises(ValueError):
            prepare_examples(Tokenizer(), [task], {task.task_id: TaskLabel(task.task_id, "A")}, dataclasses.replace(cfg, context_limit=8))

    def test_resume_recipe_change_rejected_before_model_loading(self):
        from pact.training.warmstart import run_warmstart
        cfg = WarmstartConfig("a"*64)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_json(root / "run.json", {"recipe_hash": "incompatible"})
            with patch("pact.training.warmstart.warmstart_plan", return_value=([], {}, [], {"data_manifest_hash": "a"*64})), \
                    patch("pact.backends.transformers.TransformersBackend") as backend:
                with self.assertRaisesRegex(ValueError, "before model load"):
                    run_warmstart(cfg, root, root, root, resume=True)
                backend.assert_not_called()

    def test_atomic_checkpoint_integrity_sequence_and_identity(self):
        identity = {"config": "pinned", "data": "train", "model": "base", "runtime": "cpu", "source": "code"}
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            callback = lambda p: p.write_bytes(b"explicit fixture, not neural tensors")
            p0 = commit_checkpoint(root, step=0, identity=identity, tree={}, write_tensors=callback)
            p1 = commit_checkpoint(root, step=1, identity=identity, tree={}, write_tensors=callback)
            self.assertEqual(latest_checkpoint(root, identity)[0], p1)
            for field in identity:
                with self.assertRaises(ValueError):
                    read_checkpoint(p1, {**identity, field: "changed"})
            with self.assertRaises(ValueError):
                commit_checkpoint(root, step=1, identity=identity, tree={}, write_tensors=callback)
            with self.assertRaises(RuntimeError):
                commit_checkpoint(root, step=2, identity=identity, tree={},
                                  write_tensors=lambda p: (_ for _ in ()).throw(RuntimeError("interrupted")))
            self.assertFalse((root / "step-000002").exists())
            self.assertEqual(latest_checkpoint(root, identity)[0], p1)
            (p0 / "tensors.safetensors").write_bytes(b"corrupt")
            with self.assertRaises(ValueError):
                latest_checkpoint(root, identity)

    def test_dry_run_never_loads_model_or_creates_run(self):
        tasks = [dataclasses.replace(t, split="train") for t, _ in fixtures(4)]
        manifest = {"fixture": True}
        cfg = WarmstartConfig(digest(manifest), steps_per_agent=1, effective_batch=2)
        with tempfile.TemporaryDirectory() as tmp, contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            root = Path(tmp)
            write_json(root / "config.json", cfg)
            args = ["warmstart", "--config", str(root / "config.json"), "--data-dir", "unused", "--run-dir", str(root / "run")]
            with patch("pact.training.warmstart_config.read_training_data", return_value=(tasks, {}, manifest, {})), \
                    patch("pact.training.warmstart.run_warmstart") as execute:
                self.assertEqual(main(args), 0)
                self.assertEqual(main(args + ["--resume"]), 2)
                self.assertEqual(main(args + ["--stop-after", "0", "--execute"]), 2)
                execute.assert_not_called()
            self.assertFalse((root / "run").exists())


@unittest.skipUnless(os.environ.get("PACT_TEST_NEURAL") == "1", "explicit opt-in tiny CPU model; no pretrained weights")
class WarmstartNeuralTests(unittest.TestCase):
    def test_update_isolation_and_exact_resume_with_dropout(self):
        import torch
        from transformers import Qwen3Config, Qwen3ForCausalLM
        from pact.training.warmstart import create_adapters, adapter_parameters, train_adapters, export_references, training_adapter
        from peft import PeftModel
        torch.set_num_threads(1)
        cfg = WarmstartConfig("a"*64, rank=2, alpha=2, steps_per_agent=2, effective_batch=2,
                              learning_rate=0.001, context_limit=64, dropout=0.2)
        def base():
            torch.manual_seed(99)
            return Qwen3ForCausalLM(Qwen3Config(vocab_size=32, hidden_size=16, intermediate_size=32,
                    num_hidden_layers=1, num_attention_heads=2, num_key_value_heads=2, head_dim=8,
                    max_position_embeddings=64, attention_dropout=0.1))
        def model():
            value = create_adapters(base(), cfg)
            value.config.use_cache = False
            value.gradient_checkpointing_enable(gradient_checkpointing_kwargs={"use_reentrant": False})
            return value
        examples = [{"task_id": f"fixture-{j}", "input_ids": [1,2,3+j,4,0],
                     "attention_mask": [1]*5, "completion_mask": [0,0,0,1,1]} for j in range(4)]
        orders = [[0,1,2,3], [3,2,1,0], [0,2,1,3]]
        identity = {"kind": "random_tiny_model_fixture", "config": digest(cfg), "examples": digest(examples)}
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            uninterrupted = model()
            initial = {n: p.detach().clone() for n, p in uninterrupted.named_parameters()}
            with self.assertRaises(RuntimeError):
                with training_adapter(uninterrupted, "agent1"):
                    self.assertTrue(all(not p.requires_grad for n, p in uninterrupted.named_parameters()
                                        if n not in adapter_parameters(uninterrupted, "agent1")))
                    raise RuntimeError("simulated failure")
            self.assertTrue(all(not p.requires_grad for p in uninterrupted.parameters()))
            full = train_adapters(uninterrupted, examples, orders, cfg, root / "full", identity)
            interrupted = model()
            partial = train_adapters(interrupted, examples, orders, cfg, root / "split", identity, stop_after=1)
            self.assertEqual(partial["completed_steps"], 1)
            for n, p in interrupted.named_parameters():
                if n not in adapter_parameters(interrupted, "agent0"):
                    self.assertTrue(torch.equal(p, initial[n]), n)
            resumed = model()  # Different process-like model/optimizer objects, not in-memory continuation.
            outcome = train_adapters(resumed, examples, orders, cfg, root / "split", identity, resume=True)
            self.assertEqual(full, outcome)
            active = adapter_parameters(resumed)
            for n, p in resumed.named_parameters():
                self.assertTrue(torch.equal(p, dict(uninterrupted.named_parameters())[n]), n)
                if n not in active:
                    self.assertTrue(torch.equal(p, initial[n]), n)
            for agent in ("agent0", "agent1", "agent2"):
                self.assertTrue(any(not torch.equal(p, initial[n]) for n, p in adapter_parameters(resumed, agent).items()))
            refs = export_references(resumed, root / "split", identity, 6)
            self.assertEqual(refs, export_references(resumed, root / "split", identity, 6))
            restored = PeftModel.from_pretrained(base(), root / "split" / "references" / "agent0", adapter_name="agent0", is_trainable=False)
            for n, p in adapter_parameters(restored, "agent0").items():
                self.assertTrue(torch.equal(p, active[n]), n)
            self.assertTrue(all(not p.requires_grad for p in resumed.parameters()))
            with torch.no_grad():
                next(iter(active.values())).add_(1.)
            with self.assertRaisesRegex(ValueError, "reference weights differ"):
                export_references(resumed, root / "split", identity, 6)
