"""Offline checks for Step 3: BM25 ranking/filter and RRF fusion (no DB, no model)."""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.hybrid import HybridRRFRetriever  # noqa: E402
from src.lexical import BM25Retriever, tokenize  # noqa: E402


def chunk(cid, text, tax="general"):
    return {"id": cid, "text": text, "source_id": "d", "source": "d.pdf", "page": 1,
            "metadata": {"taxonomy": tax}}


CHUNKS = [chunk("c1", "Backdoor poisoning attacks insert a trigger.", "predictive_ai"),
          chunk("c2", "Prompt injection attacks target LLM agents.", "generative_ai"),
          chunk("c3", "Privacy attacks reconstruct training data.", "predictive_ai")]


class Fake:
    def __init__(self, order): self.order = order
    def search(self, query, *, filters=None, top_k=3):
        return [{**next(c for c in CHUNKS if c["id"] == i), "rank": r + 1, "score": 1.0}
                for r, i in enumerate(self.order[:top_k])]


class Step3Tests(unittest.TestCase):
    def test_tokenize_rejoins_hyphenated_line_break(self):
        self.assertEqual(tokenize("gener-\nalize the Model"), ["generalize", "model"])

    def test_bm25_ranks_and_filters(self):
        bm = BM25Retriever(CHUNKS)
        self.assertEqual(bm.search("backdoor trigger", top_k=3)[0]["id"], "c1")
        out = bm.search("attacks", filters={"taxonomy": "generative_ai"}, top_k=3)
        self.assertEqual([r["id"] for r in out], ["c2"])
        with self.assertRaises(ValueError):
            bm.search("attacks", filters={"page": 1})

    def test_rrf_uses_ranks_not_raw_scores(self):
        h = HybridRRFRetriever(Fake(["c1", "c2", "c3"]), Fake(["c2", "c3", "c1"]), candidates=3, k=60)
        out = h.search("q", top_k=3)
        self.assertEqual(out[0]["id"], "c2")  # ranks 2 + 1 beat 1 + 3
        self.assertEqual(out[0]["fusion"], {"dense_rank": 2, "bm25_rank": 1})
        self.assertEqual([r["rank"] for r in out], [1, 2, 3])


if __name__ == "__main__":
    unittest.main()