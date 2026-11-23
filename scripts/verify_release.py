"""Check the source archive and start an extracted demo without site-packages.

Only project-local temporary data and loopback requests are used. No scans run.
"""
from __future__ import annotations

import hashlib
import http.client
import json
from pathlib import Path, PurePosixPath
import queue
import re
import subprocess
import sys
import tempfile
import threading
import zipfile

from package import ROOT, build, version


def verify():
    archive = build()
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    assert hashlib.sha256(build().read_bytes()).hexdigest() == digest, "Build is not deterministic"
    qa = ROOT / ".qa"
    qa.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="release-check-", dir=qa) as temporary:
        folder = Path(temporary).resolve()
        assert ROOT in folder.parents
        with zipfile.ZipFile(archive) as source:
            assert source.testzip() is None
            names = source.namelist()
            assert len(names) == len(set(names)), "Duplicate archive entries"
            for name in names:
                parts = PurePosixPath(name).parts
                assert parts[0] == "lumen-audit" and ".." not in parts and "\\" not in name
                assert not {".qa", ".local", "node_modules", "__pycache__", ".git", "dist"}.intersection(parts)
            manifest = json.loads(source.read("lumen-audit/RELEASE-MANIFEST.json"))
            assert manifest["version"] == version()
            assert set(names) == {"lumen-audit/" + name for name in manifest["files"]} | {"lumen-audit/RELEASE-MANIFEST.json"}
            for name, expected in manifest["files"].items():
                assert hashlib.sha256(source.read("lumen-audit/" + name)).hexdigest() == expected
            source.extractall(folder)
        checkout = folder / "lumen-audit"
        result = subprocess.run([sys.executable, "-S", "run.py", "--help"], cwd=checkout, capture_output=True, timeout=10)
        assert result.returncode == 0, result.stderr
        result = subprocess.run([sys.executable, "-S", "-m", "unittest", "discover", "-s", "tests", "-q"],
                                cwd=checkout, capture_output=True, timeout=60)
        assert result.returncode == 0, result.stderr.decode("utf-8", errors="replace")
        state_dir = checkout / "demo-state-must-stay-absent"
        process = subprocess.Popen([sys.executable, "-S", "run.py", "--demo-only", "--no-browser", "--port", "0", "--state-dir", str(state_dir)],
                                   cwd=checkout, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        lines = queue.Queue()
        def output_reader():
            for line in process.stdout:
                lines.put(line)
        reader = threading.Thread(target=output_reader, daemon=True)
        reader.start()
        try:
            port = None
            for _ in range(10):
                line = lines.get(timeout=5)
                match = re.search(r"http://127\.0\.0\.1:(\d+)", line)
                if match:
                    port = int(match.group(1))
                    break
            assert port is not None, "Extracted server did not print its local address"
            def request(path, method="GET", body=None, token=""):
                connection = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
                try:
                    connection.request(method, path, json.dumps(body) if body is not None else None,
                                       {"X-Lumen-Token": token, "Content-Type": "application/json"})
                    response = connection.getresponse()
                    return response.status, response.read()
                finally:
                    connection.close()
            status, raw = request("/api/bootstrap")
            config = json.loads(raw)
            assert status == 200 and config["demo_only"] and config["version"] == version()
            token = config["token"]
            for asset in ("/", "/app.js", "/styles.css", "/favicon.svg"):
                status, body = request(asset)
                assert status == 200 and body, asset
            status, raw = request("/api/history", token=token)
            assert status == 200 and all(report["demo"] for report in json.loads(raw))
            status, raw = request("/api/reports/demo-current", token=token)
            assert status == 200 and json.loads(raw)["summary"]["files"] > 0
            # Demo mode must reject the request before considering any root path.
            status, raw = request("/api/scan", "POST", {"roots": ["invalid-unused-fixture-root"]}, token)
            assert status == 403, raw
            assert not state_dir.exists(), "Demo startup created a state directory"
            assert not (checkout / ".local").exists(), "Demo startup created a database"
        finally:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)
            reader.join(2)
            process.stdout.close()
            process.stderr.close()
    results = {"passed": True, "version": version(), "source_files": len(manifest["files"]),
               "archive_bytes": archive.stat().st_size, "sha256": digest,
               "checks": ["deterministic build", "source allowlist", "manifest integrity", "fresh extracted CLI", "extracted backend suite",
                          "no site-packages", "all web assets", "demo API", "scan rejection", "no demo state writes"]}
    (qa / "release-results.json").write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    verify()
