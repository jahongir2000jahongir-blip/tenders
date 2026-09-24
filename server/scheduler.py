"""Background scheduler: runs the full collection every N hours (default 3).

Two ways to run it:
  * in-process, started by the web app (TB_SCHEDULER=1, default);
  * externally via cron / systemd timer calling `python -m server.collect` (set TB_SCHEDULER=0).
The two never overlap thanks to a process-wide lock and a DB-level "collect_lock" record.
"""
from __future__ import annotations

import logging
import threading
import time
from datetime import datetime, timedelta, timezone

from . import config, db, pipeline

log = logging.getLogger("scheduler")
_run_lock = threading.Lock()
_stop = threading.Event()
_thread: threading.Thread | None = None


def is_running() -> bool:
    return _run_lock.locked()


def collect_now(only: list[str] | None = None) -> bool:
    """Run a collection unless one is already in progress. Returns False when skipped."""
    if not _run_lock.acquire(blocking=False):
        log.info("collection already running, skipped")
        return False
    try:
        db.set_setting("collect_running_since", db.utcnow())
        pipeline.run_all(only)
    finally:
        db.set_setting("collect_running_since", None)
        _run_lock.release()
    return True


def next_run_at() -> str | None:
    last = db.get_setting("last_collect_at")
    if not last:
        return None
    dt = datetime.fromisoformat(last) + timedelta(hours=config.COLLECT_INTERVAL_HOURS)
    return dt.astimezone(timezone.utc).replace(microsecond=0).isoformat()


def _loop() -> None:
    interval = config.COLLECT_INTERVAL_HOURS * 3600
    if config.COLLECT_ON_START:
        last = db.get_setting("last_collect_at")
        stale = True
        if last:
            age = (datetime.now(timezone.utc) - datetime.fromisoformat(last)).total_seconds()
            stale = age > interval
        if stale:
            collect_now()
    while not _stop.is_set():
        nxt = next_run_at()
        wait = interval
        if nxt:
            wait = max(30.0, (datetime.fromisoformat(nxt) - datetime.now(timezone.utc)).total_seconds())
        if _stop.wait(min(wait, 600)):
            break
        nxt = next_run_at()
        if not nxt or datetime.fromisoformat(nxt) <= datetime.now(timezone.utc):
            collect_now()


def start() -> None:
    global _thread
    if _thread and _thread.is_alive():
        return
    _stop.clear()
    _thread = threading.Thread(target=_loop, name="tb-scheduler", daemon=True)
    _thread.start()
    log.info("scheduler started, every %s h", config.COLLECT_INTERVAL_HOURS)


def stop() -> None:
    _stop.set()
