"""Step 3: compare retrieval methods on the same corpus, questions and labels.

Methods: dense (Day 6 pgvector), bm25, hybrid_rrf, bm25_rerank (BM25 top-20 -> cross-encoder). Same filter rule for all:
the user-given `filter` of a question (Day 6 strategy C), or none with --no-filter.
Metrics on ANSWERABLE questions only (unanswerable are excluded from denominators):
  Hit@1, Evidence Hit@3, MRR@10, Hit@10, Context Evidence Rate (top-3 packed into a
  char budget with starter pack_context). Unanswerable questions are still run and
  their top scores logged (useful later for abstention).

Test split is refused until results/selected_config.json exists (config frozen on dev).

Usage:  python scripts/eval_retrieval.py                       # dev, all methods
        python scripts/eval_retrieval.py --methods bm25        # no DB/model needed
        python scripts/eval_retrieval.py --budget 2000 --tag b2000
"""
import argparse
import json
import statistics
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "starter"))

from baseline import hit, pack_context  # noqa: E402
from src import config  # noqa: E402
from src.lexical import BM25Retriever  # noqa: E402

ALL_METHODS = ("dense", "bm25", "hybrid_rrf", "bm25_rerank")


def build(methods: list[str], chunks: list[dict]) -> dict:
    retrievers, info = {}, {}
    bm25 = BM25Retriever(chunks) if {"bm25", "hybrid_rrf", "bm25_rerank"} & set(methods) else None
    dense = None
    if {"dense", "hybrid_rrf"} & set(methods):
        from src.dense import DenseRetriever
        from src.embeddings import MyEmbedder
        emb = MyEmbedder(config.EMBEDDING_MODEL)
        dense = DenseRetriever(emb, config.DATABASE_URL, strategy=config.DAY6_STRATEGY)
        info["dense_store"] = dense.check()
        info["embedding"] = emb.info()
    for m in methods:
        if m == "dense":
            retrievers[m] = dense
        elif m == "bm25":
            retrievers[m] = bm25
        elif m == "hybrid_rrf":
            from src.hybrid import HybridRRFRetriever
            retrievers[m] = HybridRRFRetriever(dense, bm25, candidates=20, k=60)
        elif m == "bm25_rerank":
            from src.rerank import CrossEncoderReranker
            retrievers[m] = CrossEncoderReranker(bm25, candidates=20, name="bm25_rerank")
            info["rerank"] = retrievers[m].info()
    return retrievers, info


def evaluate(name, retriever, questions, use_filter, budget, depth=10):
    traces = []
    for q in questions:
        f = q.get("filter") if use_filter else None
        t0 = time.perf_counter()
        try:
            results = retriever.search(q["question"], filters=f, top_k=depth)
            error = None
        except Exception as e:  # recorded, never replaced by fake results
            results, error = [], f"{type(e).__name__}: {e}"
        ms = (time.perf_counter() - t0) * 1000
        top3 = results[:3]
        context, ctx_ids = pack_context(top3, budget=budget)
        row = {"method": name, "query_id": q["id"], "split": q["split"], "answerable": q["answerable"],
               "question": q["question"], "filter": f, "latency_ms": round(ms, 1), "error": error,
               "results": [{"rank": r["rank"], "id": r["id"], "page": r["page"],
                            "taxonomy": r["metadata"].get("taxonomy"), "score": r["score"],
                            **({"fusion": r["fusion"]} if "fusion" in r else {}),
                            **({"rerank": r["rerank"]} if "rerank" in r else {}),
                            **({"hit": hit(r, q["gold"])} if q["answerable"] else {})} for r in results],
               "context_ids": ctx_ids, "context_chars": len(context)}
        if q["answerable"]:
            marks = [hit(r, q["gold"]) for r in results]
            first = next((i + 1 for i, m in enumerate(marks) if m), None)
            row.update({"hit1": bool(marks[:1] and marks[0]), "hit3": any(marks[:3]),
                        "hit10": any(marks[:10]), "rr10": 1 / first if first else 0.0,
                        "context_hit": any(m and r["id"] in ctx_ids for r, m in zip(top3, marks[:3]))})
        traces.append(row)
    return traces


def summarize(name, traces, budget):
    ans = [t for t in traces if t["answerable"]]
    n = len(ans)
    frac = lambda k: f"{sum(t[k] for t in ans)}/{n}"  # noqa: E731
    return {"method": name, "N_answerable": n, "hit1": frac("hit1"), "hit3": frac("hit3"),
            "hit10": frac("hit10"), "mrr10": round(sum(t["rr10"] for t in ans) / n, 3),
            "context_evidence": frac("context_hit"), "budget_chars": budget,
            "avg_context_chars": round(statistics.mean(t["context_chars"] for t in ans)),
            "median_latency_ms": round(statistics.median(t["latency_ms"] for t in traces), 1),
            "errors": sum(t["error"] is not None for t in traces), "cost_usd": 0.0}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--split", default="dev", choices=("dev", "test"))
    ap.add_argument("--methods", default=",".join(ALL_METHODS))
    ap.add_argument("--no-filter", action="store_true", help="ignore user-given filters")
    ap.add_argument("--budget", type=int, default=800, help="context budget in characters (starter default 800)")
    ap.add_argument("--tag", default="", help="suffix for the output folder")
    args = ap.parse_args()
    methods = [m.strip() for m in args.methods.split(",") if m.strip()]
    unknown = set(methods) - set(ALL_METHODS)
    if unknown:
        sys.exit(f"unknown methods {unknown}; choose from {ALL_METHODS}")
    if args.split == "test" and not (config.RESULTS_DIR / "selected_config.json").exists():
        sys.exit("Refusing test: freeze the config on dev first (results/selected_config.json).")

    chunks = json.loads((config.DATA_DIR / "chunks.json").read_text(encoding="utf-8"))
    bench = json.loads((ROOT / "data" / "benchmark.json").read_text(encoding="utf-8"))
    questions = [q for q in bench if q["split"] == args.split]
    retrievers, info = build(methods, chunks)

    all_traces, summary = [], []
    for m in methods:
        tr = evaluate(m, retrievers[m], questions, not args.no_filter, args.budget)
        all_traces += tr
        summary.append(summarize(m, tr, args.budget))

    folder = f"step3_{args.split}" + (f"_{args.tag}" if args.tag else "")
    out = config.RESULTS_DIR / folder
    out.mkdir(parents=True, exist_ok=True)
    meta = {"run_at": datetime.now(timezone.utc).isoformat(timespec="seconds"), "split": args.split,
            "filter_rule": "none" if args.no_filter else "user-given question filter (Day 6 strategy C)",
            "top_k_reported": 3, "depth": 10, "hybrid": {"fusion": "RRF", "k": 60, "candidates_per_retriever": 20},
            "bm25": {"k1": 1.5, "b": 0.75, "tokenizer": "NFC, de-hyphenate line breaks, lower, \\w+, stopwords"},
            **info, "summary": summary}
    (out / "summary.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (out / "traces.json").write_text(json.dumps(all_traces, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"split={args.split} filter={meta['filter_rule']} budget={args.budget} chars -> {out}")
    print(f"{'method':12s} {'Hit@1':>7s} {'Hit@3':>7s} {'Hit@10':>7s} {'MRR@10':>7s} {'CtxEvid':>8s} {'ms':>7s} err")
    for s in summary:
        print(f"{s['method']:12s} {s['hit1']:>7s} {s['hit3']:>7s} {s['hit10']:>7s} {s['mrr10']:>7.3f} "
              f"{s['context_evidence']:>8s} {s['median_latency_ms']:>7.1f} {s['errors']}")


if __name__ == "__main__":
    main()