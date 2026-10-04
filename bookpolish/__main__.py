# Author: joelsnl
"""Chapter-file CLI. Narrative order is the order of the segments list.

`run` edits a chapter. `verify` re-checks a `run` output with a judge, so the
editor and the judge never need to share the GPU.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

from bookpolish.engine import (
    POLICY,
    BookDB,
    Edit,
    ModelError,
    Run,
    Server,
    apply_glossary,
    load_chapter,
    load_glossary,
    polish,
    preview,
    verify_edits,
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
                "detail": [list(sentence) for sentence in edit.sentences],
            }
            for edit in run.edits
        ],
    }


def _load_run(path: Path) -> list[Edit]:
    """Read a `run` output back into edits, for the verify pass."""
    data = json.loads(path.read_text(encoding="utf-8"))
    edits = []
    for item in data["edits"]:
        counts = item.get("sentences") or {}
        edits.append(
            Edit(
                item["id"], item["english"], item["accepted"], item["reason"], item["model"],
                item["policy"], item.get("cached", False),
                sentences_edited=counts.get("edited", 0),
                sentences_rejected=counts.get("rejected", 0),
                sentences_skipped=counts.get("skipped", 0),
                sentences_flagged=counts.get("flagged", 0),
                sentences=tuple(tuple(row) for row in item.get("detail") or ()),
            )
        )
    return edits


def _add_judge_args(parser: argparse.ArgumentParser, required: bool) -> None:
    parser.add_argument(
        "--verify",
        metavar="URL",
        required=required,
        help="System One judge server (POST /v1/systemone), e.g. a local Kev, Laya, or "
        "Winnow at http://127.0.0.1:8009; edited sentences are sent to it",
    )
    parser.add_argument("--verify-model", default="", help="judge name; keys cached verdicts")
    parser.add_argument("--verify-threshold", type=float, default=0.7)
    parser.add_argument("--verify-workers", type=int, default=4)


def _write(run: Run, output: str | None) -> int:
    payload = json.dumps(_dump(run), ensure_ascii=False, indent=2)
    if output:
        Path(output).write_text(payload + "\n", encoding="utf-8")
    else:
        print(payload)
    if run.error:
        print(run.error, file=sys.stderr)
        return 1
    return 0


def _judge(args: argparse.Namespace) -> SystemOneVerifier:
    return SystemOneVerifier(args.verify, args.verify_model, args.verify_threshold)


def _cmd_run(args: argparse.Namespace) -> int:
    if args.ctx < 1 or args.workers < 1:
        print("ctx and workers must be positive", file=sys.stderr)
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
            verifier = _judge(args) if args.verify else None
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
        )
        if verifier is not None and result.error is None:
            try:
                result = verify_edits(
                    segments, result.edits, verifier=verifier, db=db,
                    workers=args.verify_workers,
                )
            finally:
                verifier.close()
    return _write(result, args.output)


def _cmd_verify(args: argparse.Namespace) -> int:
    segments = load_chapter(Path(args.chapter))
    edits = _load_run(Path(args.run_output))
    if any(edit.reason in ("error", "not-run") for edit in edits):
        print("finish the run first: its output still has error or not-run edits",
              file=sys.stderr)
        return 2
    try:
        verifier = _judge(args)
    except ValueError as exc:
        print(exc, file=sys.stderr)
        return 1
    with BookDB(Path(args.db) if args.db else _default_db()) as db:
        try:
            result = verify_edits(
                segments, edits, verifier=verifier, db=db, workers=args.verify_workers
            )
        finally:
            verifier.close()
    return _write(result, args.output)


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
    _add_judge_args(run, required=False)

    verify = sub.add_parser(
        "verify", help="re-check a run output with a judge (second pass, editor unloaded)"
    )
    verify.add_argument("chapter")
    verify.add_argument("run_output", help="JSON written by `bookpolish run -o`")
    verify.add_argument("-o", "--output")
    verify.add_argument("--db", default="")
    _add_judge_args(verify, required=True)

    args = parser.parse_args(argv)
    return _cmd_run(args) if args.cmd == "run" else _cmd_verify(args)


if __name__ == "__main__":
    raise SystemExit(main())
