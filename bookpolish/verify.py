# Author: joelsnl
"""Second-stage meaning check for edits the regex gates accepted.

The regex gates see names, numbers, pronouns, person, negation, and
conditionals. They cannot see a noun that now means a different thing
(agarwood -> sandalwood), an invented detail, or a changed actor.
Two judges ask literal yes/no questions per edited sentence and reject the
edit when an answer reaches the threshold:

- ChatLogprobVerifier reads P(Yes) from any chat model's logprobs. Pointed at
  the editor's own llama-server it costs no extra memory, and it is the free
  default worth trying first.
- SystemOneVerifier talks to a `POST /v1/systemone` server: Kev, Laya, or
  Winnow running locally, or TypeSafe's hosted Jev.

Measured with Jev 1.13 as the judge on 200 accepted Gemma edits plus 11 known
misses and 60 injected noun swaps (reports/research-program.md): at 0.7 it
flagged 9/11 misses, 50/60 swaps, and 11/200 ordinary edits, about half of
which were real drift. A local judge must be measured the same way before
its threshold is trusted (scripts/eval_judge.py).
"""

from __future__ import annotations

import json
import math
import os
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urlparse

from bookpolish.engine import ModelError

QUESTIONS_VERSION = "q1"
QUESTIONS = {
    "changed_thing": {
        "type": "noul",
        "instructions": "Does `edited_english` name a different object, material, substance, "
        "creature, place, or title than `machine_english` does for the same thing?",
        "criteria": {
            "true": "A noun now refers to something different (e.g. agarwood became "
            "sandalwood, a sword became a spear)",
            "false": "Same things, possibly reworded or with synonyms",
        },
    },
    "added_claim": {
        "type": "noul",
        "instructions": "Does `edited_english` state a fact, action, title, or detail that "
        "appears in neither `machine_english` nor `chinese_source`?",
        "criteria": {
            "true": "New information was invented",
            "false": "Only rewording of information already present",
        },
    },
    "changed_who": {
        "type": "noul",
        "instructions": "Does `edited_english` change who does, says, wants, or permits "
        "something compared with `machine_english`?",
    },
    "changed_logic": {
        "type": "noul",
        "instructions": "Does `edited_english` turn a condition, hypothetical, question, or "
        "possibility in `machine_english` into a plain statement, or the reverse?",
    },
}
_RETRY_STATUS = frozenset({429, 500, 502, 503, 504})


HOSTED_JEV = "https://api.typesafe.ai"


class _JudgeBase:
    """Shared plumbing: URL check, thread pool, and POST with retries."""

    def __init__(self, url: str, model: str, timeout: float, retries: int, parallel: int):
        parsed = urlparse(url)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise ValueError("verifier url must be an http or https URL")
        if not model:
            raise ValueError("verifier model name is required; it keys the cache")
        self.url = url.rstrip("/")
        self.model = model
        self.timeout = timeout
        self.retries = retries
        self.api_key = ""
        self._pool = ThreadPoolExecutor(max_workers=parallel)
        self._sleep = time.sleep

    def close(self) -> None:
        self._pool.shutdown(wait=False, cancel_futures=True)

    def _post(self, path: str, body: dict) -> dict:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        request = urllib.request.Request(
            self.url + path, data=json.dumps(body).encode(), headers=headers, method="POST"
        )
        for attempt in range(self.retries + 1):
            try:
                with urllib.request.urlopen(request, timeout=self.timeout) as response:
                    return json.loads(response.read().decode())
            except urllib.error.HTTPError as exc:
                if exc.code not in _RETRY_STATUS or attempt == self.retries:
                    raise ModelError(f"verifier HTTP {exc.code}") from exc
            except (urllib.error.URLError, TimeoutError, ConnectionError) as exc:
                if attempt == self.retries:
                    raise ModelError(f"verifier unreachable: {exc}") from exc
            except ValueError as exc:
                raise ModelError(f"verifier response unreadable: {exc}") from exc
            self._sleep(2.0 * 2**attempt)
        raise AssertionError("unreachable")


class SystemOneVerifier(_JudgeBase):
    """Flags edited sentences whose meaning moved, via POST /v1/systemone.

    `url` is the server root; the text of each edit is sent there. `model`
    names the judge and goes into the cache key, so name Kev-0.8B and Laya
    differently even when they share a port.
    """

    def __init__(
        self,
        url: str,
        model: str,
        threshold: float = 0.7,
        api_key: str | None = None,
        timeout: float = 60,
        retries: int = 3,
        parallel: int = 8,
    ):
        super().__init__(url, model, timeout, retries, parallel)
        self.api_key = api_key or ""
        if self.url == HOSTED_JEV:
            self.api_key = self.api_key or os.environ.get("TYPESAFE_API_KEY", "")
            if not self.api_key:
                raise ValueError("hosted Jev needs TYPESAFE_API_KEY")
        self.threshold = threshold

    @property
    def name(self) -> str:
        """Keys cached verdicts: a different judge or threshold asks again."""
        return f"systemone:{self.model}:{QUESTIONS_VERSION}:{self.threshold}"

    def check(self, source: str, pairs: list[tuple[str, str]]) -> list[bool]:
        """True for each (machine, edited) pair that keeps its meaning."""
        states = [
            {"chinese_source": source, "machine_english": machine, "edited_english": edited}
            for machine, edited in pairs
        ]
        return [
            max(answers.values()) < self.threshold
            for answers in self._pool.map(self._ask, states)
        ]

    def _ask(self, state: dict) -> dict[str, float]:
        body = self._post(
            "/v1/systemone", {"state": state, "model": self.model, "questions": QUESTIONS}
        )
        try:
            return {key: float(answer["noul"]) for key, answer in body["answers"].items()}
        except (KeyError, TypeError, ValueError) as exc:
            raise ModelError(f"verifier response unreadable: {exc}") from exc


LOGPROB_QUESTIONS = ("changed_thing", "added_claim")
_LOGPROB_SYSTEM = (
    "You check a copy edit of machine-translated fiction. Compare EDITED with MACHINE "
    "(and the Chinese SOURCE). Answer with exactly one word: Yes or No."
)


class ChatLogprobVerifier(_JudgeBase):
    """Uses any chat model, such as the editor itself, as the judge.

    Asks each question as a one-token chat completion and reads P(Yes) from
    the top logprobs (OpenAI-compatible `logprobs`/`top_logprobs`, which
    llama-server supports). Pointing it at the editor's own server costs no
    extra memory. When neither Yes nor No is among the top tokens the answer
    counts as 0.5, which flags at the default threshold: unsure means keep
    the machine line.

    Default questions and threshold come from evals/judge_set.json with Gemma 4
    E4B as the judge: "changed thing" or "added claim" >= 0.5 caught 6/11 real
    misses, 51/60 noun swaps, and 4/5 sampled drift, and flagged 5/193 good
    edits. The two other questions were noisy for this model.
    """

    def __init__(
        self,
        url: str,
        model: str,
        threshold: float = 0.5,
        questions: tuple[str, ...] = LOGPROB_QUESTIONS,
        timeout: float = 120,
        retries: int = 3,
        parallel: int = 8,
    ):
        super().__init__(url, model, timeout, retries, parallel)
        unknown = set(questions) - set(QUESTIONS)
        if unknown or not questions:
            raise ValueError(f"unknown judge questions: {sorted(unknown)}")
        self.threshold = threshold
        self.questions = tuple(questions)

    @property
    def name(self) -> str:
        return (
            f"logprob:{self.model}:{QUESTIONS_VERSION}:{','.join(self.questions)}:"
            f"{self.threshold}"
        )

    def check(self, source: str, pairs: list[tuple[str, str]]) -> list[bool]:
        jobs = [(source, m, e, q) for m, e in pairs for q in self.questions]
        scores = list(self._pool.map(lambda job: self.p_yes(*job), jobs))
        per_pair = len(self.questions)
        return [
            max(scores[i * per_pair : (i + 1) * per_pair]) < self.threshold
            for i in range(len(pairs))
        ]

    def p_yes(self, source: str, machine: str, edited: str, question: str) -> float:
        spec = QUESTIONS[question]
        text = (
            spec["instructions"]
            .replace("`edited_english`", "EDITED")
            .replace("`machine_english`", "MACHINE")
            .replace("`chinese_source`", "SOURCE")
        )
        criteria = spec.get("criteria")
        hint = (
            f"\nYes means: {criteria['true']}\nNo means: {criteria['false']}"
            if criteria
            else ""
        )
        user = (
            f"SOURCE: {source}\nMACHINE: {machine}\nEDITED: {edited}\n\n"
            f"Question: {text}{hint}\nAnswer Yes or No."
        )
        body = self._post(
            "/v1/chat/completions",
            {
                "model": self.model,
                "temperature": 0,
                "max_tokens": 1,
                "logprobs": True,
                "top_logprobs": 10,
                "messages": [
                    {"role": "system", "content": _LOGPROB_SYSTEM},
                    {"role": "user", "content": user},
                ],
            },
        )
        try:
            tops = body["choices"][0]["logprobs"]["content"][0]["top_logprobs"]
            yes = sum(math.exp(t["logprob"]) for t in tops if t["token"].strip().lower() == "yes")
            no = sum(math.exp(t["logprob"]) for t in tops if t["token"].strip().lower() == "no")
        except (KeyError, IndexError, TypeError, ValueError) as exc:
            raise ModelError(f"judge gave no logprobs: {exc}") from exc
        return yes / (yes + no) if yes + no else 0.5
