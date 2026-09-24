"""Generic JSON-list collector used by portals whose SPA backend returns a list of notices.

The field map is tolerant: each logical field has several candidate keys, and the list
itself is looked up under common container keys. Used by uz_xarid, kg_zakupki, az_etender.
"""
from __future__ import annotations

from typing import Any, Iterable

from .. import config
from .base import Notice, bounded, clean, client, log, parse_amount, parse_date

CONTAINER_KEYS = ("data", "items", "result", "results", "rows", "content", "list", "releases", "records", "value")


def find_list(payload: Any) -> list[dict]:
    if isinstance(payload, list):
        return [x for x in payload if isinstance(x, dict)]
    if isinstance(payload, dict):
        for key in CONTAINER_KEYS:
            if key in payload:
                found = find_list(payload[key])
                if found:
                    return found
        for value in payload.values():
            if isinstance(value, (list, dict)):
                found = find_list(value)
                if found:
                    return found
    return []


def first(d: dict, keys: Iterable[str]) -> Any:
    for k in keys:
        cur: Any = d
        for part in k.split("."):
            if isinstance(cur, dict) and part in cur:
                cur = cur[part]
            else:
                cur = None
                break
        if cur not in (None, "", [], {}):
            return cur
    return None


FIELD_KEYS = {
    "id": ("id", "lotId", "lot_id", "tenderId", "tender_id", "eventId", "ocid", "number", "code", "uid"),
    "title": ("title", "name", "lotName", "lot_name", "productName", "subject", "eventName", "tender.title", "description"),
    "customer": ("customer", "customerName", "customer_name", "organization", "organizationName", "buyer.name",
                 "buyerOrganizationName", "procuringEntity.name", "orgName", "tender.procuringEntity.name"),
    "region": ("region", "regionName", "city", "area", "buyer.address.region"),
    "method": ("method", "procurementMethod", "tenderType", "type", "procedureType", "tender.procurementMethodDetails"),
    "amount": ("amount", "sum", "price", "startPrice", "totalSum", "estimatedAmount", "value.amount", "tender.value.amount", "budget"),
    "currency": ("currency", "currencyCode", "value.currency", "tender.value.currency"),
    "published": ("publishedDate", "publishDate", "published_at", "createdDate", "startDate", "date", "dateModified",
                  "tender.tenderPeriod.startDate", "publicationDate"),
    "deadline": ("deadline", "endDate", "deadlineDate", "closeDate", "tender.tenderPeriod.endDate", "expireDate", "finishDate"),
    "description": ("description", "details", "tender.description", "note"),
    "cpv": ("cpv", "cpvCode", "classification.id", "tender.classification.id", "category"),
}


def map_generic(item: dict, source: str, country: str, currency: str, url_tpl: str) -> Notice | None:
    ext = first(item, FIELD_KEYS["id"])
    title = clean(first(item, FIELD_KEYS["title"]))
    if not ext or not title:
        return None
    cpv = first(item, FIELD_KEYS["cpv"])
    return Notice(
        source=source, external_id=str(ext), country=country, title=title,
        url=url_tpl.format(id=ext),
        description=clean(first(item, FIELD_KEYS["description"])),
        customer=clean(first(item, FIELD_KEYS["customer"])),
        region=clean(first(item, FIELD_KEYS["region"])),
        method=clean(first(item, FIELD_KEYS["method"])),
        amount=parse_amount(first(item, FIELD_KEYS["amount"])),
        currency=(first(item, FIELD_KEYS["currency"]) or currency),
        published_at=parse_date(first(item, FIELD_KEYS["published"])),
        deadline_at=parse_date(first(item, FIELD_KEYS["deadline"])),
        cpv=str(cpv) if cpv and str(cpv)[:2].isdigit() else None,
        raw={"keys": sorted(item.keys())[:40]},
    )


def make_collector(*, source: str, country: str, currency: str, endpoints: list[dict], url_tpl: str, lang: str):
    """`endpoints` are tried in order; each is {"url", "method", "params"|"json"}."""
    def collect() -> list[Notice]:
        last_error: Exception | None = None
        with client(headers={"Accept": "application/json, text/plain, */*"}) as c:
            for ep in endpoints:
                try:
                    if ep.get("method", "GET").upper() == "POST":
                        r = c.post(ep["url"], json=ep.get("json"), params=ep.get("params"))
                    else:
                        r = c.get(ep["url"], params=ep.get("params"))
                    r.raise_for_status()
                    items = find_list(r.json())
                    notices = []
                    for it in items:
                        try:
                            n = map_generic(it, source, country, currency, url_tpl)
                            if n:
                                n.lang = lang
                                notices.append(n)
                        except Exception as exc:
                            log.warning("%s: skipped item: %s", source, exc)
                    if notices:
                        return bounded(notices, config.MAX_PER_SOURCE)
                    last_error = RuntimeError(f"{ep['url']}: no notices recognised in response")
                except Exception as exc:
                    last_error = exc
                    log.warning("%s: endpoint %s failed: %s", source, ep["url"], exc)
        raise RuntimeError(f"all endpoints failed: {last_error}")
    collect.__name__ = f"collect_{source}"
    return collect
