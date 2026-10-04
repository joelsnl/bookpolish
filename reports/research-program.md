# bookpolish research program

bookpolish copy-edits machine-translated web fiction with a local model and ships a change only after checks show it kept who, what, how many, whether, and if. Anything that fails a check keeps the machine line. The goal of this program is to make that pass faster on one consumer GPU while keeping the share of accepted edits that change meaning near zero.

This file is the brief for agents working on the project. It says what to measure, where the evidence stands, which questions are open, and how to run an experiment so that its result can be trusted.

## What the product is

**One line:** a safe copy-editor for machine-translated novels. It fixes the English and leaves the story alone.

**Who it is for:** readers and tools such as HuaEPUB that turn web novels into ebooks. They have the Chinese source and Google/NMT English, and they want better prose without new mistakes.

**Why it is different:** most LLM polishers rewrite and hope. bookpolish:

- treats the machine line as the safe default;
- edits with the source and neighbouring paragraphs attached;
- rejects any sentence whose names, numbers, pronouns, person, negation, conditionals, or quotes moved;
- can ask a second judge whether a noun now means something else.

Every run reports what it changed and why the rest was kept.

## Where it stands (4 Oct 2026)

| | Evidence |
|---|---|
| Full novel, Gemma 4 E4B, 12 GB RTX 4070 | 3,269 paragraphs in 17 min, one process (`reports/bookpolish-2-gemma.md`) |
| Fallback paragraphs vs bookpolish-1 | 689 → 598 |
| Broken or added quote marks | 18 paragraphs → 0 |
| Regex gate recall on injected damage | negation, gender, number 100%; conditional 94%; person 95.7%; name 94%; invented clause 100% (`scripts/eval_gates.py`) |
| Regex gate false rejects on two recorded runs | 34 of 3,934 accepted edits (0.9%) |
| Drift the regex gates still let through | about 3% of accepted edits (5 of the 11 Jev flagged out of 200 sampled; read by hand) |
| Jev as a second judge, threshold 0.7 | 9/11 real misses, 50/60 noun swaps, 4/193 good edits flagged; AUC 0.983 |
| Free local judges | The editor itself (Gemma 4 E4B, logprobs, 2 questions) AUC 0.966; Winnow-12B Q4 (logprobs, 4 questions) AUC 0.939 and 10/11 real misses; together they match Jev's recall with ~2× its false flags (4–6% of good edits, each of which just keeps the machine line) |
| Other open judges zero-shot | Kev-4B AUC 0.909 but 3 s per item and fills the GPU; Kev-0.8B 0.74; Laya near chance |
| Speed on the 1,837-paragraph benchmark | 150.8 → **306.6 paragraphs/min (2.03×)** with 8 slots + Gemma MTP drafting 6 tokens; outcome counts unchanged within noise |

## Metrics

Every experiment reports both groups. A speed result that moves accuracy, or an accuracy result that moves speed, has to say so.

**Accuracy (lower is better unless noted)**

- **False-accept rate.** Share of accepted edits that change meaning, judged against the Chinese.
  - Measured with `evals/judge_set.json` and a hand-labelled gold set (Track D).
  - Proxy: damage recall from `scripts/eval_gates.py`.
- **False-reject rate.** Share of edits a past run accepted that a gate change now rejects (`scripts/replay_gates.py`). Rejecting a good edit costs only a missed improvement, so this may rise a little to buy a lower false-accept rate.
- **Edit yield (higher is better).** Share of paragraphs that change. It is a measure of usefulness, not of correctness.

**Speed**

- **Paragraphs per minute** on the benchmark (`scripts/bench_speed.py`), same model, fresh cache.
- **Server metrics:** generated tokens per second and draft acceptance from the server log.

**Cost**

- External calls per book: none by default.
- VRAM headroom left beside the editor.

## The benchmark kit

| Tool | What it does |
|---|---|
| `scripts/export_huaepub.py BOOK_URL -o book.json [--chapters N]` | Builds an aligned chapter file from the HuaEPUB cache (read-only). Any of the 85 books in `~/.huaepub/books` can become a benchmark. |
| `_run/bench/b111022-8.json`, `b108244-8.json`, `b109954-8.json` | The standing speed benchmark: first 8 chapters of three small books, 1,837 paragraphs, 34.5k words. Rebuild with the exporter if `_run/` is gone. |
| `scripts/bench_speed.py LABEL --model GGUF [--workers N] -- [server flags]` | Starts llama-server, runs the benchmark, writes `_run/bench/results/LABEL/summary.json`. |
| `scripts/replay_gates.py` / `scripts/eval_gates.py` | Gate false rejects on recorded runs, and recall on injected damage. No GPU needed. |
| `scripts/eval_judge.py URL NAME` | Scores any `/v1/systemone` judge on `evals/judge_set.json`, beside Jev's stored answers. |

## Research tracks, ranked

### A. Throughput: the cheapest wins first

Recommended server today, 2.03× the original setup (S7):

```text
llama-server -m gemma-4-E4B-it-qat-UD-Q4_K_XL.gguf -c 8192 --reasoning off -fit on -fa on --jinja -np 8 --spec-type draft-mtp -md mtp-gemma-4-E4B-it.gguf --spec-draft-n-max 6
bookpolish run ... --workers 8
```

1. **Slots (done).** 8 slots is the peak on a 12 GB 4070. 12 and 16 slots are slower even with a doubled cache, so the card is compute-bound.
2. **Speculative decoding (done, tune further).**
   - Speculation pays off only together with 8 slots: +25% on top of them, but about +8% at 4 slots.
   - Next: `--spec-draft-n-max` 4/8, `--spec-type ngram-simple,draft-mtp` together, and `ngram-mod`.
3. **Fewer generated tokens.** Have the model return only changed labels (`[2] …`) and treat a missing label as unchanged. About 30% of sentences come back unchanged, so the output shrinks by about that much.
   - Risk: small models drift toward "no change". This needs a `POLICY` bump and an edit-yield comparison.
4. **Skip paragraphs that are already fine.**
   - A cheap scorer that predicts "the model will return this unchanged", such as HuaEPUB's `mtl_score` regexes or a small classifier trained on this project's own run logs.
   - Measure the share skipped against edits lost.
5. **Model choice.** Gemma 4 E4B fits with room to spare. Qwen3.5-4B was slower per line in the probe. Any new candidate must beat Gemma on the speed benchmark *and* on false-accept rate.

### B. Verification without a paid service

Jev proved a second judge catches what regex cannot: agarwood→sandalwood, invented details, changed actors. It is a paid trial, so it is used only as a reference. Local results so far (`evals/judge_*.json`, `scripts/eval_judge.py`):

| Judge | thing | claim | who | logic | Fit beside the editor |
|---|---:|---:|---:|---:|---|
| Jev 1.13 (hosted, reference) | 0.951 | 0.960 | 0.769 | 0.508 | n/a |
| Gemma 4 E4B, logprobs (the editor) | 0.965 | 0.923 | 0.781 | 0.368 | yes, it is the editor |
| Winnow-12B Q4_K_M, logprobs | 0.958 | 0.936 | 0.903 | 0.826 | no: second pass |
| Kev-4B (systemone) | 0.874 | 0.811 | 0.762 | 0.435 | no, and 3 s/item |
| Kev-0.8B / Laya (systemone) | ≤ 0.74 | | | | yes, but too weak zero-shot |

Values are AUC per question; 0.5 is chance.

**Shipped stack:** edit with Gemma, then run `verify` with Gemma on "changed thing" and "added claim" (threshold 0.5) through the same server. Optionally run a second `verify` with Winnow on all four questions after unloading Gemma. Gemma ≥ 0.5 or Winnow ≥ 0.7 caught 10/11 real misses, 51/60 noun swaps, and 5/5 sampled drift, and flagged 12/193 good edits. Jev at 0.7 caught 9/11, 50/60, and 5/5, and flagged 4/193.

Open work:

1. **Fewer false flags.** The local stack flags 2–3× more good edits than Jev.
   - Tune per-question thresholds on a larger judge set.
   - Run Winnow through its own `/v1/systemone` server (patched llama.cpp: Linux/WSL, or a CUDA build on Windows), which reads answers the way it was trained.
   - Try Winnow Q5/Q6 if they fit.
2. **Distil Jev into a small open judge.** While the trial lasts:
   - Label 3,000–5,000 accepted edits with Jev. That is about $0.10 at the published price.
   - Fine-tune Kev-0.8B (LoRA; `kev.train`) or Laya (ModernBERT, ~421M) on those labels.
   - Score with `scripts/eval_judge.py`. The target is AUC ≥ 0.95 at under 100 ms per edit beside the editor.
3. **Cascade.** Ask only the two questions that work for open models ("changed thing" and "added claim"; "changed logic" was inverted for Kev and Laya). Run the judge only on edits that changed a content word, which a lemma diff can find in about 1 ms.
4. **Calibrate per judge.** Kev's scores sit far lower than Jev's, so a fixed 0.7 is wrong for it. Store a per-judge threshold fitted on the judge set: false-flag rate ≤ 3% on ok edits, then maximise recall.

### C. Edit quality

1. **Glossaries.** HuaEPUB already harvests per-book glossaries (`~/.huaepub/glossaries`), but they are noisy (verb+name fragments).
   - Filter them to names and set phrases.
   - Feed them in with `--glossary`.
   - Add a curated idiom list for common xianxia set phrases (魚肚白 fish-belly white, 抱大腿 hug a thigh, 韭菜 leeks).
   - Glossary terms are locked by the gate, which is the only current fix for idiom literalisation.
2. **Prompt.**
   - Tell the model to keep established set-phrase renderings.
   - Measure the effect on the judge set and on edit yield, not by eye.
3. **Context.** Earlier-source memory is two paragraphs. Test whether chapter-level names and terms (entity records) reduce name and title errors.

### D. A gold set people can trust

Synthetic damage and Jev labels are proxies. Build a hand-labelled set:

- **Scope:** 300 accepted edits, 150 rejected, from at least three books.
- **Fields:** Chinese, machine, edited, meaning changed (none / minor / major), MQM category, better / same / worse.
- **Effort:** about 3–4 hours of reading.
- **Second label:** a strong LLM labels 100 items; report agreement.
- **Reporting:** Wilson 95% intervals. At n = 300, a 3% rate is about ±2%.

### E. Packaging (side track)

- **One command:** `bookpolish serve` that finds llama-server and the GGUF and starts them with the tuned flags.
- **HuaEPUB integration:** replace the body of `core/local_polish.py:polish_paragraphs` in novelDownloader with a `bookpolish.polish` call. Change its cache backend name so old `span-polish:v2` rows are not reused. HuaEPUB's older polish path has never run, according to its logs.

## How agents run an experiment

This is the autoresearch loop: one variable, one fixed benchmark, keep or discard.

1. **State it first.** Write the hypothesis and the metric it should move before changing anything.
2. **Change one thing.** A server flag, a gate, a prompt line. Never two.
3. **Run the matching tool:**
   - speed → `bench_speed.py`
   - gates → `eval_gates.py` + `replay_gates.py`
   - judges → `eval_judge.py`
4. **Keep or discard:**
   - **Keep** when the target metric improves and no other metric worsens beyond noise. Run-to-run noise on the benchmark is about ±3% for paragraphs/min and ±20 paragraphs for outcome counts.
   - **Discard** otherwise.
   - A simpler change that ties is a keep.
5. **Record and commit:**
   - Append the result to the log below.
   - When a gate or the prompt changes, bump `POLICY` in `engine.py` and add a regression test from a real example.
   - Run `python -m pytest tests -q` and `python -m ruff check bookpolish tests scripts`.
   - Commit with the numbers in the message.
6. **Hygiene:**
   - Never weaken a test to pass.
   - Never put two GPU workloads on the card during a speed run.
   - Never send book text to an external service without the user's say-so.

## Experiment log

| # | Change | Result | Decision |
|---|---|---|---|
| G1 | Conditional gate (if/unless) | Caught the fate-note flip; 14/2043 and 18/1891 recorded edits now rejected, nearly all real defects | keep |
| G2 | Quote-aware sentence split + parity gate | Broken/added quote paragraphs 18 → 0 on full novel | keep |
| G3 | Person gate: compare counts, not presence | Person recall 46.8% → 95.7%; +2 false rejects, both real viewpoint changes | keep |
| S0 | Baseline: 4 slots, 4 workers | 150.8 paragraphs/min, 1,837 paragraphs | baseline |
| S1 | 8 slots, 8 workers | 244.6 /min (+62%); outcomes within noise | keep |
| S2 | n-gram speculative, n=3 m=16, 4 slots | 165.9 /min (+10%); overlapped a stray GPU process, rerun as S2b | superseded |
| S3 | Gemma MTP draft, 4 slots, 3 drafted | 165.8 /min (+10%); ~95% acceptance at 3 tokens | tuned in S7 |
| J1 | Jev 1.13 judge | AUC 0.983; 9/11 real, 4/193 false flags at 0.7 | reference only (paid) |
| J2 | Laya zero-shot | Near chance; two questions inverted | discard as-is; fine-tune candidate |
| J3 | Kev-0.8B zero-shot | Best question AUC 0.74; never fires at 0.7 | discard as-is; fine-tune candidate |
| J4 | Kev-4B zero-shot | AUC 0.909 (thing/claim); 3.1 s per item; fills 12 GB | too heavy beside the editor |
| J5 | Gemma 4 E4B (the editor) as logprob judge | thing/claim AUC 0.966; 0.5: 6/11 real, 51/60 swaps, 5/193 false flags; 206 ms/item for 4 questions | keep, default judge |
| J6 | Winnow-12B Q4 as logprob judge (second pass) | all four questions useful (who 0.903, logic 0.826); 0.7: 10/11 real, 44/60 swaps, 7/193 false flags; 549 ms/item | keep, optional second pass |
| S2b | n-gram speculative, n=3 m=16, 4 slots (clean rerun) | 163.2 /min (+8%), 51.5% acceptance | superseded |
| S4 | 8 slots + n-gram m=8 | 289.7 /min (1.92×), 67.7% acceptance | superseded by S7 |
| S5 | 12 slots | 228.1 /min, below 8 slots | discard |
| S6 | 16 slots, -c 16384 | 237.7 /min, below 8 slots: compute-bound, not cache-bound | discard |
| S7 | 8 slots + Gemma MTP, 6 drafted | **306.6 /min (2.03×)**, 69% acceptance, outcomes within noise | keep: recommended server config |
| S8 | 4 slots + Gemma MTP, 6 drafted | 161.0 /min | speculation pays off only with 8 slots |
