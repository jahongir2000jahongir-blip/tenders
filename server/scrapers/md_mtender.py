"""Moldova, MTender public OCDS API.

List:   https://public.mtender.gov.md/tenders/?descending=1     -> {"data": [{"ocid", "date"}]}
Detail: https://public.mtender.gov.md/tenders/{ocid}            -> {"records": [{"compiledRelease": {...}}]}
"""
from __future__ import annotations

from .. import config
from .base import Notice, bounded, clean, client, log, parse_date

SOURCE = "md_mtender"
LIST = "https://public.mtender.gov.md/tenders/"
DETAIL = "https://public.mtender.gov.md/tenders/{ocid}"
PORTAL = "https://mtender.gov.md/tenders/{ocid}"
DETAILS_PER_RUN = 60


def map_release(ocid: str, rel: dict) -> Notice | None:
    tender = rel.get("tender") or {}
    if not tender.get("title"):
        return None
    value = tender.get("value") or {}
    period = tender.get("tenderPeriod") or {}
    buyer = rel.get("buyer") or {}
    items = tender.get("items") or []
    cpv = (tender.get("classification") or {}).get("id") or (
        (items[0].get("classification") or {}).get("id") if items else None)
    return Notice(
        source=SOURCE, external_id=ocid, country="MD", title=clean(tender.get("title")) or "",
        url=PORTAL.format(ocid=ocid), description=clean(tender.get("description")),
        customer=clean(buyer.get("name")),
        method=clean(tender.get("procurementMethodDetails") or tender.get("procurementMethod")),
        amount=float(value["amount"]) if value.get("amount") is not None else None,
        currency=value.get("currency") or "MDL",
        published_at=parse_date(period.get("startDate")) or parse_date(rel.get("date")),
        deadline_at=parse_date(period.get("endDate")),
        cpv=cpv, lang="ro", raw={"status": tender.get("status")},
    )


def collect() -> list[Notice]:
    notices: list[Notice] = []
    with client(headers={"Accept": "application/json"}) as c:
        r = c.get(LIST, params={"descending": "1"})
        r.raise_for_status()
        ids = [row.get("ocid") for row in (r.json().get("data") or []) if row.get("ocid")]
        for ocid in ids[:DETAILS_PER_RUN]:
            try:
                d = c.get(DETAIL.format(ocid=ocid))
                d.raise_for_status()
                records = d.json().get("records") or []
                rel = (records[0].get("compiledRelease") if records else None) or {}
                n = map_release(ocid, rel)
                if n:
                    notices.append(n)
            except Exception as exc:
                log.warning("%s: skipped %s: %s", SOURCE, ocid, exc)
    return bounded(notices, config.MAX_PER_SOURCE)
