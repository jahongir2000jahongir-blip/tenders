"""Collection pipeline: run collectors, normalise notices, upsert without duplicates.

De-duplication has two layers:
  1. UNIQUE (source, external_id) — the same notice from the same portal is updated in place.
  2. A content fingerprint (country + normalised title + deadline day + normalised buyer) —
     the same tender re-published by another source (e.g. TED and a national portal)
     is skipped and counted as a duplicate.
"""
from __future__ import annotations

import hashlib
import json
import logging
import re
import time
import traceback
from dataclasses import dataclass
from datetime import datetime, timezone

from . import db, rates
from .classify import classify
from .countries import SOURCE_BY_CODE
from .scrapers import COLLECTORS, Notice

log = logging.getLogger("pipeline")

_WS = re.compile(r"\s+")
_PUNCT = re.compile(r"[^\w\s]", re.UNICODE)


def norm(text: str | None) -> str:
    return _WS.sub(" ", _PUNCT.sub(" ", (text or "").lower())).strip()


def fingerprint(n: Notice) -> str:
    day = (n.deadline_at or "")[:10]
    key = "|".join([n.country, norm(n.title)[:160], day, norm(n.customer)[:80]])
    return hashlib.sha1(key.encode("utf-8")).hexdigest()


def status_for(deadline_at: str | None) -> str:
    if not deadline_at:
        return "open"
    try:
        dl = datetime.fromisoformat(deadline_at.replace("Z", "+00:00"))
    except ValueError:
        return "open"
    if dl.tzinfo is None:
        dl = dl.replace(tzinfo=timezone.utc)
    return "closed" if dl < datetime.now(timezone.utc) else "open"


@dataclass
class RunResult:
    source: str
    status: str
    fetched: int = 0
    added: int = 0
    updated: int = 0
    duplicates: int = 0
    error: str | None = None
    seconds: float = 0.0


def upsert(notices: list[Notice], source: str) -> RunResult:
    """Write notices for one source. Returns counters."""
    res = RunResult(source=source, status="ok", fetched=len(notices))
    now = db.utcnow()
    with db.tx() as con:
        for n in notices:
            if not n.title or not n.external_id:
                continue
            fp = fingerprint(n)
            existing = con.execute(
                "SELECT id FROM tenders WHERE source=? AND external_id=?", (n.source, n.external_id)
            ).fetchone()
            amount_usd = rates.to_usd(n.amount, n.currency)
            category = classify(n.title, n.description, n.cpv)
            payload = (
                n.country, n.title[:600], (n.description or None) and n.description[:4000], n.customer, n.region,
                category, n.method, n.amount, n.currency, amount_usd, n.published_at, n.deadline_at, n.url,
                status_for(n.deadline_at), fp, n.lang, json.dumps(n.raw, ensure_ascii=False, default=str)[:20000], now,
            )
            if existing:
                con.execute(
                    "UPDATE tenders SET country=?, title=?, description=?, customer=?, region=?, category=?, method=?, "
                    "amount=?, currency=?, amount_usd=?, published_at=?, deadline_at=?, url=?, status=?, fingerprint=?, "
                    "lang=?, raw=?, updated_at=? WHERE id=?",
                    payload + (existing["id"],),
                )
                res.updated += 1
                continue
            dup = con.execute(
                "SELECT id, source FROM tenders WHERE fingerprint=? AND source<>? LIMIT 1", (fp, n.source)
            ).fetchone()
            if dup:
                res.duplicates += 1
                continue
            con.execute(
                "INSERT INTO tenders (source, external_id, country, title, description, customer, region, category, "
                "method, amount, currency, amount_usd, published_at, deadline_at, url, status, fingerprint, lang, raw, "
                "first_seen_at, updated_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (n.source, n.external_id) + payload[:-1] + (now, now),
            )
            res.added += 1
    return res


def record_run(res: RunResult, started_at: str) -> None:
    with db.tx() as con:
        con.execute(
            "INSERT INTO runs (source, started_at, finished_at, status, fetched, added, updated, duplicates, error) "
            "VALUES (?,?,?,?,?,?,?,?,?)",
            (res.source, started_at, db.utcnow(), res.status, res.fetched, res.added, res.updated, res.duplicates, res.error),
        )
        con.execute(
            "UPDATE sources SET last_run_at=?, last_status=?, last_error=?, last_fetched=?, last_added=?, last_updated=? "
            "WHERE code=?",
            (db.utcnow(), res.status, res.error, res.fetched, res.added, res.updated, res.source),
        )
        # keep the runs table small
        con.execute("DELETE FROM runs WHERE id NOT IN (SELECT id FROM runs ORDER BY id DESC LIMIT 2000)")


def run_source(code: str) -> RunResult:
    collector = COLLECTORS.get(code)
    if not collector:
        raise KeyError(f"unknown source {code}")
    started = db.utcnow()
    t0 = time.time()
    try:
        notices = collector()
        # a collector must only return notices for its own source code
        notices = [n for n in notices if n.source == code]
        res = upsert(notices, code)
    except Exception as exc:
        log.error("%s failed: %s", code, exc)
        res = RunResult(source=code, status="error", error=f"{type(exc).__name__}: {exc}"[:1000])
        log.debug(traceback.format_exc())
    res.seconds = round(time.time() - t0, 1)
    record_run(res, started)
    log.info("%s: %s fetched=%s added=%s updated=%s dup=%s (%.1fs)", code, res.status, res.fetched,
             res.added, res.updated, res.duplicates, res.seconds)
    return res


def expire_closed() -> int:
    """Mark tenders whose deadline has passed as closed."""
    with db.tx() as con:
        cur = con.execute(
            "UPDATE tenders SET status='closed' WHERE status='open' AND deadline_at IS NOT NULL AND deadline_at < ?",
            (db.utcnow(),),
        )
        return cur.rowcount


def run_all(only: list[str] | None = None) -> list[RunResult]:
    db.init()
    rates.refresh()
    enabled = {r["code"] for r in db.rows("SELECT code FROM sources WHERE enabled=1")}
    codes = [c for c in COLLECTORS if (only is None or c in only) and (only is not None or c in enabled)]
    results = [run_source(c) for c in codes]
    closed = expire_closed()
    db.set_setting("last_collect_at", db.utcnow())
    db.set_setting("last_collect_summary", {
        "sources": len(results), "added": sum(r.added for r in results), "updated": sum(r.updated for r in results),
        "duplicates": sum(r.duplicates for r in results), "errors": sum(1 for r in results if r.status != "ok"),
        "closed": closed,
    })
    return results


def source_meta(code: str) -> dict:
    return SOURCE_BY_CODE.get(code, {"code": code, "country": "?", "name": code})
