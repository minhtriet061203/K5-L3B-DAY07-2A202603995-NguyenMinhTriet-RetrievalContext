"""Offline checks for the cross-encoder rerank method (fake scorer, no model download)."""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.agent_configs import CONFIGS  # noqa: E402
from src.lexical import BM25Retriever  # noqa: E402
from src.rerank import CrossEncoderReranker  # noqa: E402
from src.retrievers import METHODS  # noqa: E402


def chunk(cid, text, tax="general"):
    return {"id": cid, "text": text, "source_id": "d", "source": "d.pdf", "page": 1,
            "metadata": {"taxonomy": tax}}


CHUNKS = [chunk("c1", "Gradient attacks compute gradients of the model.", "predictive_ai"),
          chunk("c2", "Zeroth-order optimization estimates gradients without derivatives.", "predictive_ai"),
          chunk("c3", "Gradient based prompt attacks on LLMs.", "generative_ai")]


class KeywordScorer:
    """Fake cross-encoder: score = 1 if 'zeroth' in passage else 0; records the pairs it saw."""
    def __init__(self): self.pairs = []
    def predict(self, pairs):
        self.pairs += list(pairs)
        return [1.0 if "Zeroth" in p else 0.0 for _q, p in pairs]


class RecordingFirstStage:
    def __init__(self, inner): self.inner, self.calls = inner, []
    def search(self, query, *, filters=None, top_k=3):
        self.calls.append({"filters": filters, "top_k": top_k})
        return self.inner.search(query, filters=filters, top_k=top_k)


class RerankTests(unittest.TestCase):
    def test_reorders_by_cross_encoder_and_keeps_first_stage_rank(self):
        first = RecordingFirstStage(BM25Retriever(CHUNKS))
        rr = CrossEncoderReranker(first, scorer=KeywordScorer(), candidates=20)
        self.assertEqual(first.inner.search("gradients model", top_k=3)[0]["id"], "c1")  # BM25 order
        out = rr.search("gradients model", top_k=2)
        self.assertEqual(out[0]["id"], "c2")
        self.assertEqual([r["rank"] for r in out], [1, 2])
        self.assertEqual(out[0]["method"], "bm25_rerank")
        self.assertIn("first_stage_rank", out[0]["rerank"])
        self.assertEqual(first.calls[-1]["top_k"], 20)  # fetches candidates, not top_k

    def test_filter_passed_to_first_stage_and_ties_keep_first_stage_order(self):
        first = RecordingFirstStage(BM25Retriever(CHUNKS))
        scorer = KeywordScorer()
        rr = CrossEncoderReranker(first, scorer=scorer, candidates=20)
        out = rr.search("gradient", filters={"taxonomy": "generative_ai"}, top_k=3)
        self.assertEqual([r["id"] for r in out], ["c3"])
        self.assertEqual(first.calls[0]["filters"], {"taxonomy": "generative_ai"})
        self.assertEqual(scorer.pairs, [("gradient", CHUNKS[2]["text"])])

    def test_empty_first_stage_returns_empty_without_scoring(self):
        scorer = KeywordScorer()
        rr = CrossEncoderReranker(BM25Retriever(CHUNKS), scorer=scorer)
        self.assertEqual(rr.search("nonexistentterm", top_k=3), [])
        self.assertEqual(scorer.pairs, [])

    def test_method_registered_and_config_changes_only_method(self):
        self.assertIn("bm25_rerank", METHODS)
        a, b = CONFIGS["bm25_k3_b4000"], CONFIGS["bm25_rerank_k3_b4000"]
        self.assertEqual({k for k in a if a[k] != b.get(k)}, {"method"})


if __name__ == "__main__":
    unittest.main()
