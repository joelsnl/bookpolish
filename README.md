# bookpolish

Copy-edits machine English for one chapter file. The host supplies the Chinese source, the machine English, and any canonical names. bookpolish returns the English it accepted, or the original line when a change would alter a name, a quantity, a gendered pronoun, or a negation.

HuaEPUB is not imported. A host integrates by calling `bookpolish.polish` with a release of this repo.

Chapter JSON is read in file order. That order is the narrative order. Neighbors are the previous and next paragraph when the file does not set them.

```bash
python -m bookpolish run fixtures/chapter.json --print-prompt
python -m bookpolish run fixtures/chapter.json -o out.json --host http://127.0.0.1:8080 --model MODEL
python -m unittest discover -s tests -v
```

The local server should expose `POST /v1/chat/completions`. Evidence and the edit cache are stored in `~/.bookpolish/bookpolish.sqlite`. Pass `--db` to use another file.

`--ctx` is the model context length in tokens (default 4096). A span that does not fit is left unchanged and is not sent.
