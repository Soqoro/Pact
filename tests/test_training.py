from __future__ import annotations

import contextlib
import dataclasses as dc
import io
import json
import math
import os
import tempfile
import unittest
from pathlib import Path

from pact.cli import main
from pact.training.assignment import solve_assignment, standardize_answer_nll, loss_coefficients, weighted_loss
from pact.training.bank import assign_bank, bank_from_dict, read_bank
from pact.training.checks import fixture_bank
from pact.training.losses import answer_target, completion_logprob, tokenize_completion, dpo_loss
from pact.training.preferences import build_preferences
from pact.training.reference import ReferenceCache, reference_request
from pact.util import canonical, digest, read_json, write_json


class AssignmentTests(unittest.TestCase):
    def test_masked_softmax_and_empty_rows(self):
        result = solve_assignment([[0., 0.4, None], [None, None, None]], balance=0)
        expected = 1 / (1 + math.exp(-2))
        self.assertEqual(result["status"], "converged")
        self.assertAlmostEqual(result["weights"][0][0], expected, places=7)
        self.assertEqual(result["weights"][0][2], 0.)
        self.assertEqual(result["weights"][1], [0., 0., 0.])
        self.assertEqual(result["masked_mass"], 0.)
        empty = solve_assignment([[None] * 3])
        self.assertEqual(empty["status"], "no_eligible_rows")
        self.assertIsNone(empty["objective"])

    def test_balance_against_independent_coordinate_bisection(self):
        # Two binary simplexes, solved independently with scalar coordinate roots.
        # Agent 2 is wholly inaccessible; no EG or softmax code is reused.
        costs = [[0., 0.7, None], [0.9, 0., None]]
        tau, balance = 0.3, 0.8
        xs = [0.5, 0.5]
        for _ in range(100):
            for b in range(2):
                lo, hi = 1e-14, 1 - 1e-14
                for _ in range(60):
                    x = (lo + hi) / 2
                    mean = (x + xs[1 - b]) / 2
                    gradient = costs[b][0] - costs[b][1] + tau * math.log(x / (1 - x))
                    gradient += balance * math.log(mean / (1 - mean))
                    if gradient > 0:
                        hi = x
                    else:
                        lo = x
                xs[b] = (lo + hi) / 2
        result = solve_assignment(costs, tau=tau, balance=balance)
        self.assertEqual(result["status"], "converged")
        for b in range(2):
            self.assertAlmostEqual(result["weights"][b][0], xs[b], places=7)
        self.assertLessEqual(result["duality_gap"], result["tolerance"])
        self.assertLess(result["max_row_sum_error"], 1e-12)
        history = result["objective_history"]
        self.assertTrue(all(b <= a + 1e-12 for a, b in zip(history, history[1:])))

    def test_changed_support_and_nonconvergence(self):
        result = solve_assignment([[None, 0., 1.]], warm_start=[[1., 0., 0.]])
        self.assertEqual(result["weights"][0][0], 0.)
        self.assertEqual(result["status"], "converged")
        short = solve_assignment([[0., 1., 2.]], max_iterations=1, tolerance=1e-14)
        self.assertEqual(short["status"], "not_converged")
        for costs in ([[float("nan"), 0.]], [[0.], [1., 2.]]):
            with self.assertRaises(ValueError):
                solve_assignment(costs)

    def test_snapshot_global_normalization(self):
        values, stats = standardize_answer_nll([[0., 1.], [2., 3.]], split="train", snapshot="s", bank_hash="b")
        self.assertAlmostEqual(sum(sum(r) for r in values), 0.)
        self.assertAlmostEqual(sum(x*x for r in values for x in r) / 4, 1.)
        self.assertEqual(stats["count"], 4)
        same, stats = standardize_answer_nll([[2., 2.]], split="train", snapshot="s", bank_hash="b")
        self.assertEqual(same, [[0., 0.]])
        self.assertTrue(stats["constant_bank"])
        raw, _ = standardize_answer_nll([[2., 3.]], split="train", snapshot="s", bank_hash="b", mode="raw")
        self.assertEqual(raw, [[2., 3.]])
        with self.assertRaises(ValueError):
            standardize_answer_nll([[2.]], split="validation", snapshot="s", bank_hash="b")

    def test_global_loss_weights_and_missing_nan(self):
        cs = loss_coefficients([[0.8, 0.2, 0.], [0., 0., 1.], [0., 0., 0.]],
                               [[False]*3, [True]*3, [False]*3])
        self.assertEqual(cs["omega"], [1.6, 0.4, 0.])
        self.assertAlmostEqual(sum(map(sum, cs["base"])), 1.)
        self.assertAlmostEqual(sum(map(sum, cs["specialization"])), 1.)
        losses = [[2., 3., float("nan")], [None, None, 4.], [None]*3]
        value = weighted_loss(cs["specialization"], losses)
        per_agent = sum(weighted_loss([[r[i]] for r in cs["specialization"]], [[r[i]] for r in losses]) for i in range(3))
        self.assertAlmostEqual(value, 2.56)
        self.assertAlmostEqual(value, per_agent)
        self.assertGreater(sum(cs["base"][2]), 0.)


class BankPreferenceTests(unittest.TestCase):
    def setUp(self):
        self.bank = fixture_bank()

    def test_bank_roundtrip_split_and_identity(self):
        data = json.loads(canonical(self.bank))
        self.assertEqual(bank_from_dict(data, allow_synthetic=True), self.bank)
        with self.assertRaises(ValueError):
            bank_from_dict(data)
        for bank in (dc.replace(self.bank, split="validation"), dc.replace(self.bank, kind="validation_handoff"),
                     dc.replace(self.bank, rows=(dc.replace(self.bank.rows[0], split="test"),)),
                     dc.replace(self.bank, rows=(dc.replace(self.bank.rows[0], label_hash="f"*64),)),
                     dc.replace(self.bank, rows=(dc.replace(self.bank.rows[0], delta=(1., 0., 0.)),))):
            with self.assertRaises(ValueError):
                bank.validate(allow_synthetic=True)
        result = assign_bank(self.bank, allow_synthetic=True)
        self.assertEqual(result["normalization"]["count"], 9)  # includes all-missing row's base scores
        self.assertEqual(result["base_only_rows"], [self.bank.rows[2].row_id])
        self.assertEqual(result["solver"]["weights"][2], [0., 0., 0.])
        self.assertEqual(result["bank_hash"], self.bank.identity)

    def test_same_context_strata_and_accounting(self):
        result = build_preferences(self.bank, allow_synthetic=True)
        self.assertEqual(result["pair_counts"], {"hold": 1, "repair": 1})
        self.assertTrue(result["full_revision_ready"])
        self.assertEqual(result["contexts"][2]["missing_reason"], "missing_incorrect")
        self.assertEqual(sum(p["revision_coefficient"] for p in result["pairs"]), 1.)
        only_hold = dc.replace(self.bank, receivers=(self.bank.receivers[0],))
        missing = build_preferences(only_hold, allow_synthetic=True)
        self.assertFalse(missing["full_revision_ready"])
        self.assertEqual(missing["missing_strata"], ["repair"])
        self.assertIsNone(missing["pairs"][0]["revision_coefficient"])

    def test_reject_cross_context_prefix_and_eos(self):
        ctx = self.bank.receivers[0]
        for candidate in (dc.replace(ctx.candidates[0], context_hash=digest("other prompt")),
                          dc.replace(ctx.candidates[0], prompt_ids=(42,)),
                          dc.replace(ctx.candidates[0], completion_ids=(42,))):
            bad = dc.replace(self.bank, receivers=(dc.replace(ctx, candidates=(candidate, ctx.candidates[1])),))
            with self.assertRaises(ValueError):
                build_preferences(bad, allow_synthetic=True)

    def test_invalid_is_not_negative_and_empty_is_missing(self):
        ctx = self.bank.receivers[0]
        for raw, stop in (("malformed", "eos"), ('{"answer":"ABSTAIN","justification":"x"}', "eos"),
                          (ctx.candidates[1].raw, "length")):
            invalid = dc.replace(ctx.candidates[1], raw=raw, stop_reason=stop)
            bank = dc.replace(self.bank, receivers=(dc.replace(ctx, candidates=(ctx.candidates[0], invalid)),))
            result = build_preferences(bank, allow_synthetic=True)
            self.assertEqual(result["pairs"], [])
            self.assertEqual(result["contexts"][0]["missing_reason"], "missing_incorrect")
        empty = dc.replace(self.bank, receivers=(dc.replace(ctx, candidates=()),))
        self.assertEqual(build_preferences(empty, allow_synthetic=True)["contexts"][0]["missing_reason"], "missing_both")
        overflow = dc.replace(ctx.candidates[0], raw="", completion_ids=(), stop_reason="context_overflow")
        bank = dc.replace(self.bank, receivers=(dc.replace(ctx, candidates=(overflow,)),))
        report = build_preferences(bank, allow_synthetic=True)
        self.assertEqual(report["contexts"][0]["parser_counts"], {"context_overflow": 1})
        self.assertEqual(report["contexts"][0]["missing_reason"], "missing_both")

    def test_prespecified_length_matching_then_stable_index(self):
        ctx = self.bank.receivers[0]
        positive = dc.replace(ctx.candidates[0], completion_ids=(1,)*30 + (0,))
        near_other_bin = dc.replace(ctx.candidates[1], completion_ids=(2,)*31 + (0,))
        same_bin = dc.replace(ctx.candidates[1], completion_ids=(3,)*28 + (0,))
        ctx = dc.replace(ctx, candidates=(positive, near_other_bin, same_bin, same_bin))
        result = build_preferences(dc.replace(self.bank, receivers=(ctx,)), allow_synthetic=True)
        self.assertEqual(result["pairs"][0]["negative_index"], 2)
        self.assertTrue(result["pairs"][0]["length_matched"])


class CompletionReferenceTests(unittest.TestCase):
    def test_causal_shift_padding_and_reductions(self):
        ids = [2, 1, 2, 0, -1]
        logits = [[float("nan")]*3, [0., 0., math.log(2)], [math.log(3), 0., 0.], [float("nan")]*3, [float("nan")]*3]
        score = completion_logprob(logits, ids, [1,1,1,1,0], [0,0,1,1,0])
        expected = math.log(0.5) + math.log(0.6)
        self.assertAlmostEqual(score["sum_logp"], expected)
        self.assertAlmostEqual(score["mean_nll"], -expected/2)
        self.assertEqual(score["token_count"], 2)
        self.assertEqual(completion_logprob(logits[:4], ids[:4], [1]*4, [0,0,1,1]), score)
        for mask in ([1,1,1,1,0], [0,1,0,1,0], [0,0,1,1,1]):
            with self.assertRaises(ValueError):
                completion_logprob(logits, ids, [1,1,1,1,0], mask)

    def test_tokenization_eos_and_no_truncation(self):
        class Characters:
            def encode(self, s, **kwargs):
                return [ord(c) for c in s]
        target = answer_target("B")
        self.assertEqual(target, '{"answer":"B"}')
        tokens = tokenize_completion(Characters(), "prompt:", target, eos_id=0, max_length=100)
        self.assertEqual(tokens["completion_ids"][-1], 0)
        self.assertEqual(sum(tokens["completion_mask"]), len(target) + 1)
        with self.assertRaises(ValueError):
            tokenize_completion(Characters(), "prompt:", target, eos_id=0, max_length=8)
        with self.assertRaises(ValueError):
            tokenize_completion(Characters(), "prompt:", target + "\x00", eos_id=0, max_length=100)
        class BoundaryChange:
            def encode(self, s, **kwargs):
                return [1, 2] if s == "prompt" else [1, 3, 4]
        with self.assertRaises(ValueError):
            tokenize_completion(BoundaryChange(), "prompt", target, eos_id=0, max_length=100)

    def test_dpo_reference_identity_and_summed_scores(self):
        self.assertAlmostEqual(dpo_loss(-3., -4., -3., -4.), math.log(2))
        expected = math.log1p(math.exp(-0.2))
        self.assertAlmostEqual(dpo_loss(-3., -6., -4., -5.), expected)
        self.assertLess(dpo_loss(-3., -6., -4., -5.), math.log(2))
        self.assertTrue(math.isfinite(dpo_loss(-10000., -1., -1., -10000.)))
        for bad in (float("nan"), float("inf"), 1.):
            with self.assertRaises(ValueError):
                dpo_loss(bad, -1., -1., -1.)

    def test_cache_invalidation_and_immutability(self):
        bank = fixture_bank()
        pair = build_preferences(bank, allow_synthetic=True)["pairs"][0]
        request = reference_request(bank, pair, "positive")
        with tempfile.TemporaryDirectory() as tmp:
            cache = ReferenceCache(Path(tmp))
            with self.assertRaises(FileNotFoundError):
                cache.get(request)
            cache.put(request, -4.)
            cache.put(request, -4.)
            self.assertEqual(cache.get(request), -4.)
            with self.assertRaises(ValueError):
                cache.put(request, -5.)
            for changed in (dc.replace(request, adapter_hash=digest("other")),
                            dc.replace(request, agent=1), dc.replace(request, base_snapshot=digest("other")),
                            dc.replace(request, prompt=request.prompt + " "), dc.replace(request, prompt_ids=(1,2)),
                            dc.replace(request, completion=request.completion + " "),
                            dc.replace(request, completion_ids=(1,2,0)), dc.replace(request, precision="bfloat16"),
                            dc.replace(request, tokenizer_revision="a"*40), dc.replace(request, template_hash=digest("other")),
                            dc.replace(request, runtime_fingerprint=digest("other"))):
                self.assertNotEqual(changed.key, request.key)
                with self.assertRaises(FileNotFoundError):
                    cache.get(changed)
            for kind in ("base", "current_actor"):
                with self.assertRaises(ValueError):
                    cache.put(dc.replace(request, kind=kind), -4.)
            path = Path(tmp) / f"{request.key}.json"
            value = read_json(path)
            value["sum_logp"] = -7.
            write_json(path, value)
            with self.assertRaises(ValueError):
                cache.get(request)


class TrainingCLITests(unittest.TestCase):
    def test_fixture_round_trip_and_fail_closed(self):
        with tempfile.TemporaryDirectory() as tmp, contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            root = Path(tmp)
            output = root / "check"
            self.assertEqual(main(["training-check", "--output-dir", str(output)]), 0)
            summary = read_json(output / "summary.json")
            self.assertFalse(summary["training_executed"])
            self.assertEqual(summary["status"], "cpu_fixture_only_no_model_training")
            self.assertEqual(main(["training-check", "--output-dir", str(output)]), 2)
            bank = output / "bank.json"
            for command, filename in (("assign", "assignments.json"), ("build-preferences", "preferences.json")):
                target = root / filename
                args = [command, "--bank", str(bank), "--output", str(target)]
                self.assertEqual(main(args), 2)
                self.assertFalse(target.exists())
                self.assertEqual(main(args + ["--allow-synthetic"]), 0)
                self.assertEqual(read_json(target), read_json(output / filename))
                self.assertEqual(main(args + ["--allow-synthetic"]), 2)
            data = read_json(bank)
            data["split"] = "validation"
            write_json(root / "invalid.json", data)
            self.assertEqual(main(["assign", "--bank", str(root / "invalid.json"), "--output", str(root / "bad.json"), "--allow-synthetic"]), 2)
            self.assertFalse((root / "bad.json").exists())
            for command in ("train", "collect-bank"):
                self.assertEqual(main([command]), 2)

    @unittest.skipUnless(os.environ.get("PACT_TEST_NEURAL") == "1", "explicit optional torch check; no downloads")
    def test_optional_torch_gradients_masks_and_reference_detach(self):
        import torch
        from pact.training.losses import torch_completion_logps, torch_dpo_loss
        logits = torch.zeros((2, 5, 3), dtype=torch.float64, requires_grad=True)
        ids = torch.tensor([[1,2,1,0,-1], [1,2,0,-1,-1]])
        attention = torch.tensor([[1,1,1,1,0], [1,1,1,0,0]])
        masks = torch.tensor([[0,0,1,1,0], [0,0,1,0,0]])
        sums, counts = torch_completion_logps(logits, ids, attention, masks)
        for b in range(2):
            expected = completion_logprob(logits[b].tolist(), ids[b].tolist(), attention[b].tolist(), masks[b].tolist())
            self.assertAlmostEqual(sums[b].item(), expected["sum_logp"])
            self.assertEqual(counts[b].item(), expected["token_count"])
        before = sums.detach().clone()
        (-sums.mean()).backward()
        self.assertEqual(logits.grad[0,0].abs().sum().item(), 0.)
        self.assertEqual(logits.grad[0,3:].abs().sum().item(), 0.)
        with torch.no_grad():
            logits -= 0.1 * logits.grad
        after, _ = torch_completion_logps(logits, ids, attention, masks)
        self.assertTrue((after > before).all())
        p, n, rp, rn = [torch.tensor([-v], requires_grad=True) for v in (3., 6., 4., 5.)]
        loss = torch_dpo_loss(p, n, rp, rn).sum()
        self.assertAlmostEqual(loss.item(), dpo_loss(-3., -6., -4., -5.), places=6)
        loss.backward()
        self.assertLess(p.grad.item(), 0.)
        self.assertGreater(n.grad.item(), 0.)
        self.assertIsNone(rp.grad)
        self.assertIsNone(rn.grad)
