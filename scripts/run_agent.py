"""Run the agent with one configuration on one split and save traces + automatic metrics.

Automatic metrics (no human judgement): status counts, tool use, number of searches,
citation ids present in context, Context Evidence Rate (gold evidence inside the final
context, answerable only), abstention on unanswerable, false refusals, latency, tokens.
Answer correctness and whether a citation really supports the answer are graded by hand
later (reviews.json) and summarised with starter/agent_metrics.py.

Test split is refused until results/selected_config.json exists.

Usage:  python scripts/run_agent.py --config bm25_k3_b800 --ids q01,u01   # smoke test
        python scripts/run_agent.py --config bm25_k3_b800                 # whole dev split
"""
import argparse
import json
import statistics
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "starter"))

from baseline import hit  # noqa: E402
from src import config  # noqa: E402
from src.agent import run_question  # noqa: E402
from src.agent_configs import CONFIGS  # noqa: E402
from src.llm import LLMClient  # noqa: E402
from src.retrievers import load_chunks, make_retriever  # noqa: E402


def summarize(traces: list[dict], questions: dict[str, dict], chunk_by_id: dict[str, dict]) -> dict:
    ok = [t for t in traces if t["status"] != "error"]
    ans = [t for t in ok if questions[t["query_id"]]["answerable"]]
    una = [t for t in ok if not questions[t["query_id"]]["answerable"]]
    for t in ans:
        gold = questions[t["query_id"]]["gold"]
        t["context_evidence"] = any(hit(chunk_by_id[i], gold) for i in t["context_ids"])
    cites = [c for t in ok for c in t["citations"]]
    cites_in_ctx = sum(c in t["context_ids"] for t in ok for c in t["citations"])
    answered = [t for t in ok if t["status"] == "answered"]
    frac = lambda a, b: f"{a}/{b}"  # noqa: E731
    summary = {
        "runs": len(traces), "errors": len(traces) - len(ok),
        "status": dict(Counter(t["status"] for t in traces)),
        "tool_use": frac(sum(t["searches"] > 0 for t in ok), len(ok)),
        "searches_distribution": dict(sorted(Counter(t["searches"] for t in ok).items())),
        "llm_calls_distribution": dict(sorted(Counter(t["usage"]["llm_calls"] for t in ok).items())),
        "context_evidence_rate": frac(sum(t["context_evidence"] for t in ans), len(ans)),
        "answered_answerable": frac(sum(t["status"] == "answered" for t in ans), len(ans)),
        "false_refusal": frac(sum(t["status"] == "abstain" for t in ans), len(ans)),
        "abstention_unanswerable": frac(sum(t["status"] == "abstain" for t in una), len(una)),
        "answers_with_citation": frac(sum(bool(t["citations"]) for t in answered), len(answered)),
        "citation_ids_in_context": frac(cites_in_ctx, len(cites)),
        "invalid_citation_events": sum(e["event"] == "invalid_or_missing_citations" for t in ok for e in t["events"]),
        "median_latency_s": round(statistics.median(t["latency_s"] for t in traces), 2) if traces else None,
        "prompt_tokens": sum(t["usage"]["prompt_tokens"] for t in traces),
        "completion_tokens": sum(t["usage"]["completion_tokens"] for t in traces),
        "avg_context_chars": round(statistics.mean(t["context_chars"] for t in ok)) if ok else 0,
    }
    tin = sum(t["usage"]["prompt_tokens"] for t in traces)
    tout = sum(t["usage"]["completion_tokens"] for t in traces)
    summary["cost_usd"] = round(tin / 1e6 * config.LLM_PRICE_IN + tout / 1e6 * config.LLM_PRICE_OUT, 5)
    summary["cost_note"] = (f"tokens x list price: in ${config.LLM_PRICE_IN}/1M, out ${config.LLM_PRICE_OUT}/1M; "
                            "retrieval/embedding run locally ($0)")
    return summary


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--config", required=True, choices=sorted(CONFIGS))
    ap.add_argument("--split", default="dev", choices=("dev", "test"))
    ap.add_argument("--ids", default="", help="comma-separated question ids (smoke test)")
    args = ap.parse_args()
    if args.split == "test" and not (config.RESULTS_DIR / "selected_config.json").exists():
        sys.exit("Refusing test: freeze the config on dev first (results/selected_config.json).")

    cfg = CONFIGS[args.config]
    bench = json.loads((ROOT / "data" / "benchmark.json").read_text(encoding="utf-8"))
    questions = {q["id"]: q for q in bench}
    selected = [q for q in bench if q["split"] == args.split]
    if args.ids:
        wanted = [i.strip() for i in args.ids.split(",") if i.strip()]
        selected = [q for q in selected if q["id"] in wanted]
        if len(selected) != len(wanted):
            sys.exit(f"ids not found in {args.split}: {set(wanted) - {q['id'] for q in selected}}")

    temp = float(config.LLM_TEMPERATURE) if config.LLM_TEMPERATURE else None
    llm = LLMClient(config.LLM_BASE_URL, config.LLM_API_KEY, config.LLM_MODEL,
                    min_interval=config.LLM_MIN_INTERVAL, temperature=temp)
    retriever = make_retriever(cfg["method"])
    chunk_by_id = {c["id"]: c for c in load_chunks()}

    traces = []
    for i, q in enumerate(selected, 1):
        # Only the question text and its user-given filter go to the agent; gold stays here.
        t = run_question({k: q[k] for k in ("id", "split", "question") if k in q} | {"filter": q.get("filter")},
                         llm, retriever, cfg)
        t["config_name"] = args.config
        t["model"] = config.LLM_MODEL
        traces.append(t)
        print(f"[{i}/{len(selected)}] {q['id']:4s} {t['status']:8s} searches={t['searches']} "
              f"cites={t['citations']} {t['latency_s']}s")

    summary = summarize(traces, questions, chunk_by_id)
    tag = f"{args.config}_{args.split}" + ("_smoke" if args.ids else "")
    out = config.RESULTS_DIR / "agent" / tag
    out.mkdir(parents=True, exist_ok=True)
    meta = {"run_at": datetime.now(timezone.utc).isoformat(timespec="seconds"), "config_name": args.config,
            "config": cfg, "split": args.split, "llm": llm.info(), "ids": [q["id"] for q in selected],
            "summary": summary}
    (out / "summary.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (out / "traces.json").write_text(json.dumps(traces, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    print(f"-> {out}")


if __name__ == "__main__":
    main()