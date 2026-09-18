"""Standard-library masked convex assignment and globally normalized loss weights."""
from __future__ import annotations

import math


def finite(value, name):
    if type(value) not in (int, float) or not math.isfinite(value):
        raise ValueError(f"{name} must be finite")
    return float(value)


def standardize_answer_nll(values, *, split, snapshot, bank_hash, mode="standardized"):
    if split != "train":
        raise ValueError("Fit answer-NLL statistics on the training bank only")
    if mode not in ("raw", "standardized"):
        raise ValueError("Choose raw or standardized answer NLL")
    flat = [finite(x, "answer NLL") for row in values for x in row]
    if not flat or any(x < 0 for x in flat):
        raise ValueError("Answer NLL must be nonnegative and nonempty")
    mean = math.fsum(flat) / len(flat)
    std = math.sqrt(math.fsum((x - mean) ** 2 for x in flat) / len(flat))
    scale = std if std > 0 else 1.0
    transformed = [[(x - mean) / scale if mode == "standardized" else x for x in row] for row in values]
    return transformed, {"mode": mode, "scope": "all agent cells of this frozen training bank",
                         "snapshot": snapshot, "bank_hash": bank_hash, "count": len(flat),
                         "mean": mean, "population_std": std, "scale": scale,
                         "constant_bank": std == 0}


def solve_assignment(costs, *, tau=0.2, balance=0.1, tolerance=1e-8, max_iterations=10000, warm_start=None):
    """None is inaccessible; entirely missing rows stay zero and leave the objective.

    Exponentiated gradient with backtracking and a convex first-order gap stopping
    rule. Gradients are scaled by the eligible-row count, absorbed in the step size.
    """
    tau, balance = finite(tau, "tau"), finite(balance, "balance")
    if tau <= 0 or balance < 0 or finite(tolerance, "tolerance") <= 0:
        raise ValueError("Need tau>0, balance>=0 and tolerance>0")
    if type(max_iterations) is not int or max_iterations < 1:
        raise ValueError("Need a positive iteration cap")
    if not costs or not costs[0]:
        raise ValueError("Cost matrix must be nonempty")
    width = len(costs[0])
    if any(len(row) != width for row in costs):
        raise ValueError("Ragged cost matrix")
    for row in costs:
        for x in row:
            if x is not None:
                finite(x, "cost")
    support = [[i for i, value in enumerate(row) if value is not None] for row in costs]
    active = [b for b, indices in enumerate(support) if indices]
    weights = [[0.0] * width for _ in costs]
    if warm_start is not None:
        if len(warm_start) != len(costs) or any(len(row) != width for row in warm_start):
            raise ValueError("Warm-start shape mismatch")
        if any(finite(x, "warm-start weight") < 0 for row in warm_start for x in row):
            raise ValueError("Warm-start weights must be nonnegative")
    for b in active:
        indices = support[b]
        # A changed support or zero accessible weight restarts the row uniformly.
        row = [warm_start[b][i] for i in indices] if warm_start is not None else []
        if not row or any(x == 0 for x in row):
            row = [1.0] * len(indices)
        total = math.fsum(row)
        for i, value in zip(indices, row):
            weights[b][i] = value / total
    if not active:
        return {"weights": weights, "eligible_rows": [], "status": "no_eligible_rows",
                "tolerance": tolerance, "max_iterations": max_iterations,
                "iterations": 0, "objective": None, "duality_gap": None, "objective_history": [],
                "max_row_sum_error": 0.0, "masked_mass": 0.0}
    count = len(active)
    log_floor = 1e-300  # Used inside logs only; never allocates mass to missing cells.

    def terms(w):
        columns = [math.fsum(w[b][i] for b in active) / count for i in range(width)]
        linear_entropy = math.fsum(w[b][i] * (costs[b][i] + tau * math.log(max(w[b][i], log_floor)))
                                   for b in active for i in support[b]) / count
        kl = math.fsum(x * math.log(width * x) for x in columns if x > 0)
        value = linear_entropy + balance * kl
        gradient = [[0.0] * width for _ in costs]
        for b in active:
            for i in support[b]:
                gradient[b][i] = costs[b][i] + tau * (math.log(max(w[b][i], log_floor)) + 1)
                gradient[b][i] += balance * (math.log(max(width * columns[i], log_floor)) + 1)
        gap = math.fsum(math.fsum(w[b][i] * gradient[b][i] for i in support[b])
                         - min(gradient[b][i] for i in support[b]) for b in active) / count
        return finite(value, "objective"), gradient, max(0.0, finite(gap, "duality gap"))

    objective, gradient, gap = terms(weights)
    history = [objective]
    step = 1.0 / max(1.0, tau + balance)
    iterations = 0
    while gap > tolerance and iterations < max_iterations:
        accepted = False
        for _ in range(60):
            candidate = [[0.0] * width for _ in costs]
            for b in active:
                logits = [math.log(max(weights[b][i], log_floor)) - step * gradient[b][i] for i in support[b]]
                top = max(logits)
                exps = [math.exp(x - top) for x in logits]
                total = math.fsum(exps)
                for i, x in zip(support[b], exps):
                    candidate[b][i] = x / total
            value, next_gradient, next_gap = terms(candidate)
            descent = math.fsum(gradient[b][i] * (candidate[b][i] - weights[b][i])
                               for b in active for i in support[b]) / count
            if value <= objective + 1e-4 * descent + 1e-14:
                accepted = True
                break
            step *= 0.5
        if not accepted:
            break
        weights, objective, gradient, gap = candidate, value, next_gradient, next_gap
        history.append(objective)
        iterations += 1
        # The column KL is bounded by the mean row KL (log-sum inequality).
        # Thus tau+balance bounds curvature relative to row negative entropy.
        # Capping the mirror step also avoids roundoff-driven oscillation when
        # the objective is flat to machine precision but the gap is still large.
        step = min(step * 1.2, 1.0 / (tau + balance))
    return {"weights": weights, "eligible_rows": active,
            "tolerance": tolerance, "max_iterations": max_iterations,
            "status": "converged" if gap <= tolerance else "not_converged",
            "iterations": iterations, "objective": objective, "duality_gap": gap,
            "objective_history": history,
            "max_row_sum_error": max(abs(math.fsum(weights[b]) - 1) for b in active),
            "masked_mass": math.fsum(weights[b][i] for b, row in enumerate(costs) for i, x in enumerate(row) if x is None)}


def loss_coefficients(weights, initial_correct):
    """Detached global coefficients: never renormalize within an adapter/microbatch."""
    if not weights or len(weights) != len(initial_correct):
        raise ValueError("Weight/initial-correctness row mismatch")
    width = len(weights[0])
    if not width or any(len(r) != width for r in weights) or any(len(r) != width for r in initial_correct):
        raise ValueError("Loss coefficient shape mismatch")
    if any(type(x) is not bool for row in initial_correct for x in row):
        raise ValueError("Initial correctness must be boolean")
    if any(finite(x, "responsibility") < 0 for row in weights for x in row):
        raise ValueError("Responsibilities must be nonnegative")
    active = [b for b, row in enumerate(weights) if math.fsum(row) > 0]
    if any(not math.isclose(math.fsum(weights[b]), 1., abs_tol=1e-8) for b in active):
        raise ValueError("Active responsibilities must sum to one")
    omega = [0.0] * len(weights)
    if active:
        raw = [1.0 / (1 + sum(initial_correct[b])) for b in active]
        mean = math.fsum(raw) / len(raw)
        for b, x in zip(active, raw):
            omega[b] = x / mean
    return {"base": [[1.0 / (len(weights) * width)] * width for _ in weights],
            "specialization": [[omega[b] * x / len(active) if active else 0.0 for x in row]
                               for b, row in enumerate(weights)], "omega": omega}


def weighted_loss(coefficients, losses):
    if len(coefficients) != len(losses) or any(len(c) != len(x) for c, x in zip(coefficients, losses)):
        raise ValueError("Loss shape mismatch")
    values = []
    for cs, xs in zip(coefficients, losses):
        for c, x in zip(cs, xs):
            if finite(c, "coefficient") < 0:
                raise ValueError("Negative loss coefficient")
            if c:  # Do not evaluate 0 * NaN/None from an unavailable packet.
                values.append(c * finite(x, "active loss"))
    return math.fsum(values)
