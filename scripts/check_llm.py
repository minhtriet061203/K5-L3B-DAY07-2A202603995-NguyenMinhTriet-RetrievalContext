"""Step 4 check: the LLM in .env is reachable and supports tool calling.

1. Lists models visible to the key (names containing 'gemini' or all, if none match).
2. Sends one request with the `search` tool and checks the model calls it.
Never prints the API key.  Usage: python scripts/check_llm.py
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src import config  # noqa: E402
from src.agent import TOOLS  # noqa: E402
from src.llm import LLMClient  # noqa: E402


def main() -> None:
    temp = float(config.LLM_TEMPERATURE) if config.LLM_TEMPERATURE else None
    llm = LLMClient(config.LLM_BASE_URL, config.LLM_API_KEY, config.LLM_MODEL, min_interval=0, temperature=temp)
    print(f"endpoint: {config.LLM_BASE_URL}\nmodel in .env: {config.LLM_MODEL}")
    try:
        names = sorted(m.id for m in llm.client.models.list())
        flash = [n for n in names if "flash" in n] or names
        print(f"models available to this key ({len(names)}), flash models:")
        for n in flash:
            print("  ", n)
    except Exception as e:
        print(f"could not list models: {type(e).__name__}: {e}")
    msg, usage = llm.chat([{"role": "system", "content": "Use the search tool to find information."},
                           {"role": "user", "content": "What is a backdoor poisoning attack?"}], TOOLS)
    calls = msg.get("tool_calls") or []
    print(f"tool calls: {[(c['function']['name'], c['function']['arguments']) for c in calls]}")
    print(f"usage: {usage}")
    if not calls or calls[0]["function"]["name"] != "search":
        sys.exit("FAIL: model did not call the search tool")
    print("LLM OK: tool calling works")


if __name__ == "__main__":
    main()