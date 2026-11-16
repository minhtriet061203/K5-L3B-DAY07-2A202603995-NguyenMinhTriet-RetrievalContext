"""Build a retriever by method name: dense | bm25 | hybrid_rrf | bm25_rerank (shared by eval and agent)."""
import json
from functools import lru_cache

from . import config
from .lexical import BM25Retriever

METHODS = ("dense", "bm25", "hybrid_rrf", "bm25_rerank")


@lru_cache(maxsize=1)
def load_chunks() -> tuple:
    return tuple(json.loads((config.DATA_DIR / "chunks.json").read_text(encoding="utf-8")))


@lru_cache(maxsize=1)
def _bm25():
    return BM25Retriever(list(load_chunks()))


@lru_cache(maxsize=1)
def _dense():
    from .dense import DenseRetriever
    from .embeddings import MyEmbedder
    r = DenseRetriever(MyEmbedder(config.EMBEDDING_MODEL), config.DATABASE_URL, strategy=config.DAY6_STRATEGY)
    r.check()
    return r


@lru_cache(maxsize=1)
def _bm25_rerank():
    from .rerank import CrossEncoderReranker
    return CrossEncoderReranker(_bm25(), candidates=20, name="bm25_rerank")


def make_retriever(method: str):
    if method == "bm25":
        return _bm25()
    if method == "dense":
        return _dense()
    if method == "hybrid_rrf":
        from .hybrid import HybridRRFRetriever
        return HybridRRFRetriever(_dense(), _bm25(), candidates=20, k=60)
    if method == "bm25_rerank":
        return _bm25_rerank()
    raise ValueError(f"unknown method {method!r}; choose from {METHODS}")