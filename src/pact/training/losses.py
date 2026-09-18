"""Explicit causal completion scoring; PyTorch imports remain optional and lazy."""
from __future__ import annotations

import math
from .assignment import finite
from ..util import canonical


def answer_target(answer_id: str) -> str:
    if not isinstance(answer_id, str) or len(answer_id) != 1 or answer_id not in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ':
        raise ValueError("Expected a canonical answer ID")
    return canonical({"answer": answer_id})


def tokenize_completion(tokenizer, prompt: str, completion: str, *, eos_id: int, max_length: int):
    """Use joint tokenization, verify the prompt prefix, append one EOS; never truncate."""
    if not prompt or not completion or type(eos_id) is not int or eos_id < 0:
        raise ValueError("Nonempty prompt/completion and explicit EOS required")
    prefix = list(tokenizer.encode(prompt, add_special_tokens=False))
    joined = list(tokenizer.encode(prompt + completion, add_special_tokens=False))
    if not prefix or joined[:len(prefix)] != prefix or len(joined) <= len(prefix):
        raise ValueError("Tokenization changed the prompt prefix at the completion boundary")
    target = joined[len(prefix):]
    if eos_id in target:
        raise ValueError("Completion text must not contain EOS; it is appended explicitly")
    target.append(eos_id)
    if len(prefix) + len(target) > max_length:
        raise ValueError("Prompt plus completion exceeds cap; no implicit truncation")
    return {"prompt_ids": prefix, "completion_ids": target,
            "input_ids": prefix + target, "attention_mask": [1] * (len(prefix) + len(target)),
            "completion_mask": [0] * len(prefix) + [1] * len(target),
            "eos_policy": "one appended EOS, included in completion loss"}


def completion_positions(ids, attention, completion):
    if not ids or len(ids) != len(attention) or len(ids) != len(completion):
        raise ValueError("Token/mask lengths differ")
    if any(x not in (0, 1) for x in (*attention, *completion)):
        raise ValueError("Masks must be binary")
    attended = sum(attention)
    if list(attention) != [1] * attended + [0] * (len(ids) - attended):
        raise ValueError("Only contiguous right padding is supported")
    positions = [i for i, x in enumerate(completion) if x]
    if not positions or positions[0] < 1 or positions != list(range(positions[0], attended)):
        raise ValueError("Completion must be a nonempty suffix after an attended prompt")
    if any(type(x) is not int or x < 0 for x in ids[:attended]):
        raise ValueError("Attended token IDs must be nonnegative integers")
    return positions


def completion_logprob(logits, ids, attention, completion):
    """Independent CPU numerical reference: logits[t] predicts input_ids[t+1]."""
    positions = completion_positions(ids, attention, completion)
    if len(logits) != len(ids):
        raise ValueError("Logit/token length mismatch")
    values = []
    for t in positions:
        row = [finite(x, "scored logit") for x in logits[t - 1]]
        if not row or ids[t] >= len(row):
            raise ValueError("Target token outside vocabulary")
        top = max(row)
        values.append(row[ids[t]] - top - math.log(math.fsum(math.exp(x - top) for x in row)))
    total = math.fsum(values)
    return {"sum_logp": total, "token_count": len(values), "mean_nll": -total / len(values)}


def dpo_loss(policy_positive, policy_negative, reference_positive, reference_negative, *, beta=0.1):
    scores = [finite(x, "summed completion log probability") for x in
              (policy_positive, policy_negative, reference_positive, reference_negative)]
    if any(x > 0 for x in scores) or finite(beta, "beta") <= 0:
        raise ValueError("Log probabilities must be <=0 and beta positive")
    z = beta * ((scores[0] - scores[2]) - (scores[1] - scores[3]))
    finite(z, "DPO margin")
    # softplus(-z), stable even for very large finite margins.
    return max(-z, 0) + math.log1p(math.exp(-abs(z)))


def torch_completion_logps(logits, input_ids, attention_mask, completion_mask):
    """Differentiable sums/counts; evaluate only supervised positions, not padding."""
    import torch
    import torch.nn.functional as F
    if logits.ndim != 3 or input_ids.ndim != 2 or logits.shape[:2] != input_ids.shape:
        raise ValueError("Expected [batch,time,vocabulary] logits and [batch,time] IDs")
    if attention_mask.shape != input_ids.shape or completion_mask.shape != input_ids.shape:
        raise ValueError("Mask shape mismatch")
    batch_indices, time_indices, targets, counts = [], [], [], []
    for b, (ids, attention, completion) in enumerate(zip(input_ids.detach().cpu().tolist(),
            attention_mask.detach().cpu().tolist(), completion_mask.detach().cpu().tolist())):
        positions = completion_positions(ids, attention, completion)
        if any(ids[t] >= logits.shape[-1] for t in positions):
            raise ValueError("Target token outside vocabulary")
        counts.append(len(positions))
        for t in positions:
            batch_indices.append(b); time_indices.append(t - 1); targets.append(ids[t])
    if not counts:
        raise ValueError("Empty completion batch")
    bi = torch.tensor(batch_indices, dtype=torch.long, device=logits.device)
    ti = torch.tensor(time_indices, dtype=torch.long, device=logits.device)
    target = torch.tensor(targets, dtype=torch.long, device=logits.device)
    selected = logits[bi, ti]
    if not torch.isfinite(selected).all():
        raise ValueError("Nonfinite supervised logits")
    # FP32 accumulation for low precision, preserve FP64 for numerical checks.
    selected = selected.float() if selected.dtype in (torch.float16, torch.bfloat16) else selected
    token_logps = F.log_softmax(selected, dim=-1).gather(1, target[:, None]).squeeze(1)
    sums = token_logps.new_zeros(input_ids.shape[0]).index_add(0, bi, token_logps)
    return sums, torch.tensor(counts, device=logits.device)


def torch_dpo_loss(policy_positive, policy_negative, reference_positive, reference_negative, *, beta=0.1):
    import torch
    import torch.nn.functional as F
    if finite(beta, "beta") <= 0:
        raise ValueError("beta must be positive")
    scores = (policy_positive, policy_negative, reference_positive, reference_negative)
    if any(x.shape != policy_positive.shape for x in scores) or policy_positive.numel() == 0:
        raise ValueError("DPO score shapes must match and be nonempty")
    if any(not torch.isfinite(x).all() or (x > 0).any() for x in scores):
        raise ValueError("Invalid completion log probabilities")
    z = beta * ((policy_positive - reference_positive.detach()) - (policy_negative - reference_negative.detach()))
    if not torch.isfinite(z).all():
        raise ValueError("Nonfinite DPO margin")
    return F.softplus(-z)  # Caller supplies global, stratum-balanced coefficients.
