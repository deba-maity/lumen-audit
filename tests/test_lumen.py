"""Behavioral tests use only fixtures created beneath this checkout; never real user folders."""
from __future__ import annotations

import copy
import hashlib
import http.client
import json
import os
import stat
import tempfile
import threading
import time
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from lumen import assistant
from lumen.demo import demo_reports
from lumen.export import html_report
from lumen.rules import DAY, MIB, describe_file, findings_for, generated_info
from lumen.scanner import ScanCancelled, scan, unsafe_entry, validate_roots
from lumen.server import App, create_server
from lumen.store import Store, compare

FIXTURES = Path(__file__).resolve().parent.parent / ".qa" / "fixtures"
FIXTURES.mkdir(parents=True, exist_ok=True)


class FixtureCase(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="lumen-test-", dir=FIXTURES)
        self.base = Path(self.temp.name).resolve()
        self.root = self.base / "selected"
        self.root.mkdir()

    def tearDown(self):
        self.temp.cleanup()

    def write(self, name, data=b"fixture"):
        target = self.root / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        return target

    def audit(self, **kwargs):
        return scan([self.root], cancel=threading.Event(), progress=lambda _: None, **kwargs)


class ScannerTests(FixtureCase):
    def test_inventory_does_not_change_contents_names_or_modification_times(self):
        paths = [self.write("readme.md"), self.write("notes/plan.txt", b"important")]
        before = {str(p): (p.read_bytes(), p.stat().st_mtime_ns) for p in paths}
        report = self.audit()
        after = {str(p): (p.read_bytes(), p.stat().st_mtime_ns) for p in paths}
        self.assertEqual(before, after)
        self.assertEqual(set(before), {item["path"] for item in report["files"]})
        self.assertFalse(report["coverage"]["hashing"])
        self.assertTrue(all(item["last_opened"] is None for item in report["files"]))

    def test_metadata_scan_never_opens_file_contents(self):
        self.write("private.txt", b"not for a model")
        with patch("lumen.scanner.os.open", side_effect=AssertionError("File content was opened")):
            report = self.audit()
        self.assertEqual(report["summary"]["files"], 1)

    def test_duplicates_require_full_hash_and_same_size_is_not_enough(self):
        self.write("one.txt", b"same content")
        self.write("two.txt", b"same content")
        self.write("different.txt", b"other string")
        report = self.audit(hash_duplicates=True)
        self.assertEqual(len(report["duplicates"]), 1)
        group = report["duplicates"][0]
        self.assertEqual(group["hash"], hashlib.sha256(b"same content").hexdigest())
        self.assertEqual(group["potential_bytes"], len(b"same content"))
        self.assertEqual(len(group["files"]), 2)

    def test_hard_links_are_not_duplicate_savings(self):
        original = self.write("one.txt", b"same content")
        try:
            os.link(original, self.root / "hardlink.txt")
        except OSError:
            self.skipTest("Hard links unsupported on this test filesystem")
        report = self.audit(hash_duplicates=True)
        self.assertEqual(len(report["files"]), 1)
        self.assertEqual(report["duplicates"], [])
        self.assertEqual(report["coverage"]["skipped"], 1)

    def test_protected_and_sensitive_items_are_skipped(self):
        for name in (".ssh/id_ed25519", ".git/config", "Windows/data", ".env", ".env.production", "ok.txt"):
            self.write(name)
        report = self.audit()
        self.assertEqual([file["name"] for file in report["files"]], ["ok.txt"])
        self.assertEqual(report["coverage"]["skipped"], 5)

    def test_cloud_and_reparse_attributes_are_excluded(self):
        for attribute in (0x1000, 0x40000, 0x400000, 0x400):
            info = SimpleNamespace(st_mode=stat.S_IFREG, st_file_attributes=attribute)
            self.assertIsNotNone(unsafe_entry(Path("placeholder"), info))

    def test_links_are_rejected_without_creating_privileged_links(self):
        info = SimpleNamespace(st_mode=stat.S_IFLNK, st_file_attributes=0)
        self.assertIn("not followed", unsafe_entry(Path("link"), info))

    def test_overlap_roots_are_deduplicated(self):
        nested = self.root / "nested"
        nested.mkdir()
        self.assertEqual(validate_roots([str(nested), str(self.root)]), [self.root])
        self.assertEqual(validate_roots([str(self.root), str(nested)]), [self.root])

    def test_invalid_network_and_relative_roots_rejected(self):
        for roots in (None, [], ["relative/path"], [r"\\server\share"], ["//server/share"], [123], [str(self.root)] * 9):
            with self.subTest(roots=roots), self.assertRaises((ValueError, OSError)):
                validate_roots(roots)

    def test_app_state_is_excluded(self):
        state = self.root / "state"
        state.mkdir()
        (state / "snapshots.sqlite3").write_bytes(b"private inventory")
        self.write("keep.txt")
        report = self.audit(excluded=state)
        self.assertEqual([file["name"] for file in report["files"]], ["keep.txt"])
        with self.assertRaises(ValueError):
            validate_roots([str(state)], excluded=state)

    def test_scan_limit_reports_partial_coverage(self):
        for index in range(5):
            self.write(f"{index}.txt")
        report = self.audit(max_files=2)
        self.assertEqual(len(report["files"]), 2)
        self.assertTrue(report["coverage"]["limited"])
        self.assertTrue(report["warnings"])

    def test_cancellation_stops_scan(self):
        cancel = threading.Event()
        cancel.set()
        with self.assertRaises(ScanCancelled):
            scan([self.root], cancel=cancel, progress=lambda _: None)

    def test_hash_budget_is_enforced(self):
        self.write("one.txt", b"same content")
        self.write("two.txt", b"same content")
        report = self.audit(hash_duplicates=True, hash_budget=12)
        self.assertLessEqual(report["coverage"]["hashed_bytes"], 12)
        self.assertEqual(report["duplicates"], [])
        self.assertTrue(report["coverage"]["hash_skipped"])

    def test_generated_root_and_nested_generated_folders(self):
        root = self.root / "node_modules"
        path = root / "package" / "module.js"
        self.assertEqual(generated_info(path, root), (str(root), "node_modules"))
        nested = self.root / "project" / ".next" / "cache" / "chunk"
        self.assertEqual(generated_info(nested, self.root), (str(self.root / "project" / ".next"), ".next"))

    def test_review_space_does_not_double_count_duplicates_in_generated_folders(self):
        self.write("project/node_modules/a.bin", b"x" * (2 * MIB))
        self.write("copy.bin", b"x" * (2 * MIB))
        self.write("project/node_modules/b.bin", b"y" * MIB)
        report = self.audit(hash_duplicates=True)
        self.assertEqual(report["summary"]["review_bytes"], 3 * MIB)
        self.assertEqual(report["summary"]["duplicate_bytes"], 2 * MIB)

    def test_file_change_during_hash_is_not_a_duplicate(self):
        target = self.write("one.txt", b"identical")
        self.write("two.txt", b"identical")
        original = os.open
        def change_before_open(path, flags):
            if Path(path) == target:
                target.write_bytes(b"changed!!")
            return original(path, flags)
        with patch("lumen.scanner.os.open", side_effect=change_before_open):
            report = self.audit(hash_duplicates=True)
        self.assertEqual(report["duplicates"], [])


class EvidenceTests(unittest.TestCase):
    def setUp(self):
        self.current, self.previous = demo_reports()

    def test_demo_has_no_filesystem_reads(self):
        with patch("os.scandir", side_effect=AssertionError("Host scan")):
            current, _ = demo_reports()
        self.assertTrue(current["demo"])
        self.assertGreater(len(current["findings"]), 5)

    def test_age_does_not_mean_unused(self):
        file = copy.deepcopy(self.current["files"][0])
        file.update(path="/fixture/old-notes.txt", size=123, modified=time.time() - 1000 * DAY, generated=None)
        self.assertEqual(findings_for([file], [], time.time()), [])

    def test_out_of_range_file_dates_do_not_abort_analysis(self):
        file = copy.deepcopy(self.current["files"][0])
        file.update(path="/fixture/setup.msi", size=20 * MIB, modified=-1e20, generated=None)
        findings = findings_for([file], [], time.time())
        self.assertEqual(len(findings), 1)
        self.assertTrue(any("Outside the supported" in value for value in findings[0]["evidence"]))

    def test_important_project_metadata_is_explained_as_non_cache(self):
        file = {"path": "/fixture/package-lock.json", "category": "Development", "generated": None}
        self.assertIn("not a disposable cache", describe_file(file)["purpose"])

    def test_change_comparison_reports_new_missing_and_growing_files(self):
        result = compare(self.previous, self.current)
        self.assertEqual(result["added"], 2)
        self.assertEqual(result["removed"], 1)
        self.assertEqual(result["changed"], 1)
        self.assertGreater(result["delta"], 0)
        self.assertTrue(result["partial"])

    def test_comparison_rejects_unrelated_scopes(self):
        self.previous["roots"] = ["unrelated"]
        with self.assertRaises(ValueError):
            compare(self.previous, self.current)

    def test_export_escapes_untrusted_paths_and_titles(self):
        self.current["findings"][0]["title"] = '<script>alert("bad")</script>'
        self.current["findings"][0]["paths"] = ['<img src=x onerror="alert(1)">']
        exported = html_report(self.current)
        self.assertNotIn("<script>", exported)
        self.assertNotIn("<img src=x", exported)
        self.assertIn("&lt;script&gt;", exported)
        self.assertIn("Fictional demo report", exported)

    def test_evidence_guide_does_not_call_model(self):
        with patch.object(assistant, "ollama_request", side_effect=AssertionError("Unexpected AI call")):
            result = assistant.answer(self.current, "What should I review first?")
        self.assertEqual(result["source"], "evidence")
        self.assertTrue(result["references"])

    def test_last_opened_is_explicitly_unknown(self):
        result = assistant.answer(self.current, "When was this last opened?")
        self.assertIn("cannot establish", result["answer"])

    def test_local_ai_masks_roots_and_filters_fake_references(self):
        captured = {}
        valid_id = self.current["findings"][0]["id"]
        def response(path, data=None, timeout=4):
            if path == "/api/tags":
                return {"models": [{"name": "local-test"}]}
            if path == "/api/show":
                return {"details": {"format": "gguf"}}
            captured.update(data)
            return {"message": {"content": json.dumps({"answer": "Review the linked evidence.", "references": [valid_id, "invented", {"bad": "reference"}]})}}
        with patch.object(assistant, "ollama_request", side_effect=response):
            result = assistant.answer(self.current, "What is in C:/Users/Alex?", "local-test")
        self.assertEqual(result["references"], [valid_id])
        self.assertNotIn("C:/Users/Alex", json.dumps(captured))
        self.assertNotIn("tools", captured)
        self.assertEqual(result["source"], "ollama")

    def test_cloud_alias_cannot_be_used(self):
        def response(path, data=None, timeout=4):
            return {"models": [{"name": "innocent-alias"}]} if path == "/api/tags" else {"remote_model": "cloud-model", "remote_host": "https://remote.example"}
        with patch.object(assistant, "ollama_request", side_effect=response), self.assertRaises(ValueError):
            assistant.answer(self.current, "Explain", "innocent-alias")

    def test_model_catalog_excludes_cloud_models(self):
        catalog = {"models": [{"name": "safe"}, {"name": "big:cloud"}, {"name": "alias", "remote_model": "remote"}]}
        with patch.object(assistant, "ollama_request", return_value=catalog):
            self.assertEqual(assistant.models()["models"], ["safe"])


class StoreTests(FixtureCase):
    def test_store_is_lazy_and_roundtrips_report(self):
        store = Store(self.base / "state")
        self.assertEqual(store.list(), [])
        self.assertFalse(store.directory.exists())
        report = demo_reports()[0]
        store.save(report)
        self.assertEqual(store.get(report["id"]), report)
        self.assertEqual(store.list()[0]["summary"], report["summary"])
        self.assertEqual(list(self.root.iterdir()), [])


class ServerFixtureCase(FixtureCase):
    def setUp(self):
        super().setUp()
        self.server = create_server(0, self.base / "state", demo_only=True)
        self.thread = threading.Thread(target=self.server.serve_forever, kwargs={"poll_interval": .02}, daemon=True)
        self.thread.start()

    def tearDown(self):
        self.server.app.cancel.set()
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(2)
        super().tearDown()

    def request(self, method, path, body=None, token=True, extra=None):
        conn = http.client.HTTPConnection("127.0.0.1", self.server.server_port, timeout=10)
        headers = {"Content-Type": "application/json"}
        if token:
            headers["X-Lumen-Token"] = self.server.app.token
        headers.update(extra or {})
        conn.request(method, path, json.dumps(body) if body is not None else None, headers)
        response = conn.getresponse()
        status, data, response_headers = response.status, response.read(), dict(response.getheaders())
        conn.close()
        return status, data, response_headers

class ServerTests(ServerFixtureCase):
    def test_bootstrap_and_demo_are_available_without_scanning(self):
        with patch("lumen.server.validate_roots", side_effect=AssertionError("Host scan")):
            status, data, _ = self.request("GET", "/api/bootstrap", token=False)
            self.assertEqual(status, 200)
            self.assertTrue(json.loads(data)["demo_only"])
            status, data, _ = self.request("GET", "/api/reports/demo-current")
            self.assertEqual(status, 200)
            self.assertTrue(json.loads(data)["demo"])
        self.assertFalse(self.server.app.store.directory.exists())

    def test_demo_mode_blocks_scan_before_validating_paths(self):
        with patch("lumen.server.validate_roots", side_effect=AssertionError("Unexpected path inspection")):
            status, _, _ = self.request("POST", "/api/scan", {"roots": [str(self.root)]})
        self.assertEqual(status, 403)

    def test_token_origin_and_host_protection(self):
        self.assertEqual(self.request("GET", "/api/history", token=False)[0], 403)
        self.assertEqual(self.request("POST", "/api/scan", {}, token=False)[0], 403)
        self.assertEqual(self.request("GET", "/api/bootstrap", extra={"Origin": "https://evil.example"})[0], 403)
        self.assertEqual(self.request("GET", "/api/bootstrap", extra={"Host": "evil.example"})[0], 403)
        self.assertEqual(self.request("GET", "/api/bootstrap", extra={"Sec-Fetch-Site": "cross-site"})[0], 403)

    def test_export_is_downloadable_and_has_no_external_assets(self):
        status, data, headers = self.request("GET", "/api/reports/demo-current.html")
        self.assertEqual(status, 200)
        self.assertIn("attachment", headers["Content-Disposition"])
        self.assertNotIn(b"<script", data)
        self.assertNotIn(b"https://", data)

    def test_static_paths_cannot_traverse_to_source(self):
        self.assertEqual(self.request("GET", "/../lumen/server.py")[0], 404)
        self.assertEqual(self.request("GET", "/lumen/server.py")[0], 404)

    def test_scan_worker_saves_only_fixture_inventory(self):
        self.server.app.demo_only = False
        self.write("one.txt", b"sample")
        self.write("two.txt", b"sample")
        status, _, _ = self.request("POST", "/api/scan", {"roots": [str(self.root)], "hash_duplicates": True})
        self.assertEqual(status, 202)
        for _ in range(100):
            status, data, _ = self.request("GET", "/api/scan")
            result = json.loads(data)
            if result["status"] != "running":
                break
            time.sleep(.01)
        self.assertEqual(result["status"], "complete", result)
        report = self.server.app.report(result["report_id"])
        self.assertFalse(report["demo"])
        self.assertEqual(report["summary"]["files"], 2)
        self.assertEqual(len(report["duplicates"]), 1)
        self.assertEqual(len(list(self.root.iterdir())), 2)

    def test_ask_rejects_malformed_input(self):
        self.assertEqual(self.request("POST", "/api/ask", {"question": []})[0], 400)
        self.assertEqual(self.request("POST", "/api/ask", {"question": "a" * 2001})[0], 400)

    def test_ask_evidence_endpoint_and_compare(self):
        status, data, _ = self.request("POST", "/api/ask", {"question": "Explain duplicate files", "report_id": "demo-current"})
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(data)["result"]["source"], "evidence")
        self.assertEqual(self.request("GET", "/api/compare?before=demo-previous&after=demo-current")[0], 200)


if __name__ == "__main__":
    unittest.main()
