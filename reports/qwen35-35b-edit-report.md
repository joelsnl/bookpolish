# Machine English against the polished copy

Qwen3.5 35B-A3B copy-edited all 3,269 paragraphs of the shortest novel in the library, *Lurking in the Tibetan Scripture Pavilion* by Chang Qingteng. The polished text is slightly tighter and often closer to the Chinese. A few accepted lines change the meaning anyway.

| | |
|---|---|
| Paragraphs whose text changed | 1,999 |
| Paragraphs accepted as an edit | 60.2% |
| Paragraphs with a rejected sentence | 23.5% |
| Words versus the machine English | −222 |

Share of 3,269 paragraphs: 1,968 edited, 532 unchanged, 769 fallback.

Of 3,269 paragraphs, 1,968 were accepted rewrites, 532 came back identical, and 769 were marked fallback because at least one sentence failed a gate. In 31 of those fallback paragraphs, other sentences in the same paragraph were still kept, so 1,999 paragraphs differ from the epub. Word count moved from 36,908 to 36,686.

## Read both versions

Changed lines are the ones where the two columns differ. Chapter 1, paragraphs 1–12, is the opening of the book.

### Chapter 1 opening

| Machine English | After bookpolish |
|---|---|
| "Elder Ye?" | "Elder Ye?" |
| On the first floor of the Sutra Pavilion, the light is dim. | On the first floor of the Sutra Pavilion, the light was dim. |
| The air was filled with the unique musty smell of old paper, mixed with a hint of agarwood. | The air was filled with the unique musty smell of old paper, mixed with a hint of sandalwood. |
| A cautious voice sounded softly in front of the counter, as if afraid of disturbing some ferocious beast. | A cautious voice sounded softly in front of the counter, as if afraid of disturbing some ferocious beast. |
| "Elder Ye?" | "Elder Ye?" |
| The voice called again, with a bit of testing. | The voice called again, with a hint of testing. |
| Ye Xuan slowly opened his eyes from the wicker chair. | Ye Xuan slowly opened his eyes from the rattan chair. |
| He yawned and glanced lazily at the wooden platform in front of him. | He yawned and glanced lazily at the wooden platform in front of him. |
| A yellowed thread-bound book, "Qi Gathering Jue", was lying there quietly. | A yellowed thread-bound book, "Qi Gathering Jue", lay quietly there. |
| Standing beside the book was a young boy, wearing gray and white outer disciple clothes, with an awkward look on his face. | Standing beside the book was a young boy, wearing gray and white outer disciple clothes, with an awkward look on his face. |
| Ye Xuan rubbed his sleepy eyes and said casually: | Ye Xuan rubbed his sleepy eyes and said casually: |
| "Borrow for one month, ten low-grade spiritual stones." | "Borrow for one month, ten low-grade spirit stones." |

Six of these twelve lines changed.

### Closer to the Chinese

**Chapter 9.** The Chinese says the followers are at Qi Gathering perfection, fists rubbing.

| Machine English | After bookpolish |
|---|---|
| Behind him, there were three followers who had gathered their strength, and they were all gearing up and showing evil intentions. | Behind him were three followers who had reached the peak of Qi Gathering, rubbing their fists and looking malicious. |

**Chapter 15.** 窺探天機 is peeking into heavenly secrets, not a secret of spying.

| Machine English | After bookpolish |
|---|---|
| The secret of spying is backfired, and the inner demons take advantage of it. This is a trauma at the level of the soul, and ordinary medicine is naturally ineffective. | Peeking into heavenly secrets backfires, allowing heart demons to take advantage. This is a trauma on the soul level, so ordinary medicine is naturally ineffective. |

**Chapter 3.** The narration is third person. The machine line had slipped into I.

| Machine English | After bookpolish |
|---|---|
| I saw an elixir the size of a dragon's eye lying quietly on the velvet. The elixir was round and had three flame-like elixir patterns on its surface. | A dragon-eye-sized pill lay quietly on the velvet. The pill was round, with three flame-like patterns on its surface. |

**Chapter 18.** 常勝將軍 is an ever-victorious general, and 權傾朝野 is power over the court.

| Machine English | After bookpolish |
|---|---|
| His name is Chen Feiyu, and his father is a victorious general of the Daqian Empire. He holds a large number of troops and has power over the entire government. | His name is Chen Feiyu, and his father is the Daqian Empire's ever-victorious general. He commands a large army and holds power that overshadows the entire court. |

**Chapter 21, last line of the book.** The machine fragment real is 真的.

| Machine English | After bookpolish |
|---|---|
| "real!" | "Really!" |

### Meaning drift

**Chapter 9.** 天不生我齊木春，劍道萬古如長夜 is a conditional: if Heaven had not given birth to Qi Muchun, the sword path would be an eternal night. Both lines contain one not, so the negation gate let this through. Another sentence in the same paragraph was rejected, which is why the run tagged the paragraph fallback.

| Machine English | After bookpolish |
|---|---|
| [Fate Note: If heaven had not given birth to me, Qi Muchun, the way of swordsmanship would be like a long night! This boy is a prodigy of swordsmanship who has never appeared in thousands of years. He will surely reach the pinnacle of swordsmanship in the future and become a swordsman of a generation!] | [Fate Note: Heaven did not give birth to me, Qi Muchun, and the path of the sword would be an eternal night! This boy is a prodigy of swordsmanship who has never appeared in thousands of years. He will surely ascend to the pinnacle of the sword path in the future, achieving the status of a Sword Venerable!] |

**Chapter 1.** 沉香 is agarwood. Sandalwood is a different wood.

| Machine English | After bookpolish |
|---|---|
| The air was filled with the unique musty smell of old paper, mixed with a hint of agarwood. | The air was filled with the unique musty smell of old paper, mixed with a hint of sandalwood. |

**Chapter 4.** 魚肚白 is the set phrase for the pale color of dawn. The rewrite takes the fish more literally.

| Machine English | After bookpolish |
|---|---|
| There was a fish-belly white color in the east, and the first ray of morning light shone through the window lattice and fell on Ye Xuan's body. | The east turned the color of a fish's belly, and the first ray of morning light shone through the window lattice, falling on Ye Xuan's body. |

## Paragraph outcome by chapter

Each row is one chapter. Counts are paragraphs. Edited means the gate accepted a rewrite of that paragraph. Unchanged means the model returned the same text. Fallback means at least one sentence was rejected and the original sentence was kept.

Source: bookpolish run on 3 Oct 2026, chapters 1–21 of twkan book 103145.

| Chapter | Edited | Unchanged | Fallback | Paragraphs |
|---|---:|---:|---:|---:|
| 1 | 58 | 23 | 21 | 102 |
| 2 | 90 | 18 | 38 | 146 |
| 3 | 80 | 12 | 21 | 113 |
| 4 | 89 | 20 | 41 | 150 |
| 5 | 60 | 14 | 22 | 96 |
| 6 | 85 | 30 | 30 | 145 |
| 7 | 61 | 14 | 17 | 92 |
| 8 | 60 | 15 | 28 | 103 |
| 9 | 69 | 20 | 29 | 118 |
| 10 | 99 | 17 | 55 | 171 |
| 11 | 81 | 12 | 23 | 116 |
| 12 | 112 | 25 | 36 | 173 |
| 13 | 105 | 22 | 31 | 158 |
| 14 | 157 | 52 | 59 | 268 |
| 15 | 74 | 24 | 31 | 129 |
| 16 | 77 | 25 | 35 | 137 |
| 17 | 102 | 31 | 45 | 178 |
| 18 | 116 | 29 | 41 | 186 |
| 19 | 69 | 21 | 29 | 119 |
| 20 | 170 | 55 | 70 | 295 |
| 21 | 154 | 53 | 67 | 274 |
| **Total** | **1,968** | **532** | **769** | **3,269** |

## What the pass is doing

Most accepted edits are small: tense, word order, and a more natural verb. The useful ones restore a cultivation term or a viewpoint the machine line dropped. The gates block a change that drops a name, a quantity, a gendered pronoun, or a negation, or that changes the length and shape too far. They do not check whether the remaining words still mean the same thing.

### Where it gets closer

Realm names come back when the machine English paraphrased them away, as with the peak of Qi Gathering. Set phrases such as peeking into heavenly secrets replace word-for-word nonsense. A first-person "I saw" in third-person narration is removed. The last line of the book, the fragment "real", becomes "Really".

### Where it drifts

**The fate-note conditional was flipped.** The machine English kept "if Heaven had not given birth to Qi Muchun". The polished line says Heaven did not give birth to him, and then still treats the sword path as an eternal night. That is a different claim. The negation counter saw one "not" on each side and allowed it.

Agarwood was rewritten as sandalwood, and the dawn phrase "fish-belly white" became "the color of a fish's belly". Those are accepted edits, not fallbacks. Names, numbers, and Ye Xuan's pronouns stayed put across the book, which is what the gates are built to protect.

## llama.cpp and bookpolish parameters

Binary: llama.cpp `b10488`, CUDA 12.4, `llama-server.exe` from `.huaepub\polish\llama-server`.

The server was started with this command shape. Only the model path and the `-a` alias change between runs.

```text
llama-server.exe -m Qwen3.5-35B-A3B-UD-Q4_K_XL.gguf --host 127.0.0.1 --port 8080 -c 8192 --reasoning off -fit on -fa on -a qwen3.5-35b-a3b --jinja
```

| Parameter | Value | What it did |
|---|---|---|
| `-m` | `Qwen3.5-35B-A3B-UD-Q4_K_XL.gguf` (21.8 GB) | Weights. The separate mmproj file was not loaded. |
| `-c`, `--ctx-size` | 8192 | Server context per slot. The log reported `n_ctx_slot = 8192`. |
| `--reasoning` | `off` | No chain-of-thought. bookpolish only reads `message.content`, and its `max_tokens` budget is sized for the edit, not a thinking trace. |
| `-fit`, `--fit` | `on` | Let llama.cpp place layers so the model fits the 12 GB GPU. It did not. The log says tensor overrides went to CPU, with mmap left on, and layer 0 stayed on CPU. Fused Gated Delta Net was disabled because that layer was on CPU while the fused op was assigned to CUDA. During the run the GPU held about 11.5 GB. |
| `-fa`, `--flash-attn` | `on` | Flash attention forced on. |
| `--jinja` | on | Chat template taken from the GGUF. |
| `-a`, `--alias` | `qwen3.5-35b-a3b` | Name bookpolish sent as the `model` field. |
| `--host` / `--port` | `127.0.0.1:8080` | OpenAI-compatible `POST /v1/chat/completions`. |
| MTP / draft model | not passed | `blk.40` next-token tensors in the GGUF were ignored. No `--spec-type` and no draft GGUF. |
| `-ngl` | not passed | Layer split was left to `--fit`. |
| `-np`, `--parallel` | not passed | The log still reported `n_slots = 4` and `kv_unified = true`. That is this build's default at this context size. |
| `-t`, threads | not passed | The log reported `n_threads = 8`. |
| KV cache type | not passed | Default K/V cache type. |
| Server temperature | not passed | Each request carried temperature from bookpolish. |

bookpolish then called that server with:

| Parameter | Value |
|---|---|
| `--model` | `qwen3.5-35b-a3b` |
| `--ctx` | 4096 |
| `--timeout` | 300 seconds |
| Workers | 4, one per chapter range, separate sqlite caches |
| Request `temperature` | 0.2, hardcoded in `bookpolish` |
| Request `max_tokens` | Per span, about 1.35 times the estimated input tokens plus 24, and at least 32 per sentence |

`--ctx 4096` is bookpolish's own packing budget (characters divided by 4, plus slack). It is not the server context. The server had 8192 tokens so a prompt the tool estimated under 4096 still had room when the Chinese was denser than that estimate. No request came back truncated (`truncated = 0` on the sampled timings), and the run returned no server error.

A sampled 35B prompt in the log evaluated at about 59 tokens per second, then generated at about 26 tokens per second.

## How this run was made

The model is Qwen3.5-35B-A3B, file `Qwen3.5-35B-A3B-UD-Q4_K_XL.gguf` (21.8 GB) from the local Hugging Face cache. It is the largest general-purpose model there with weights on disk. The coder snapshot has no weights, bge-small is an embedding model, and the Qwen2.5 0.5B snapshot is only a tokenizer. Gemma 4 E4B and Qwen3.5 4B are smaller. llama.cpp served it on this RTX 4070 with reasoning turned off. Four bookpolish workers shared that server and finished in 73 minutes.

The novel is the shortest epub in `.huaepub\books`, 117 KB, 21 chapters. The English is the text in the epub. The Chinese is the cached source for twkan book 103145, aligned paragraph by paragraph. Five site-promo lines that existed only in the Chinese were left out. Policy `bookpolish-1`, temperature 0.2.
