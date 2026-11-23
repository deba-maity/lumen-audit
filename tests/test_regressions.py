"""Regression cases from the extended reliability review."""
import json
import os
from pathlib import Path
from types import SimpleNamespace
import stat
import threading
import time
from unittest.mock import patch

import test_lumen as base
from lumen import assistant
from lumen.server import App
from lumen.store import compare
from lumen.scanner import unsafe_entry, validate_roots


class ScannerRegressions(base.FixtureCase):
    def test_quoted_copy_as_path_is_accepted(self):
        self.assertEqual(validate_roots(['"' + str(self.root) + '"']), [self.root])

    @base.unittest.skipUnless(os.name == "nt", "Windows root-folder convention")
    def test_windows_dev_folder_is_not_unix_device_directory(self):
        info = SimpleNamespace(st_mode=stat.S_IFDIR, st_file_attributes=0)
        self.assertIsNone(unsafe_entry(Path("C:/dev"), info))
    def test_project_lib_and_bin_are_not_system_directories(self):
        self.write("project/.venv/Lib/package/module.py")
        self.write("project/node_modules/tool/bin/tool.js")
        self.write("project/dev/notes.md")
        report = self.audit()
        self.assertEqual(len(report["files"]), 3)

    def test_reversed_comparison_rejected(self):
        current, previous = base.demo_reports()
        with self.assertRaises(ValueError):
            compare(current, previous)


class ServerRegressions(base.ServerFixtureCase):
    def test_snapshot_label_validation(self):
        self.server.app.demo_only = False
        for label in ([], "x" * 81):
            status,_,_=self.request("POST","/api/scan",{"roots":[str(self.root)],"name":label})
            self.assertEqual(status,400)
    def test_demo_mode_never_reads_saved_real_data(self):
        with patch.object(self.server.app.store, "list", side_effect=AssertionError("Read real history")):
            self.assertEqual(self.request("GET", "/api/history")[0], 200)
        with patch.object(self.server.app.store, "get", side_effect=AssertionError("Read real snapshot")):
            self.assertEqual(self.request("GET", "/api/reports/real-snapshot")[0], 404)

    def test_unicode_session_token_rejected_cleanly(self):
        self.assertEqual(self.request("GET", "/api/history", extra={"X-Lumen-Token": "caf\u00e9"})[0], 403)

    def test_unknown_finding_is_not_silently_replaced_by_generic_advice(self):
        status, _, _ = self.request("POST", "/api/ask", {"question": "Explain", "finding_id": "not-a-finding"})
        self.assertEqual(status, 400)

    def test_idle_cancellation_reports_no_job(self):
        status, data, _ = self.request("POST", "/api/scan/cancel", {})
        self.assertEqual(status, 200)
        self.assertFalse(json.loads(data)["requested"])

    def test_late_cancel_does_not_promise_to_undo_committed_snapshot(self):
        self.server.app.demo_only = False
        self.write("test.txt")
        entered, release = threading.Event(), threading.Event()
        original = self.server.app.store.save
        def slow_save(report):
            entered.set()
            self.assertTrue(release.wait(3))
            original(report)
        responses = []
        with patch.object(self.server.app.store, "save", side_effect=slow_save):
            self.server.app.start_scan({"roots":[str(self.root)]})
            self.assertTrue(entered.wait(3))
            caller = threading.Thread(target=lambda: responses.append(self.server.app.cancel_scan()))
            caller.start()
            release.set()
            caller.join(3)
        self.assertFalse(caller.is_alive())
        self.assertFalse(responses[0]["requested"])
        self.assertEqual(self.server.app.scan_state["status"], "complete")


class AssistantRegressions(base.unittest.TestCase):
    def test_scope_does_not_match_copies(self):
        report = base.demo_reports()[0]
        result = assistant.evidence_answer(report, "What is the scope of this snapshot?")
        self.assertIn("covers", result["answer"])

    def test_malformed_model_catalog_falls_back(self):
        for payload in ([], {"models": None}, {"models": [None, {"name": 12}]}):
            with self.subTest(payload=payload), patch.object(assistant, "ollama_request", return_value=payload):
                self.assertEqual(assistant.models()["models"], [])

    def test_context_is_bounded_and_windows_question_paths_are_masked(self):
        report = base.demo_reports()[0]
        for finding in report["findings"]:
            finding["purpose"] = "Long metadata " * 10000
        captured = {}
        def response(path, data=None, timeout=4):
            if path == "/api/tags":
                return {"models": [{"name": "local-test"}]}
            if path == "/api/show":
                return {}
            captured.update(data)
            return {"message": {"content": '{"answer":"Review evidence","references":[]}'}}
        with patch.object(assistant, "ollama_request", side_effect=response):
            assistant.answer(report, "Explain c:\\users\\alex\\Downloads", "local-test")
        content = captured["messages"][1]["content"]
        self.assertLess(len(content), 27000)
        self.assertNotIn("users", content.lower())
