"""One live instance: one copy of the same character at a time (Trundle, Nov 1, 2026).

The rule limits copies of one character, not how many people share the screen. Any number of different
characters may appear together. The same character may not be live twice at once: listed twice in one shot,
or on two channels whose windows overlap (for example a Ch 2 crossover while that character is live on Ch 12).
Back-to-back windows (one ends exactly when the next starts) are not an overlap."""

from __future__ import annotations

import datetime
from collections import defaultdict
from typing import Any


class LiveInstanceError(ValueError):
    pass


def _key(character: Any) -> str:
    if not isinstance(character, str) or not character.strip():
        raise LiveInstanceError("character must be a non-empty string")
    return character.strip().casefold()


def _instant(value: Any, label: str) -> float:
    if isinstance(value, bool):
        raise LiveInstanceError(f"{label} must be a number or ISO timestamp")
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            when = datetime.datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            raise LiveInstanceError(f"{label} {value!r} is not an ISO timestamp") from None
        if when.tzinfo is None:
            raise LiveInstanceError(f"{label} {value!r} needs a UTC offset")
        return when.timestamp()
    raise LiveInstanceError(f"{label} must be a number or ISO timestamp")


def copies_in_shot(characters: list[str]) -> list[str]:
    """Characters listed more than once in one shot. Distinct characters together are fine."""
    seen: dict[str, int] = defaultdict(int)
    for character in characters:
        seen[_key(character)] += 1
    return sorted(k for k, n in seen.items() if n > 1)


def live_instance_conflicts(appearances: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Overlapping windows of the same character.

    Each appearance has `character`, `start` and `end` (numbers or ISO timestamps with an offset; end is
    exclusive), plus optional `channel` and `clip_id` echoed back in the conflict."""
    by_character: dict[str, list[tuple[float, float, dict[str, Any]]]] = defaultdict(list)
    for n, item in enumerate(appearances):
        start = _instant(item.get("start"), f"appearance {n} start")
        end = _instant(item.get("end"), f"appearance {n} end")
        if end <= start:
            raise LiveInstanceError(f"appearance {n} ends before it starts")
        by_character[_key(item.get("character"))].append((start, end, item))

    conflicts: list[dict[str, Any]] = []
    for character, windows in sorted(by_character.items()):
        windows.sort(key=lambda w: (w[0], w[1]))
        for i, (start_a, end_a, a) in enumerate(windows):
            for start_b, end_b, b in windows[i + 1 :]:
                if start_b >= end_a:
                    break
                conflicts.append(
                    {
                        "character": character,
                        "first": {k: a.get(k) for k in ("channel", "clip_id", "start", "end")},
                        "second": {k: b.get(k) for k in ("channel", "clip_id", "start", "end")},
                    }
                )
    return conflicts
