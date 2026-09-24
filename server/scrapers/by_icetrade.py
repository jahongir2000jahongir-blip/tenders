"""Belarus, icetrade.by (public tender list, HTML).

Endpoint: https://icetrade.by/tenders/all — table rows linking to /tenders/view/{id}.
"""
from __future__ import annotations

import re

from bs4 import BeautifulSoup

from .. import config
from .base import Notice, bounded, clean, client, parse_amount, parse_date

SOURCE = "by_icetrade"
LIST = "https://icetrade.by/tenders/all"
BASE = "https://icetrade.by"

_DATE = re.compile(r"\d{2}\.\d{2}\.\d{4}(?:\s+\d{2}:\d{2})?")


def parse_list(html: str) -> list[Notice]:
    soup = BeautifulSoup(html, "lxml")
    notices: list[Notice] = []
    seen: set[str] = set()
    for link in soup.select("a[href*='/tenders/view/']"):
        m = re.search(r"/tenders/view/(\d+)", link["href"])
        if not m or m.group(1) in seen:
            continue
        seen.add(m.group(1))
        row = link.find_parent("tr") or link.find_parent("div")
        text = clean(row.get_text(" ")) if row else ""
        cells = [clean(td.get_text(" ")) or "" for td in row.find_all("td")] if row and row.name == "tr" else []
        dates = _DATE.findall(text or "")
        customer = None
        if len(cells) >= 3:
            customer = next((c for c in cells if c and c != clean(link.get_text()) and not _DATE.search(c)
                             and not re.fullmatch(r"[\d\s.,]+", c)), None)
        amount = None
        am = re.search(r"([\d\s]+(?:[.,]\d+)?)\s*(BYN|руб)", text or "", re.IGNORECASE)
        if am:
            amount = parse_amount(am.group(1))
        notices.append(Notice(
            source=SOURCE, external_id=m.group(1), country="BY",
            title=clean(link.get_text()) or "", url=BASE + link["href"] if link["href"].startswith("/") else link["href"],
            customer=customer, amount=amount, currency="BYN" if amount else None,
            published_at=parse_date(dates[0]) if dates else None,
            deadline_at=parse_date(dates[-1]) if len(dates) > 1 else None,
            lang="ru",
        ))
    return notices


def collect() -> list[Notice]:
    notices: list[Notice] = []
    with client() as c:
        for page in (1, 2, 3):
            r = c.get(LIST, params={"page": page})
            r.raise_for_status()
            batch = parse_list(r.text)
            if not batch:
                break
            notices.extend(batch)
            if len(notices) >= config.MAX_PER_SOURCE:
                break
    return bounded(notices, config.MAX_PER_SOURCE)
