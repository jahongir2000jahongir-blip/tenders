"""Kazakhstan, goszakup.gov.kz.

Preferred: open API v3 (needs a free bearer token, env GOSZAKUP_TOKEN):
    GET https://ows.goszakup.gov.kz/v3/trd-buy?limit=100   -> {"items": [...]}
Fallback without a token: the public announcements search page (HTML table).
"""
from __future__ import annotations

import re

from bs4 import BeautifulSoup

from .. import config
from .base import Notice, bounded, clean, client, log, parse_amount, parse_date

SOURCE = "kz_goszakup"
API = "https://ows.goszakup.gov.kz/v3/trd-buy"
SEARCH = "https://goszakup.gov.kz/ru/search/announce"
ANNOUNCE = "https://goszakup.gov.kz/ru/announce/index/{id}"
METHODS = {1: "Открытый конкурс", 2: "Запрос ценовых предложений", 3: "Из одного источника",
           6: "Аукцион", 7: "Конкурс с предварительным квалификационным отбором", 32: "Открытый конкурс"}


def map_api_item(it: dict) -> Notice:
    return Notice(
        source=SOURCE, external_id=str(it.get("id") or it.get("number_anno")), country="KZ",
        title=clean(it.get("name_ru") or it.get("name_kz")) or "",
        url=ANNOUNCE.format(id=it.get("id")),
        customer=clean(it.get("org_name_ru") or it.get("org_name_kz") or it.get("customer_name_ru")),
        method=METHODS.get(it.get("ref_trade_methods_id"), clean(it.get("ref_trade_methods_name"))),
        amount=parse_amount(it.get("total_sum")), currency="KZT",
        published_at=parse_date(it.get("publish_date") or it.get("start_date")),
        deadline_at=parse_date(it.get("end_date")),
        lang="ru", raw={"number": it.get("number_anno"), "lots": it.get("count_lots")},
    )


def parse_search_html(html: str) -> list[Notice]:
    soup = BeautifulSoup(html, "lxml")
    notices: list[Notice] = []
    for tr in soup.select("table tr"):
        cells = [clean(td.get_text(" ")) or "" for td in tr.find_all("td")]
        link = tr.find("a", href=re.compile(r"/announce/index/(\d+)"))
        if not link or len(cells) < 5:
            continue
        aid = re.search(r"/announce/index/(\d+)", link["href"]).group(1)
        # columns: № объявления | наименование | организатор | способ | статус? | дата начала | дата окончания | сумма
        dates = [c for c in cells if re.search(r"\d{4}-\d{2}-\d{2}|\d{2}\.\d{2}\.\d{4}", c)]
        sums = [c for c in cells if re.fullmatch(r"[\d\s\xa0]+([.,]\d+)?", c)]
        notices.append(Notice(
            source=SOURCE, external_id=aid, country="KZ",
            title=cells[1] if len(cells) > 1 else clean(link.get_text()) or "",
            url="https://goszakup.gov.kz" + link["href"] if link["href"].startswith("/") else link["href"],
            customer=cells[2] if len(cells) > 2 else None,
            method=cells[3] if len(cells) > 3 else None,
            amount=parse_amount(sums[-1]) if sums else None, currency="KZT",
            published_at=parse_date(dates[0]) if dates else None,
            deadline_at=parse_date(dates[1]) if len(dates) > 1 else None,
            lang="ru",
        ))
    return notices


def collect() -> list[Notice]:
    notices: list[Notice] = []
    with client() as c:
        if config.GOSZAKUP_TOKEN:
            r = c.get(API, params={"limit": 100}, headers={"Authorization": f"Bearer {config.GOSZAKUP_TOKEN}",
                                                            "Accept": "application/json"})
            r.raise_for_status()
            for it in r.json().get("items") or []:
                try:
                    notices.append(map_api_item(it))
                except Exception as exc:
                    log.warning("%s: skipped %s: %s", SOURCE, it.get("id"), exc)
        else:
            for page in (1, 2):
                r = c.get(SEARCH, params={"filter[status][]": "210", "count_record": 50, "page": page})
                r.raise_for_status()
                notices.extend(parse_search_html(r.text))
                if len(notices) >= config.MAX_PER_SOURCE:
                    break
    return bounded(notices, config.MAX_PER_SOURCE)
