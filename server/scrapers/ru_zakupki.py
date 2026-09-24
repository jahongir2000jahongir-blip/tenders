"""Russia, zakupki.gov.ru (EIS) via the official RSS feed of the extended search.

Endpoint: https://zakupki.gov.ru/epz/order/extendedsearch/rss.html
Each item carries the registry number in the link and a HTML description with
"Заказчик", "Начальная цена", "Размещено", "Окончание подачи заявок".
"""
from __future__ import annotations

import re

import feedparser

from .. import config
from .base import Notice, bounded, clean, client, log, parse_amount, parse_date

SOURCE = "ru_zakupki"
RSS_URL = (
    "https://zakupki.gov.ru/epz/order/extendedsearch/rss.html"
    "?morphology=on&search-filter=Дате+размещения&fz44=on&fz223=on&af=on"
    "&currencyIdGeneral=-1&sortBy=PUBLISH_DATE&sortDirection=false&recordsPerPage=_50"
)

_FIELD = re.compile(r"<strong>\s*([^<:]+?)\s*:?\s*</strong>\s*([^<]*)", re.IGNORECASE)


def parse_description(html: str) -> dict[str, str]:
    """Turn the RSS description ('<strong>Заказчик:</strong> Имя<br>…') into a dict."""
    fields: dict[str, str] = {}
    for key, value in _FIELD.findall(html or ""):
        fields[key.strip().rstrip(":").lower()] = clean(value) or ""
    return fields


def parse_feed(text: str) -> list[Notice]:
    feed = feedparser.parse(text)
    notices: list[Notice] = []
    for entry in feed.entries:
        try:
            link = entry.get("link", "")
            m = re.search(r"regNumber=(\d+)", link) or re.search(r"noticeInfoId=(\d+)", link)
            ext = m.group(1) if m else link
            fields = parse_description(entry.get("summary") or entry.get("description") or "")
            title = clean(entry.get("title")) or ""
            title = re.sub(r"^№\s*\S+\s*", "", title)
            price_raw = fields.get("начальная цена") or fields.get("начальная (максимальная) цена контракта") or ""
            currency = "RUB" if ("руб" in price_raw.lower() or not price_raw) else None
            if not currency:
                currency = "USD" if "доллар" in price_raw.lower() else "EUR" if "евро" in price_raw.lower() else "RUB"
            notices.append(Notice(
                source=SOURCE, external_id=ext, country="RU", title=title, url=link,
                description=fields.get("наименование объекта закупки"),
                customer=fields.get("заказчик"),
                method=fields.get("способ размещения закупки") or fields.get("способ определения поставщика"),
                amount=parse_amount(price_raw), currency=currency,
                published_at=parse_date(fields.get("размещено")) or parse_date(entry.get("published")),
                deadline_at=parse_date(fields.get("окончание подачи заявок")),
                lang="ru", raw={"fields": fields},
            ))
        except Exception as exc:  # one bad entry must not kill the run
            log.warning("%s: skipped entry: %s", SOURCE, exc)
    return notices


def collect() -> list[Notice]:
    with client(headers={"Accept": "application/rss+xml, application/xml"}) as c:
        r = c.get(RSS_URL)
        r.raise_for_status()
        return bounded(parse_feed(r.text), config.MAX_PER_SOURCE)
