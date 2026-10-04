"""The optional verifier stage, with a fake judge and a mocked Jev endpoint."""

from __future__ import annotations

import io
import json
import sys
import tempfile
import unittest
import urllib.error
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from bookpolish.engine import BookDB, ModelError, Segment, polish  # noqa: E402
from bookpolish.verify import HOSTED_JEV, SystemOneVerifier  # noqa: E402


class Editor:
    model = "fake-model"

    def __init__(self, reply: str):
        self.reply = reply

    def generate(self, system, user, max_tokens):
        return self.reply

    def close(self):
        pass


class Judge:
    """Flags any edit containing a banned word; records what it was asked."""

    name = "judge-v1"

    def __init__(self, banned: str = "sandalwood", fail: bool = False):
        self.banned = banned
        self.fail = fail
        self.asked: list[tuple[str, str]] = []

    def check(self, source, pairs):
        if self.fail:
            raise ModelError("judge down")
        self.asked.extend(pairs)
        return [self.banned not in edited for _, edited in pairs]


ENGLISH = "The room smelled of agarwood. Ye Xuan is asleep. She is calm."
REPLY = "[1] The room smelled of sandalwood.\n[2] Ye Xuan was asleep.\n[3] He is calm."


class VerifierStageTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = BookDB(Path(self.tmp.name) / "t.sqlite")

    def tearDown(self):
        self.db.close()
        self.tmp.cleanup()

    def run_one(self, judge):
        segment = Segment("b", "s", 1, ENGLISH, source="沉香")
        return polish([segment], client=Editor(REPLY), db=self.db, verifier=judge)

    def test_flagged_edit_keeps_machine_english(self):
        edit = self.run_one(Judge()).edits[0]
        self.assertEqual(
            edit.english, "The room smelled of agarwood. Ye Xuan was asleep. She is calm."
        )
        self.assertEqual(edit.reason, "fallback")
        self.assertEqual(
            (edit.sentences_edited, edit.sentences_flagged, edit.sentences_rejected), (1, 1, 1)
        )

    def test_only_gate_accepted_changes_are_checked(self):
        judge = Judge()
        self.run_one(judge)
        # "He is calm." failed the pronoun gate; it never reaches the judge.
        self.assertEqual(
            [edited for _, edited in judge.asked],
            ["The room smelled of sandalwood.", "Ye Xuan was asleep."],
        )

    def test_judge_failure_stops_the_run(self):
        run = self.run_one(Judge(fail=True))
        self.assertEqual(run.error, "judge down")
        self.assertEqual(run.edits[0].reason, "error")

    def test_verifier_is_part_of_the_cache_key(self):
        self.run_one(None)
        judge = Judge()
        edit = self.run_one(judge).edits[0]
        self.assertFalse(edit.cached)
        self.assertTrue(judge.asked)
        self.assertTrue(self.run_one(Judge()).edits[0].cached)


def jev_reply(value: float):
    answers = {key: {"type": "noul", "noul": value} for key in ("a", "b")}
    response = mock.MagicMock()
    response.read.return_value = json.dumps({"answers": answers}).encode()
    response.__enter__.return_value = response
    return response


def http_error(code: int) -> urllib.error.HTTPError:
    return urllib.error.HTTPError("http://x", code, "err", {}, io.BytesIO(b""))


class SystemOneVerifierTests(unittest.TestCase):
    def setUp(self):
        self.jev = SystemOneVerifier("http://127.0.0.1:8009", "kev-0.8b", parallel=2)
        self.jev._sleep = mock.Mock()

    def tearDown(self):
        self.jev.close()

    def test_threshold_splits_kept_and_flagged(self):
        with mock.patch("urllib.request.urlopen", side_effect=[jev_reply(0.69), jev_reply(0.7)]):
            verdicts = self.jev.check("源", [("a", "b")])
            verdicts += self.jev.check("源", [("a", "c")])
        self.assertEqual(verdicts, [True, False])

    def test_retries_busy_then_answers(self):
        effects = [http_error(503), jev_reply(0.1)]
        with mock.patch("urllib.request.urlopen", side_effect=effects) as urlopen:
            self.assertEqual(self.jev.check("源", [("a", "b")]), [True])
        self.assertEqual(urlopen.call_count, 2)

    def test_auth_error_is_a_model_error(self):
        with mock.patch("urllib.request.urlopen", side_effect=[http_error(401)]):
            with self.assertRaisesRegex(ModelError, "verifier HTTP 401"):
                self.jev.check("源", [("a", "b")])

    def test_local_server_sends_no_key(self):
        with mock.patch("urllib.request.urlopen", side_effect=[jev_reply(0.1)]) as urlopen:
            self.jev.check("源", [("a", "b")])
        request = urlopen.call_args.args[0]
        self.assertEqual(request.full_url, "http://127.0.0.1:8009/v1/systemone")
        self.assertIsNone(request.get_header("Authorization"))

    def test_hosted_jev_needs_a_key(self):
        with mock.patch.dict("os.environ", {}, clear=True):
            with self.assertRaises(ValueError):
                SystemOneVerifier(HOSTED_JEV, "jev-latest")

    def test_model_name_is_required(self):
        with self.assertRaises(ValueError):
            SystemOneVerifier("http://127.0.0.1:8009", "")

    def test_name_tracks_model_and_threshold(self):
        names = {
            SystemOneVerifier("http://127.0.0.1:8009", "kev-0.8b").name,
            SystemOneVerifier("http://127.0.0.1:8009", "laya").name,
            SystemOneVerifier("http://127.0.0.1:8009", "kev-0.8b", threshold=0.8).name,
        }
        self.assertEqual(len(names), 3)


if __name__ == "__main__":
    unittest.main()
