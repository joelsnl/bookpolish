# Twice as fast, and what a second judge can and cannot do

Same GPU, same model, same edits, at twice the speed. On a 1,837-paragraph benchmark drawn from three small books, Gemma 4 E4B went from 150.8 to 306.6 paragraphs a minute, and the share of paragraphs edited, unchanged, or kept did not move. A full 60-chapter novel took 13 minutes to edit.

The second half of this report tested whether a local model can catch the meaning drift the regex gates miss. It can catch it, but the obvious way of asking also throws away the best edits. Verification stays off by default.

| | |
|---|---|
| Benchmark speed | 150.8 → 306.6 paragraphs/min (2.03×) |
| Full novel, 4,116 paragraphs | 13.1 min to edit |
| Sentences the regex gates wrongly rejected, now kept | 95 of 886 in that novel |
| Self-judge flags on that novel that were good corrections | 15 of 16 sampled |

## Speed

Each row ran the same 1,837 paragraphs: the first 8 chapters of books 111022, 108244, and 109954 from the HuaEPUB library. Every run used a fresh cache and changed one server setting. The outcome counts stay within noise across all rows, so none of these settings changes what gets edited.

| Server setting | Paragraphs/min | vs. original | Edited | Unchanged | Fallback |
|---|---:|---:|---:|---:|---:|
| 4 slots (the setup in the earlier reports) | 150.8 | 1.00× | 910 | 568 | 359 |
| 4 slots, n-gram drafting (16 tokens) | 163.2 | 1.08× | 890 | 598 | 349 |
| 4 slots, Gemma MTP drafting (3 or 6 tokens) | 161–166 | ~1.08× | 893–916 | 572–591 | 349–353 |
| 8 slots | 244.6 | 1.62× | 898 | 596 | 343 |
| 12 slots | 228.1 | 1.51× | 895 | 590 | 352 |
| 16 slots, 16k context | 237.7 | 1.58× | 915 | 582 | 340 |
| 8 slots, n-gram drafting (8 tokens) | 289.7 | 1.92× | 899 | 588 | 350 |
| **8 slots, Gemma MTP drafting (6 tokens)** | **306.6** | **2.03×** | 924 | 571 | 342 |

Eight slots is the peak on a 12 GB RTX 4070. Twelve and sixteen slots are slower even with twice the context, because the card is out of compute, not memory. Speculative drafting is worth about 8% at four slots and about 25% on top of eight. Gemma's MTP head accepted about 95% of drafts at 3 tokens and 69% at 6, and 6 was faster overall.

```text
llama-server.exe -m gemma-4-E4B-it-qat-UD-Q4_K_XL.gguf --host 127.0.0.1 --port 8080 -c 8192 --reasoning off -fit on -fa on --jinja -np 8 --spec-type draft-mtp -md mtp-gemma-4-E4B-it.gguf --spec-draft-n-max 6
python -m bookpolish run book.json -o out.json --workers 8
```

## A whole novel

*Mortal, you're a newborn* (twkan book 111022): 60 chapters, 4,116 paragraphs, 78,306 words. It was built from the HuaEPUB cache with `scripts/export_huaepub.py`.

| | |
|---|---|
| Edit pass | 13.1 min, 314 paragraphs/min |
| Paragraphs changed | 2,049 |
| Sentences edited | 2,096 |
| Sentences rejected by the gates | 888 |
| Words | 78,306 → 77,690 |

Typical accepted edits:

| Machine English | After bookpolish |
|---|---|
| "Elder, rest assured, we will never betray you or the Miaoyin Sect." | "Supreme Elder, rest assured, we will never betray you or the Miaoyin Sect." |
| Not only do they know about Tianxing City and other islands in the Inner Star Sea, … | Not only do Tianxing City and other islands in the Inner Star Sea know, … |
| …their souls would be extracted and their spirits broken. | …their souls would be extracted and their spirits refined. |
| "Alright, you can go now. I agree to this." | "Alright, you may leave now. I have agreed to this." |

太上長老 is Supreme Elder, and 抽魂煉魄 is extracting the soul and refining the spirit. In the second row, the Chinese says the islands themselves know. The edit fixes the grammar.

## The gates threw away good edits

A capitalized word that opened a sentence was locked as a name. "Therefore" → "So", "Upon hearing" → "Hearing", and "Okay" → "Alright" all fell back to the machine line. Discourse openers and pronouns are now in the closed-word list (`bookpolish-4`).

- **Recovered:** 95 of the 886 rejected sentences in this novel now pass, and the 12 sampled were all good edits.
- **Recall:** injected-damage recall did not move on the first book. On this book, name recall moved 89.4% → 89.2% (2 of 1,409).
- **Rejected alternative:** a broader fix unlocked any opener the book also uses in lowercase. It recovered 138 sentences but let drift through ("Sending messages within the cave" → "Conducting the teleportation within the cave"), so it was discarded.

## A second judge

The regex gates cannot see a noun that now means something else. Earlier tests used TypeSafe Jev as a judge. Jev is a paid trial, so this round tested free, local judges.

| Judge | Fits beside the editor | Ranking quality (AUC) |
|---|---|---|
| Jev 1.13, hosted (reference) | n/a | 0.983 |
| Gemma 4 E4B, the editor itself, reading P(yes) | yes | 0.966 on two questions |
| Winnow-12B Q4_K_M, reading P(yes) | no, run as a second pass | 0.939 on four questions |
| Kev-4B | no, and 3 s per item | 0.909 |
| Kev-0.8B, Laya | yes | ≤ 0.74 |

On the judge set (`evals/judge_set.json`), Gemma or Winnow matched Jev's recall:

- **Real misses:** 10/11, where Jev caught 9/11.
- **Noun swaps:** 51/60, where Jev caught 50/60.
- **Good edits flagged:** 12/193, against Jev's 4/193.

The full novel showed the catch. Gemma, judging its own edits, flagged 160 of 2,096, so 7.6% of the edits were rolled back. Read against the Chinese, 15 of 16 sampled flags were corrections toward the source:

| Flagged edit | The Chinese |
|---|---|
| "infant cultivator" → "Nascent Soul cultivator" | 元嬰 |
| "below the Nascent Soul stage" → "below the Transformation God stage" | 化神之下 |
| "constellation" → "Star Palace" | 星宮 |
| "palm, like a fan" → "palm, like a whisk" | 蒲扇, a palm-leaf fan: the one real drift |

The questions asked whether the edit names a different thing than the machine line. When the machine line is wrong, a correct fix is a different thing. Winnow's extra pass (18.8 min) showed the same pattern: it caught "greets" → "has seen" for 見過 and a refuse/agree flip, but mostly flagged fixes.

Two questions anchored to the Chinese ("is the edit less faithful to the source than the machine line?") fix that. Requiring an edit to be both changed and less faithful reverted 0 of 15 corrections, but recall on real misses fell to 4/11. That is the open problem, and it is the first item of Track B in `reports/research-program.md`.

## What changed in the tool

| Command or file | What it does |
|---|---|
| `bookpolish verify CHAPTER RUN_OUTPUT --verify URL` | Checks a finished run with a judge after the editor is unloaded. Verdicts are cached. If the judge fails, unchecked edits fall back. |
| `--verify-kind chat` | Reads P(yes) from any chat model's logprobs, including the editor's own server. |
| `--verify-kind systemone` | Talks to Kev, Laya, Winnow, or Jev. |
| `scripts/export_huaepub.py` | Turns any book in the HuaEPUB library into a benchmark, read-only. |
| `scripts/bench_speed.py` | Times a server setting over a fixed set of chapter files. |
| `scripts/eval_gates.py` | Scores the gates for false rejects and recall against injected damage. |
| `scripts/eval_judge.py` | Scores a judge on `evals/judge_set.json`. |

## How this was run

- **Hardware and server:** RTX 4070 12 GB, llama.cpp `b10488` CUDA 12.4.
- **Editor:** `gemma-4-E4B-it-qat-UD-Q4_K_XL.gguf` with `mtp-gemma-4-E4B-it.gguf`.
- **Judges:** Winnow `Winnow-12B-Q4_K_M.gguf` (Piotr1215, SHA-256 checked). Kev 1.0 0.8B/4B from github.com/jaredpalmer/kev. Laya 0.3.26 from PyPI.
- **Settings:** temperature 0.2, reasoning off, `--ctx 4096`.
- **Policy:** speed runs used `bookpolish-3`, and the gate fix is `bookpolish-4`.
- **Date and data:** 4 Oct 2026, books 111022, 108244, and 109954 from the local HuaEPUB cache.
