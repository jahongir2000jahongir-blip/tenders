"""Parser tests against recorded payload shapes of each portal. Run: python -m unittest -v"""
from __future__ import annotations

import unittest

from server.scrapers import by_icetrade, kz_goszakup, md_mtender, pl_bzp, ru_zakupki, ted, tj_zakupki, ua_prozorro, ungm
from server.scrapers.generic_json import find_list, map_generic

RU_RSS = """<?xml version="1.0" encoding="UTF-8"?><rss version="2.0"><channel><title>Закупки</title>
<item><title>№ 0373100001224000101 Поставка канцелярских товаров</title>
<link>https://zakupki.gov.ru/epz/order/notice/ea20/view/common-info.html?regNumber=0373100001224000101</link>
<description><![CDATA[<strong>Наименование объекта закупки:</strong> Поставка канцелярских товаров<br/><strong>Заказчик:</strong> ФГБУ &quot;Центр&quot;<br/><strong>Начальная цена:</strong> 1 250 000,00 Российский рубль<br/><strong>Размещено:</strong> 20.09.2026<br/><strong>Окончание подачи заявок:</strong> 30.09.2026 09:00]]></description>
<pubDate>Sat, 20 Sep 2026 08:00:00 +0300</pubDate></item></channel></rss>"""


class RuTests(unittest.TestCase):
    def test_rss(self):
        n = ru_zakupki.parse_feed(RU_RSS)[0]
        self.assertEqual(n.external_id, "0373100001224000101")
        self.assertEqual(n.title, "Поставка канцелярских товаров")
        self.assertEqual(n.customer, 'ФГБУ "Центр"')
        self.assertEqual(n.amount, 1250000.0)
        self.assertEqual(n.currency, "RUB")
        self.assertEqual(n.deadline_at, "2026-09-30T09:00:00")
        self.assertEqual(n.published_at, "2026-09-20T00:00:00")


class ProzorroTests(unittest.TestCase):
    def test_map(self):
        t = {"id": "abc", "tenderID": "UA-2026-09-20-000001-a", "status": "active.tendering", "title": "Ремонт покрівлі",
             "procuringEntity": {"name": "Школа №5", "address": {"region": "Львівська область"}},
             "value": {"amount": 850000.5, "currency": "UAH"}, "tenderPeriod": {"startDate": "2026-09-20T10:00:00+03:00", "endDate": "2026-10-05T12:00:00+03:00"},
             "procurementMethodType": "aboveThresholdUA", "items": [{"classification": {"id": "45260000-7"}}]}
        n = ua_prozorro.map_item(t)
        self.assertEqual(n.external_id, "UA-2026-09-20-000001-a")
        self.assertEqual(n.customer, "Школа №5")
        self.assertEqual(n.cpv, "45260000-7")
        self.assertEqual(n.deadline_at, "2026-10-05T09:00:00+00:00")
        self.assertEqual(n.method, "Открытые торги")
        self.assertIsNone(ua_prozorro.map_item({**t, "status": "complete"}))


class BzpTests(unittest.TestCase):
    def test_map(self):
        n = pl_bzp.map_item({"objectId": "9a1", "noticeNumber": "2026/BZP 00012345/01", "orderObject": "Dostawa mebli szkolnych",
                             "organizationName": "Gmina Kraków", "organizationCity": "Kraków", "organizationProvince": "małopolskie",
                             "publicationDate": "2026-09-20T09:12:00", "submittingOffersDate": "2026-10-01T10:00:00", "cpvCode": "39160000-1"})
        self.assertEqual(n.external_id, "9a1")
        self.assertEqual(n.region, "Kraków, małopolskie")
        self.assertEqual(n.cpv, "39160000-1")
        self.assertTrue(n.url.endswith("/9a1"))


class TedTests(unittest.TestCase):
    def test_multilingual(self):
        n = ted.map_item({"publication-number": "555-2026", "notice-title": {"ces": "Oprava mostu", "eng": "Bridge repair"},
                          "buyer-name": {"eng": ["City of Brno"]}, "publication-date": "2026-09-20+02:00",
                          "deadline-receipt-tender-date-lot": ["2026-10-20+02:00"], "estimated-value-lot": ["1200000"],
                          "estimated-value-cur-lot": ["CZK"], "classification-cpv": ["45221100"],
                          "links": {"html": {"ENG": "https://ted.europa.eu/en/notice/555-2026"}}}, "CZ")
        self.assertEqual(n.title, "Oprava mostu")
        self.assertEqual(n.customer, "City of Brno")
        self.assertEqual(n.amount, 1200000.0)
        self.assertEqual(n.currency, "CZK")
        self.assertEqual(n.source, "ted_cz")
        self.assertEqual(n.deadline_at, "2026-10-20T00:00:00")
        self.assertEqual(n.url, "https://ted.europa.eu/en/notice/555-2026")


class MtenderTests(unittest.TestCase):
    def test_release(self):
        n = md_mtender.map_release("ocds-b3wdp1-MD-1", {"tender": {"title": "Achiziția de medicamente", "value": {"amount": 500000, "currency": "MDL"},
                                                          "tenderPeriod": {"endDate": "2026-10-10T09:00:00Z"}, "classification": {"id": "33600000-6"}},
                                                        "buyer": {"name": "IMSP Spitalul"}})
        self.assertEqual(n.customer, "IMSP Spitalul")
        self.assertEqual(n.deadline_at, "2026-10-10T09:00:00+00:00")
        self.assertEqual(n.cpv, "33600000-6")


class HtmlTests(unittest.TestCase):
    def test_kz_search_table(self):
        html = """<table><tr><td><a href="/ru/announce/index/12345">12345-1</a></td><td>Поставка угля</td><td>КГУ Школа</td>
        <td>Запрос ценовых предложений</td><td>Опубликовано</td><td>2026-09-20 10:00:00</td><td>2026-09-27 10:00:00</td><td>4 500 000</td></tr></table>"""
        n = kz_goszakup.parse_search_html(html)[0]
        self.assertEqual(n.external_id, "12345")
        self.assertEqual(n.title, "Поставка угля")
        self.assertEqual(n.customer, "КГУ Школа")
        self.assertEqual(n.amount, 4500000.0)
        self.assertEqual(n.deadline_at, "2026-09-27T10:00:00")

    def test_icetrade(self):
        html = """<table><tr><td>1</td><td><a href="/tenders/view/998877">Закупка мебели для офиса</a></td><td>ОАО Белшина</td>
        <td>20.09.2026</td><td>30.09.2026 12:00</td><td>150 000 BYN</td></tr></table>"""
        n = by_icetrade.parse_list(html)[0]
        self.assertEqual(n.external_id, "998877")
        self.assertEqual(n.customer, "ОАО Белшина")
        self.assertEqual(n.amount, 150000.0)
        self.assertEqual(n.published_at, "2026-09-20T00:00:00")
        self.assertEqual(n.deadline_at, "2026-09-30T12:00:00")

    def test_tj(self):
        html = """<ul><li><a href="/index.php/ru/tenders/view/4521">Строительство школы в Вахдате</a> Заказчик: Хукумат города
        20.09.2026 — 10.10.2026 1 200 000 сомони</li></ul>"""
        n = tj_zakupki.parse_list(html)[0]
        self.assertEqual(n.external_id, "4521")
        self.assertEqual(n.currency, "TJS")
        self.assertEqual(n.deadline_at, "2026-10-10T00:00:00")

    def test_ungm(self):
        html = """<div class="tableRow dataRow" data-noticeid="77001"><div class="tableCell resultTitle">Supply of solar kits</div>
        <div class="tableCell resultDeadline">30-Sep-2026 12:00</div><div class="tableCell resultAgency">UNDP</div>
        <div class="tableCell resultType">RFQ</div><div class="tableCell resultReference">UNDP-TKM-00123</div>
        <div class="tableCell resultCountry">Turkmenistan</div><div class="tableCell resultPublished">20-Sep-2026</div></div>
        <div class="tableRow dataRow" data-noticeid="77002"><div class="tableCell resultTitle">Other</div><div class="tableCell resultCountry">Kenya</div></div>"""
        ns = ungm.parse_rows(html, "TM")
        self.assertEqual(len(ns), 1)
        self.assertEqual(ns[0].customer, "UNDP")
        self.assertEqual(ns[0].source, "ungm_tm")


class GenericTests(unittest.TestCase):
    def test_find_list_and_map(self):
        payload = {"success": True, "data": {"items": [{"id": 5, "name": "Поставка компьютеров", "customerName": "Хокимият", "startPrice": "150000000", "endDate": "2026-10-01T00:00:00"}]}}
        items = find_list(payload)
        self.assertEqual(len(items), 1)
        n = map_generic(items[0], "uz_xarid", "UZ", "UZS", "https://x/{id}")
        self.assertEqual(n.external_id, "5")
        self.assertEqual(n.amount, 150000000.0)
        self.assertEqual(n.currency, "UZS")
        self.assertEqual(n.url, "https://x/5")


if __name__ == "__main__":
    unittest.main()
