"""Collector registry: source code -> callable returning notices."""
from __future__ import annotations

from .base import Collector, Notice  # noqa: F401
from . import by_icetrade, kz_goszakup, md_mtender, pl_bzp, ru_zakupki, ted, tj_zakupki, ua_prozorro, ungm
from .portals import az_etender, kg_zakupki, uz_xarid

COLLECTORS: dict[str, Collector] = {
    "tj_zakupki": tj_zakupki.collect,
    "uz_xarid": uz_xarid,
    "kg_zakupki": kg_zakupki,
    "kz_goszakup": kz_goszakup.collect,
    "ungm_tm": ungm.make_collector("TM"),
    "ungm_af": ungm.make_collector("AF"),
    "ru_zakupki": ru_zakupki.collect,
    "by_icetrade": by_icetrade.collect,
    "ua_prozorro": ua_prozorro.collect,
    "md_mtender": md_mtender.collect,
    "az_etender": az_etender,
    "pl_bzp": pl_bzp.collect,
    "ted_cz": ted.make_collector("CZ"),
    "ted_de": ted.make_collector("DE"),
    "ted_lt": ted.make_collector("LT"),
}
