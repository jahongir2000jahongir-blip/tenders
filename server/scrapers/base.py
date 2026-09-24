"""Shared collector primitives.

A collector is a callable returning a list of `Notice` objects. Every collector:
  * fetches only the newest notices (bounded by `config.MAX_PER_SOURCE`),
  * never raises for a single bad record (it is skipped and logged),
  * returns whatever it managed to parse; the pipeline handles de-duplication.
"""
from __future__ import annotations

import html as _html
import logging
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable

import httpx

from .. import config

log = logging.getLogger("collector")


@dataclass
class Notice:
    source: str
    external_id: str
    country: str
    title: str
    url: str | None = None
    description: str | None = None
    customer: str | None = None
    region: str | None = None
    method: str | None = None
    amount: float | None = None
    currency: str | None = None
    published_at: str | None = None   # ISO 8601
    deadline_at: str | None = None    # ISO 8601
    cpv: str | None = None
    lang: str | None = None
    raw: dict[str, Any] = field(default_factory=dict)


Collector = Callable[[], list[Notice]]


def client(**kw) -> httpx.Client:
    headers = {"User-Agent": config.USER_AGENT, "Accept-Language": "ru,en;q=0.8"}
    headers.update(kw.pop("headers", {}))
    return httpx.Client(timeout=config.HTTP_TIMEOUT, follow_redirects=True, headers=headers, **kw)


# ---------- small parsing helpers ----------

_DATE_PATTERNS = [
    "%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%S.%f%z", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%S.%f",
    "%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d",
    "%d.%m.%Y %H:%M:%S", "%d.%m.%Y %H:%M", "%d.%m.%Y",
    "%d/%m/%Y %H:%M", "%d/%m/%Y", "%d-%m-%Y",
    "%a, %d %b %Y %H:%M:%S %z", "%a, %d %b %Y %H:%M:%S %Z",
]


def parse_date(value: Any) -> str | None:
    """Best-effort conversion of many date spellings into ISO 8601 (UTC when zone is known)."""
    if value in (None, ""):
        return None
    if isinstance(value, (int, float)):
        ts = float(value)
        if ts > 1e12:
            ts /= 1000
        return datetime.fromtimestamp(ts, tz=timezone.utc).replace(microsecond=0).isoformat()
    s = str(value).strip()
    s = re.sub(r"\s+", " ", s)
    s = s.replace("Z", "+00:00") if s.endswith("Z") else s
    # 2024-05-01T10:00:00+0300 -> +03:00
    s = re.sub(r"([+-]\d{2})(\d{2})$", r"\1:\2", s)
    for pat in _DATE_PATTERNS:
        try:
            dt = datetime.strptime(s, pat)
        except ValueError:
            continue
        if dt.tzinfo is not None:
            dt = dt.astimezone(timezone.utc)
        return dt.replace(microsecond=0).isoformat()
    m = re.search(r"(\d{4})-(\d{2})-(\d{2})", s)
    if m:
        return f"{m.group(1)}-{m.group(2)}-{m.group(3)}T00:00:00"
    m = re.search(r"(\d{2})\.(\d{2})\.(\d{4})", s)
    if m:
        return f"{m.group(3)}-{m.group(2)}-{m.group(1)}T00:00:00"
    return None


def parse_amount(value: Any) -> float | None:
    if value in (None, ""):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    s = str(value)
    s = re.sub(r"[^\d,.\-]", "", s.replace("\xa0", ""))
    if not s:
        return None
    # "1 234 567,89" -> 1234567.89 ; "1,234,567.89" -> 1234567.89
    if s.count(",") and s.count("."):
        s = s.replace(",", "") if s.rfind(".") > s.rfind(",") else s.replace(".", "").replace(",", ".")
    elif s.count(","):
        parts = s.split(",")
        s = s.replace(",", ".") if len(parts) == 2 and len(parts[1]) <= 2 else s.replace(",", "")
    try:
        return float(s)
    except ValueError:
        return None


def clean(text: Any) -> str | None:
    if text is None:
        return None
    s = re.sub(r"<[^>]+>", " ", str(text))
    s = _html.unescape(s)
    s = re.sub(r"\s+", " ", s).strip()
    return s or None


def bounded(items: list, limit: int | None = None) -> list:
    return items[: (limit or config.MAX_PER_SOURCE)]
