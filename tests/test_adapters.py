import contextlib
import importlib.util
import os
import unittest

from pact.backends.transformers import inference_adapter


class Parameter:
    def __init__(self):
        self.requires_grad = True
    def requires_grad_(self, flag):
        self.requires_grad = flag


class FakeModel:
    def __init__(self):
        self.active_adapter = "distinct-a"
        self.disabled = False
        self.weights = {"distinct-a": 3.0, "distinct-b": -7.0, "base": 1.0}
        self.parameter = Parameter()
    def parameters(self):
        return [self.parameter]
    def eval(self):
        return self
    def set_adapter(self, identity):
        self.active_adapter = identity
        self.parameter.requires_grad = True
    @contextlib.contextmanager
    def disable_adapter(self):
        self.disabled = True
        try:
            yield
        finally:
            self.disabled = False
    def output(self):
        return self.weights["base" if self.disabled else self.active_adapter]


class AdapterTests(unittest.TestCase):
    def test_disable_and_restore_even_on_error(self):
        model = FakeModel()
        with inference_adapter(model, "distinct-b", True):
            self.assertEqual(model.output(), -7.0)
            self.assertFalse(model.parameter.requires_grad)
        self.assertEqual(model.output(), 3.0)
        with self.assertRaises(RuntimeError):
            with inference_adapter(model, None, True):
                self.assertEqual(model.output(), 1.0)
                raise RuntimeError("simulated model failure")
        self.assertEqual(model.active_adapter, "distinct-a")
        self.assertFalse(model.disabled)
        self.assertFalse(model.parameter.requires_grad)

    @unittest.skipUnless(os.environ.get("PACT_TEST_NEURAL") == "1", "opt-in tiny neural test; no model downloads")
    def test_real_peft_tiny_distinct_adapters(self):
        import torch
        from transformers import Qwen3Config, Qwen3ForCausalLM
        from peft import LoraConfig, get_peft_model
        torch.manual_seed(1)
        base = Qwen3ForCausalLM(Qwen3Config(vocab_size=32, hidden_size=16, intermediate_size=32,
                                          num_hidden_layers=1, num_attention_heads=2, num_key_value_heads=2,
                                          head_dim=8, max_position_embeddings=64))
        cfg = LoraConfig(r=2, lora_alpha=2, target_modules=["q_proj", "v_proj"], task_type="CAUSAL_LM")
        model = get_peft_model(base, cfg, adapter_name="a")
        model.add_adapter("b", cfg)
        with torch.no_grad():
            for name, p in model.named_parameters():
                if "lora_B" in name:
                    p.fill_(0.7 if ".a." in name else -0.4)
        inputs = torch.tensor([[1, 2, 3]])
        with inference_adapter(model, "a", True), torch.no_grad():
            a = model(inputs).logits.clone()
        with inference_adapter(model, "b", True), torch.no_grad():
            b = model(inputs).logits.clone()
        with inference_adapter(model, None, True), torch.no_grad():
            clean = model(inputs).logits.clone()
        self.assertFalse(torch.allclose(a, b))
        self.assertFalse(torch.allclose(a, clean))
        self.assertEqual(model.active_adapter, "a")
        self.assertTrue(all(not p.requires_grad for p in model.parameters()))
