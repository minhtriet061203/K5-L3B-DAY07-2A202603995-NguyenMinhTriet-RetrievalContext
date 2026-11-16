"""Step 2: build the Day 7 benchmark = Day 6 questions + Day 7 additions.

Checks (fails on any error):
- every answerable gold evidence is found inside a chunk of the gold source/page
  (rewritten to the verbatim chunk span, like import_day6.py);
- every unanswerable question lists terms that appear in NO indexed chunk;
- split sizes meet BENCHMARK.md (dev >= 15 + 2, test >= 5 + 2);
- dev and test answerable questions share no gold page.

Output: data/benchmark.json, data/cases.json (for starter/agent_metrics.py),
        data/benchmark_report.json
Usage:  python scripts/build_benchmark.py
"""
import json
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "starter"))

from baseline import validate  # noqa: E402
from src.evidence import find_verbatim, normalize  # noqa: E402

MIN = {"dev": (15, 2), "test": (5, 2)}  # (answerable, unanswerable)


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def resolve_gold(q: dict, chunks: list[dict]) -> list[dict]:
    gold = []
    for g in q["gold"]:
        spans = [find_verbatim(g["evidence"], c["text"]) for c in chunks
                 if c["source_id"] == g["source_id"] and c["page"] == g["page"]]
        spans = [s for s in spans if s]
        if not spans:
            raise ValueError(f"{q['id']}: evidence not inside one chunk of p{g['page']}")
        gold += [{**g, "evidence": s} for s in spans]
    return gold


def check_absence(q: dict, chunks: list[dict]) -> dict:
    corpus = [(c["id"], c["page"], normalize(c["text"])) for c in chunks]
    found = {}
    for term in q["absence_check"]["terms_absent"]:
        t = normalize(term)
        pat = re.compile(r"\b" + re.escape(t) + r"\b")
        hits = [f"{cid} (p{page})" for cid, page, text in corpus if pat.search(text)]
        if hits:
            found[term] = hits
    if found:
        raise ValueError(f"{q['id']}: 'absent' terms found in corpus: {found}")
    return {"id": q["id"], "terms_absent": q["absence_check"]["terms_absent"], "chunks_scanned": len(corpus)}


def main() -> None:
    chunks = load(ROOT / "data" / "day6" / "chunks.json")
    base = load(ROOT / "data" / "day6" / "questions.json")
    additions = load(ROOT / "data" / "benchmark_additions.json")
    base_ids = {q["id"] for q in base}
    questions = base + additions
    ids = [q["id"] for q in questions]
    if len(ids) != len(set(ids)):
        raise ValueError(f"duplicate ids: {[i for i, n in Counter(ids).items() if n > 1]}")

    absence_log = []
    for q in questions:
        if q.get("answerable", True):
            q["answerable"] = True
            q.setdefault("expected_behavior", "search_and_answer")
            q["gold"] = resolve_gold(q, chunks)
            q["origin"] = "day6" if q["id"] in base_ids else "day7"
        else:
            if q.get("expected_behavior") != "search_and_abstain" or not q.get("absence_reason"):
                raise ValueError(f"{q['id']}: unanswerable needs expected_behavior + absence_reason")
            absence_log.append(check_absence(q, chunks))
            q["origin"] = "day7"
    validate(chunks, [q for q in questions if q["answerable"]])

    counts = {s: {"answerable": sum(q["split"] == s and q["answerable"] for q in questions),
                  "unanswerable": sum(q["split"] == s and not q["answerable"] for q in questions)}
              for s in ("dev", "test")}
    for s, (na, nu) in MIN.items():
        if counts[s]["answerable"] < na or counts[s]["unanswerable"] < nu:
            raise ValueError(f"{s} split too small: {counts[s]}, need {na}+{nu}")
    pages = {s: {g["page"] for q in questions if q["split"] == s and q["answerable"] for g in q["gold"]}
             for s in ("dev", "test")}
    shared = sorted(pages["dev"] & pages["test"])
    if shared:
        raise ValueError(f"dev and test share gold pages {shared}")

    out = ROOT / "data"
    (out / "benchmark.json").write_text(json.dumps(questions, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    cases = [{"id": q["id"], "split": q["split"], "answerable": q["answerable"],
              "expected_behavior": q["expected_behavior"]} for q in questions]
    (out / "cases.json").write_text(json.dumps(cases, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    report = {"total": len(questions), "counts": counts,
              "types": dict(Counter(f"{q['split']}:{q.get('type')}" for q in questions)),
              "with_filter": [q["id"] for q in questions if q.get("filter")],
              "dev_gold_pages": sorted(pages["dev"]), "test_gold_pages": sorted(pages["test"]),
              "dev_test_shared_gold_pages": shared, "absence_checks": absence_log,
              "absence_scope": "full-text scan of all indexed chunks (pages 14-73); references/glossary "
                               "(pages 74-127) are not indexed and not part of the corpus."}
    (out / "benchmark_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"total={len(questions)} dev={counts['dev']} test={counts['test']} shared_gold_pages={shared}")


if __name__ == "__main__":
    main()