# Author: joelsnl
"""Replay the current gates over edits a past run already accepted.

Usage: python scripts/replay_gates.py CHAPTER.json OUT.json [OUT.json ...]

Each changed paragraph is split into sentences. When the machine English and
the output have the same sentence count they are paired one to one; otherwise
the whole paragraph is one pair. A pair the current gates reject is printed.
The count is the cost of a gate change in edits a past run kept.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from bookpolish.engine import _sentences, accept_edit, load_chapter  # noqa: E402


def changed_pairs(chapter: Path, outputs: list[Path]):
    segments = {segment.segment_id: segment for segment in load_chapter(chapter)}
    for output in outputs:
        for edit in json.loads(output.read_text(encoding="utf-8"))["edits"]:
            segment = segments[edit["id"]]
            if edit["english"] == segment.english:
                continue
            before, after = _sentences(segment.english), _sentences(edit["english"])
            if len(before) != len(after):
                before, after = [segment.english], [edit["english"]]
            for source, result in zip(before, after, strict=False):
                if source != result:
                    yield segment, source, result


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print(__doc__, file=sys.stderr)
        return 2
    total = rejected = 0
    for segment, source, result in changed_pairs(Path(argv[0]), [Path(p) for p in argv[1:]]):
        total += 1
        if not accept_edit(source, result, segment.terms):
            rejected += 1
            print(f"{segment.segment_id}\n  - {source}\n  + {result}")
    share = rejected / total if total else 0.0
    print(f"rejected {rejected} of {total} accepted sentence edits ({share:.1%})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
