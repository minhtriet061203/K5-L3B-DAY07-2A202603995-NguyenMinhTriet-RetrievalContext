"""Retrieval + rerank: a first-stage retriever returns `candidates` chunks (same filter),
then a cross-encoder scores each (query, passage) pair and the top_k by that score are kept.

Default model: cross-encoder/ms-marco-MiniLM-L-6-v2 (sentence-transformers CrossEncoder, CPU).
The scorer is injectable (any object with .predict(list[tuple[str, str]]) -> list[float])
so the ranking logic can be unit-tested without downloading a model.
Ties are broken by first-stage rank. The first-stage rank/score are kept in `rerank`.
"""
from typing import Any

DEFAULT_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"


class CrossEncoderReranker:
    def __init__(self, first_stage, scorer=None, model_name: str = DEFAULT_MODEL,
                 candidates: int = 20, name: str = "bm25_rerank") -> None:
        self.first_stage, self.model_name, self.candidates, self.name = first_stage, model_name, candidates, name
        self._scorer = scorer

    @property
    def scorer(self):
        if self._scorer is None:
            from sentence_transformers import CrossEncoder
            self._scorer = CrossEncoder(self.model_name, device="cpu")
        return self._scorer

    def info(self) -> dict[str, Any]:
        return {"method": self.name, "reranker": self.model_name, "candidates": self.candidates}

    def search(self, query: str, *, filters: dict[str, Any] | None = None, top_k: int = 3) -> list[dict[str, Any]]:
        cands = self.first_stage.search(query, filters=filters, top_k=max(self.candidates, top_k))
        if not cands:
            return []
        scores = [float(s) for s in self.scorer.predict([(query, c["text"]) for c in cands])]
        order = sorted(range(len(cands)), key=lambda i: (-scores[i], cands[i]["rank"]))[:top_k]
        out = []
        for new_rank, i in enumerate(order, 1):
            c = {k: v for k, v in cands[i].items() if k not in ("score", "rank", "method")}
            out.append({**c, "score": round(scores[i], 4), "rank": new_rank, "method": self.name,
                        "rerank": {"first_stage_rank": cands[i]["rank"],
                                   "first_stage_score": cands[i].get("score")}})
        return out
