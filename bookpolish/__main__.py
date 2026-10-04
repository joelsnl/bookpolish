# Author: joelsnl
"""Chapter-file CLI. Narrative order is the order of the segments list."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from bookpolish.engine import POLICY, BookDB, Run, Server, load_chapter, polish, preview


def _default_db() -> Path:
    return Path.home() / ".bookpolish" / "bookpolish.sqlite"


def _dump(run: Run) -> dict:
    model = run.edits[0].model if run.edits else ""
    return {
        "policy": POLICY,
        "model": model,
        "error": run.error,
        "edits": [
            {
                "id": edit.segment_id,
                "english": edit.english,
                "accepted": edit.accepted,
                "reason": edit.reason,
                "model": edit.model,
                "policy": edit.policy,
                "cached": edit.cached,
            }
            for edit in run.edits
        ],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="bookpolish")
    sub = parser.add_subparsers(dest="cmd", required=True)
    run = sub.add_parser("run", help="edit a chapter file")
    run.add_argument("chapter")
    run.add_argument("-o", "--output")
    run.add_argument("--host", default="http://127.0.0.1:8080")
    run.add_argument("--model", default="")
    run.add_argument("--ctx", type=int, default=4096)
    run.add_argument("--db", default="")
    run.add_argument("--timeout", type=float, default=180)
    run.add_argument("--print-prompt", action="store_true")
    args = parser.parse_args(argv)
    if args.ctx < 1:
        print("ctx must be positive", file=sys.stderr)
        return 2
    segments = load_chapter(Path(args.chapter))
    with BookDB(Path(args.db) if args.db else _default_db()) as db:
        if args.print_prompt:
            for block in preview(segments, db, num_ctx=args.ctx):
                print(block)
                print("\n---\n")
            return 0
        client = Server(args.host, args.model, timeout=args.timeout)
        result = polish(segments, client=client, db=db, num_ctx=args.ctx, close_client=True)
    payload = json.dumps(_dump(result), ensure_ascii=False, indent=2)
    if args.output:
        Path(args.output).write_text(payload + "\n", encoding="utf-8")
    else:
        print(payload)
    if result.error:
        print(result.error, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
