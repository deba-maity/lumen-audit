"""Real loopback transport failure tests; no actual Ollama service is contacted."""
import gzip
from contextlib import closing
import http.client
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import sqlite3
import threading
import time
import unittest
from unittest.mock import patch

import test_lumen as base
from lumen import assistant
from lumen.store import Store


class FakeModelHandler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def do_GET(self):
        mode = self.server.mode
        if mode == "redirect":
            self.send_response(302)
            self.send_header("Location", "http://external.invalid/")
            self.end_headers()
            return
        data = b'{"models":[]}' if mode == "valid" else b"x" * (2*1024*1024+1) if mode == "oversized" else b'{"models":[]}'
        self.send_response(200)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        try:
            if mode == "drip":
                for byte in data:
                    self.wfile.write(bytes([byte]))
                    self.wfile.flush()
                    time.sleep(.08)
            else:
                self.wfile.write(data)
        except OSError:
            pass


class LocalModelTransportTests(unittest.TestCase):
    def setUp(self):
        self.server = ThreadingHTTPServer(("127.0.0.1",0), FakeModelHandler)
        self.server.daemon_threads = True
        self.server.mode = "valid"
        self.thread = threading.Thread(target=self.server.serve_forever,kwargs={"poll_interval":.01},daemon=True)
        self.thread.start()
        original = http.client.HTTPConnection
        self.redirect = patch.object(assistant.http.client,"HTTPConnection",side_effect=lambda host,port,timeout:original("127.0.0.1",self.server.server_port,timeout=timeout))
        self.redirect.start()

    def tearDown(self):
        self.redirect.stop()
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(2)

    def test_valid_response(self):
        self.assertEqual(assistant.ollama_request("/api/tags"),{"models":[]})

    def test_redirect_is_not_followed(self):
        self.server.mode="redirect"
        with self.assertRaisesRegex(ValueError,"redirect"):
            assistant.ollama_request("/api/tags")

    def test_oversized_response_is_stopped(self):
        self.server.mode="oversized"
        with self.assertRaisesRegex(ValueError,"too large"):
            assistant.ollama_request("/api/tags")

    def test_wall_clock_deadline_stops_drip_feed(self):
        self.server.mode="drip"
        start=time.monotonic()
        with self.assertRaises(TimeoutError):
            assistant.ollama_request("/api/tags",timeout=.15)
        self.assertLess(time.monotonic()-start,.8)


class SerializationTests(base.ServerFixtureCase):
    def test_compressed_large_inventory_matches_json(self):
        self.server.app.demos["demo-current"]["padding"]="fixture"*100000
        status,body,headers=self.request("GET","/api/reports/demo-current",extra={"Accept-Encoding":"gzip, deflate"})
        self.assertEqual(status,200)
        self.assertEqual(headers["Content-Encoding"],"gzip")
        self.assertEqual(json.loads(gzip.decompress(body))["padding"],"fixture"*100000)
        self.assertLess(len(body),30000)

    def test_gzip_opt_out_is_respected(self):
        self.server.app.demos["demo-current"]["padding"]="fixture"*100000
        status,body,headers=self.request("GET","/api/reports/demo-current",extra={"Accept-Encoding":"gzip;q=0"})
        self.assertEqual(status,200)
        self.assertNotIn("Content-Encoding",headers)
        self.assertEqual(json.loads(body)["id"],"demo-current")

    def test_html_export_handles_surrogate_filenames(self):
        self.server.app.demos["demo-current"]["findings"][0]["title"]="invalid-byte-\udcff"
        self.assertEqual(self.request("GET","/api/reports/demo-current.html")[0],200)


class StateFileTests(base.FixtureCase):
    def test_unicode_and_space_in_state_path(self):
        store=Store(self.base / "state caf\u00e9 #1")
        report=base.demo_reports()[0]
        store.save(report)
        self.assertEqual(store.get(report["id"]),report)
    def test_unrelated_database_is_not_modified(self):
        store=Store(self.base / "state")
        store.directory.mkdir()
        with closing(sqlite3.connect(store.path)) as connection:
            connection.execute("CREATE TABLE unrelated (value TEXT)")
            connection.commit()
        before=store.path.read_bytes()
        with self.assertRaises(sqlite3.DatabaseError):
            store.save(base.demo_reports()[0])
        self.assertEqual(store.path.read_bytes(),before)

    def test_read_connection_cannot_write(self):
        store=Store(self.base / "state")
        store.save(base.demo_reports()[0])
        connection=store._connect()
        try:
            with self.assertRaises(sqlite3.OperationalError):
                connection.execute("DELETE FROM snapshots")
        finally:
            connection.close()


class RedactionTests(unittest.TestCase):
    def test_root_masking_preserves_path_boundaries(self):
        self.assertEqual(assistant.redact_paths("/home/alexander/file",["/home/alex"]),"/home/alexander/file")
        self.assertEqual(assistant.redact_paths("C:/Users/Alexander/file",["C:/Users/Alex"]),"C:/Users/Alexander/file")
        self.assertEqual(assistant.redact_paths("/home/alex/file",["/"]),"[selected-folder-1]/home/alex/file")
        self.assertEqual(assistant.redact_paths("c:\\users\\alex?",["C:/Users/Alex"]),"[selected-folder-1]?")
