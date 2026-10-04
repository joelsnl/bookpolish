# Author: joelsnl
"""Score the accept gates on recorded edits: false rejects and false accepts.

Usage: python scripts/eval_gates.py CHAPTER.json OUT.json [OUT.json ...]

False rejects: accepted sentence edits from a past run that the current gates
now reject (the same pairs replay_gates.py prints).

False accepts: each accepted edit is damaged with one known meaning change
(drop a negation, flip a pronoun's gender, change a number, drop "if", swap a
name, swap the speaker's person, append an invented clause). A damaged edit
the gates still accept is a miss. Recall is reported per kind of damage.

The damage is synthetic and regex-made, so recall here is an upper bound on
real recall: it says nothing about idioms or wrong-but-plausible nouns.
"""

from __future__ import annotations

import random
import re
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from bookpolish.engine import accept_edit  # noqa: E402
from scripts.replay_gates import changed_pairs  # noqa: E402

_GENDER = {"he": "she", "she": "he", "him": "her", "his": "her", "her": "his",
           "himself": "herself", "herself": "himself"}
_NUMBER = {"one": "two", "two": "three", "three": "four", "four": "five", "five": "six",
           "ten": "nine", "hundred": "thousand", "thousand": "hundred"}
_NAME = re.compile(r"\b[A-Z][a-z]+ [A-Z][a-z]+\b")
_INVENTED = ", and a cold killing intent flashed deep in his eyes"


def _sub_once(pattern: str, repl, text: str) -> str | None:
    changed = re.sub(pattern, repl, text, count=1)
    return changed if changed != text else None


def drop_negation(text: str) -> str | None:
    return _sub_once(r"\b(?:not|never) |n't\b", "", text)


def flip_gender(text: str) -> str | None:
    def swap(match: re.Match) -> str:
        word = match.group(0)
        new = _GENDER[word.lower()]
        return new.capitalize() if word[0].isupper() else new

    return _sub_once(r"\b(?:" + "|".join(_GENDER) + r")\b", swap, text)


def change_number(text: str) -> str | None:
    digit = _sub_once(r"\b\d+\b", lambda m: str(int(m.group(0)) + 1), text)
    if digit:
        return digit
    return _sub_once(
        r"\b(?:" + "|".join(_NUMBER) + r")\b", lambda m: _NUMBER[m.group(0).lower()], text
    )


def drop_if(text: str) -> str | None:
    return _sub_once(r"(?<!\bas )\b[Ii]f\b ", "", text)


def swap_person(text: str) -> str | None:
    if not re.search(r"\byou\b", text):
        return None
    return re.sub(r"\byou\b", "I", re.sub(r"\byour\b", "my", text))


def invent_clause(text: str) -> str | None:
    match = re.search(r"[.!?][\"”’]?\s*$", text)
    if not match:
        return None
    return text[: match.start()] + _INVENTED + text[match.start():]


def make_name_swap(names: list[str]):
    def swap_name(text: str) -> str | None:
        found = _NAME.search(text)
        if not found:
            return None
        others = [name for name in names if name != found.group(0)]
        return text.replace(found.group(0), others[0], 1) if others else None

    return swap_name


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print(__doc__, file=sys.stderr)
        return 2
    pairs = list(changed_pairs(Path(argv[0]), [Path(p) for p in argv[1:]]))
    names = [name for name, _ in Counter(
        m for _, _, out in pairs for m in _NAME.findall(out)).most_common(20)]
    damages = {
        "negation": drop_negation, "gender": flip_gender, "number": change_number,
        "conditional": drop_if, "name": make_name_swap(names), "person": swap_person,
        "invented": invent_clause,
    }
    kept = [(seg, src, out) for seg, src, out in pairs if accept_edit(src, out, seg.terms)]
    false_rejects = len(pairs) - len(kept)
    print(f"false rejects: {false_rejects} of {len(pairs)} ({false_rejects / len(pairs):.1%})")
    rng = random.Random(0)
    total_hits = total_tried = 0
    for kind, damage in damages.items():
        tried = caught = 0
        examples = []
        for seg, src, out in kept:
            bad = damage(out)
            if bad is None:
                continue
            tried += 1
            if not accept_edit(src, bad, seg.terms):
                caught += 1
            elif len(examples) < 2 and rng.random() < 0.3:
                examples.append(bad)
        total_hits += caught
        total_tried += tried
        recall = caught / tried if tried else 0.0
        print(f"{kind:12} recall {recall:6.1%}  ({caught}/{tried})")
        for example in examples:
            print(f"    missed: {example[:140]}")
    print(f"overall damage recall {total_hits / total_tried:.1%} ({total_hits}/{total_tried})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
