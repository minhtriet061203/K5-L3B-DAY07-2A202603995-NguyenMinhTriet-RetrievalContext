"""Lexical retrieval: Okapi BM25 over the same Day 6 chunks (data/day6/chunks.json).

Tokenizer for this English corpus: NFC, re-join words hyphenated across a line break
("gener-\\nalize" -> "generalize"), lower-case, \\w+ tokens, drop a small stopword list.
No stemming. Metadata filters are applied before ranking (same keys as dense).
"""
import math
import re
import unicodedata
from collections import Counter
from typing import Any

STOPWORDS = set("""a an the and or of to in on for by with as at from is are was were be been being this that
these those it its into than then which what who whom whose how when where why do does did can could
may might should would will shall not no nor such also there their they them we our you your he she his her
i me my if so but about over under between""".split())

FILTER_KEYS = {"taxonomy", "section", "subsection", "source_id"}


def tokenize(text: str) -> list[str]:
    text = unicodedata.normalize("NFC", text)
    text = re.sub(r"(\w)-\s*\n\s*(\w)", r"\1\2", text)
    return [t for t in re.findall(r"\w+", text.casefold()) if t not in STOPWORDS]


def matches(chunk: dict[str, Any], filters: dict[str, Any] | None) -> bool:
    for key, value in (filters or {}).items():
        if key not in FILTER_KEYS:
            raise ValueError(f"filter '{key}' not allowed; allowed: {sorted(FILTER_KEYS)}")
        actual = chunk["source_id"] if key == "source_id" else chunk["metadata"].get(key)
        if actual != value:
            return False
    return True


class BM25Retriever:
    name = "bm25"

    def __init__(self, chunks: list[dict[str, Any]], k1: float = 1.5, b: float = 0.75) -> None:
        if not chunks:
            raise ValueError("no chunks")
        self.chunks, self.k1, self.b = chunks, k1, b
        self.tf = [Counter(tokenize(c["text"])) for c in chunks]
        self.len = [sum(tf.values()) for tf in self.tf]
        self.avgdl = sum(self.len) / len(self.len)
        df = Counter(t for tf in self.tf for t in tf)
        n = len(chunks)
        self.idf = {t: math.log(1 + (n - d + 0.5) / (d + 0.5)) for t, d in df.items()}

    def _score(self, i: int, terms: list[str]) -> float:
        tf, dl, s = self.tf[i], self.len[i], 0.0
        for t in terms:
            f = tf.get(t, 0)
            if f:
                s += self.idf[t] * f * (self.k1 + 1) / (f + self.k1 * (1 - self.b + self.b * dl / self.avgdl))
        return s

    def search(self, query: str, *, filters: dict[str, Any] | None = None, top_k: int = 3) -> list[dict[str, Any]]:
        if not isinstance(query, str) or not query.strip():
            raise ValueError("query must be a non-empty string")
        terms = tokenize(query)
        scored = [(self._score(i, terms), c["id"], c) for i, c in enumerate(self.chunks) if matches(c, filters)]
        scored = [x for x in scored if x[0] > 0]
        scored.sort(key=lambda x: (-x[0], x[1]))
        return [{**c, "score": round(s, 6), "rank": r + 1, "method": "bm25"}
                for r, (s, _, c) in enumerate(scored[:top_k])]