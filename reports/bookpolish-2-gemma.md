# bookpolish-2 against bookpolish-1 on Gemma 4 E4B

Same model, same server, same book. bookpolish-2 finished all 3,269 paragraphs in 17 minutes from one process, against 26 minutes from four. It rejected 13% fewer paragraphs and shipped no broken quotation marks. The fate-note conditional both earlier runs flipped is now kept.

| | bookpolish-1 | bookpolish-2 |
|---|---:|---:|
| Wall time | 26 min, 4 processes | 17 min, 1 process, `--workers 4` |
| Edited | 1,824 | 1,906 |
| Unchanged | 756 | 765 |
| Fallback | 689 | 598 |
| Paragraphs whose text changed | 1,855 | 1,926 |
| Paragraphs with an unbalanced quote | 4 | 0 |
| Paragraphs that gained quote marks | 14 | 0 |
| Words versus the machine English | −594 | −579 |

72.0% of paragraphs came out identical across the two runs.

## What changed in the tool

- **Conditional gate.** The count of bare "if" and "unless" must match. "As if" is not counted.
- **Person gate.** An edit may drop or add a grammatical person ("I saw X" → "X"). It may not lose one person and gain another ("you can only wait" → "I can only wait").
- **Quotations stay whole.** Sentences are split only where quote marks balance, and the gate compares quote parity with the source. Before, a two-sentence quotation was cut in half, and the model closed each half, so one utterance became two.
- **Whitespace.** A fallback paragraph is now returned byte for byte.
- **Workers.** Every segment is ingested in narrative order first, then four requests run at once against the server's four slots. One cache, one evidence log.
- **Token estimate.** A CJK character counts as one token. On 300 sampled prompts, Gemma's tokenizer measured the old chars/4 estimate at 0.73–0.91 of the real count, and the new one at 0.94–1.08 (median 1.01).
- **Glossary, retries, `<think>` stripping, per-sentence counts.** Not exercised by this comparison; covered by tests.

## The lines the earlier reports flagged

**Chapter 9, the fate note.** 天不生我齊木春 is a conditional. Gemma dropped "if" again, and the gate now rejected the sentence. The machine line stands.

| Machine English | bookpolish-1 | bookpolish-2 |
|---|---|---|
| [Fate Note: If heaven had not given birth to me, Qi Muchun, the way of swordsmanship would be like a long night! … | [Fate Note: Heaven did not give birth to me, Qi Muchun, the way of swordsmanship would be like a long night! … | [Fate Note: If heaven had not given birth to me, Qi Muchun, the way of swordsmanship would be like a long night! … |

**Quotations.** bookpolish-1 accepted these because each half of a cut quotation passed on its own.

| Machine English | bookpolish-1 | bookpolish-2 |
|---|---|---|
| "It's open! It's open!" | "It's open! "It's open!" | "It's open! It's open!" |
| "What?! Defection? Why?" | "What?!" "Defection?" "Why?" | "What?! Defection? Why?" |
| "And this system has no cool-down time. Once the investment is completed, you can get returns immediately." | "Furthermore, this system has no cool-down time." "Once the investment is complete, you can receive returns immediately." | "Furthermore, this system has no cool-down time; once the investment is complete, you can receive returns immediately." |

**Chapter 3, a duplicated sentence.** bookpolish-1 merged the second sentence into the first and still kept the second.

| Machine English | bookpolish-1 | bookpolish-2 |
|---|---|---|
| "I don't practice fire-based techniques, and there is no cold poison in my body. This thing will just eat ashes if it is left here." | "… in my body, so this thing will just gather dust if I keep it here." This thing will just eat ashes if it is left here." | "… in my body. This thing will just gather dust if it is left here." |

**Chapter 14, a viewpoint swap.** The person gate rejected it.

| Machine English | bookpolish-1 | bookpolish-2 |
|---|---|---|
| If you want to invest in this girl, you can only wait until it is refreshed tomorrow. | If I want to invest in this girl, I can only wait until it refreshes tomorrow. | (machine line kept) |

## What it still misses

- **Fish-belly white** still becomes "the pale color of a fish's belly". No gate judges idioms. A glossary entry (`魚肚白 = fish-belly white`) would lock the phrase.
- **Agarwood** stayed agarwood with Gemma in both runs. The sandalwood swap was the 35B model's, and it needs a glossary entry to block. That model was not re-run.
- **Added first person.** "Then it's up to you" → "Then I will let you" adds a person without removing one, so the person gate allows it.

## How this run was made

The llama.cpp `b10488` CUDA 12.4 server was started with the flags from the earlier reports:

```text
llama-server.exe -m gemma-4-E4B-it-qat-UD-Q4_K_XL.gguf --host 127.0.0.1 --port 8080 -c 8192 --reasoning off -fit on -fa on -a gemma-4-e4b --jinja
```

The log reported `n_slots = 4` and `n_ctx_slot = 8192`, with no truncated requests and no server errors.

```text
python -m bookpolish run chapter.json -o gemma-out.json --model gemma-4-e4b --ctx 4096 --timeout 180 --workers 4 --db gemma.sqlite
```

Run on 4 Oct 2026 against the same aligned chapters 1–21 of twkan book 103145, with policy `bookpolish-2` and temperature 0.2. Across the book, 1,959 sentences were accepted as edits, 604 were rejected, and none were skipped. In 20 fallback paragraphs, other sentences were still kept. Replaying the current gates over this run's output rejects none of its 1,959 accepted sentences.
