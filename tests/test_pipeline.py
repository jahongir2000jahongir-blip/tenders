"""Pipeline tests: de-duplication, updates, status, classification. Run: python -m unittest -v"""
from __future__ import annotations

import os
import tempfile
import unittest

_tmp = tempfile.mkdtemp()
os.environ["TB_DATA_DIR"] = _tmp
os.environ["TB_DB_PATH"] = os.path.join(_tmp, "test.db")

from server import db, pipeline  # noqa: E402
from server.classify import classify  # noqa: E402
from server.scrapers.base import Notice, parse_amount, parse_date  # noqa: E402


def notice(**kw) -> Notice:
    base = dict(source="ua_prozorro", external_id="UA-1", country="UA", title="Капітальний ремонт дороги",
                customer="Департамент", deadline_at="2099-01-10T10:00:00", amount=1000000, currency="UAH")
    base.update(kw)
    return Notice(**base)


class PipelineTests(unittest.TestCase):
    def setUp(self):
        db.init()
        with db.tx() as con:
            con.execute("DELETE FROM tenders"); con.execute("DELETE FROM runs")

    def test_same_notice_twice_is_updated_not_duplicated(self):
        r1 = pipeline.upsert([notice()], "ua_prozorro")
        r2 = pipeline.upsert([notice(title="Капітальний ремонт дороги (уточнено)")], "ua_prozorro")
        self.assertEqual((r1.added, r1.updated), (1, 0))
        self.assertEqual((r2.added, r2.updated), (0, 1))
        self.assertEqual(db.one("SELECT COUNT(*) n FROM tenders")["n"], 1)
        self.assertIn("уточнено", db.one("SELECT title FROM tenders")["title"])

    def test_same_tender_from_other_source_is_skipped(self):
        pipeline.upsert([notice()], "ua_prozorro")
        r = pipeline.upsert([notice(source="ted_cz", external_id="TED-9", title="Капітальний ремонт дороги.")], "ted_cz")
        self.assertEqual((r.added, r.duplicates), (0, 1))
        self.assertEqual(db.one("SELECT COUNT(*) n FROM tenders")["n"], 1)

    def test_different_deadline_is_not_a_duplicate(self):
        pipeline.upsert([notice()], "ua_prozorro")
        r = pipeline.upsert([notice(source="ted_cz", external_id="TED-9", deadline_at="2099-02-01T10:00:00")], "ted_cz")
        self.assertEqual(r.added, 1)

    def test_status_and_usd(self):
        pipeline.upsert([notice(deadline_at="2000-01-01T00:00:00"), notice(external_id="UA-2")], "ua_prozorro")
        rows = {r["external_id"]: r for r in db.rows("SELECT * FROM tenders")}
        self.assertEqual(rows["UA-1"]["status"], "closed")
        self.assertEqual(rows["UA-2"]["status"], "open")
        self.assertGreater(rows["UA-2"]["amount_usd"], 0)
        self.assertEqual(rows["UA-2"]["category"], "construction")

    def test_records_without_id_or_title_are_ignored(self):
        r = pipeline.upsert([notice(title=""), notice(external_id="")], "ua_prozorro")
        self.assertEqual(r.added, 0)

    def test_run_source_records_error_without_raising(self):
        pipeline.COLLECTORS["__broken__"] = lambda: (_ for _ in ()).throw(RuntimeError("boom"))
        try:
            res = pipeline.run_source("__broken__")
        finally:
            del pipeline.COLLECTORS["__broken__"]
        self.assertEqual(res.status, "error")
        self.assertIn("boom", res.error)
        self.assertEqual(db.one("SELECT status FROM runs ORDER BY id DESC")["status"], "error")


class HelperTests(unittest.TestCase):
    def test_parse_date(self):
        self.assertEqual(parse_date("2024-05-01T10:00:00+03:00"), "2024-05-01T07:00:00+00:00")
        self.assertEqual(parse_date("01.05.2024 10:30"), "2024-05-01T10:30:00")
        self.assertEqual(parse_date("2024-05-01"), "2024-05-01T00:00:00")
        self.assertEqual(parse_date("Wed, 01 May 2024 10:00:00 +0300"), "2024-05-01T07:00:00+00:00")
        self.assertEqual(parse_date(1714557600000), "2024-05-01T10:00:00+00:00")
        self.assertIsNone(parse_date(""))

    def test_parse_amount(self):
        self.assertEqual(parse_amount("1 234 567,89 Российский рубль"), 1234567.89)
        self.assertEqual(parse_amount("1,234,567.89"), 1234567.89)
        self.assertEqual(parse_amount("2500000"), 2500000.0)
        self.assertEqual(parse_amount(12.5), 12.5)
        self.assertIsNone(parse_amount("—"))

    def test_classify(self):
        self.assertEqual(classify("Поставка лекарственных препаратов"), "medical")
        self.assertEqual(classify("Dostawa sprzętu komputerowego"), "it")
        self.assertEqual(classify("anything", cpv="45233142-6"), "construction")
        self.assertEqual(classify("Неизвестный предмет"), "other")


if __name__ == "__main__":
    unittest.main()
