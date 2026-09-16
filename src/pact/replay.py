from __future__ import annotations

from .protocol import Protocol
from .parsing import parse_answer
from .schemas import ReplayPair, PreferencePair, TaskLabel, Trajectory
from .util import digest, node_seed


def choose_pair(packets, gold: str, length_bin: int):
    positive = [i for i, p in enumerate(packets) if p.parser_status == "ok" and p.answer_id == gold]
    negative = [i for i, p in enumerate(packets) if p.parser_status == "ok" and p.answer_id != gold]
    if not positive or not negative:
        return None, None, None, "missing_correct" if not positive else "missing_incorrect"
    def rank(pair):
        a, b = (packets[i].call.output_tokens for i in pair)
        return (a // length_bin != b // length_bin, abs(a - b), *pair)
    plus, minus = min(((p, n) for p in positive for n in negative), key=rank)
    return plus, minus, not rank((plus, minus))[0], None


def probe(protocol: Protocol, trajectory: Trajectory, label: TaskLabel) -> tuple[tuple[ReplayPair, ...], tuple[PreferencePair, ...]]:
    if trajectory.method != "debate" or trajectory.status != "complete" or label.task_id != trajectory.task.task_id:
        raise ValueError("Probe requires completed reference debate and same-task evaluator label")
    config = protocol.config
    snapshot = protocol.backend.identity["snapshot"]
    if trajectory.snapshot != snapshot:
        raise ValueError("Whole-team snapshot changed before probe")
    pairs, preferences = [], []
    task = trajectory.task
    for agent in range(3):
        original = trajectory.private[agent]
        candidates = tuple(protocol.private_packet(task, agent, trajectory.attack,
                            node_seed(config.seed, trajectory.trajectory_id, agent, "alternative", j))
                           for j in range(config.probe.candidates))
        if any(p.call.messages != original.call.messages or p.call.context_hash != original.call.context_hash for p in candidates):
            raise AssertionError("Candidate actor context changed")
        positive, negative, matched, reason = choose_pair(candidates, label.answer_id, config.probe.length_bin)
        positive_suffixes, negative_suffixes, differences = [], [], []
        seeds = tuple(node_seed(config.seed, trajectory.trajectory_id, agent, "suffix", k)
                      for k in range(config.probe.suffix_seeds)) if reason is None else ()
        for seed in seeds:
            branches = []
            for index, name in ((positive, "positive"), (negative, "negative")):
                private = tuple(candidates[index] if i == agent else p for i, p in enumerate(trajectory.private))
                branches.append(protocol.suffix(task, "debate", trajectory.attack, private, seed,
                                                digest([trajectory.trajectory_id, agent, seed, name])))
            p, n = branches
            if [c.seed for c in p.calls] != [c.seed for c in n.calls]:
                raise AssertionError("Suffix seeds were not paired by node")
            positive_suffixes.append(p)
            negative_suffixes.append(n)
            differences.append(int(p.final.answer_id == label.answer_id) - int(n.final.answer_id == label.answer_id))
        q_plus = sum(p.final.answer_id == label.answer_id for p in positive_suffixes) / len(seeds) if seeds else None
        q_minus = sum(p.final.answer_id == label.answer_id for p in negative_suffixes) / len(seeds) if seeds else None
        pairs.append(ReplayPair(digest([trajectory.trajectory_id, agent, "pair"]), trajectory.trajectory_id,
                     task.task_id, task.split, task.dataset_revision, task.source_hash, trajectory.attack.attack_id,
                     snapshot, agent, original.answer_id == label.answer_id, candidates,
                     "eligible" if reason is None else "missing_pair", reason, positive, negative, matched, seeds,
                     tuple(positive_suffixes), tuple(negative_suffixes), tuple(differences), q_plus, q_minus,
                     q_plus - q_minus if seeds else None))

        peer_answers = [parse_answer(m.text, tuple(o.answer_id for o in task.options))[0]
                        for m in trajectory.delivered if m.recipient == agent]
        initially_correct = original.answer_id == label.answer_id
        stratum = ("hold" if initially_correct and any(a is not None and a != label.answer_id for a in peer_answers)
                   else "repair" if not initially_correct and label.answer_id in peer_answers else "ineligible_context")
        revision = trajectory.revised[agent]
        receiver_candidates = tuple(protocol.packet(task, agent, "revision", revision.call.messages,
                                    node_seed(config.seed, trajectory.trajectory_id, agent, "receiver", j))
                                    for j in range(config.probe.revision_candidates)) if stratum != "ineligible_context" else ()
        if any(p.call.context_hash != revision.call.context_hash for p in receiver_candidates):
            raise AssertionError("Receiver prompt changed within eligibility probe")
        rp, rn, _, missing = choose_pair(receiver_candidates, label.answer_id, config.probe.length_bin)
        preferences.append(PreferencePair(trajectory.trajectory_id, task.task_id, agent, stratum,
                                           revision.call.context_hash, receiver_candidates, rp, rn,
                                           "eligible" if missing is None else "missing_pair" if receiver_candidates else "ineligible_context"))
        if protocol.backend.identity["snapshot"] != snapshot:
            raise AssertionError("Whole-team snapshot changed during replay")
    return tuple(pairs), tuple(preferences)
