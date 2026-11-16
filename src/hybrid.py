"""Hybrid retrieval: Reciprocal Rank Fusion (RRF) of dense (pgvector) and BM25.

Raw cosine and BM25 scores are on different scales, so they are NOT added;
RRF uses ranks only: score(d) = sum_r 1 / (k + rank_r(d)). Each retriever returns
`candidates` chunks with the same filter; ties broken by chunk id.
"""
from typing import Any


class HybridRRFRetriever:
    name = "hybrid_rrf"

    def __init__(self, dense, lexical, candidates: int = 20, k: int = 60) -> None:
        self.dense, self.lexical, self.candidates, self.k = dense, lexical, candidates, k

    def search(self, query: str, *, filters: dict[str, Any] | None = None, top_k: int = 3) -> list[dict[str, Any]]:
        n = max(self.candidates, top_k)
        lists = {"dense": self.dense.search(query, filters=filters, top_k=n),
                 "bm25": self.lexical.search(query, filters=filters, top_k=n)}
        fused: dict[str, dict[str, Any]] = {}
        for name, results in lists.items():
            for r in results:
                entry = fused.setdefault(r["id"], {"chunk": r, "rrf": 0.0, "ranks": {}})
                entry["rrf"] += 1.0 / (self.k + r["rank"])
                entry["ranks"][name] = r["rank"]
        ordered = sorted(fused.values(), key=lambda e: (-e["rrf"], e["chunk"]["id"]))[:top_k]
        out = []
        for i, e in enumerate(ordered):
            c = {k: v for k, v in e["chunk"].items() if k not in ("score", "rank", "method")}
            out.append({**c, "score": round(e["rrf"], 6), "rank": i + 1, "method": self.name,
                        "fusion": {"dense_rank": e["ranks"].get("dense"), "bm25_rank": e["ranks"].get("bm25")}})
        return out