"""Runtime configuration (environment variables with sensible defaults)."""
from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = Path(os.getenv("TB_DATA_DIR", ROOT / "data"))
DATA_DIR.mkdir(parents=True, exist_ok=True)

DB_PATH = Path(os.getenv("TB_DB_PATH", DATA_DIR / "tenders.db"))

# Collector schedule, hours between runs (the task asked for 3).
COLLECT_INTERVAL_HOURS = float(os.getenv("TB_COLLECT_INTERVAL_HOURS", "3"))
# Set to "0" to disable the in-process scheduler (e.g. when cron runs `python -m server.collect`).
SCHEDULER_ENABLED = os.getenv("TB_SCHEDULER", "1") not in ("0", "false", "no")
# Run a collection right after the server starts.
COLLECT_ON_START = os.getenv("TB_COLLECT_ON_START", "1") not in ("0", "false", "no")

HTTP_TIMEOUT = float(os.getenv("TB_HTTP_TIMEOUT", "40"))
USER_AGENT = os.getenv(
    "TB_USER_AGENT",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0 Safari/537.36 tenders.best-collector/1.0",
)

# How many notices a collector fetches per run (newest first).
MAX_PER_SOURCE = int(os.getenv("TB_MAX_PER_SOURCE", "150"))

# Initial admin account, created once when the users table is empty.
ADMIN_USER = os.getenv("TB_ADMIN_USER", "admin")
ADMIN_PASSWORD = os.getenv("TB_ADMIN_PASSWORD", "ololoevadmin123!")

SESSION_DAYS = int(os.getenv("TB_SESSION_DAYS", "7"))
SECURE_COOKIES = os.getenv("TB_SECURE_COOKIES", "0") in ("1", "true", "yes")

# Optional API keys
GOSZAKUP_TOKEN = os.getenv("GOSZAKUP_TOKEN", "")          # goszakup.gov.kz open API bearer token
TED_API_KEY = os.getenv("TED_API_KEY", "")                # not required for search, kept for future use
