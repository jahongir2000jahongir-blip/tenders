"""UN Global Marketplace public notices, filtered by beneficiary country (Turkmenistan, Afghanistan).

Endpoint: POST https://www.ungm.org/Public/Notice/Search (JSON body, HTML rows in the response).
The response is a table of `div.tableRow` elements with `data-noticeid` attributes.
"""
from __future__ import annotations

import re

from bs4 import BeautifulSoup

from .. import config
from .base import Notice, bounded, clean, client, log, parse_date

SEARCH = "https://www.ungm.org/Public/Notice/Search"
NOTICE = "https://www.ungm.org/Public/Notice/{id}"
COUNTRY_NAMES = {"TM": ("Turkmenistan",), "AF": ("Afghanistan",)}


def search_body(page: int) -> dict:
    return {
        "PageIndex": page, "PageSize": 100, "Title": "", "Description": "", "Reference": "",
        "PublishedFrom": "", "PublishedTo": "", "DeadlineFrom": "", "DeadlineTo": "",
        "Countries": [], "Agencies": [], "UNSPSCs": [], "NoticeTypes": [], "SortField": "DatePublished",
        "SortAscending": False, "isPicker": False, "IsSustainable": False, "NoticeDisplayType": None,
        "NoticeSearchTotalLabelId": "noticeSearchTotal", "TypeOfCompetitions": [],
    }


def _cell(row, *names: str) -> str | None:
    for name in names:
        el = row.select_one(f".{name}")
        if el:
            return clean(el.get_text(" "))
    return None


def parse_rows(html: str, country: str) -> list[Notice]:
    soup = BeautifulSoup(html, "lxml")
    wanted = COUNTRY_NAMES[country]
    notices: list[Notice] = []
    for row in soup.select("div.tableRow[data-noticeid], div[data-noticeid]"):
        nid = row.get("data-noticeid")
        ctry = _cell(row, "resultCountry", "notice-country") or ""
        if not nid or not any(w.lower() in ctry.lower() for w in wanted):
            continue
        title = _cell(row, "resultTitle", "notice-title") or clean(row.get_text(" ")) or ""
        notices.append(Notice(
            source=f"ungm_{country.lower()}", external_id=str(nid), country=country, title=title,
            url=NOTICE.format(id=nid),
            customer=_cell(row, "resultAgency", "notice-agency"),
            method=_cell(row, "resultType", "notice-type"),
            published_at=parse_date(_cell(row, "resultPublished", "notice-published")),
            deadline_at=parse_date(_cell(row, "resultDeadline", "notice-deadline")),
            lang="en", raw={"reference": _cell(row, "resultReference", "notice-reference")},
        ))
    return notices


def make_collector(country: str):
    def collect() -> list[Notice]:
        notices: list[Notice] = []
        with client(headers={"Accept": "text/html, */*", "X-Requested-With": "XMLHttpRequest"}) as c:
            c.get("https://www.ungm.org/Public/Notice")  # cookies / anti-forgery
            for page in range(0, 6):
                r = c.post(SEARCH, json=search_body(page))
                r.raise_for_status()
                batch = parse_rows(r.text, country)
                notices.extend(batch)
                if not re.search(r"data-noticeid", r.text):
                    break
        return bounded(notices, config.MAX_PER_SOURCE)
    collect.__name__ = f"collect_ungm_{country.lower()}"
    return collect
