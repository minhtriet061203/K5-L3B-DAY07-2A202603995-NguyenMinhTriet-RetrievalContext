"""Step 1 check: Day 7 is really connected to the Day 6 embedder + pgvector index.

1. Index matches the query embedder (model name, 384 dims) and is not empty.
2. Chunk IDs and texts in pgvector == data/day6/chunks.json (same corpus version).
3. Dense retrieval on the DEV split only, top-3, reproduces Day 6 numbers
   (B: no filter; C: user-given filter). Test split is NOT touched here.

Output: results/step1/check.json, results/step1/dense_dev_traces.json
Usage:  python scripts/check_day6_store.py
"""
import hashlib
import json
import statistics
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "starter"))

from baseline import hit  # noqa: E402  (starter definition of a hit)
from src import config  # noqa: E402
from src.dense import DenseRetriever  # noqa: E402
from src.embeddings import MyEmbedder  # noqa: E402

DAY6_DEV = {"B": {"hit1": 11, "hit3": 12, "N": 15}, "C": {"hit1": 11, "hit3": 12, "N": 15}}


def h(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def main() -> None:
    chunks = json.loads((config.DATA_DIR / "chunks.json").read_text(encoding="utf-8"))
    questions = json.loads((config.DATA_DIR / "questions.json").read_text(encoding="utf-8"))
    dev = [q for q in questions if q["split"] == "dev" and q.get("answerable", True)]

    t0 = time.perf_counter()
    embedder = MyEmbedder(config.EMBEDDING_MODEL)
    load_s = time.perf_counter() - t0
    retriever = DenseRetriever(embedder, config.DATABASE_URL, strategy=config.DAY6_STRATEGY)

    store = retriever.check()
    db = retriever.ids_and_texts()
    local = {c["id"]: c["text"] for c in chunks}
    missing_in_db = sorted(set(local) - set(db))
    extra_in_db = sorted(set(db) - set(local))
    text_mismatch = sorted(i for i in set(local) & set(db) if h(local[i]) != h(db[i]))
    corpus_ok = not (missing_in_db or extra_in_db or text_mismatch)

    traces, summary = [], {}
    for variant, use_filter in (("dense", False), ("dense+filter", True)):
        n1 = n3 = 0
        latencies = []
        for q in dev:
            f = q.get("filter") if use_filter else None
            t = time.perf_counter()
            results = retriever.search(q["question"], filters=f, top_k=3)
            latencies.append((time.perf_counter() - t) * 1000)
            marks = [hit(r, q["gold"]) for r in results]
            n1 += bool(marks and marks[0])
            n3 += any(marks)
            traces.append({"variant": variant, "query_id": q["id"], "question": q["question"], "filter": f,
                           "results": [{"rank": r["rank"], "id": r["id"], "page": r["page"],
                                        "taxonomy": r["metadata"].get("taxonomy"), "score": r["score"],
                                        "hit": m} for r, m in zip(results, marks)],
                           "hit1": bool(marks and marks[0]), "hit3": any(marks),
                           "timing_ms": retriever.last_timing})
        summary[variant] = {"N": len(dev), "hit1": f"{n1}/{len(dev)}", "hit3": f"{n3}/{len(dev)}",
                            "median_latency_ms": round(statistics.median(latencies), 1),
                            "_n1": n1, "_n3": n3}

    reproduced = {
        "dense vs Day6 B": (summary["dense"]["_n1"], summary["dense"]["_n3"]) == (DAY6_DEV["B"]["hit1"], DAY6_DEV["B"]["hit3"]),
        "dense+filter vs Day6 C": (summary["dense+filter"]["_n1"], summary["dense+filter"]["_n3"]) == (DAY6_DEV["C"]["hit1"], DAY6_DEV["C"]["hit3"]),
    }
    for s in summary.values():
        s.pop("_n1"), s.pop("_n3")
    report = {"run_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
              "python": sys.version.split()[0], "embedding": embedder.info(),
              "model_load_seconds": round(load_s, 2), "store": store,
              "corpus_match": {"ok": corpus_ok, "local_chunks": len(local), "db_chunks": len(db),
                               "missing_in_db": missing_in_db, "extra_in_db": extra_in_db,
                               "text_mismatch": text_mismatch},
              "dev_dense_top3": summary, "day6_dev_reference": DAY6_DEV, "reproduced_day6": reproduced,
              "cost_usd": 0.0}
    out = config.RESULTS_DIR / "step1"
    out.mkdir(parents=True, exist_ok=True)
    (out / "check.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (out / "dense_dev_traces.json").write_text(json.dumps(traces, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"store: {store}")
    print(f"corpus match: {corpus_ok} (local {len(local)} / db {len(db)})")
    for k, v in summary.items():
        print(f"{k:13s} dev Hit@1 {v['hit1']}  Hit@3 {v['hit3']}  median {v['median_latency_ms']} ms")
    print(f"reproduced Day 6: {reproduced}")
    if not corpus_ok:
        sys.exit("FAIL: pgvector index differs from data/day6/chunks.json")


if __name__ == "__main__":
    main()