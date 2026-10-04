"""The verify pass, with a fake judge and a mocked System One endpoint."""

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

from bookpolish.engine import BookDB, ModelError, Segment, polish, verify_edits  # noqa: E402
from bookpolish.verify import (  # noqa: E402
    HOSTED_JEV,
    ChatLogprobVerifier,
    SystemOneVerifier,
)


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


class VerifierPassTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = BookDB(Path(self.tmp.name) / "t.sqlite")
        self.segment = Segment("b", "s", 1, ENGLISH, source="沉香")

    def tearDown(self):
        self.db.close()
        self.tmp.cleanup()

    def edit_then_verify(self, judge):
        run = polish([self.segment], client=Editor(REPLY), db=self.db)
        return verify_edits([self.segment], run.edits, verifier=judge, db=self.db)

    def test_editing_records_each_sentence(self):
        edit = polish([self.segment], client=Editor(REPLY), db=self.db).edits[0]
        self.assertEqual(
            [outcome for _, _, outcome in edit.sentences], ["edited", "edited", "fallback"]
        )
        cached = polish([self.segment], client=Editor(REPLY), db=self.db).edits[0]
        self.assertTrue(cached.cached)
        self.assertEqual(cached.sentences, edit.sentences)

    def test_flagged_edit_keeps_machine_english(self):
        edit = self.edit_then_verify(Judge()).edits[0]
        self.assertEqual(
            edit.english, "The room smelled of agarwood. Ye Xuan was asleep. She is calm."
        )
        self.assertEqual(edit.reason, "fallback")
        self.assertEqual(
            (edit.sentences_edited, edit.sentences_flagged, edit.sentences_rejected), (1, 1, 1)
        )

    def test_only_gate_accepted_changes_are_checked(self):
        judge = Judge()
        self.edit_then_verify(judge)
        # "He is calm." failed the pronoun gate; it never reaches the judge.
        self.assertEqual(
            [edited for _, edited in judge.asked],
            ["The room smelled of sandalwood.", "Ye Xuan was asleep."],
        )

    def test_judge_failure_never_ships_an_unchecked_edit(self):
        run = self.edit_then_verify(Judge(fail=True))
        self.assertEqual(run.error, "judge down")
        self.assertEqual(run.edits[0].reason, "not-run")
        self.assertEqual(run.edits[0].english, ENGLISH)

    def test_unedited_paragraphs_pass_through_untouched(self):
        plain = Segment("b", "p", 1, "Mira waited.")
        echo = Editor("[1] Mira waited.")
        run = polish([plain], client=echo, db=self.db)
        judge = Judge()
        checked = verify_edits([plain], run.edits, verifier=judge, db=self.db)
        self.assertEqual(checked.edits, run.edits)
        self.assertEqual(judge.asked, [])

    def test_verdicts_are_cached_so_a_rerun_asks_nothing(self):
        self.edit_then_verify(Judge())
        again = Judge()
        edit = self.edit_then_verify(again).edits[0]
        self.assertEqual(again.asked, [])
        self.assertEqual(edit.sentences_flagged, 1)

    def test_a_different_judge_asks_again(self):
        self.edit_then_verify(Judge())

        class Other(Judge):
            name = "judge-v2"

        other = Other()
        self.edit_then_verify(other)
        self.assertEqual(len(other.asked), 2)


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



def logprob_reply(tokens: dict[str, float]):
    tops = [{"token": t, "logprob": lp} for t, lp in tokens.items()]
    return {"choices": [{"logprobs": {"content": [{"top_logprobs": tops}]}}]}


class ChatLogprobVerifierTests(unittest.TestCase):
    def setUp(self):
        self.judge = ChatLogprobVerifier("http://127.0.0.1:8080", "gemma-e4b", parallel=2)
        self.asked: list[dict] = []

    def tearDown(self):
        self.judge.close()

    def answer(self, tokens):
        def post(path, body):
            self.asked.append(body)
            return logprob_reply(tokens)

        self.judge._post = post

    def test_reads_p_yes_from_logprobs(self):
        self.answer({" Yes": -0.1, "No": -2.4})
        self.assertAlmostEqual(self.judge.p_yes("源", "a", "b", "added_claim"), 0.909, places=3)

    def test_flags_when_any_question_reaches_threshold(self):
        self.answer({"Yes": -0.69, "No": -0.69})  # exactly 0.5
        self.assertEqual(self.judge.check("源", [("a", "b")]), [False])
        self.answer({"Yes": -3.0, "No": -0.05})
        self.assertEqual(self.judge.check("源", [("a", "b")]), [True])

    def test_unsure_answer_keeps_the_machine_line(self):
        self.answer({"Maybe": -0.1})
        self.assertEqual(self.judge.check("源", [("a", "b")]), [False])

    def test_asks_one_token_per_question(self):
        self.answer({"No": -0.01})
        self.judge.check("源", [("a", "b"), ("c", "d")])
        self.assertEqual(len(self.asked), 4)
        self.assertTrue(all(body["max_tokens"] == 1 for body in self.asked))

    def test_missing_logprobs_is_a_model_error(self):
        self.judge._post = lambda path, body: {"choices": [{}]}
        with self.assertRaises(ModelError):
            self.judge.p_yes("源", "a", "b", "added_claim")

    def test_rejects_unknown_questions(self):
        with self.assertRaises(ValueError):
            ChatLogprobVerifier("http://127.0.0.1:8080", "m", questions=("vibes",))

    def test_name_tracks_questions_and_threshold(self):
        names = {
            self.judge.name,
            ChatLogprobVerifier("http://127.0.0.1:8080", "gemma-e4b", threshold=0.6).name,
            ChatLogprobVerifier(
                "http://127.0.0.1:8080", "gemma-e4b", questions=("changed_thing",)
            ).name,
        }
        self.assertEqual(len(names), 3)


if __name__ == "__main__":
    unittest.main()
