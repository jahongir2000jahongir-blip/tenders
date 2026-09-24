"""EU countries via Tenders Electronic Daily (TED) search API v3.

Endpoint: POST https://api.ted.europa.eu/v3/notices/search
Query language is TED expert search; multilingual fields come back as {lang: value}.
One collector instance per country (CZ, DE, LT); Poland is covered by BZP.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from .. import config
from .base import Notice, bounded, clean, client, log, parse_amount, parse_date

API = "https://api.ted.europa.eu/v3/notices/search"
FIELDS = [
    "publication-number", "notice-title", "buyer-name", "buyer-country", "publication-date",
    "deadline-receipt-tender-date-lot", "estimated-value-lot", "estimated-value-cur-lot",
    "classification-cpv", "place-of-performance", "procedure-type", "links", "notice-type",
]
ISO3 = {"CZ": "CZE", "DE": "DEU", "LT": "LTU", "PL": "POL"}
LANG_PREF = {"CZ": ["ces", "eng"], "DE": ["deu", "eng"], "LT": ["lit", "eng"], "PL": ["pol", "eng"]}


def pick_lang(value: Any, prefs: list[str]) -> Any:
    """TED multilingual fields: {"eng": "x"} or {"eng": ["x"]}; return a plain string."""
    if value is None:
        return None
    if isinstance(value, dict):
        for lang in prefs + list(value.keys()):
            if lang in value:
                return pick_lang(value[lang], prefs)
        return None
    if isinstance(value, list):
        return pick_lang(value[0], prefs) if value else None
    return value


def map_item(n: dict, country: str) -> Notice:
    prefs = LANG_PREF.get(country, ["eng"])
    pub = str(n.get("publication-number"))
    links = n.get("links") or {}
    html = links.get("html") or {}
    url = pick_lang(html, ["ENG", "eng"] + [p.upper() for p in prefs]) if html else None
    url = url or f"https://ted.europa.eu/en/notice/-/detail/{pub}"
    cpv = n.get("classification-cpv")
    if isinstance(cpv, list):
        cpv = cpv[0] if cpv else None
    return Notice(
        source=f"ted_{country.lower()}", external_id=pub, country=country,
        title=clean(pick_lang(n.get("notice-title"), prefs)) or "",
        url=url, customer=clean(pick_lang(n.get("buyer-name"), prefs)),
        region=clean(pick_lang(n.get("place-of-performance"), prefs)),
        method=clean(pick_lang(n.get("procedure-type"), prefs)),
        amount=parse_amount(pick_lang(n.get("estimated-value-lot"), prefs)),
        currency=(pick_lang(n.get("estimated-value-cur-lot"), prefs) or "EUR"),
        published_at=parse_date(n.get("publication-date")),
        deadline_at=parse_date(pick_lang(n.get("deadline-receipt-tender-date-lot"), prefs)),
        cpv=str(cpv) if cpv else None, lang=prefs[0][:2],
        raw={"notice-type": n.get("notice-type")},
    )


def make_collector(country: str):
    def collect() -> list[Notice]:
        since = (datetime.now(timezone.utc) - timedelta(days=3)).strftime("%Y%m%d")
        query = (
            f"(place-of-performance IN ({ISO3[country]}) OR buyer-country = {ISO3[country]}) "
            f"AND notice-type IN (cn-standard cn-social cn-desg pin-cfc-standard) "
            f"AND publication-date >= {since}"
        )
        body = {"query": query, "fields": FIELDS, "limit": min(100, config.MAX_PER_SOURCE),
                "page": 1, "scope": "LATEST", "paginationMode": "PAGE_NUMBER"}
        notices: list[Notice] = []
        with client(headers={"Accept": "application/json"}) as c:
            r = c.post(API, json=body)
            r.raise_for_status()
            for n in (r.json().get("notices") or []):
                try:
                    notices.append(map_item(n, country))
                except Exception as exc:
                    log.warning("ted_%s: skipped %s: %s", country, n.get("publication-number"), exc)
        return bounded(notices, config.MAX_PER_SOURCE)
    collect.__name__ = f"collect_ted_{country.lower()}"
    return collect
