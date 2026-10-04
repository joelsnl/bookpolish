# bookpolish

Copy-edits machine English for one chapter file. The host supplies the Chinese source, the machine English, and any canonical names. bookpolish returns the English it accepted, or the original line when a change would alter a name, a quantity, a gendered pronoun, the grammatical person, a negation, or a conditional.

HuaEPUB is not imported. A host integrates by calling `bookpolish.polish` with a release of this repo.

Chapter JSON is read in file order. That order is the narrative order. Neighbors are the previous and next paragraph when the file does not set them.

```bash
python -m bookpolish run fixtures/chapter.json --print-prompt
python -m bookpolish run fixtures/chapter.json -o out.json --host http://127.0.0.1:8080 --model MODEL
python -m pytest tests -v
```

The local server should expose `POST /v1/chat/completions`. Evidence and the edit cache are stored in `~/.bookpolish/bookpolish.sqlite`. Pass `--db` to use another file.

`--ctx` is the model context length in tokens (default 4096). A span that does not fit is left unchanged and is not sent. The estimate counts each CJK character as a token and other text as four characters per token.

## Workers

`--workers N` keeps N requests in flight against one server. Match it to the server's parallel slots (llama.cpp `-np`, default 4). Every segment is ingested in narrative order before any request, so earlier-source memory and the cache are the same as a one-worker run. Results are written in narrative order. If the server fails, no new segment starts; segments already in flight keep their edits, and the rest are marked `not-run`. A rerun with the same `--db` picks up from the cache.

Timeouts, connection errors, and HTTP 429/5xx are retried twice with backoff before a segment is marked `error`.

## Glossary

`--glossary terms.json` attaches book-wide terms to every segment that mentions them, by source form in the Chinese or by English form in the machine English:

```json
[
  { "canonical": "agarwood", "source": "沉香" },
  { "canonical": "spirit stones", "aliases": ["spirit stone"], "source": "灵石" }
]
```

An attached term is listed in the prompt (`沉香 = agarwood`) and locked by the gate: an edit that drops it falls back to the machine line.

## Verification (optional)

The regex gates cannot see a noun that now means something else (agarwood → sandalwood) or an invented detail. A judge can: a System One server (`POST /v1/systemone`) such as Kev, Laya, or Winnow running locally, or hosted Jev with `TYPESAFE_API_KEY`. Each sentence that passed the gates and changed goes to the judge, and a flagged sentence keeps its machine line.

Verification is a second pass, so the editor and the judge never have to share the GPU:

```bash
python -m bookpolish run chapter.json -o edited.json --workers 8      # editor loaded
# stop the editor server, start the judge server
python -m bookpolish verify chapter.json edited.json -o final.json --verify http://127.0.0.1:8009 --verify-model kev-4b
```

`run --verify URL --verify-model NAME` does both in one process when a small judge fits beside the editor. Verdicts are cached by judge name, so an interrupted pass resumes. If the judge fails, every edit it had not checked falls back to its machine line (`not-run`). Off by default, because no open judge yet matches Jev zero-shot on this task: score one with `python scripts/eval_judge.py URL NAME` before trusting its threshold (`reports/research-program.md`).

## Output

Each edit carries `reason` (`edited`, `unchanged`, `fallback`, `skipped`, `error`, `not-run`) and per-sentence counts. A `fallback` paragraph with `sentences.edited > 0` still carries the sentences that passed. `summary` counts edits by reason.

Reasoning models may emit a `<think>` trace; it is removed before the labels are read. A trace cut off by `max_tokens` falls back, so keep reasoning off on the server when you can.

## Changing a gate

Bump `POLICY` in `engine.py` when `accept_edit` or the prompt changes; cached rows are keyed by it. Measure the change against a past run's accepted edits:

```bash
python scripts/replay_gates.py chapter.json out-part-0.json out-part-1.json
```

It prints each accepted edit the current gates would now reject, and the share.
