"""Import Day 6 chunks (index B) and benchmark into the Day 7 JSON schema.

Input  (Day 6 repo, read-only):  <day6>/starter/results/chunks_B.jsonl
                                 <day6>/starter/benchmark/questions.jsonl
Output (Day 7 repo):             data/day6/chunks.json, data/day6/questions.json,
                                 data/day6/import_report.json

Only field renames + verbatim evidence lookup. No gold is invented: every evidence
string is located inside exactly the chunk of the gold source/page, else the script fails.

Usage:  python scripts/import_day6.py --day6 E:\\VinAI\\K5-L3B-DAY06-...\\starter
"""
import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "starter"))

from src.evidence import find_verbatim  # noqa: E402
from baseline import validate  # noqa: E402  (starter validator, exact-substring gold check)

CORE = ("chunk_id", "document_id", "source", "page", "text")


def read_jsonl(path: Path) -> list[dict]:
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not rows:
        raise ValueError(f"{path} is empty")
    return rows


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def convert_chunk(c: dict) -> dict:
    missing = [k for k in CORE if c.get(k) in (None, "")]
    if missing:
        raise ValueError(f"chunk {c.get('chunk_id')} missing {missing}")
    return {"id": c["chunk_id"], "text": c["text"], "source_id": c["document_id"],
            "source": c["source"], "page": int(c["page"]),
            "metadata": {k: v for k, v in c.items() if k not in CORE}}


def convert_question(q: dict, chunks: list[dict]) -> tuple[dict, dict]:
    page, source_id = int(q["gold_page"]), q["gold_source_id"]
    matches = []
    for c in chunks:
        if c["source_id"] == source_id and c["page"] == page:
            span = find_verbatim(q["evidence_quote"], c["text"])
            if span is not None:
                matches.append((c["id"], span))
    if not matches:
        raise ValueError(f"{q['id']}: evidence not found inside any chunk of {source_id} p{page}")
    gold = [{"source_id": source_id, "page": page, "evidence": span} for _, span in matches]
    out = {"id": q["id"], "split": q["split"], "type": q.get("type"), "question": q["question"],
           "expected_answer": q["expected_answer"], "answerable": True,
           "expected_behavior": "search_and_answer", "gold": gold}
    if q.get("filter"):
        out["filter"] = q["filter"]  # given with the question in Day 6, not derived from gold
    log = {"id": q["id"], "gold_chunks": [cid for cid, _ in matches],
           "evidence_rewritten": any(span != q["evidence_quote"] for _, span in matches)}
    return out, log


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--day6", required=True, type=Path, help="Day 6 starter/ directory")
    ap.add_argument("--strategy", default="B", help="Day 6 chunk strategy to import (default B)")
    ap.add_argument("--out", default=ROOT / "data" / "day6", type=Path)
    args = ap.parse_args()

    chunk_file = args.day6 / "results" / f"chunks_{args.strategy}.jsonl"
    question_file = args.day6 / "benchmark" / "questions.jsonl"
    chunks = [convert_chunk(c) for c in read_jsonl(chunk_file)]
    if len({c["id"] for c in chunks}) != len(chunks):
        raise ValueError("duplicate chunk IDs")
    questions, logs = zip(*(convert_question(q, chunks) for q in read_jsonl(question_file)))
    questions = list(questions)
    validate(chunks, questions)  # starter check: each gold evidence is a literal substring of a gold chunk

    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "chunks.json").write_text(json.dumps(chunks, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    (args.out / "questions.json").write_text(json.dumps(questions, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    report = {
        "imported_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "day6_strategy": args.strategy,
        "inputs": {"chunks": {"file": chunk_file.name, "sha256": sha256(chunk_file)},
                   "questions": {"file": question_file.name, "sha256": sha256(question_file)}},
        "chunks": len(chunks), "pages": len({c["page"] for c in chunks}),
        "questions": {s: sum(q["split"] == s for q in questions) for s in ("dev", "test")},
        "with_filter": [q["id"] for q in questions if q.get("filter")],
        "evidence_rewritten_to_verbatim": sum(l["evidence_rewritten"] for l in logs),
        "per_question": list(logs),
        "note": "evidence = exact span of the gold chunk matching the Day 6 quote after "
                "NFC + whitespace collapse + lower-case (same rule as Day 6 evaluation).",
    }
    (args.out / "import_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"chunks={len(chunks)} pages={report['pages']} questions={report['questions']} "
          f"evidence_rewritten={report['evidence_rewritten_to_verbatim']}/{len(questions)} -> {args.out}")


if __name__ == "__main__":
    main()