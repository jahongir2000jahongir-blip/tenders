"""Poland, Biuletyn Zamówień Publicznych open API (ezamowienia.gov.pl).

Endpoint: https://ezamowienia.gov.pl/mo-board/api/v1/notice
Returns a JSON array of notices; `objectId` is the stable identifier.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from .. import config
from .base import Notice, bounded, clean, client, log, parse_amount, parse_date

SOURCE = "pl_bzp"
API = "https://ezamowienia.gov.pl/mo-board/api/v1/notice"
DETAIL = "https://ezamowienia.gov.pl/mo-client-board/bzp/notice-details/{id}"


def map_item(n: dict) -> Notice:
    ext = str(n.get("objectId") or n.get("noticeNumber") or n.get("bzpTenderNoticeId"))
    city = clean(n.get("organizationCity"))
    province = clean(n.get("organizationProvince"))
    region = ", ".join(x for x in (city, province) if x) or None
    return Notice(
        source=SOURCE, external_id=ext, country="PL",
        title=clean(n.get("orderObject") or n.get("noticeTitle") or n.get("title")) or "",
        url=DETAIL.format(id=n.get("objectId") or ext),
        customer=clean(n.get("organizationName")), region=region,
        method=clean(n.get("procedureType") or n.get("tenderType")),
        amount=parse_amount(n.get("estimatedValue") or n.get("orderValue")), currency="PLN",
        published_at=parse_date(n.get("publicationDate")),
        deadline_at=parse_date(n.get("submittingOffersDate") or n.get("offersDeadline")),
        cpv=str(n.get("cpvCode") or "") or None, lang="pl",
        raw={"noticeNumber": n.get("noticeNumber"), "orderType": n.get("orderType")},
    )


def collect() -> list[Notice]:
    since = (datetime.now(timezone.utc) - timedelta(days=3)).strftime("%Y-%m-%dT00:00:00")
    notices: list[Notice] = []
    with client(headers={"Accept": "application/json"}) as c:
        page = 1
        while len(notices) < config.MAX_PER_SOURCE and page <= 5:
            r = c.get(API, params={
                "NoticeType": "ContractNotice", "PublicationDateFrom": since,
                "PageSize": 100, "PageNumber": page,
                "SortingColumnName": "PublicationDate", "SortingDirection": "DESC",
            })
            r.raise_for_status()
            batch = r.json()
            if isinstance(batch, dict):
                batch = batch.get("items") or batch.get("data") or []
            if not batch:
                break
            for n in batch:
                try:
                    notices.append(map_item(n))
                except Exception as exc:
                    log.warning("%s: skipped %s: %s", SOURCE, n.get("objectId"), exc)
            if len(batch) < 100:
                break
            page += 1
    return bounded(notices, config.MAX_PER_SOURCE)
