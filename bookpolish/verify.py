# Author: joelsnl
"""Second-stage meaning check for edits the regex gates accepted.

The regex gates see names, numbers, pronouns, person, negation, and
conditionals. They cannot see a noun that now means a different thing
(agarwood -> sandalwood), an invented detail, or a changed actor. JevVerifier
asks TypeSafe's Jev four literal yes/no questions per edited sentence and
rejects the edit when any answer reaches the threshold.

Measured on 200 accepted Gemma edits plus 11 known misses and 60 injected noun
swaps (reports/research-program.md): at 0.7 it flagged 9/11 misses, 50/60
swaps, and 11/200 ordinary edits, about half of which were real drift.
"""

from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor

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


class JevVerifier:
    """Flags edited sentences whose meaning moved. Sends text to api.typesafe.ai."""

    def __init__(
        self,
        api_key: str | None = None,
        threshold: float = 0.7,
        model: str = "jev-latest",
        timeout: float = 60,
        retries: int = 3,
        parallel: int = 8,
    ):
        self.api_key = api_key or os.environ.get("TYPESAFE_API_KEY", "")
        if not self.api_key:
            raise ValueError("JevVerifier needs TYPESAFE_API_KEY")
        self.threshold = threshold
        self.model = model
        self.timeout = timeout
        self.retries = retries
        self._pool = ThreadPoolExecutor(max_workers=parallel)
        self._sleep = time.sleep

    @property
    def name(self) -> str:
        """Part of the cache key: a different judge or threshold re-runs edits."""
        return f"jev:{self.model}:{QUESTIONS_VERSION}:{self.threshold}"

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

    def close(self) -> None:
        self._pool.shutdown(wait=False, cancel_futures=True)

    def _ask(self, state: dict) -> dict[str, float]:
        body = json.dumps({"state": state, "model": self.model, "questions": QUESTIONS})
        request = urllib.request.Request(
            "https://api.typesafe.ai/v1/systemone",
            data=body.encode(),
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        for attempt in range(self.retries + 1):
            try:
                with urllib.request.urlopen(request, timeout=self.timeout) as response:
                    answers = json.loads(response.read().decode())["answers"]
                return {key: float(answer["noul"]) for key, answer in answers.items()}
            except urllib.error.HTTPError as exc:
                if exc.code not in _RETRY_STATUS or attempt == self.retries:
                    raise ModelError(f"verifier HTTP {exc.code}") from exc
            except (urllib.error.URLError, TimeoutError, ConnectionError) as exc:
                if attempt == self.retries:
                    raise ModelError(f"verifier unreachable: {exc}") from exc
            except (KeyError, TypeError, ValueError) as exc:
                raise ModelError(f"verifier response unreadable: {exc}") from exc
            self._sleep(2.0 * 2**attempt)
        raise AssertionError("unreachable")
