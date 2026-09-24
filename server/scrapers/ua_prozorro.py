"""Ukraine, Prozorro central database public API (OpenProcurement).

Endpoint: https://public.api.openprocurement.org/api/2.5/tenders?descending=1&opt_fields=...
The list endpoint returns the newest modified tenders with the requested fields inline.
"""
from __future__ import annotations

from .. import config
from .base import Notice, bounded, clean, client, log, parse_date

SOURCE = "ua_prozorro"
API = "https://public.api.openprocurement.org/api/2.5/tenders"
OPT_FIELDS = "status,tenderID,title,procuringEntity,value,tenderPeriod,procurementMethodType,items,dateModified"
ACTIVE = {"active.enquiries", "active.tendering", "active.prequalification", "active.auction"}
METHODS = {
    "aboveThresholdUA": "Открытые торги", "aboveThresholdEU": "Открытые торги с публикацией на английском",
    "belowThreshold": "Допороговая закупка", "reporting": "Отчёт о договоре", "negotiation": "Переговорная процедура",
    "competitiveDialogueUA": "Конкурентный диалог", "esco": "ESCO", "priceQuotation": "Запрос цен",
    "simple.defense": "Упрощённая закупка (оборона)", "closeFrameworkAgreementUA": "Рамочное соглашение",
}


def map_item(t: dict) -> Notice | None:
    if t.get("status") not in ACTIVE:
        return None
    tid = t.get("tenderID") or t.get("id")
    value = t.get("value") or {}
    period = t.get("tenderPeriod") or {}
    entity = t.get("procuringEntity") or {}
    addr = entity.get("address") or {}
    items = t.get("items") or []
    cpv = (items[0].get("classification") or {}).get("id") if items else None
    return Notice(
        source=SOURCE, external_id=str(tid), country="UA", title=clean(t.get("title")) or "",
        url=f"https://prozorro.gov.ua/tender/{tid}",
        description=clean(t.get("description")),
        customer=clean(entity.get("name")), region=clean(addr.get("region")),
        method=METHODS.get(t.get("procurementMethodType"), t.get("procurementMethodType")),
        amount=float(value["amount"]) if value.get("amount") is not None else None,
        currency=value.get("currency"),
        published_at=parse_date(period.get("startDate")) or parse_date(t.get("dateModified")),
        deadline_at=parse_date(period.get("endDate")),
        cpv=cpv, lang="uk", raw={"status": t.get("status"), "cpv": cpv},
    )


def collect() -> list[Notice]:
    notices: list[Notice] = []
    with client(headers={"Accept": "application/json"}) as c:
        offset = None
        while len(notices) < config.MAX_PER_SOURCE:
            params = {"descending": "1", "limit": "100", "opt_fields": OPT_FIELDS}
            if offset:
                params["offset"] = offset
            r = c.get(API, params=params)
            r.raise_for_status()
            data = r.json()
            batch = data.get("data") or []
            if not batch:
                break
            for t in batch:
                try:
                    n = map_item(t)
                    if n:
                        notices.append(n)
                except Exception as exc:
                    log.warning("%s: skipped %s: %s", SOURCE, t.get("id"), exc)
            offset = (data.get("next_page") or {}).get("offset")
            if not offset or len(batch) < 100:
                break
    return bounded(notices, config.MAX_PER_SOURCE)
