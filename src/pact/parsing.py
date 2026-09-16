from __future__ import annotations

import json


def parse_answer(raw: str, allowed: tuple[str, ...], *, final: bool = False,
                 stop_reason: str = "eos") -> tuple[str | None, str, str]:
    """Exactly one JSON object; no fences, duplicate keys, repairs or label access."""
    if stop_reason in ("context_overflow", "length"):
        return None, "", stop_reason
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("duplicate key")
            result[key] = value
        return result
    try:
        data = json.loads(raw, object_pairs_hook=unique)
    except (ValueError, TypeError):
        return None, "", "malformed"
    expected = {"answer"} if final else {"answer", "justification"}
    if not isinstance(data, dict) or set(data) != expected:
        return None, "", "malformed"
    answer = data["answer"]
    if answer == "ABSTAIN":
        return None, "", "abstention"
    if type(answer) is not str or answer not in allowed:
        return None, "", "invalid_answer"
    explanation = "" if final else data["justification"]
    if type(explanation) is not str or (not final and not explanation.strip()):
        return None, "", "malformed"
    return answer, explanation, "ok"
