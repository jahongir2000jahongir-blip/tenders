"""Demo tenders for previewing the catalogue before the collectors have run.

Every record has source='demo' and is removed with `python -m server.collect --purge-demo`
or from the admin panel. Titles are realistic but the notices are not real.
"""
from __future__ import annotations

import random
from datetime import datetime, timedelta, timezone

from . import db
from .countries import COUNTRIES
from .pipeline import upsert
from .scrapers.base import Notice

_TITLES = {
    "construction": ["Капитальный ремонт здания школы №{n}", "Реконструкция участка автодороги {n} км", "Строительство детского сада на {n} мест", "Благоустройство дворовых территорий, {n} объектов"],
    "medical": ["Поставка лекарственных препаратов для больницы №{n}", "Поставка медицинского оборудования: УЗИ-аппараты, {n} шт.", "Расходные материалы для отделения реанимации"],
    "it": ["Поставка серверного оборудования и систем хранения данных", "Разработка информационной системы электронного документооборота", "Поставка {n} ноутбуков и лицензий ПО"],
    "energy": ["Модернизация трансформаторной подстанции {n} кВ", "Поставка светодиодных светильников уличного освещения, {n} шт.", "Ремонт тепловых сетей, {n} м"],
    "transport": ["Поставка {n} автобусов средней вместимости", "Услуги по перевозке грузов", "Поставка дизельного топлива, {n} т"],
    "food": ["Поставка продуктов питания для школьных столовых", "Организация горячего питания, {n} учреждений"],
    "education": ["Поставка школьной мебели: {n} комплектов", "Поставка учебников для начальных классов"],
    "security": ["Услуги по охране объектов, {n} постов", "Монтаж системы видеонаблюдения и пожарной сигнализации"],
    "equipment": ["Поставка строительной техники: экскаватор-погрузчик", "Поставка оборудования для пищевого производства"],
    "services": ["Услуги по уборке помещений, {n} м²", "Аудит финансовой отчётности за {n} год"],
    "agro": ["Поставка минеральных удобрений, {n} т", "Поставка семян озимой пшеницы"],
}
_CUSTOMERS = ["Управление капитального строительства", "Городская клиническая больница", "Министерство образования", "Департамент транспорта", "Государственное предприятие «Водоканал»", "Акимат района", "Хукумат города", "Хокимият района", "Urząd Miasta", "Krajský úřad", "Landkreis", "Savivaldybės administracija", "Районная администрация", "Primăria municipiului", "Icra Hakimiyyəti"]
_METHODS = ["Открытый конкурс", "Запрос ценовых предложений", "Аукцион", "Открытые торги"]
_REGIONS = {"TJ": ["Душанбе", "Худжанд", "Бохтар"], "UZ": ["Ташкент", "Самарканд", "Бухара"], "KG": ["Бишкек", "Ош"], "KZ": ["Астана", "Алматы", "Шымкент"],
            "TM": ["Ашхабад", "Туркменабат"], "AF": ["Кабул", "Герат"], "RU": ["Москва", "Казань", "Новосибирск"], "BY": ["Минск", "Гомель"],
            "UA": ["Киев", "Львов", "Одесса"], "MD": ["Кишинёв", "Бельцы"], "AZ": ["Баку", "Гянджа"], "PL": ["Warszawa", "Kraków", "Gdańsk"],
            "CZ": ["Praha", "Brno"], "DE": ["Berlin", "München", "Hamburg"], "LT": ["Vilnius", "Kaunas"]}
_RATES = {"TJS": 10.9, "UZS": 12700, "KGS": 87, "KZT": 480, "TMT": 3.5, "AFN": 71, "RUB": 92, "BYN": 3.27, "UAH": 41, "MDL": 17.7, "AZN": 1.7, "PLN": 3.95, "CZK": 23.2, "EUR": 0.92}


def seed(per_country: int = 6) -> int:
    rnd = random.Random(42)
    now = datetime.now(timezone.utc)
    notices: list[Notice] = []
    i = 0
    for code, meta in COUNTRIES.items():
        for _ in range(per_country):
            i += 1
            cat = rnd.choice(list(_TITLES))
            title = rnd.choice(_TITLES[cat]).format(n=rnd.choice([3, 5, 12, 24, 40, 110, 250]))
            usd = rnd.choice([12_000, 48_000, 95_000, 240_000, 610_000, 1_400_000, 3_800_000])
            cur = meta["currency"]
            published = now - timedelta(days=rnd.randint(0, 12), hours=rnd.randint(0, 20))
            deadline = published + timedelta(days=rnd.randint(5, 35))
            notices.append(Notice(
                source="demo", external_id=f"demo-{code}-{i}", country=code, title=title,
                url=None, description="Демонстрационная запись: показывает, как выглядит карточка тендера. Реальные объявления появятся после первого запуска сборщика.",
                customer=rnd.choice(_CUSTOMERS), region=rnd.choice(_REGIONS[code]), method=rnd.choice(_METHODS),
                amount=round(usd * _RATES.get(cur, 1), -2), currency=cur,
                published_at=published.replace(microsecond=0).isoformat(), deadline_at=deadline.replace(microsecond=0).isoformat(),
                lang="ru", raw={"demo": True},
            ))
    res = upsert(notices, "demo")
    return res.added


def purge() -> int:
    with db.tx() as con:
        return con.execute("DELETE FROM tenders WHERE source='demo'").rowcount
