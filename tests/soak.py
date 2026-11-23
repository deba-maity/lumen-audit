"""Repeat real HTTP scans and concurrent reads against self-created fixtures only.

Usage: python tests/soak.py --seconds 3600
No third-party packages, host scans, installed-app reads, or external requests.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import http.client
import json
from pathlib import Path
import random
import sys
import tempfile
import threading
import time

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from lumen.server import create_server


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--seconds", type=int, default=60)
    args = parser.parse_args()
    if not 1 <= args.seconds <= 86400:
        parser.error("Duration must be 1–86400 seconds.")
    qa = ROOT / ".qa"
    qa.mkdir(exist_ok=True)
    stats = {"cycles": 0, "http_requests": 0, "errors": [], "duration_requested": args.seconds}
    started = time.monotonic()
    rng = random.Random(1049)
    with tempfile.TemporaryDirectory(prefix="soak-", dir=qa) as temporary:
        folder = Path(temporary).resolve()
        assert ROOT in folder.parents
        selected = folder / "fixture"
        selected.mkdir()
        expected = {}
        for index in range(80):
            target = selected / ("project/.venv/Lib" if index % 3 else "project/node_modules/tool/bin") / f"item-{index}.txt"
            target.parent.mkdir(parents=True, exist_ok=True)
            data = bytes([index % 10]) * (128 + index % 10)
            target.write_bytes(data)
            expected[str(target)] = hashlib.sha256(data).hexdigest()
        server = create_server(0, folder / "state")
        thread = threading.Thread(target=server.serve_forever, kwargs={"poll_interval": .05}, daemon=True)
        thread.start()
        original = server.app.start_scan
        def guarded(body):
            if body.get("roots") != [str(selected)] or body.get("include_apps"):
                raise ValueError("The soak server only accepts its own fixture.")
            return original(body)
        server.app.start_scan = guarded
        request_lock = threading.Lock()
        def request(method, path, body=None):
            connection = http.client.HTTPConnection("127.0.0.1", server.server_port, timeout=15)
            try:
                connection.request(method, path, json.dumps(body) if body is not None else None,
                                   {"X-Lumen-Token": server.app.token, "Content-Type": "application/json"})
                response = connection.getresponse()
                raw = response.read()
                assert response.status < 400, (path, response.status, raw[:300])
                with request_lock:
                    stats["http_requests"] += 1
                return json.loads(raw)
            finally:
                connection.close()
        last_print = -60
        try:
            with ThreadPoolExecutor(max_workers=4) as workers:
                while time.monotonic() - started < args.seconds:
                    request("POST", "/api/scan", {"roots": [str(selected)], "hash_duplicates": True})
                    while True:
                        status = request("GET", "/api/scan")
                        if status["status"] != "running":
                            break
                        time.sleep(.02)
                    assert status["status"] == "complete", status
                    identifier = status["report_id"]
                    report = request("GET", "/api/reports/" + identifier)
                    assert len(report["files"]) == 80
                    assert len(report["duplicates"]) == 10
                    assert report["coverage"]["skipped"] == 0
                    assert report["summary"]["review_bytes"] <= report["summary"]["bytes"]
                    routes = ["/api/history", "/api/reports/" + identifier, "/api/scan", "/api/reports/demo-current"]
                    rng.shuffle(routes)
                    futures = [workers.submit(request, "GET", route) for route in routes]
                    for future in futures:
                        future.result()
                    result = request("POST", "/api/ask", {"report_id": identifier, "question": "Explain duplicate files"})
                    assert result["result"]["references"]
                    for path, digest in expected.items():
                        assert hashlib.sha256(Path(path).read_bytes()).hexdigest() == digest, path
                    stats["cycles"] += 1
                    elapsed = time.monotonic() - started
                    if elapsed - last_print >= 60:
                        print(f"{elapsed:.0f}s: {stats['cycles']} scan/store cycles, {stats['http_requests']} HTTP requests; contents unchanged", flush=True)
                        last_print = elapsed
                    stats["elapsed_seconds"] = round(elapsed, 2)
                    (qa / "soak-progress.json").write_text(json.dumps(stats, indent=2), encoding="utf-8")
                    time.sleep(min(10, max(0, args.seconds - elapsed)))
        except BaseException as error:
            stats["errors"].append(repr(error))
            raise
        finally:
            server.app.cancel.set()
            server.shutdown()
            server.server_close()
            thread.join(5)
            stats["elapsed_seconds"] = round(time.monotonic() - started, 2)
            stats["complete"] = stats["elapsed_seconds"] >= args.seconds and not stats["errors"]
            (qa / "soak-results.json").write_text(json.dumps(stats, indent=2), encoding="utf-8")
            print(json.dumps(stats), flush=True)


if __name__ == "__main__":
    main()
