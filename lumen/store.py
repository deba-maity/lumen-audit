"""Only Lumen's own SQLite file is written; audited locations are never modified."""
import json
import sqlite3
from contextlib import closing
from pathlib import Path


class Store:
    def __init__(self, directory: Path):
        self.directory = directory.resolve()
        self.path = self.directory / "snapshots.sqlite3"

    def _connect(self, write=False):
        existing = self.path.exists()
        if write:
            self.directory.mkdir(parents=True, exist_ok=True)
            connection = sqlite3.connect(self.path, timeout=10)
        else:
            connection = sqlite3.connect(self.path.as_uri() + "?mode=ro", uri=True, timeout=10)
        try:
            if existing:
                columns = [row[1] for row in connection.execute("PRAGMA table_info(snapshots)")]
                if columns != ["id", "created", "summary", "report"]:
                    raise sqlite3.DatabaseError("This state file is not a supported Lumen database. Choose another --state-dir; the existing file was not changed.")
            if write:
                connection.execute("CREATE TABLE IF NOT EXISTS snapshots (id TEXT PRIMARY KEY, created REAL NOT NULL, summary TEXT NOT NULL, report TEXT NOT NULL)")
            return connection
        except Exception:
            connection.close()
            raise

    def save(self, report):
        brief = {key: report[key] for key in ("id", "name", "created", "roots", "summary", "demo")}
        with closing(self._connect(write=True)) as connection:
            connection.execute("INSERT OR REPLACE INTO snapshots VALUES (?, ?, ?, ?)", (report["id"], report["created"], json.dumps(brief), json.dumps(report)))
            connection.commit()

    def list(self):
        if not self.path.exists():
            return []
        with closing(self._connect()) as connection:
            return [json.loads(row[0]) for row in connection.execute("SELECT summary FROM snapshots ORDER BY created DESC LIMIT 100")]

    def get(self, identifier):
        if not self.path.exists():
            return None
        with closing(self._connect()) as connection:
            row = connection.execute("SELECT report FROM snapshots WHERE id = ?", (identifier,)).fetchone()
            return json.loads(row[0]) if row else None


def compare(before, after):
    if before["created"] > after["created"]:
        raise ValueError("The comparison baseline must be older than the current snapshot.")
    if before["demo"] != after["demo"] or sorted(before["roots"]) != sorted(after["roots"]):
        raise ValueError("Compare snapshots with the same selected folders and mode.")
    old = {file["path"]: file for file in before["files"]}
    new = {file["path"]: file for file in after["files"]}
    changes = []
    for path in old.keys() | new.keys():
        previous, current = old.get(path), new.get(path)
        delta = (current["size"] if current else 0) - (previous["size"] if previous else 0)
        kind = "added" if previous is None else "removed" if current is None else "changed"
        if kind != "changed" or delta or previous["modified"] != current["modified"]:
            changes.append({"path": path, "name": (current or previous)["name"], "kind": kind, "delta": delta,
                            "before": previous["size"] if previous else None, "after": current["size"] if current else None})
    return {"before": before["id"], "after": after["id"], "delta": after["summary"]["bytes"] - before["summary"]["bytes"],
            "added": sum(item["kind"] == "added" for item in changes), "removed": sum(item["kind"] == "removed" for item in changes),
            "changed": sum(item["kind"] == "changed" for item in changes),
            "partial": bool(before["coverage"]["limited"] or after["coverage"]["limited"] or before["coverage"]["skipped"] or after["coverage"]["skipped"]),
            "total_changes": len(changes),
            "changes": sorted(changes, key=lambda item: (-abs(item["delta"]), item["path"]))[:500]}
