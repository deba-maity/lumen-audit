"""Two local browser-test servers; live scans restricted to a newly created fixture."""
from pathlib import Path
import json
import sys
import tempfile
import threading

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from lumen.server import create_server

qa = ROOT / ".qa"
qa.mkdir(exist_ok=True)
with tempfile.TemporaryDirectory(prefix="ui-fixture-", dir=qa) as temporary:
    base = Path(temporary).resolve()
    assert ROOT in base.parents
    selected = base / "selected"
    selected.mkdir()
    for name, content in {"first.txt":"identical fixture", "second.txt":"identical fixture", "package.json":'{"name":"fixture"}', "readme.md":"UI fixture"}.items():
        (selected / name).write_text(content, encoding="utf-8")
    demo = create_server(0, base / "demo-state", demo_only=True)
    live = create_server(0, base / "live-state")
    original = live.app.start_scan
    def guarded(body):
        if body.get("roots") != [str(selected)] or body.get("include_apps"):
            raise ValueError("Browser tests accept only their own fixture folder, without installed-app inventory.")
        return original(body)
    live.app.start_scan = guarded
    threads = []
    for server in (demo, live):
        thread = threading.Thread(target=server.serve_forever, kwargs={"poll_interval": .05}, daemon=True)
        thread.start()
        threads.append(thread)
    print(json.dumps({"demo":f"http://127.0.0.1:{demo.server_port}", "live":f"http://127.0.0.1:{live.server_port}", "root":str(selected)}), flush=True)
    try:
        sys.stdin.read()  # Parent closes stdin on success, failure, or interruption.
    finally:
        for server in (demo, live):
            server.app.cancel.set()
            server.shutdown()
            server.server_close()
        for thread in threads:
            thread.join(3)
