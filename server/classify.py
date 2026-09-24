"""Sector classification from CPV codes and title keywords (RU / EN / UK / PL / CS / DE)."""
from __future__ import annotations

import re

CATEGORIES: dict[str, dict[str, str]] = {
    "construction": {"ru": "Строительство и ремонт", "en": "Construction and repair"},
    "medical": {"ru": "Медицина и фармацевтика", "en": "Medical and pharma"},
    "it": {"ru": "ИТ и связь", "en": "IT and telecom"},
    "energy": {"ru": "Энергетика и ЖКХ", "en": "Energy and utilities"},
    "transport": {"ru": "Транспорт и логистика", "en": "Transport and logistics"},
    "food": {"ru": "Продукты питания", "en": "Food"},
    "education": {"ru": "Образование и культура", "en": "Education and culture"},
    "security": {"ru": "Безопасность и охрана", "en": "Security"},
    "equipment": {"ru": "Оборудование и техника", "en": "Equipment and machinery"},
    "services": {"ru": "Услуги и консалтинг", "en": "Services and consulting"},
    "agro": {"ru": "Сельское хозяйство", "en": "Agriculture"},
    "other": {"ru": "Прочее", "en": "Other"},
}

# CPV division (first two digits) -> category
_CPV: dict[str, str] = {
    "45": "construction", "44": "construction", "71": "construction",
    "33": "medical", "85": "medical",
    "30": "it", "48": "it", "72": "it", "32": "it", "64": "it",
    "09": "energy", "31": "energy", "65": "energy", "90": "energy",
    "34": "transport", "60": "transport", "63": "transport",
    "15": "food", "55": "food",
    "22": "education", "39": "equipment", "80": "education", "92": "education",
    "35": "security", "79": "services", "98": "services", "75": "services", "73": "services", "66": "services",
    "16": "agro", "03": "agro", "77": "agro",
    "42": "equipment", "43": "equipment", "38": "equipment", "37": "equipment", "18": "equipment", "19": "equipment",
}

_KEYWORDS: list[tuple[str, str]] = [
    ("construction", r"строител|ремонт|реконструк|капитальн|дорог|асфальт|благоустрой|будівниц|ремонт|budow|remont|stavb|rekonstruk|bau|sanierung|road|construct|renovat|repair"),
    ("medical", r"медиц|лекарств|препарат|фармац|больниц|поликлин|медич|ліки|szpital|lek[iy]|medyc|zdravot|léč|nemocnic|medizin|arznei|klinik|medical|pharma|hospital|drug|vaccin|diagnost"),
    ("it", r"программн|ит-|компьютер|сервер|лицензи|информацион|связи|интернет|телеком|програмн|komputer|oprogramowan|informatyc|software|počítač|it-|telekom|server|licen[cz]|network|сеть|ноутбук|laptop"),
    ("energy", r"электро|энерг|теплов|котель|газ|водоснаб|канализ|отоплен|енерг|electric|energy|energ|prąd|ciepł|wodoci|teplo|elektr|strom|wasser|heating|water supply|utility"),
    ("transport", r"транспорт|автомоб|перевоз|логист|автобус|грузов|запчаст|шин|топлив|бензин|дизел|transport|vehicle|bus|truck|fuel|logist|pojazd|paliw|vozidl|fahrzeug|kraftstoff"),
    ("food", r"продукт|питани|продовольств|мясо|молок|хлеб|овощ|харч|żywno|posił|potravin|straven|lebensmittel|verpfleg|food|catering|meal"),
    ("education", r"учебн|образован|школ|детск|учебник|книг|мебель|культур|освіт|szkol|edukac|podręcznik|škol|vzděl|schule|bildung|school|education|textbook|furniture|мебл"),
    ("security", r"охран|безопас|видеонаблюд|пожарн|сигнализ|охорон|ochron|bezpiecz|monitoring|ostraha|požár|sicherheit|brandschutz|security|surveillance|fire"),
    ("agro", r"сельск|аграр|удобрен|семен|скот|зерн|сільськ|rolnic|nawoz|zemědě|hnojiv|landwirt|agric|fertil|seed|livestock"),
    ("equipment", r"оборудован|станк|техник|прибор|инструмент|обладнан|urządzen|sprzęt|maszyn|zařízen|stroj|ausrüst|maschine|equipment|machin|device|instrument"),
    ("services", r"услуг|консульт|аудит|обслуживан|уборк|аренд|страхов|послуг|usług|doradz|sprzątan|služb|poraden|úklid|dienstleist|beratung|service|consult|cleaning|insurance|maintenance"),
]
_COMPILED = [(cat, re.compile(rx, re.IGNORECASE)) for cat, rx in _KEYWORDS]


def from_cpv(cpv: str | None) -> str | None:
    if not cpv:
        return None
    digits = re.sub(r"\D", "", str(cpv))[:2]
    return _CPV.get(digits)


def classify(title: str | None, description: str | None = None, cpv: str | None = None) -> str:
    cat = from_cpv(cpv)
    if cat:
        return cat
    text = f"{title or ''} {description or ''}"[:2000]
    for cat, rx in _COMPILED:
        if rx.search(text):
            return cat
    return "other"
