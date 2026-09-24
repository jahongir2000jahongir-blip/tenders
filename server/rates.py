"""Currency conversion to USD.

A static table is the fallback; when the network allows, `refresh()` pulls
current rates from open.er-api.com once a day and stores them in the settings table.
"""
from __future__ import annotations

import logging
import time

import httpx

from . import config, db

log = logging.getLogger(__name__)

# Units of local currency per 1 USD (approximate, updated by refresh()).
STATIC_RATES: dict[str, float] = {
    "USD": 1.0, "EUR": 0.92, "RUB": 92.0, "UAH": 41.0, "BYN": 3.27, "MDL": 17.7,
    "KZT": 480.0, "UZS": 12700.0, "KGS": 87.0, "TJS": 10.9, "TMT": 3.5, "AFN": 71.0,
    "AZN": 1.7, "PLN": 3.95, "CZK": 23.2, "GBP": 0.79, "TRY": 33.0, "CNY": 7.2,
}

_cache: dict[str, float] | None = None
_cache_at = 0.0


def rates() -> dict[str, float]:
    global _cache, _cache_at
    if _cache is None or time.time() - _cache_at > 3600:
        stored = db.get_setting("rates")
        _cache = {**STATIC_RATES, **(stored or {})}
        _cache_at = time.time()
    return _cache


def to_usd(amount: float | None, currency: str | None) -> float | None:
    if amount is None or not currency:
        return None
    rate = rates().get(currency.upper())
    if not rate:
        return None
    return round(amount / rate, 2)


def refresh() -> bool:
    """Fetch live rates. Returns True when the table was updated."""
    global _cache
    try:
        r = httpx.get("https://open.er-api.com/v6/latest/USD", timeout=config.HTTP_TIMEOUT,
                      headers={"User-Agent": config.USER_AGENT})
        r.raise_for_status()
        data = r.json()
        live = data.get("rates") or {}
        picked = {k: float(live[k]) for k in STATIC_RATES if k in live}
        if not picked:
            return False
        db.set_setting("rates", picked)
        db.set_setting("rates_updated_at", db.utcnow())
        _cache = None
        return True
    except Exception as exc:  # network is optional here
        log.warning("rates refresh failed: %s", exc)
        return False
