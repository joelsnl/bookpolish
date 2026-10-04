"""Concurrency, retries, parsing, and the CLI against a local fake server."""

from __future__ import annotations

import io
import json
import re
import sqlite3
import sys
import tempfile
import threading
import time
import unittest
import urllib.error
from contextlib import redirect_stderr, redirect_stdout
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from bookpolish.__main__ import main  # noqa: E402
from bookpolish.engine import (  # noqa: E402
    BookDB,
    ModelError,
    Segment,
    Server,
    parse_labels,
    polish,
    tokens,
)

ROOT = Path(__file__).resolve().parents[1]


def spans(user: str) -> list[str]:
    body = re.search(r"<replace>\n(.*)\n</replace>", user, re.S).group(1)
    return re.findall(r"^\[\d+\] (.*)$", body, re.M)


def tense_fix(user: str) -> str:
    """Answer every span, turning "is" into "was" so edits are visible."""
    out = [re.sub(r"\bis\b", "was", span) for span in spans(user)]
    return "\n".join(f"[{i}] {text}" for i, text in enumerate(out, start=1))


class Slow:
    """Fake client that records how many requests overlap."""

    def __init__(self, fail_on: str | None = None):
        self.model = "fake-model"
        self.fail_on = fail_on
        self.lock = threading.Lock()
        self.active = 0
        self.peak = 0
        self.seen: list[str] = []

    def generate(self, system, user, max_tokens):
        del system, max_tokens
        with self.lock:
            self.active += 1
            self.peak = max(self.peak, self.active)
            self.seen.append(spans(user)[0])
        try:
            time.sleep(0.02)
            if self.fail_on and self.fail_on in user:
                raise ModelError("slot crashed")
            return tense_fix(user)
        finally:
            with self.lock:
                self.active -= 1

    def close(self):
        pass


def book(count: int) -> list[Segment]:
    return [
        Segment("book", f"p{i}", 1, f"Mira is at gate {i}.", source=f"源{i}")
        for i in range(count)
    ]


class WorkerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = BookDB(Path(self.tmp.name) / "t.sqlite")

    def tearDown(self):
        self.db.close()
        self.tmp.cleanup()

    def test_workers_overlap_requests(self):
        client = Slow()
        polish(book(8), client=client, db=self.db, workers=4)
        self.assertGreater(client.peak, 1)
        self.assertLessEqual(client.peak, 4)

    def test_workers_keep_narrative_order_and_results(self):
        sequential = polish(book(8), client=Slow(), db=self.db, workers=1)
        other = BookDB(Path(self.tmp.name) / "other.sqlite")
        try:
            parallel = polish(book(8), client=Slow(), db=other, workers=4)
        finally:
            other.close()
        self.assertEqual(
            [(e.segment_id, e.english, e.reason) for e in parallel.edits],
            [(e.segment_id, e.english, e.reason) for e in sequential.edits],
        )
        self.assertEqual(parallel.edits[3].english, "Mira was at gate 3.")

    def test_one_worker_is_sequential(self):
        client = Slow()
        polish(book(4), client=client, db=self.db, workers=1)
        self.assertEqual(client.peak, 1)

    def test_error_stops_new_work_and_keeps_in_flight_edits(self):
        client = Slow(fail_on="gate 2.")
        run = polish(book(10), client=client, db=self.db, workers=3)
        reasons = [edit.reason for edit in run.edits]
        self.assertEqual(run.error, "slot crashed")
        self.assertEqual(reasons[:2], ["edited", "edited"])
        self.assertEqual(reasons[2], "error")
        # p3 and p4 were already in flight with p2; nothing after them started.
        self.assertEqual(reasons[3:5], ["edited", "edited"])
        self.assertEqual(reasons[5:], ["not-run"] * 5)
        self.assertEqual(len(client.seen), 5)

    def test_in_flight_edits_are_cached_after_an_error(self):
        polish(book(10), client=Slow(fail_on="gate 2."), db=self.db, workers=3)
        retry = Slow()
        run = polish(book(10), client=retry, db=self.db, workers=3)
        self.assertIsNone(run.error)
        redone = sorted(f"Mira is at gate {i}." for i in (2, 5, 6, 7, 8, 9))
        self.assertEqual(sorted(retry.seen), redone)

    def test_rejects_zero_workers(self):
        with self.assertRaises(ValueError):
            polish(book(1), client=Slow(), db=self.db, workers=0)

    def test_sentence_counts_on_a_partial_fallback(self):
        english = "Mira is at the gate. She is calm."

        class Partial(Slow):
            def generate(self, system, user, max_tokens):
                return "[1] Mira was at the gate.\n[2] He was calm."

        edit = polish([Segment("b", "s", 1, english)], client=Partial(), db=self.db).edits[0]
        self.assertEqual(edit.reason, "fallback")
        self.assertEqual(edit.english, "Mira was at the gate. She is calm.")
        self.assertEqual((edit.sentences_edited, edit.sentences_rejected), (1, 1))
        cached = polish([Segment("b", "s", 1, english)], client=Partial(), db=self.db).edits[0]
        self.assertTrue(cached.cached)
        self.assertEqual((cached.sentences_edited, cached.sentences_rejected), (1, 1))


class ParsingTests(unittest.TestCase):
    def test_think_trace_is_dropped(self):
        text = "<think>[1] scratch [2] work</think>\n[1] Mira looked up."
        self.assertEqual(parse_labels(text, 1), ["Mira looked up."])

    def test_think_without_opening_tag(self):
        self.assertEqual(parse_labels("plan it\n</think>[1] Mira waited.", 1), ["Mira waited."])

    def test_truncated_think_falls_back(self):
        self.assertIsNone(parse_labels("<think>still reasoning about [1]", 1))

    def test_cjk_counts_about_a_token_per_character(self):
        # 11 ideographs, plus the full stop counted like Latin text.
        self.assertEqual(tokens("葉玄從藤椅上緩緩睜開眼。"), 12)
        self.assertEqual(tokens("Ye Xuan slowly opened his eyes."), 8)


class MigrationTests(unittest.TestCase):
    def test_old_cache_table_gains_count_columns(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "old.sqlite"
            conn = sqlite3.connect(path)
            conn.execute(
                "create table cache (key text primary key, english text not null, "
                "accepted integer not null, reason text not null, model text not null)"
            )
            conn.execute("insert into cache values ('k', 'Mira.', 1, 'edited', 'm')")
            conn.commit()
            conn.close()
            with BookDB(path) as db:
                edit = db.get_cached("k", "s")
            self.assertEqual((edit.english, edit.sentences_edited), ("Mira.", 0))


def http_error(code: int) -> urllib.error.HTTPError:
    return urllib.error.HTTPError("http://x", code, "err", {}, io.BytesIO(b"busy"))


class RetryTests(unittest.TestCase):
    def server(self) -> Server:
        server = Server("http://127.0.0.1:9", "m", timeout=1, retries=2)
        server._sleep = mock.Mock()
        return server

    def reply(self, text: str):
        response = mock.MagicMock()
        response.read.return_value = json.dumps(
            {"choices": [{"message": {"content": text}}]}
        ).encode()
        response.__enter__.return_value = response
        return response

    def test_retries_busy_server_then_succeeds(self):
        server = self.server()
        effects = [http_error(503), TimeoutError("slow"), self.reply("[1] ok")]
        with mock.patch("urllib.request.urlopen", side_effect=effects) as urlopen:
            self.assertEqual(server.generate("s", "u", 10), "[1] ok")
        self.assertEqual(urlopen.call_count, 3)
        self.assertEqual([c.args[0] for c in server._sleep.call_args_list], [2.0, 4.0])

    def test_client_error_is_not_retried(self):
        server = self.server()
        with mock.patch("urllib.request.urlopen", side_effect=[http_error(400)]) as urlopen:
            with self.assertRaisesRegex(ModelError, "HTTP 400"):
                server.generate("s", "u", 10)
        self.assertEqual(urlopen.call_count, 1)

    def test_gives_up_after_retries(self):
        server = self.server()
        down = urllib.error.URLError("refused")
        with mock.patch("urllib.request.urlopen", side_effect=[down] * 3) as urlopen:
            with self.assertRaisesRegex(ModelError, "refused"):
                server.generate("s", "u", 10)
        self.assertEqual(urlopen.call_count, 3)


class FakeChat(BaseHTTPRequestHandler):
    """OpenAI-shaped server. The first chat request gets a 503."""

    failures = 1

    def do_GET(self):
        self._send(200, {"data": [{"id": "fake-chat"}]})

    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        if FakeChat.failures:
            FakeChat.failures -= 1
            self._send(503, {"error": "loading"})
            return
        answer = "<think>easy</think>\n" + tense_fix(body["messages"][1]["content"])
        self._send(200, {"choices": [{"message": {"content": answer}}]})

    def _send(self, code, payload):
        data = json.dumps(payload).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, *args):
        pass


class CliTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.httpd = ThreadingHTTPServer(("127.0.0.1", 0), FakeChat)
        threading.Thread(target=self.httpd.serve_forever, daemon=True).start()
        FakeChat.failures = 1
        self.host = f"http://127.0.0.1:{self.httpd.server_address[1]}"

    def tearDown(self):
        self.httpd.shutdown()
        self.httpd.server_close()
        self.tmp.cleanup()

    def test_run_end_to_end_with_workers_and_glossary(self):
        chapter = Path(self.tmp.name) / "chapter.json"
        chapter.write_text(
            json.dumps(
                {
                    "book_key": "demo",
                    "segments": [
                        {"id": f"p{i}", "chapter": 1, "source": "沉香", "english": text}
                        for i, text in enumerate(
                            [
                                "Ye Xuan is in the pavilion.",
                                "The air is thick with agarwood.",
                                "The voice is soft.",
                            ]
                        )
                    ],
                }
            ),
            encoding="utf-8",
        )
        out = Path(self.tmp.name) / "out.json"
        with mock.patch("bookpolish.engine.RETRY_DELAY", 0):
            code = main(
                [
                    "run",
                    str(chapter),
                    "-o",
                    str(out),
                    "--host",
                    self.host,
                    "--db",
                    str(Path(self.tmp.name) / "db.sqlite"),
                    "--workers",
                    "2",
                    "--glossary",
                    str(ROOT / "fixtures" / "glossary.json"),
                ]
            )
        self.assertEqual(code, 0)
        result = json.loads(out.read_text(encoding="utf-8"))
        self.assertEqual(result["model"], "fake-chat")
        self.assertEqual(result["summary"], {"edited": 3})
        self.assertEqual(
            [edit["english"] for edit in result["edits"]],
            [
                "Ye Xuan was in the pavilion.",
                "The air was thick with agarwood.",
                "The voice was soft.",
            ],
        )
        self.assertEqual(
            result["edits"][0]["sentences"],
            {"edited": 1, "rejected": 0, "skipped": 0, "flagged": 0},
        )

    def test_unreachable_server_is_a_clean_error(self):
        err = io.StringIO()
        with redirect_stderr(err), redirect_stdout(io.StringIO()):
            code = main(
                [
                    "run",
                    str(ROOT / "fixtures" / "chapter.json"),
                    "--host",
                    "http://127.0.0.1:9",
                    "--timeout",
                    "1",
                    "--db",
                    str(Path(self.tmp.name) / "db.sqlite"),
                ]
            )
        self.assertEqual(code, 1)
        self.assertIn("could not read a model id", err.getvalue())


if __name__ == "__main__":
    unittest.main()
