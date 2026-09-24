"""Collectors for SPA-style portals built on the generic JSON collector.

Endpoints below are the ones the portals' own front-ends call. They cannot be
verified from the build sandbox (no outbound access); if a portal changes its API,
adjust the `endpoints` list here — nothing else needs to change.
"""
from __future__ import annotations

from .generic_json import make_collector

# Uzbekistan — UZEX e-procurement (xarid.uzex.uz / etender.uzex.uz)
uz_xarid = make_collector(
    source="uz_xarid", country="UZ", currency="UZS", lang="uz",
    url_tpl="https://xarid.uzex.uz/ru/tender/{id}",
    endpoints=[
        {"url": "https://xarid-api-trade.uzex.uz/Common/GetTradeList",
         "method": "POST", "json": {"trade_type": 3, "page_index": 1, "page_size": 100, "status": 1}},
        {"url": "https://apietender.uzex.uz/api/common/LotsList",
         "method": "POST", "json": {"from": 0, "to": 100, "categoryId": 0, "status": 1}},
    ],
)

# Kyrgyzstan — OCDS publication of zakupki.gov.kg
kg_zakupki = make_collector(
    source="kg_zakupki", country="KG", currency="KGS", lang="ru",
    url_tpl="https://zakupki.gov.kg/popp/view/order/view.xhtml?id={id}",
    endpoints=[
        {"url": "https://ocds.zakupki.gov.kg/api/tendering", "params": {"page": 1, "size": 100, "sort": "date,desc"}},
        {"url": "https://zakupki.gov.kg/popp/api/v1/tender/search", "params": {"page": 0, "size": 100, "status": "PUBLISHED"}},
    ],
)

# Azerbaijan — etender.gov.az
az_etender = make_collector(
    source="az_etender", country="AZ", currency="AZN", lang="az",
    url_tpl="https://etender.gov.az/main/competition/detail/{id}",
    endpoints=[
        {"url": "https://etender.gov.az/api/events", "params": {"EventType": 2, "EventStatus": 1, "PageSize": 100, "PageNumber": 1}},
        {"url": "https://etender.gov.az/api/events", "params": {"PageSize": 100, "PageNumber": 1}},
    ],
)
