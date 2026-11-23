"""Build a deterministic source release, excluding snapshots and development data.

Usage: python scripts/package.py
The ZIP is written to dist/; only explicitly selected source directories are read.
"""
from __future__ import annotations

import ast
import hashlib
import json
import os
from pathlib import Path
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parent.parent
ROOT_FILES = {"README.md", "CHANGELOG.md", "LICENSE", "run.py", "Start Lumen.cmd", "Start Demo.cmd", ".gitignore"}
SOURCE_TYPES = {
    "lumen": {".py"}, "web": {".html", ".js", ".css", ".svg"},
    "tests": {".py", ".cjs"}, "scripts": {".py"},
    "docs": {".md", ".png"}, ".github": {".yml", ".yaml"},
}


def version():
    tree = ast.parse((ROOT / "lumen" / "__init__.py").read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(isinstance(target, ast.Name) and target.id == "__version__" for target in node.targets):
            return ast.literal_eval(node.value)
    raise ValueError("Missing release version.")


def is_link(path):
    return path.is_symlink() or bool(getattr(path.lstat(), "st_file_attributes", 0) & 0x400)


def sources():
    for name in sorted(ROOT_FILES):
        path = ROOT / name
        if not path.is_file() or is_link(path):
            raise ValueError(f"Missing source file or unexpected link: {name}")
        yield path
    for name, extensions in SOURCE_TYPES.items():
        directory = ROOT / name
        if is_link(directory):
            raise ValueError(f"Unexpected linked source directory: {name}")
        for current, dirs, files in os.walk(directory, followlinks=False):
            dirs[:] = sorted(part for part in dirs if part != "__pycache__" and not part.startswith(".") and not is_link(Path(current) / part))
            for file in sorted(files):
                path = Path(current) / file
                if path.suffix.lower() in extensions and not is_link(path):
                    yield path


def build():
    release_version = version()
    destination = ROOT / "dist"
    destination.mkdir(exist_ok=True)
    if is_link(destination):
        raise ValueError("The release directory must not be a link.")
    output = destination / f"lumen-audit-{release_version}.zip"
    entries = {path.relative_to(ROOT).as_posix(): path.read_bytes() for path in sources()}
    manifest = {"version": release_version, "files": {name: hashlib.sha256(data).hexdigest() for name, data in sorted(entries.items())}}
    entries["RELEASE-MANIFEST.json"] = (json.dumps(manifest, indent=2, ensure_ascii=True) + "\n").encode("utf-8")
    with tempfile.NamedTemporaryFile(prefix="release-", suffix=".zip", dir=destination, delete=False) as stream:
        temporary = Path(stream.name)
    try:
        with zipfile.ZipFile(temporary, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
            for name, data in sorted(entries.items()):
                entry = zipfile.ZipInfo("lumen-audit/" + name, date_time=(2000, 1, 1, 0, 0, 0))
                entry.create_system = 3
                entry.external_attr = 0o100644 << 16
                entry.compress_type = zipfile.ZIP_DEFLATED
                archive.writestr(entry, data, compresslevel=9)
        os.replace(temporary, output)
    finally:
        temporary.unlink(missing_ok=True)
    return output


if __name__ == "__main__":
    archive = build()
    print(json.dumps({"archive": str(archive), "bytes": archive.stat().st_size,
                      "sha256": hashlib.sha256(archive.read_bytes()).hexdigest()}, indent=2))
