# Author: joelsnl
"""Score a System One judge (Kev, Laya, Jev) on evals/judge_set.json.

Usage:
    python scripts/eval_judge.py URL MODEL [--set evals/judge_set.json]

Sends every item through SystemOneVerifier's questions and reports, per
threshold, how many drift items were flagged (recall) and how many ok items
were flagged (false flags), plus latency. Jev 1.13's stored answers are scored
alongside for comparison. Items labelled "unsure" are left out of both rates.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from bookpolish.verify import SystemOneVerifier  # noqa: E402

THRESHOLDS = (0.5, 0.6, 0.7, 0.8, 0.9)


def table(name: str, items: list[dict], scores: list[float]) -> None:
    print(f"\n{name}")
    print("  thr   real-drift  swap-drift  sample-drift  ok-flagged")
    for thr in THRESHOLDS:
        cells = []
        for kind, label in (("real", "drift"), ("swap", "drift"), ("sample", "drift"),
                            ("sample", "ok")):
            group = [s for it, s in zip(items, scores, strict=True)
                     if it["kind"] == kind and it["label"] == label]
            cells.append(f"{sum(s >= thr for s in group)}/{len(group)}")
        print(f"  {thr:.1f}  " + "  ".join(f"{c:>10}" for c in cells))


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="eval_judge")
    parser.add_argument("url")
    parser.add_argument("model")
    parser.add_argument("--set", default=str(ROOT / "evals" / "judge_set.json"))
    args = parser.parse_args(argv)
    items = json.loads(Path(args.set).read_text(encoding="utf-8"))["items"]
    judge = SystemOneVerifier(args.url, args.model)
    states = [
        {key: item[key] for key in ("chinese_source", "machine_english", "edited_english")}
        for item in items
    ]
    start = time.time()
    try:
        answers = list(judge._pool.map(judge._ask, states))
    finally:
        judge.close()
    seconds = time.time() - start
    print(f"{args.model}: {len(items)} items in {seconds:.1f}s "
          f"({seconds / len(items) * 1000:.0f} ms each, 8 in flight)")
    table(args.model, items, [max(a.values()) for a in answers])
    table("jev-1.13 (stored)", items, [max(it["jev_1_13"].values()) for it in items])
    out = Path(args.set).with_name(f"judge_{args.model.replace('/', '_')}.json")
    out.write_text(json.dumps(answers), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
