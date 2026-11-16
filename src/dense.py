"""Dense retrieval on the Day 6 pgvector store (read-only).

Same embedding model (BAAI/bge-small-en-v1.5, 384 dims, query prefix) and same table /
strategy (index B) as Day 6. Exact cosine search with `<=>`, optional metadata filter
whose column names come from a whitelist (values are SQL parameters).
Returns chunks in the Day 7 format: id, text, source_id, source, page, metadata, score, rank.
"""
import time
from typing import Any, Callable

import psycopg

# Day 7 filter key -> Day 6 column.
FILTER_COLUMNS = {"taxonomy": "taxonomy", "section": "section", "subsection": "subsection",
                  "source_id": "document_id"}
TAXONOMY_VALUES = {"predictive_ai", "generative_ai", "general"}


def _vec(v: list[float]) -> str:
    return "[" + ",".join(f"{x:.7g}" for x in v) + "]"


def build_where(strategy: str, filters: dict[str, Any] | None) -> tuple[str, list[Any]]:
    where, params = ["strategy = %s"], [strategy]
    for key, value in (filters or {}).items():
        if key not in FILTER_COLUMNS:
            raise ValueError(f"filter '{key}' not allowed; allowed: {sorted(FILTER_COLUMNS)}")
        if key == "taxonomy" and value not in TAXONOMY_VALUES:
            raise ValueError(f"taxonomy must be one of {sorted(TAXONOMY_VALUES)}, got {value!r}")
        where.append(f"{FILTER_COLUMNS[key]} = %s")
        params.append(value)
    return " AND ".join(where), params


def row_to_chunk(rank: int, row: tuple) -> dict[str, Any]:
    chunk_id, document_id, source, page, taxonomy, section, subsection, text, metadata, score = row
    meta = dict(metadata or {})
    meta.update({"taxonomy": taxonomy, "section": section, "subsection": subsection})
    return {"id": chunk_id, "text": text, "source_id": document_id, "source": source, "page": int(page),
            "metadata": meta, "score": round(float(score), 6), "rank": rank, "method": "dense"}


class DenseRetriever:
    name = "dense"

    def __init__(self, embedder, database_url: str, strategy: str = "B",
                 connect: Callable[[], Any] | None = None) -> None:
        if not database_url and connect is None:
            raise ValueError("DATABASE_URL is empty: copy .env.example to .env")
        self.embedder = embedder
        self.strategy = strategy
        self._connect = connect or (lambda: psycopg.connect(database_url, connect_timeout=5))
        self.last_timing: dict[str, float] = {}

    def check(self) -> dict[str, Any]:
        """Fail fast if the index does not match the query embedder (model name, dims)."""
        with self._connect() as conn:
            col = conn.execute("""SELECT format_type(atttypid, atttypmod) FROM pg_attribute
                                  WHERE attrelid = 'chunks'::regclass AND attname = 'embedding'""").fetchone()[0]
            models = [r[0] for r in conn.execute(
                "SELECT DISTINCT embedding_model FROM chunks WHERE strategy = %s", (self.strategy,)).fetchall()]
            n = conn.execute("SELECT count(*) FROM chunks WHERE strategy = %s", (self.strategy,)).fetchone()[0]
            version = conn.execute("SELECT extversion FROM pg_extension WHERE extname = 'vector'").fetchone()
        if n == 0:
            raise RuntimeError(f"index {self.strategy} is empty in the Day 6 store")
        if col != f"vector({self.embedder.dimensions})":
            raise RuntimeError(f"index column is {col}, query embedder has {self.embedder.dimensions} dims")
        if models != [self.embedder.model_name]:
            raise RuntimeError(f"index built with {models}, query embedder is {self.embedder.model_name}")
        return {"strategy": self.strategy, "rows": n, "column_type": col, "embedding_model": models[0],
                "pgvector": version[0] if version else None}

    def ids_and_texts(self) -> dict[str, str]:
        with self._connect() as conn:
            rows = conn.execute("SELECT chunk_id, text FROM chunks WHERE strategy = %s",
                                (self.strategy,)).fetchall()
        return {r[0]: r[1] for r in rows}

    def search(self, query: str, *, filters: dict[str, Any] | None = None, top_k: int = 3) -> list[dict[str, Any]]:
        if not isinstance(query, str) or not query.strip():
            raise ValueError("query must be a non-empty string")
        if top_k < 1:
            raise ValueError("top_k must be >= 1")
        where, params = build_where(self.strategy, filters)
        t0 = time.perf_counter()
        qv = self.embedder.embed_query(query)
        if len(qv) != self.embedder.dimensions:
            raise ValueError(f"query vector has {len(qv)} dims, expected {self.embedder.dimensions}")
        t1 = time.perf_counter()
        q = _vec(qv)
        sql = f"""SELECT chunk_id, document_id, source, page, taxonomy, section, subsection, text, metadata,
                         1 - (embedding <=> %s::vector) AS score
                  FROM chunks WHERE {where}
                  ORDER BY embedding <=> %s::vector, chunk_id
                  LIMIT %s"""
        with self._connect() as conn:
            rows = conn.execute(sql, [q, *params, q, top_k]).fetchall()
        t2 = time.perf_counter()
        self.last_timing = {"embed_ms": round((t1 - t0) * 1000, 1), "db_ms": round((t2 - t1) * 1000, 1)}
        return [row_to_chunk(i + 1, r) for i, r in enumerate(rows)]