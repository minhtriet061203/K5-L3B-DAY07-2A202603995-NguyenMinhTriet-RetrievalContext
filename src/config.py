"""Settings from .env (repo root). The LLM key lives only in .env (never committed)."""
import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")

DATABASE_URL = os.getenv("DATABASE_URL", "")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "BAAI/bge-small-en-v1.5")
DAY6_STRATEGY = os.getenv("DAY6_STRATEGY", "B")
DATA_DIR = ROOT / "data" / "day6"
RESULTS_DIR = ROOT / "results"

# Agent LLM (OpenAI-compatible endpoint: Gemini or Ollama).
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "")
LLM_API_KEY = os.getenv("LLM_API_KEY", "")
LLM_MODEL = os.getenv("LLM_MODEL", "")
LLM_MIN_INTERVAL = float(os.getenv("LLM_MIN_INTERVAL", "6"))  # seconds between calls (free-tier rate limit)
LLM_TEMPERATURE = os.getenv("LLM_TEMPERATURE", "")              # empty = provider default
# USD per 1M tokens, used to report cost (0 for free tiers / local models).
LLM_PRICE_IN = float(os.getenv("LLM_PRICE_IN_PER_M", "0"))
LLM_PRICE_OUT = float(os.getenv("LLM_PRICE_OUT_PER_M", "0"))