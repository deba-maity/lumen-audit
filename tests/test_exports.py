import csv
import io
import unittest

import test_lumen as base
from lumen.export import csv_inventory, html_report


class InventoryExportTests(unittest.TestCase):
    def setUp(self):
        self.report = base.demo_reports()[0]

    def records(self):
        return list(csv.DictReader(io.StringIO(csv_inventory(self.report).lstrip("\ufeff"))))

    def test_csv_includes_every_file_and_exact_totals(self):
        records = self.records()
        self.assertEqual(len(records), self.report["summary"]["files"])
        self.assertEqual(sum(int(row["Logical bytes"]) for row in records), self.report["summary"]["bytes"])
        self.assertTrue(all(row["Last human-opened"] == "Unknown" for row in records))
        self.assertTrue(any(row["Raw access timestamp (UTC)"] == "Unknown" for row in records))
        self.assertTrue(any(row["Finding IDs"] for row in records))

    def test_csv_roundtrips_quotes_newlines_and_international_names(self):
        name = 'caf\u00e9, "notes"\n\u65e5\u672c\u8a9e.txt'
        self.report["files"][0]["name"] = name
        self.assertEqual(self.records()[0]["Name"], name)

    def test_inventory_text_cannot_become_a_spreadsheet_formula(self):
        for value in ('=1+1', '+SUM(1,2)', '-2+3', '@SUM(1,2)', ' \t=1+1', '\n=1+1'):
            with self.subTest(value=value):
                self.report["files"][0]["name"] = value
                self.report["files"][0]["purpose"] = value
                record = self.records()[0]
                self.assertEqual(record["Name"], "'" + value)
                self.assertEqual(record["Likely purpose"], "'" + value)

    def test_readable_report_keeps_label_and_locations_visible(self):
        self.report["name"] = 'Before <cleanup>'
        exported = html_report(self.report)
        self.assertIn('Before &lt;cleanup&gt;', exported)
        self.assertEqual(exported.count('<details open>'), len(self.report["findings"]))


class ExportEndpointTests(base.ServerFixtureCase):
    def test_csv_download_content_type_and_unicode_encoding(self):
        status, body, headers = self.request("GET", "/api/reports/demo-current.csv")
        self.assertEqual(status, 200)
        self.assertTrue(body.startswith(b"\xef\xbb\xbf"))
        self.assertEqual(headers["Content-Type"], "text/csv; charset=utf-8")
        self.assertIn("attachment", headers["Content-Disposition"])
        rows = list(csv.DictReader(io.StringIO(body.decode("utf-8-sig"))))
        self.assertEqual(len(rows), self.server.app.demos["demo-current"]["summary"]["files"])
