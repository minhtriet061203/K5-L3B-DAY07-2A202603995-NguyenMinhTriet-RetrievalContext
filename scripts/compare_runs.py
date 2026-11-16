"""Collect retrieval (step3) and agent summaries of one split into one Markdown table.

Usage:  python scripts/compare_runs.py --split dev
Output: printed table + results/compare_<split>.md (paste into the report)
"""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src import config  # noqa: E402
from src.agent_configs import CONFIGS  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", default="dev", choices=("dev", "test"))
    args = ap.parse_args()
    lines = []

    ret = config.RESULTS_DIR / f"step3_{args.split}" / "summary.json"
    if ret.exists():
        s = json.loads(ret.read_text(encoding="utf-8"))
        lines += [f"### Retrieval only ({args.split}, top-3, filter: {s['filter_rule']})", "",
                  "| Method | Hit@1 | Evidence Hit@3 | Hit@10 | MRR@10 | Context Evidence (budget) | Median ms |",
                  "|---|---|---|---|---|---|---|"]
        for m in s["summary"]:
            lines.append(f"| {m['method']} | {m['hit1']} | {m['hit3']} | {m['hit10']} | {m['mrr10']} | "
                         f"{m['context_evidence']} ({m['budget_chars']} chars) | {m['median_latency_ms']} |")
        lines.append("")

    lines += [f"### Agent ({args.split})", "",
              "| Config | Method, top-k, budget, max searches | Context Evidence | Answered (answerable) | "
              "False refusal | Abstention (unanswerable) | Citation ids in context | Searches dist. | "
              "Median s | Tokens in/out | Cost USD | Errors |",
              "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    found = 0
    for name in CONFIGS:
        f = config.RESULTS_DIR / "agent" / f"{name}_{args.split}" / "summary.json"
        if not f.exists():
            continue
        found += 1
        m = json.loads(f.read_text(encoding="utf-8"))
        c, s = m["config"], m["summary"]
        lines.append(
            f"| {name} | {c['method']}, k={c['top_k']}, {c['budget']} chars, {c['max_searches']} | "
            f"{s['context_evidence_rate']} | {s['answered_answerable']} | {s['false_refusal']} | "
            f"{s['abstention_unanswerable']} | {s['citation_ids_in_context']} | {s['searches_distribution']} | "
            f"{s['median_latency_s']} | {s['prompt_tokens']}/{s['completion_tokens']} | {s['cost_usd']} | "
            f"{s['errors']} |")
    if not found:
        lines.append("| (no agent runs found) |||||||||||| ")
    text = "\n".join(lines) + "\n"
    out = config.RESULTS_DIR / f"compare_{args.split}.md"
    out.write_text(text, encoding="utf-8")
    print(text)
    print(f"-> {out}")


if __name__ == "__main__":
    main()