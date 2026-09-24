"""Tajikistan, zakupki.gov.tj (HTML announcements list).

The portal is a classic server-rendered site; announcements are links whose text is the
tender title, with dates and the buyer in surrounding cells. The parser is defensive:
it finds announcement links by URL pattern and reads dates from the row text.
"""
from __future__ import annotations

import re

from bs4 import BeautifulSoup

from .. import config
from .base import Notice, bounded, clean, client, parse_amount, parse_date

SOURCE = "tj_zakupki"
BASE = "https://zakupki.gov.tj"
LISTS = ["https://zakupki.gov.tj/index.php/ru/tenders", "https://zakupki.gov.tj/ru/tenders", "https://zakupki.gov.tj/tenders"]
_LINK = re.compile(r"/(tender|tenders|lot|announce|zakupk|elon)[^\"']*?(\d{2,})", re.IGNORECASE)
_DATE = re.compile(r"\d{2}\.\d{2}\.\d{4}(?:\s+\d{2}:\d{2})?|\d{4}-\d{2}-\d{2}")


def parse_list(html: str) -> list[Notice]:
    soup = BeautifulSoup(html, "lxml")
    notices: list[Notice] = []
    seen: set[str] = set()
    for link in soup.find_all("a", href=True):
        m = _LINK.search(link["href"])
        title = clean(link.get_text())
        if not m or not title or len(title) < 12:
            continue
        ext = m.group(2)
        if ext in seen:
            continue
        seen.add(ext)
        row = link.find_parent("tr") or link.find_parent("li") or link.find_parent("div")
        text = clean(row.get_text(" ")) if row else ""
        dates = _DATE.findall(text or "")
        am = re.search(r"([\d\s]{3,}(?:[.,]\d+)?)\s*(сомони|TJS)", text or "", re.IGNORECASE)
        customer = None
        cm = re.search(r"(?:Заказчик|Организатор)\s*:?\s*([^|•]+?)(?:\s{2,}|$)", text or "")
        if cm:
            customer = clean(cm.group(1))
        href = link["href"]
        notices.append(Notice(
            source=SOURCE, external_id=ext, country="TJ", title=title,
            url=href if href.startswith("http") else BASE + ("" if href.startswith("/") else "/") + href,
            customer=customer, amount=parse_amount(am.group(1)) if am else None, currency="TJS" if am else None,
            published_at=parse_date(dates[0]) if dates else None,
            deadline_at=parse_date(dates[-1]) if len(dates) > 1 else None,
            lang="ru",
        ))
    return notices


def collect() -> list[Notice]:
    last: Exception | None = None
    with client() as c:
        for url in LISTS:
            try:
                r = c.get(url)
                r.raise_for_status()
                notices = parse_list(r.text)
                if notices:
                    return bounded(notices, config.MAX_PER_SOURCE)
                last = RuntimeError(f"{url}: no announcements recognised")
            except Exception as exc:
                last = exc
    raise RuntimeError(f"all list pages failed: {last}")
