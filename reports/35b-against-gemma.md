# 35B against the model that fits

Run Gemma 4 E4B for this book on this GPU. It finished in 26 minutes and used about 4.5 GB. Qwen3.5 35B-A3B took 73 minutes because a 22 GB model does not fit in 12 GB, and it rewrote more lines, including several cultivation phrases Gemma left flatter. The two edits are the same paragraph only 39.2% of the time.

Both reports cover all 3,269 paragraphs of *Lurking in the Tibetan Scripture Pavilion*, with the Chinese source attached. The 35B report is the largest model in the cache. The Gemma report is the best one that still fits the card and the volume of short calls.

| | |
|---|---|
| Gemma finished faster | 2.8× |
| Paragraphs with identical output | 39.2% |
| Words Gemma removed | −594 |
| Words the 35B removed | −222 |

## llama.cpp parameters

All three servers were the same binary, llama.cpp `b10488` built for CUDA 12.4. The flags that were actually passed are the same except the model file and the alias. Nothing model-specific was tuned: no manual GPU layer count, no KV cache quant, no speculative decoding, no different context.

```text
llama-server.exe -m <gguf> --host 127.0.0.1 --port 8080 -c 8192 --reasoning off -fit on -fa on -a <alias> --jinja
```

| | Qwen3.5 35B-A3B | Gemma 4 E4B | Qwen3.5 4B BF16 |
|---|---|---|---|
| Run | Full novel | Full novel | 12-line probe only |
| `-m` | `Qwen3.5-35B-A3B-UD-Q4_K_XL.gguf`, 21.8 GB, Q4 | `gemma-4-E4B-it-qat-UD-Q4_K_XL.gguf`, 4.0 GB, QAT Q4 | `Qwen3.5-4B-BF16.gguf`, 8.3 GB, BF16 |
| `-a` | `qwen3.5-35b-a3b` | `gemma-4-e4b` | `qwen3.5-4b` |
| `-c` | 8192 | 8192 | 8192 |
| `--reasoning` | off | off | off |
| `-fit` | on | on | on |
| `-fa` | on | on | on |
| `--jinja` | on | on | on |
| Host | `127.0.0.1:8080` | `127.0.0.1:8080` | `127.0.0.1:8080` |
| `-ngl` | not passed | not passed | not passed |
| `-np` | not passed; log `n_slots = 4` | not passed; log `n_slots = 4` | not passed; log `n_slots = 4` |
| Threads | not passed; log `n_threads = 8` | not passed; log `n_threads = 8` | not passed; log `n_threads = 8` |
| KV cache | default, `kv_unified = true` | default, `kv_unified = true` | default, `kv_unified = true` |
| MTP / draft | not loaded; `blk.40.nextn.*` ignored | MTP file on disk, not passed | `blk.32.nextn.*` ignored |
| `--fit` result | CPU overrides, layer 0 on CPU, fused Gated Delta Net disabled, GPU about 11.5 GB | Fully on GPU, about 4.5 GB, no CPU-override warning | On GPU, about 10.2 GB |
| Sampled prompt speed | about 59 tok/s | about 566 tok/s | about 510 tok/s, one request |
| Sampled generation | about 26 tok/s | about 40 tok/s alone, about 16–26 tok/s with four workers | about 47 tok/s, one request |

bookpolish was also aligned, with one timeout difference:

| | 35B novel | Gemma novel | 4B probe |
|---|---|---|---|
| `--ctx` | 4096 | 4096 | 4096 |
| `--timeout` | 300 s | 180 s | 180 s |
| Workers | 4 | 4 | 1 |
| Request temperature | 0.2 | 0.2 | 0.2 |
| `max_tokens` | span formula | same formula | same formula |

`--ctx 4096` is bookpolish's packing limit, estimated as characters/4. The server window was 8192 on every model, so the tool's budget was the tighter one. Temperature was not a server flag. bookpolish puts `0.2` on every chat request. `--reasoning off` mattered more than the temperature: a thinking trace would have been cut off by `max_tokens` or would have landed outside `message.content`, and the line would have been kept as a fallback.

The timeout did not change the texts. Both full runs finished with no server error. The speed gap is the fit, not a different context or sampling setup. Gemma's prompts were prefilled about ten times faster because `--fit on` could keep 4 GB on the GPU. The same flag could not keep 22 GB on a 12 GB card, so the 35B prefill fell to about 59 tokens per second. Generation rates ended up close once four workers were sharing the GPU. The 4B BF16 probe was fast per token and still the wrong full-novel choice: `--fit on` already used about 10.2 GB, leaving little spare for four slots of 8192 context.

## Share of paragraphs by outcome

Percent of 3,269 paragraphs. Edited means the gate accepted a rewrite. Unchanged means the model returned the same text. Fallback means at least one sentence was rejected.

Source: the two full bookpolish runs, 3–4 Oct 2026.

| Outcome | Qwen3.5 35B-A3B | Gemma 4 E4B |
|---|---:|---:|
| Edited | 60.2% | 55.8% |
| Unchanged | 16.3% | 23.1% |
| Fallback | 23.5% | 21.1% |

## Where the two texts agree

Counts are paragraphs in narrative order, chapters 1–21. Identical output is the first two rows together, 1,283 paragraphs, 39.2%.

| What happened | Paragraphs | Share of the book |
|---|---:|---:|
| Both left the machine line | 918 | 28.1% |
| Both made the same rewrite | 365 | 11.2% |
| Both rewrote it, and the results differ | 1,138 | 34.8% |
| Only the 35B changed it | 496 | 15.2% |
| Only Gemma changed it | 352 | 10.8% |

## The same lines, three ways

These are the lines the two reports used to judge the edit.

### Opening

Both fix the tense. The hall is already in the past.

| Machine English | Qwen3.5 35B-A3B | Gemma 4 E4B |
|---|---|---|
| On the first floor of the Sutra Pavilion, the light is dim. | On the first floor of the Sutra Pavilion, the light was dim. | On the first floor of the Sutra Pavilion, the light was dim. |

沉香 is agarwood. The 35B swaps in sandalwood. Gemma keeps the wood.

| Machine English | Qwen3.5 35B-A3B | Gemma 4 E4B |
|---|---|---|
| The air was filled with the unique musty smell of old paper, mixed with a hint of agarwood. | The air was filled with the unique musty smell of old paper, mixed with a hint of sandalwood. | The air was filled with the unique musty smell of old paper, mixed with a faint scent of agarwood. |

試探 is probing. Gemma names it. The 35B only softens "testing".

| Machine English | Qwen3.5 35B-A3B | Gemma 4 E4B |
|---|---|---|
| The voice called again, with a bit of testing. | The voice called again, with a hint of testing. | The voice called again, with a hint of probing. |

Both turn the wicker chair into rattan, which matches 藤椅.

| Machine English | Qwen3.5 35B-A3B | Gemma 4 E4B |
|---|---|---|
| Ye Xuan slowly opened his eyes from the wicker chair. | Ye Xuan slowly opened his eyes from the rattan chair. | Ye Xuan slowly opened his eyes from the rattan chair. |

### Where the 35B goes further

聚氣圓滿 and 摩拳擦掌. The 35B keeps the realm name and the rubbing fists. Gemma is plainer, and "flexing" is a looser match.

| Machine English | Qwen3.5 35B-A3B | Gemma 4 E4B |
|---|---|---|
| Behind him, there were three followers who had gathered their strength, and they were all gearing up and showing evil intentions. | Behind him were three followers who had reached the peak of Qi Gathering, rubbing their fists and looking malicious. | Behind him, there were three followers who had reached the peak of gathering qi, and they were all flexing their fists with ill intentions. |

窺探天機. The 35B reaches heavenly secrets and heart demons. Gemma repairs the grammar and stays closer to spying.

| Machine English | Qwen3.5 35B-A3B | Gemma 4 E4B |
|---|---|---|
| The secret of spying is backfired, and the inner demons take advantage of it. This is a trauma at the level of the soul, and ordinary medicine is naturally ineffective. | Peeking into heavenly secrets backfires, allowing heart demons to take advantage. This is a trauma on the soul level, so ordinary medicine is naturally ineffective. | Spying on the heavenly secrets backfired, and the inner demons took advantage of it. This is a trauma at the soul level, and ordinary medicine is naturally ineffective. |

常勝將軍 and 權傾朝野. The 35B restores both. Gemma's proposal was rejected, so the machine line stands.

| Machine English | Qwen3.5 35B-A3B | Gemma 4 E4B |
|---|---|---|
| His name is Chen Feiyu, and his father is a victorious general of the Daqian Empire. He holds a large number of troops and has power over the entire government. | His name is Chen Feiyu, and his father is the Daqian Empire's ever-victorious general. He commands a large army and holds power that overshadows the entire court. | His name is Chen Feiyu, and his father is a victorious general of the Daqian Empire. He holds a large number of troops and has power over the entire government. |

便是 and 打破頭顱. The 35B pushes this to a fight to the death. Gemma only removes the extra "but also".

| Machine English | Qwen3.5 35B-A3B | Gemma 4 E4B |
|---|---|---|
| Not to mention the Lingyun Sect, but also the Daqian royal family, if one leaks out, it will attract countless strong men to fight for it. | Not to mention the Lingyun Sect, but even the Daqian royal family, if a single one were to leak out, it would cause countless powerful experts to fight to the death to seize it. | Not to mention the Lingyun Sect, even the Daqian royal family, if one leaks out, it will attract countless strong individuals to fight over it. |

### Shared misses

Both drop "if" from 天不生我齊木春. The 35B also rewrites the rest of the note. Gemma leaves the following sentences and produces a broken one. The negation gate saw one "not" on each side.

| Machine English | Qwen3.5 35B-A3B | Gemma 4 E4B |
|---|---|---|
| [Fate Note: If heaven had not given birth to me, Qi Muchun, the way of swordsmanship would be like a long night! This boy is a prodigy of swordsmanship who has never appeared in thousands of years. He will surely reach the pinnacle of swordsmanship in the future and become a swordsman of a generation!] | [Fate Note: Heaven did not give birth to me, Qi Muchun, and the path of the sword would be an eternal night! This boy is a prodigy of swordsmanship who has never appeared in thousands of years. He will surely ascend to the pinnacle of the sword path in the future, achieving the status of a Sword Venerable!] | [Fate Note: Heaven did not give birth to me, Qi Muchun, the way of swordsmanship would be like a long night! This boy is a prodigy of swordsmanship who has never appeared in thousands of years. He will surely reach the pinnacle of swordsmanship in the future and become a swordsman of a generation!] |

Both turn 魚肚白, the pale color of dawn, into the color of a fish.

| Machine English | Qwen3.5 35B-A3B | Gemma 4 E4B |
|---|---|---|
| There was a fish-belly white color in the east, and the first ray of morning light shone through the window lattice and fell on Ye Xuan's body. | The east turned the color of a fish's belly, and the first ray of morning light shone through the window lattice, falling on Ye Xuan's body. | The east was tinged with the color of a fish's belly, and the first ray of morning light shone through the window lattice, falling on Ye Xuan's body. |

Both repair the last line of the book. 真的 was "real".

| Machine English | Qwen3.5 35B-A3B | Gemma 4 E4B |
|---|---|---|
| "real!" | "Really!" | "Really!" |

## What each report is saying

### Qwen3.5 35B-A3B

1,999 paragraphs changed, 60.2% accepted as an edit, 23.5% with a rejected sentence, 73 minutes. It restores Qi Gathering, heavenly secrets, and the ever-victorious general. It also turns agarwood into sandalwood and fish-belly white into a fish.

### Gemma 4 E4B

1,855 paragraphs changed, 55.8% accepted as an edit, 21.1% with a rejected sentence, 26 minutes in about 4.5 GB. It keeps agarwood, names the probing voice, and cuts more words. Realm terms come back in plainer English, and the Chen Feiyu line was rejected rather than improved.

Scale did not close the gate hole both reports found. Each model dropped "if" from the Qi Muchun fate note, because both versions still contain a single "not". A context-thin probe of Qwen3.5 4B BF16 left that conditional alone, and it was the slower, tighter fit: 10.9 seconds and about 10 GB for those 12 lines, against Gemma's 5.3 seconds and 4.5 GB, with two fallbacks. That 4B model was not run on the whole novel.
