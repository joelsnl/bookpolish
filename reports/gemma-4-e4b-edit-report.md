# Gemma 4 E4B against the machine English

Gemma 4 E4B copy-edited all 3,269 paragraphs of *Lurking in the Tibetan Scripture Pavilion* by Chang Qingteng. It is the model that fits this job: the weights sit in the 12 GB GPU, and the book finished in 26 minutes. The prose is shorter by 594 words. Most edits are small, and a few still move the meaning.

| | |
|---|---|
| Paragraphs whose text changed | 1,855 |
| Paragraphs accepted as an edit | 55.8% |
| Paragraphs with a rejected sentence | 21.1% |
| Words versus the machine English | −594 |

Of 3,269 paragraphs, 1,824 were accepted rewrites, 756 came back identical, and 689 were marked fallback because at least one sentence failed a gate. In 31 of those fallback paragraphs, another sentence was still kept, so 1,855 paragraphs differ from the epub. Word count moved from 36,908 to 36,314.

## Read both versions

Chapter 1, paragraphs 1–12, is the opening of the book.

### Chapter 1 opening

| Machine English | After Gemma 4 E4B |
|---|---|
| "Elder Ye?" | "Elder Ye?" |
| On the first floor of the Sutra Pavilion, the light is dim. | On the first floor of the Sutra Pavilion, the light was dim. |
| The air was filled with the unique musty smell of old paper, mixed with a hint of agarwood. | The air was filled with the unique musty smell of old paper, mixed with a faint scent of agarwood. |
| A cautious voice sounded softly in front of the counter, as if afraid of disturbing some ferocious beast. | A cautious voice sounded softly in front of the counter, as if afraid of disturbing some ferocious beast. |
| "Elder Ye?" | "Elder Ye?" |
| The voice called again, with a bit of testing. | The voice called again, with a hint of probing. |
| Ye Xuan slowly opened his eyes from the wicker chair. | Ye Xuan slowly opened his eyes from the rattan chair. |
| He yawned and glanced lazily at the wooden platform in front of him. | He yawned and glanced lazily at the wooden platform before him. |
| A yellowed thread-bound book, "Qi Gathering Jue", was lying there quietly. | A yellowed thread-bound book, "Qi Gathering Jue", was lying there quietly. |
| Standing beside the book was a young boy, wearing gray and white outer disciple clothes, with an awkward look on his face. | Standing beside the book was a young boy, wearing gray and white outer disciple clothes, with an awkward look on his face. |
| Ye Xuan rubbed his sleepy eyes and said casually: | Ye Xuan rubbed his somewhat sleepy eyes and said casually: |
| "Borrow for one month, ten low-grade spiritual stones." | "Borrow for one month, ten low-grade spiritual stones." |

Six of these twelve lines changed.

### Closer to the Chinese

**Chapter 1.** 沉香 stays agarwood. The change is scent, not the wood.

| Machine English | After Gemma 4 E4B |
|---|---|
| The air was filled with the unique musty smell of old paper, mixed with a hint of agarwood. | The air was filled with the unique musty smell of old paper, mixed with a faint scent of agarwood. |

**Chapter 1.** 試探 is probing, not a test.

| Machine English | After Gemma 4 E4B |
|---|---|
| The voice called again, with a bit of testing. | The voice called again, with a hint of probing. |

**Chapter 9.** 聚氣圓滿 comes back as a stage, and 摩拳擦掌 becomes the fists.

| Machine English | After Gemma 4 E4B |
|---|---|
| Behind him, there were three followers who had gathered their strength, and they were all gearing up and showing evil intentions. | Behind him, there were three followers who had reached the peak of gathering qi, and they were all flexing their fists with ill intentions. |

**Chapter 15.** The grammar is repaired. 窺探天機 is still rendered as spying on secrets.

| Machine English | After Gemma 4 E4B |
|---|---|
| The secret of spying is backfired, and the inner demons take advantage of it. This is a trauma at the level of the soul, and ordinary medicine is naturally ineffective. | Spying on the heavenly secrets backfired, and the inner demons took advantage of it. This is a trauma at the soul level, and ordinary medicine is naturally ineffective. |

**Chapter 21, last line.** 真的 was the fragment "real".

| Machine English | After Gemma 4 E4B |
|---|---|
| "real!" | "Really!" |

### Meaning drift

**Chapter 9.** 天不生我齊木春，劍道萬古如長夜 means if Heaven had not given birth to Qi Muchun, the sword path would be an eternal night. The rewrite drops "if" and leaves a broken claim. The paragraph is tagged fallback because another sentence was rejected; this sentence was kept.

| Machine English | After Gemma 4 E4B |
|---|---|
| [Fate Note: If heaven had not given birth to me, Qi Muchun, the way of swordsmanship would be like a long night! This boy is a prodigy of swordsmanship who has never appeared in thousands of years. He will surely reach the pinnacle of swordsmanship in the future and become a swordsman of a generation!] | [Fate Note: Heaven did not give birth to me, Qi Muchun, the way of swordsmanship would be like a long night! This boy is a prodigy of swordsmanship who has never appeared in thousands of years. He will surely reach the pinnacle of swordsmanship in the future and become a swordsman of a generation!] |

**Chapter 4.** 魚肚白 is the pale color of dawn. The rewrite takes the fish literally.

| Machine English | After Gemma 4 E4B |
|---|---|
| There was a fish-belly white color in the east, and the first ray of morning light shone through the window lattice and fell on Ye Xuan's body. | The east was tinged with the color of a fish's belly, and the first ray of morning light shone through the window lattice, falling on Ye Xuan's body. |

**Chapter 3.** The "I" is gone, which matches the narration. 龍眼 is a longan; "dragon-eye" keeps the calque.

| Machine English | After Gemma 4 E4B |
|---|---|
| I saw an elixir the size of a dragon's eye lying quietly on the velvet. The elixir was round and had three flame-like elixir patterns on its surface. | A dragon-eye-sized pill lay quietly on the velvet. The pill was round and had three flame-like patterns on its surface. |

## Paragraph outcome by chapter

Each row is one chapter. Counts are paragraphs. Edited means the gate accepted a rewrite of that paragraph. Unchanged means the model returned the same text. Fallback means at least one sentence was rejected and the original sentence was kept.

Source: Gemma 4 E4B bookpolish run on 4 Oct 2026, chapters 1–21 of twkan book 103145.

| Chapter | Edited | Unchanged | Fallback | Paragraphs |
|---|---:|---:|---:|---:|
| 1 | 53 | 28 | 21 | 102 |
| 2 | 74 | 38 | 34 | 146 |
| 3 | 69 | 29 | 15 | 113 |
| 4 | 86 | 36 | 28 | 150 |
| 5 | 58 | 12 | 26 | 96 |
| 6 | 82 | 36 | 27 | 145 |
| 7 | 62 | 16 | 14 | 92 |
| 8 | 58 | 21 | 24 | 103 |
| 9 | 60 | 30 | 28 | 118 |
| 10 | 90 | 39 | 42 | 171 |
| 11 | 74 | 15 | 27 | 116 |
| 12 | 102 | 41 | 30 | 173 |
| 13 | 93 | 34 | 31 | 158 |
| 14 | 136 | 71 | 61 | 268 |
| 15 | 76 | 32 | 21 | 129 |
| 16 | 70 | 35 | 32 | 137 |
| 17 | 100 | 38 | 40 | 178 |
| 18 | 103 | 43 | 40 | 186 |
| 19 | 73 | 21 | 25 | 119 |
| 20 | 158 | 75 | 62 | 295 |
| 21 | 147 | 66 | 61 | 274 |
| **Total** | **1,824** | **756** | **689** | **3,269** |

## What the pass is doing

Gemma edits less eagerly than the larger Qwen run of the same file. The typical change is tense, a plainer verb, or a slightly shorter sentence. The gates still block a dropped name, quantity, gendered pronoun, or negation, and they still do not check that the remaining words mean the same thing.

### Where it gets closer

Agarwood stays agarwood, with the smell softened to a faint scent. 試探 becomes probing. The rattan chair replaces wicker. The last line of the book becomes "Really". A Qi Gathering stage comes back, in plainer words than the capitalized term a larger model used.

### Where it drifts

**The fate-note conditional lost its if.** The machine English kept "if Heaven had not given birth to Qi Muchun". Gemma dropped "if" and left "Heaven did not give birth to me, Qi Muchun, the way of swordsmanship would be like a long night". Both sides still contain one "not", so the negation gate allowed the sentence.

The dawn phrase "fish-belly white" became "the color of a fish's belly". The longan-sized pill stayed a dragon-eye. Names, the ten spiritual stones, and Ye Xuan's pronouns stayed put.

## llama.cpp and bookpolish parameters

Binary: the same llama.cpp `b10488` CUDA 12.4 server used for the 35B run.

```text
llama-server.exe -m gemma-4-E4B-it-qat-UD-Q4_K_XL.gguf --host 127.0.0.1 --port 8080 -c 8192 --reasoning off -fit on -fa on -a gemma-4-e4b --jinja
```

| Parameter | Value | What it did |
|---|---|---|
| `-m` | `gemma-4-E4B-it-qat-UD-Q4_K_XL.gguf` (4.0 GB) | Weights. `mmproj-F16.gguf` and `mtp-gemma-4-E4B-it.gguf` were in the same snapshot and were not loaded. |
| `-c`, `--ctx-size` | 8192 | Log: `n_ctx_slot = 8192`. |
| `--reasoning` | `off` | Same as the 35B server. The edit has to land in `message.content` inside bookpolish's token budget. |
| `-fit`, `--fit` | `on` | The model stayed on the GPU. nvidia-smi showed about 4.5 GB used, against about 11.5 GB for the 35B server. No CPU tensor-override warning. |
| `-fa`, `--flash-attn` | `on` | Flash attention forced on. |
| `--jinja` | on | Template from the GGUF. The loader overrode `<|tool_response|>` and `</s>` as control tokens. |
| `-a`, `--alias` | `gemma-4-e4b` | The `model` field bookpolish sent. |
| `--host` / `--port` | `127.0.0.1:8080` | Same endpoint shape. |
| MTP draft | not passed | The 57 MB MTP GGUF was left on disk. |
| `-ngl`, `-np`, `-t`, KV type, server temperature | not passed | Log defaults: `n_slots = 4`, `kv_unified = true`, `n_threads = 8`. Temperature came from bookpolish on each request. |

bookpolish flags for the full novel:

| Parameter | Value |
|---|---|
| `--model` | `gemma-4-e4b` |
| `--ctx` | 4096 |
| `--timeout` | 180 seconds |
| Workers | 4, same chapter split as the 35B run |
| Request `temperature` | 0.2 |
| Request `max_tokens` | Same formula as the 35B run |

The 35B workers used `--timeout 300`. Gemma used 180. Neither run stopped on a timeout. `--ctx 4096` is again the tool's packing budget, not the server window of 8192.

A sampled Gemma prompt in the log evaluated at about 566 tokens per second, then generated at about 40 tokens per second. Under the four live workers, generation on a busy slot dropped to roughly 16–26 tokens per second.

The Qwen3.5 4B BF16 probe used the same server flags, with `-a qwen3.5-4b` and that model's GGUF. `--fit on` filled about 10.2 GB. Its MTP block (`blk.32.nextn.*`) was ignored. bookpolish on that probe was `--ctx 4096 --timeout 180 --model qwen3.5-4b`. One slot showed prompt eval around 510 tokens per second and generation around 47 tokens per second, but only one request was in flight.

## Why this model

The file is `gemma-4-E4B-it-qat-UD-Q4_K_XL.gguf`, about 4.0 GB, from the local Hugging Face cache. On this RTX 4070 it used about 4.5 GB and finished the novel in 26 minutes with four bookpolish workers. Qwen3.5 35B-A3B is the larger general model in that cache, and it does not fit in 12 GB. Qwen3.5 4B BF16 does fit, at about 10 GB, but the same 12 diagnostic paragraphs took 10.9 seconds against Gemma's 5.3, and two of them were rejected outright.

The novel is the shortest epub in `.huaepub\books`, 117 KB, 21 chapters. The English is the epub text. The Chinese is the cached source for twkan book 103145. Five site-promo lines that existed only in the Chinese were left out. Policy `bookpolish-1`, temperature 0.2, reasoning off.
