# Author: joelsnl
"""Chapter-file CLI. Narrative order is the order of the segments list."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

from bookpolish.engine import (
    POLICY,
    BookDB,
    ModelError,
    Run,
    Server,
    apply_glossary,
    load_chapter,
    load_glossary,
    polish,
    preview,
)
from bookpolish.verify import SystemOneVerifier


def _default_db() -> Path:
    return Path.home() / ".bookpolish" / "bookpolish.sqlite"


def _dump(run: Run) -> dict:
    model = run.edits[0].model if run.edits else ""
    return {
        "policy": POLICY,
        "model": model,
        "error": run.error,
        "summary": dict(Counter(edit.reason for edit in run.edits)),
        "edits": [
            {
                "id": edit.segment_id,
                "english": edit.english,
                "accepted": edit.accepted,
                "reason": edit.reason,
                "model": edit.model,
                "policy": edit.policy,
                "cached": edit.cached,
                "sentences": {
                    "edited": edit.sentences_edited,
                    "rejected": edit.sentences_rejected,
                    "skipped": edit.sentences_skipped,
                    "flagged": edit.sentences_flagged,
                },
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
    run.add_argument("--glossary", help="JSON list of book-wide terms")
    run.add_argument(
        "--workers",
        type=int,
        default=1,
        help="requests in flight at once; match the server's parallel slots",
    )
    run.add_argument(
        "--verify",
        metavar="URL",
        help="re-check accepted edits with a System One server, e.g. a local Kev or Laya "
        "at http://127.0.0.1:8009 (edited sentences are sent to it)",
    )
    run.add_argument("--verify-model", default="", help="judge name; keys the cache")
    run.add_argument("--verify-threshold", type=float, default=0.7)
    args = parser.parse_args(argv)
    if args.ctx < 1:
        print("ctx must be positive", file=sys.stderr)
        return 2
    if args.workers < 1:
        print("workers must be positive", file=sys.stderr)
        return 2
    segments = load_chapter(Path(args.chapter))
    if args.glossary:
        segments = apply_glossary(segments, load_glossary(Path(args.glossary)))
    with BookDB(Path(args.db) if args.db else _default_db()) as db:
        if args.print_prompt:
            for block in preview(segments, db, num_ctx=args.ctx):
                print(block)
                print("\n---\n")
            return 0
        try:
            verifier = (
                SystemOneVerifier(args.verify, args.verify_model, args.verify_threshold)
                if args.verify
                else None
            )
            client = Server(args.host, args.model, timeout=args.timeout)
        except (ModelError, ValueError) as exc:
            print(exc, file=sys.stderr)
            return 1
        result = polish(
            segments,
            client=client,
            db=db,
            num_ctx=args.ctx,
            close_client=True,
            workers=args.workers,
            verifier=verifier,
        )
        if verifier is not None:
            verifier.close()
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
