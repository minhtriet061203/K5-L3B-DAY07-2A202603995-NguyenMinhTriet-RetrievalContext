"""Offline checks for Step 1 (no DB, no model): evidence mapping, import, dense SQL/filters."""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "starter"))

from src.evidence import find_verbatim  # noqa: E402

try:
    import psycopg  # noqa: F401
    HAS_PSYCOPG = True
except ImportError:
    HAS_PSYCOPG = False


class EvidenceTests(unittest.TestCase):
    def test_line_breaks_and_case_map_back_to_exact_span(self):
        text = "Intro.\nThe field of ADVERSARIAL MACHINE\nLEARNING (AML) studies attacks.  Next."
        span = find_verbatim("the field of adversarial machine learning (AML) studies attacks.", text)
        self.assertEqual(span, "The field of ADVERSARIAL MACHINE\nLEARNING (AML) studies attacks.")
        self.assertIn(span, text)

    def test_absent_quote(self):
        self.assertIsNone(find_verbatim("not here", "some other text"))


class ImportTests(unittest.TestCase):
    def test_convert_question_uses_gold_page_only(self):
        from import_day6 import convert_chunk, convert_question
        raw = [{"chunk_id": "B:d:p001:c00", "document_id": "d", "source": "d.pdf", "page": 1,
                "text": "Answer\nhere.", "taxonomy": "general"},
               {"chunk_id": "B:d:p002:c00", "document_id": "d", "source": "d.pdf", "page": 2,
                "text": "Answer here.", "taxonomy": "general"}]
        chunks = [convert_chunk(c) for c in raw]
        self.assertEqual(chunks[0]["metadata"]["taxonomy"], "general")
        q = {"id": "q", "split": "dev", "question": "?", "expected_answer": "a", "gold_source_id": "d",
             "gold_page": 1, "evidence_quote": "answer here.", "filter": None}
        out, log = convert_question(q, chunks)
        self.assertEqual(out["gold"], [{"source_id": "d", "page": 1, "evidence": "Answer\nhere."}])
        self.assertEqual(log["gold_chunks"], ["B:d:p001:c00"])
        self.assertNotIn("filter", out)


@unittest.skipUnless(HAS_PSYCOPG, "psycopg not installed")
class DenseTests(unittest.TestCase):
    def setUp(self):
        from src.dense import DenseRetriever

        class Emb:
            model_name, dimensions = "m", 3
            def embed_query(self, q): return [0.1, 0.2, 0.3]

        class Conn:
            def __init__(s): s.calls = []
            def __enter__(s): return s
            def __exit__(s, *a): return False
            def execute(s, sql, params=None):
                s.calls.append((sql, params))
                row = ("B:d:p001:c00", "d", "d.pdf", 1, "general", "1. Intro", "1. Intro", "txt",
                       {"chunk_index": 0}, 0.87654321)
                return type("R", (), {"fetchall": lambda _: [row]})()
        self.conn = Conn()
        self.r = DenseRetriever(Emb(), "", connect=lambda: self.conn)

    def test_search_maps_to_day7_format_and_uses_params(self):
        out = self.r.search("q", filters={"taxonomy": "general"}, top_k=2)
        self.assertEqual(out[0]["id"], "B:d:p001:c00")
        self.assertEqual(out[0]["source_id"], "d")
        self.assertEqual(out[0]["metadata"]["taxonomy"], "general")
        self.assertEqual(out[0]["rank"], 1)
        sql, params = self.conn.calls[0]
        self.assertIn("taxonomy = %s", sql)
        self.assertEqual(params[1:3], ["B", "general"])
        self.assertEqual(params[-1], 2)

    def test_filter_whitelist_and_values(self):
        with self.assertRaises(ValueError):
            self.r.search("q", filters={"page; DROP TABLE chunks": 1})
        with self.assertRaises(ValueError):
            self.r.search("q", filters={"taxonomy": "robotics"})


if __name__ == "__main__":
    unittest.main()