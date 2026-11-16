"""Offline checks for the agent loop with a scripted fake LLM (does NOT measure model quality)."""
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.agent import ContextWindow, run_question  # noqa: E402

C1 = {"id": "B:d:p001:c00", "text": "Backdoor attacks need training and testing data control.",
      "source_id": "d", "source": "d.pdf", "page": 1, "metadata": {"section": "2"}}
C2 = {"id": "B:d:p002:c00", "text": "x" * 500, "source_id": "d", "source": "d.pdf", "page": 2,
      "metadata": {"section": "2"}}
CFG = {"method": "fake", "top_k": 2, "budget": 400, "max_searches": 2, "filter_mode": "given"}
Q = {"id": "q1", "split": "dev", "question": "Which attack needs both?", "filter": {"taxonomy": "predictive_ai"}}


def call(name, **args):
    return {"id": f"call_{name}", "type": "function", "function": {"name": name, "arguments": json.dumps(args)}}


class FakeLLM:
    def __init__(self, turns): self.turns, self.seen = iter(turns), []
    def chat(self, messages, tools):
        self.seen.append([m["role"] for m in messages])
        return next(self.turns), {"prompt_tokens": 10, "completion_tokens": 2}


class FakeRetriever:
    def __init__(self, rows): self.rows, self.calls = rows, []
    def search(self, query, *, filters=None, top_k=3):
        self.calls.append((query, filters, top_k))
        return [{**r, "rank": i + 1, "score": 1.0} for i, r in enumerate(self.rows[:top_k])]


def turn(*calls_, content=None):
    m = {"role": "assistant", "tool_calls": list(calls_)} if calls_ else {"role": "assistant"}
    if content is not None:
        m["content"] = content
    return m


class AgentTests(unittest.TestCase):
    def test_search_then_cited_answer(self):
        llm = FakeLLM([turn(call("search", query="backdoor")),
                       turn(call("answer", answer=f"Backdoor attacks [{C1['id']}].", citations=[C1["id"]]))])
        r = FakeRetriever([C1, C2])
        out = run_question(Q, llm, r, CFG)
        self.assertEqual(out["status"], "answered")
        self.assertEqual(out["citations"], [C1["id"]])
        self.assertEqual(r.calls, [("backdoor", {"taxonomy": "predictive_ai"}, 2)])
        self.assertEqual(out["context_ids"], [C1["id"]])           # C2 did not fit the 400-char budget
        self.assertEqual(out["events"][0]["dropped_budget"], [C2["id"]])
        self.assertEqual(llm.seen[1][-1], "tool")                  # tool result sent back to the model

    def test_citation_not_in_context_becomes_abstain(self):
        llm = FakeLLM([turn(call("search", query="q")),
                       turn(call("answer", answer="Yes [B:d:p009:c00].", citations=["B:d:p009:c00"]))])
        out = run_question(Q, llm, FakeRetriever([C1]), CFG)
        self.assertEqual(out["status"], "abstain")
        self.assertEqual(out["model_reason"], "invalid_citation")
        self.assertIn("raw_answer", out)

    def test_listed_citation_is_appended_and_grouped_brackets_parsed(self):
        llm = FakeLLM([turn(call("search", query="q")),
                       turn(call("answer", answer="Backdoor attacks.", citations=[C1["id"]]))])
        out = run_question(Q, llm, FakeRetriever([C1]), {**CFG, "budget": 10_000})
        self.assertEqual(out["status"], "answered")
        self.assertTrue(out["answer"].endswith(f"[{C1['id']}]"))
        self.assertIn("citations_appended", [e["event"] for e in out["events"]])
        from src.agent import extract_ids
        self.assertEqual(extract_ids(f"x [{C1['id']}, {C2['id']}] y"), [C1["id"], C2["id"]])

    def test_abstain_and_search_limit(self):
        llm = FakeLLM([turn(call("search", query="a")), turn(call("search", query="b")),
                       turn(call("search", query="c")), turn(call("abstain", reason="not in report"))])
        out = run_question(Q, llm, FakeRetriever([C1]), CFG)
        self.assertEqual(out["status"], "abstain")
        self.assertEqual(out["searches"], 2)
        self.assertEqual([e["event"] for e in out["events"]],
                         ["search", "search", "search_limit", "abstain"])

    def test_filter_none_mode_and_text_answer(self):
        llm = FakeLLM([turn(call("search", query="q")), turn(content=f"Answer [{C1['id']}]")])
        r = FakeRetriever([C1])
        out = run_question(Q, llm, r, {**CFG, "filter_mode": "none"})
        self.assertIsNone(r.calls[0][1])
        self.assertEqual(out["status"], "answered")

    def test_provider_error_is_recorded(self):
        class Boom:
            def chat(self, m, t): raise RuntimeError("429 quota")
        out = run_question(Q, Boom(), FakeRetriever([C1]), CFG)
        self.assertEqual(out["status"], "error")
        self.assertIn("429", out["error"])

    def test_context_window_dedup(self):
        w = ContextWindow(10_000)
        w.add([C1])
        shown, dup, dropped = w.add([C1, C2])
        self.assertEqual(([c["id"] for c in shown], dup, dropped), ([C2["id"]], [C1["id"]], []))


if __name__ == "__main__":
    unittest.main()