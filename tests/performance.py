"""Synthetic maximum-inventory benchmark. Creates no files outside a temporary project directory."""
import json
from pathlib import Path
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from lumen.demo import demo_reports
from lumen.rules import findings_for, summarize, uid
from lumen.store import Store, compare

report = demo_reports()[0]
template = report["files"][0]
start = time.perf_counter()
report["files"] = [{**template, "id":uid(str(i)), "path":f"C:/synthetic/fixture-{i}.txt", "relative":f"fixture-{i}.txt", "name":f"fixture-{i}.txt", "generated":None, "size":700_000_000 if i % 20 == 0 else i+1} for i in range(100_000)]
report["duplicates"] = []
report["findings"] = findings_for(report["files"], [], report["created"])
report["summary"] = summarize(report["files"], report["findings"])
stats = {"files":len(report["files"]), "findings":len(report["findings"]), "analysis_seconds":round(time.perf_counter()-start,3)}
qa = ROOT / ".qa"
qa.mkdir(exist_ok=True)
with tempfile.TemporaryDirectory(prefix="benchmark-", dir=qa) as temporary:
    store = Store(Path(temporary))
    start = time.perf_counter()
    store.save(report)
    stats["save_seconds"] = round(time.perf_counter()-start,3)
    stats["database_bytes"] = store.path.stat().st_size
    start = time.perf_counter()
    restored = store.get(report["id"])
    stats["load_seconds"] = round(time.perf_counter()-start,3)
    assert restored == report
    start = time.perf_counter()
    result = compare(report, restored)
    stats["compare_seconds"] = round(time.perf_counter()-start,3)
    assert result["changes"] == []
    stats["round_trip_verified"] = True
(qa / "performance-backend.json").write_text(json.dumps(stats,indent=2),encoding="utf-8")
print(json.dumps(stats,indent=2))
