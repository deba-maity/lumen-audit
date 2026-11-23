"""Handcrafted fictional data. This module never inspects the host filesystem."""
from __future__ import annotations

import copy
import time
from pathlib import Path

from .rules import DAY, GIB, MIB, category, describe_file, findings_for, summarize, uid


def demo_reports() -> list[dict]:
    now = time.time()
    root = "C:/Users/Alex"
    entries = [
        ("Videos/Weekend in Kyoto.mov", 6.8 * GIB, 18),
        ("Videos/Screen recordings/Product walkthrough.mp4", 2.3 * GIB, 12),
        ("Videos/Screen recordings/Prototype review.mp4", 1.6 * GIB, 45),
        ("Videos/Portfolio reel.mp4", 870 * MIB, 6),
        ("Downloads/DesignKit-2024.zip", 1.2 * GIB, 210),
        ("Downloads/Blender-4.2.msi", 312 * MIB, 190),
        ("Downloads/Notion-setup.msi", 145 * MIB, 120),
        ("Downloads/Ubuntu-desktop.iso", 4.5 * GIB, 95),
        ("Downloads/Brand-assets.zip", 240 * MIB, 27),
        ("Documents/Archive/Brand-assets.zip", 240 * MIB, 27),
        ("Desktop/Brand-assets-final.zip", 240 * MIB, 20),
        ("Pictures/Iceland/DSC_4028.raw", 42 * MIB, 330),
        ("Pictures/Iceland/DSC_4029.raw", 41 * MIB, 330),
        ("Pictures/Iceland/DSC_4030.raw", 40 * MIB, 330),
        ("Pictures/Studio/Website hero.psd", 780 * MIB, 32),
        ("Pictures/Studio/Packaging exploration.psd", 650 * MIB, 47),
        ("Pictures/Exports/Website hero.png", 16 * MIB, 30),
        ("Desktop/Website hero.png", 16 * MIB, 29),
        ("Documents/Research/Interview synthesis.pdf", 8 * MIB, 4),
        ("Documents/Research/Customer interviews.pdf", 14 * MIB, 7),
        ("Documents/Finance/Annual summary.xlsx", 3 * MIB, 90),
        ("Documents/Portfolio.pdf", 24 * MIB, 8),
        ("Documents/Notes/Ideas.md", 12000, 1),
        ("Projects/atlas/node_modules/typescript/lib/typescript.js", 12 * MIB, 120),
        ("Projects/atlas/node_modules/@next/swc/native.node", 130 * MIB, 120),
        ("Projects/atlas/node_modules/playwright/.local-browsers/browser.bin", 280 * MIB, 120),
        ("Projects/atlas/node_modules/esbuild/bin/esbuild", 9 * MIB, 120),
        ("Projects/atlas/.next/cache/webpack/client.pack", 820 * MIB, 110),
        ("Projects/atlas/.next/cache/webpack/server.pack", 460 * MIB, 110),
        ("Projects/atlas/package.json", 1800, 110),
        ("Projects/atlas/package-lock.json", 450000, 110),
        ("Projects/atlas/src/app.tsx", 9000, 110),
        ("Projects/fieldnotes/.venv/Lib/site-packages/torch/lib/torch_cpu.dll", 620 * MIB, 40),
        ("Projects/fieldnotes/.venv/Lib/site-packages/numpy/core/native.pyd", 18 * MIB, 40),
        ("Projects/fieldnotes/__pycache__/pipeline.cpython.pyc", 2 * MIB, 20),
        ("Projects/fieldnotes/requirements.txt", 500, 20),
        ("Projects/fieldnotes/pipeline.py", 12000, 3),
        ("Projects/fieldnotes/data/embeddings.bin", 1.8 * GIB, 20),
        ("Music/Field recordings/Rain in the garden.wav", 410 * MIB, 60),
        ("Music/Field recordings/Morning birds.wav", 290 * MIB, 60),
        ("Backups/Notebook-2025.zip", 3.4 * GIB, 300),
        ("Backups/Project-sources.zip", 220 * MIB, 90),
        ("Downloads/Project-sources.zip", 220 * MIB, 90),
    ]
    files = []
    for relative, size, age in entries:
        path = f"{root}/{relative}"
        generated = None
        for name in ("node_modules", ".next", ".venv", "__pycache__"):
            if f"/{name}/" in path:
                generated = [path.split(f"/{name}/")[0] + f"/{name}", name]
                break
        files.append({"id": uid(path), "name": relative.split("/")[-1], "path": path, "root": root, "relative": relative,
                      "folder": relative.split("/")[0], "size": int(size), "modified": now - age * DAY,
                      "accessed": None, "last_opened": None, "category": category(Path(path)), "generated": generated})

    def make_report(items, created, identifier, name):
        for file in items:
            file.update(describe_file(file))
        groups = []
        for names in (["Brand-assets.zip", "Brand-assets-final.zip"], ["Website hero.png"], ["Project-sources.zip"]):
            members = [file for file in items if file["name"] in names]
            if len(members) > 1:
                digest = uid(names[0]) * 3 + "abcd"
                groups.append({"id": digest[:20], "hash": digest, "size": members[0]["size"], "files": members,
                               "potential_bytes": members[0]["size"] * (len(members) - 1)})
        findings = findings_for(items, groups, created)
        return {"id": identifier, "name": name, "demo": True, "created": created, "duration": 8.4, "roots": [root],
                "files": items, "findings": findings, "duplicates": groups,
                "apps": [
                    {"name": "Visual Studio Code", "version": "1.95.0", "publisher": "Microsoft", "location": root + "/AppData/Local/Programs/Microsoft VS Code", "service_date": "20261028", "last_used": None, "source": "Fictional demo metadata"},
                    {"name": "Blender", "version": "4.2.0", "publisher": "Blender Foundation", "location": "C:/Program Files/Blender Foundation/Blender 4.2", "service_date": "20260914", "last_used": None, "source": "Fictional demo metadata"},
                    {"name": "Notion", "version": "3.16.0", "publisher": "Notion Labs", "location": root + "/AppData/Local/Programs/Notion", "service_date": "20261002", "last_used": None, "source": "Fictional demo metadata"},
                ],
                "skipped": [{"path": root + "/.ssh", "reason": "Credential directory"}, {"path": root + "/OneDrive", "reason": "Reparse point; not followed"}, {"path": "C:/Windows", "reason": "Protected system directory"}],
                "warnings": ["This snapshot contains only fictional data. Creating it does not scan this computer."],
                "coverage": {"skipped": 3, "directories": 28, "entries": len(items) + 31, "limited": False, "hashing": True, "hashed_files": 7, "hashed_bytes": 1472 * MIB, "hash_skipped": 0, "apps_requested": True},
                "summary": summarize(items, findings)}
    previous = copy.deepcopy(files)
    previous = [file for file in previous if file["relative"] not in {"Videos/Weekend in Kyoto.mov", "Videos/Portfolio reel.mp4"}]
    for file in previous:
        if file["name"] == "client.pack":
            file["size"] = 320 * MIB
    old_path = root + "/Downloads/Old-conference.mp4"
    previous.append({"id": uid(old_path), "name": "Old-conference.mp4", "path": old_path, "root": root, "relative": "Downloads/Old-conference.mp4", "folder": "Downloads", "size": 940 * MIB, "modified": now - 80 * DAY, "accessed": None, "last_opened": None, "category": "Video & audio", "generated": None})
    return [make_report(files, now - 300, "demo-current", "Alex’s laptop"), make_report(previous, now - 7 * DAY, "demo-previous", "One week earlier")]
