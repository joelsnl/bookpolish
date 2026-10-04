# Author: joelsnl
"""Time one server configuration over a fixed set of chapter files.

Usage:
    python scripts/bench_speed.py LABEL --model GGUF [--workers N] [--retain]
        [--files a.json b.json ...] -- [extra llama-server flags]

Starts llama-server on 127.0.0.1:8080 with the flags the reports used plus the
extra flags, polishes each file into a fresh cache, stops the server, and writes
_run/bench/results/LABEL/{summary.json,<file>-out.json}. The summary holds wall
time, paragraphs and words per minute, outcome counts, and server token rates.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import time
import urllib.request
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from bookpolish.engine import BookDB, Server, load_chapter, polish  # noqa: E402
from bookpolish.verify import SystemOneVerifier  # noqa: E402

SERVER = next(
    (Path.home() / ".huaepub" / "polish" / "llama-server").glob("*/llama-server.exe"), None
)
BASE_FLAGS = ["--host", "127.0.0.1", "--port", "8080", "-c", "8192", "--reasoning", "off",
              "-fit", "on", "-fa", "on", "-a", "bench", "--jinja"]
DEFAULT_FILES = sorted((ROOT / "_run" / "bench").glob("b*-8.json"))


def wait_ready(proc: subprocess.Popen, log: Path, limit: float = 300) -> None:
    start = time.time()
    while time.time() - start < limit:
        if proc.poll() is not None:
            raise SystemExit(f"server exited early; see {log}")
        try:
            urllib.request.urlopen("http://127.0.0.1:8080/v1/models", timeout=2).read()
            return
        except OSError:
            time.sleep(1)
    raise SystemExit("server did not become ready")


def server_rates(log: Path) -> dict:
    """Mean prompt and generation tokens/s from llama-server timing lines."""
    text = log.read_text(encoding="utf-8", errors="replace")
    prompt = [float(x) for x in re.findall(r"prompt eval time.*?([\d.]+) tokens per second", text)]
    gen = [float(x) for x in re.findall(r"\beval time.*?([\d.]+) tokens per second", text)]
    draft = [(int(a), int(d)) for a, d in
             re.findall(r"\(\s*(\d+) accepted /\s*(\d+) generated\)", text)]
    drafted = sum(d for _, d in draft)
    mean = lambda xs: round(sum(xs) / len(xs), 1) if xs else None  # noqa: E731
    return {"prompt_tps": mean(prompt), "gen_tps": mean(gen),
            "draft_acceptance": round(sum(a for a, _ in draft) / drafted, 3) if drafted else None}


def main(argv: list[str]) -> int:
    extra: list[str] = []
    if "--" in argv:
        cut = argv.index("--")
        argv, extra = argv[:cut], argv[cut + 1:]
    parser = argparse.ArgumentParser(prog="bench_speed")
    parser.add_argument("label")
    parser.add_argument("--model", required=True)
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--files", nargs="*", default=[str(p) for p in DEFAULT_FILES])
    parser.add_argument("--verify", metavar="URL", help="System One server to re-check edits")
    parser.add_argument("--verify-model", default="")
    args = parser.parse_args(argv)
    out = ROOT / "_run" / "bench" / "results" / args.label
    out.mkdir(parents=True, exist_ok=True)
    log = out / "server.log"
    command = [str(SERVER), "-m", args.model, *BASE_FLAGS, *extra]
    with log.open("w", encoding="utf-8") as handle:
        proc = subprocess.Popen(command, stdout=handle, stderr=subprocess.STDOUT)
    try:
        wait_ready(proc, log)
        reasons: Counter[str] = Counter()
        paragraphs = words = flagged = 0
        errors = []
        verifier = (
            SystemOneVerifier(args.verify, args.verify_model) if args.verify else None
        )
        start = time.time()
        for name in args.files:
            segments = load_chapter(Path(name))
            db_path = out / (Path(name).stem + ".sqlite")
            db_path.unlink(missing_ok=True)
            with BookDB(db_path) as db:
                run = polish(segments, client=Server("http://127.0.0.1:8080", "bench"),
                             db=db, workers=args.workers, close_client=True,
                             verifier=verifier)
            if run.error:
                errors.append(run.error)
            reasons.update(edit.reason for edit in run.edits)
            flagged += sum(edit.sentences_flagged for edit in run.edits)
            paragraphs += len(segments)
            words += sum(len(s.english.split()) for s in segments)
            (out / (Path(name).stem + "-out.json")).write_text(
                json.dumps([edit.__dict__ for edit in run.edits], ensure_ascii=False),
                encoding="utf-8",
            )
        seconds = time.time() - start
    finally:
        proc.terminate()
        proc.wait(timeout=60)
    summary = {
        "label": args.label, "model": Path(args.model).name, "workers": args.workers,
        "extra_flags": extra, "seconds": round(seconds, 1), "paragraphs": paragraphs,
        "paragraphs_per_min": round(paragraphs / seconds * 60, 1),
        "words_per_min": round(words / seconds * 60), "reasons": dict(reasons),
        "verify": args.verify, "sentences_flagged": flagged,
        "errors": errors, **server_rates(log),
    }
    (out / "summary.json").write_text(json.dumps(summary, indent=1), encoding="utf-8")
    print(json.dumps(summary))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
