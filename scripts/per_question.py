"""Per-question view of several agent runs on one split (for error analysis).

For every question and config: status, number of searches, whether the final context
contains gold evidence, pages in context, and the model's abstain reason (short).
Usage:  python scripts/per_question.py --split dev --configs dense_k3_b800,bm25_k3_b800,hybrid_k3_b800
Output: printed table + results/per_question_<split>.md (or --out NAME)
"""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "starter"))

from baseline import hit  # noqa: E402
from src import config  # noqa: E402
from src.retrievers import load_chunks  # noqa: E402


def page_of(cid: str) -> int:
    return int(cid.split(":p")[1][:3])


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", default="dev", choices=("dev", "test"))
    ap.add_argument("--configs", default="dense_k3_b800,bm25_k3_b800,hybrid_k3_b800")
    ap.add_argument("--out", default="", help="output file name in results/ (default per_question_<split>.md)")
    args = ap.parse_args()
    configs = [c.strip() for c in args.configs.split(",") if c.strip()]
    bench = {q["id"]: q for q in json.loads((ROOT / "data" / "benchmark.json").read_text(encoding="utf-8"))}
    chunks = {c["id"]: c for c in load_chunks()}
    runs = {}
    for c in configs:
        f = config.RESULTS_DIR / "agent" / f"{c}_{args.split}" / "traces.json"
        runs[c] = {t["query_id"]: t for t in json.loads(f.read_text(encoding="utf-8"))}

    head = "| id | gold | " + " | ".join(configs) + " |"
    lines = [head, "|" + "---|" * (len(configs) + 2)]
    reasons = []
    for qid in runs[configs[0]]:
        q = bench[qid]
        gold = f"p{q['gold'][0]['page']}" if q["answerable"] else "none"
        cells = []
        for c in configs:
            t = runs[c][qid]
            ctx = "-" if not q["answerable"] else ("Y" if any(hit(chunks[i], q["gold"]) for i in t["context_ids"]) else "N")
            pages = ",".join(str(page_of(i)) for i in t["context_ids"]) or "-"
            cells.append(f"{t['status'][:6]} s{t['searches']} ctx:{ctx} p[{pages}]")
            if t["status"] != "answered" or not q["answerable"]:
                why = t.get("model_reason") or t.get("error") or ""
                reasons.append(f"- {qid} / {c}: {t['status']} - {why[:140]}")
        lines.append(f"| {qid} | {gold} | " + " | ".join(cells) + " |")
    text = "\n".join(lines) + "\n\nAbstain / error reasons:\n" + "\n".join(reasons) + "\n"
    out = config.RESULTS_DIR / (args.out or f"per_question_{args.split}.md")
    out.write_text(text, encoding="utf-8")
    print(text)
    print(f"-> {out}")


if __name__ == "__main__":
    main()