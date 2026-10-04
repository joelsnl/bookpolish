# Author: joelsnl
"""Score a System One judge (Kev, Laya, Jev) on evals/judge_set.json.

Usage:
    python scripts/eval_judge.py URL MODEL [--kind systemone|chat] [--set PATH]

Asks every item all four judge questions through the product verifier class
(SystemOneVerifier, or ChatLogprobVerifier for a chat model's logprobs) and
reports, per threshold, how many drift items were flagged (recall) and how many
ok items were flagged (false flags), plus ranking quality (AUC) per question.
fix-flagged counts good corrections toward the Chinese that the judge would
revert, the failure a machine-anchored judge shows on a book with bad terms.
Jev 1.13's stored answers are scored alongside for comparison. Items labelled
"unsure" are left out of both rates.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from bookpolish.verify import (  # noqa: E402
    QUESTIONS,
    ChatLogprobVerifier,
    SystemOneVerifier,
)

THRESHOLDS = (0.5, 0.6, 0.7, 0.8, 0.9)


def auc(drift: list[float], ok: list[float]) -> float:
    pairs = sum((d > o) + 0.5 * (d == o) for d in drift for o in ok)
    return pairs / (len(drift) * len(ok))


def report_auc(items: list[dict], answers: list[dict[str, float]]) -> None:
    for key in (*QUESTIONS, "max", "thing|claim"):
        if key == "max":
            pick = lambda a: max(a.values())  # noqa: E731
        elif key == "thing|claim":
            pick = lambda a: max(a["changed_thing"], a["added_claim"])  # noqa: E731
        else:
            pick = lambda a, k=key: a[k]  # noqa: E731
        drift = [pick(a) for it, a in zip(items, answers, strict=True) if it["label"] == "drift"]
        ok = [pick(a) for it, a in zip(items, answers, strict=True) if it["label"] == "ok"]
        print(f"  AUC {key:14} {auc(drift, ok):.3f}")


def table(name: str, items: list[dict], scores: list[float]) -> None:
    print(f"\n{name}")
    print("  thr   real-drift  swap-drift  sample-drift  ok-flagged  fix-flagged")
    for thr in THRESHOLDS:
        cells = []
        for kind, label in (("real", "drift"), ("swap", "drift"), ("sample", "drift"),
                            ("sample", "ok"), ("correction", "ok")):
            group = [s for it, s in zip(items, scores, strict=True)
                     if it["kind"] == kind and it["label"] == label]
            cells.append(f"{sum(s >= thr for s in group)}/{len(group)}")
        print(f"  {thr:.1f}  " + "  ".join(f"{c:>10}" for c in cells))


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="eval_judge")
    parser.add_argument("url")
    parser.add_argument("model")
    parser.add_argument("--kind", choices=["systemone", "chat"], default="systemone")
    parser.add_argument("--set", default=str(ROOT / "evals" / "judge_set.json"))
    args = parser.parse_args(argv)
    items = json.loads(Path(args.set).read_text(encoding="utf-8"))["items"]
    start = time.time()
    if args.kind == "systemone":
        judge = SystemOneVerifier(args.url, args.model)
        states = [
            {key: item[key] for key in ("chinese_source", "machine_english", "edited_english")}
            for item in items
        ]
        try:
            answers = list(judge._pool.map(judge._ask, states))
        finally:
            judge.close()
    else:
        judge = ChatLogprobVerifier(args.url, args.model, questions=tuple(QUESTIONS))
        jobs = [(i, q) for i in range(len(items)) for q in QUESTIONS]
        try:
            scores = list(judge._pool.map(lambda job: judge.p_yes(
                items[job[0]]["chinese_source"], items[job[0]]["machine_english"],
                items[job[0]]["edited_english"], job[1]), jobs))
        finally:
            judge.close()
        answers = [{} for _ in items]
        for (i, q), score in zip(jobs, scores, strict=True):
            answers[i][q] = score
    seconds = time.time() - start
    print(f"{args.model}: {len(items)} items in {seconds:.1f}s "
          f"({seconds / len(items) * 1000:.0f} ms each, 8 in flight)")
    report_auc(items, answers)
    table(args.model, items, [max(a.values()) for a in answers])
    with_jev = [it for it in items if it["jev_1_13"]]
    table("jev-1.13 (stored)", with_jev, [max(it["jev_1_13"].values()) for it in with_jev])
    out = Path(args.set).with_name(f"judge_{args.model.replace('/', '_')}.json")
    out.write_text(json.dumps(answers), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
