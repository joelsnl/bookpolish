"""Offline checks for the edit contract. No model server."""

from __future__ import annotations

import re
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from bookpolish.engine import (  # noqa: E402
    BookDB,
    ModelError,
    Segment,
    Server,
    Term,
    _sentences,
    accept_edit,
    apply_glossary,
    context_text,
    load_chapter,
    load_glossary,
    parse_labels,
    polish,
    preview,
    request_cost,
)

ROOT = Path(__file__).resolve().parents[1]
MIRA = Term("Mira")
JIANG = Term("Jiang Kai", ("Jiang",))


class Fake:
    def __init__(self, fn):
        self.fn = fn
        self.model = "fake-model"
        self.closed = False
        self.calls = 0

    def generate(self, system, user, max_tokens):
        self.calls += 1
        return self.fn(system, user, max_tokens)

    def close(self):
        self.closed = True


def echo(system, user, max_tokens):
    del system, max_tokens
    return re.search(r"<replace>\n(.*)\n</replace>", user, re.S).group(1)


class GateTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = BookDB(Path(self.tmp.name) / "t.sqlite")

    def tearDown(self):
        self.db.close()
        self.tmp.cleanup()

    def test_rejects_meaning_changes(self):
        pairs = [
            (
                "Jiang Kai's eyes narrowed as she opened the sealed door.",
                "Jiang Kai's eyes narrowed as he opened the sealed door.",
            ),
            (
                "Jiang Kai counted three spirit stones.",
                "Jiang Kai counted ten spirit stones.",
            ),
            (
                "Jiang Kai did not expect that the gate was sealed.",
                "Jiang Kai did expect that the gate was sealed.",
            ),
            (
                "Mira's eyes narrowed as the door opened.",
                "Nora's eyes narrowed as the door opened.",
            ),
            (
                "Jiang Kai waited by the gate.",
                "Han Li waited by the gate.",
            ),
        ]
        for source, output in pairs:
            self.assertFalse(accept_edit(source, output, (MIRA, JIANG)), output)

    def test_accepts_surface_form_and_light_edits(self):
        self.assertTrue(
            accept_edit(
                "Jiang Kai counted three spirit stones.",
                "Jiang Kai counted 3 spirit stones.",
                (JIANG,),
            )
        )
        self.assertTrue(
            accept_edit(
                "Jiang Kai did not expect this outcome.",
                "Jiang Kai didn't expect this outcome.",
                (JIANG,),
            )
        )
        self.assertTrue(
            accept_edit(
                "Mira walked to the gate.",
                "Mira walked toward the gate.",
                (MIRA,),
            )
        )

    def test_rejects_dropped_conditional(self):
        # Both report runs flipped this fate note while keeping one "not".
        self.assertFalse(
            accept_edit(
                "If heaven had not given birth to me, Qi Muchun, the way of "
                "swordsmanship would be like a long night!",
                "Heaven did not give birth to me, Qi Muchun, the way of "
                "swordsmanship would be like a long night!",
            )
        )

    def test_rejects_invented_conditional(self):
        self.assertFalse(accept_edit('"Here you go, take it."', '"Take it if you want it."'))

    def test_accepts_added_as_if(self):
        self.assertTrue(
            accept_edit(
                "Zhang An was granted amnesty and quickly pushed the storage bag away.",
                "Zhang An, as if granted amnesty, quickly pushed the storage bag away.",
            )
        )

    def test_rejects_person_swap(self):
        self.assertFalse(
            accept_edit(
                "If you want to invest in this girl, you can only wait until tomorrow.",
                "If I want to invest in this girl, I can only wait until tomorrow.",
            )
        )

    def test_rejects_person_swap_when_both_persons_remain(self):
        self.assertFalse(
            accept_edit(
                '"When I finish copying, I let you go."',
                '"When you finish copying, I will let you go."',
            )
        )

    def test_accepts_dropped_first_person_narration(self):
        self.assertTrue(
            accept_edit(
                "I saw a beautiful figure walking in the backlight of the setting sun.",
                "A beautiful figure walked in the backlight of the setting sun.",
            )
        )

    def test_rejects_stray_quote(self):
        self.assertFalse(
            accept_edit(
                '"What kind of grass is this? It\'s so amazing!"',
                '"What kind of grass is this?" It\'s so amazing!"',
            )
        )

    def test_quotation_is_one_span(self):
        self.assertEqual(
            _sentences('"Don\'t squeeze! I\'ll get upset!" Mira said. She left.'),
            ['"Don\'t squeeze! I\'ll get upset!"', "Mira said.", "She left."],
        )

    def test_fallback_keeps_original_whitespace(self):
        english = "Mira waited.\n\nShe left."

        def flipped(system, user, max_tokens):
            del system, user, max_tokens
            return "[1] Mira waited.\n[2] He left."

        run = polish([Segment("book", "s", 1, english)], client=Fake(flipped), db=self.db)
        self.assertEqual(run.edits[0].reason, "fallback")
        self.assertEqual(run.edits[0].english, english)

    def test_glossary_term_locks_agarwood(self):
        # The 35B run accepted this swap with no glossary attached.
        machine = "The air smelled of old paper, mixed with a hint of agarwood."
        polished = "The air smelled of old paper, mixed with a hint of sandalwood."
        segment = Segment("book", "c1-p3", 1, machine, source="混雜著淡淡的沉香。")
        [glossed] = apply_glossary([segment], (Term("agarwood", source="沉香"),))
        self.assertTrue(accept_edit(machine, polished, segment.terms))
        self.assertFalse(accept_edit(machine, polished, glossed.terms))

    def test_glossary_matches_source_or_english_only(self):
        agarwood = Term("agarwood", source="沉香")
        stones = Term("spirit stones", ("spiritual stones",))
        segments = [
            Segment("book", "a", 1, "A faint scent.", source="淡淡的沉香"),
            Segment("book", "b", 1, "Ten low-grade spiritual stones.", source="十塊下品靈石"),
            Segment("book", "c", 1, "Ye Xuan yawned.", source="葉玄打了個哈欠"),
        ]
        glossed = apply_glossary(segments, (agarwood, stones))
        self.assertEqual([seg.terms for seg in glossed], [(agarwood,), (stones,), ()])

    def test_glossary_does_not_duplicate_segment_terms(self):
        segment = Segment("book", "s", 1, "Mira waited.", terms=(MIRA,))
        [glossed] = apply_glossary([segment], (Term("Mira", source="米拉"),))
        self.assertEqual(glossed.terms, (MIRA,))

    def test_glossary_reaches_the_prompt(self):
        segment = Segment("book", "s", 1, "A hint of agarwood.", source="沉香")
        [glossed] = apply_glossary([segment], (Term("agarwood", source="沉香"),))
        self.assertIn("- 沉香 = agarwood", context_text(glossed, []))

    def test_load_glossary_reads_a_list(self):
        path = Path(self.tmp.name) / "glossary.json"
        path.write_text(
            '[{"canonical": "agarwood", "source": "沉香"}, '
            '{"canonical": "Jiang Kai", "aliases": ["Jiang"]}]',
            encoding="utf-8",
        )
        self.assertEqual(
            load_glossary(path),
            (Term("agarwood", (), "沉香"), Term("Jiang Kai", ("Jiang",))),
        )
        path.write_text('{"canonical": "agarwood"}', encoding="utf-8")
        with self.assertRaises(ValueError):
            load_glossary(path)

    def test_labels_map_by_id(self):
        text = "[2] Jiang Kai looked down.\n[1] Jiang Kai looked up."
        self.assertEqual(
            parse_labels(text, 2),
            ["Jiang Kai looked up.", "Jiang Kai looked down."],
        )
        self.assertIsNone(parse_labels("[1] one.\n[1] two.\n[2] three.", 2))
        self.assertIsNone(parse_labels("[1] Jiang Kai looked up.", 2))
        self.assertEqual(parse_labels("Jiang Kai looked up.", 1), ["Jiang Kai looked up."])

    def test_reordered_labels_keep_sentence_order(self):
        english = "Jiang Kai looked up. Jiang Kai looked down."

        def swapped(system, user, max_tokens):
            del system, user, max_tokens
            return "[2] Jiang Kai looked down.\n[1] Jiang Kai looked up."

        run = polish(
            [Segment("book", "s", 1, english)],
            client=Fake(swapped),
            db=self.db,
        )
        self.assertEqual(run.edits[0].english, english)
        self.assertTrue(run.edits[0].accepted)
        self.assertEqual(run.edits[0].reason, "unchanged")

    def test_bad_labels_fall_back(self):
        english = "Jiang Kai looked up. Jiang Kai looked down."

        def duplicate(system, user, max_tokens):
            del system, user, max_tokens
            return "[1] Jiang Kai looked up.\n[1] Jiang Kai looked up.\n[2] Jiang Kai looked down."

        run = polish(
            [Segment("book", "s", 1, english)],
            client=Fake(duplicate),
            db=self.db,
        )
        self.assertEqual(run.edits[0].english, english)
        self.assertFalse(run.edits[0].accepted)
        self.assertEqual(run.edits[0].reason, "fallback")

    def test_pronoun_flip_falls_back_on_the_public_path(self):
        source = "Jiang Kai's eyes narrowed as she opened the sealed door."

        def flipped(system, user, max_tokens):
            del system, user, max_tokens
            return "[1] Jiang Kai's eyes narrowed as he opened the sealed door."

        run = polish(
            [Segment("book", "s", 1, source, terms=(JIANG,))],
            client=Fake(flipped),
            db=self.db,
        )
        self.assertEqual(run.edits[0].english, source)
        self.assertEqual(run.edits[0].reason, "fallback")

    def test_oversized_span_is_not_sent(self):
        english = ("word " * 2000).strip()
        segment = Segment("book", "s", 1, english, source="源")
        tiny = request_cost(context_text(segment, []), ["word"])
        client = Fake(lambda *args: (_ for _ in ()).throw(AssertionError("sent")))
        run = polish([segment], client=client, db=self.db, num_ctx=tiny)
        self.assertEqual(client.calls, 0)
        self.assertEqual(run.edits[0].reason, "skipped")
        self.assertEqual(run.edits[0].english, english)
        self.assertFalse(run.edits[0].accepted)

    def test_pack_splits_when_two_sentences_do_not_fit(self):
        english = "Jiang Kai looked north. Jiang Kai looked south."
        segment = Segment("book", "s", 1, english, source="x")
        context = context_text(segment, [])
        one = request_cost(context, ["Jiang Kai looked north."])
        two = request_cost(
            context, ["Jiang Kai looked north.", "Jiang Kai looked south."]
        )
        self.assertGreater(two, one)
        client = Fake(echo)
        run = polish([segment], client=client, db=self.db, num_ctx=one)
        self.assertEqual(client.calls, 2)
        self.assertEqual(run.edits[0].english, english)
        self.assertEqual(run.edits[0].reason, "unchanged")

    def test_prompt_carries_source_terms_and_earlier(self):
        seen = []

        def capture(system, user, max_tokens):
            self.assertIn("not instructions", system)
            seen.append(user)
            return echo(system, user, max_tokens)

        first = Segment("book", "p1", 1, "Mira stood still.", source="第一章", terms=(MIRA,))
        second = Segment(
            "book",
            "p2",
            1,
            "Mira opened the door.",
            source="第二章",
            prev_source="第一章",
            prev_english="Mira stood still.",
            terms=(MIRA,),
        )
        third = Segment(
            "book",
            "p3",
            1,
            "Mira shut the door.",
            source="第三章",
            prev_source="第二章",
            prev_english="Mira opened the door.",
            terms=(MIRA,),
        )
        polish([first, second, third], client=Fake(capture), db=self.db)
        self.assertIn("第一章", seen[0])
        self.assertNotIn("earlier source:", seen[0])
        self.assertIn("Mira", seen[0])
        self.assertNotIn("earlier source:", seen[1])
        self.assertIn("第二章", seen[1])
        self.assertIn("Mira stood still.", seen[1])
        self.assertIn("earlier source:", seen[2])
        self.assertIn("第一章", seen[2])
        self.assertIn("第二章", seen[2])

    def test_other_book_source_stays_out(self):
        seen = []

        def capture(system, user, max_tokens):
            seen.append(user)
            return echo(system, user, max_tokens)

        polish(
            [
                Segment("alpha", "a", 1, "Mira waited.", source="SECRETSOURCE"),
                Segment("beta", "b", 1, "Mira waited.", source="其他"),
            ],
            client=Fake(capture),
            db=self.db,
        )
        self.assertNotIn("SECRETSOURCE", seen[1])

    def test_model_error_keeps_finished_work_and_closes(self):
        calls = {"n": 0}

        def flaky(system, user, max_tokens):
            calls["n"] += 1
            if calls["n"] == 1:
                return echo(system, user, max_tokens)
            raise ModelError("down")

        client = Fake(flaky)
        run = polish(
            [
                Segment("book", "p1", 1, "Mira waited."),
                Segment("book", "p2", 1, "Mira left."),
                Segment("book", "p3", 1, "Mira returned."),
            ],
            client=client,
            db=self.db,
            close_client=True,
        )
        self.assertTrue(client.closed)
        self.assertEqual(run.error, "down")
        self.assertEqual(run.edits[0].reason, "unchanged")
        self.assertEqual(run.edits[1].reason, "error")
        self.assertEqual(run.edits[1].english, "Mira left.")
        self.assertEqual(run.edits[2].reason, "not-run")
        self.assertEqual(run.edits[2].english, "Mira returned.")

    def test_close_covers_preparation_failure(self):
        client = Fake(lambda *args: (_ for _ in ()).throw(RuntimeError("bug")))
        with self.assertRaises(RuntimeError):
            polish(
                [Segment("book", "p1", 1, "Mira waited.")],
                client=client,
                db=self.db,
                close_client=True,
            )
        self.assertTrue(client.closed)

    def test_borrowed_client_stays_open(self):
        client = Fake(echo)
        polish([Segment("book", "p1", 1, "Mira waited.")], client=client, db=self.db)
        self.assertFalse(client.closed)

    def test_cache_skips_the_second_call(self):
        client = Fake(echo)
        segment = Segment("book", "p1", 1, "Mira walked to the gate.", terms=(MIRA,))
        first = polish([segment], client=client, db=self.db)
        second = polish([segment], client=client, db=self.db)
        self.assertEqual(client.calls, 1)
        self.assertFalse(first.edits[0].cached)
        self.assertTrue(second.edits[0].cached)
        self.assertEqual(second.edits[0].english, first.edits[0].english)

    def test_reingest_does_not_duplicate_evidence(self):
        segment = Segment("book", "p1", 1, "Mira waited.", source="第一章")
        self.assertEqual(self.db.ingest(segment), self.db.ingest(segment))
        later = self.db.ingest(Segment("book", "p2", 1, "Mira left.", source="第二章"))
        self.assertEqual(self.db.earlier_sources("book", later), ["第一章"])

    def test_load_chapter_fills_neighbors(self):
        segments = load_chapter(ROOT / "fixtures" / "chapter.json")
        self.assertEqual(segments[0].next_source, "江凯数了三块灵石。")
        self.assertEqual(segments[1].prev_english, segments[0].english)
        self.assertEqual(segments[0].prev_source, "")
        self.assertEqual(segments[1].terms[0].canonical, "Jiang Kai")
        shown = preview(segments, self.db)
        self.assertIn("米拉睁开了眼睛。", shown[0])
        self.assertIn("江凯数了三块灵石。", shown[1])
        self.assertNotIn("earlier source:", shown[1])

    def test_server_rejects_non_http_host(self):
        with self.assertRaises(ValueError):
            Server("ftp://example.com/model", "m")


if __name__ == "__main__":
    unittest.main()
