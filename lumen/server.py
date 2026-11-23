"""Loopback HTTP application. No remote binding, shell execution, or filesystem mutations API."""
from __future__ import annotations

import argparse
import gzip
import json
import secrets
import threading
import time
import urllib.parse
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from . import __version__
from .assistant import answer, models
from .demo import demo_reports
from .export import csv_inventory, html_report
from .scanner import ScanCancelled, scan, validate_roots
from .store import Store, compare

BASE = Path(__file__).resolve().parent.parent
WEB = BASE / "web"


class App:
    def __init__(self, state_dir=None, demo_only=False):
        self.demo_only = demo_only
        self.token = secrets.token_urlsafe(32)
        self.store = Store(Path(state_dir) if state_dir else BASE / ".local")
        self.demos = {report["id"]: report for report in demo_reports()}
        self.lock = threading.Lock()
        self.scan_state = {"status": "idle"}
        self.cancel = threading.Event()
        self.ai_lock = threading.Lock()
        self.ai_jobs = {}

    def report(self, identifier):
        if not isinstance(identifier, str) or len(identifier) > 100:
            raise ValueError("Invalid snapshot identifier.")
        report = self.demos.get(identifier)
        if report is None and not self.demo_only:
            report = self.store.get(identifier)
        if not report:
            raise LookupError("Snapshot not found.")
        return report

    def history(self):
        keys = ("id", "name", "created", "roots", "summary", "demo")
        return [{key: report[key] for key in keys} for report in self.demos.values()] + ([] if self.demo_only else self.store.list())

    def cancel_scan(self):
        with self.lock:
            active = self.scan_state["status"] == "running"
            if active:
                self.cancel.set()
            return {"requested": active, "message": "Cancellation requested." if active else "No scan is currently running."}

    def start_scan(self, body):
        if self.demo_only:
            raise PermissionError("Demo-only mode blocks all filesystem scans. Run Lumen normally on your own laptop to enable scanning.")
        for key in ("hash_duplicates", "include_apps"):
            if key in body and not isinstance(body[key], bool):
                raise ValueError(f"{key} must be true or false.")
        name = body.get("name", "")
        if not isinstance(name, str) or len(name) > 80:
            raise ValueError("Snapshot labels must be text, up to 80 characters.")
        name = name.strip() or "Local snapshot"
        with self.lock:
            if self.scan_state["status"] == "running":
                raise ValueError("A scan is already running. Cancel it or wait for it to finish.")
        roots = validate_roots(body.get("roots"), self.store.directory)
        with self.lock:
            if self.scan_state["status"] == "running":
                raise ValueError("A scan is already running. Cancel it or wait for it to finish.")
            self.cancel = threading.Event()
            self.scan_state = {"status": "running", "phase": "inventory", "files": 0, "folders": 0, "skipped": 0, "started": time.time()}
        def progress(update):
            with self.lock:
                self.scan_state.update(update)
        def worker():
            try:
                report = scan(roots, cancel=self.cancel, progress=progress,
                              hash_duplicates=body.get("hash_duplicates", False), include_apps=body.get("include_apps", False),
                              excluded=self.store.directory)
                report["name"] = name
                # Cancellation and commit are serialized: once commit wins, a late
                # cancellation reports no active scan instead of promising rollback.
                with self.lock:
                    if self.cancel.is_set():
                        raise ScanCancelled()
                    self.store.save(report)
                    self.scan_state.update({"status": "complete", "report_id": report["id"], "files": len(report["files"])})
            except ScanCancelled:
                progress({"status": "cancelled", "message": "Scan cancelled. No partial snapshot was saved."})
            except Exception as error:
                progress({"status": "error", "message": str(error)[:500] or "Scan failed."})
        threading.Thread(target=worker, daemon=True, name="lumen-scan").start()
        return {"started": True}

    def start_answer(self, body):
        question = body.get("question", "")
        model = body.get("model")
        finding_id = body.get("finding_id")
        file_id = body.get("file_id")
        if not isinstance(question, str) or not question.strip() or len(question) > 2000:
            raise ValueError("Ask a question between 1 and 2,000 characters.")
        if model is not None and (not isinstance(model, str) or len(model) > 200):
            raise ValueError("Invalid model name.")
        if finding_id is not None and not isinstance(finding_id, str):
            raise ValueError("Invalid finding identifier.")
        if file_id is not None and not isinstance(file_id, str):
            raise ValueError("Invalid file identifier.")
        report = self.report(body.get("report_id", "demo-current"))
        if finding_id and not any(item["id"] == finding_id for item in report["findings"]):
            raise ValueError("This finding is not in the selected snapshot.")
        if file_id and not any(item["id"] == file_id for item in report["files"]):
            raise ValueError("This file is not in the selected snapshot.")
        if finding_id and file_id:
            raise ValueError("Select one finding or one file for an explanation.")
        if not model:
            return {"status": "complete", "result": answer(report, question, finding_id=finding_id, file_id=file_id)}
        if not self.ai_lock.acquire(blocking=False):
            raise ValueError("A local model is already responding. Please wait for it to finish.")
        identifier = secrets.token_hex(12)
        with self.lock:
            if len(self.ai_jobs) >= 20:
                self.ai_jobs.pop(next(iter(self.ai_jobs)))
            self.ai_jobs[identifier] = {"status": "running"}
        def worker():
            try:
                result = answer(report, question, model, finding_id, file_id)
                with self.lock:
                    self.ai_jobs[identifier] = {"status": "complete", "result": result}
            except Exception as error:
                with self.lock:
                    self.ai_jobs[identifier] = {"status": "error", "message": str(error)[:500] or "Local model failed. Try the evidence guide."}
            finally:
                self.ai_lock.release()
        threading.Thread(target=worker, daemon=True, name="lumen-explanation").start()
        return {"status": "running", "job_id": identifier}


class Handler(BaseHTTPRequestHandler):
    server_version = "Lumen/" + __version__

    def setup(self):
        super().setup()
        self.connection.settimeout(15)

    def log_message(self, *args):
        # Do not log filenames, paths, questions, or tokens.
        pass

    @property
    def app(self):
        return self.server.app

    def send(self, status, body, content_type="application/json; charset=utf-8", headers=None):
        if isinstance(body, (dict, list)):
            body = json.dumps(body, ensure_ascii=True, separators=(",", ":")).encode()
        elif isinstance(body, str):
            body = body.encode("utf-8", errors="replace")
        headers = dict(headers or {})
        # Large inventories transfer efficiently while remaining ordinary JSON to browsers.
        encodings = [part.strip().split(";")[0] for part in self.headers.get("Accept-Encoding", "").split(",") if ";" not in part]
        if len(body) >= 262144 and content_type.startswith("application/json") and "gzip" in encodings:
            body = gzip.compress(body, compresslevel=3)
            headers["Content-Encoding"] = "gzip"
            headers["Vary"] = "Accept-Encoding"
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Content-Security-Policy", "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; font-src 'self'; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'")
        for key, value in (headers or {}).items():
            self.send_header(key, value)
        self.end_headers()
        try:
            self.wfile.write(body)
        except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
            pass

    def trusted(self, require_token=False):
        port = self.server.server_port
        allowed_hosts = {f"127.0.0.1:{port}", f"localhost:{port}"}
        if self.headers.get("Host", "") not in allowed_hosts:
            self.send(403, {"error": "Invalid local host."})
            return False
        origin = self.headers.get("Origin")
        if origin and origin not in {"http://" + host for host in allowed_hosts}:
            self.send(403, {"error": "Cross-origin requests are not allowed."})
            return False
        if self.headers.get("Sec-Fetch-Site") == "cross-site":
            self.send(403, {"error": "Cross-site requests are not allowed."})
            return False
        token = self.headers.get("X-Lumen-Token", "")
        if require_token and (not token.isascii() or not secrets.compare_digest(token, self.app.token)):
            self.send(403, {"error": "Session token missing or expired. Reload Lumen."})
            return False
        return True

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        if not self.trusted(require_token=path.startswith("/api/") and path != "/api/bootstrap"):
            return
        try:
            if path == "/api/bootstrap":
                home = Path.home()
                self.send(200, {"token": self.app.token, "version": __version__, "demo_only": self.app.demo_only,
                                "locations": [{"label": name, "path": str(home / name)} for name in ("Downloads", "Documents", "Desktop", "Pictures", "Videos")],
                                "state_dir": str(self.app.store.directory)})
            elif path == "/api/history":
                self.send(200, self.app.history())
            elif path == "/api/scan":
                with self.app.lock:
                    state = dict(self.app.scan_state)
                self.send(200, state)
            elif path == "/api/models":
                self.send(200, models())
            elif path.startswith("/api/answers/"):
                with self.app.lock:
                    job = self.app.ai_jobs.get(path.rsplit("/", 1)[1])
                if not job:
                    raise LookupError("Explanation job not found.")
                self.send(200, job)
            elif path == "/api/compare":
                query = urllib.parse.parse_qs(parsed.query)
                self.send(200, compare(self.app.report(query.get("before", [""])[0]), self.app.report(query.get("after", [""])[0])))
            elif path.startswith("/api/reports/"):
                identifier = path.rsplit("/", 1)[1]
                extension = next((suffix for suffix in (".html", ".json", ".csv") if identifier.endswith(suffix)), "")
                report = self.app.report(identifier[:-len(extension)] if extension else identifier)
                if extension == ".html":
                    self.send(200, html_report(report), "text/html; charset=utf-8", {"Content-Disposition": 'attachment; filename="lumen-report.html"'})
                elif extension == ".csv":
                    self.send(200, csv_inventory(report), "text/csv; charset=utf-8", {"Content-Disposition": 'attachment; filename="lumen-inventory.csv"'})
                elif extension == ".json":
                    self.send(200, report, headers={"Content-Disposition": 'attachment; filename="lumen-snapshot.json"'})
                else:
                    self.send(200, report)
            else:
                assets = {"/": ("index.html", "text/html; charset=utf-8"), "/app.js": ("app.js", "text/javascript; charset=utf-8"),
                          "/styles.css": ("styles.css", "text/css; charset=utf-8"), "/favicon.svg": ("favicon.svg", "image/svg+xml")}
                if path not in assets:
                    raise LookupError("Not found.")
                file, mime = assets[path]
                self.send(200, (WEB / file).read_bytes(), mime)
        except LookupError as error:
            self.send(404, {"error": str(error)})
        except (ValueError, OSError) as error:
            self.send(400, {"error": str(error)[:500]})
        except Exception:
            self.send(500, {"error": "Could not load local data. Check that Lumen's state folder is accessible."})

    def do_POST(self):
        if not self.trusted(require_token=True):
            return
        try:
            if self.headers.get("Transfer-Encoding") or len(self.headers.get_all("Content-Length", [])) != 1:
                raise ValueError("Provide one Content-Length header; chunked requests are not supported.")
            if self.headers.get("Content-Type", "").split(";")[0] != "application/json":
                raise ValueError("Expected application/json.")
            length = int(self.headers.get("Content-Length", "0"))
            if not 0 < length <= 32_768:
                raise ValueError("Request must be between 1 and 32,768 bytes.")
            body = json.loads(self.rfile.read(length))
            if not isinstance(body, dict):
                raise ValueError("Expected a JSON object.")
            if self.path == "/api/scan":
                self.send(202, self.app.start_scan(body))
            elif self.path == "/api/scan/cancel":
                self.send(200, self.app.cancel_scan())
            elif self.path == "/api/ask":
                self.send(200, self.app.start_answer(body))
            else:
                self.send(404, {"error": "Not found."})
        except PermissionError as error:
            self.send(403, {"error": str(error)})
        except LookupError as error:
            self.send(404, {"error": str(error)})
        except (ValueError, OSError, TypeError, RecursionError) as error:
            self.send(400, {"error": str(error)[:500]})
        except Exception:
            self.send(500, {"error": "Could not complete this request. Local data may be unavailable."})


def create_server(port=8765, state_dir=None, demo_only=False):
    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    server.daemon_threads = True
    server.app = App(state_dir, demo_only)
    return server


def main():
    parser = argparse.ArgumentParser(description="Lumen — local, read-only storage intelligence")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--demo-only", action="store_true", help="Block all filesystem scans; explore fictional data only")
    parser.add_argument("--no-browser", action="store_true")
    parser.add_argument("--state-dir", type=Path, help="Directory for Lumen's own snapshots (default: .local beside run.py)")
    args = parser.parse_args()
    if not 0 <= args.port <= 65535:
        parser.error("Port must be between 0 and 65535.")
    try:
        server = create_server(args.port, args.state_dir, args.demo_only)
    except OSError as error:
        if args.port == 8765:
            try:
                server = create_server(0, args.state_dir, args.demo_only)
                print("  Default port unavailable; selected a free local port.", flush=True)
            except OSError:
                parser.exit(1, f"Could not start Lumen: {error}\nTry another port: python run.py --port 0\n")
        else:
            parser.exit(1, f"Could not start Lumen: {error}\nTry another port: python run.py --port 0\n")
    url = f"http://127.0.0.1:{server.server_port}"
    print(f"\n  LUMEN {__version__}\n  {url}\n  {'Demo-only: filesystem scans are disabled.' if args.demo_only else 'Local mode: no scan starts until you choose folders and start one.'}\n  Press Ctrl+C to stop.\n", flush=True)
    browser_timer = None
    if not args.no_browser:
        browser_timer = threading.Timer(0.5, lambda: webbrowser.open(url))
        browser_timer.daemon = True
        browser_timer.start()
    try:
        server.serve_forever(poll_interval=0.3)
    except KeyboardInterrupt:
        pass
    finally:
        if browser_timer:
            browser_timer.cancel()
        server.app.cancel.set()
        server.server_close()


if __name__ == "__main__":
    main()
