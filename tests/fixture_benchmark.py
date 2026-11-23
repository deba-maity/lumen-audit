"""Benchmark real reads of self-created tiny files, never personal directories.

Usage: python tests/fixture_benchmark.py --files 10000
All files are created under .qa/, verified unchanged, and removed on completion.
"""
import argparse
import csv
import hashlib
import io
import json
from pathlib import Path
import sys
import tempfile
import threading
import time

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from lumen.export import csv_inventory
from lumen.scanner import scan, validate_roots
from lumen.store import Store


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--files", type=int, default=1000)
    args = parser.parse_args()
    if not 2 <= args.files <= 20000:
        parser.error("Choose between 2 and 20,000 fixture files.")
    qa = ROOT / ".qa"
    qa.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="filesystem-benchmark-", dir=qa) as temporary:
        folder = Path(temporary).resolve()
        assert ROOT in folder.parents
        selected = folder / "fixture"
        selected.mkdir()
        expected = {}
        print(f"Creating {args.files:,} fixture files inside .qa/", flush=True)
        for index in range(args.files):
            subfolder = ".venv/Lib/package" if index % 2 else "node_modules/tool/bin"
            path = selected / f"project-{index // 100}" / subfolder / f"fixture-{index}.txt"
            path.parent.mkdir(parents=True, exist_ok=True)
            data = (f"lumen-fixture-{index // 2:06d}\n".encode() * 64)[:1024]
            path.write_bytes(data)
            expected[path] = (hashlib.sha256(data).hexdigest(), path.stat().st_mtime_ns)
        roots = validate_roots([str(selected)])
        started = time.perf_counter()
        report = scan(roots, cancel=threading.Event(), progress=lambda update: None, hash_duplicates=True)
        scan_seconds = time.perf_counter() - started
        assert len(report["files"]) == args.files
        assert len(report["duplicates"]) == args.files // 2
        assert report["summary"]["bytes"] == args.files * 1024
        assert report["coverage"]["skipped"] == 0
        assert not report["coverage"]["limited"]
        print("Scan complete; checking CSV, SQLite, and unchanged fixture contents", flush=True)
        started = time.perf_counter()
        exported = csv_inventory(report)
        csv_seconds = time.perf_counter() - started
        rows = list(csv.DictReader(io.StringIO(exported.lstrip("\ufeff"))))
        assert len(rows) == args.files
        assert sum(int(row["Logical bytes"]) for row in rows) == report["summary"]["bytes"]
        store = Store(folder / "state")
        started = time.perf_counter()
        store.save(report)
        restored = store.get(report["id"])
        store_seconds = time.perf_counter() - started
        assert restored["summary"] == report["summary"]
        for path, (digest, modified) in expected.items():
            assert hashlib.sha256(path.read_bytes()).hexdigest() == digest
            assert path.stat().st_mtime_ns == modified
        result = {"files": args.files, "fixture_bytes": report["summary"]["bytes"],
                  "duplicates": len(report["duplicates"]), "hashed_files": report["coverage"]["hashed_files"],
                  "scan_and_hash_seconds": round(scan_seconds, 3), "csv_seconds": round(csv_seconds, 3),
                  "sqlite_round_trip_seconds": round(store_seconds, 3), "contents_and_modified_times_unchanged": True,
                  "scope": "self-created 1 KiB files under .qa/; warm filesystem cache", "passed": True}
    (qa / "fixture-benchmark.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
