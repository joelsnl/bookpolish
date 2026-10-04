# Author: joelsnl
"""Build a bookpolish chapter file from a HuaEPUB cache, read-only.

Usage:
    python scripts/export_huaepub.py BOOK_URL -o book.json [--chapters N] [--cache PATH]

BOOK_URL is the library's source_url, e.g. https://twkan.com/book/111022.html.
Source paragraphs are split the way HuaEPUB splits them, and each one is paired
with its cached machine translation. The backend with the most hits for the
book wins (glossary-suffixed backends differ per book). Paragraphs with no
cached translation, such as site promo lines, are left out and counted.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sqlite3
import sys
from collections import Counter
from pathlib import Path

_TAGS = re.compile(r"<[^>]+>")
_WS = re.compile(r"\s+")
_DEFAULT_CACHE = Path.home() / ".huaepub" / "cache.db"


def paragraphs(html: str) -> list[str]:
    """Same split as HuaEPUB core.ad_detect.paragraphs."""
    text = _TAGS.sub("\n", html or "")
    return [line for chunk in re.split(r"[\n\r]+", text) if (line := _WS.sub(" ", chunk).strip())]


def translation_key(backend: str, source: str) -> str:
    """Same key as HuaEPUB NovelCache._translation_key."""
    normalized = _WS.sub(" ", source.strip())
    return hashlib.sha256(f"{backend}\x00{normalized}".encode()).hexdigest()


def chapter_urls(conn: sqlite3.Connection, book_url: str) -> list[str]:
    row = conn.execute(
        "select payload from chapter_lists where source_url = ?", (book_url,)
    ).fetchone()
    if row is None:
        raise SystemExit(f"no chapter list cached for {book_url}")
    return [entry["url"] for entry in json.loads(row[0])]


def pick_backend(conn: sqlite3.Connection, sample: list[str]) -> str:
    backends = [row[0] for row in conn.execute("select distinct backend from translations")]
    hits: Counter[str] = Counter()
    for backend in backends:
        keys = [translation_key(backend, text) for text in sample]
        marks = ",".join("?" * len(keys))
        hits[backend] = conn.execute(
            f"select count(*) from translations where key in ({marks})", keys
        ).fetchone()[0]
    backend, count = hits.most_common(1)[0]
    if not count:
        raise SystemExit("no cached translations match this book")
    return backend


def export(cache: Path, book_url: str, limit: int | None) -> tuple[dict, dict]:
    conn = sqlite3.connect(f"file:{cache.as_posix()}?mode=ro", uri=True)
    urls = chapter_urls(conn, book_url)[:limit]
    chapters: list[list[str]] = []
    for url in urls:
        row = conn.execute("select content from chapters where url = ?", (url,)).fetchone()
        chapters.append(paragraphs(row[0]) if row else [])
    sample = [text for chapter in chapters[:3] for text in chapter][:200]
    backend = pick_backend(conn, sample)
    segments, missing = [], 0
    for number, chapter in enumerate(chapters, start=1):
        for index, source in enumerate(chapter, start=1):
            row = conn.execute(
                "select translated from translations where key = ?",
                (translation_key(backend, source),),
            ).fetchone()
            if row is None or not row[0].strip():
                missing += 1
                continue
            segments.append(
                {"id": f"c{number}-p{index}", "chapter": number, "source": source,
                 "english": row[0].strip()}
            )
    conn.close()
    stats = {"backend": backend, "chapters": len(urls), "segments": len(segments),
             "missing": missing}
    return {"book_key": book_url, "segments": segments}, stats


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="export_huaepub")
    parser.add_argument("book_url")
    parser.add_argument("-o", "--output", required=True)
    parser.add_argument("--chapters", type=int, default=None)
    parser.add_argument("--cache", default=str(_DEFAULT_CACHE))
    args = parser.parse_args(argv)
    data, stats = export(Path(args.cache), args.book_url, args.chapters)
    Path(args.output).write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(stats), file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
